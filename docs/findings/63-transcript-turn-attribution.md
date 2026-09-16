# 63 — multi-turn transcript scoring masks omitted dialogue

Status: CLOSED in PR #94 / commit `a827110`; per-turn transcript attribution
is on `main`.

## Evidence

Qodo review of PR #84 found that `transcript_judge` concatenated multiple
intended turns into one reference. A correctly transcribed long turn could
therefore dominate normalized WER while a short turn was completely absent and
still pass the per-turn gate.

## Minimal fix

Align the complete transcript to the combined, turn-delimited reference using
sequence matching, attribute edit operations to their intended turns, and
require every turn to meet the pass bar. Persist the per-turn score list as
`turn_scores` while retaining the worst-turn summary.

Regression coverage proves:

```text
long turn present + short turn omitted → fail
all turns present                     → per-turn scores 1.0
```

## Resolution

`predict.continuation_lane._turn_transcript_scores` attributes edit operations
to intended turns, exposes `turn_scores`, and uses the worst turn as the gate
summary. Regression coverage is in `tests/test_continuation_lane.py`. The full
suite at `9b70be1` passed 1380 tests with one intentional skip and no
failures.
