#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OpenClaw API服务器 - 提供CLI命令执行接口"""

import json
import subprocess
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


class APIHandler(SimpleHTTPRequestHandler):
    def _json(self, obj, code=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        # 提供静态文件服务
        parsed = urlparse(self.path)
        if parsed.path.startswith('/api/'):
            self.handle_api()
        else:
            # 静态文件服务 - 指定web目录
            self.directory = str(BASE_DIR / 'web')
            try:
                super().do_GET()
            except:
                # 如果文件不存在，返回404
                self.send_error(404)

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path.startswith('/api/'):
            self.handle_api()
        else:
            self._json({"ok": False, "error": "Not Found"}, code=404)

    def handle_api(self):
        if self.path == '/api/openclaw-exec':
            try:
                # 获取命令参数
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length).decode('utf-8')
                
                # 解析JSON参数
                params = json.loads(post_data) if post_data else {}
                cmd = params.get('cmd', 'openclaw subagents list --json')
                
                # 执行命令
                result = subprocess.run(
                    cmd, 
                    shell=True, 
                    capture_output=True, 
                    text=True, 
                    timeout=30
                )
                
                # 解析输出
                output = {
                    'ok': result.returncode == 0,
                    'stdout': result.stdout.strip(),
                    'stderr': result.stderr.strip(),
                    'returncode': result.returncode,
                    'command': cmd
                }
                
                # 尝试解析JSON输出
                if result.returncode == 0 and result.stdout.strip():
                    try:
                        output['data'] = json.loads(result.stdout.strip())
                    except json.JSONDecodeError:
                        output['data'] = result.stdout.strip()
                
                self._json(output, code=200 if result.returncode == 0 else 500)
                
            except Exception as e:
                self._json({
                    'ok': False,
                    'error': str(e),
                    'command': cmd if 'cmd' in locals() else 'unknown'
                }, code=500)
        else:
            self._json({"ok": False, "error": "Not Found"}, code=404)


def main():
    host = "127.0.0.1"
    port = 18980
    server = ThreadingHTTPServer((host, port), APIHandler)
    print(f"🚀 OpenClaw API Server running: http://{host}:{port}")
    print(f"📊 Office Dashboard: http://{host}:{port}/custom-ui/board/office-visual.html")
    server.serve_forever()


if __name__ == "__main__":
    from urllib.parse import urlparse
    main()