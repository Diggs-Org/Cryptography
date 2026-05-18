"""
Serves the Vite production build (`dist/`) via Python's built-in HTTP server.

Usage:
    python scripts/serve.py [port]

Run `npm run build` first to populate the dist/ directory.
"""

import http.server
import os
import sys

ROOT = os.path.join(os.path.dirname(__file__), '..', 'dist')
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)


if __name__ == '__main__':
    os.makedirs(ROOT, exist_ok=True)
    with http.server.HTTPServer(('', PORT), Handler) as httpd:
        print(f'Serving {os.path.abspath(ROOT)} at http://localhost:{PORT}')
        httpd.serve_forever()
