"""Local preview server with clean URLs, as Vercel. Usage: python3 tools/serve.py [port]"""
import http.server
import socketserver
import os
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "src"


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(SRC), **kwargs)

    def do_GET(self):
        path = self.path.split("?")[0].split("#")[0]
        target = SRC / path.lstrip("/")
        if path.startswith("/_vercel/"):
            self.send_response(200)
            self.send_header("Content-Type", "application/javascript")
            self.end_headers()
            return
        if not target.exists() and (SRC / (path.lstrip("/") + ".html")).is_file():
            self.path = path + ".html"
        return super().do_GET()

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else int(os.environ.get("PORT", 8080))
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer(("127.0.0.1", port), Handler) as server:
        print(f"Past Mystery preview: http://localhost:{port}")
        server.serve_forever()
