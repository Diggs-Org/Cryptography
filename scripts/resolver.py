"""Puzzle definition loader and seed-based resolver.

Responsible for:
- Registering the !rng / !gen YAML custom tags
- Loading and caching puzzle definition files
- Two-pass param resolution (statics first, then tagged calls in RNG order)
- HMAC answer token creation and verification
"""

import hashlib
import hmac
import os
import re
import sys
from pathlib import Path

import yaml

ROOT        = Path(__file__).parent.parent
DEFINITIONS = ROOT / 'puzzle-definitions'

HMAC_SECRET = os.environ.get('PUZZLE_HMAC_SECRET', 'dev-secret-change-in-production').encode()

sys.path.insert(0, str(ROOT))
import puzzle_types.generators as _generators  # noqa: E402 — registers all functions

# ---------------------------------------------------------------------------
# YAML custom tags
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

# ---------------------------------------------------------------------------
# Expression parser and argument resolver
# ---------------------------------------------------------------------------

def _parse_call(expr: str) -> tuple[str, list]:
    """Parse "func_name(arg1, arg2)" into ('func_name', ['arg1', 'arg2'])."""
    m = re.match(r'^(\w+)\((.*)\)$', expr.strip())
    if not m:
        raise ValueError(f"Cannot parse generator call: {expr!r}")
    name = m.group(1)
    raw_args = [a.strip() for a in m.group(2).split(',') if a.strip()] if m.group(2).strip() else []
    return name, raw_args


def _resolve_arg(arg: str, params: dict):
    """Coerce a string argument token to a Python value."""
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


def _resolve_value(value, params: dict, rng):
    """Recursively resolve _TaggedCall nodes, dicts, and lists."""
    if isinstance(value, _TaggedCall):
        name, raw_args = _parse_call(value.expr)
        fn = _generators.get(name)
        args = [_resolve_arg(a, params) for a in raw_args]
        return fn(rng, *args) if value.tag == 'rng' else fn(*args)
    if isinstance(value, dict):
        return {k: _resolve_value(v, params, rng) for k, v in value.items()}
    if isinstance(value, list):
        return [_resolve_value(item, params, rng) for item in value]
    return value

# ---------------------------------------------------------------------------
# Mulberry32 RNG (mirrors src/rng.js / scripts/rng.py)
# ---------------------------------------------------------------------------

def _djb2(s: str) -> int:
    h = 5381
    for c in s:
        h = ((h * 33) + ord(c)) & 0xFFFFFFFF
    return h


def make_rng(seed: str):
    """Return a zero-argument callable producing floats in [0, 1) from the seed."""
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
# Definition loader
# ---------------------------------------------------------------------------

_CACHE: dict[str, dict] = {}


def load_definition(puzzle_id: str) -> dict:
    """Load and cache the YAML definition for a puzzle ID. Raises FileNotFoundError."""
    if puzzle_id in _CACHE:
        return _CACHE[puzzle_id]
    for path in DEFINITIONS.rglob('*.yaml'):
        raw = yaml.safe_load(path.read_text())
        if str(raw.get('id')) == puzzle_id:
            defn = yaml.load(path.read_text(), Loader=yaml.SafeLoader)
            _CACHE[puzzle_id] = defn
            return defn
    raise FileNotFoundError(f"No definition found for puzzle id {puzzle_id!r}")

# ---------------------------------------------------------------------------
# Resolver
# ---------------------------------------------------------------------------

def resolve_puzzle(defn: dict, seed: str) -> tuple[dict, dict, str]:
    """Return (resolved_params, resolved_content, answer_token).

    Two-pass param resolution:
      Pass 1 — static values (lists, strings, numbers) resolved unconditionally
      Pass 2 — !rng / !gen calls resolved in document order (RNG order is immutable)
    This lets static data appear anywhere in the params block.
    """
    rng = make_rng(seed)
    raw_params = defn.get('params', {})

    params: dict = {}
    for key, value in raw_params.items():
        if not isinstance(value, _TaggedCall):
            params[key] = _resolve_value(value, params, rng)

    for key, value in raw_params.items():
        if isinstance(value, _TaggedCall):
            params[key] = _resolve_value(value, params, rng)

    content      = _resolve_value(defn.get('content', {}), params, rng)
    raw_answer   = _resolve_value(defn.get('answer'), params, rng)
    answer_token = make_token(str(raw_answer))

    return params, content, answer_token

# ---------------------------------------------------------------------------
# Answer token (HMAC-SHA256)
# ---------------------------------------------------------------------------

def make_token(answer: str) -> str:
    normalised = answer.strip().upper()
    return hmac.new(HMAC_SECRET, normalised.encode(), hashlib.sha256).hexdigest()


def check_answer(guess: str, token: str) -> bool:
    return hmac.compare_digest(make_token(guess), token)
