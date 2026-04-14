import http.server
import json
import os
import sys
import time
import subprocess
import threading
from urllib.parse import urlparse, parse_qs
from collections import deque

BASE = os.path.dirname(os.path.abspath(__file__))
MAIN = os.path.join(BASE, "main.py")

MAIN_PROCESS = None
MAIN_LOCK = threading.Lock()

LOG_BUFFER = deque(maxlen=2000)
LOG_LOCK = threading.Lock()


def add_log(message, source="SERVER", store=True, echo=True):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    entry = {
        "timestamp": ts,
        "source": source,
        "message": str(message).rstrip()
    }

    if store:
        with LOG_LOCK:
            LOG_BUFFER.append(entry)

    if echo:
        print(f"[{ts}] [{source}] {message}")


def read_stream(stream, source):
    try:
        while True:
            line = stream.readline()
            if not line:
                break
            clean = line.rstrip("\n")
            if clean:
                add_log(clean, source=source)
    except Exception as e:
        add_log(f"Error leyendo stream {source}: {e}", source="SERVER")


def start_main():
    global MAIN_PROCESS

    if not os.path.exists(MAIN):
        add_log(f"No se encontró main.py en: {MAIN}", "SERVER")
        return False

    if MAIN_PROCESS and MAIN_PROCESS.poll() is None:
        add_log("main.py ya está corriendo.", "SERVER")
        return True

    add_log("🚀 Iniciando servicio ETL (main.py)...", "SERVER")

    MAIN_PROCESS = subprocess.Popen(
        [sys.executable, MAIN],
        cwd=BASE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )

    threading.Thread(target=read_stream, args=(MAIN_PROCESS.stdout, "MAIN-OUT"), daemon=True).start()
    threading.Thread(target=read_stream, args=(MAIN_PROCESS.stderr, "MAIN-ERR"), daemon=True).start()

    add_log(f"✅ Servicio ETL iniciado correctamente. PID={MAIN_PROCESS.pid}", "SERVER")
    return True


def stop_main():
    global MAIN_PROCESS

    if not MAIN_PROCESS:
        return

    if MAIN_PROCESS.poll() is not None:
        add_log("El servicio ETL ya estaba detenido.", "SERVER")
        MAIN_PROCESS = None
        return

    add_log("🛑 Deteniendo servicio ETL...", "SERVER")

    try:
        MAIN_PROCESS.terminate()
        MAIN_PROCESS.wait(timeout=8)
        add_log("✅ Servicio ETL detenido correctamente.", "SERVER")
    except subprocess.TimeoutExpired:
        add_log("⚠️ El servicio ETL no cerró a tiempo. Forzando cierre...", "SERVER")
        try:
            MAIN_PROCESS.kill()
            MAIN_PROCESS.wait(timeout=5)
            add_log("✅ Servicio ETL finalizado por cierre forzado.", "SERVER")
        except Exception as e:
            add_log(f"❌ No se pudo forzar el cierre del servicio ETL: {e}", "SERVER")
    except Exception as e:
        add_log(f"❌ Error al detener servicio ETL: {e}", "SERVER")
    finally:
        MAIN_PROCESS = None


def restart_main():
    with MAIN_LOCK:
        add_log("🔄 Reiniciando servicio ETL...", "SERVER")
        stop_main()
        time.sleep(1)
        return start_main()


