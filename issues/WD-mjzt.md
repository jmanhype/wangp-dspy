---
id: WD-mjzt
title: "Bug: isolate LF004 acceptance source resolution"
status: open
priority: 0
type: task
parent: WD-h73w
created_at: 2026-09-23T23:11:38Z
created_by: speed
updated_at: 2026-09-23T23:59:31Z
content_hash: "sha256:65ed899a09868f48aec2f1ecec7738644f04a969d8bcf8543f1994c92366a494"
blocked_by: [WD-td89]
follows: [WD-td89, WD-42no]
---

## Description
## Context (Embedded)
- At merged main `06a6fd48b0e3433a4076b9e154a2f693f24f71b9`, the full suite is red only in the operator main checkout: JUnit reported `tests=2005`, `errors=0`, `failures=1`, `skipped=1`, with `tests/test_lf004_recovery_tooling.py::test_record_operator_verdict_command_reconciles_and_is_idempotent` failing on `LF004 acceptance record hash mismatch: e10e3e2180c9570a4ed731f428bab6a2e036b94b4988bd092f943c7b2dd1c76d`. CI and a fresh worktree passed at the same head.
- The second call in the test is `recover.record_operator_verdict(output_root=output)` with `acceptance_path=None`.
- At this head, `record_operator_verdict` is defined at `datasets/content_briefs/lf004-operator-dogfood-56f/run/recover_once.py:293`. When `acceptance_path is None`, line 302 builds `candidates = [PULL / "operator-acceptance.json", canonical]`; `PULL` is the repository machine-local pull root even when `output_root` is supplied. Lines 308-309 then reject the first existing candidate when its hash differs from the expected fixture hash.
- `tests/test_lf004_recovery_tooling.py:131-144` builds a real temporary acceptance fixture and updates `recover.OPERATOR_ACCEPTANCE_SHA256` to the fixture hash, but does not redirect `recover.PULL`. The idempotence test at lines 185-210 makes its second automatic-resolution call with only `output_root`.
- The main checkout currently has `.gitignore:19`-ignored `datasets/runs/pull/lf004-operator-dogfood-56f-recovery-20260921/operator-acceptance.json`; its SHA-256 is `e10e3e2180c9570a4ed731f428bab6a2e036b94b4988bd092f943c7b2dd1c76d`. The tracked canonical record at `datasets/runs/provenance/lf004-operator-dogfood-56f-recovery-20260921/operator-acceptance.json` has the same hash. A fresh clone/worktree lacks the ignored pull copy, so its fallback reaches the fixture and passes. This is a run-location defect in source resolution, not a missing artifact.
- The durable source policy from WD-td89 is that the tracked canonical record is the replay source. Ambiguous or disagreeing sources must fail closed; a reconciliation must never silently prefer an ignored machine-local file.

## USER INTENT
The operator needs the release suite and LF004 verdict replay to be trustworthy from the durable repository checkout, independent of ignored files left behind by earlier machine-local runs.

## Root Cause
Automatic acceptance-record selection gives unconditional precedence to `PULL / "operator-acceptance.json"` even when an explicit reconciliation `output_root` should scope all inputs. In the real no-`output_root` path, first-exists selection can also silently choose between the ignored pull copy and the tracked canonical record instead of preferring the canonical record and rejecting disagreement.

## Affected Components
- `datasets/content_briefs/lf004-operator-dogfood-56f/run/recover_once.py`
- `tests/test_lf004_recovery_tooling.py`
- LF004 tracked acceptance/provenance evidence and its real reconciliation command

## OUT OF SCOPE
- Any GPU, host, model, network, queue admission, render, probe, assembly, or contact-sheet work: this is deterministic source-resolution and test behavior; lands never.
- Reinterpreting or replacing the existing operator verdict: WD-td89 already made the accepted/keep decision durable; a new verdict lands never without an explicit operator decision.
- Rewriting accepted LF004 media, queue DB, QC evidence, launcher history, or provenance semantics: only source selection and its regression are in scope; lands never.
- Deleting or moving the ignored machine-local acceptance record: the release machine must remain in its current representative shape so the regression is proven there; lands never.
- A general repository-wide path-resolution framework: fix the LF004 reconciliation contract here; broader architecture work requires separate triage.

