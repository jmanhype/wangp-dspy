---
id: WD-m25k
title: "H3 KFI/audio-refinement no-download video batch"
status: in_progress
priority: 1
type: task
labels: [capability, video, evidence, external-integration]
parent: WD-3nod
created_at: 2026-09-27T01:24:28Z
created_by: speed
updated_at: 2026-09-27T01:24:44Z
content_hash: "sha256:0938314a0277c8044153b14282cde9cb205dd0e39a3dbd3a30853ca87a75c0c8"
blocks: [WD-fay0]
assignee: dev-WD-m25k
follows: [WD-obkn]
---

## Description
## USER INTENT
The H3 video lane emits a terminal, hash-backed disposition for each of the sixteen still-planned KFI/audio-refinement cells. The user can inspect one bundle and see either real generated media evidence or an exact fail-closed boundary for every target operation.

## Embedded Current State
At merged main 28fc76a1:

- minimax_h3/kfi_frames_injection: create, extend, blend, edit, outpaint, repaint, recast, and upscale are planned; retake is already host_run_verified.
- minimax_h3/h3_audio_refinement: create, extend, blend, retake, outpaint, repaint, recast, and upscale are planned; edit is already host_run_verified.
- LTX-2.5 is no longer the highest-priority zero-download target: after WD-i7qs/WD-m7xw, four operations are host_run_verified and four are dependency_blocked.
- The RTX 3090 currently exposes preexisting MiniMax H3 FL2VA/Ref2VA, audio VAE, video VAE, and latent-upscaler assets. The story records zero download bytes.
- Existing WD-2gyw, WD-isg9, and WD-9t9o bundles contain reusable references, settings patterns, operation maps, and fail-closed probes.

## Operator Authorization
Verbatim current instruction: Continue the remaining 56 video cells, prioritizing no-download LTX-2.5 after the tokenizer fix.

Dispatcher interpretation: continue no-download RTX 3090 evidence work after the accepted LTX-2.5 batch. Exact scope is the sixteen H3 cells named above, zero model/dependency download bytes, and no unrelated service mutation. Record this interpretation and stop if it is insufficient.

## OUT OF SCOPE
- Any other family, preset, operation, row, GUI surface, training, provider, publication, or threshold change.
- Inheriting another operation's or preset's evidence.
- Mutating accepted predecessor bundles.
- Editing protected engine semantics or the live Wan2GP tree outside an isolated run worktree.
- Downloading any model, LoRA, dependency, or dataset.

## DIFF BUDGET
About two authored surfaces: docs/video-capabilities.md plus the story evidence bundle. Keep media and logs bounded and commit no model weights.

## Boundary Map
PRODUCES:
- datasets/runs/maestro-parity/WD-m25k/ -> hash-backed per-cell H3 evidence or exact fail-closed boundaries
  spec: authorization, base identity, asset hashes, zero-download pre/postflight, native argv/logs, queue/exit records, output hashes/metadata, objective gates, checker result, reviewer placeholder, and matrix transition.
- docs/video-capabilities.md -> mechanically derived target-cell updates
  event: update exactly the sixteen owned planned cells and cite only this bundle.

CONSUMES:
- datasets/runs/maestro-parity/WD-2gyw/ -> accepted H3 create/KFI/audio/Hunyuan evidence and reusable references
  source: hash-copy only; never mutate the accepted bundle.
- datasets/runs/maestro-parity/WD-isg9/ -> H3 standard settings, outputs, and boundary-probe patterns
  source: hash-copy only; never inherit evidence across operation or preset.
- datasets/runs/maestro-parity/WD-9t9o/ -> H3 VDN settings and boundary-probe patterns
  source: hash-copy only; never inherit evidence across operation or preset.
- scripts/verify_maestro_parity.py -> canonical Maestro evidence checker
  event: checker exit 0 is required before any host_run_verified disposition.

