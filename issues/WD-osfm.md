---
id: WD-osfm
title: "LTX-2.3 authorized download video batch"
status: in_progress
priority: 1
type: task
labels: [capability, video, evidence, external-integration, delivered]
parent: WD-3nod
created_at: 2026-09-27T16:21:08Z
created_by: speed
updated_at: 2026-09-27T19:43:07Z
content_hash: "sha256:e2f1764bb517cac806e4d7fc54a6ff39dfd527dd9554d92ca50a3511257c5f51"
blocks: [WD-fay0]
assignee: dev-WD-osfm
follows: [WD-28i5, WD-ycjg]
---

## Description
## USER INTENT AND DISPATCHER DECISION
The operator was asked which remaining download batch to authorize and replied verbatim: "you decide."

The dispatcher now selects LTX-2.3 as the final planned video row. After accepted SCAIL-2 and Wan/2GP work, LTX-2.3 is the only remaining planned row. The old 29,531,884,062-byte Comfy FP8 checkpoint does not match WanGP packaging, so this story selects the native WanGP LTX-2.3 Distilled 1.0 GGUF Q4_K_M Light checkpoint.

The delivered bundle stores one terminal disposition for every LTX-2.3 cell and returns a fail-closed checker verdict rather than prose-only completion.

## Embedded Current State
At merged main 0f91e83c the video matrix has 35 host_run_verified cells, 51 unsupported cells, 4 dependency_blocked cells, and 9 planned cells. All nine planned cells are LTX-2.3. This story owns create, extend, blend, retake, edit, outpaint, repaint, recast, and upscale.

Host free space is 21,203,777,584 bytes. The selected download set is 35,379,235,525 bytes and needs storage preparation. A superseded, unused 34,038,903,007-byte MiniMax H3 full-int8 checkpoint is present at `/home/straughter/Wan2GP/ckpts/MiniMax-H3-FL2VA_int8_convrot.safetensors` with SHA-256 `83a36b67776962f44087f2f7c12d95791393f3cce1ef898efc90405216e7b0c0`. It will be byte-verified and moved to the Mac offload area, not deleted blindly. The active rank8 H3 checkpoint remains untouched.

## Storage Boundary
- Offload destination: `/Users/Shared/HermesWorkspace/model-offload/wangp-3090/MiniMax-H3-FL2VA_int8_convrot.safetensors`
- Destination has at least 100 GiB free.
- Record before/after hashes and sizes on both hosts.
- Remove the remote copy only after the local copy is byte-identical.
- Preserve every other model and checkpoint.

