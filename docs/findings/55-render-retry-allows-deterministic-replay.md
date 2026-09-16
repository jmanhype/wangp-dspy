
# 55 — render retry allows an unchanged deterministic replay

Status: CLOSED in PR #85 / commit `0ddfcb4`; deterministic replay rejection
is on `main`.

## Evidence

LF002 renders `0064`, `0067`, `0068`, and `0069` all used the same effective
renderer inputs at seed 904. Their raw MP4 SHA256 was identical:

```text
8731fc9f9b0c7276fa2befff6e0d3d4887d9fee8ecfd2b3bdb002881bb71fa79
```

Calling the later job a regeneration was misleading: deterministic H3 replayed
the same failure. The first materially new attempt was `render-0070`, which
changed only the seed to 905.

## Minimal fix

At queue submission, compute a content-aware effective renderer fingerprint from
model/kind/recipe/prompt/seed/profile/resolution/steps/image refs/image start/
audio guide/frame count and prompt modes. Hash real local image/WAV bytes when
available. Persist the fingerprint on each clip.

A new submission with the same fingerprint as a failed or dead-letter clip is
rejected unless it explicitly sets `allow_deterministic_replay`. Changing an
effective input, notably seed 904 to 905, produces a different fingerprint and
is accepted.

## Resolution

The initial replay guard landed in `services/jobs/queue.py` with regression
coverage in `tests/test_jobs_queue.py`. Finding #64 later canonicalized and
attempt-scoped the fingerprint without reopening unchanged deterministic
rejection. The full suite at `9b70be1` passed 1380 tests with one intentional
skip and no failures.
