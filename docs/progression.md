# Puzzle Progression and Grouping Model

This document is the canonical record of how players move through the game — unlock conditions,
progress persistence, and replay rules.

## Group Unlock Model

All **7 groups are available from the start**. Players are not required to complete one group
before accessing another. Each group independently starts with its first puzzle unlocked.

## Within-Group Puzzle Gating

Puzzles within a group are **sequential**. Puzzle N-2 is locked until N-1 is complete;
N-3 until N-2. Every group starts with its first puzzle (N-1) unlocked.

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
| Group unlock order | All groups open from the start |
| Within-group puzzle order | Sequential (complete N-1 to unlock N-2) |
| Progress persistence | `localStorage` via `src/state.js` |
| Scoring / rating | None (deferred to Phase 4) |
| Replay with different seed | Yes — does not reset completion |
