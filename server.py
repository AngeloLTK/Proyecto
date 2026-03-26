import http.server
import json
import urllib
import os

class Handler(http.server.SimpleHTTPRequestHandler):

    def do_POST(self):
        if self.path.startswith("/save/"):
            file = self.path.replace("/save/", "").strip()
            if file not in ("etl_config", "notification_config"):
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Archivo no permitido")
                return

            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)
            try:
                data = json.loads(body.decode("utf-8"))
                with open(f"{file}.json", "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"OK")
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(str(e).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

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


print("Servidor listo en http://localhost:8000")
http.server.ThreadingHTTPServer(("localhost", 8000), Handler).serve_forever()