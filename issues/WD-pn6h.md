---
id: WD-pn6h
title: "Spend-gate canonical paths leak nested worktree prefixes"
status: in_progress
priority: 0
type: bug
parent: WD-as25
created_at: 2026-09-23T18:47:35Z
created_by: speed
updated_at: 2026-09-23T19:10:47Z
content_hash: "sha256:35a17472d1727cbc343679c2bdfa486be962e22829f288c4f13ac86e8924c332"
blocks: [WD-l48s]
assignee: dev-WD-pn6h
follows: [WD-v6xp, WD-rf1a]
labels: [delivered]
---
## Description
## Context
At merged main `8c67a01`, the full suite is RED in the operator's main checkout. The WD-h73w completion gate requires the full suite to pass on merged main, so this regression blocks release confidence even though a clean CI clone can pass.

Measured failure:

```text
uv run --frozen --extra dev pytest -q --junitxml=/tmp/main-gate.xml
tests=1991 errors=0 failures=1 skipped=1
tests/test_spend_gate.py::test_lf004_parity_queue_join_and_live_atomic_recorder FAILED
tests/test_spend_gate.py:57
```

The failing assertion is:

```python
assert all(row[key] == value for key, value in comparable.items()) and row["queue_join_status"] == "matched"
```

## USER INTENT
The operator must be able to release Wangp from the authoritative main checkout and trust the same spend-gate evidence identity in the main checkout, a nested story worktree, a clean clone, and a foreign repository root. A path recorded while rendering must never make the repository's release gate depend on which checkout later verifies it.

## Root Cause
`services/jobs/spend_gate.py::_canonical_stored_path(value: Any, repository_root: Path) -> Any` first tries `resolved.relative_to(repository_root)`. If an absolute historical path is physically under the main repository but beneath `.claude/worktrees/`, that branch returns the nested-checkout prefix as part of the stored relative path. Only the fallback branch strips to the stable `datasets` or `assets` anchor.

Independent proof at `8c67a01` for this recorded path:

```text
/Users/Shared/HermesWorkspace/wangp-dspy/.claude/worktrees/dev-WD-g125/datasets/runs/pull/acceptance/worker-511ee9ee6a8f/render-0000/qc-evidence.json
```

produced:

```text
repository_root = main checkout
  -> .claude/worktrees/dev-WD-g125/datasets/runs/pull/acceptance/worker-511ee9ee6a8f/render-0000/qc-evidence.json

repository_root = nested worktree
  -> datasets/runs/pull/acceptance/worker-511ee9ee6a8f/render-0000/qc-evidence.json

repository_root = foreign path
  -> datasets/runs/pull/acceptance/worker-511ee9ee6a8f/render-0000/qc-evidence.json
```

This contradicts the function's stated intent never to persist the machine or checkout that wrote evidence. The committed LF004 final provenance contains equivalent absolute paths under `.claude/worktrees/dev-WD-g125`; therefore parity passes when canonicalized from a clean/foreign root but fails when `repository_root` is the operator main checkout.

## Affected Components
- `services/jobs/spend_gate.py`
- `tests/test_spend_gate.py`
- `scripts/build_spend_gate_corpus.py`
- `datasets/spend-gate/v1/corpus.jsonl`
- `datasets/spend-gate/v1/manifest.json`
- `datasets/runs/pull/lf004-operator-dogfood-56f-recovery-20260921/final-provenance.json`
- `wgp release verify`

## OUT OF SCOPE
- Changes to `services/jobs/queue.py`, `services/director/renderers/policy.py`, `services/director/wiring.py`, `services/jobs/preflight.py`, or `scripts/run_film.py`: these protected engine files are explicitly forbidden for this bug and receive no changes here.
- Queue-join, retry, or attempt-count semantic redesign: this bug concerns stored-path canonicalization; existing LF004 assertions continue to enforce queue behavior.
- GPU, remote-host, model, render, or network work: no rendering or host access is needed to normalize and replay committed evidence.
- Replay policy tuning, threshold changes, or model recalibration: only deterministic artifact regeneration required by canonical paths is allowed; policy work needs a separate story.
- Introducing a new spend-gate schema or rewriting all historical provenance: preserve the current versioned schema unless deterministic drift verification proves a narrowly required artifact update.

## DIFF BUDGET
- Approximately 2-7 files, under 500 total changed LOC; implementation and tests should remain under 250 changed LOC.
- Regenerated versioned artifact lines are included in the file-count budget but must be mechanically derived, not hand-edited.

## Boundary Map
PRODUCES:
- services/jobs/spend_gate.py -> `_canonical_stored_path(value: Any, repository_root: Path) -> Any`
  spec: a recorded absolute path containing a stable `datasets` or `assets` anchor canonicalizes to the same checkout-independent suffix for main-checkout, nested-worktree, and foreign roots, and never emits a `.claude/worktrees/` segment.
