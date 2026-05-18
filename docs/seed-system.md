# Seed System

This document is the canonical spec for how seeds are formatted, hashed into PRNG state,
and consumed to produce deterministic puzzle parameters.

## Seed Format

- **Characters:** `[a-zA-Z0-9-]` (alphanumeric plus hyphen to support date format)
- **Length:** 1–16 characters
- **Normalization:** lowercased before hashing
- **Validation regex:** `^[a-zA-Z0-9-]{1,16}$`

Examples: `abc123`, `puzzle42`, `2026-05-18`, `xk9q`

## Default / Daily Seed Strategy

| Context | Seed value |
|---|---|
| Daily puzzle | Today's date as `YYYY-MM-DD` (e.g. `2026-05-18`) |
| Random play | Random 6-character alphanumeric string generated at page load |
| Shared puzzle | Value of the `?seed=` URL parameter; falls back to daily seed if absent or invalid |

## Hashing: djb2

The seed string is converted to a 32-bit unsigned integer using the **djb2** algorithm,
which is trivially portable between Python and JavaScript:

```
hash = 5381
for each character c in seed:
    hash = ((hash << 5) + hash) + char_code(c)
    hash = hash & 0xFFFFFFFF   # keep 32 bits
```

The same seed string always produces the same 32-bit hash value in both runtimes.

## PRNG: Mulberry32

The 32-bit hash is used as the initial state for the **Mulberry32** PRNG, which produces
a float in `[0, 1)` on each call:

```
function mulberry32(state):
    state = (state + 0x6D2B79F5) & 0xFFFFFFFF
    z = state
    z = ((z ^ (z >> 15)) * (z | 1)) & 0xFFFFFFFF
    z ^= z + ((z ^ (z >> 7)) * (z | 61)) & 0xFFFFFFFF
    return ((z ^ (z >> 14)) >>> 0) / 4294967296
```

Mulberry32 was chosen because:
- Identical output in Python and JavaScript given the same 32-bit state
- High statistical quality for a 32-bit generator
- ~5 lines of code with no dependencies

## Consuming the RNG: Parameter Mapping

Each puzzle type documents a fixed call order. The RNG is called sequentially; the order
must never change once published, as it would break existing seed/puzzle links.

### Example: Caesar Cipher (Group 1, Puzzle 1)

| Call # | Usage | Mapping |
|---|---|---|
| 1 | Shift key | `floor(rng() * 25) + 1` → integer in [1, 25] |
| 2 | Plaintext index | `floor(rng() * len(wordlist))` → index into plaintext wordlist |

Additional puzzle types will follow the same pattern, documented here as each group is
implemented.

## Seed URL Embedding

Seeds are embedded in the URL as a query parameter:

```
https://example.com/puzzle/1-1?seed=abc123
```

The frontend reads `new URLSearchParams(window.location.search).get('seed')` on load,
validates it, then seeds the RNG. Invalid or missing seeds fall back to the daily seed.
