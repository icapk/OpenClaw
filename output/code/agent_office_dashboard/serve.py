#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""简单本地服务器：提供静态页面 + /api/refresh"""

import json
import subprocess
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parent
WEB_DIR = BASE_DIR / "web"
GEN_SCRIPT = BASE_DIR / "generate_data.py"


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BASE_DIR), **kwargs)

    def _json(self, obj, code=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path in {"/", "/index.html"}:
            self.path = "/index.html"
        elif parsed.path in {"/office", "/office/", "/office/index.html"}:
            self.path = "/web/index.html"
        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/refresh":
            p = subprocess.run(["python3", str(GEN_SCRIPT)], capture_output=True, text=True)
            ok = p.returncode == 0
            return self._json(
                {
                    "ok": ok,
                    "stdout": (p.stdout or "").strip(),
                    "stderr": (p.stderr or "").strip(),
                },
                code=200 if ok else 500,
            )
        return self._json({"ok": False, "error": "Not Found"}, code=404)


def main():
    host = "127.0.0.1"
    port = 18979
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"🚀 Portal running: http://{host}:{port}")
    print(f"🏢 Office dashboard: http://{host}:{port}/office")
    server.serve_forever()


if __name__ == "__main__":
    main()