def save_json_file(file_name, data):
    path = os.path.join(BASE, f"{file_name}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def count_etl_rules(data):
    return sum(len(d.get("route_rules", [])) for d in data.get("directories", []))


def count_notification_rules(data):
    return sum(len(d.get("recipient_rules", [])) for d in data.get("directories", []))


def get_status_payload():
    running = MAIN_PROCESS is not None and MAIN_PROCESS.poll() is None
    pid = MAIN_PROCESS.pid if running else None
    return {
        "ok": True,
        "main_running": running,
        "main_pid": pid,
        "server_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "base_path": BASE
    }


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE, **kwargs)

    def _json_response(self, status_code, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/system-status":
            self._json_response(200, get_status_payload())
            return

        if path == "/logs":
            query = parse_qs(parsed.query)
            try:
                limit = int(query.get("limit", ["300"])[0])
            except Exception:
                limit = 300

            limit = max(1, min(limit, 2000))

            with LOG_LOCK:
                logs = list(LOG_BUFFER)[-limit:]

            self._json_response(200, {
                "ok": True,
                "count": len(logs),
                "logs": logs
            })
            return

        super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path.startswith("/save/"):
            file_name = path.replace("/save/", "").strip()

            if file_name not in ("etl_config", "notification_config"):
                self._json_response(400, {"ok": False, "error": "Archivo no permitido"})
                return

            try:
                content_length = int(self.headers.get("Content-Length", "0"))
                body = self.rfile.read(content_length)
                data = json.loads(body.decode("utf-8"))

                if file_name == "etl_config":
                    total_rules = count_etl_rules(data)
                    add_log("📝 Se detectó una actualización en configuración ETL.", "CONFIG")
                    add_log(f"📦 Total de cargas ETL registradas: {total_rules}", "CONFIG")
                    add_log("💾 Guardando cambios en etl_config.json...", "CONFIG")

                    save_json_file(file_name, data)

                    add_log("✅ etl_config.json actualizado correctamente.", "CONFIG")
                    add_log("♻️ Aplicando cambios al sistema ETL...", "CONFIG")

                elif file_name == "notification_config":
                    total_rules = count_notification_rules(data)
                    add_log("📝 Se detectó una actualización en configuración de notificaciones.", "CONFIG")
                    add_log(f"🔔 Total de reglas de notificación registradas: {total_rules}", "CONFIG")
                    add_log("💾 Guardando cambios en notification_config.json...", "CONFIG")

                    save_json_file(file_name, data)

                    add_log("✅ notification_config.json actualizado correctamente.", "CONFIG")
                    add_log("♻️ Aplicando cambios al sistema ETL...", "CONFIG")

                restarted = restart_main()

                if restarted:
                    add_log("✅ Cambios aplicados correctamente en el sistema.", "CONFIG")
                else:
                    add_log("⚠️ El archivo se guardó, pero no se pudo reiniciar el sistema ETL.", "CONFIG")

                self._json_response(200, {
                    "ok": True,
                    "message": f"{file_name}.json guardado correctamente",
                    "main_restarted": restarted
                })
            except Exception as e:
                add_log(f"❌ Error guardando {file_name}: {e}", "CONFIG")
                self._json_response(500, {"ok": False, "error": str(e)})
            return

        if path == "/reload-system":
            try:
                add_log("🔄 Solicitud manual de reinicio del sistema recibida.", "SERVER")
                restarted = restart_main()
                if restarted:
                    add_log("✅ Reinicio manual completado correctamente.", "SERVER")
                else:
                    add_log("⚠️ No se pudo completar el reinicio manual.", "SERVER")

                self._json_response(200, {
                    "ok": True,
                    "message": "Sistema recargado correctamente",
                    "main_restarted": restarted
                })
            except Exception as e:
                add_log(f"❌ Error en reload-system: {e}", "SERVER")
                self._json_response(500, {"ok": False, "error": str(e)})
            return

        self._json_response(404, {"ok": False, "error": "Endpoint no encontrado"})

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def log_message(self, format, *args):
        message = format % args

        # Silenciar endpoints ruidosos que se consultan seguido desde el HTML
        noisy_paths = (
            "GET /system-status",
            "GET /logs"
        )

        if any(p in message for p in noisy_paths):
            return

        # Dejar solo logs HTTP realmente útiles
        add_log(message, "HTTP")


if __name__ == "__main__":
    add_log("=================================", "SERVER")
    add_log("API ETL + RELOAD + LOG EN VIVO", "SERVER")
    add_log("=================================", "SERVER")

    start_main()

    add_log("🌐 Servidor listo en http://localhost:8000", "SERVER")
    add_log("📌 Endpoints disponibles:", "SERVER")
    add_log("   POST /save/etl_config", "SERVER")
    add_log("   POST /save/notification_config", "SERVER")
    add_log("   POST /reload-system", "SERVER")
    add_log("   GET  /system-status", "SERVER")
    add_log("   GET  /logs?limit=300", "SERVER")

    try:
        http.server.ThreadingHTTPServer(("localhost", 8000), Handler).serve_forever()
    except KeyboardInterrupt:
        add_log("🛑 Cerrando servidor...", "SERVER")
    finally:
        stop_main()
        add_log("✅ Servidor cerrado.", "SERVER")
