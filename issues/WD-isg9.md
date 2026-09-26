---
id: WD-isg9
title: "Maestro parity: H3 standard operation batch"
status: in_progress
priority: 1
type: task
labels: [capability, evidence]
parent: WD-3nod
created_at: 2026-09-26T13:07:47Z
created_by: speed
updated_at: 2026-09-26T13:08:07Z
content_hash: "sha256:2055302c80a1a891cf9c0a6a257fa8cc987b49cc7aae106f1939a388091bc55c"
assignee: dev-WD-isg9
follows: [WD-14ej]
blocks: [WD-fay0]
---

## Description
## Description

Execute the next operator-authorized Maestro-parity video evidence batch with
**zero new model downloads**. The batch is limited to the eight remaining
`minimax_h3/standard` matrix cells:

- extend
- blend
- retake
- edit
- outpaint
- repaint
- recast
- upscale

`create` is already verified by WD-2gyw and must not be rerun or treated as
evidence for any other cell.

The work must use the already present, hash-verified MiniMax H3 FL2VA assets on
host `3090`, preserve the accepted `WD-2gyw` provenance/checker contract, and
stop on host/disk/GPU preflight failure. A real operation may be marked only
`host_run_verified` with its own hashed output and objective gates. If the real
host control rejects an operation, record the exact fail-closed diagnostic and
promote that cell only to the documented `unsupported` boundary; never relabel
a generic render as the requested operation.

## Operator authorization

- 2026-09-26: "Authorized and approved."
- 2026-09-26: "continue"
- Scope inferred from those instructions: begin the previously identified
  per-family/per-operation host-run evidence batch using existing assets.
- No training, paid provider, GUI work, unrelated GPU process, new download, or
  model deletion is authorized by this story.

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

## Acceptance Criteria


## Design


## Notes


## History
- 2026-09-26T13:08:07Z status: open -> in_progress
- 2026-09-26T13:08:07Z auto-follows: linked to predecessor WD-14ej
- 2026-09-26T13:08:07Z claimed by dev-WD-isg9
- 2026-09-26T13:08:15Z dep_added: blocks WD-fay0

## Links
- Parent: [[WD-3nod]]
- Blocks: [[WD-fay0]]
- Follows: [[WD-14ej]]

## Comments
