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
updated_at: 2026-09-26T14:44:30Z
content_hash: "sha256:0bbe03a68d16b88e3906998e394f704c43741d4a84e0e2d7129e7eb574b3be72"
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