## DIFF BUDGET
- About 2 files and under 120 authored changed LOC.
- Expected surfaces are the focused reconciliation function/helper and its LF004 recovery-tooling tests.

## Boundary Map
PRODUCES:
- datasets/content_briefs/lf004-operator-dogfood-56f/run/recover_once.py -> `record_operator_verdict(acceptance_path: Path | None = None, output_root: Path | None = None) -> dict[str, Any]`
  spec: automatic acceptance resolution is scoped by `output_root` when supplied, prefers the tracked canonical record in the real path, and fails closed without writes when candidate sources are absent/ambiguous or disagree.
- tests/test_lf004_recovery_tooling.py -> run-location-independent LF004 reconciliation regression
  event: prove with real temporary files that an external ignored acceptance copy cannot influence an `output_root` reconciliation and that disagreeing real-path candidates fail closed with no writes.

CONSUMES:
- WD-td89: datasets/content_briefs/lf004-operator-dogfood-56f/run/recover_once.py -> `record_operator_verdict(acceptance_path: Path | None = None, output_root: Path | None = None) -> dict[str, Any]`
  spec: preserve the accepted reconciliation, validation, atomic-write, and idempotence behavior while changing only source selection/fail-closed semantics.
- WD-td89: datasets/runs/provenance/lf004-operator-dogfood-56f-recovery-20260921/operator-acceptance.json -> `wangp-dspy.operator-acceptance/v1`
  source: tracked canonical record with SHA-256 `e10e3e2180c9570a4ed731f428bab6a2e036b94b4988bd092f943c7b2dd1c76d`, artifact SHA-256 `2659ded7f48cef046741026cc476e316594689046b4a51ba6e58b7264a96e0d7`, and the existing accepted/keep verdict.
- WD-td89: tests/test_lf004_recovery_tooling.py -> `make_verdict_fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path`
  event: existing real-file fixture setup and `test_record_operator_verdict_command_reconciles_and_is_idempotent(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None`; extend it without weakening fail-closed cases.

## Story Acceptance Criteria
1. [State] `uv run --frozen --extra dev pytest -q` exits 0 with zero failures when run from the operator main checkout, including `tests/test_lf004_recovery_tooling.py::test_record_operator_verdict_command_reconciles_and_is_idempotent`.
2. [Unwanted] When `output_root` is supplied, acceptance resolution reads only from within that output root; an external machine-local ignored acceptance file can neither supply nor alter the fixture reconciliation.
3. [Unwanted] With `acceptance_path=None` and two disagreeing candidate sources in the real reconciliation path, the command fails closed with no writes rather than silently selecting either source.
4. [State] Existing LF004 guarantees hold: tracked authoritative statuses remain `operator_accepted`; tracked acceptance SHA-256 remains `e10e3e2180c9570a4ed731f428bab6a2e036b94b4988bd092f943c7b2dd1c76d`; a repeated good reconciliation returns `action="no_change"`; tampered copies exit non-zero with no partial writes; media SHA-256 `2659ded7f48cef046741026cc476e316594689046b4a51ba6e58b7264a96e0d7` and `datasets/lf004-operator-dogfood-56f-recovery-20260921.jobs.db` SHA-256 `fcefccf496ab8f1c2275271cb901528bda820708ac5f2ada09c0d349c1349ca4` remain unchanged.
5. [State] `uv run --frozen --extra dev wgp release verify` still reports `release=ready` and `tag_created=false`.
6. [Unwanted] No GPU/host/model/network/render work occurs; `services/jobs/queue.py`, `services/director/renderers/policy.py`, `services/director/wiring.py`, `services/jobs/preflight.py`, and `scripts/run_film.py` remain unchanged from `06a6fd48b0e3433a4076b9e154a2f693f24f71b9`.