## Exact Authorized Downloads
| Asset | Destination | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| ltx-2.3-22b-distilled-Q4_K_M_light.gguf | /home/straughter/Wan2GP/ckpts/ltx-2.3-22b-distilled-Q4_K_M_light.gguf | 12971904032 | e324dbdacfc228e02e79e2f952c8274b16ba155d029db5f9abdd55a311325208 |
| gemma-3 int8 encoder | /home/straughter/Wan2GP/ckpts/gemma-3-12b-it-qat-q4_0-unquantized/gemma-3-12b-it-qat-q4_0-unquantized_quanto_bf16_int8.safetensors | 13210647730 | 1fad55b5df6c660c7982985c8ced76369114b1d31bbec93fbecc66a8bf30f36a |
| ltx-2.3 video VAE | /home/straughter/Wan2GP/ckpts/ltx-2.3-22b_vae.safetensors | 1452263226 | 646b77e252d08ec3a6e24fccb4bf53c80c7cf52025272f155f30fe2b84f0e1d4 |
| ltx-2.3 audio VAE | /home/straughter/Wan2GP/ckpts/ltx-2.3-22b_audio_vae.safetensors | 106538084 | c99a673c32ad0f7f6349df58466c0a1c2f398e314484a33988794322375cbde4 |
| ltx-2.3 vocoder | /home/straughter/Wan2GP/ckpts/ltx-2.3-22b_vocoder.safetensors | 258347744 | 3624e13fcf9fa8b2a1437bd9eb628c3a436282125e9e28ca1071142a4946e3f5 |
| ltx-2.3 text projection | /home/straughter/Wan2GP/ckpts/ltx-2.3-22b_text_embedding_projection.safetensors | 2312151888 | 985bba2295af346ac74b627afc8d27f4b5f277fb20c87968d569b4bb5d7fd28f |
| ltx-2.3 embeddings connector | /home/straughter/Wan2GP/ckpts/ltx-2.3-22b_embeddings_connector.safetensors | 4032404584 | eb37b1ec8024a311e863bcf5a684bdb6c64707216c3754c6f4078eae908d0600 |
| ltx-2.3 spatial upscaler | /home/straughter/Wan2GP/ckpts/ltx-2.3-spatial-upscaler-x2-1.1.safetensors | 995743560 | 5f416311fa8172b65af67530758964708d29a317b830d689a51143b7f91913ed |
| Gemma added_tokens.json | /home/straughter/Wan2GP/ckpts/gemma-3-12b-it-qat-q4_0-unquantized/added_tokens.json | 35 | 50b2f405ba56a26d4913fd772089992252d7f942123cc0a034d96424221ba946 |
| Gemma chat_template.json | /home/straughter/Wan2GP/ckpts/gemma-3-12b-it-qat-q4_0-unquantized/chat_template.json | 1615 | fe16baf728db49457cde32802cd7efc0ac8a7a9877dbe22fe3322b2d9dc6ccd9 |
| Gemma config_light.json | /home/straughter/Wan2GP/ckpts/gemma-3-12b-it-qat-q4_0-unquantized/config_light.json | 907 | c425c32bd6ea9ef8542ca0567fb903be7b728dc3b454d2511adecfc85978bb5c |
| Gemma generation_config.json | /home/straughter/Wan2GP/ckpts/gemma-3-12b-it-qat-q4_0-unquantized/generation_config.json | 173 | 13da6aad6852a008419f46df754b3452fc96387a4213c25811509d474e5a4776 |
| Gemma preprocessor_config.json | /home/straughter/Wan2GP/ckpts/gemma-3-12b-it-qat-q4_0-unquantized/preprocessor_config.json | 570 | f688d6bb20c5017601c4011de7ca656da8485b540b05013efdaf986c0fcc918d |
| Gemma processor_config.json | /home/straughter/Wan2GP/ckpts/gemma-3-12b-it-qat-q4_0-unquantized/processor_config.json | 70 | 3ffd5f11778dc73e2b69b3c00535e4121e1badf7018136263cd17b5b34fbaa53 |
| Gemma special_tokens_map.json | /home/straughter/Wan2GP/ckpts/gemma-3-12b-it-qat-q4_0-unquantized/special_tokens_map.json | 662 | 2f7b0adf4fb469770bb1490e3e35df87b1dc578246c5e7e6fc76ecf33213a397 |
| Gemma tokenizer.json | /home/straughter/Wan2GP/ckpts/gemma-3-12b-it-qat-q4_0-unquantized/tokenizer.json | 33384570 | 7d4046bf0505a327dd5a0abbb427ecd4fc82f99c2ceaa170bc61ecde12809b0c |
| Gemma tokenizer.model | /home/straughter/Wan2GP/ckpts/gemma-3-12b-it-qat-q4_0-unquantized/tokenizer.model | 4689074 | 1299c11d7cf632ef3b4e11937501358ada021bbdf7c47638d13c0ee982f2e79c |
| Gemma tokenizer_config.json | /home/straughter/Wan2GP/ckpts/gemma-3-12b-it-qat-q4_0-unquantized/tokenizer_config.json | 1157001 | 31e860fdfa360fa5aa58fe93252799facde5a52d1352f77d45978ab2a7e9eeb1 |

Total exact downloads: 35,379,235,525 bytes. The required temporal upscaler is already present under the LTX-2.5 filename with identical SHA-256 `2bc3300f2b3c3c1834d72164fbf13a3b9fd73e5a741e8a2c3f4035f89a75c3fe`; create a link only after hash verification, with zero download bytes.

