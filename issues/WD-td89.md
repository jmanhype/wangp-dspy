---
id: WD-td89
title: "Bug: reconcile durable LF004 post-execution provenance"
status: closed
priority: 0
type: bug
parent: WD-h73w
created_at: 2026-09-23T21:35:44Z
created_by: speed
updated_at: 2026-09-23T22:32:05Z
content_hash: "sha256:3430869f5af1cc95e0069bce0c4eedd5abe6b94159192e9aa12c554b2125a523"
assignee: dev-WD-td89
follows: [WD-42no, WD-g125]
labels: [delivered, accepted]
closed_at: 2026-09-23T22:32:04Z
close_reason: "Accepted via pvg story accept"
---

## Description
## USER INTENT
The operator needs a stranger inspecting tracked repository evidence at the WD-h73w merged head to see the real LF004 creative outcome and reconcile the launcher that executed the film with the launcher now present, without rerunning or re-approving the film.

## Context (Embedded)
- Milestone review found two post-execution provenance-completeness defects at merged head `1f86aaa2d799bdf151376fc6e71fcf88fd2fc44e`; they are one bounded reconciliation, not two independent findings or PRs.
- Tracked `datasets/runs/pull/lf004-operator-dogfood-56f-recovery-20260921/final-provenance.json` says `status = "operator_review_pending"` and `creative_acceptance = "none"`.
- The operator decision already exists at ignored `datasets/runs/pull/lf004-operator-dogfood-56f-recovery-20260921/operator-acceptance.json` (`.gitignore:19`): `status = "operator_accepted"`, `creative_acceptance = "accepted"`, `verdict = "keep"`, and `verdict_source = 'operator message: "i approve"'`. WD-42no also records that verdict and the two exact plan approvals. This story performs durability/reconciliation only; it must not fabricate or reinterpret approval.
- Other tracked authoritative review artifacts still say pending: `datasets/lf004-operator-dogfood-56f-recovery-20260921.run_ledger.json`, `datasets/runs/pull/lf004-operator-dogfood-56f-recovery-20260921/operator_review_pending.json`, `review.md`, and current status fields in `final-provenance.json` / `postprocess-recovery.json`.
- Existing provenance records `inputs.launcher_sha256 = 419ba28c8f9ce5ce5028a66de424d7e67bbdf231724c3f586940f9f1b4720cc7`, the launcher identity captured when the recovery executed. The checkout later changed launcher wiring without changing `scripts/run_film.py`: at head `1f86aaa`, `scripts/run_film.py` SHA-256 is `9e8760927c8bd4548a1f315711e86afba42ea98d68a31632e8f257a0305f36a5` and Git blob is `f8af9b7eaee0da2a3b7af95a6845788f1c6a8aca`. Current evidence does not distinguish execution-time launcher identity from checkout identity.
- Treat historical pre-verdict states as history only. The fix must make the current authoritative state unambiguous rather than retroactively claiming the film was accepted before the operator said “i approve”.

## OUT OF SCOPE
- Any GPU, host, queue admission, model, remote-host, network, render, QC re-run, assembly, probe, or contact-sheet work: the accepted media and gate evidence are immutable; lands never.
- Changing protected engine files `services/jobs/queue.py`, `services/director/renderers/policy.py`, `services/director/wiring.py`, `services/jobs/preflight.py`, and `scripts/run_film.py`: this is evidence reconciliation, not engine behavior work; lands never in this story.
- Claiming a new or inferred creative verdict: only the existing WD-42no operator acceptance and its source may be made durable; a new decision lands never without an explicit operator message.
- Redesigning general provenance/release architecture: fix this governed LF004 evidence path and its focused tests; broader design lands in a separately triaged story.
- Modifying final media, queue DB, first-attempt evidence, accepted QC evidence, or their hashes; lands never.

## DIFF BUDGET
- About 6 files and under 250 authored changed LOC. Generated/evidence JSON changes are additional bytes but not authored implementation LOC.
- Expected implementation surfaces: LF004 recovery tooling, focused LF004 tooling tests, a tracked canonical operator-acceptance record, and the affected authoritative LF004 status/evidence documents.