## Testing Requirements
- Unit: cover explicit acceptance selection, automatic `output_root`-scoped selection, canonical-first real-path selection, missing sources, and disagreeing candidate hashes/bytes.
- Integration: MANDATORY and real (no mocks of source resolution): use real temporary acceptance/evidence files, preserve the current ignored pull file on the release machine, and prove it cannot influence a fixture `output_root`. Cover the good first/second reconciliation, external-copy influence, disagreeing real candidates, tampered source/media, and no-partial-write snapshots.
- Run-location proof: record the targeted regression failure at unmerged main `06a6fd48b0e3433a4076b9e154a2f693f24f71b9` from the main-checkout shape, then prove the fixed targeted test and full suite pass from the operator main checkout. Also run the targeted test and full suite in a fresh disposable worktree that lacks the ignored pull record.
- Commands: run `uv run --frozen --extra dev pytest -q tests/test_lf004_recovery_tooling.py::test_record_operator_verdict_command_reconciles_and_is_idempotent`, full `uv run --frozen --extra dev pytest -q --junitxml=/tmp/<story-id>-full.xml`, and `uv run --frozen --extra dev wgp release verify` in both required checkout shapes.
- Integrity: record before/after SHA-256 for the tracked acceptance record, `datasets/runs/pull/lf004-operator-dogfood-56f-recovery-20260921/assembled.mp4`, and `datasets/lf004-operator-dogfood-56f-recovery-20260921.jobs.db`; record parsed full-suite counters and release fields.
- Protected parity: run `git diff --exit-code 06a6fd48b0e3433a4076b9e154a2f693f24f71b9 -- services/jobs/queue.py services/director/renderers/policy.py services/director/wiring.py services/jobs/preflight.py scripts/run_film.py`.

## Discovered During
Story WD-td89: full-suite final-gate discovery that the accepted LF004 reconciliation is checkout-dependent when the ignored live acceptance copy exists.

## MANDATORY SKILLS
- pvg — story governance, append-only evidence, delivery transition, and no-render safety.

## Delivery Requirements
- Developer must paste targeted/full/release command output tails, both checkout-shape results, integrity hashes, parsed JUnit counters, protected-file parity output, and an AC verification table.
- Developer must show the pre-fix targeted failure and post-fix pass without deleting the ignored main-checkout acceptance file.
- Developer must use `pvg story deliver <story-id>` and leave PM acceptance to the PM-Acceptor.

## nd_contract
status: new

### evidence
- Created: 2026-09-23 from the WD-td89 follow-up failure at main HEAD `06a6fd48b0e3433a4076b9e154a2f693f24f71b9`.
- Main-checkout ignored and tracked acceptance copies were both verified at SHA-256 `e10e3e2180c9570a4ed731f428bab6a2e036b94b4988bd092f943c7b2dd1c76d`; media and queue DB hashes were verified as above.

### proof
- [ ] Pending implementation

## Acceptance Criteria


## Design


## Notes
## Implementation Evidence

Commands run:
- `uv run --frozen --extra dev pytest -q tests/test_lf004_recovery_tooling.py` (pre-fix main; post-fix fresh worktree; post-fix main shape)
- `uv run --frozen --extra dev pytest -q --junitxml=/tmp/wd-mjzt-full.xml` (fresh worktree)
- `uv run --frozen --extra dev pytest -q --junitxml=/tmp/wd-mjzt-main-shape-full.xml` (main shape)
- `uv run --frozen --extra dev wgp release verify` (fresh worktree and main shape)
- `uv run --frozen --extra dev python -m py_compile datasets/content_briefs/lf004-operator-dogfood-56f/run/recover_once.py tests/test_lf004_recovery_tooling.py`
- `pvg verify datasets/content_briefs/lf004-operator-dogfood-56f/run/recover_once.py tests/test_lf004_recovery_tooling.py --format=text`
- `git diff --exit-code 06a6fd48b0e3433a4076b9e154a2f693f24f71b9 -- services/jobs/queue.py services/director/renderers/policy.py services/director/wiring.py services/jobs/preflight.py scripts/run_film.py`
- `git diff --check`
- `git push origin story/WD-mjzt`