## Boundary Map
PRODUCES:
- datasets/runs/maestro-parity/WD-osfm/ -> authorized storage offload, LTX-2.3 downloads, and nine-cell evidence
  spec: offload hashes/size, download report, shared-link proof, isolated source identity, native argv/logs, outputs/boundaries, media gates, checker result, reviewer decision, and matrix transition.
- docs/video-capabilities.md -> nine LTX-2.3 target-cell updates
  event: change only the nine owned planned cells.

CONSUMES:
- datasets/runs/maestro-parity/WD-ycjg/outputs/create/wd_ycjg_create.mp4 -> local person-bearing control/reference
  source: hash-copy only.
- datasets/runs/maestro-parity/WD-m7xw/evidence.json -> proven LTX tokenizer/offload execution patterns
  source: pattern only; no inherited evidence.
- scripts/verify_maestro_parity.py -> canonical evidence checker
  event: checker exit 0 is required for each host_run_verified disposition.

## Story Acceptance Criteria
1. [State] Start from current origin/main, create/push a clean story branch/worktree, record base identity, and atomically claim the story before storage or network mutation.
2. [State] Byte-verify and offload exactly the superseded full-int8 H3 checkpoint to the declared Mac path; remove the remote copy only after local size and SHA-256 match, and leave every other checkpoint untouched.
3. [State] Download only the eighteen declared files, verify every size/hash, create the temporal-upscaler link from the hash-identical existing file, and record all storage/network accounting.
4. [State] Give each of the nine target cells its own native attempt or exact typed boundary; evidence cannot be inherited across operations.
5. [State] Every successful output stores argv, native log, queue/exit state, SHA-256, ffprobe metadata, contact sheet/first frame, and an operation-appropriate objective gate.
6. [State] Every unsuccessful cell stores exact exit/failing stage, missing control or dependency, before/after GPU/source state, and an honest host-implementation or dependency boundary rather than a hardware verdict.
7. [Unwanted] No undeclared download, live dependency mutation, protected-engine semantic change, threshold change, training, provider spend, unrelated process action, or deletion of an unverified artifact occurs.
8. [State] docs/video-capabilities.md mechanically changes exactly the nine owned planned cells; a transition artifact proves zero LTX-2.3 planned cells and no unrelated matrix change.
9. [State] Delivery passes pvg lint, targeted video/evidence tests, canonical checker after independent review, release verification with release=ready and tag_created=false, protected-file parity, and git diff --check; it is delivered and independently accepted without self-approval.

## Testing Requirements
- Real no-mock storage transfer and host integration.
- Verify all copied/downloaded/linked files by exact SHA-256 and byte size.
- Probe all successful media and mechanically derive gates and matrix transitions.
- Run canonical checker, targeted tests, pvg lint, release verify, protected parity, and diff check.

## Delivery Requirements
Record authorization/decision, offload proof, download bytes, hashes, disk/GPU snapshots, command inventory, per-operation outputs/boundaries, matrix transition, gates, bundle size, pushed head, and PR. Stop on any undeclared network need, storage mismatch, or missing input.

## MANDATORY SKILLS
- pvg

## nd_contract
status: new

### evidence
- Authored from merged main 0f91e83c, live host storage inspection, Hugging Face metadata, WanGP native defaults, and the operator's "you decide" authorization.

### proof
- [ ] Pending atomic claim, verified offload, bounded download, and implementation.

## USER INTENT AND DISPATCHER DECISION
The operator was asked which remaining download batch to authorize and replied verbatim: "you decide."

The dispatcher now selects LTX-2.3 as the final planned video row. After accepted SCAIL-2 and Wan/2GP work, LTX-2.3 is the only remaining planned row. The old 29,531,884,062-byte Comfy FP8 checkpoint does not match WanGP packaging, so this story selects the native WanGP LTX-2.3 Distilled 1.0 GGUF Q4_K_M Light checkpoint.

