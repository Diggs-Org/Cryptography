# Cryptography Puzzle Game

A web-based collection of cryptography puzzles. No installation required — runs entirely in the browser.

## Project Overview

Each puzzle teaches a real cryptographic concept (Caesar cipher, frequency analysis, XOR encoding, etc.) through hands-on problem solving. Puzzles are **seed-randomized**: the strategy to solve a puzzle is the same for every player, but the specific values (keys, messages, cities, numbers) differ based on a shareable seed. Share a seed with a friend to race on identical inputs.

Puzzles are organized into **concept groups** — each group introduces one idea through a series of escalating challenges. After completing all groups, a **final puzzle** combines techniques from across the game.

## Tech Stack

| Layer | Technology |
|---|---|
| Puzzle generation & seeding | Python |
| Web frontend | Vanilla JS + Vite |
| State management | ES module + `localStorage` |
| Dev server | Vite HMR (`npm run dev`) |
| Production serving | Python `http.server` (`npm run serve`) |

## Puzzle Structure

```
Game
├── Group 1: Classical Ciphers
│   ├── Puzzle 1-1  (Caesar cipher)
│   ├── Puzzle 1-2  (ROT-13 variant)
│   └── Puzzle 1-3  (Vigenère cipher)
├── Group 2: Text Encoding
│   ├── Puzzle 2-1  (binary / ASCII)
│   ├── Puzzle 2-2  (hex encoding)
│   └── Puzzle 2-3  (Base64)
├── Group 3: Hidden in Plain Sight
│   ├── Puzzle 3-1  (acrostics)
│   ├── Puzzle 3-2  (null ciphers)
│   └── Puzzle 3-3  (first-letter codes)
├── Group 4: Whitespace & Invisible Characters
│   ├── Puzzle 4-1  (zero-width character hiding)
│   ├── Puzzle 4-2  (whitespace Morse code)
│   └── Puzzle 4-3  (Unicode homoglyphs)
├── Group 5: Image Steganography
│   ├── Puzzle 5-1  (LSB pixel hiding)
│   ├── Puzzle 5-2  (color channel extraction)
│   └── Puzzle 5-3  (alpha channel secrets)
├── Group 6: Audio Steganography
│   ├── Puzzle 6-1  (spectrogram messages)
│   ├── Puzzle 6-2  (LSB audio encoding)
│   └── Puzzle 6-3  (Morse code in tone)
├── Group 7: Dead Drops & Open Web
│   ├── Puzzle 7-1  (word-pattern hiding in social posts)
│   ├── Puzzle 7-2  (book cipher with public article as key)
│   └── Puzzle 7-3  (messages hidden in public commit histories)
└── Final Puzzle  (image LSB → Base64 → book cipher, multi-concept)
```

Full catalog and rationale: [docs/puzzle-catalog.md](docs/puzzle-catalog.md)

## Seed System

A seed (numeric or short string) drives all random choices in a puzzle:

```
seed → deterministic RNG → puzzle parameters (key, plaintext, etc.)
```

Seeds are embedded in the URL so puzzles are bookmarkable and shareable:

```
https://example.com/puzzle/2-1?seed=abc123
```

The same seed always produces the same puzzle. A new seed produces a structurally identical but differently parameterized puzzle.

## Architecture

```
Python scripts (build time)
  └─ generate puzzle manifests (JSON) from seed templates

Vite (build time)
  └─ bundle JS + assets → dist/

Python http.server (runtime / self-hosted)
  └─ serve dist/ on localhost:8000

Browser (runtime)
  ├─ reads seed from URL
  ├─ seeds a JS PRNG with it
  └─ renders puzzle from manifest + seeded values
```

The frontend is built with Vite into a static `dist/` directory. For local play or
self-hosted deployments, `scripts/serve.py` serves that directory via Python's built-in
HTTP server. No application server or database is required.

## Development Workflow

```bash
npm run dev        # Vite dev server with HMR (http://localhost:5173)
npm run build      # Compile to dist/
npm run serve      # Build + serve dist/ via Python (http://localhost:8000)
python scripts/serve.py 9000  # Serve on a custom port
```

## Development Roadmap

| Phase | Milestone |
|---|---|
| 1 | Project setup, seed system, one playable cipher group |
| 2 | Remaining concept groups |
| 3 | Final multi-concept puzzle |
| 4 | Polish: UI, scoring, progress tracking |
| 5 | Public launch |

## Contributing

Design decisions (puzzle types, API shape, frontend framework) are tracked as Jira tickets in the **CRYPT** project. See those tickets before starting implementation work.
