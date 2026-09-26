---
id: WD-isg9
title: "Maestro parity: H3 standard operation batch"
status: in_progress
priority: 1
type: task
labels: [capability, evidence, delivered]
parent: WD-3nod
created_at: 2026-09-26T13:07:47Z
created_by: speed
updated_at: 2026-09-26T14:50:51Z
content_hash: "sha256:eee459adc81118830bf34eb48e17c6da19aa90e482bd8b3ee7b716710a705bcf"
assignee: dev-WD-isg9
follows: [WD-14ej, WD-i7qs]
blocks: [WD-fay0]
---

## Description
WD-isg9 emits terminal, operation-specific evidence for the eight remaining
`minimax_h3/standard` cells using already present hash-verified FL2VA assets on
host `3090`, with no new model download. The cells are extend, blend, retake,
edit, outpaint, repaint, recast, and upscale. The verified create cell cannot
proxy for any other cell.

Each cell must end as `host_run_verified` with its own distinct nonempty hashed
media artifact and objective gates, or as documented `unsupported` backed by a
real host rejection or implementation boundary. Never relabel a generic render
as an operation.

Operator authorization is the 2026-09-26 text "Authorized and approved." followed
by "continue", scoped to this existing-asset host-run batch. Training, paid
providers, GUI work, unrelated GPU processes, new downloads, and model deletion
are not authorized.

The bundle must record repository/base state; live SSH, H3 hash, disk, GPU, and
QC preflight; exact command argv; model/reference/mask provenance; durable
queue admission; output hashes; ffprobe metadata; operation-specific objective
gates; and reviewer links. Capture fail-closed diagnostics for blend, recast,
and outpaint. Update only the eight `minimax_h3/standard` cells in
`docs/video-capabilities.md`. The parity checker, scoped/full tests, backlog
lint, and delivery proof must pass.

## Acceptance Criteria

1. A clean story worktree is created from current `main`, and the story is
   atomically claimed before implementation.
2. Before host contact, record repository state and a live host preflight
   including SSH, model hashes, disk floor, GPU state, and unrelated-process
   state. Any failed prerequisite stops the batch.
3. The bundle records operator authorization, exact local/remote command argv,
   repository identity, model provenance, bundle-relative references, durable
   queue admission, output hashes, ffprobe metadata, objective gates, and
   reviewer evidence.
4. Every one of the eight named cells reaches a terminal state:
   `host_run_verified` with a distinct nonempty media artifact, or documented
   `unsupported` backed by a real host rejection/implementation boundary.
5. `docs/video-capabilities.md` changes only the eight cells in this story and
   links each change to the new evidence.
6. `scripts/verify_maestro_parity.py` passes on the new bundle, and existing
   capability/evidence tests pass.
7. `pvg lint --backlog` passes, the story delivery proof passes, and the PR
   contains only this batch's evidence and documentation updates.

## MANDATORY SKILLS

None identified.

## Design


## Notes
## Implementation Evidence (DELIVERED)

Commands run:

- `ssh 3090 /home/straughter/Wan2GP/wd-isg9/host-scripts/wd_isg9_boundary_probes.sh`
- `ssh 3090 /home/straughter/Wan2GP/wd-isg9/host-scripts/wd_isg9_render.sh`
- `uv run --frozen --extra dev python datasets/runs/maestro-parity/WD-isg9/build-objective-gates.py`
- `uv run --frozen --extra dev python datasets/runs/maestro-parity/WD-isg9/build-evidence.py`
- `uv run --frozen --extra dev python scripts/verify_maestro_parity.py datasets/runs/maestro-parity/WD-isg9`
- `uv run --frozen --extra dev pytest -q tests/test_video_capabilities.py tests/test_maestro_parity_evidence.py`
- `pvg lint --backlog`

Summary:

Five H3-standard operations produced real distinct hashed media; blend, recast, and outpaint reached evidenced host implementation boundaries. Independent PM review is pending.

Commit SHA: ee81c0ccd763376d86734791a342e16efad78ebb

### AC Verification

| AC | Result | Evidence |
| --- | --- | --- |
| 1 | PASS | Clean story worktree and atomic claim completed. |
| 2 | PASS | `preflight.json` passes SSH, model hashes, disk, GPU, and QC. |
| 3 | PASS | `evidence.json`, queue DB, argv logs, hashes, ffprobe, and gates record the required provenance. |
| 4 | PASS | Five outputs and three boundary diagnostics disposition all eight cells. |
| 5 | PASS | `docs/video-capabilities.md` changes only the eight H3-standard cells plus their supporting narrative. |
| 6 | PENDING REVIEWER | Objective/scoped gates pass; canonical checker awaits independent reviewer approval. |
| 7 | PENDING REVIEWER | Lint/diff pass; PM acceptance and merge remain. |

## nd_contract
status: delivered

### evidence

- Commit SHA: ee81c0ccd763376d86734791a342e16efad78ebb is pushed on `story/WD-isg9`.
- Objective gates 43/43 pass; scoped tests exit 0; backlog lint and diff-check exit 0.
- Reviewer approval is intentionally pending.

### proof

