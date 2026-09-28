---
id: WD-dc3w
title: "Bug: FastAPI TestClient emits Starlette deprecation warning"
status: closed
priority: 0
type: bug
labels: [bug, test, evidence, discovered-by-pm, delivered, accepted]
parent: WD-3nod
created_at: 2026-09-28T02:20:14Z
created_by: speed
updated_at: 2026-09-28T05:19:59Z
content_hash: "sha256:bcf7f954c24fffe0b7099cf6dd402b8b307b6c32ab4c84ea22cab4db2584c273"
follows: [WD-qswf, WD-osfm, WD-s2nb]
assignee: dev-WD-dc3w
closed_at: 2026-09-28T05:19:58Z
close_reason: "Accepted: exact-head dependency, warning-guard, full-suite, CI, and gate evidence is complete and independently verified."
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
SHA: 7a8d9e1088abd971c7e4053721050abd00b4c0ab
## PM Decision
ACCEPTED [2026-09-28]: Evidence independently reviewed and meets the bar.

## nd_contract
status: accepted

### evidence
- Verified delivered exact head and remote PR alignment at 7a8d9e1088abd971c7e4053721050abd00b4c0ab; PR #212 diff byte-matched the local 29-file diff (SHA-256 461fb4865117c4a1e139c1ec960e439c403555d4e69a03613246c1fcfadb4a8d).
- Parsed pyproject/uv lock from base to head: direct dev dependency changes httpx>=0.28.1 to httpx2>=2.13.1; packages 119->123 with only httpcore2/httpx2/httpx2-jsfetch/truststore added, zero removals, and zero existing-version changes.
- Verified all 33 entries in the local evidence.sha256 manifest. Receipts show the legacy-warning RED failure, green guard, all four real TestClient modules plus guard passing 26/26 under warning-as-error, focused coverage 20.77% overall and 89.86% for qc/audio_critic/service.py, and the undeselected suite at 2108 passed / 1 recorded baseline skip / 0 failed / 0 errors with all forbidden warning scans zero.
- Live-fetched CI run 36378948395 / check 108790483454: completed success at the exact head, all steps success, annotations zero. The freshly downloaded log byte-matched receipt SHA-256 3d7011cee97781822ac2e9a33fb0ea2c752a5c23e31fa68a65a40c27ee5769de; exact forbidden-string counts were zero, and no Starlette/httpx warning or deprecation line was present.
- Independently confirmed uv lock --check, git diff --check, protected parity receipt (only pyproject.toml, uv.lock, and the new guard outside evidence), exact-head release=ready/tag_created=false, and delivered pvg lint/verify receipts. Tests were not rerun because the recorded proof was complete and internally consistent.

### proof
- [x] AC #1: locked dev transport is httpx2>=2.13.1 and direct legacy httpx is removed.
- [x] AC #2: all four real TestClient modules passed under warning-as-error.
- [x] AC #3: undeselected full suite passed with zero forbidden warning strings.
- [x] AC #4: no protected behavior, broad dependency upgrade, or warning suppression was introduced.
- [x] AC #5: exact PR-head CI succeeded with zero TestClient deprecations and annotations.
- [x] AC #6: lint, release, protected parity, and diff gates pass.

## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-28.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## Implementation Evidence

Summary:
- Replaced the direct dev dependency `httpx>=0.28.1` with `httpx2>=2.13.1` in `pyproject.toml` and `uv.lock`.
- Added `tests/qc/audio_critic/test_testclient_transport.py`, a clean-subprocess regression guard that installs a warning filter for `StarletteDeprecationWarning` before importing the real `fastapi.testclient`.
- The guard was first executed against the legacy environment and failed with the exact warning (`red-warning-guard.out`); after the lock update it passed (`green-warning-guard.out`).
- Legacy `httpx==0.28.1` remains transitive through dspy/openai/litellm/Hugging Face dependencies, not as a direct project requirement; `legacy-httpx-transitive-requirements.txt` records that provenance.
- Lock additions only: `httpx2==2.13.1`, `httpcore2==2.13.1`, `httpx2-jsfetch==1.0`, and `truststore==0.10.4`. No existing package version was upgraded.
- Evidence bundle: `datasets/runs/ci-hygiene/httpx2-testclient/`; exact-run receipts and `evidence.sha256` are retained locally in that bundle after the no-further-push instruction.

