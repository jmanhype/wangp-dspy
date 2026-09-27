---
id: WD-m25k
title: "H3 KFI/audio-refinement no-download video batch"
status: in_progress
priority: 1
type: task
labels: [capability, video, evidence, external-integration, delivered]
parent: WD-3nod
created_at: 2026-09-27T01:24:28Z
created_by: speed
updated_at: 2026-09-27T02:39:36Z
content_hash: "sha256:c1fe238ed57a1a865423c14b19d68210040eaf9e3f68b20af9057ca624987fce"
blocks: [WD-fay0]
assignee: dev-WD-m25k
follows: [WD-obkn, WD-7fvx]
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
## Implementation Evidence (DELIVERED FOR REVIEW)

### Authorization, source, and no-download preflight
- Verbatim operator scope and bounded interpretation: `datasets/runs/maestro-parity/WD-m25k/operator-authorization.md`.
- Base repository commit: `28fc76a1`; isolated Wan2GP commit: `4c93b64a47b5b0a915f2abec2ce754be98227150`.
- All four required H3 model assets and all reused source/helper assets matched their expected SHA-256 values before execution: `host-logs/11_asset_hashes_before.txt`.
- Final hashes also matched: `host-logs/91_asset_hashes_after.txt`.
- Offline mode was forced; planned and actual download bytes are zero: `host-logs/94_download_accounting.txt`.
- Initial `pip check` reported only the preexisting Gradio/DeepFilterNet environment conflicts. It was retained as advisory evidence, with no dependency mutation, in `host-logs/13_python_pip_check_advisory.txt` and `host-logs/16_resume_preflight.txt`.

### Real outputs
- KFI repaint: `outputs/kfi_repaint/wd_m25k_kfi_repaint.mp4`; SHA-256 `421921a18a43edfe7d8d14848a33a326403d7dbc4a015132f38db45cbfd116cf`; source PSNR `20.118892 dB`.
- KFI upscale: `outputs/kfi_upscale/wd_m25k_kfi_upscale.mp4`; SHA-256 `e0967683615ab24bb2536d51040e68667f88774873d4f531100dda81fd4a3249`; 960x1664.
- Audio-refinement repaint: `outputs/audio_repaint/wd_m25k_audio_repaint.mp4`; SHA-256 `a604bb30d15ff05f8a2c9f57b2125f1cb96c80e650e699bfc0351b94aaeefa53`; source PSNR `21.554022 dB`.
- Audio-refinement upscale: `outputs/audio_upscale/wd_m25k_audio_upscale.mp4`; SHA-256 `7b3b0ea53d287a55bdd114b559816d06a258ee6b835c972a16eb2d0551cab6fa`; 960x1664.
- Exact media metadata, hashes, argv, logs, host snapshots, and objective measurements are in `evidence.json`, `objective-measurements.json`, `outputs/`, and `host-logs/`.

### Typed boundaries
- All twelve unsuccessful/non-qualifying target cells have individual native or seed-specific records in `boundary-evidence.json`.
- KFI create requires a reference; KFI extend/blend/edit/outpaint fail on `resolved_frame_index`; KFI recast requires Ref2VA.
- Audio create/extend/retake/recast require a control video; FL2VA audio blend lacks `reference_video_max_frames`; audio outpaint emitted a real MP4 but stayed 480x832, so it is correctly `unsupported`, not host-run verified.
- The first mtime-based mapping of the two repaint outputs was quarantined and rebound by seed; the correction is recorded in `runtime_notes.initial_output_mapping_error`.

### Matrix and gates
- `matrix-transition-check.json`: exactly 16 target cells changed, 0 target cells remain planned, 6 row cells are host_run_verified including the two already accepted predecessor cells, and 12 are unsupported boundaries.
- Targeted tests: 110/110 PASS; JUnit `tests=110`, `errors=0`, `failures=0`, `skipped=0` (`targeted-tests-counters.json`).
- `pvg verify`: PASS; backlog lint: 140 scanned, 0 errors, 0 review findings.
- Release verification at clean implementation head: `release=ready`, `tag_created=false`.
- Protected-file parity and `git diff --check`: PASS.
- Canonical checker currently fails exactly and only because `reviewer_verdict.decision` is pending and links are empty. The developer did not self-approve.

### Branch and PR
- Implementation commit: `a77b901e83372b00a04f0c45542f66ffd3c81b72`.
- Final pushed evidence head: `cb18f108`.
- Branch: `story/WD-m25k`.
- PR: https://github.com/jmanhype/wangp-dspy/pull/205

## History
- 2026-09-27T01:24:29Z dep_added: blocks WD-fay0
- 2026-09-27T01:24:44Z status: open -> in_progress
- 2026-09-27T01:24:44Z auto-follows: linked to predecessor WD-obkn
- 2026-09-27T01:24:44Z claimed by dev-WD-m25k
- 2026-09-27T02:39:36Z status: in_progress -> in_progress
- 2026-09-27T02:39:36Z auto-follows: linked to predecessor WD-7fvx

## Links
- Parent: [[WD-3nod]]
- Blocks: [[WD-fay0]]
- Follows: [[WD-obkn]], [[WD-7fvx]]

## Comments
