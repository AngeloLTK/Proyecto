# ============================================================
# launcher.py
# Levanta server.py y abre la UI principal
# ============================================================

import threading
import subprocess
import sys
import os
import time
import webbrowser

BASE = os.path.dirname(os.path.abspath(__file__))
SERVER = os.path.join(BASE, "server.py")

server_process = None

def run_server():
    global server_process
    print(">>> Iniciando API + administrador ETL (server.py)...")
    server_process = subprocess.Popen([sys.executable, SERVER], cwd=BASE)

if __name__ == "__main__":
    print("=================================")
    print("       LANZADOR ETL - SURA")
    print("=================================")

    t1 = threading.Thread(target=run_server, daemon=True)
    t1.start()

    time.sleep(2)

    url = "http://localhost:8000/notifi9.html"
    print(f">>> Abriendo navegador en {url} ...")
    time.sleep(2)
    webbrowser.open(url)

    print(">>> Todo funcionando ✔")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n>>> Cerrando launcher...")
        try:
            if server_process and server_process.poll() is None:
                server_process.terminate()
        except Exception:
            pass
        print(">>> Cerrado por usuario.")