## Boundary Map
PRODUCES:
- datasets/content_briefs/lf004-operator-dogfood-56f/run/recover_once.py -> `record_operator_verdict(acceptance_path: Path | None = None, output_root: Path | None = None) -> dict[str, Any]`
  spec: fail-closed, no-render, idempotent reconciliation command; reads/validates the existing acceptance record, preserves the executed launcher hash, computes checkout launcher and `scripts/run_film.py` identities, and rewrites only authoritative evidence through supported helpers.
- datasets/runs/provenance/lf004-operator-dogfood-56f-recovery-20260921/operator-acceptance.json
  schema: tracked canonical copy of `wangp-dspy.operator-acceptance/v1` with `status="operator_accepted"`, `creative_acceptance="accepted"`, `verdict="keep"`, exact `verdict_source`, artifact SHA-256 `2659ded7f48cef046741026cc476e316594689046b4a51ba6e58b7264a96e0d7`, and record SHA-256 `e10e3e2180c9570a4ed731f428bab6a2e036b94b4988bd092f943c7b2dd1c76d`.
- datasets/runs/pull/lf004-operator-dogfood-56f-recovery-20260921/final-provenance.json
  schema: current status `operator_accepted`; durable operator-verdict/source/hash fields; explicit launcher `as_executed` versus `current_checkout` identities including current `scripts/run_film.py` SHA-256 and Git blob.
- datasets/lf004-operator-dogfood-56f-recovery-20260921.run_ledger.json
  schema: current run-ledger status `operator_accepted` with reconciliation evidence while preserving immutable repository identity and final hash.
- tests/test_lf004_recovery_tooling.py
  event: real temp-file integration coverage for accepted-record success, fail-closed mismatch/source rejection, stale-pending reconciliation, launcher identity, and idempotence.

CONSUMES:
- (existing ignored source): datasets/runs/pull/lf004-operator-dogfood-56f-recovery-20260921/operator-acceptance.json -> `wangp-dspy.operator-acceptance/v1`
  source: the only pre-existing operator decision; require its recorded artifact hash and fields verbatim. In a clean checkout, the tracked canonical copy under `datasets/runs/provenance/.../operator-acceptance.json` is the replay source.
- (existing): datasets/content_briefs/lf004-operator-dogfood-56f/run/recover_once.py -> `sha(path: Path) -> str`, `write_json(path: Path, payload: dict[str, Any]) -> None`, `main(argv: list[str]) -> int`
  spec: reuse deterministic hashing and atomic JSON writing; add the new command rather than duplicating hash/serialization behavior.
- (existing): services/director/run_ledger.py -> `repository_identity(repo_root: Optional[os.PathLike[str] | str] = None) -> dict`
  source: canonical repository root/HEAD used when recording checkout identity; do not infer from cwd.
- (existing): services/director/run_ledger.py -> `write_run_ledger(path: os.PathLike[str] | str, *, run_id: str, identity: Mapping[str, str], status: str = "planned", extra: Optional[Mapping[str, object]] = None) -> Path`
  spec: supported atomic rewrite of the current ledger status; immutable historical facts must remain in `extra`.

## Story Acceptance Criteria
1. [State] Tracked evidence durably records the operator's actual decision verbatim — accepted/keep plus its exact `verdict_source` and the acceptance-record SHA-256 — and every current authoritative tracked status for this film is `operator_accepted`; no authoritative tracked artifact still presents the film as awaiting operator review. Historical pre-verdict snapshots, if retained, must be explicitly labeled as history.
2. [State] The evidence distinguishes launcher `as_executed` SHA-256 `419ba28c8f9ce5ce5028a66de424d7e67bbdf231724c3f586940f9f1b4720cc7` from the launcher identity present in the checkout at reconciliation time, and separately makes current `scripts/run_film.py` SHA-256 `9e8760927c8bd4548a1f315711e86afba42ea98d68a31632e8f257a0305f36a5` and Git blob `f8af9b7eaee0da2a3b7af95a6845788f1c6a8aca` discoverable with the recording repository HEAD. It must not claim an unrecorded execution-time hash for `scripts/run_film.py`.
3. [Unwanted] No tracked evidence is hand-edited to satisfy this story. A supported `recover_once.py` reconciliation command performs the writes, validates the final-media hash and acceptance source before changing status, and is idempotent: a second run creates no semantic change and performs no media, render, GPU, host, network, or queue work.
4. [State] `uv run --frozen --extra dev pytest -q` exits 0; `uv run --frozen --extra dev wgp release verify` reports `release=ready` and `tag_created=false`; spend-gate parity (`tests/test_spend_gate.py::test_lf004_parity_queue_join_and_live_atomic_recorder`) and WD-pn6h regression (`tests/test_spend_gate.py::test_historical_nested_worktree_paths_are_checkout_independent`) pass.
5. [Unwanted] No GPU/host/model/network work or render/probe/contact-sheet re-run occurs; final media, queue DB, accepted QC evidence, and protected engine files `services/jobs/queue.py`, `services/director/renderers/policy.py`, `services/director/wiring.py`, `services/jobs/preflight.py`, and `scripts/run_film.py` remain unchanged from `1f86aaa2d799bdf151376fc6e71fcf88fd2fc44e`.

