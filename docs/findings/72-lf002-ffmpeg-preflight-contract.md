# 72 — LF002 ffmpeg validation parsed the wrong line and ran too late

Status: OPEN; source repair staged for review.

## Evidence

Qodo's post-merge review of PR #102 found two correctness gaps in the #71
repair:

1. The probe compared `Lavf62.3.100` against only the first line of
   `ffmpeg -version`. That line identifies the ffmpeg release, while the
   pinned identity is derived from the full `libavformat 62.  3.100` line.
   The intended local executable is therefore rejected by its own validation.
2. `run_bundle` resolved the LF002 configuration only after media staging,
   ledger emission, queue submission, and both renders. A missing or wrong
   executable wasted the expensive part of the run and left durable partial
   state before failing.

## Minimal fix

- probe the selected executable with an argv list, never a shell string;
- normalize the complete `libavformat major.minor.micro` output to
   `Lavf<major>.<minor>.<micro>`;
- compare that normalized identity exactly with the configured expectation;
- resolve and probe LF002 golden configuration immediately after validating
  `golden_canary.recipe_version`;
- reject invalid configuration before host creation, staging, planning,
  ledger emission, queue creation, or rendering;
- pass the preflight-validated identity into assembly so the executable is not
  probed redundantly after rendering.

The exact artifact canary remains the final authority.
