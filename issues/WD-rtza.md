---
id: WD-rtza
title: "H3 KFI/audio-refinement no-download video batch"
status: open
priority: 1
type: task
labels: [capability, video, evidence, external-integration]
parent: WD-3nod
created_at: 2026-09-27T01:22:06Z
created_by: speed
updated_at: 2026-09-27T01:22:17Z
content_hash: "sha256:2d59df8988900d4494af8fde76c91a0229cf9f4de10cec21976b8a37c14aab04"
---

## Description

## Description

Continue the Maestro video-parity program with the next zero-download MiniMax H3 batch. This story owns exactly the sixteen still-planned cells in the kfi_frames_injection and h3_audio_refinement rows. It must produce either per-cell real host-run evidence or an exact fail-closed implementation/dependency boundary; it must not inherit another operation's evidence or label a missing asset as hardware infeasibility.

## Embedded Current State

At merged main 28fc76a1, the target rows are:

- minimax_h3/kfi_frames_injection: create, extend, blend, edit, outpaint, repaint, recast, and upscale are planned; retake is already host_run_verified.
- minimax_h3/h3_audio_refinement: create, extend, blend, retake, outpaint, repaint, recast, and upscale are planned; edit is already host_run_verified.
- LTX-2.5 is no longer the highest-priority zero-download target: after WD-i7qs/WD-m7xw, its four executable operations are host_run_verified and its four missing-LoRA operations are dependency_blocked.
- The RTX 3090 host currently has the preexisting MiniMax H3 FL2VA/Ref2VA, audio VAE, video VAE, and latent upscaler assets; this story must hash them and perform zero download bytes.
- Existing WD-2gyw, WD-isg9, and WD-9t9o bundles contain reusable source assets, native settings patterns, operation maps, and fail-closed host probes.

## Operator Authorization

Verbatim current instruction: Continue the remaining 56 video cells, prioritizing no-download LTX-2.5 after the tokenizer fix. The dispatcher interprets this as continued no-download RTX 3090 evidence work after the accepted LTX-2.5 batch. The exact scope of this story is limited to the sixteen H3 cells named above, with zero model/dependency download bytes and no unrelated service mutation. The worker must record this interpretation verbatim in the evidence bundle and stop if that is insufficient.

## Boundary Map

PRODUCES:
- datasets/runs/maestro-parity/WD-rtza/ -> hash-backed H3 KFI/audio-refinement operation evidence or exact fail-closed boundaries
  spec: authorization, base identity, asset hashes, zero-download pre/postflight, native argv and logs, queue/exit records, output hashes and media metadata, objective gates, checker result, reviewer placeholder, and matrix transition.
- docs/video-capabilities.md -> mechanically derived target-cell updates
  event: cite only this bundle; leave every non-target cell byte-for-byte unchanged.

CONSUMES:
- WD-2gyw: H3 create/KFI/audio/Hunyuan evidence and reusable local generated references
  source: hash-copy only; never mutate the accepted bundle.
- WD-isg9: H3 standard operation settings, outputs, and boundary-probe patterns
  source: hash-copy only; never inherit evidence across operation or preset.
- WD-9t9o: H3 VDN operation settings and boundary-probe patterns
  source: hash-copy only; never inherit evidence across operation or preset.
- WD-i7qs: accepted LTX tokenizer fix and offline run discipline
  source: pattern only unless a hash-matched H3 runtime file is explicitly required.
- WD-651z: scripts/verify_maestro_parity.py
  event: canonical checker must pass before a host_run_verified disposition.

## Acceptance Criteria

1. [State] The story starts from current origin/main, uses a clean pushed story worktree, records repository/base identity before work, and atomically claims this story before any host mutation.
2. [Unwanted] A no-download preflight hashes every required H3 asset, sets offline mode, records zero planned and actual download bytes, and stops before queue admission on absent/mismatched assets, dirty isolated source, insufficient disk/GPU headroom, or unexpected occupancy.
3. [State] Every one of the sixteen target cells receives its own native operation attempt or a typed boundary probe; operation evidence is never inherited across family, preset, or operation.
4. [State] Every successful output records exact argv, native log, queue/exit state, SHA-256, ffprobe metadata, and at least one operation-appropriate objective gate derived from raw media.
5. [State] Every unsuccessful cell records exact exit, failing stage, required absent/mismatched asset or disabled control, GPU/source state before and after, and an honest dependency_blocked or unsupported_host_implementation boundary rather than a hardware verdict.
6. [Unwanted] No model, LoRA, dependency, provider, or dataset download; no live Wan2GP-tree mutation except an isolated worktree; no threshold or protected engine semantic change; no unrelated process kill/restart.
7. [State] docs/video-capabilities.md changes only the sixteen owned target cells from planned to an evidence-backed terminal state; a matrix-transition artifact records target and unchanged-cell counts and rejects drift elsewhere.
8. [State] Delivery passes pvg lint --backlog, the canonical Maestro evidence checker, targeted video/evidence tests, wgp release verify (release=ready and tag_created=false), protected-file parity, and git diff --check; any full-suite boundary must be recorded explicitly rather than summarized as pass.
9. [State] The story is delivered, not self-accepted, with exact artifact paths, commit SHA, branch/PR state, hashes, gate outputs, bundle size, and any unresolved independent-review requirement.

## Testing Requirements

Use real no-mock integration evidence where admitted. Rehash all copied references before and after. Parse all media from ffprobe. Mechanically derive gates and matrix transitions. Run the canonical checker and targeted tests in the story worktree. Do not fabricate a reviewer decision.

## nd_contract

status: new

### evidence

- Created from merged main 28fc76a1 and the operator's 2026-09-27 instruction to continue the remaining video cells after the accepted no-download LTX-2.5 batch.