## Testing Requirements
- Unit: validate acceptance schema, exact verdict/source, artifact and record hashes, repository/launcher identity fields, and deterministic serialization.
- Integration: MANDATORY and real (no mocks): invoke the actual reconciliation function/command against temporary copies of provenance, ledger, review, and acceptance files. Cover success, mismatched final media, mismatched acceptance hash, missing/unsupported verdict source, stale pending sidecars, changed checkout launcher identity, and repeat invocation.
- Negative: prove fail-closed behavior writes no partial accepted status when acceptance or media identity does not match, and prove a nonexistent pending sidecar cannot be silently ignored when it is authoritative.
- Commands: the two AC #4 commands plus targeted `pytest` node IDs; include exact output tails in delivery evidence.
- Artifact integrity: record pre/post SHA-256 for final media and queue DB (must match), and show `git diff --exit-code 1f86aaa2d799bdf151376fc6e71fcf88fd2fc44e --` for every protected engine file.

## MANDATORY SKILLS
- pvg — story governance, append-only evidence, delivery transition, and no-render safety.

## Delivery Requirements
- Developer must paste command output tails, acceptance/provenance/launcher hash table, protected-file parity output, and an AC verification table.
- Developer must record before/after authoritative status fields and identify every retained historical pending mention.
- Developer must use the supported reconciliation command for all evidence writes and show the second-run idempotence result.

## nd_contract
status: new

### evidence
- Created: 2026-09-23 from WD-h73w milestone-review defects at merged head `1f86aaa2d799bdf151376fc6e71fcf88fd2fc44e`.

### proof
- [ ] Pending implementation

## Acceptance Criteria


## Design


## Notes
## Implementation Evidence
### CI/Test Results
Commands run:
- Required targeted, full, spend-gate, release, protected-diff, and diff-check commands all exited 0 as detailed in the prior Implementation Evidence blocks.
Summary: PASS at commit 533ff7a471f022c28d5967130aad93e640535fa0; full JUnit tests=2005 errors=0 failures=0 skipped=1; reconciliation second run no_change.

## Implementation Evidence (DELIVERED)

### CI/Test Results
Commands run:
- timeout 300 uv run --frozen --extra dev pytest -q tests/test_lf004_recovery_tooling.py -> EXIT 0, 11 passed.
- timeout 1800 uv run --frozen --extra dev pytest -q -> EXIT 0, JUnit tests=2005 errors=0 failures=0 skipped=1.
- timeout 600 uv run --frozen --extra dev pytest -q tests/test_spend_gate.py -> EXIT 0, 19 passed.
- timeout 300 uv run --frozen --extra dev pytest -q tests/test_spend_gate.py::test_lf004_parity_queue_join_and_live_atomic_recorder tests/test_spend_gate.py::test_historical_nested_worktree_paths_are_checkout_independent -> EXIT 0, 2 passed.
- timeout 600 uv run --frozen --extra dev wgp release verify -> EXIT 0, release=ready tag_created=false.
- git diff --exit-code 1f86aaa2d799bdf151376fc6e71fcf88fd2fc44e -- services/jobs/queue.py services/director/renderers/policy.py services/director/wiring.py services/jobs/preflight.py scripts/run_film.py -> EXIT 0.
- git diff --check -> EXIT 0.
Summary: PASS; commit 533ff7a471f022c28d5967130aad93e640535fa0; canonical acceptance SHA e10e3e2180c9570a4ed731f428bab6a2e036b94b4988bd092f943c7b2dd1c76d; final media and queue DB unchanged; second reconciliation no_change.

