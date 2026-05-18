# Puzzle Generation Architecture

This document is the canonical reference for how puzzles are defined, generated, and served.

## Guiding Principle

A puzzle author writes a single YAML file describing *what* the puzzle contains.
The Python backend reads it at request time, seeds the RNG, calls generator functions
to resolve values, and renders a prebuilt Jinja2 HTML template. No HTML, JS, or CSS
is touched by the puzzle author.

---

## Runtime Flow

```
Browser: GET /puzzle/1-1?seed=abc123
         │
Python backend (scripts/serve.py)
  1. Load puzzle-definitions/group-<n>/<id>.yaml
  2. Seed RNG from URL param  (djb2 + Mulberry32 — see docs/seed-system.md)
  3. Resolve `params` block   — !rng calls consume from the seeded RNG (order fixed)
  4. Evaluate `content` block — !gen calls are pure functions on resolved params
  5. Compute `answer`         — !gen call, result HMAC-signed, raw value discarded
  6. Render templates/puzzle-types/<type>.html with: puzzle, content, answer_token, seed
  7. Return complete HTML page
```

The HTML templates live in the repo and are **never generated at runtime — only rendered**.
Adding a new *puzzle type* means writing a new template and a `PuzzleTypeGenerator` subclass.
Adding a new *puzzle* within an existing type means writing a YAML file only.

---

## YAML Definition Format

The definition describes content, parameters, answer, and hints.
It does not describe UI, layout, styling, or win conditions — those belong to the template.

```yaml
schema_version: "1.0"
id: "1-1"
group_id: 1
type: conversation        # selects templates/puzzle-types/conversation.html
title: "Caesar Cipher"
flavor: "Alice and Bob have been passing notes. Something seems off."

# Concrete values produced from the seed.
# !rng calls consume from the RNG — ORDER IS IMMUTABLE after first publish.
# Reordering breaks all existing seed/URL combinations.
params:
  shift:     !rng rand_int(1, 25)
  plaintext: !rng rand_choice(wordlist)
  wordlist:
    - "MEET AT THE PARK AT NOON"
    - "THE PACKAGE IS UNDER THE BRIDGE"
    - "RENDEZVOUS BEHIND THE OLD MILL"

# The puzzle content — resolved before the template is rendered.
# !gen calls are pure functions on already-resolved param values.
content:
  exchanges:
    - speaker: Alice
      text: !gen caesar_encode(plaintext, shift)
    - speaker: Bob
      text: "Understood. Same key as last time?"
    - speaker: Alice
      text: !gen caesar_encode("YES CONFIRMED", shift)
  question: "Decode Alice's first message. What does it say?"

# Answer computed server-side. Never sent to the browser in plaintext.
answer: !gen identity(plaintext)

hints:
  - "Every letter has been shifted the same number of positions in the alphabet."
  - "The letter E is the most common in English — find it in the ciphertext."
  - "The shift is a whole number between 1 and 25."
```

### YAML Tags

| Tag | Meaning | RNG consumed? |
|---|---|---|
| `!rng func(args)` | Call a registered generator function that reads from the seeded RNG | Yes — order matters |
| `!gen func(args)` | Call a registered generator function with resolved param values only | No — pure function |

### Answer Security

The raw answer is never sent to the browser. After resolution the backend:
1. Computes `HMAC-SHA256(secret_key, normalize(answer))`
2. Sends only the token to the browser (embedded in a hidden form field)
3. On submission, re-derives the token from the player's guess and compares

---

## Generator Function Library (`puzzle-types/generators.py`)

Generator functions are plain Python registered by name:

```python
@register("caesar_encode")
def caesar_encode(text: str, shift: int) -> str: ...

@register("rand_int")
def rand_int(rng, low: int, high: int) -> int: ...

@register("rand_choice")
def rand_choice(rng, items: list): ...

@register("identity")
def identity(value): ...
```

Rules:
- `!rng` functions receive `rng` as their first argument (injected by the resolver)
- `!gen` functions receive only param values — no RNG argument
- Registered function names are **immutable** once a puzzle references them in a published YAML

---

## PuzzleTypeGenerator ABC (`puzzle-types/base.py`)

Used **only** when adding a new puzzle *type*. Puzzle authors adding puzzles within
an existing type never need this.

```python
class PuzzleTypeGenerator(ABC):
    type_id: str

    @abstractmethod
    def validate_definition(self, defn: dict) -> None:
        """Raise ValueError with a clear message if the definition is malformed."""

    @abstractmethod
    def required_generators(self) -> list[str]:
        """Names of generator functions this type depends on."""
```

Each type lives in `puzzle-types/<type-id>.py`. The corresponding Jinja2 template lives
in `templates/puzzle-types/<type-id>.html`.

---

## Template Context

Every puzzle template receives:

| Variable | Type | Contents |
|---|---|---|
| `puzzle` | dict | Full YAML definition (id, title, flavor, hints) |
| `content` | dict | Resolved content block |
| `answer_token` | str | HMAC-signed hash of the normalised answer |
| `seed` | str | The seed string (for display and the share URL) |

Templates extend `templates/base.html`, which provides the shared page layout,
hint panel, answer submission form, and win/fail state handling.

---

## Directory Layout

```
puzzle-definitions/
  group-1-classical-ciphers/
    1-1-caesar.yaml
    1-2-rot13.yaml
    1-3-vigenere.yaml
  group-2-text-encoding/
    ...

puzzle-types/
  base.py           # PuzzleTypeGenerator ABC
  generators.py     # @register decorator + all generator functions
  conversation.py   # type: conversation
  ...

templates/
  base.html                         # shared layout
  puzzle-types/
    conversation.html               # chat-exchange + text input
    encode-decode.html              # ciphertext shown, plaintext input
    text-reveal.html                # annotated text, highlight/identify input
    media-inspect.html              # image or audio asset + text input
    web-artifact.html               # simulated social post / article
    multi-step.html                 # chained sub-puzzle progress

schemas/
  puzzle-definition.schema.yaml     # JSON Schema (YAML syntax) for CI validation

scripts/
  serve.py          # HTTP server — routes /puzzle/<id> through the generation pipeline
```