### proof

- [ ] Pending atomic claim and implementation.

## Acceptance Criteria


## Design


## Notes


## History


## Links
- Parent: [[WD-3nod]]

## Comments

## Description

Continue the Maestro video-parity program with the next zero-download MiniMax H3 batch. This story owns exactly the sixteen still-planned cells in the kfi_frames_injection and h3_audio_refinement rows. It must produce either per-cell real host-run evidence or an exact fail-closed implementation/dependency boundary; it must not inherit another operation's evidence or label a missing asset as hardware infeasibility.

## Embedded Current State

At merged main 28fc76a1, the target rows are:

- minimax_h3/kfi_frames_injection: create, extend, blend, edit, outpaint, repaint, recast, and upscale are planned; retake is already host_run_verified.
- minimax_h3/h3_audio_refinement: create, extend, blend, retake, outpaint, repaint, recast, and upscale are planned; edit is already host_run_verified.
- LTX-2.5 is no longer the highest-priority zero-download target: after WD-i7qs/WD-m7xw, its four executable operations are host_run_verified and its four missing-LoRA operations are dependency_blocked.
- The RTX 3090 host currently has the preexisting MiniMax H3 FL2VA/Ref2VA, audio VAE, video VAE, and latent upscaler assets; this story must hash them and perform zero download bytes.
- Existing WD-2gyw, WD-isg9, and WD-9t9o bundles contain reusable source assets, native settings patterns, operation maps, and fail-closed host probes.

## Operator Authorization

Verbatim current instruction: Continue the remaining 56 video cells, prioritizing no-download LTX-2.5 after the tokenizer fix. The dispatcher interprets this as continued no-download RTX 3090 evidence work after the accepted LTX-2.5 batch. The exact scope of this story is limited to the sixteen H3 cells named above, with zero model/dependency download bytes and no unrelated service mutation. The worker must record this interpretation verbatim in the evidence bundle and stop if that is insufficient.

## Boundary Map

PRODUCES:
- datasets/runs/maestro-parity/WD-NEW/ -> hash-backed H3 KFI/audio-refinement operation evidence or exact fail-closed boundaries
  spec: authorization, base identity, asset hashes, zero-download pre/postflight, native argv and logs, queue/exit records, output hashes and media metadata, objective gates, checker result, reviewer placeholder, and matrix transition.
- docs/video-capabilities.md -> mechanically derived target-cell updates
  event: cite only this bundle; leave every non-target cell byte-for-byte unchanged.

CONSUMES:
- WD-2gyw: H3 create/KFI/audio/Hunyuan evidence and reusable local generated references
  source: hash-copy only; never mutate the accepted bundle.
- WD-isg9: H3 standard operation settings, outputs, and boundary-probe patterns
  source: hash-copy only; never inherit evidence across operation or preset.
- WD-9t9o: H3 VDN operation settings and boundary-probe patterns
  source: hash-copy only; never inherit evidence across operation or preset.
- WD-i7qs: accepted LTX tokenizer fix and offline run discipline
  source: pattern only unless a hash-matched H3 runtime file is explicitly required.
- WD-651z: scripts/verify_maestro_parity.py
  event: canonical checker must pass before a host_run_verified disposition.

## Acceptance Criteria

1. [State] The story starts from current origin/main, uses a clean pushed story worktree, records repository/base identity before work, and atomically claims this story before any host mutation.
2. [Unwanted] A no-download preflight hashes every required H3 asset, sets offline mode, records zero planned and actual download bytes, and stops before queue admission on absent/mismatched assets, dirty isolated source, insufficient disk/GPU headroom, or unexpected occupancy.
3. [State] Every one of the sixteen target cells receives its own native operation attempt or a typed boundary probe; operation evidence is never inherited across family, preset, or operation.
4. [State] Every successful output records exact argv, native log, queue/exit state, SHA-256, ffprobe metadata, and at least one operation-appropriate objective gate derived from raw media.
5. [State] Every unsuccessful cell records exact exit, failing stage, required absent/mismatched asset or disabled control, GPU/source state before and after, and an honest dependency_blocked or unsupported_host_implementation boundary rather than a hardware verdict.
6. [Unwanted] No model, LoRA, dependency, provider, or dataset download; no live Wan2GP-tree mutation except an isolated worktree; no threshold or protected engine semantic change; no unrelated process kill/restart.
7. [State] docs/video-capabilities.md changes only the sixteen owned target cells from planned to an evidence-backed terminal state; a matrix-transition artifact records target and unchanged-cell counts and rejects drift elsewhere.
8. [State] Delivery passes pvg lint --backlog, the canonical Maestro evidence checker, targeted video/evidence tests, wgp release verify (release=ready and tag_created=false), protected-file parity, and git diff --check; any full-suite boundary must be recorded explicitly rather than summarized as pass.
9. [State] The story is delivered, not self-accepted, with exact artifact paths, commit SHA, branch/PR state, hashes, gate outputs, bundle size, and any unresolved independent-review requirement.

## Testing Requirements

Use real no-mock integration evidence where admitted. Rehash all copied references before and after. Parse all media from ffprobe. Mechanically derive gates and matrix transitions. Run the canonical checker and targeted tests in the story worktree. Do not fabricate a reviewer decision.

## nd_contract

status: new

### evidence

- Created from merged main 28fc76a1 and the operator's 2026-09-27 instruction to continue the remaining video cells after the accepted no-download LTX-2.5 batch.

### proof

- [ ] Pending atomic claim and implementation.

## Acceptance Criteria


## Design


## Notes


## History


## Links
- Parent: [[WD-3nod]]

## Comments
