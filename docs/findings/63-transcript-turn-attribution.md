# 63 — multi-turn transcript scoring masks omitted dialogue

Status: OPEN; source repair staged for review.

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
