---
id: WD-8h6p
title: "Hunyuan no-download video boundary batch"
status: open
priority: 1
type: task
labels: [capability, video, evidence, external-integration]
parent: WD-3nod
created_at: 2026-09-27T03:22:55Z
created_by: speed
updated_at: 2026-09-27T03:22:56Z
content_hash: "sha256:baa651d55dea085dbac1adfd9fd8f3a77d179f101a4b2d4148a80bd163a2aebc"
blocks: [WD-fay0]
---

## Description
## USER INTENT
The Hunyuan video row emits a terminal disposition for each of its seven still-planned cells using only preexisting hash-matched assets. The user can inspect one bundle and see either real generated media evidence or an exact fail-closed host boundary.

## Embedded Current State
At merged main 8103327f:

- hunyuan/standard create is already host_run_verified by WD-2gyw.
- outpaint is already a typed backend boundary.
- extend, blend, retake, edit, repaint, recast, and upscale remain planned.
- The 3090 has the preexisting Hunyuan 1.5 int8 transformer, VAE, config, and helper assets used by WD-2gyw.
- WD-m25k proves the no-download/isolated-worktree pattern and exact boundary discipline.

## Operator Authorization
Verbatim current instruction: Continue the remaining 56 video cells, prioritizing no-download LTX-2.5 after the tokenizer fix.

Dispatcher interpretation: after accepted no-download LTX-2.5 and H3 batches, continue with the next no-download Hunyuan batch. Exact scope is these seven cells, zero model/dependency download bytes, no live Wan2GP mutation outside an isolated worktree, and no unrelated process action.

## Boundary Map
PRODUCES:
- datasets/runs/maestro-parity/WD-8h6p/ -> hash-backed Hunyuan per-cell evidence or exact boundaries
  spec: authorization, base/source identity, asset hashes, zero-download pre/postflight, native argv/logs, queue/output or boundary records, media metadata/gates, checker result, reviewer decision, and matrix transition.
- docs/video-capabilities.md -> seven mechanically derived target-cell updates
  event: cite only this bundle and leave every non-target cell unchanged.

CONSUMES:
- datasets/runs/maestro-parity/WD-2gyw/ -> verified Hunyuan create output, asset provenance, and settings
  source: hash-copy only; never mutate the accepted bundle.
- scripts/verify_maestro_parity.py -> canonical evidence checker
  event: checker exit 0 is required for any host_run_verified disposition.

## Story Acceptance Criteria
1. [State] Start from current origin/main, create/push a clean story branch/worktree, record base identity, and atomically claim the story before host mutation.
2. [Unwanted] A no-download preflight hashes every required Hunyuan asset and reused source, forces offline mode, records zero planned/actual download bytes, and stops on hash, disk, GPU, or source-state failure.
3. [State] Each of the seven target cells receives its own native attempt or typed boundary; no evidence is inherited across operation.
4. [State] Each successful output stores argv, native log, queue/exit state, SHA-256, ffprobe metadata, and an operation-appropriate objective gate.
5. [State] Each unsuccessful cell stores exact exit/failing stage, required missing control or asset, before/after host state, and an honest dependency or host-implementation boundary.
6. [Unwanted] No download, live-tree mutation, protected-engine semantic change, threshold change, or unrelated process action occurs.
7. [State] docs/video-capabilities.md changes exactly the seven target planned cells and the matrix-transition artifact proves zero target planned cells remain.
8. [State] Delivery passes pvg lint, canonical checker after independent review, targeted tests, release verification, protected parity, and diff check; it is delivered and independently accepted without self-approval.

## Testing Requirements
- Real no-mock native execution where admitted.
- Rehash reused references before/after.
- Parse successful media with ffprobe and mechanically derive gates/matrix transitions.
- Run canonical checker, targeted tests, pvg lint, release verify, protected parity, and diff check.

## Delivery Requirements
Record authorization, hashes, source identity, host snapshots, command inventory, outputs/boundaries, gates, matrix transition, bundle size, pushed head, and PR. Stop on any missing required input.

## MANDATORY SKILLS
- pvg

## nd_contract
status: new

