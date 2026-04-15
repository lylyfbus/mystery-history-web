#!/usr/bin/env python3
"""Local dev server with clean URL support for PastMysteries.com.

Usage:  python3 serve.py
Open:   http://localhost:8080
"""
import http.server
import os
import sys
from pathlib import Path

class CleanURLHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split('?')[0].split('#')[0]
        rel_path = path.lstrip('/')
        if not rel_path:
            rel_path = 'index.html'
        base_dir = Path(os.getcwd())
        target = base_dir / rel_path
        if target.is_dir():
            target = target / 'index.html'
        if not target.exists() and not target.suffix:
            html_target = target.with_suffix('.html')
            if html_target.exists():
                self.path = '/' + str(html_target.relative_to(base_dir))
        elif not target.exists():
            html_candidate = base_dir / (rel_path + '.html')
            if html_candidate.exists():
                self.path = '/' + str(html_candidate.relative_to(base_dir))
        return super().do_GET()

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

PORT = 8080
print(f"Past Mystery local server running at http://localhost:{PORT}")
print(f"Serving from: {os.getcwd()}")
print("Clean URLs enabled: /posts/pyramids-of-giza works without .html")
print("Press Ctrl+C to stop")
print()
with http.server.HTTPServer(('', PORT), CleanURLHandler) as httpd:
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("Server stopped.")
        sys.exit(0)
