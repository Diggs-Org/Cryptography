# Final Puzzle Design

This document is the canonical spec for the capstone multi-concept puzzle that players
unlock after completing every group. It covers concept selection, stage structure, seed
usage, unlock conditions, and the YAML skeleton that implements it.

---

## Overview

The final puzzle is a three-stage chain where the output of each stage becomes the input
for the next. No single technique is novel — every step is something the player has already
mastered in one of the seven groups — but recognizing *which* technique to apply at each
layer, without being told, is the challenge.

**Narrative framing:** The player receives an anonymous image file and a short handwritten
clue card (rendered as flavor text). Nothing else. The instructions read:

> *"Someone left this. We don't know who sent it or why. Start with what you can see."*

There is no hint about what kind of puzzle this is or how many layers it has. Each stage
reveals itself only after the previous one is solved.

---

## Unlock Condition

The final puzzle is **locked** until the player has completed all seven group capstone
puzzles: **1-3, 2-3, 3-3, 4-3, 5-3, 6-3, and 7-3**.

| Property | Value |
|---|---|
| Unlock trigger | All seven `"<n>-3": true` entries present in `crypt-progress` localStorage |
| Check location | `src/state.js` — same authority as all other progress reads |
| UI state when locked | Final puzzle tile shown but dimmed; tooltip: "Complete all group challenges to unlock" |
| UI state when unlocked | Tile becomes active; no special fanfare — the unlock is its own reward |

**Rationale:** The capstone deliberately requires *every* group, not a subset.
Techniques from Groups 5 (image) and 2 (Base64) appear in Stage 1; Group 3 (hidden in
plain sight) in Stage 2; Group 7 (book cipher) in Stage 3. A player who skipped audio
steganography (Group 6) has not been exposed to the mindset of inspecting files for
hidden data, which is exactly the posture Stage 1 demands. Requiring all seven ensures
no prerequisite skill is missing.

---

## Concept Groups Used

| Stage | Group | Technique |
|---|---|---|
| 1a | 5 — Image Steganography | LSB extraction from the red channel |
| 1b | 2 — Text Encoding | Base64 decoding |
| 2  | 3 — Hidden in Plain Sight | First-letter / acrostic extraction |
| 3  | 7 — Dead Drops & Open Web | Book cipher against a public Wikipedia article |

Groups 1 (classical ciphers) and 6 (audio steganography) are intentionally excluded to
keep the puzzle solvable in a single sitting. Their techniques have already been rewarded
within their own groups.

---

## Stage-by-Stage Structure

### Stage 1 — Image → Base64 → Article Title

The player is given a PNG image. Extracting the **LSBs of every red-channel pixel**,
read left-to-right, top-to-bottom, yields a byte sequence. Treating those bytes as
ASCII produces a **Base64-encoded string**. Decoding that string yields the title of a
Wikipedia article (e.g., `Enigma machine`).

- The image is selected from a curated library of 20 thematically neutral photographs
  (landscapes, architecture). The selected image is pre-processed at puzzle-generation
  time to embed the article title in the red-channel LSBs.
- The Base64 payload is self-delimiting: generation pads it to a fixed byte length
  known to the player through a subtle pixel-count hint in the image metadata (alt text
  on the `<img>` tag states the payload length in bits).
- Stage 1 is complete when the player has identified the Wikipedia article title.

### Stage 2 — Clue Card → Book Cipher Coordinates

The clue card is a short paragraph of flavor text rendered alongside the image — it
looks like a handwritten note. It is an **acrostic**: the first letter of each sentence,
read in order, spells out a coordinate pair in the format `P<n>W<n>` (e.g., `P3W7` =
paragraph 3, word 7).

Example clue card (illustrative only — actual text is seed-driven):

> *Please remember our old code. All channels, every word.*
> Reading top to bottom, only the beginnings matter.
> Wait for the third line to anchor your count.
> Seven steps in, stop.

First letters: P, R, R, W → not a valid example, but the format is `P<paragraph>W<word>`.

The clue card sentences are drawn from a library of 50 seed-indexed templates. Each
template encodes a specific coordinate pair as an acrostic. The RNG selects which
template to use, consistent with the paragraph/word numbers selected for Stage 3.

- The coordinate format `P<n>W<n>` is not explained anywhere in the UI. Players must
  recognize from prior Group 7 experience that this is a book cipher coordinate.
- Stage 2 is complete when the player has decoded the coordinate pair from the acrostic.

### Stage 3 — Book Cipher → Final Answer

Using the Wikipedia article from Stage 1 as the key and the `(paragraph, word)`
coordinates from Stage 2, the player extracts a **single word** — the final answer.

- "Paragraph" counts only non-empty body paragraphs (lead section is paragraph 1;
  section headers are skipped).
- "Word" counts space-delimited tokens; punctuation attached to a word is stripped.
- The final answer is always a common English noun or verb (ensured by curation of the
  article list and coordinate ranges).

