"""
HTTP server for the Cryptography Puzzle Game.

Routes:
  GET  /                          Game index (served from dist/ if built, else stub)
  GET  /puzzle/<id>?seed=<seed>   Render a puzzle page
  POST /puzzle/<id>/check         Check a player's answer (JSON in, JSON out)
  GET  /*                         Static files from dist/

Usage:
    python scripts/serve.py [port]

For development, run alongside Vite:
    npm run dev          # Vite HMR on :5173 for JS/CSS assets
    python scripts/serve.py 8000  # puzzle routing on :8000
"""

import hashlib
import hmac
import http.server
import importlib
import json
import os
import re
import sys
import urllib.parse
from pathlib import Path

import yaml

ROOT        = Path(__file__).parent.parent
DIST        = ROOT / 'dist'
TEMPLATES   = ROOT / 'templates'
DEFINITIONS = ROOT / 'puzzle-definitions'
PUZZLE_TYPES_DIR = ROOT / 'puzzle_types'
PORT        = int(sys.argv[1]) if len(sys.argv) > 1 else 8000

# Secret used for HMAC answer tokens. In production, set via env var.
HMAC_SECRET = os.environ.get('PUZZLE_HMAC_SECRET', 'dev-secret-change-in-production').encode()

# ---------------------------------------------------------------------------
# Bootstrap: load Jinja2 and the generator/type registry
# ---------------------------------------------------------------------------

try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    _jinja_env = Environment(
        loader=FileSystemLoader(str(TEMPLATES)),
        autoescape=select_autoescape(['html']),
    )
except ImportError:
    _jinja_env = None

# Add puzzle-types/ to path so generator modules can import each other
sys.path.insert(0, str(ROOT))
import puzzle_types.generators as _gen_module  # noqa: E402 — registers all generators

# Load all PuzzleTypeGenerator subclasses
_TYPE_REGISTRY: dict[str, object] = {}
for _f in PUZZLE_TYPES_DIR.glob('*.py'):
    if _f.stem in ('base', 'generators', '__init__'):
        continue
    _mod = importlib.import_module(f'puzzle_types.{_f.stem}')
    for _name in dir(_mod):
        _cls = getattr(_mod, _name)
        if (
            isinstance(_cls, type)
            and hasattr(_cls, 'type_id')
            and _cls.type_id
            and _cls is not _cls.__bases__[0]  # skip the ABC itself
        ):
            _TYPE_REGISTRY[_cls.type_id] = _cls()

# ---------------------------------------------------------------------------
# YAML custom tags: !rng and !gen
# ---------------------------------------------------------------------------

class _TaggedCall:
    def __init__(self, tag: str, expr: str):
        self.tag  = tag   # 'rng' or 'gen'
        self.expr = expr  # e.g. "rand_int(1, 25)"


def _tagged_constructor(tag):
    def constructor(loader, node):
        return _TaggedCall(tag, loader.construct_scalar(node))
    return constructor


yaml.add_constructor('!rng', _tagged_constructor('rng'), Loader=yaml.SafeLoader)
yaml.add_constructor('!gen', _tagged_constructor('gen'), Loader=yaml.SafeLoader)


def _parse_call(expr: str) -> tuple[str, list]:
    """Parse "func_name(arg1, arg2)" into ('func_name', ['arg1', 'arg2'])."""
    m = re.match(r'^(\w+)\((.*)\)$', expr.strip())
    if not m:
        raise ValueError(f"Cannot parse generator call: {expr!r}")
    name = m.group(1)
    raw_args = [a.strip() for a in m.group(2).split(',') if a.strip()] if m.group(2).strip() else []
    return name, raw_args


def _resolve_arg(arg: str, params: dict):
    """Resolve a string argument to a Python value using resolved params."""
    if arg.startswith('"') and arg.endswith('"'):
        return arg[1:-1]
    if arg.startswith("'") and arg.endswith("'"):
        return arg[1:-1]
    try:
        return int(arg)
    except ValueError:
        pass
    try:
        return float(arg)
    except ValueError:
        pass
    if arg in params:
        return params[arg]
    raise ValueError(f"Cannot resolve argument: {arg!r}")

# ---------------------------------------------------------------------------
# Mulberry32 RNG (mirrors src/rng.js)
# ---------------------------------------------------------------------------

def _djb2(s: str) -> int:
    h = 5381
    for c in s:
        h = ((h * 33) + ord(c)) & 0xFFFFFFFF
    return h


def _make_rng(seed: str):
    state = [_djb2(seed.lower()) & 0xFFFFFFFF]

    def rng():
        s = (state[0] + 0x6D2B79F5) & 0xFFFFFFFF
        state[0] = s
        z = s
        z = ((z ^ (z >> 15)) * (z | 1)) & 0xFFFFFFFF
        z = (z ^ (z + ((z ^ (z >> 7)) * (z | 61)) & 0xFFFFFFFF)) & 0xFFFFFFFF
        return ((z ^ (z >> 14)) & 0xFFFFFFFF) / 4294967296

    return rng

# ---------------------------------------------------------------------------
# Definition loader and resolver
# ---------------------------------------------------------------------------

_DEFINITION_CACHE: dict[str, dict] = {}


def _find_definition(puzzle_id: str) -> Path | None:
    for path in DEFINITIONS.rglob('*.yaml'):
        with path.open() as f:
            raw = yaml.safe_load(f)
        if str(raw.get('id')) == puzzle_id:
            return path
    return None


