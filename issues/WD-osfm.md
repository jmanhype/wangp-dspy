---
id: WD-osfm
title: "LTX-2.3 authorized download video batch"
status: open
priority: 1
type: task
labels: [capability, video, evidence, external-integration]
parent: WD-3nod
created_at: 2026-09-27T16:21:08Z
created_by: speed
updated_at: 2026-09-27T16:21:09Z
content_hash: "sha256:c6c440b9e8dafdb19c4da919b6a956179b76f94bb779cd4d960adac38c664951"
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


## History


## Links
- Parent: [[WD-3nod]]

## Comments
