# Chaining Gap — `verified` (gap), `open` (fix)

**Observation (verified by user observation, USER-OBS-CHAINING):**
per-cut same-master renders **reset the scene at every cut** — shot 2
re-imagines the scene instead of continuing shot 1.

Fix path (NOT YET IMPLEMENTED — open):

1. **Last-frame chaining**: extract shot 1's final frame (ffmpeg), use
   it as shot 2's `image_start` reference so composition carries over.
2. **FL2VA multishot**: native multishot continuation
   (`models/minimax_h3/multishot.py` path).

Status: **OPEN** — no code in this repo or in the WanGP checkout
implements chained shots end-to-end yet. See
`experiments/live/chained-test/` for the first controlled attempt.

## Evidence

- USER-OBS-CHAINING: repeated observation across per-cut render
  batches.
- Code audit: no chaining driver existed at time of writing.