def _load_definition(puzzle_id: str) -> dict:
    if puzzle_id in _DEFINITION_CACHE:
        return _DEFINITION_CACHE[puzzle_id]
    path = _find_definition(puzzle_id)
    if path is None:
        raise FileNotFoundError(f"No definition found for puzzle id {puzzle_id!r}")
    with path.open() as f:
        defn = yaml.load(f, Loader=yaml.SafeLoader)
    _DEFINITION_CACHE[puzzle_id] = defn
    return defn


def _resolve_value(value, params: dict, rng):
    """Recursively resolve _TaggedCall nodes and dicts/lists."""
    if isinstance(value, _TaggedCall):
        name, raw_args = _parse_call(value.expr)
        fn = _gen_module.get(name)
        args = [_resolve_arg(a, params) for a in raw_args]
        if value.tag == 'rng':
            return fn(rng, *args)
        else:
            return fn(*args)
    if isinstance(value, dict):
        return {k: _resolve_value(v, params, rng) for k, v in value.items()}
    if isinstance(value, list):
        return [_resolve_value(item, params, rng) for item in value]
    return value


def resolve_puzzle(defn: dict, seed: str) -> tuple[dict, dict, str]:
    """Return (resolved_params, resolved_content, answer_token).

    Two-pass param resolution:
      Pass 1 — static values (lists, strings, numbers) loaded unconditionally
      Pass 2 — !rng / !gen calls resolved in document order (RNG order is immutable)
    This lets static data like wordlists appear anywhere in the params block.
    """
    rng = _make_rng(seed)
    raw_params = defn.get('params', {})

    # Pass 1: static values
    params: dict = {}
    for key, value in raw_params.items():
        if not isinstance(value, _TaggedCall):
            params[key] = _resolve_value(value, params, rng)

    # Pass 2: tagged calls in document order
    for key, value in raw_params.items():
        if isinstance(value, _TaggedCall):
            params[key] = _resolve_value(value, params, rng)

    content = _resolve_value(defn.get('content', {}), params, rng)
    raw_answer = _resolve_value(defn.get('answer'), params, rng)
    answer_token = _make_token(str(raw_answer))

    return params, content, answer_token


def _make_token(answer: str) -> str:
    normalised = answer.strip().upper()
    return hmac.new(HMAC_SECRET, normalised.encode(), hashlib.sha256).hexdigest()


def _check_answer(guess: str, token: str) -> bool:
    return hmac.compare_digest(_make_token(guess), token)

# ---------------------------------------------------------------------------
# Request handler
# ---------------------------------------------------------------------------

_PUZZLE_RE       = re.compile(r'^/puzzle/([^/]+)$')
_PUZZLE_CHECK_RE = re.compile(r'^/puzzle/([^/]+)/check$')
_VALID_SEED_RE   = re.compile(r'^[a-zA-Z0-9-]{1,16}$')


def _daily_seed() -> str:
    from datetime import date
    return date.today().isoformat()


class Handler(http.server.BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):  # noqa: N802
        print(f'  {self.address_string()} {fmt % args}')

    # -- routing -------------------------------------------------------------

    def do_GET(self):  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        path   = parsed.path

        m = _PUZZLE_RE.match(path)
        if m:
            seed = urllib.parse.parse_qs(parsed.query).get('seed', [None])[0]
            if seed is None or not _VALID_SEED_RE.match(seed):
                seed = _daily_seed()
            self._serve_puzzle(m.group(1), seed, self.path)
            return

        self._serve_static(path)

    def do_POST(self):  # noqa: N802
        m = _PUZZLE_CHECK_RE.match(urllib.parse.urlparse(self.path).path)
        if m:
            self._check_puzzle_answer(m.group(1))
            return
        self._send_json(404, {'error': 'not found'})

    # -- puzzle rendering ----------------------------------------------------

    def _serve_puzzle(self, puzzle_id: str, seed: str, request_url: str):
        if _jinja_env is None:
            self._send_error(500, 'Jinja2 is not installed. Run: pip install jinja2')
            return

        try:
            defn = _load_definition(puzzle_id)
        except FileNotFoundError:
            self._send_error(404, f'Puzzle {puzzle_id!r} not found')
            return

        puzzle_type = defn.get('type')
        template_path = f'puzzle-types/{puzzle_type}.html'

        try:
            template = _jinja_env.get_template(template_path)
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

    def _check_puzzle_answer(self, puzzle_id: str):
        length = int(self.headers.get('Content-Length', 0))
        body   = json.loads(self.rfile.read(length))
        guess  = str(body.get('answer', ''))
        token  = str(body.get('token', ''))
        self._send_json(200, {'correct': _check_answer(guess, token)})

    # -- static files --------------------------------------------------------

    def _serve_static(self, path: str):
        if path == '/':
            path = '/index.html'
        file_path = DIST / path.lstrip('/')
        if not file_path.exists():
            self._send_error(404, 'Not found')
            return
        content_type = _guess_type(file_path.suffix)
        data = file_path.read_bytes()
        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    # -- helpers -------------------------------------------------------------

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


def _guess_type(suffix: str) -> str:
    return {
        '.html': 'text/html; charset=utf-8',
        '.js':   'application/javascript',
        '.css':  'text/css',
        '.json': 'application/json',
        '.png':  'image/png',
        '.jpg':  'image/jpeg',
        '.svg':  'image/svg+xml',
    }.get(suffix, 'application/octet-stream')


# ---------------------------------------------------------------------------

if __name__ == '__main__':
    os.makedirs(DIST, exist_ok=True)
    with http.server.HTTPServer(('', PORT), Handler) as httpd:
        print(f'Puzzle server running at http://localhost:{PORT}')
        print(f'  Static files:       {DIST}')
        print(f'  Puzzle definitions: {DEFINITIONS}')
        print(f'  Templates:          {TEMPLATES}')
        httpd.serve_forever()
