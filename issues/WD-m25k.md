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
updated_at: 2026-09-27T02:41:45Z
content_hash: "sha256:26166a925e46067af0ec66eb8a23ef07723f3a06602929a9a56291fa38f660d3"
blocks: [WD-fay0]
assignee: dev-WD-m25k
follows: [WD-obkn, WD-7fvx, WD-m7xw, WD-5k28]
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

## Acceptance Criteria

## Design

## Notes
## Implementation Evidence

### Authorization, source, and no-download preflight
- Verbatim operator scope and bounded interpretation: `datasets/runs/maestro-parity/WD-m25k/operator-authorization.md`.
- Base repository commit: `28fc76a1`; isolated Wan2GP commit: `4c93b64a47b5b0a915f2abec2ce754be98227150`.
- All four required H3 model assets and every reused source/helper asset matched expected SHA-256 values before execution: `datasets/runs/maestro-parity/WD-m25k/host-logs/11_asset_hashes_before.txt`.
- Final hashes matched: `datasets/runs/maestro-parity/WD-m25k/host-logs/91_asset_hashes_after.txt`.
- Offline mode was forced; planned and actual download bytes are zero: `datasets/runs/maestro-parity/WD-m25k/host-logs/94_download_accounting.txt`.
- Initial `pip check` reported only preexisting Gradio/DeepFilterNet environment conflicts. It was retained as advisory evidence with no dependency mutation: `datasets/runs/maestro-parity/WD-m25k/host-logs/13_python_pip_check_advisory.txt`.

### Real outputs
- KFI repaint: `datasets/runs/maestro-parity/WD-m25k/outputs/kfi_repaint/wd_m25k_kfi_repaint.mp4`; SHA-256 `421921a18a43edfe7d8d14848a33a326403d7dbc4a015132f38db45cbfd116cf`; source PSNR `20.118892 dB`.
- KFI upscale: `datasets/runs/maestro-parity/WD-m25k/outputs/kfi_upscale/wd_m25k_kfi_upscale.mp4`; SHA-256 `e0967683615ab24bb2536d51040e68667f88774873d4f531100dda81fd4a3249`; 960x1664.
- Audio-refinement repaint: `datasets/runs/maestro-parity/WD-m25k/outputs/audio_repaint/wd_m25k_audio_repaint.mp4`; SHA-256 `a604bb30d15ff05f8a2c9f57b2125f1cb96c80e650e699bfc0351b94aaeefa53`; source PSNR `21.554022 dB`.
- Audio-refinement upscale: `datasets/runs/maestro-parity/WD-m25k/outputs/audio_upscale/wd_m25k_audio_upscale.mp4`; SHA-256 `7b3b0ea53d287a55bdd114b559816d06a258ee6b835c972a16eb2d0551cab6fa`; 960x1664.

### Typed boundaries
- All twelve non-verified target cells have individual native or seed-specific records in `datasets/runs/maestro-parity/WD-m25k/boundary-evidence.json`.
- KFI create requires a reference; KFI extend/blend/edit/outpaint fail on `resolved_frame_index`; KFI recast requires Ref2VA.
- Audio create/extend/retake/recast require a control video; FL2VA audio blend lacks `reference_video_max_frames`; audio outpaint emitted an MP4 but stayed 480x832, so it is `unsupported`, not host-run verified.
- The initial mtime-based mapping of two repaint outputs was quarantined and rebound by seed; the correction is recorded in `evidence.json.runtime_notes.initial_output_mapping_error`.

### CI/Test Results
Commands run:
- `uv run --frozen --extra dev pytest -q tests/test_maestro_parity_evidence.py tests/test_video_capabilities.py --junitxml=datasets/runs/maestro-parity/WD-m25k/targeted-tests.xml`
- `uv run --frozen --extra dev python scripts/verify_maestro_parity.py datasets/runs/maestro-parity/WD-m25k`
- `pvg verify docs/video-capabilities.md datasets/runs/maestro-parity/WD-m25k/build_evidence.py datasets/runs/maestro-parity/WD-m25k/host-scripts/*.sh`
- `pvg lint --backlog`
- `uv run --frozen --extra dev wgp release verify`
- `git diff --check`
- `git diff --exit-code 28fc76a1 -- services/jobs/queue.py services/director/renderers/policy.py services/director/wiring.py services/jobs/preflight.py scripts/run_film.py`

Summary: targeted pytest PASS 110/110 with `errors=0`, `failures=0`, `skipped=0`; pvg verify PASS; backlog lint PASS 140 scanned, 0 errors, 0 review findings; release verification at clean implementation head reports `release=ready` and `tag_created=false`; protected-file parity and diff-check PASS. Canonical checker is pending exactly and only the independent PM reviewer decision/links; the developer did not self-approve.

### Matrix transition
`datasets/runs/maestro-parity/WD-m25k/matrix-transition-check.json` records exactly 16 changed target cells, 0 target cells left planned, 6 host_run_verified row cells including the two predecessor-verified cells, and 12 unsupported boundaries.

### AC Verification
| AC | Result | Evidence |
| --- | --- | --- |
| 1 | PASS | Clean pushed branch/worktree and atomic claim; `host-logs/00_host_before.txt` |
| 2 | PASS | Model/source hashes, offline mode, disk/GPU preflight, and zero download accounting |
| 3 | PASS | Four output records plus twelve per-cell boundary records |
| 4 | PASS | Four hashed MP4s, argv/logs, ffprobe metadata, PSNR/dimension gates |
| 5 | PASS | Exact exits, error tails, source/GPU snapshots, and typed boundary reasons |
| 6 | PASS | Isolated source, unchanged protected files, zero downloads, no unrelated service action |
| 7 | PASS | 16-cell matrix-transition artifact with zero target planned cells |
| 8 | PASS pending independent reviewer | Targeted tests, lint, release, parity, diff pass; canonical checker awaits independent reviewer only |
| 9 | PASS | Delivered, pushed branch/PR, exact paths, hashes, gates, bundle size/count, no self-acceptance |

### Branch, PR, and bundle
- Implementation commit SHA: `a77b901e83372b00a04f0c45542f66ffd3c81b72`.
- Final pushed evidence head: `cb18f108`.
- Branch: `story/WD-m25k`.
- PR: https://github.com/jmanhype/wangp-dspy/pull/205
- Bundle: 204 files, 31,017,923 bytes (`bundle-file-count.txt`, `bundle-size.txt`).


## History
- 2026-09-27T01:24:29Z dep_added: blocks WD-fay0
- 2026-09-27T01:24:44Z status: open -> in_progress
- 2026-09-27T01:24:44Z auto-follows: linked to predecessor WD-obkn
- 2026-09-27T01:24:44Z claimed by dev-WD-m25k
- 2026-09-27T02:39:36Z status: in_progress -> in_progress
- 2026-09-27T02:39:36Z auto-follows: linked to predecessor WD-7fvx
- 2026-09-27T02:41:33Z status: in_progress -> in_progress
- 2026-09-27T02:41:34Z auto-follows: linked to predecessor WD-m7xw
- 2026-09-27T02:41:46Z status: in_progress -> in_progress
- 2026-09-27T02:41:46Z auto-follows: linked to predecessor WD-5k28

## Links
- Parent: [[WD-3nod]]
- Blocks: [[WD-fay0]]
- Follows: [[WD-obkn]], [[WD-7fvx]], [[WD-m7xw]], [[WD-5k28]]

## Comments

