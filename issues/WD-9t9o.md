---
id: WD-9t9o
title: "Maestro parity: H3 VDN operation batch"
status: closed
priority: 1
type: task
labels: [capability, evidence, delivered]
parent: WD-3nod
created_at: 2026-09-26T15:56:38Z
created_by: speed
updated_at: 2026-09-26T16:57:25Z
content_hash: "sha256:89a5ec3e24abf818290bfd0d1cac10cacb3860989efcf5ca638d4ff61bc7de7a"
assignee: dev-WD-9t9o
follows: [WD-isg9, WD-14ej]
closed_at: 2026-09-26T16:57:25Z
close_reason: "Accepted: verified all eight VDN dispositions, real boundaries, local hashes, objective gates, delivery proof, canonical checker, and PR 198 CI at 216e7448."
---

## Description
WD-H3VDN emits terminal, operation-specific evidence for the eight remaining
`minimax_h3/h3_vdn_hybrid_attention` cells using already present hash-verified
FL2VA assets on host `3090`, with no new model download. The cells are extend,
blend, retake, edit, outpaint, repaint, recast, and upscale. The verified create
cell cannot proxy for any other cell.

Each cell must end as `host_run_verified` with its own distinct nonempty hashed
media artifact and objective gates, or as documented `unsupported` backed by a
real host rejection or implementation boundary. Generative VDN operations must
preserve the Sol-Attn runtime proof; a generic SDPA render cannot proxy for the
VDN preset. Never relabel a generic render as an operation.

Operator authorization is the 2026-09-26 text "Authorized and approved." followed
by "continue", scoped to this existing-asset host-run batch. Training, paid
providers, GUI work, unrelated GPU processes, new downloads, and model deletion
are not authorized.

The bundle must record repository/base state; original preflight command plus
raw live model hashes/sizes/mtimes; SSH, disk, GPU, unrelated-process, and QC
state; exact command argv; model/reference/mask provenance; durable queue
admission; output hashes; ffprobe metadata; operation-specific objective gates;
and reviewer links. Capture fail-closed diagnostics for blend, recast, and
outpaint. Update only the eight `h3_vdn_hybrid_attention` cells in
`docs/video-capabilities.md`. The parity checker, scoped tests, backlog lint,
delivery proof, clean release verification, and PR CI must pass.

## Acceptance Criteria


## Design


## Notes
## Implementation Evidence

Commands run:

- `ssh 3090 /home/straughter/Wan2GP/wd-9t9o/host-scripts/wd_9t9o_preflight_hash_probe.sh`
- `ssh 3090 /home/straughter/Wan2GP/wd-9t9o/host-scripts/wd_9t9o_boundary_probes.sh`
- `ssh 3090 /home/straughter/Wan2GP/wd-9t9o/host-scripts/wd_9t9o_render.sh`
- `ssh 3090 bash /tmp/wd_9t9o_retry_sdpa.sh`
- `uv run --frozen --extra dev python datasets/runs/maestro-parity/WD-9t9o/build_preflight_hash_summary.py`
- `uv run --frozen --extra dev python datasets/runs/maestro-parity/WD-9t9o/measure_objective_gates.py`
- `uv run --frozen --extra dev python datasets/runs/maestro-parity/WD-9t9o/build-objective-gates.py`
- `uv run --frozen --extra dev python datasets/runs/maestro-parity/WD-9t9o/build-evidence.py`
- `uv run --frozen --extra dev python scripts/verify_maestro_parity.py datasets/runs/maestro-parity/WD-9t9o`
- `uv run --frozen --extra dev pytest -q tests/test_video_capabilities.py tests/test_maestro_parity_evidence.py`
- `pvg lint --backlog`
- `git diff --check`
- `uv run --frozen --extra dev wgp release verify --json`

Summary:

WD-9t9o terminally dispositioned all eight H3 VDN cells: edit, repaint, and upscale produced real distinct media with Sol-Attn proof; extend, retake, blend, recast, and outpaint reached evidenced host boundaries. No model-download bytes were used.

Commit SHA: 216e7448c9a287f9df1b74e56f7dfd044e35af96

### CI/Test Results