The delivered bundle stores one terminal disposition for every LTX-2.3 cell and returns a fail-closed checker verdict rather than prose-only completion.

## Embedded Current State
At merged main 0f91e83c the video matrix has 35 host_run_verified cells, 51 unsupported cells, 4 dependency_blocked cells, and 9 planned cells. All nine planned cells are LTX-2.3. This story owns create, extend, blend, retake, edit, outpaint, repaint, recast, and upscale.

Host free space is 21,203,777,584 bytes. The selected download set is 35,379,235,525 bytes and needs storage preparation. A superseded, unused 34,038,903,007-byte MiniMax H3 full-int8 checkpoint is present at `/home/straughter/Wan2GP/ckpts/MiniMax-H3-FL2VA_int8_convrot.safetensors` with SHA-256 `83a36b67776962f44087f2f7c12d95791393f3cce1ef898efc90405216e7b0c0`. It will be byte-verified and moved to the Mac offload area, not deleted blindly. The active rank8 H3 checkpoint remains untouched.

## Storage Boundary
- Offload destination: `/Users/Shared/HermesWorkspace/model-offload/wangp-3090/MiniMax-H3-FL2VA_int8_convrot.safetensors`
- Destination has at least 100 GiB free.
- Record before/after hashes and sizes on both hosts.
- Remove the remote copy only after the local copy is byte-identical.
- Preserve every other model and checkpoint.

