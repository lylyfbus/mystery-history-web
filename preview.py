#!/usr/bin/env python3
"""
PastMysteries Local Preview Server
Run this on your host machine to preview the site with clean URL support.

Usage:
  cd mystery-history-web
  python3 preview.py

Then open http://localhost:8080 in your browser.
Press Ctrl+C to stop.
"""

import os
import sys
import http.server
import socketserver

PORT = 8080
BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')

class CleanURLHandler(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path):
        path = path.split('?')[0].split('#')[0]
        rel = path.lstrip('/')
        full = os.path.join(BASE, rel)

        if os.path.isfile(full):
            return full
        if os.path.isfile(full + '.html'):
            return full + '.html'
        if os.path.isdir(full):
            idx = os.path.join(full, 'index.html')
            if os.path.isfile(idx):
                return idx
        return full

    def end_headers(self):
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        super().end_headers()

class ReuseServer(socketserver.TCPServer):
    allow_reuse_address = True

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else PORT
    os.chdir(BASE)
    server = ReuseServer(('0.0.0.0', port), CleanURLHandler)
    print(f'
  PastMysteries Local Preview')
    print(f'  ----------------------------')
    print(f'  Homepage:    http://localhost:{port}/')
    print(f'  All Stories: http://localhost:{port}/archive')
    print(f'  Sample Post: http://localhost:{port}/posts/dyatlov-pass')
    print(f'  Category:    http://localhost:{port}/categories/ancient-mysteries')
    print(f'  About:       http://localhost:{port}/about')
    print(f'  RSS Feed:    http://localhost:{port}/feed.xml')
    print(f'
  Press Ctrl+C to stop.
')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('
  Server stopped.')
        server.shutdown()