## nd_contract
status: delivered

### evidence
- Detailed evidence, command tails, status transitions, launcher table, and AC table are in the Implementation Evidence blocks above.

### proof
- [x] AC #1: exact accepted/keep verdict is durable and current statuses are accepted.
- [x] AC #2: executed and current launcher plus run_film SHA/blob/HEAD identities are recorded.
- [x] AC #3: supported reconciliation is fail-closed and idempotent with no render work.
- [x] AC #4: required tests and release verification pass.
- [x] AC #5: immutable media/DB/QC and protected files remain unchanged.

## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-23.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## Implementation Evidence (DELIVERED)

PROOF:

### Commands and measured results
- timeout 300 uv run --frozen --extra dev pytest -q tests/test_lf004_recovery_tooling.py -> EXIT 0; 11 passed.
- timeout 1800 uv run --frozen --extra dev pytest -q -> EXIT 0; JUnit tests=2005 errors=0 failures=0 skipped=1. The only skip is tests.test_jobs_integration_3090.test_live_preflight_against_3090, gated on WANGP_3090=1 and not enabled because this story forbids host work.
- timeout 1800 uv run --frozen --extra dev pytest -q --junitxml=/tmp/WD-td89-full.xml -> EXIT 0; same counters (2005/0/0/1).
- timeout 600 uv run --frozen --extra dev pytest -q tests/test_spend_gate.py -> EXIT 0; 19 passed.
- timeout 300 uv run --frozen --extra dev pytest -q tests/test_spend_gate.py::test_lf004_parity_queue_join_and_live_atomic_recorder tests/test_spend_gate.py::test_historical_nested_worktree_paths_are_checkout_independent -> EXIT 0; 2 passed.
- timeout 600 uv run --frozen --extra dev wgp release verify -> EXIT 0; release=ready, tag_created=false, tag-ready=v0.1.0.
- git diff --exit-code 1f86aaa2d799bdf151376fc6e71fcf88fd2fc44e -- services/jobs/queue.py services/director/renderers/policy.py services/director/wiring.py services/jobs/preflight.py scripts/run_film.py -> EXIT 0, no output.
- git diff --check -> EXIT 0, no output.
- pvg verify datasets/content_briefs/lf004-operator-dogfood-56f/run/recover_once.py tests/test_lf004_recovery_tooling.py datasets/runs/provenance/lf004-operator-dogfood-56f-recovery-20260921/operator-acceptance.json --format=text -> VERIFY: PASSED (2 files scanned, 0 issues).

### Commit and push
- Branch: story/WD-td89
- SHA: 533ff7a471f022c28d5967130aad93e640535fa0
- Push: origin/story/WD-td89 succeeded.

### Reconciliation and integrity
- First supported command run: action=reconciled; status=operator_accepted; acceptance SHA-256 e10e3e2180c9570a4ed731f428bab6a2e036b94b4988bd092f943c7b2dd1c76d.
- Second supported command run: action=no_change; changed_paths=[].
- Final media pre/post SHA-256: 2659ded7f48cef046741026cc476e316594689046b4a51ba6e58b7264a96e0d7 both times.
- Queue DB pre/post SHA-256: fcefccf496ab8f1c2275271cb901528bda820708ac5f2ada09c0d349c1349ca4 both times.
- Launcher table: as_executed=419ba28c8f9ce5ce5028a66de424d7e67bbdf231724c3f586940f9f1b4720cc7; current checkout launcher=6176d944e520ca77cf1e50fc3688706de666ea534708bf5b4ea86f8477ea2858; current scripts/run_film.py SHA-256=9e8760927c8bd4548a1f315711e86afba42ea98d68a31632e8f257a0305f36a5; Git blob=f8af9b7eaee0da2a3b7af95a6845788f1c6a8aca; recording HEAD=1f86aaa2d799bdf151376fc6e71fcf88fd2fc44e.