## Exact Authorized Downloads
| Asset | Destination | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| ltx-2.3-22b-distilled-Q4_K_M_light.gguf | /home/straughter/Wan2GP/ckpts/ltx-2.3-22b-distilled-Q4_K_M_light.gguf | 12971904032 | e324dbdacfc228e02e79e2f952c8274b16ba155d029db5f9abdd55a311325208 |
| gemma-3 int8 encoder | /home/straughter/Wan2GP/ckpts/gemma-3-12b-it-qat-q4_0-unquantized/gemma-3-12b-it-qat-q4_0-unquantized_quanto_bf16_int8.safetensors | 13210647730 | 1fad55b5df6c660c7982985c8ced76369114b1d31bbec93fbecc66a8bf30f36a |
| ltx-2.3 video VAE | /home/straughter/Wan2GP/ckpts/ltx-2.3-22b_vae.safetensors | 1452263226 | 646b77e252d08ec3a6e24fccb4bf53c80c7cf52025272f155f30fe2b84f0e1d4 |
| ltx-2.3 audio VAE | /home/straughter/Wan2GP/ckpts/ltx-2.3-22b_audio_vae.safetensors | 106538084 | c99a673c32ad0f7f6349df58466c0a1c2f398e314484a33988794322375cbde4 |
| ltx-2.3 vocoder | /home/straughter/Wan2GP/ckpts/ltx-2.3-22b_vocoder.safetensors | 258347744 | 3624e13fcf9fa8b2a1437bd9eb628c3a436282125e9e28ca1071142a4946e3f5 |
| ltx-2.3 text projection | /home/straughter/Wan2GP/ckpts/ltx-2.3-22b_text_embedding_projection.safetensors | 2312151888 | 985bba2295af346ac74b627afc8d27f4b5f277fb20c87968d569b4bb5d7fd28f |
| ltx-2.3 embeddings connector | /home/straughter/Wan2GP/ckpts/ltx-2.3-22b_embeddings_connector.safetensors | 4032404584 | eb37b1ec8024a311e863bcf5a684bdb6c64707216c3754c6f4078eae908d0600 |
| ltx-2.3 spatial upscaler | /home/straughter/Wan2GP/ckpts/ltx-2.3-spatial-upscaler-x2-1.1.safetensors | 995743560 | 5f416311fa8172b65af67530758964708d29a317b830d689a51143b7f91913ed |
| Gemma added_tokens.json | /home/straughter/Wan2GP/ckpts/gemma-3-12b-it-qat-q4_0-unquantized/added_tokens.json | 35 | 50b2f405ba56a26d4913fd772089992252d7f942123cc0a034d96424221ba946 |
| Gemma chat_template.json | /home/straughter/Wan2GP/ckpts/gemma-3-12b-it-qat-q4_0-unquantized/chat_template.json | 1615 | fe16baf728db49457cde32802cd7efc0ac8a7a9877dbe22fe3322b2d9dc6ccd9 |
| Gemma config_light.json | /home/straughter/Wan2GP/ckpts/gemma-3-12b-it-qat-q4_0-unquantized/config_light.json | 907 | c425c32bd6ea9ef8542ca0567fb903be7b728dc3b454d2511adecfc85978bb5c |
| Gemma generation_config.json | /home/straughter/Wan2GP/ckpts/gemma-3-12b-it-qat-q4_0-unquantized/generation_config.json | 173 | 13da6aad6852a008419f46df754b3452fc96387a4213c25811509d474e5a4776 |
| Gemma preprocessor_config.json | /home/straughter/Wan2GP/ckpts/gemma-3-12b-it-qat-q4_0-unquantized/preprocessor_config.json | 570 | f688d6bb20c5017601c4011de7ca656da8485b540b05013efdaf986c0fcc918d |
| Gemma processor_config.json | /home/straughter/Wan2GP/ckpts/gemma-3-12b-it-qat-q4_0-unquantized/processor_config.json | 70 | 3ffd5f11778dc73e2b69b3c00535e4121e1badf7018136263cd17b5b34fbaa53 |
| Gemma special_tokens_map.json | /home/straughter/Wan2GP/ckpts/gemma-3-12b-it-qat-q4_0-unquantized/special_tokens_map.json | 662 | 2f7b0adf4fb469770bb1490e3e35df87b1dc578246c5e7e6fc76ecf33213a397 |
| Gemma tokenizer.json | /home/straughter/Wan2GP/ckpts/gemma-3-12b-it-qat-q4_0-unquantized/tokenizer.json | 33384570 | 7d4046bf0505a327dd5a0abbb427ecd4fc82f99c2ceaa170bc61ecde12809b0c |
| Gemma tokenizer.model | /home/straughter/Wan2GP/ckpts/gemma-3-12b-it-qat-q4_0-unquantized/tokenizer.model | 4689074 | 1299c11d7cf632ef3b4e11937501358ada021bbdf7c47638d13c0ee982f2e79c |
| Gemma tokenizer_config.json | /home/straughter/Wan2GP/ckpts/gemma-3-12b-it-qat-q4_0-unquantized/tokenizer_config.json | 1157001 | 31e860fdfa360fa5aa58fe93252799facde5a52d1352f77d45978ab2a7e9eeb1 |

Total exact downloads: 35,379,235,525 bytes. The required temporal upscaler is already present under the LTX-2.5 filename with identical SHA-256 `2bc3300f2b3c3c1834d72164fbf13a3b9fd73e5a741e8a2c3f4035f89a75c3fe`; create a link only after hash verification, with zero download bytes.

## Boundary Map
PRODUCES:
- datasets/runs/maestro-parity/WD-VIDEO/ -> authorized storage offload, LTX-2.3 downloads, and nine-cell evidence
  spec: offload hashes/size, download report, shared-link proof, isolated source identity, native argv/logs, outputs/boundaries, media gates, checker result, reviewer decision, and matrix transition.
- docs/video-capabilities.md -> nine LTX-2.3 target-cell updates
  event: change only the nine owned planned cells.

CONSUMES:
- datasets/runs/maestro-parity/WD-ycjg/outputs/create/wd_ycjg_create.mp4 -> local person-bearing control/reference
  source: hash-copy only.
- datasets/runs/maestro-parity/WD-m7xw/evidence.json -> proven LTX tokenizer/offload execution patterns
  source: pattern only; no inherited evidence.
- scripts/verify_maestro_parity.py -> canonical evidence checker
  event: checker exit 0 is required for each host_run_verified disposition.

