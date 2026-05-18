"""HTTP request handler for the Cryptography Puzzle Game.

Routes:
  GET  /puzzle/<id>?seed=<seed>   Render a puzzle page
  POST /puzzle/<id>/check         Validate a player's answer (JSON)
  GET  /static/<path>             Serve files from templates/static/
  GET  /*                         Serve files from dist/
"""

import http.server
import json
import re
import urllib.parse
from datetime import date
from pathlib import Path

from scripts.resolver import check_answer, load_definition, resolve_puzzle

ROOT      = Path(__file__).parent.parent
DIST      = ROOT / 'dist'
TEMPLATES = ROOT / 'templates'

try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    _jinja_env = Environment(
        loader=FileSystemLoader(str(TEMPLATES)),
        autoescape=select_autoescape(['html']),
    )
except ImportError:
    _jinja_env = None

_PUZZLE_RE       = re.compile(r'^/puzzle/([^/]+)$')
_PUZZLE_CHECK_RE = re.compile(r'^/puzzle/([^/]+)/check$')
_STATIC_RE       = re.compile(r'^/static/(.+)$')
_VALID_SEED_RE   = re.compile(r'^[a-zA-Z0-9-]{1,16}$')

_MIME_TYPES = {
    '.html': 'text/html; charset=utf-8',
    '.js':   'application/javascript',
    '.css':  'text/css',
    '.json': 'application/json',
    '.png':  'image/png',
    '.jpg':  'image/jpeg',
    '.svg':  'image/svg+xml',
}


class PuzzleHandler(http.server.BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):  # noqa: N802
        print(f'  {self.address_string()} {fmt % args}')

    # -- routing -------------------------------------------------------------

    def do_GET(self):  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        path   = parsed.path

        m = _PUZZLE_RE.match(path)
        if m:
            seed = urllib.parse.parse_qs(parsed.query).get('seed', [None])[0]
            if not seed or not _VALID_SEED_RE.match(seed):
                seed = date.today().isoformat()
            self._serve_puzzle(m.group(1), seed, self.path)
            return

        m = _STATIC_RE.match(path)
        if m:
            self._serve_file(TEMPLATES / 'static' / m.group(1))
            return

        self._serve_file(DIST / (path.lstrip('/') or 'index.html'))

    def do_POST(self):  # noqa: N802
        m = _PUZZLE_CHECK_RE.match(urllib.parse.urlparse(self.path).path)
        if m:
            self._check_answer(m.group(1))
            return
        self._send_json(404, {'error': 'not found'})

    # -- puzzle rendering ----------------------------------------------------

    def _serve_puzzle(self, puzzle_id: str, seed: str, request_url: str):
        if _jinja_env is None:
            self._send_error(500, 'Jinja2 is not installed. Run: pip install jinja2')
            return

        try:
            defn = load_definition(puzzle_id)
        except FileNotFoundError:
            self._send_error(404, f'Puzzle {puzzle_id!r} not found')
            return

        puzzle_type = defn.get('type')
        try:
            template = _jinja_env.get_template(f'puzzle-types/{puzzle_type}.html')
        except Exception:
            self._send_error(500, f'No template for puzzle type {puzzle_type!r}')
            return

        try:
            _params, content, answer_token = resolve_puzzle(defn, seed)
        except Exception as exc:
            self._send_error(500, f'Error resolving puzzle: {exc}')
            return

        html = template.render(
            puzzle=defn,
            content=content,
            answer_token=answer_token,
            seed=seed,
            request_url=request_url,
        )
        self._send_html(html)

    def _check_answer(self, puzzle_id: str):  # noqa: ARG002
        length = int(self.headers.get('Content-Length', 0))
        body   = json.loads(self.rfile.read(length))
        guess  = str(body.get('answer', ''))
        token  = str(body.get('token', ''))
        self._send_json(200, {'correct': check_answer(guess, token)})

    # -- static file serving -------------------------------------------------

    def _serve_file(self, file_path: Path):
        if not file_path.exists():
            self._send_error(404, 'Not found')
            return
        mime = _MIME_TYPES.get(file_path.suffix, 'application/octet-stream')
        data = file_path.read_bytes()
        self.send_response(200)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    # -- response helpers ----------------------------------------------------

    def _send_html(self, html: str):
        data = html.encode()
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_json(self, status: int, payload: dict):
        data = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_error(self, status: int, message: str):
        self._send_html(f'<pre style="color:red">{status} {message}</pre>')
