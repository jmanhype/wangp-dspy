---
id: WD-dc3w
title: "Bug: FastAPI TestClient emits Starlette deprecation warning"
status: open
priority: 0
type: bug
labels: [bug, test, evidence, discovered-by-pm]
parent: WD-3nod
created_at: 2026-09-28T02:20:14Z
created_by: speed
updated_at: 2026-09-28T02:20:14Z
content_hash: "sha256:4dbc72eba36ba86eee3968d335022ae9714518800f33c216f5743b8333110484"
blocks: [WD-fay0]
follows: [WD-qswf]
---

## Description
## Context

## USER INTENT
The repository's normal test suite must be warning-clean, not merely green. A dependency deprecation warning makes every CI run noisy, hides future regressions, and violates the standing delivery rule that all warnings be owned or removed.

## Observed defect
Exact-head CI run `36350323341` and the local full suite both finish with zero failures, but pytest reports:

```text
.venv/lib/python3.12/site-packages/fastapi/testclient.py:1
  StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa
```

The affected imports are in:

- `tests/qc/audio_critic/test_slice2.py`
- `tests/qc/audio_critic/test_generate_contract.py`
- `tests/qc/audio_critic/test_pipe_waveform.py`
- `tests/qc/audio_critic/test_default_loader.py`

Current locked versions are FastAPI `0.141.1` and Starlette `1.6.0`. Starlette `1.6.0` first tries `import httpx2 as httpx`, falls back to `httpx`, and emits the warning only on fallback. The direct dev dependency is currently `httpx>=0.28.1`.

Candidate evidence:

- Current `httpx2` release: `2.13.1`.
- `uv run --frozen --extra dev --with httpx2 python -c 'import fastapi.testclient'` imports without the warning.
- The same transient `--with httpx2` layer still warns when running the project `.venv` pytest script, proving the fix must be represented in `pyproject.toml` and `uv.lock`, not applied only as an ephemeral CLI option.

## Root Cause
The test environment supplies only legacy `httpx` to Starlette TestClient. The project has no direct `httpx` imports outside its dev dependency declaration, so that direct dev dependency is pointing at the deprecated transport.

## Affected Components
- `pyproject.toml`
- `uv.lock`
- the four real FastAPI TestClient test modules named above

## OUT OF SCOPE
- GitHub Actions Node 20/action deprecation warnings: unrelated CI runtime finding; lands in a separate one-finding story.
- Production FastAPI endpoint behavior, queue admission, rendering, QC thresholds, and engine policy: no behavior change is wanted.
- Broad dependency upgrades unrelated to TestClient transport.

## DIFF BUDGET
- About 3 files and under 120 changed LOC: dependency manifest/lock, optional pytest warning guard or focused test adjustment, and evidence receipts.

## Boundary Map
PRODUCES:
- pyproject.toml -> dev dependency set containing locked-compatible `httpx2>=2.13.1` and no redundant direct legacy `httpx` dev dependency
  spec: `[project.optional-dependencies].dev` must install the non-deprecated Starlette TestClient transport.
- uv.lock -> immutable locked `httpx2` package resolution and hashes
  source: `uv lock` output for the updated dev extra.
- datasets/runs/ci-hygiene/httpx2-testclient/ -> warning-removal evidence
  event: stores focused warning-as-error output, full-suite warning scan, dependency versions, commit SHA, and exact-head CI receipt.

CONSUMES:
- (existing): tests/qc/audio_critic/test_slice2.py -> `from fastapi.testclient import TestClient`
  Pattern: instantiate the real application with `TestClient(app)` and exercise actual HTTP behavior; no mock transport is acceptable.
- (existing): .venv/lib/python3.12/site-packages/starlette/testclient.py -> import selection `try: import httpx2 as httpx; except ModuleNotFoundError: import httpx`
  Pattern: installing `httpx2` in the project dev environment removes the fallback warning at import time.

## Story Acceptance Criteria
1. [State] The project dev environment installs `httpx2>=2.13.1`; if legacy `httpx` remains directly declared, the delivery records the exact direct requirement that still needs it, otherwise the redundant dev entry is removed.
2. [State] All four real FastAPI TestClient modules pass with the Starlette deprecation warning promoted to an error, proving the warning cannot silently return.
3. [State] The undeselected full suite passes and its captured output contains zero occurrences of `StarletteDeprecationWarning`, `Using httpx with starlette.testclient is deprecated`, and `install httpx2 instead`.
4. [Unwanted] No production endpoint, queue, renderer, QC threshold, or protected engine behavior changes; no broad dependency upgrade; no warning suppression filter that hides the deprecation instead of selecting `httpx2`.
5. [State] The exact PR-head CI run completes successfully, and its downloaded log contains zero Starlette TestClient deprecation occurrences.
6. [State] `pvg lint --backlog`, `wgp release verify` with `release=ready` and `tag_created=false`, protected-file parity from base `7275e44f56c0df99e74d2a8b762b162bde07f95b`, and `git diff --check` pass.

## Testing Requirements
- Integration tests are MANDATORY with no mocks: exercise the actual FastAPI applications through `TestClient`.
- Focused warning-as-error command must include all four affected modules.
- Run the undeselected full suite and scan its complete captured stderr/stdout for the three forbidden warning strings.
- Record measured coverage for the focused warning-regression scope; do not merely write “coverage passed”.
- Require exact-head CI success and scan the downloaded GitHub Actions log for the same forbidden strings.
- Run the standard release, lint, protected-file, and diff gates.

## Delivery Requirements
- Record dependency versions before/after, lock diff, focused command/output, full-suite warning count, coverage percentage, exact CI run URL/conclusion, commit SHA, branch, and PR.
- Include `## Implementation Evidence`, `Summary:`, `Commands run:`, `SHA:`, `### CI/Test Results`, `### AC Verification`, and `LEARNINGS:`.
- Explicitly state that GitHub Actions deprecation warnings, if still present, belong to their separate story and are not dismissed as unrelated.

## MANDATORY SKILLS
- pvg

## nd_contract
status: new

### evidence
- Created from WD-qswf PM discovery and exact CI run `36350323341`; current merged base is `7275e44f56c0df99e74d2a8b762b162bde07f95b`.

### proof
- [ ] Pending dependency repair, warning-as-error proof, full-suite warning scan, coverage, CI proof, and standard delivery gates.

## Acceptance Criteria


## Design


## Notes


## History
- 2026-09-28T02:20:14Z dep_added: blocks WD-fay0

## Links
- Parent: [[WD-3nod]]
- Blocks: [[WD-fay0]]
- Follows: [[WD-qswf]]

## Comments
