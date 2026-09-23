---
id: WD-td89
title: "Bug: reconcile durable LF004 post-execution provenance"
status: in_progress
priority: 0
type: bug
parent: WD-h73w
created_at: 2026-09-23T21:35:44Z
created_by: speed
updated_at: 2026-09-23T21:38:23Z
content_hash: "sha256:043e21d69c1fae3687308e875a0cc795d6a537d1d1aa05a6c94b036bb9dbb64d"
assignee: dev-WD-td89
follows: [WD-42no]
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


## History
- 2026-09-23T21:38:23Z status: open -> in_progress
- 2026-09-23T21:38:23Z auto-follows: linked to predecessor WD-42no
- 2026-09-23T21:38:23Z claimed by dev-WD-td89

## Links
- Parent: [[WD-h73w]]
- Follows: [[WD-42no]]

## Comments