- tests/test_spend_gate.py -> an automated regression test for the exact recorded path and three repository-root cases
  spec: assert one identical expected `datasets/runs/.../qc-evidence.json` value and recursively reject `.claude/worktrees/` in canonicalized path fields.
- datasets/spend-gate/v1/corpus.jsonl -> deterministic canonical rows, only if regeneration is required by the corrected normalization
  schema: `wangp-dspy.spend-gate-row/v1`, unchanged except for checkout-dependent path correction.
- datasets/spend-gate/v1/manifest.json -> deterministic matching corpus hash and row count, only if the corpus changes
  schema: `wangp-dspy.spend-gate-manifest/v1` with `verify_artifact(...)` passing.

CONSUMES:
- (existing): services/jobs/spend_gate.py -> `_canonicalize_paths(value: Any, repository_root: Path) -> Any`
  spec: recursively applies `_canonical_stored_path(...)` to fields named `path`, `filename`, or ending in `_path`; the regression must exercise this public recursion over real LF004 cuts.
- (existing): services/jobs/spend_gate.py -> `verify_artifact(output_dir: Path) -> dict[str, Any]`
  spec: validates corpus SHA-256, schema-drift SHA-256, declared row count, and manifest SHA-256; it must return successfully after any artifact regeneration.
- (existing): scripts/build_spend_gate_corpus.py -> `main(argv: Sequence[str] | None = None) -> int`
  source: CLI supports `--repository-root`, `--evidence-mode {tracked,all-local}`, `--output-dir`, `--replay`, and `--verify-artifact`; deterministic regeneration uses this entry point rather than manual JSON edits.
- (existing): `wgp release verify`
  endpoint: local release command must exit successfully and report `tag_created=false`, `release=ready`; no tag creation is authorized.

## Required Outcomes
1. [State] When the main checkout is at the story head, `uv run --frozen --extra dev pytest -q` exits 0 with zero failures, and `tests/test_spend_gate.py::test_lf004_parity_queue_join_and_live_atomic_recorder` passes.
2. [State] When the exact recorded absolute path above is canonicalized with `repository_root` equal to the main checkout, its nested worktree, and a foreign path, the system returns one identical checkout-independent value (`datasets/runs/pull/acceptance/worker-511ee9ee6a8f/render-0000/qc-evidence.json`); an automated regression test must prove all three cases.
3. [Unwanted] After canonicalization, no canonicalized path field anywhere in `datasets/spend-gate/v1/corpus.jsonl`, and no path field in the LF004 final-provenance cuts, contains a `.claude/worktrees/` segment; violations must fail a real test.
4. [Unwanted] If the committed corpus or manifest must change, the implementation regenerates the affected versioned artifacts deterministically with `scripts/build_spend_gate_corpus.py`, `verify_artifact` passes, and corpus, manifest, replay output, and LF004 provenance remain consistent with no silent hand-edited divergence.
5. [State] When `uv run --frozen --extra dev wgp release verify` runs from the story head, it reports `tag_created=false` and `release=ready`.
6. [Unwanted] The existing LF004 queue-join status and attempt-count assertions, including the expected `[2, 0, 0, 0]` attempt sequence, remain intact and passing; queue semantics are not relaxed or replaced.

## Testing Requirements
- Unit: canonicalize the exact recorded path with all three roots; recursively canonicalize real LF004 provenance cuts; assert stable anchor behavior and reject `.claude/worktrees/` in every canonicalized path field.
- Integration: MANDATORY, no mocks. Use the committed corpus, committed LF004 provenance, real corpus-builder subprocess path where applicable, and the real release verifier.
- Negative/fail-closed: any corpus/manifest hash, row-count, replay, or provenance divergence must fail rather than silently selecting a different root.
- Commands to run:
  - `uv run --frozen --extra dev pytest -q tests/test_spend_gate.py`
  - `uv run --frozen --extra dev pytest -q`
  - `uv run --frozen --extra dev python scripts/build_spend_gate_corpus.py --repository-root . --evidence-mode all-local --output-dir datasets/spend-gate/v1 --replay --verify-artifact`
  - `uv run --frozen --extra dev wgp release verify`
  - `git diff --exit-code main -- services/jobs/queue.py services/director/renderers/policy.py services/director/wiring.py services/jobs/preflight.py scripts/run_film.py`
  - `git diff --check`

## Discovered During
- WD-h73w merged-main full-suite completion gate at repository HEAD `8c67a01`.
- Natural subsystem lineage: accepted WD-as25/WD-v6xp spend-gate seam; parent epic reopened because this defect invalidates its checkout-independent normalized-evidence outcome.

