# Puzzle Type Catalog

This document is the canonical reference for which cryptographic and steganographic concepts
are included in the game, their ordering, and the design of the final multi-concept puzzle.

## Concept Groups

Groups are ordered by intended difficulty. Each group contains three escalating puzzles.

| Group | Concept | Puzzle 1 | Puzzle 2 | Puzzle 3 |
|---|---|---|---|---|
| 1 | **Classical Ciphers** | Caesar cipher | ROT-13 variant | Vigenère cipher |
| 2 | **Text Encoding** | Binary / ASCII | Hex encoding | Base64 |
| 3 | **Hidden in Plain Sight** | Acrostics | Null ciphers | First-letter codes |
| 4 | **Whitespace & Invisible Characters** | Zero-width character hiding | Whitespace Morse code | Unicode homoglyphs |
| 5 | **Image Steganography** | LSB pixel hiding | Color channel extraction | Alpha channel secrets |
| 6 | **Audio Steganography** | Spectrogram messages | LSB audio encoding | Morse code in tone |
| 7 | **Dead Drops & Open Web** | Word-pattern hiding in social posts | Book cipher (public article as key) | Hidden messages in public commit histories |

## Final Puzzle

The final puzzle is a multi-layer challenge that chains techniques from Groups 2, 3, 5, and 7:

1. **Image** — an image is provided; extracting the LSBs of the red channel yields a Base64 string.
2. **Decode** — the Base64 string decodes to a Wikipedia article title.
3. **Book cipher** — the article text is the key; a set of coordinates `(paragraph, word)` reveals the final message.

This design rewards players who have internalized each individual technique and can recognize
which tool applies at each layer.

## Rationale

- Groups 1–2 cover the classic "information is scrambled" paradigm before moving to hiding.
- Groups 3–4 cover linguistic and typographic concealment — no special tools required, just careful reading.
- Groups 5–6 cover media-based steganography — information hidden inside files that appear innocent.
- Group 7 covers social / open-web steganography — information hiding in publicly visible, everyday content.
- The final puzzle deliberately skips Groups 1 (classical ciphers) and 6 (audio) to keep it solvable
  in a single sitting; cipher-breaking and audio analysis are already rewarded within their own groups.
