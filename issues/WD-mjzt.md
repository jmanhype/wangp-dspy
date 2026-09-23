---
id: WD-mjzt
title: "Bug: isolate LF004 acceptance source resolution"
status: open
priority: 0
type: task
parent: WD-h73w
created_at: 2026-09-23T23:11:38Z
created_by: speed
updated_at: 2026-09-23T23:11:38Z
content_hash: "sha256:63e9f4aef5a4ca47fda9d90fe92eb7573a95db6b4d917545222b82aa5807ebe4"
blocked_by: [WD-td89]
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


## History
- 2026-09-23T23:11:39Z dep_added: blocked_by WD-td89

## Links
- Parent: [[WD-h73w]]
- Blocked by: [[WD-td89]]

## Comments
