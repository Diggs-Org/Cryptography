"""Seed-based PRNG — Python mirror of src/rng.js.

djb2 hash + Mulberry32 PRNG.  Must produce bit-identical output to the JS
implementation for any given seed string.
"""
import re
from datetime import date

SEED_RE = re.compile(r'^[a-zA-Z0-9-]{1,16}$')
_U32 = 0xFFFFFFFF


def djb2(s: str) -> int:
    h = 5381
    for c in s:
        h = ((h * 33) + ord(c)) & _U32
    return h


def _mulberry32(state: int):
    """Returns a generator that yields floats in [0, 1)."""
    s = state & _U32
    while True:
        s = (s + 0x6D2B79F5) & _U32
        z = s
        z = ((z ^ (z >> 15)) * (z | 1)) & _U32
        z = (z ^ (z + ((z ^ (z >> 7)) * (z | 61)) & _U32)) & _U32
        yield ((z ^ (z >> 14)) & _U32) / 4294967296


def validate_seed(seed: str) -> bool:
    return bool(SEED_RE.match(seed))


def daily_seed() -> str:
    return date.today().isoformat()


def make_rng(seed: str):
    """Return a zero-argument callable that produces floats in [0, 1)."""
    gen = _mulberry32(djb2(seed.lower()))
    return lambda: next(gen)


def rand_int(rng, min_: int, max_: int) -> int:
    """Return a random integer in [min_, max_)."""
    return int(rng() * (max_ - min_)) + min_