## MANDATORY SKILLS
- pvg

## Delivery Requirements
- Paste exact targeted/full-suite, deterministic rebuild, protected-path diff, whitespace, and release-verification output into story evidence.
- Include an AC verification table for all six criteria.
- Record the story head SHA and every regenerated artifact SHA-256 that changed.
- Deliver through `pvg story deliver`; do not close the story as a developer.

## nd_contract
status: new

### evidence
- Created 2026-09-23 from a measured full-suite failure at main `8c67a01`.
- Targeted reproduction: `uv run --frozen --extra dev pytest -q tests/test_spend_gate.py::test_lf004_parity_queue_join_and_live_atomic_recorder --junitxml=/tmp/srpm-spend-gate-bug.xml` exited 1 at `tests/test_spend_gate.py:57`.
- Minimal root-cause script measured the main-checkout prefix leak and identical nested/foreign output.
- Baseline `pvg lint --backlog`: 111 issues scanned, 0 errors, 0 review findings.

### proof
- [ ] Pending implementation.

## Acceptance Criteria

## Design

## Notes


## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-23.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## nd_contract
status: in_progress

### evidence
- Story head: `5d9380a9da499770bd29794db92c8d2b19407c7a` (`fix(WD-pn6h): canonicalize nested worktree evidence paths`), pushed to `origin/story/WD-pn6h`.
- Diff: `services/jobs/spend_gate.py` 9 insertions / 2 deletions; `tests/test_spend_gate.py` 26 insertions / 2 deletions. Total 31 insertions / 4 deletions across 2 files.
- `uv run --frozen --extra dev pytest -q tests/test_spend_gate.py` -> 19 passed, exit 0.
- `uv run --frozen --extra dev pytest -q --junitxml=/tmp/wd-pn6h-full.xml` -> exit 0; JUnit `tests=1996 errors=0 failures=0 skipped=1` (707.796s).
- `uv run --frozen --extra dev python scripts/build_spend_gate_corpus.py --repository-root . --evidence-mode all-local --output-dir datasets/spend-gate/v1 --replay --verify-artifact` -> `rows=36 mode=all-local`, exit 0. Regenerated corpus/replay bytes were identical to HEAD; only builder-owned manifest checkout metadata differed transiently and was not committed.
- `uv run --frozen --extra dev wgp release verify` -> all checks pass, `tag_created=false`, `release=ready`, exit 0.
- Protected-path diff -> exit 0, no diff. `git diff --check` -> exit 0, no output.
- Committed artifact SHA-256 unchanged: corpus `970632d10e8de2dd68ec2b585911400e6522da09676ff322a8378a7c1186f3c1`; manifest `07599793152d2e8f1a659f25c2395169a1352f6410dd7f4db0007732913b1468`; schema drift `538712be86789709c8d296a3cca08c45861ffa1df8fab0a3b452de0f261d0c5f`; replay metrics `86865a99033ebe04c35b8a7a12fa23cf1e0dfff2a489beaf48fda1e4acfe947c`; replay report `452bb6f90005d7535ee7549c95201cab02f04c7d82a5133be416a9bcb09c102d`.

### proof
- [x] AC #1: Full suite exits 0 with zero failures; LF004 parity test passed in the 19-test targeted suite and full suite (JUnit failures=0).
- [x] AC #2: `tests/test_spend_gate.py:217-222` canonicalizes the exact recorded path with main, nested, and foreign roots and requires the one expected `datasets/.../qc-evidence.json` value.
- [x] AC #3: `tests/test_spend_gate.py:224-236` recursively extracts path fields from canonical LF004 cuts and every committed corpus row and rejects any `.claude` path segment.
- [x] AC #4: No corpus/manifest content change was required. The deterministic builder ran with `--replay --verify-artifact` successfully; corpus/replay hashes remained unchanged.
- [x] AC #5: `wgp release verify` reported `tag_created=false` and `release=ready`.
- [x] AC #6: Existing LF004 assertions at `tests/test_spend_gate.py:51-63`, including attempt sequence `[2, 0, 0, 0]`, remain intact and passed.


## History
- 2026-09-23T18:47:57Z dep_added: blocks WD-l48s
- 2026-09-23T18:53:01Z status: open -> in_progress
- 2026-09-23T18:53:01Z auto-follows: linked to predecessor WD-v6xp
- 2026-09-23T18:53:01Z claimed by dev-WD-pn6h
- 2026-09-23T19:10:47Z status: in_progress -> in_progress
- 2026-09-23T19:10:47Z auto-follows: linked to predecessor WD-rf1a

## Links
- Parent: [[WD-as25]]
- Blocks: [[WD-l48s]]
- Follows: [[WD-v6xp]], [[WD-rf1a]]

## Comments