## Story Acceptance Criteria
1. [State] Start from current origin/main, create/push a clean story branch and worktree, record repository/base identity, and atomically claim the story before host mutation.
2. [Unwanted] A no-download preflight hashes every required H3 asset, sets offline mode, records zero planned and actual download bytes, and stops before queue admission on absent/mismatched assets, dirty isolated source, insufficient disk/GPU headroom, or unexpected occupancy.
3. [State] Each of the sixteen target cells receives its own native operation attempt or typed boundary probe; evidence is never inherited across family, preset, or operation.
4. [State] Each successful output stores exact argv, native log, queue/exit state, SHA-256, ffprobe metadata, and at least one operation-appropriate objective gate derived from raw media.
5. [State] Each unsuccessful cell stores exact exit, failing stage, required missing asset or disabled control, before/after GPU and source state, and an honest dependency or host-implementation boundary rather than a hardware verdict.
6. [Unwanted] No download, live-tree mutation, protected-engine semantic change, threshold change, or unrelated process kill/restart occurs.
7. [State] docs/video-capabilities.md mechanically moves only the sixteen target cells from planned to evidence-backed terminal states; a transition artifact records target/unchanged counts and rejects drift elsewhere.
8. [State] Delivery passes pvg backlog lint, the canonical evidence checker, targeted video/evidence tests, release verification with release=ready and tag_created=false, protected-file parity, and git diff --check; any full-suite stop is recorded explicitly.
9. [State] The story is delivered, not self-accepted, with exact artifact paths, commit SHA, pushed branch/PR state, hashes, gate outputs, bundle size, and any independent-review requirement.

## Testing Requirements
- Real no-mock integration evidence where admitted.
- Rehash copied references before and after execution.
- Parse successful media with ffprobe and mechanically derive gates and matrix transitions.
- Run the canonical checker, targeted tests, release verification, lint, protected parity, and diff check in the story worktree.
- Do not fabricate a reviewer decision.

## Delivery Requirements
Paste authorization, asset hash result, base/source identity, host and GPU snapshots, exact command inventory, per-operation outputs/boundaries, hashes, checker and test receipts, matrix transition, bundle size, zero-download accounting, and final pushed head. If a required input fails, record the exact blocker without changing a cell.

## MANDATORY SKILLS
- pvg

## nd_contract
status: new

### evidence
- Authored from merged main 28fc76a1 and the operator's 2026-09-27 instruction to continue remaining video work after the accepted no-download LTX-2.5 batch.

### proof
- [ ] Pending atomic claim and implementation.

## USER INTENT
The H3 video lane emits a terminal, hash-backed disposition for each of the sixteen still-planned KFI/audio-refinement cells. The user can inspect one bundle and see either real generated media evidence or an exact fail-closed boundary for every target operation.

## Embedded Current State
At merged main 28fc76a1:

- minimax_h3/kfi_frames_injection: create, extend, blend, edit, outpaint, repaint, recast, and upscale are planned; retake is already host_run_verified.
- minimax_h3/h3_audio_refinement: create, extend, blend, retake, outpaint, repaint, recast, and upscale are planned; edit is already host_run_verified.
- LTX-2.5 is no longer the highest-priority zero-download target: after WD-i7qs/WD-m7xw, four operations are host_run_verified and four are dependency_blocked.
- The RTX 3090 currently exposes preexisting MiniMax H3 FL2VA/Ref2VA, audio VAE, video VAE, and latent-upscaler assets. The story records zero download bytes.
- Existing WD-2gyw, WD-isg9, and WD-9t9o bundles contain reusable references, settings patterns, operation maps, and fail-closed probes.

## Operator Authorization
Verbatim current instruction: Continue the remaining 56 video cells, prioritizing no-download LTX-2.5 after the tokenizer fix.

Dispatcher interpretation: continue no-download RTX 3090 evidence work after the accepted LTX-2.5 batch. Exact scope is the sixteen H3 cells named above, zero model/dependency download bytes, and no unrelated service mutation. Record this interpretation and stop if it is insufficient.

## OUT OF SCOPE
- Any other family, preset, operation, row, GUI surface, training, provider, publication, or threshold change.
- Inheriting another operation's or preset's evidence.
- Mutating accepted predecessor bundles.
- Editing protected engine semantics or the live Wan2GP tree outside an isolated run worktree.
- Downloading any model, LoRA, dependency, or dataset.

## DIFF BUDGET
About two authored surfaces: docs/video-capabilities.md plus the story evidence bundle. Keep media and logs bounded and commit no model weights.