## Story Acceptance Criteria
1. [State] Start from current origin/main, create/push a clean story branch/worktree, record base identity, and atomically claim the story before storage or network mutation.
2. [State] Byte-verify and offload exactly the superseded full-int8 H3 checkpoint to the declared Mac path; remove the remote copy only after local size and SHA-256 match, and leave every other checkpoint untouched.
3. [State] Download only the eighteen declared files, verify every size/hash, create the temporal-upscaler link from the hash-identical existing file, and record all storage/network accounting.
4. [State] Give each of the nine target cells its own native attempt or exact typed boundary; evidence cannot be inherited across operations.
5. [State] Every successful output stores argv, native log, queue/exit state, SHA-256, ffprobe metadata, contact sheet/first frame, and an operation-appropriate objective gate.
6. [State] Every unsuccessful cell stores exact exit/failing stage, missing control or dependency, before/after GPU/source state, and an honest host-implementation or dependency boundary rather than a hardware verdict.
7. [Unwanted] No undeclared download, live dependency mutation, protected-engine semantic change, threshold change, training, provider spend, unrelated process action, or deletion of an unverified artifact occurs.
8. [State] docs/video-capabilities.md mechanically changes exactly the nine owned planned cells; a transition artifact proves zero LTX-2.3 planned cells and no unrelated matrix change.
9. [State] Delivery passes pvg lint, targeted video/evidence tests, canonical checker after independent review, release verification with release=ready and tag_created=false, protected-file parity, and git diff --check; it is delivered and independently accepted without self-approval.

## Testing Requirements
- Real no-mock storage transfer and host integration.
- Verify all copied/downloaded/linked files by exact SHA-256 and byte size.
- Probe all successful media and mechanically derive gates and matrix transitions.
- Run canonical checker, targeted tests, pvg lint, release verify, protected parity, and diff check.

## Delivery Requirements
Record authorization/decision, offload proof, download bytes, hashes, disk/GPU snapshots, command inventory, per-operation outputs/boundaries, matrix transition, gates, bundle size, pushed head, and PR. Stop on any undeclared network need, storage mismatch, or missing input.

## MANDATORY SKILLS
- pvg

## nd_contract
status: new

### evidence
- Authored from merged main 0f91e83c, live host storage inspection, Hugging Face metadata, WanGP native defaults, and the operator's "you decide" authorization.

### proof
- [ ] Pending atomic claim, verified offload, bounded download, and implementation.

## Acceptance Criteria


## Design


## Notes
## Implementation Evidence

Summary: WD-osfm terminalizes all nine LTX-2.3 cells with five real hashed outputs, one exact host boundary, three exact dependency boundaries, exact storage/network accounting, independent review, and all delivery gates except PM acceptance.

Commit SHA: `d34f0b65b04d8d15edad92f73d1621baf561e254`

Branch: `story/WD-osfm`

PR: https://github.com/jmanhype/wangp-dspy/pull/209

Commands run:

- `git fetch origin main && git worktree add .claude/worktrees/dev-WD-osfm -b story/WD-osfm origin/main && pvg story claim WD-osfm`
- `datasets/runs/maestro-parity/WD-osfm/host-scripts/05_validate_offload_and_free.sh`
- `datasets/runs/maestro-parity/WD-osfm/host-scripts/15_deploy_run_assets.sh`
- `ssh 3090 /tmp/10_download_preflight_osfm.sh`
- `ssh 3090 /home/straughter/wd-osfm-run/host-scripts/16_stage_local_gguf_dependency.sh`
- `ssh 3090 /home/straughter/wd-osfm-run/host-scripts/20_run_create.sh`
- `ssh 3090 /home/straughter/wd-osfm-run/host-scripts/21_run_probes_upscale.sh`
- `ssh 3090 /home/straughter/wd-osfm-run/host-scripts/22_promote_probe_outputs.sh`
- `ssh 3090 /home/straughter/wd-osfm-run/host-scripts/30_postflight.sh`
- `python3 datasets/runs/maestro-parity/WD-osfm/build_evidence.py`
- `uv run --frozen --extra dev python scripts/verify_maestro_parity.py datasets/runs/maestro-parity/WD-osfm`
- `uv run --frozen --extra dev pytest -q tests/test_video_capabilities.py tests/test_maestro_parity_evidence.py tests/test_no_maestro_verbatim.py --junitxml=datasets/runs/maestro-parity/WD-osfm/targeted-tests.xml`
- `pvg lint --backlog`
- `uv run --frozen --extra dev wgp release verify`
- `uv run --frozen --extra dev pytest -q --deselect tests/test_lf004_recovery_tooling.py::test_launcher_setup_is_root_relative_from_foreign_cwd --junitxml=/tmp/wd-osfm-fullsuite-clean.xml`
- `git diff --check`
- `git add docs/video-capabilities.md datasets/runs/maestro-parity/WD-osfm && git commit`
- `git push -u origin story/WD-osfm`
- `gh pr create --base main --head story/WD-osfm`

