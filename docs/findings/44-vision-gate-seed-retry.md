# Finding #44 — probabilistic visual-gate misses need bounded reseed retries

## Symptom

The live acceptance run produced a valid, fully rendered cut whose visual
judge correctly rejected speaker attribution (`mouth_sync/action_match/
speaker_attribution = 0`). The recipe is stochastic: the dungeon runs showed
that attribution can flip on a reseed. Treating the first miss as terminal
would therefore discard a recoverable cut, while blindly retrying every QC
exception would hide Whisper, transport, and malformed-response failures.

## Root cause

`JobExecutor._qc_clips()` treated every typed QC exception as terminal. There
was no policy distinguishing the judge's explicit `visual gate failed` result
from a judge outage, and no durable per-seed attempt trail.

## Fix (landed)

`JobExecutor` now recognizes only the explicit visual-gate rejection, records
the failed seed and artifact paths, bumps the clip seed by one, clears the
render/QC claims, and appends a new queue attempt with a reason. The default
budget is two retries (`WANGP_VISION_RETRIES`); a third miss is terminal/dead
letter and retains all prior attempt evidence. Different seeds are included
in failure signatures so the queue's same-signature loop guard remains active
for accidental deterministic repeats. Missing/invalid seeds and all other QC
errors still fail closed without a retry.

## Acceptance

The executor regression test verifies seed `41 → 42 → 43`, immutable attempt
history/reasons, preserved prior mp4/log evidence, and terminal failure after
the third visual miss. A non-visual vision-service timeout is asserted to
remain non-retryable.
