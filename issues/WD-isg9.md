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
updated_at: 2026-09-26T13:27:54Z
content_hash: "sha256:e14ce04e4dba1eacc3c9ba07bc9fcf7087804b73591f7a71d914b9230af1be9f"
assignee: dev-WD-isg9
follows: [WD-14ej]
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

## Scope

WD-isg9 emits terminal, operation-specific evidence for the eight remaining
`minimax_h3/standard` cells using the already present hash-verified FL2VA
assets on host `3090`. It performs no new model download.

Cells: extend, blend, retake, edit, outpaint, repaint, recast, upscale. The
already verified create cell is not rerun and cannot proxy for another cell.

Each cell must end as either:

- `host_run_verified`, with its own distinct nonempty hashed media artifact and
  objective gates; or
- documented `unsupported`, backed by a real host rejection or implementation
  boundary.

Never relabel a generic render as an operation.

## Operator authorization

- 2026-09-26: "Authorized and approved."
- 2026-09-26: "continue"
- Scope: begin the previously identified per-family/per-operation host-run
  evidence batch using existing assets.
- Not authorized: training, paid providers, GUI work, unrelated GPU processes,
  new downloads, or model deletion.

## Required evidence

1. Record clean worktree/base and live host preflight: SSH, H3 hashes, disk
   floor, GPU state, and QC health. Stop on any failure.
2. Record exact local and remote command argv, model provenance, source and
   mask hashes, durable queue admission, output hashes, ffprobe metadata,
   operation-specific objective gates, and reviewer links.
3. Capture fail-closed host diagnostics for blend, recast, and outpaint rather
   than inventing substitute renders.
4. Update only the eight `minimax_h3/standard` cells in
   `docs/video-capabilities.md`, each linked to the new evidence.
5. The parity checker passes, scoped/full tests pass, `pvg lint --backlog`
   passes, and the delivery proof passes.

## Scope

WD-isg9 emits terminal, operation-specific evidence for the eight remaining
`minimax_h3/standard` cells using the already present hash-verified FL2VA
assets on host `3090`. It performs no new model download.

Cells: extend, blend, retake, edit, outpaint, repaint, recast, upscale. The
already verified create cell is not rerun and cannot proxy for another cell.

Each cell must end as either:

- `host_run_verified`, with its own distinct nonempty hashed media artifact and
  objective gates; or
- documented `unsupported`, backed by a real host rejection or implementation
  boundary.

Never relabel a generic render as an operation.

## Operator authorization

- 2026-09-26: "Authorized and approved."
- 2026-09-26: "continue"
- Scope: begin the previously identified per-family/per-operation host-run
  evidence batch using existing assets.
- Not authorized: training, paid providers, GUI work, unrelated GPU processes,
  new downloads, or model deletion.

## Required evidence

1. Record clean worktree/base and live host preflight: SSH, H3 hashes, disk
   floor, GPU state, and QC health. Stop on any failure.
2. Record exact local and remote command argv, model provenance, source and
   mask hashes, durable queue admission, output hashes, ffprobe metadata,
   operation-specific objective gates, and reviewer links.
3. Capture fail-closed host diagnostics for blend, recast, and outpaint rather
   than inventing substitute renders.
4. Update only the eight `minimax_h3/standard` cells in
   `docs/video-capabilities.md`, each linked to the new evidence.
5. The parity checker passes, scoped/full tests pass, `pvg lint --backlog`
   passes, and the delivery proof passes.

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