### Status transitions
- final-provenance.json: operator_review_pending / creative_acceptance none -> operator_accepted / accepted, with durable operator_verdict and launcher_reconciliation.
- run ledger: operator_review_pending -> operator_accepted, preserving original repository and final hash.
- review.md: operator_review_pending -> operator_accepted plus explicit Pre-verdict history.
- operator_review_pending.json: pending sidecar -> status operator_accepted, record_class historical_pre_verdict_snapshot, historical_status operator_review_pending.
- postprocess-recovery.json and nested final-provenance post_execution_recovery: final_status pending -> accepted plus status_history.
- tracked canonical acceptance: absent -> datasets/runs/provenance/lf004-operator-dogfood-56f-recovery-20260921/operator-acceptance.json with SHA-256 e10e3e2180c9570a4ed731f428bab6a2e036b94b4988bd092f943c7b2dd1c76d.
- Retained historical pending mentions are explicitly labeled history at final-provenance status_history and post_execution_recovery.status_history, postprocess-recovery.status_history, operator_review_pending.historical_status, and review.md Pre-verdict history.

### AC Verification
| AC | Requirement | Evidence | Status |
| 1 | Durable verbatim verdict and accepted current statuses | Canonical acceptance plus final/ledger/review/sidecar/postprocess status fields | PASS |
| 2 | Distinguish executed and checkout launcher identities, record run_film SHA/blob/HEAD | final-provenance launcher_reconciliation and ledger operator_reconciliation | PASS |
| 3 | Supported fail-closed, no-render, idempotent reconciliation command | recover_once.py record_operator_verdict plus 11 focused tests and second-run no_change | PASS |
| 4 | Full suite, release, spend parity/regression | Commands above | PASS |
| 5 | No immutable/protected mutation | Protected diff clean; media and DB hashes unchanged | PASS |

LEARNINGS:
- The ignored operator-acceptance bytes must be preserved verbatim; deterministic re-serialization changes the record hash, so the canonical copy is byte-copied by the supported command.
- final-provenance embeds a post_execution_recovery snapshot, so both the sidecar file and nested copy needed explicit current-status/history treatment.
- The pre-existing live-3090 pytest skip cannot be enabled under this story's no-host boundary.

### OBSERVATIONS (unrelated)
- Pre-existing FastAPI/Starlette deprecation warning in .venv fastapi/testclient.py during the full suite.
- Pre-existing WANGP_3090-gated live preflight test remains skipped; enabling it would violate this story.

## nd_contract
status: delivered

### evidence
- Commit 533ff7a471f022c28d5967130aad93e640535fa0 pushed to origin/story/WD-td89.
- Focused/full/spend/release/protected/diff checks recorded above.

### proof
- [x] AC #1: operator keep verdict, exact source, acceptance hash, and accepted authoritative statuses are durable.
- [x] AC #2: executed versus checkout launcher identities and current scripts/run_film.py SHA/blob/HEAD are recorded.
- [x] AC #3: supported reconciliation is fail-closed, no-render, and idempotent.
- [x] AC #4: required tests and release verification pass.
- [x] AC #5: protected files, media, queue DB, and accepted QC evidence remain unchanged.

## nd_contract
status: in_progress

### evidence
- Claimed by dispatcher as dev-WD-td89 at 2026-09-23.
- Base HEAD: 1f86aaa2d799bdf151376fc6e71fcf88fd2fc44e.

### proof
- [ ] Pending implementation

## History
- 2026-09-23T21:38:23Z status: open -> in_progress
- 2026-09-23T21:38:23Z auto-follows: linked to predecessor WD-42no
- 2026-09-23T21:38:23Z claimed by dev-WD-td89
- 2026-09-23T22:14:29Z status: in_progress -> in_progress
- 2026-09-23T22:14:30Z auto-follows: linked to predecessor WD-g125
- 2026-09-23T22:32:04Z status: in_progress -> closed

## Links
- Parent: [[WD-h73w]]
- Follows: [[WD-42no]], [[WD-g125]]

## Comments

### 2026-09-23T22:15:57Z speed
## nd_contract
status: delivered

### evidence
- Commit 533ff7a471f022c28d5967130aad93e640535fa0; all required verification recorded in Implementation Evidence.

### proof
- [x] AC #1 through AC #5 verified.