Commands run:
- `pvg issues show WD-dc3w --json`
- `/opt/homebrew/bin/uv lock`
- `/opt/homebrew/bin/uv run --frozen --extra dev pytest tests/qc/audio_critic/test_testclient_transport.py` (RED before dependency change: 1 failed; GREEN after: 1 passed)
- `/opt/homebrew/bin/uv run --frozen --extra dev pytest -W error tests/qc/audio_critic/test_default_loader.py tests/qc/audio_critic/test_generate_contract.py tests/qc/audio_critic/test_pipe_waveform.py tests/qc/audio_critic/test_slice2.py tests/qc/audio_critic/test_testclient_transport.py`
- `/opt/homebrew/bin/uv run --frozen --extra dev --with pytest-cov pytest -W error <same five modules> --cov=qc/audio_critic --cov-report=term-missing --cov-report=xml:datasets/runs/ci-hygiene/httpx2-testclient/coverage-focused.xml`
- `/opt/homebrew/bin/uv run --frozen --extra dev pytest -q` on CPython 3.12
- `pvg lint --backlog`
- `pvg verify pyproject.toml uv.lock tests/qc/audio_critic/test_testclient_transport.py datasets/runs/ci-hygiene/httpx2-testclient --include-tests --format=text`
- `wgp release verify --json` in a clean temporary checkout of the exact pushed head
- `git diff --name-only 7275e44f56c0df99e74d2a8b762b162bde07f95b..HEAD`
- `git diff --check 7275e44f56c0df99e74d2a8b762b162bde07f95b..HEAD`
- `gh run view 36378948395 --log`
- `gh api repos/jmanhype/wangp-dspy/check-runs/108790483454/annotations`

### CI/Test Results
- RED warning guard: 1 failed with `StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead.`
- GREEN warning guard: 1 passed.
- Focused warning-as-error run over all four named real TestClient modules plus the new guard: 26 passed, 0 failed, 0 errors, 0 skipped.
- Measured focused coverage: `qc/audio_critic/service.py` 89.86% line coverage (124/138 statements); whole `qc/audio_critic` scope 20.77% because unrelated judge/whisper/ref2va modules are not in this focused transport scope.
- Undeselected local full suite: 2108 passed, 1 pre-existing baseline skip, 0 failed, 0 errors; no deselect was used.
- Complete local full-suite output scan: `StarletteDeprecationWarning=0`, transport-deprecation message=0, `install httpx2 instead`=0, total=0.
- `pvg lint --backlog`: PASS; scanned 147 issues, 0 errors, 0 review findings.
- `pvg verify`: PASS; 1 file scanned, 0 issues.
- Protected parity from base `7275e44f56c0df99e74d2a8b762b162bde07f95b` to head `7a8d9e1088abd971c7e4053721050abd00b4c0ab`: protected_changed=0; only non-evidence code paths are `pyproject.toml`, `uv.lock`, and the new test guard.
- `git diff --check 7275e44f56c0df99e74d2a8b762b162bde07f95b..7a8d9e1088abd971c7e4053721050abd00b4c0ab`: PASS.
- Exact-head CI run 36378948395 at `7a8d9e1088abd971c7e4053721050abd00b4c0ab`: SUCCESS in 22m13s.
- Exact-head downloaded CI log scan: all three forbidden warning strings = 0; check-run annotations = 0 (`[]`).
- Exact-head release verification: `release=ready`, `tag_created=false`, clean-tree commit SHA `7a8d9e1088abd971c7e4053721050abd00b4c0ab`.
- Exact CI URL: https://github.com/jmanhype/wangp-dspy/actions/runs/36378948395
- Exact receipt hashes:
  - log SHA256 `3d7011cee97781822ac2e9a33fb0ea2c752a5c23e31fa68a65a40c27ee5769de`
  - run JSON SHA256 `7051d899d0453fafcbdeb60b0b141369b288438199942b17d293e551bf6e424d`
  - annotations JSON SHA256 `4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945`

