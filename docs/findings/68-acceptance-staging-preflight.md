# 68 — acceptance staging preflight was incomplete

Status: CLOSED in PR #99 / commit `1ae4c0e`; complete staging preflight is on
`main`.

## Evidence

Qodo review of PR #89 found three staging gaps:

1. a missing local input could fall back to an already existing mapped remote
   file;
2. a slashless relative mapping could make the destination filename be treated
   as its parent directory;
3. inputs were staged before complete bundle planning, so malformed bundles
   could create remote files and a planned ledger before rejection.

## Minimal fix

- collect every media-manifest and per-cut plate input;
- require all sources to exist locally before any remote mapping or upload;
- derive destination parents with POSIX path semantics and skip `.` parents;
- complete pure `DirectorRun.plan(..., emit_record=False)` validation before
   staging;
- emit the planned ledger only after staging succeeds;
- wrap planning rejection as typed `AcceptanceBundleError`.

This prevents invalid bundles from reaching remote staging or creating a
renderable queue.

## Resolution

`scripts/run_acceptance.py` now completes pure DirectorRun planning with
`emit_record=False`, validates every local input before mapping/upload, uses
POSIX destination semantics, and emits the ledger only after staging succeeds.
Regression coverage is in `tests/test_run_acceptance.py`. The full suite at
`9b70be1` passed 1380 tests with one intentional skip and no failures.
