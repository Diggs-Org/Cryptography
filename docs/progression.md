# Puzzle Progression and Grouping Model

This document is the canonical record of how players move through the game — unlock conditions,
progress persistence, and replay rules.

## Group Unlock Model

Groups unlock **sequentially**. A player must complete all three puzzles in group N before group
N+1 becomes accessible. Groups 2–7 are locked on first load; only Group 1 is available
immediately.

**Rationale:** Each group introduces a meaningfully different concept. Encountering audio
steganography before understanding classical ciphers or text encoding would undermine the intended
learning arc. Sequential gating enforces the pedagogical order without ambiguity.

## Within-Group Puzzle Gating

Puzzles within a group are also **sequential**. Puzzle N-2 is locked until N-1 is complete;
N-3 until N-2. Players always enter a group at its first puzzle.

**Rationale:** Within-group puzzles escalate in difficulty (e.g., Caesar → ROT-13 variant →
Vigenère). The later puzzles assume familiarity with the earlier technique, so gating prevents
players from hitting a harder variant before they have the concept.

## Progress Persistence

Progress is stored in **`localStorage`** under the key `crypt-progress`.

| Property | Value |
|---|---|
| Storage key | `crypt-progress` |
| Entry format | `{ "<puzzle-id>": true }` |
| Clear mechanism | `reset()` in `src/state.js` |
| Server-side state | None |
| Account required | No |

`src/state.js` is the sole authority for reading and writing completion state. No other module
writes directly to localStorage.

Progress is local to the browser. Clearing browser data or switching devices resets progress.
This is acceptable for the current scope; server-side persistence is deferred to a future phase.

## Scoring and Rating

**No scoring or star/rating system.** Completion is binary: a puzzle is either solved or not.

The project roadmap places scoring in Phase 4 (polish). Adding a scoring system now would
introduce UI surface and persistence complexity before the core puzzle content is complete.
When Phase 4 arrives, the `crypt-progress` schema can be extended to store per-puzzle metadata
(attempts, time, hints used) without breaking existing completion flags.

## Replay Rules

Players **can replay** any puzzle they have access to by changing the `?seed=` URL parameter.
A new seed produces a structurally identical but differently parameterized puzzle (different
key, plaintext, etc.).

- Replaying does **not** un-mark a puzzle as complete.
- Any valid seed format (`[a-zA-Z0-9-]{1,16}`) is accepted; invalid seeds fall back to the
  daily seed.
- There is no explicit "play again" UI required at this stage — sharing a seed URL or editing
  the query parameter is sufficient.

**Rationale:** The seed system was designed specifically to support this use case (see
`docs/seed-system.md`). Allowing replay without resetting progress lets players experiment
with different inputs after solving a puzzle without losing their place in the game.

## Summary Table

| Decision | Choice |
|---|---|
| Group unlock order | Sequential (complete group N to unlock N+1) |
| Within-group puzzle order | Sequential (complete N-1 to unlock N-2) |
| Progress persistence | `localStorage` via `src/state.js` |
| Scoring / rating | None (deferred to Phase 4) |
| Replay with different seed | Yes — does not reset completion |