### Commit
- Branch: `story/WD-dc3w`
- SHA: `7a8d9e1088abd971c7e4053721050abd00b4c0ab`
- PR: https://github.com/jmanhype/wangp-dspy/pull/212
- CI: exact-head `test` check SUCCESS at the SHA above.

### AC Verification
| AC # | Requirement | Result |
|---|---|---|
| 1 | Dev environment installs `httpx2>=2.13.1`; direct legacy dev `httpx` is removed | PASS — `pyproject.toml`/`uv.lock`; indirect legacy `httpx` provenance recorded |
| 2 | All four real TestClient modules pass with Starlette warning as error | PASS — 26 focused tests passed under `-W error`, including all four named modules and the guard |
| 3 | Undeselected full suite passes with zero forbidden warning strings | PASS — 2108 passed / 1 baseline skip / 0 failed; scan total 0 |
| 4 | No production/protected behavior change, broad upgrade, or suppression filter | PASS — protected_changed=0; no existing package version changed; guard promotes rather than suppresses |
| 5 | Exact PR-head CI success and downloaded log contains zero TestClient deprecations | PASS — run 36378948395 SUCCESS; log and annotations contain 0 |
| 6 | Lint, release, protected parity, and diff gates pass | PASS — outputs above |

LEARNINGS:
- Python's command-line `-W` category parser cannot import a fully qualified third-party warning class; the reliable guard sets `warnings.simplefilter('error', StarletteDeprecationWarning)` inside a clean subprocess before importing `fastapi.testclient`.
- Capturing a full-suite run directly into a tracked evidence file dirties the repository and makes the release-readiness tests fail on their own evidence; run from a clean tree to `/tmp`, then copy the immutable receipt.
- Raw GitHub Actions logs can contain trailing whitespace; normalize evidence-only logs before committing so the branch-level `git diff --check` gate remains clean.
- GitHub Actions runtime deprecations, if they recur, are explicitly WD-s2nb's separate finding; this exact-head log and annotation scan observed none.

## nd_contract
status: delivered

### evidence
- Commit `7a8d9e1088abd971c7e4053721050abd00b4c0ab`; PR #212; exact-head CI run 36378948395 SUCCESS.
- Local evidence bundle `datasets/runs/ci-hygiene/httpx2-testclient/` contains focused/full-suite outputs, coverage XML/data, dependency inventories, lock diff, lint/release/parity receipts, exact CI log/annotations, and SHA256 manifest.

### proof
- [x] AC #1: `httpx2>=2.13.1` is the direct dev dependency and legacy direct `httpx` is removed.
- [x] AC #2: all four real TestClient modules passed under warning-as-error coverage.
- [x] AC #3: undeselected full suite passed and complete output scan found zero forbidden strings.
- [x] AC #4: no protected behavior, broad upgrade, or warning suppression was introduced.
- [x] AC #5: exact PR-head CI succeeded and downloaded log/annotations found zero TestClient deprecations.
- [x] AC #6: lint, release, protected parity, and diff gates passed.

## History
- 2026-09-28T02:20:14Z dep_added: blocks WD-fay0
- 2026-09-28T02:22:41Z status: open -> in_progress
- 2026-09-28T02:22:41Z auto-follows: linked to predecessor WD-osfm
- 2026-09-28T02:22:41Z claimed by dev-WD-dc3w
- 2026-09-28T05:10:00Z status: in_progress -> in_progress
- 2026-09-28T05:10:00Z auto-follows: linked to predecessor WD-s2nb
- 2026-09-28T05:19:58Z status: in_progress -> closed
- 2026-09-28T05:19:58Z dep_removed: no_longer_blocks WD-fay0

## Links
- Parent: [[WD-3nod]]
- Follows: [[WD-qswf]], [[WD-osfm]], [[WD-s2nb]]

## Comments