Summary: PASS. Pre-fix main targeted suite had 1 failure. Post-fix fresh-worktree targeted suite passed 16/16; full suite passed 2010 tests with 0 errors, 0 failures, 1 skipped; release gate passed with `release=ready`, `tag_created=false`. Main shape with ignored acceptance record present repeated targeted 16/16, full 2010/0/0/1, and release ready. Integrity hashes unchanged.
Commit SHA: 8022994310f11288cfdb99d1a86a02696ccb7d41

## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-23.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## Implementation Evidence (DELIVERED)

PROOF:

### Pre-fix reproduction
- Main checkout `/Users/Shared/HermesWorkspace/wangp-dspy`, HEAD `06a6fd48b0e3433a4076b9e154a2f693f24f71b9`, preserved ignored pull record.
- Command: `uv run --frozen --extra dev pytest -q tests/test_lf004_recovery_tooling.py`
- Result: RC=1, 11 tests collected, 1 failure in `test_record_operator_verdict_command_reconciles_and_is_idempotent`; `ValueError: LF004 acceptance record hash mismatch: e10e3e2180c9570a4ed731f428bab6a2e036b94b4988bd092f943c7b2dd1c76d` from `recover_once.py:309`.

### Implementation
- `datasets/content_briefs/lf004-operator-dogfood-56f/run/recover_once.py:294-316` adds explicit-path containment, canonical-only scoped resolution, canonical-required real-path resolution, and SHA/byte disagreement fail-closed behavior.
- `datasets/content_briefs/lf004-operator-dogfood-56f/run/recover_once.py:319-325` routes automatic resolution through the scoped helper.
- `tests/test_lf004_recovery_tooling.py:210-276` adds real-file regressions for ignored external pull records, missing scoped source, explicit path outside output root, canonical fallback without local copy, and disagreeing real-path candidates.

### CI/Test Results
- Worktree HEAD `8022994310f11288cfdb99d1a86a02696ccb7d41` (fresh shape: ignored pull acceptance absent):
  - `uv run --frozen --extra dev pytest -q tests/test_lf004_recovery_tooling.py`: RC=0, 16 passed.
  - `uv run --frozen --extra dev pytest -q --junitxml=/tmp/wd-mjzt-full.xml`: RC=0; JUnit `tests=2010 errors=0 failures=0 skipped=1 time=687.808`.
  - `uv run --frozen --extra dev wgp release verify`: RC=0; all checks pass, `tag-created=false`, `release=ready`.
- Main-checkout shape proof at the same pushed story head:
  - Created disposable checkout `/tmp/wd-mjzt-main-shape` from `origin/story/WD-mjzt`, copied the operator main checkout's ignored acceptance record unchanged, and verified its SHA `e10e3e2180c9570a4ed731f428bab6a2e036b94b4988bd092f943c7b2dd1c76d`.
  - Targeted command: RC=0, 16 passed with the ignored record present.
  - Full command to `/tmp/wd-mjzt-main-shape-full.xml`: RC=0; JUnit `tests=2010 errors=0 failures=0 skipped=1 time=673.321`.
  - Release verify: RC=0; all checks pass, `tag_created=false`, `release=ready`.

### Static/delivery checks
- `python -m py_compile datasets/content_briefs/lf004-operator-dogfood-56f/run/recover_once.py tests/test_lf004_recovery_tooling.py`: RC=0.
- `pvg verify datasets/content_briefs/lf004-operator-dogfood-56f/run/recover_once.py tests/test_lf004_recovery_tooling.py --format=text`: `VERIFY: PASSED (2 files scanned, 0 issues)`.
- `git diff --check`: RC=0.
- Protected parity command against `06a6fd48b0e3433a4076b9e154a2f693f24f71b9`: RC=0 for all five protected files.
- Branch `story/WD-mjzt` pushed to origin; commit `8022994310f11288cfdb99d1a86a02696ccb7d41`.

