---
id: WD-8h6p
title: "Hunyuan no-download video boundary batch"
status: in_progress
priority: 1
type: task
labels: [capability, video, evidence, external-integration, delivered]
parent: WD-3nod
created_at: 2026-09-27T03:22:55Z
created_by: speed
updated_at: 2026-09-27T03:46:23Z
content_hash: "sha256:c7ca8109f0b0b3374a783758f24db7d91163d7ae2d12100b1836bfe11676e397"
blocks: [WD-fay0]
assignee: dev-WD-8h6p
follows: [WD-m25k, WD-obkn]
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


## Implementation Evidence

### Authorization, source, and no-download preflight
- Verbatim authorization and scope: `datasets/runs/maestro-parity/WD-8h6p/operator-authorization.md`.
- Repository base: `8103327f`; isolated Wan2GP source: `4c93b64a47b5b0a915f2abec2ce754be98227150`.
- Six required Hunyuan model/config assets and reused source/helpers matched hashes before and after: `host-logs/11_asset_hashes_before.txt`, `host-logs/16_resume_preflight.txt`, `host-logs/91_asset_hashes_after.txt`.
- Offline mode was forced and planned/actual download bytes are zero: `host-logs/94_download_accounting.txt`.

### Real outputs and boundaries
- extend: `outputs/extend/wd_8h6p_extend.mp4`; SHA-256 `19eb4928aa6621dc1742e23e348cae7bbfed5138cb91e0fa155057e0e3e4f58a`; duration `5.041667 s`.
- retake: `outputs/retake/wd_8h6p_retake.mp4`; SHA-256 `ca2b45eb74683548ddcbb261b7fdf367ef1d36811bffc379459eb6198149f818`; first-frame SSIM `0.448707`.
- edit: `outputs/edit/wd_8h6p_edit.mp4`; SHA-256 `c6403260e3031fed37e3ce3f7dc4f6c4dd31c9595bd71e6bb2d3fc92d85b803b`; source PSNR `18.160307 dB`.
- repaint: `outputs/repaint/wd_8h6p_repaint.mp4`; SHA-256 `c1d78362c20078e8830cc53c0decd54a8edf973bd3c1ca58c0094bc58759e57e`; source PSNR `17.875626 dB`.
- recast: `outputs/recast/wd_8h6p_recast.mp4`; SHA-256 `3784b2b8533bc6c05a37722248dd9942b44676c210c0071dbf18131fb668fe38`; source PSNR `17.448752 dB`.
- upscale: `outputs/upscale/wd_8h6p_upscale.mp4`; SHA-256 `1b8dc53cf5c084b104da2a5db189a5dc4ddc7f9e0b8f6da16c7013a8f186bf44`; dimensions `1664x960`.
- blend is an exact unsupported host boundary because the T2V model definition lacks `reference_video_max_frames`: `boundary-evidence.json`.

### CI/Test Results
Commands run:
- `uv run --frozen --extra dev pytest -q tests/test_maestro_parity_evidence.py tests/test_video_capabilities.py --junitxml=datasets/runs/maestro-parity/WD-8h6p/targeted-tests.xml`
- `uv run --frozen --extra dev python scripts/verify_maestro_parity.py datasets/runs/maestro-parity/WD-8h6p`
- `pvg verify docs/video-capabilities.md datasets/runs/maestro-parity/WD-8h6p/build_evidence.py datasets/runs/maestro-parity/WD-8h6p/promote_outputs.py datasets/runs/maestro-parity/WD-8h6p/host-scripts/*.sh`
- `pvg lint --backlog`
- `uv run --frozen --extra dev wgp release verify`
- `git diff --check`
- `git diff --exit-code 8103327f -- services/jobs/queue.py services/director/renderers/policy.py services/director/wiring.py services/jobs/preflight.py scripts/run_film.py`

Summary: targeted pytest PASS 110/110 with `errors=0`, `failures=0`, `skipped=0`; pvg verify PASS; backlog lint PASS 141 scanned, 0 errors, 0 review findings; release at clean implementation head is `release=ready` with `tag_created=false`; protected parity and diff-check PASS. Canonical checker is pending only independent reviewer decision/links.

### Matrix transition
`matrix-transition-check.json` records seven target-cell transitions, zero planned Hunyuan target cells, seven host_run_verified cells, and two unsupported cells including the pre-existing outpaint boundary.

### AC Verification
| AC | Result | Evidence |
| --- | --- | --- |
| 1 | PASS | Clean pushed branch/worktree and atomic claim |
| 2 | PASS | Asset/source hashes, offline mode, disk/GPU checks, zero downloads |
| 3 | PASS | Six per-operation outputs plus one exact blend boundary |
| 4 | PASS | Hashes, argv/logs, ffprobe metadata, duration/SSIM/PSNR/dimension gates |
| 5 | PASS | Exact blend exit, stack tail, and missing model-definition field |
| 6 | PASS | Isolated source, protected files unchanged, no unrelated process action |
| 7 | PASS | Exactly seven matrix cells changed; zero target planned cells |
| 8 | PASS pending independent reviewer | All local gates pass; canonical checker awaits reviewer fields only |

### Branch and PR
Commit SHA: 40e4a48a3f4634028467c26b8681a52d1d40954f
Branch: `story/WD-8h6p`
PR: https://github.com/jmanhype/wangp-dspy/pull/206
Bundle: 143 files, 36,883,770 bytes.

## History
- 2026-09-27T03:22:56Z dep_added: blocks WD-fay0
- 2026-09-27T03:23:11Z status: open -> in_progress
- 2026-09-27T03:23:11Z auto-follows: linked to predecessor WD-m25k
- 2026-09-27T03:23:11Z claimed by dev-WD-8h6p
- 2026-09-27T03:46:23Z status: in_progress -> in_progress
- 2026-09-27T03:46:23Z auto-follows: linked to predecessor WD-obkn

## Links
- Parent: [[WD-3nod]]
- Blocks: [[WD-fay0]]
- Follows: [[WD-m25k]], [[WD-obkn]]

## Comments

## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-26.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.