Implementation artifacts:

- Canonical evidence: `datasets/runs/maestro-parity/WD-osfm/evidence.json`
- Hash manifest: `datasets/runs/maestro-parity/WD-osfm/evidence.sha256`
- Matrix proof: `datasets/runs/maestro-parity/WD-osfm/matrix-transition-check.json`
- Boundary proof: `datasets/runs/maestro-parity/WD-osfm/boundary-evidence.json`
- Objective measurements: `datasets/runs/maestro-parity/WD-osfm/objective-measurements.json`
- Independent reviewer proof: `datasets/runs/maestro-parity/WD-osfm/reviewer-verdict.json`

## CI/Test Results

- Canonical evidence checker: PASS; 5 owned optional Wan2GP mutagen warnings; 0 unowned failures.
- Targeted video/evidence tests: PASS.
- Backlog lint: scanned 144 issues; 0 errors; 0 review findings.
- Clean-head selected full suite: 2,107 tests, 0 failures, 0 errors, 1 skip, 1234.975 seconds.
- Full-suite exclusion boundary: unrelated launcher test documented in `fullsuite-launcher-boundary.md`; not fixed in this one-finding PR.
- Clean-head release verification: version/changelog/recipe/tree PASS; `release=ready`; `tag_created=false`.
- Protected-file parity: 0 files changed.
- `git diff --check`: PASS.
- Bundle hash manifest: every listed file verifies.

## Acceptance Verification

| AC | Verdict | Proof |
| --- | --- | --- |
| 1. Clean branch/worktree/base and atomic claim | PASS | Base `0f91e83c`, story head `d34f0b65`, assignee `dev-WD-osfm` |
| 2. Exact verified H3 offload before unlink | PASS | `host-logs/00-offload-proof.txt`, `OFFLOAD_VERIFIED_AND_REMOTE_FREED=PASS` |
| 3. Exact 18-file download and zero-download link | PASS | `download-report.tsv`, `download-accounting.txt`, `95_final_download_accounting.txt` |
| 4. Operation-specific attempts/boundaries | PASS | native settings/logs and `boundary-evidence.json` |
| 5. Successful media evidence and gates | PASS | `evidence.json`, `objective-measurements.json`, ffprobe/contact sheets |
| 6. Exact unsuccessful boundaries | PASS | blend `reference_video_max_frames`; outpaint/recast/upscale exact absent assets |
| 7. No unwanted action | PASS | exact manifest, offline mode, protected parity, isolated source status `?? ckpts` |
| 8. Exact nine-cell matrix transition | PASS | `matrix-transition-check.json`: 9 changed, 0 planned, no unrelated rows |
| 9. Delivery gates and independent review | PASS pending PM acceptance | checker/tests/lint/release/parity/diff/reviewer all pass |

## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-27.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## nd_contract
status: delivered