## Boundary Map
PRODUCES:
- datasets/runs/maestro-parity/WD-VIDEO/ -> hash-backed per-cell H3 evidence or exact fail-closed boundaries
  spec: authorization, base identity, asset hashes, zero-download pre/postflight, native argv/logs, queue/exit records, output hashes/metadata, objective gates, checker result, reviewer placeholder, and matrix transition.
- docs/video-capabilities.md -> mechanically derived target-cell updates
  event: update exactly the sixteen owned planned cells and cite only this bundle.

CONSUMES:
- datasets/runs/maestro-parity/WD-2gyw/ -> accepted H3 create/KFI/audio/Hunyuan evidence and reusable references
  source: hash-copy only; never mutate the accepted bundle.
- datasets/runs/maestro-parity/WD-isg9/ -> H3 standard settings, outputs, and boundary-probe patterns
  source: hash-copy only; never inherit evidence across operation or preset.
- datasets/runs/maestro-parity/WD-9t9o/ -> H3 VDN settings and boundary-probe patterns
  source: hash-copy only; never inherit evidence across operation or preset.
- scripts/verify_maestro_parity.py -> canonical Maestro evidence checker
  event: checker exit 0 is required before any host_run_verified disposition.

## Story Acceptance Criteria
1. [State] Start from current origin/main, create/push a clean story branch and worktree, record repository/base identity, and atomically claim the story before host mutation.
2. [Unwanted] A no-download preflight hashes every required H3 asset, sets offline mode, records zero planned and actual download bytes, and stops before queue admission on absent/mismatched assets, dirty isolated source, insufficient disk/GPU headroom, or unexpected occupancy.
3. [State] Each of the sixteen target cells receives its own native operation attempt or typed boundary probe; evidence is never inherited across family, preset, or operation.
4. [State] Each successful output stores exact argv, native log, queue/exit state, SHA-256, ffprobe metadata, and at least one operation-appropriate objective gate derived from raw media.
5. [State] Each unsuccessful cell stores exact exit, failing stage, required missing asset or disabled control, before/after GPU and source state, and an honest dependency or host-implementation boundary rather than a hardware verdict.
6. [Unwanted] No download, live-tree mutation, protected-engine semantic change, threshold change, or unrelated process kill/restart occurs.
7. [State] docs/video-capabilities.md mechanically moves only the sixteen target cells from planned to evidence-backed terminal states; a transition artifact records target/unchanged counts and rejects drift elsewhere.
8. [State] Delivery passes pvg backlog lint, the canonical evidence checker, targeted video/evidence tests, release verification with release=ready and tag_created=false, protected-file parity, and git diff --check; any full-suite stop is recorded explicitly.
9. [State] The story is delivered, not self-accepted, with exact artifact paths, commit SHA, pushed branch/PR state, hashes, gate outputs, bundle size, and any independent-review requirement.

## Testing Requirements
- Real no-mock integration evidence where admitted.
- Rehash copied references before and after execution.
- Parse successful media with ffprobe and mechanically derive gates and matrix transitions.
- Run the canonical checker, targeted tests, release verification, lint, protected parity, and diff check in the story worktree.
- Do not fabricate a reviewer decision.

## Delivery Requirements
Paste authorization, asset hash result, base/source identity, host and GPU snapshots, exact command inventory, per-operation outputs/boundaries, hashes, checker and test receipts, matrix transition, bundle size, zero-download accounting, and final pushed head. If a required input fails, record the exact blocker without changing a cell.

## MANDATORY SKILLS
- pvg

## nd_contract
status: new

### evidence
- Authored from merged main 28fc76a1 and the operator's 2026-09-27 instruction to continue remaining video work after the accepted no-download LTX-2.5 batch.

### proof
- [ ] Pending atomic claim and implementation.

## Acceptance Criteria


## Design


## Notes


## History
- 2026-09-27T01:24:29Z dep_added: blocks WD-fay0
- 2026-09-27T01:24:44Z status: open -> in_progress
- 2026-09-27T01:24:44Z auto-follows: linked to predecessor WD-obkn
- 2026-09-27T01:24:44Z claimed by dev-WD-m25k

## Links
- Parent: [[WD-3nod]]
- Blocks: [[WD-fay0]]
- Follows: [[WD-obkn]]

## Comments