- [x] AC1 through AC5 pass with artifacts cited above.
- [ ] AC6 completes after independent reviewer approval.
- [ ] AC7 completes after PM acceptance and merge.

## Implementation Evidence

### Bundle

- `datasets/runs/maestro-parity/WD-isg9/evidence.json`
- `datasets/runs/maestro-parity/WD-isg9/execution-summary.md`
- `datasets/runs/maestro-parity/WD-isg9/objective-gates.json`
- `datasets/runs/maestro-parity/WD-isg9/queue.db`
- `docs/video-capabilities.md`

### Outputs

- extend SHA-256 `489f8aae72b41b669df2259182eb287ca805ff3033d2b7ed93a130b903c00cef`
- retake SHA-256 `4a75cccc6aefe55cbf3cb65e276f9783a3430635cbbc65e140ab5d7b30dd864b`
- edit SHA-256 `93acbbd1c4d432555d14135dad2648b88f19bec7a1ec40457ce6e17978158f1c`
- repaint SHA-256 `3f14efa860a0a3564abbb4a39fcc56a380731d7f5595991639dc2cfc08fa9416`
- upscale SHA-256 `ee703d736fc6a065b6d546d8756838fa2edd5feeebd4755d304463f33dbe505a`

### CI/Test Results

- Scoped tests: 92 passed, exit 0 (`scoped-tests.out`).
- Dirty-worktree full suite: 2090 tests, 0 errors, 2088 passed, 1 skipped, 2 expected release-tree failures because the evidence worktree was intentionally dirty (`fullsuite-dirty-tree-counters.json`).
- Backlog lint: 131 scanned, 0 errors, 0 review findings.
- Objective gates: 43/43 pass.
- Canonical parity checker at delivery: fails only `reviewer_verdict.decision` and `reviewer_verdict.evidence_links`; independent PM review is pending.

### Commands run

- `pvg story claim WD-isg9`
- `ssh 3090 /home/straughter/Wan2GP/wd-isg9/host-scripts/wd_isg9_boundary_probes.sh`
- `ssh 3090 /home/straughter/Wan2GP/wd-isg9/host-scripts/wd_isg9_render.sh`
- `uv run --frozen --extra dev python datasets/runs/maestro-parity/WD-isg9/measure_objective_gates.py`
- `uv run --frozen --extra dev python datasets/runs/maestro-parity/WD-isg9/build-objective-gates.py`
- `uv run --frozen --extra dev python datasets/runs/maestro-parity/WD-isg9/build-evidence.py`
- `uv run --frozen --extra dev python scripts/verify_maestro_parity.py datasets/runs/maestro-parity/WD-isg9`
- `uv run --frozen --extra dev pytest -q tests/test_video_capabilities.py tests/test_maestro_parity_evidence.py`
- `pvg lint --backlog`
- `git diff --check`

### Summary

WD-isg9 terminally dispositioned all eight remaining H3-standard cells with five real hashed media outputs and three evidenced host implementation boundaries, using zero new download bytes.

## nd_contract
status: delivered

### evidence

- Commit SHA: ee81c0ccd763376d86734791a342e16efad78ebb
- Branch: `story/WD-isg9` pushed to origin.
- Bundle: `datasets/runs/maestro-parity/WD-isg9/evidence.json`.
- Preflight: SSH/model hashes/disk/GPU/QC all pass.
- Render exits: extend/retake/edit/repaint/upscale all 0.
- Boundary exits: blend 1, recast 1; outpaint control disabled in hashed host code.
- Objective gates: 43 pass, 0 fail.
- Review status: pending independent PM approval.

### proof

- [x] AC1: clean story worktree and atomic claim completed.
- [x] AC2: live preflight recorded and all prerequisites passed.
- [x] AC3: authorization, argv, provenance, queue, hashes, ffprobe, gates, and reviewer links recorded.
- [x] AC4: all eight cells reached operation-specific terminal dispositions.
- [x] AC5: only the eight H3-standard matrix cells and their supporting narrative changed.
- [ ] AC6: canonical checker and tests complete after independent reviewer approval.
- [ ] AC7: delivery proof, PM acceptance, and final merge gate remain.

## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-26.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## History
- 2026-09-26T13:08:07Z status: open -> in_progress
- 2026-09-26T13:08:07Z auto-follows: linked to predecessor WD-14ej
- 2026-09-26T13:08:07Z claimed by dev-WD-isg9
- 2026-09-26T13:08:15Z dep_added: blocks WD-fay0
- 2026-09-26T14:44:30Z status: in_progress -> in_progress
- 2026-09-26T14:44:30Z auto-follows: linked to predecessor WD-i7qs

## Links
- Parent: [[WD-3nod]]
- Blocks: [[WD-fay0]]
- Follows: [[WD-14ej]], [[WD-i7qs]]

## Comments

### 2026-09-26T13:28:50Z speed
Dispatcher repaired malformed authored sections created by repeated body updates; canonical Description and Acceptance Criteria now occur once.

### 2026-09-26T14:48:37Z speed
Corrected delivery commit SHA to ee81c0ccd763376d86734791a342e16efad78ebb.

### 2026-09-26T14:50:51Z speed
Corrected delivery commit SHA to ee81c0ccd763376d86734791a342e16efad78ebb.
