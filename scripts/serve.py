"""
Cryptography Puzzle Game — server entry point.

Usage:
    python scripts/serve.py [port]

For development, run alongside Vite:
    npm run dev                   # Vite HMR on :5173 for JS/CSS assets
    python scripts/serve.py 8000  # puzzle routing on :8000
"""

import http.server
import os
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000

sys.path.insert(0, str(ROOT))

from scripts.handler import PuzzleHandler  # noqa: E402

if __name__ == '__main__':
    os.makedirs(ROOT / 'dist', exist_ok=True)
    with http.server.HTTPServer(('', PORT), PuzzleHandler) as httpd:
        print(f'Puzzle server running at http://localhost:{PORT}')
        print(f'  Definitions: {ROOT / "puzzle-definitions"}')
        print(f'  Templates:   {ROOT / "templates"}')
        print(f'  Static dist: {ROOT / "dist"}')
        httpd.serve_forever()