### evidence
- Base merged main: `0f91e83c9afb61fc07825d2ede6c3f265445e0fb`.
- Delivered story head: `d34f0b65b04d8d15edad92f73d1621baf561e254`.
- Pull request: https://github.com/jmanhype/wangp-dspy/pull/209
- Bundle: `datasets/runs/maestro-parity/WD-osfm/evidence.json`.
- Bundle hash manifest: `datasets/runs/maestro-parity/WD-osfm/evidence.sha256`; every listed file verifies.
- Matrix transition: exactly 9 LTX-2.3 cells changed, 0 planned remain, no unrelated row changed.
- Terminal dispositions: create/extend/retake/edit/repaint `host_run_verified`; blend `unsupported`; outpaint/recast/upscale `dependency_blocked`.
- Real output SHA-256 values:
  - create `d489d46173a3fe54e21577353ed98c76cf351610eafa0f44e279e8241a932957`
  - extend `28889e82b96acf6b6b2f417e4ddb8a45b23c7c642d9d38608107932de73406c3`
  - retake `e39904befb76d409762492f8038f153af1b7a707acbc134f4c3038febf3e7769`
  - edit `8e10fafedca771f4d90b94bf6ae1fe47c64b35b517c7aa0cfa2e5f427f7bdb60`
  - repaint `ba9202ddf487c0ce5c139332725d19024f2aecd6b427aa39df365fb9290fd20f`
- Exact storage/network accounting: 18 downloads totaling `35379235525` bytes, one zero-download hash-identical temporal-upscaler link, and verified `34038903007`-byte H3 offload before remote unlink.
- Canonical checker: PASS with 5 owned optional Wan2GP mutagen warnings and zero unowned failures.
- Independent adversarial reviewer verdict: approved at `reviewer-verdict.json`, SHA-256 `00391d93bf504c5cfe24a5b7f48c08b1ce9867c0060eae9476dcdffa323fb017`.
- Targeted tests, backlog lint, protected-file parity, diff check, bundle hash manifest, and clean-head release verification pass.
- Clean-head full-suite boundary: 2,107/2,107 selected tests pass, 0 failures/errors, 1 skip; one unrelated pre-existing launcher deadlock is explicitly documented and excluded in `fullsuite-launcher-boundary.md`.

### proof
- [x] AC 1: clean story branch/worktree from current origin/main, base identity recorded, story atomically claimed before storage/network mutation.
- [x] AC 2: superseded H3 checkpoint byte-verified and offloaded before unlink; every other checkpoint preserved.
- [x] AC 3: exactly eighteen declared files downloaded and hash-verified; temporal upscaler linked from an existing hash-identical file with zero download bytes; storage/network accounting recorded.
- [x] AC 4: all nine cells have operation-specific native attempts or exact typed boundaries; no evidence inherited across operations.
- [x] AC 5: each successful output records argv/log/task status/hash/ffprobe/contact sheet/first frame and an operation-appropriate objective gate.
- [x] AC 6: each unsuccessful cell records exact failing field/dependency and is typed as host implementation or dependency boundary, not hardware infeasibility.
- [x] AC 7: no undeclared download, live dependency mutation, protected-engine change, threshold change, training, provider spend, unrelated process action, or unverified deletion occurred.
- [x] AC 8: matrix transition artifact proves exactly nine LTX-2.3 cells changed and zero remain planned.
- [x] AC 9: lint, targeted tests, canonical checker, release=ready/tag_created=false, protected parity, diff check, delivery proof, and independent review passed; PM acceptance remains outstanding.

## History
- 2026-09-27T16:21:09Z dep_added: blocks WD-fay0
- 2026-09-27T16:21:32Z status: open -> in_progress
- 2026-09-27T16:21:33Z auto-follows: linked to predecessor WD-28i5
- 2026-09-27T16:21:33Z claimed by dev-WD-osfm
- 2026-09-27T19:42:15Z status: in_progress -> in_progress
- 2026-09-27T19:42:15Z auto-follows: linked to predecessor WD-ycjg

## Links
- Parent: [[WD-3nod]]
- Blocks: [[WD-fay0]]
- Follows: [[WD-28i5]], [[WD-ycjg]]

## Comments