### evidence
- Authored from merged main 8103327f after accepted WD-m25k and the operator's continuing no-download video instruction.

### proof
- [ ] Pending atomic claim and implementation.

## USER INTENT
The Hunyuan video row emits a terminal disposition for each of its seven still-planned cells using only preexisting hash-matched assets. The user can inspect one bundle and see either real generated media evidence or an exact fail-closed host boundary.

## Embedded Current State
At merged main 8103327f:

- hunyuan/standard create is already host_run_verified by WD-2gyw.
- outpaint is already a typed backend boundary.
- extend, blend, retake, edit, repaint, recast, and upscale remain planned.
- The 3090 has the preexisting Hunyuan 1.5 int8 transformer, VAE, config, and helper assets used by WD-2gyw.
- WD-m25k proves the no-download/isolated-worktree pattern and exact boundary discipline.

## Operator Authorization
Verbatim current instruction: Continue the remaining 56 video cells, prioritizing no-download LTX-2.5 after the tokenizer fix.

Dispatcher interpretation: after accepted no-download LTX-2.5 and H3 batches, continue with the next no-download Hunyuan batch. Exact scope is these seven cells, zero model/dependency download bytes, no live Wan2GP mutation outside an isolated worktree, and no unrelated process action.

## Boundary Map
PRODUCES:
- datasets/runs/maestro-parity/WD-VIDEO/ -> hash-backed Hunyuan per-cell evidence or exact boundaries
  spec: authorization, base/source identity, asset hashes, zero-download pre/postflight, native argv/logs, queue/output or boundary records, media metadata/gates, checker result, reviewer decision, and matrix transition.
- docs/video-capabilities.md -> seven mechanically derived target-cell updates
  event: cite only this bundle and leave every non-target cell unchanged.

CONSUMES:
- datasets/runs/maestro-parity/WD-2gyw/ -> verified Hunyuan create output, asset provenance, and settings
  source: hash-copy only; never mutate the accepted bundle.
- scripts/verify_maestro_parity.py -> canonical evidence checker
  event: checker exit 0 is required for any host_run_verified disposition.

## Story Acceptance Criteria
1. [State] Start from current origin/main, create/push a clean story branch/worktree, record base identity, and atomically claim the story before host mutation.
2. [Unwanted] A no-download preflight hashes every required Hunyuan asset and reused source, forces offline mode, records zero planned/actual download bytes, and stops on hash, disk, GPU, or source-state failure.
3. [State] Each of the seven target cells receives its own native attempt or typed boundary; no evidence is inherited across operation.
4. [State] Each successful output stores argv, native log, queue/exit state, SHA-256, ffprobe metadata, and an operation-appropriate objective gate.
5. [State] Each unsuccessful cell stores exact exit/failing stage, required missing control or asset, before/after host state, and an honest dependency or host-implementation boundary.
6. [Unwanted] No download, live-tree mutation, protected-engine semantic change, threshold change, or unrelated process action occurs.
7. [State] docs/video-capabilities.md changes exactly the seven target planned cells and the matrix-transition artifact proves zero target planned cells remain.
8. [State] Delivery passes pvg lint, canonical checker after independent review, targeted tests, release verification, protected parity, and diff check; it is delivered and independently accepted without self-approval.

## Testing Requirements
- Real no-mock native execution where admitted.
- Rehash reused references before/after.
- Parse successful media with ffprobe and mechanically derive gates/matrix transitions.
- Run canonical checker, targeted tests, pvg lint, release verify, protected parity, and diff check.

## Delivery Requirements
Record authorization, hashes, source identity, host snapshots, command inventory, outputs/boundaries, gates, matrix transition, bundle size, pushed head, and PR. Stop on any missing required input.

## MANDATORY SKILLS
- pvg

## nd_contract
status: new

### evidence
- Authored from merged main 8103327f after accepted WD-m25k and the operator's continuing no-download video instruction.

### proof
- [ ] Pending atomic claim and implementation.

## Acceptance Criteria


## Design


## Notes


## History
- 2026-09-27T03:22:56Z dep_added: blocks WD-fay0

## Links
- Parent: [[WD-3nod]]
- Blocks: [[WD-fay0]]

## Comments