---

## Seed Usage

The final puzzle uses a single seed, hashed and consumed in this fixed RNG call order:

| Call # | Parameter | Mapping |
|---|---|---|
| 1 | `article_index` | `floor(rng() * 50)` → index into 50 curated Wikipedia articles |
| 2 | `image_index` | `floor(rng() * 20)` → index into 20 base images |
| 3 | `paragraph_num` | `floor(rng() * 8) + 1` → integer in [1, 8] |
| 4 | `word_num` | `floor(rng() * 15) + 1` → integer in [1, 15] |

The clue card template is derived deterministically from `paragraph_num` and `word_num`
(not an additional RNG call): the generator looks up the entry in a 8×15 coordinate
table of pre-written acrostic sentence sets, ensuring the acrostic always encodes the
correct coordinates for Stage 3.

**Consistency guarantee:** Because all four parameters are produced from the same seeded
RNG in a fixed order, any given seed always produces the same article, image, coordinates,
and clue card. Sharing a seed URL gives another player an identical puzzle.

---

## Template

The final puzzle uses the **`multi-step`** template (`templates/puzzle-types/multi-step.html`),
which renders a step-progress indicator at the top and shows one stage at a time.
Completing a stage reveals the next.

| Stage | Input shown to player | Player enters |
|---|---|---|
| 1 | The PNG image + its pixel-count hint | The Wikipedia article title |
| 2 | The clue card paragraph | The coordinate pair (e.g., `P3W7`) |
| 3 | Confirmation of article + coordinates | The final answer word |

Stage answers are each HMAC-validated server-side before the next stage unlocks,
following the same token scheme defined in `docs/puzzle-generation.md`.

---

## YAML Definition Skeleton

```yaml
schema_version: "1.0"
id: "final"
group_id: null
type: multi-step
title: "The Package"
flavor: "Someone left this. We don't know who sent it or why. Start with what you can see."

params:
  article_index: !rng rand_int(0, 49)
  image_index:   !rng rand_int(0, 19)
  paragraph_num: !rng rand_int(1, 8)
  word_num:      !rng rand_int(1, 15)

  # Derived — not RNG calls; computed from the four params above
  article:       !gen select_article(article_index)
  base_image:    !gen select_image(image_index)
  clue_card:     !gen select_clue_card(paragraph_num, word_num)

content:
  stages:
    - id: stage-1
      type: image-lsb
      image:     !gen embed_lsb_red(base_image, b64encode(article.title))
      bit_count: !gen lsb_payload_bits(article.title)
      question:  "Extract the hidden data from the image. What Wikipedia article does it name?"
      answer:    !gen identity(article.title)

    - id: stage-2
      type: acrostic
      clue_card: !gen render_clue_card(clue_card)
      question:  "The note is hiding something. Read carefully. What are the coordinates?"
      answer:    !gen format_coordinate(paragraph_num, word_num)

    - id: stage-3
      type: book-cipher
      article_title: !gen identity(article.title)
      coordinate:    !gen format_coordinate(paragraph_num, word_num)
      question:      "Use the article as your key. What word do the coordinates point to?"
      answer:        !gen book_cipher_lookup(article, paragraph_num, word_num)

hints:
  - "Stage 1: Think about what can be hidden inside an image file."
  - "Stage 1: Look at the least significant bits — not every channel, just one."
  - "Stage 2: Reading is the skill. Which letters matter?"
  - "Stage 2: First letters. Every sentence. In order."
  - "Stage 3: You have an article and a map. Count carefully — headers don't count."
```

---

## Answer Security

Each stage answer is independently HMAC-signed, following the token scheme from
`docs/puzzle-generation.md`. The raw answer for stage N is never sent to the browser;
only its token is. Stage N+1 becomes visible only after the browser submits the correct
token for stage N.

The final answer (Stage 3) triggers the completion event: `crypt-progress["final"] = true`
is written to localStorage, and the player sees the end-game screen.

---

## Summary of Decisions

| Decision | Choice |
|---|---|
| Concept groups | 2 (Base64), 3 (acrostic), 5 (image LSB), 7 (book cipher) |
| Excluded groups | 1 (classical ciphers), 6 (audio) — already rewarded in their groups |
| Puzzle structure | 3 sequential stages; later stages hidden until prior answer is correct |
| Template | `multi-step.html` |
| Seed controls | Article (50), image (20), paragraph [1–8], word [1–15] — 4 RNG calls |
| RNG call order | article\_index, image\_index, paragraph\_num, word\_num — immutable |
| Unlock condition | All of 1-3, 2-3, 3-3, 4-3, 5-3, 6-3, 7-3 complete in localStorage |
| Narrative framing | Anonymous package; no technique hints in UI |
| Answer | Single word extracted by book cipher from Stage 3 |