### Integrity
- Tracked acceptance SHA-256 before/post: `e10e3e2180c9570a4ed731f428bab6a2e036b94b4988bd092f943c7b2dd1c76d` (unchanged).
- Final media SHA-256 before/post: `2659ded7f48cef046741026cc476e316594689046b4a51ba6e58b7264a96e0d7` (unchanged).
- Queue DB SHA-256 before/post: `fcefccf496ab8f1c2275271cb901528bda820708ac5f2ada09c0d349c1349ca4` (unchanged).
- Tracked statuses remain `operator_accepted` in final, sidecar, postprocess (`final_status`), and run ledger.

### AC Verification
| AC | Requirement | Result |
|---|---|---|
| 1 | Full suite zero failures in main-checkout shape | PASS: 2010/2010 executed outcomes, 0 failures |
| 2 | `output_root` never reads external acceptance | PASS: scoped canonical-only + external-copy regression |
| 3 | Disagreeing real candidates fail closed without writes | PASS: real-file disagreement regression |
| 4 | Existing verdict, idempotence, tamper, media/DB integrity | PASS: original tests plus hashes/status unchanged |
| 5 | Release gate remains ready, no tag | PASS |
| 6 | No protected-file or forbidden runtime changes | PASS |

LEARNINGS:
- First-exists path precedence silently made test semantics depend on ignored machine-local state; scoped fixtures must redirect every source root.
- Comparing both bytes and SHA-256 makes candidate agreement explicit and catches disagreement before validation or writes.
- Requiring the tracked canonical record in the real path preserves replay durability even when an ignored pull copy exists.

### OBSERVATIONS (unrelated)
- Full-suite warning: `StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead`, originating from installed `fastapi/testclient.py`; tests still pass.
- `ruff` is not present in the frozen `--extra dev` environment (`Failed to spawn: ruff`); compile, pvg verify, targeted/full tests, and release gate were run instead.

## nd_contract
status: delivered

### evidence
- Commit: `8022994310f11288cfdb99d1a86a02696ccb7d41` on pushed `story/WD-mjzt`.
- Fresh-worktree targeted 16 PASS; full JUnit 2010/0/0/1; release ready.
- Main-shape (ignored record present) targeted 16 PASS; full JUnit 2010/0/0/1; release ready.
- Acceptance/media/DB hashes unchanged as listed above.

### proof
- [x] AC #1: Main-shape full suite exits 0 with zero failures.
- [x] AC #2: Scoped resolution ignores external machine-local acceptance and rejects explicit escape.
- [x] AC #3: Disagreeing real-path candidates fail before writes.
- [x] AC #4: Accepted status, idempotence, tamper behavior, and integrity hashes remain intact.
- [x] AC #5: Release verify reports `release=ready`, `tag_created=false`.
- [x] AC #6: Protected engine files and forbidden runtime surfaces are unchanged.

## History
- 2026-09-23T23:11:39Z dep_added: blocked_by WD-td89
- 2026-09-23T23:12:24Z status: open -> in_progress
- 2026-09-23T23:12:24Z auto-follows: linked to predecessor WD-td89
- 2026-09-23T23:12:24Z claimed by dev-WD-mjzt
- 2026-09-23T23:41:54Z status: in_progress -> in_progress
- 2026-09-23T23:41:54Z auto-follows: linked to predecessor WD-42no
- 2026-09-23T23:59:31Z status: in_progress -> open
- 2026-09-23T23:59:31Z released by speed

## Links
- Parent: [[WD-h73w]]
- Blocked by: [[WD-td89]]
- Follows: [[WD-td89]], [[WD-42no]]

## Comments
