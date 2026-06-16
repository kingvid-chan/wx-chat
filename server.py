#!/usr/bin/env python3
"""WeChat Web Chat — 静态服务器

基于 Python 标准库 http.server，绑定 127.0.0.1:19002。
- 处理 /projects/wx-chat/ 前缀路由
- HTML 文档返回 Cache-Control: no-cache
- /projects/wx-chat/healthz 返回 200 + ok
"""

import http.server
import os
import urllib.parse
import functools

HOST = "127.0.0.1"
PORT = 19002
PREFIX = "/projects/wx-chat"
VERSION = "0.0.1"


class WeChatHandler(http.server.SimpleHTTPRequestHandler):
    """自定义请求处理器，处理 /projects/wx-chat/ 前缀路由。"""

    def __init__(self, *args, **kwargs):
        # 以脚本所在目录作为文档根
        root_dir = os.path.dirname(os.path.abspath(__file__))
        super().__init__(*args, directory=root_dir, **kwargs)

    def do_GET(self):
        """处理 GET 请求，路由分发。"""
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # healthz 端点
        if path == f"{PREFIX}/healthz":
            self._handle_healthz()
            return

        # 静态文件：去掉 /projects/wx-chat 前缀
        if path.startswith(PREFIX):
            stripped = path[len(PREFIX):]
            if not stripped:
                # /projects/wx-chat/ → 重定向到 index.html
                self.send_response(301)
                self.send_header("Location", f"{PREFIX}/index.html?v={VERSION}")
                self.end_headers()
                return
            # 用去掉前缀的路径处理
            self.path = stripped
            # 走父类静态文件逻辑，但需要拦截响应头
            self._serve_static()
            return

        # 根路径重定向
        if path == "/":
            self.send_response(301)
            self.send_header("Location", f"{PREFIX}/index.html?v={VERSION}")
            self.end_headers()
            return

        # 其他未匹配路径
        self.send_error(404)
        self.end_headers()

    def _handle_healthz(self):
        """healthz 健康检查端点。"""
        body = b"ok"
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(body)

    def _serve_static(self):
        """提供静态文件，对 HTML 追加 Cache-Control: no-cache。"""
        # 使用父类 translate_path 解析文件路径
        fs_path = self.translate_path(self.path)

        if not os.path.exists(fs_path) or os.path.isdir(fs_path):
            self.send_error(404)
            self.end_headers()
            return

        # 判断 MIME 类型
        ctype = self.guess_type(fs_path)
        is_html = ctype.startswith("text/html") if ctype else False

        try:
            with open(fs_path, "rb") as f:
                body = f.read()
        except OSError:
            self.send_error(404)
            self.end_headers()
            return

        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        if is_html:
            self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        """简洁日志格式。"""
        print(f"[{self.log_date_time_string()}] {args[0]}")


def main():
    server = http.server.HTTPServer((HOST, PORT), WeChatHandler)
    print(f"WeChat Web Chat server starting on http://{HOST}:{PORT}{PREFIX}/")
    print(f"Health check: http://{HOST}:{PORT}{PREFIX}/healthz")
    print(f"Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        server.server_close()


if __name__ == "__main__":
    main()
