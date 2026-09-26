---
id: WD-9t9o
title: "Maestro parity: H3 VDN operation batch"
status: in_progress
priority: 1
type: task
labels: [capability, evidence, delivered]
parent: WD-3nod
created_at: 2026-09-26T15:56:38Z
created_by: speed
updated_at: 2026-09-26T16:27:57Z
content_hash: "sha256:2ada37e9f4b7688d77336f6fb7d7dea3241a8f24dfadde8c5ebe61e530552e24"
blocks: [WD-fay0]
assignee: dev-WD-9t9o
follows: [WD-isg9, WD-14ej]
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


## MANDATORY SKILLS
None identified.

## History
- 2026-09-26T15:56:58Z dep_added: blocks WD-fay0
- 2026-09-26T15:57:03Z status: open -> in_progress
- 2026-09-26T15:57:03Z auto-follows: linked to predecessor WD-isg9
- 2026-09-26T15:57:03Z claimed by dev-WD-9t9o
- 2026-09-26T16:27:56Z status: in_progress -> in_progress
- 2026-09-26T16:27:57Z auto-follows: linked to predecessor WD-14ej

## Links
- Parent: [[WD-3nod]]
- Blocks: [[WD-fay0]]
- Follows: [[WD-isg9]], [[WD-14ej]]

## Comments

### 2026-09-26T16:25:12Z speed
Added the missing MANDATORY SKILLS section required by backlog lint.