- Scoped capability/evidence tests: 92 passed, exit 0.
- Backlog lint: 132 scanned, 0 errors, 0 review findings.
- `git diff --check`: exit 0.
- Clean-tree release verification at `216e7448`: version/changelog/recipe/tree all pass; `release=ready`; no tag created.
- PR 198 CI is pending at `216e7448`.
- Canonical parity checker at delivery: fails only the two independent reviewer-verdict fields.
- No scoped-test warning was emitted. Any full-suite FastAPI/Starlette deprecation warning is pre-existing and unrelated; it remains observable in CI rather than dismissed.

### AC Verification

| AC | Result | Evidence |
| --- | --- | --- |
| 1 | PASS | Story claimed and delivered from clean story worktree. |
| 2 | PASS | Raw live preflight records 4/4 model hashes/sizes, source hash, mtimes, disk, GPU, process, and QC state. |
| 3 | PASS | `evidence.json` records exact preflight, boundary, render, and retry argv with observed model provenance. |
| 4 | PASS | Three real outputs and five real host boundaries disposition all eight VDN cells. |
| 5 | PASS | Matrix changes are limited to the eight VDN cells and supporting narrative. |
| 6 | PENDING REVIEWER | 39/39 objective gates and scoped tests pass; checker awaits reviewer approval and CI. |
| 7 | PENDING REVIEWER | Delivery proof, PM acceptance, and merge remain. |

LEARNINGS:

- H3 VDN with visual source/first-frame conditioning and required Sol settings currently fails in the text/vision encoder SageAttention path before denoising; this is a reproducible host boundary, not a 24-GiB verdict.
- Grouped-row masked repaint conflicts with Sol-Attn; `h3_mask_mode=shared_timestep` preserves both the mask and the required Sol runtime.
- Preserve raw model/source hashes and mtimes up front; boolean preflight summaries are insufficient for independent PM review.

### OBSERVATIONS (unrelated)

- The existing FastAPI test-client import can emit `StarletteDeprecationWarning` in the full suite; it is unrelated to WD-9t9o and is retained for SrPM triage if CI reports it.

## nd_contract
status: delivered

### evidence

- Commit SHA: 216e7448c9a287f9df1b74e56f7dfd044e35af96
- Preflight model/source hash summary passes 4/4 plus source match.
- Objective gates: 39 pass, 0 fail.
- Scoped tests, lint, diff-check, and clean release verification pass.
- Reviewer approval remains pending.

### proof

- [x] AC1 through AC5 pass with artifacts cited above.
- [ ] AC6 completes after independent reviewer approval and PR CI.
- [ ] AC7 completes after PM acceptance and merge.

## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-26.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## MANDATORY SKILLS
None identified.

## nd_contract
status: delivered

### evidence

- Commit SHA: 216e7448c9a287f9df1b74e56f7dfd044e35af96
- Raw live preflight and operation evidence are committed and pushed.
- Objective gates 39/39 pass; scoped tests, lint, diff-check, and clean release verification pass.
- Independent reviewer approval remains pending.

### proof

- [x] AC1 through AC5 pass with artifacts cited above.
- [ ] AC6 completes after independent reviewer approval and PR CI.
- [ ] AC7 completes after PM acceptance and merge.

## History
- 2026-09-26T15:56:58Z dep_added: blocks WD-fay0
- 2026-09-26T15:57:03Z status: open -> in_progress
- 2026-09-26T15:57:03Z auto-follows: linked to predecessor WD-isg9
- 2026-09-26T15:57:03Z claimed by dev-WD-9t9o
- 2026-09-26T16:27:56Z status: in_progress -> in_progress
- 2026-09-26T16:27:57Z auto-follows: linked to predecessor WD-14ej
- 2026-09-26T16:57:25Z status: in_progress -> closed
- 2026-09-26T16:57:25Z dep_removed: no_longer_blocks WD-fay0

## Links
- Parent: [[WD-3nod]]
- Follows: [[WD-isg9]], [[WD-14ej]]

## Comments

### 2026-09-26T16:25:12Z speed
Added the missing MANDATORY SKILLS section required by backlog lint.

### 2026-09-26T16:28:44Z speed
Delivery evidence normalized to the exact pvg Implementation Evidence heading and contract placed at EOF.
