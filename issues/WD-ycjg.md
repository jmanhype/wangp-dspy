---
id: WD-ycjg
title: "SCAIL-2 authorized download video batch"
status: in_progress
priority: 1
type: task
labels: [capability, video, evidence, external-integration]
parent: WD-3nod
created_at: 2026-09-27T13:24:01Z
created_by: speed
updated_at: 2026-09-27T14:43:23Z
content_hash: "sha256:e727372d55cd2c71145482e41d08adbaf196c901a20324e11fb544cae28b857f"
blocks: [WD-fay0]
follows: [WD-8h6p, WD-m25k, WD-obkn]
---

## Description
## USER INTENT AND DISPATCHER DECISION
The delivered bundle stores one terminal disposition for every owned SCAIL-2 cell and returns a fail-closed checker verdict rather than prose-only completion.

The operator was asked which remaining download batch to authorize first and replied verbatim: "you decide."

The dispatcher decides SCAIL-2. It is the lowest-risk next batch: its complete declared dependency set is 26,009,968,164 bytes, the host has 64,910,606,336 bytes free, the GPU is idle with 23,834 MiB free, and the batch leaves roughly 38.9 GB of disk headroom. LTX-2.3 and Wan/2GP remain later batches.

## Embedded Current State
At merged main 079651d9, the video matrix has 27 host_run_verified cells, 43 unsupported cells, 4 dependency_blocked cells, and 25 planned cells. The only planned rows are:

- LTX-2.3: 9 cells
- SCAIL-2: 7 cells
- Wan/2GP: 9 cells

This story owns exactly the seven SCAIL-2 planned cells: create, extend, blend, retake, edit, repaint, and recast. The existing typed backend boundaries for SCAIL outpaint and upscale remain unchanged.

## Exact Authorized Downloads
The operator's "you decide" authorizes this selected SCAIL-2 batch only. Planned download bytes are 28,418,905,124. Sixteen model/helper files go only into the existing Wan2GP checkpoint tree; the three Python dependencies go only into the story-local run directory. Every file must be hash-verified and recorded:

| Asset | Destination | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| scail2_14B_quanto_mbf16_int8.safetensors | /home/straughter/Wan2GP/ckpts/scail2_14B_quanto_mbf16_int8.safetensors | 16644305281 | 94e4c007370587157f4ca80637fee01aaab9c700192254a6c1379d9047a14460 |
| models_t5_umt5-xxl-enc-quanto_int8.safetensors | /home/straughter/Wan2GP/ckpts/umt5-xxl/models_t5_umt5-xxl-enc-quanto_int8.safetensors | 6733337738 | 5e4961851c78838931990549810ed51c9036081b2ad80bf464c4e2603c5f922c |
| Wan2.1_VAE.safetensors | /home/straughter/Wan2GP/ckpts/Wan2.1_VAE.safetensors | 507593157 | 3ce0c02b9470532e7f63f3e2f8e83b0681fdeaa432e969c412482d2b3b78267b |
| nlf_l_multi_0.3.2.eager.safetensors | /home/straughter/Wan2GP/ckpts/pose/nlf_l_multi_0.3.2.eager.safetensors | 355296592 | 07494758eb4b7832a099dee9b3a5040288fa869b9417dc71f8dfd519c85eebd7 |
| nlf_l_multi_0.3.2.eager.meta.json | /home/straughter/Wan2GP/ckpts/pose/nlf_l_multi_0.3.2.eager.meta.json | 27222 | 1704420d3b1767d3939a32aeaa34cc6d08188109fdfea4713181eaf9b55f3c1f |
| sam3.1_multiplex_bf16.safetensors | /home/straughter/Wan2GP/ckpts/sam3/sam3.1_multiplex_bf16.safetensors | 1746597176 | 4e2cd82698b64b7d32349c8bbb4f43422e199cd1bfc9ca6b88bbef562af7e99e |
| bpe_simple_vocab_16e6.txt.gz | /home/straughter/Wan2GP/ckpts/sam3/bpe_simple_vocab_16e6.txt.gz | 1356917 | 924691ac288e54409236115652ad4aa250f48203de50a9e4722a6ecd48d6804a |
| umt5 tokenizer.json | /home/straughter/Wan2GP/ckpts/umt5-xxl/tokenizer.json | 16837417 | 6e197b4d3dbd71da14b4eb255f4fa91c9c1f2068b20a2de2472967ca3d22602b |
| umt5 spiece.model | /home/straughter/Wan2GP/ckpts/umt5-xxl/spiece.model | 4548313 | e3909a67b780650b35cf529ac782ad2b6b26e6d1f849d3fbb6a872905f452458 |
| umt5 tokenizer_config.json | /home/straughter/Wan2GP/ckpts/umt5-xxl/tokenizer_config.json | 61728 | ed9a3a8b0faa71a70a32847e0435fe036e6e112d4df4edb7bb48a921e344dc05 |
| umt5 special_tokens_map.json | /home/straughter/Wan2GP/ckpts/umt5-xxl/special_tokens_map.json | 6623 | 7b8a9f5040adb67b5805abdfd42c1f8d0f3d0e711f10726580eb3789cd0ad61d |
| XLM-R CLIP vision/text model | /home/straughter/Wan2GP/ckpts/xlm-roberta-large/models_clip_open-clip-xlm-roberta-large-vit-huge-14-bf16.safetensors | 2386119506 | 742b68fe1cade9e54863aee12aed5390a994269957bd0638799b141cbc236ad8 |
| XLM-R sentencepiece.bpe.model | /home/straughter/Wan2GP/ckpts/xlm-roberta-large/sentencepiece.bpe.model | 5069051 | cfc8146abe2a0488e9e2a0c56de7952f7c11ab059eca145a0a727afce0db2865 |
| XLM-R special_tokens_map.json | /home/straughter/Wan2GP/ckpts/xlm-roberta-large/special_tokens_map.json | 280 | 06e405a36dfe4b9604f484f6a1e619af1a7f7d09e34a8555eb0b77b66318067f |
| XLM-R tokenizer.json | /home/straughter/Wan2GP/ckpts/xlm-roberta-large/tokenizer.json | 17082660 | 62c24cdc13d4c9952d63718d6c9fa4c287974249e16b7ade6d5a85e7bbb75626 |
| XLM-R tokenizer_config.json | /home/straughter/Wan2GP/ckpts/xlm-roberta-large/tokenizer_config.json | 418 | efb5c0d09722e5fe59a462cd2a9976ee216d55b037597d997cd3fe833216da15 |
| iopath-0.1.10.tar.gz | /home/straughter/wd-ycjg-run/python-deps/src/iopath-0.1.10.tar.gz | 42226 | 3311c16a4d9137223e20f141655759933e1eda24f8bff166af834af3c645ef01 |
| portalocker-4.4.0-py3-none-any.whl | /home/straughter/wd-ycjg-run/python-deps/src/portalocker-4.4.0-py3-none-any.whl | 129647 | a8e99ea29bfb61766ee0b4008cbaf0651e8e050f7a2485ebf54316480e99226e |
| pycocotools-2.0.11 cp311 x86_64 wheel | /home/straughter/wd-ycjg-run/python-deps/src/pycocotools-2.0.11-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl | 493172 | 18ba75ff58cedb33a85ce2c18f1452f1fe20c9dd59925eec5300b2bf6205dbe1 |

The control/reference video is already local and must not be downloaded:

- /home/straughter/Downloads/HOL120_ssscdn_scail_r9_00001.mp4
- SHA-256 c71398ba3c4fe6394c83450d7cd5267187e4c65b8d9b568f9457f1a9aac03ca8
- 384x224, 9 frames, 24 fps, 0.375 s, with embedded generation provenance.

## Boundary Map
PRODUCES:
- datasets/runs/maestro-parity/WD-ycjg/ -> authorized SCAIL-2 download record and seven-cell evidence
  spec: download manifest and hashes, source/control/reference provenance, isolated Wan2GP identity, native argv/logs, outputs or exact typed boundaries, media gates, checker result, reviewer decision, and matrix transition.
- docs/video-capabilities.md -> seven SCAIL-2 target-cell updates
  event: update only the seven owned planned cells; preserve existing outpaint and upscale typed boundaries.

CONSUMES:
- datasets/runs/maestro-parity/WD-2gyw/planning/models.json -> declared SCAIL model hash and destination
  source: verify the main checkpoint hash before queue admission.
- /home/straughter/Downloads/HOL120_ssscdn_scail_r9_00001.mp4 -> local person-bearing control/reference video
  source: hash-copy into the story namespace and never mutate the source.
- scripts/verify_maestro_parity.py -> canonical evidence checker
  event: checker exit 0 is required for any host_run_verified disposition.

## Story Acceptance Criteria
1. [State] Start from current origin/main, create/push a clean story branch/worktree, record base identity, and atomically claim the story before download or host mutation.
2. [State] Record verbatim authorization and the dispatcher's SCAIL-2 decision, then download only the nineteen declared files into their exact checkpoint or story-local destinations; reject any size/hash mismatch, leave no partial file admitted, and mutate no live Python environment.
3. [State] Rehash every downloaded asset and the local control video before and after execution; record actual network bytes, destination sizes, disk before/after, and isolated Wan2GP source identity.
4. [State] Prepare a SCAIL-compatible reference frame and colored mask from the local control using the downloaded SAM3 helper without downloading any additional asset; hash every derived input.
5. [State] Give each of create, extend, blend, retake, edit, repaint, and recast its own native attempt or exact typed boundary; evidence cannot be inherited across operations.
6. [State] Every successful output records argv, native log, queue/exit state, SHA-256, ffprobe metadata, contact sheet/first frame, and an operation-appropriate objective gate.
7. [State] Every unsuccessful cell records exact exit, failing stage, missing/incompatible control, before/after GPU/source state, and an honest dependency or host-implementation boundary rather than a hardware verdict.
8. [Unwanted] No undeclared download, dependency mutation, live-tree mutation, protected-engine semantic change, threshold change, training, provider spend, or unrelated process action occurs.
9. [State] docs/video-capabilities.md mechanically changes exactly the seven owned planned cells; a transition artifact proves zero SCAIL planned cells remain and no unrelated matrix cell changes.
10. [State] Delivery passes pvg lint, targeted video/evidence tests, canonical checker after independent review, release verification with release=ready and tag_created=false, protected-file parity, and git diff --check; the story is delivered and independently accepted without self-approval.

## Testing Requirements
- Real no-mock host integration where admitted.
- Verify all downloads by exact SHA-256 and byte size.
- Rehash source and derived references before and after.
- Probe all successful media and derive objective gates mechanically.
- Run canonical checker, targeted tests, pvg lint, release verify, protected parity, and diff check.
- Preserve complete native failure tails for boundaries.

## Delivery Requirements
Record authorization/decision, download table and actual bytes, hashes, disk/GPU snapshots, source/mask derivation, commands, per-operation outputs/boundaries, matrix transition, gates, bundle size, pushed head, and PR. Stop on any undeclared network need or missing input.

## MANDATORY SKILLS
- pvg

## nd_contract
status: new

### evidence
- Authored from merged main 079651d9, live host/disk/GPU inspection, Wan2GP SCAIL model definitions, Hugging Face metadata, and the operator's "you decide" authorization.

### proof
- [ ] Pending atomic claim, bounded download, and implementation.

## USER INTENT AND DISPATCHER DECISION
The delivered bundle stores one terminal disposition for every owned SCAIL-2 cell and returns a fail-closed checker verdict rather than prose-only completion.

The operator was asked which remaining download batch to authorize first and replied verbatim: "you decide."

The dispatcher decides SCAIL-2. It is the lowest-risk next batch: its complete declared dependency set is 26,009,968,164 bytes, the host has 64,910,606,336 bytes free, the GPU is idle with 23,834 MiB free, and the batch leaves roughly 38.9 GB of disk headroom. LTX-2.3 and Wan/2GP remain later batches.

## Embedded Current State
At merged main 079651d9, the video matrix has 27 host_run_verified cells, 43 unsupported cells, 4 dependency_blocked cells, and 25 planned cells. The only planned rows are:

- LTX-2.3: 9 cells
- SCAIL-2: 7 cells
- Wan/2GP: 9 cells

This story owns exactly the seven SCAIL-2 planned cells: create, extend, blend, retake, edit, repaint, and recast. The existing typed backend boundaries for SCAIL outpaint and upscale remain unchanged.

## Exact Authorized Downloads
The operator's "you decide" authorizes this selected SCAIL-2 batch only. Planned download bytes are 26,010,633,209. Model/helper files go only into the existing Wan2GP checkpoint tree; the two Python dependencies go only into the story-local run directory. Every file must be hash-verified and recorded:

| Asset | Destination | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| scail2_14B_quanto_mbf16_int8.safetensors | /home/straughter/Wan2GP/ckpts/scail2_14B_quanto_mbf16_int8.safetensors | 16644305281 | 94e4c007370587157f4ca80637fee01aaab9c700192254a6c1379d9047a14460 |
| models_t5_umt5-xxl-enc-quanto_int8.safetensors | /home/straughter/Wan2GP/ckpts/umt5-xxl/models_t5_umt5-xxl-enc-quanto_int8.safetensors | 6733337738 | 5e4961851c78838931990549810ed51c9036081b2ad80bf464c4e2603c5f922c |
| Wan2.1_VAE.safetensors | /home/straughter/Wan2GP/ckpts/Wan2.1_VAE.safetensors | 507593157 | 3ce0c02b9470532e7f63f3e2f8e83b0681fdeaa432e969c412482d2b3b78267b |
| nlf_l_multi_0.3.2.eager.safetensors | /home/straughter/Wan2GP/ckpts/pose/nlf_l_multi_0.3.2.eager.safetensors | 355296592 | 07494758eb4b7832a099dee9b3a5040288fa869b9417dc71f8dfd519c85eebd7 |
| nlf_l_multi_0.3.2.eager.meta.json | /home/straughter/Wan2GP/ckpts/pose/nlf_l_multi_0.3.2.eager.meta.json | 27222 | 1704420d3b1767d3939a32aeaa34cc6d08188109fdfea4713181eaf9b55f3c1f |
| sam3.1_multiplex_bf16.safetensors | /home/straughter/Wan2GP/ckpts/sam3/sam3.1_multiplex_bf16.safetensors | 1746597176 | 4e2cd82698b64b7d32349c8bbb4f43422e199cd1bfc9ca6b88bbef562af7e99e |
| bpe_simple_vocab_16e6.txt.gz | /home/straughter/Wan2GP/ckpts/sam3/bpe_simple_vocab_16e6.txt.gz | 1356917 | 924691ac288e54409236115652ad4aa250f48203de50a9e4722a6ecd48d6804a |
| umt5 tokenizer.json | /home/straughter/Wan2GP/ckpts/umt5-xxl/tokenizer.json | 16837417 | 6e197b4d3dbd71da14b4eb255f4fa91c9c1f2068b20a2de2472967ca3d22602b |
| umt5 spiece.model | /home/straughter/Wan2GP/ckpts/umt5-xxl/spiece.model | 4548313 | e3909a67b780650b35cf529ac782ad2b6b26e6d1f849d3fbb6a872905f452458 |
| umt5 tokenizer_config.json | /home/straughter/Wan2GP/ckpts/umt5-xxl/tokenizer_config.json | 61728 | ed9a3a8b0faa71a70a32847e0435fe036e6e112d4df4edb7bb48a921e344dc05 |
| umt5 special_tokens_map.json | /home/straughter/Wan2GP/ckpts/umt5-xxl/special_tokens_map.json | 6623 | 7b8a9f5040adb67b5805abdfd42c1f8d0f3d0e711f10726580eb3789cd0ad61d |
| iopath-0.1.10.tar.gz | /home/straughter/wd-ycjg-run/python-deps/src/iopath-0.1.10.tar.gz | 42226 | 3311c16a4d9137223e20f141655759933e1eda24f8bff166af834af3c645ef01 |
| portalocker-4.4.0-py3-none-any.whl | /home/straughter/wd-ycjg-run/python-deps/src/portalocker-4.4.0-py3-none-any.whl | 129647 | a8e99ea29bfb61766ee0b4008cbaf0651e8e050f7a2485ebf54316480e99226e |
| pycocotools-2.0.11 cp311 x86_64 wheel | /home/straughter/wd-ycjg-run/python-deps/src/pycocotools-2.0.11-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl | 493172 | 18ba75ff58cedb33a85ce2c18f1452f1fe20c9dd59925eec5300b2bf6205dbe1 |

The control/reference video is already local and must not be downloaded:

- /home/straughter/Downloads/HOL120_ssscdn_scail_r9_00001.mp4
- SHA-256 c71398ba3c4fe6394c83450d7cd5267187e4c65b8d9b568f9457f1a9aac03ca8
- 384x224, 9 frames, 24 fps, 0.375 s, with embedded generation provenance.

## Boundary Map
PRODUCES:
- datasets/runs/maestro-parity/WD-ycjg/ -> authorized SCAIL-2 download record and seven-cell evidence
  spec: download manifest and hashes, source/control/reference provenance, isolated Wan2GP identity, native argv/logs, outputs or exact typed boundaries, media gates, checker result, reviewer decision, and matrix transition.
- docs/video-capabilities.md -> seven SCAIL-2 target-cell updates
  event: update only the seven owned planned cells; preserve existing outpaint and upscale typed boundaries.

CONSUMES:
- datasets/runs/maestro-parity/WD-2gyw/planning/models.json -> declared SCAIL model hash and destination
  source: verify the main checkpoint hash before queue admission.
- /home/straughter/Downloads/HOL120_ssscdn_scail_r9_00001.mp4 -> local person-bearing control/reference video
  source: hash-copy into the story namespace and never mutate the source.
- scripts/verify_maestro_parity.py -> canonical evidence checker
  event: checker exit 0 is required for any host_run_verified disposition.

## Story Acceptance Criteria
1. [State] Start from current origin/main, create/push a clean story branch/worktree, record base identity, and atomically claim the story before download or host mutation.
2. [State] Record verbatim authorization and the dispatcher's SCAIL-2 decision, then download only the fourteen declared files into their exact checkpoint or story-local destinations; reject any size/hash mismatch, leave no partial file admitted, and mutate no live Python environment.
3. [State] Rehash every downloaded asset and the local control video before and after execution; record actual network bytes, destination sizes, disk before/after, and isolated Wan2GP source identity.
4. [State] Prepare a SCAIL-compatible reference frame and colored mask from the local control using the downloaded SAM3 helper without downloading any additional asset; hash every derived input.
5. [State] Give each of create, extend, blend, retake, edit, repaint, and recast its own native attempt or exact typed boundary; evidence cannot be inherited across operations.
6. [State] Every successful output records argv, native log, queue/exit state, SHA-256, ffprobe metadata, contact sheet/first frame, and an operation-appropriate objective gate.
7. [State] Every unsuccessful cell records exact exit, failing stage, missing/incompatible control, before/after GPU/source state, and an honest dependency or host-implementation boundary rather than a hardware verdict.
8. [Unwanted] No undeclared download, dependency mutation, live-tree mutation, protected-engine semantic change, threshold change, training, provider spend, or unrelated process action occurs.
9. [State] docs/video-capabilities.md mechanically changes exactly the seven owned planned cells; a transition artifact proves zero SCAIL planned cells remain and no unrelated matrix cell changes.
10. [State] Delivery passes pvg lint, targeted video/evidence tests, canonical checker after independent review, release verification with release=ready and tag_created=false, protected-file parity, and git diff --check; the story is delivered and independently accepted without self-approval.

## Testing Requirements
- Real no-mock host integration where admitted.
- Verify all downloads by exact SHA-256 and byte size.
- Rehash source and derived references before and after.
- Probe all successful media and derive objective gates mechanically.
- Run canonical checker, targeted tests, pvg lint, release verify, protected parity, and diff check.
- Preserve complete native failure tails for boundaries.

## Delivery Requirements
Record authorization/decision, download table and actual bytes, hashes, disk/GPU snapshots, source/mask derivation, commands, per-operation outputs/boundaries, matrix transition, gates, bundle size, pushed head, and PR. Stop on any undeclared network need or missing input.

## MANDATORY SKILLS
- pvg

## nd_contract
status: new

### evidence
- Authored from merged main 079651d9, live host/disk/GPU inspection, Wan2GP SCAIL model definitions, Hugging Face metadata, and the operator's "you decide" authorization.

### proof
- [ ] Pending atomic claim, bounded download, and implementation.

## USER INTENT AND DISPATCHER DECISION
The delivered bundle stores one terminal disposition for every owned SCAIL-2 cell and returns a fail-closed checker verdict rather than prose-only completion.

The operator was asked which remaining download batch to authorize first and replied verbatim: "you decide."

The dispatcher decides SCAIL-2. It is the lowest-risk next batch: its complete declared dependency set is 26,009,968,164 bytes, the host has 64,910,606,336 bytes free, the GPU is idle with 23,834 MiB free, and the batch leaves roughly 38.9 GB of disk headroom. LTX-2.3 and Wan/2GP remain later batches.

## Embedded Current State
At merged main 079651d9, the video matrix has 27 host_run_verified cells, 43 unsupported cells, 4 dependency_blocked cells, and 25 planned cells. The only planned rows are:

- LTX-2.3: 9 cells
- SCAIL-2: 7 cells
- Wan/2GP: 9 cells

This story owns exactly the seven SCAIL-2 planned cells: create, extend, blend, retake, edit, repaint, and recast. The existing typed backend boundaries for SCAIL outpaint and upscale remain unchanged.

## Exact Authorized Downloads
The operator's "you decide" authorizes this selected SCAIL-2 batch only. Planned download bytes are 26,010,140,037. Model/helper files go only into the existing Wan2GP checkpoint tree; the two Python dependencies go only into the story-local run directory. Every file must be hash-verified and recorded:

| Asset | Destination | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| scail2_14B_quanto_mbf16_int8.safetensors | /home/straughter/Wan2GP/ckpts/scail2_14B_quanto_mbf16_int8.safetensors | 16644305281 | 94e4c007370587157f4ca80637fee01aaab9c700192254a6c1379d9047a14460 |
| models_t5_umt5-xxl-enc-quanto_int8.safetensors | /home/straughter/Wan2GP/ckpts/umt5-xxl/models_t5_umt5-xxl-enc-quanto_int8.safetensors | 6733337738 | 5e4961851c78838931990549810ed51c9036081b2ad80bf464c4e2603c5f922c |
| Wan2.1_VAE.safetensors | /home/straughter/Wan2GP/ckpts/Wan2.1_VAE.safetensors | 507593157 | 3ce0c02b9470532e7f63f3e2f8e83b0681fdeaa432e969c412482d2b3b78267b |
| nlf_l_multi_0.3.2.eager.safetensors | /home/straughter/Wan2GP/ckpts/pose/nlf_l_multi_0.3.2.eager.safetensors | 355296592 | 07494758eb4b7832a099dee9b3a5040288fa869b9417dc71f8dfd519c85eebd7 |
| nlf_l_multi_0.3.2.eager.meta.json | /home/straughter/Wan2GP/ckpts/pose/nlf_l_multi_0.3.2.eager.meta.json | 27222 | 1704420d3b1767d3939a32aeaa34cc6d08188109fdfea4713181eaf9b55f3c1f |
| sam3.1_multiplex_bf16.safetensors | /home/straughter/Wan2GP/ckpts/sam3/sam3.1_multiplex_bf16.safetensors | 1746597176 | 4e2cd82698b64b7d32349c8bbb4f43422e199cd1bfc9ca6b88bbef562af7e99e |
| bpe_simple_vocab_16e6.txt.gz | /home/straughter/Wan2GP/ckpts/sam3/bpe_simple_vocab_16e6.txt.gz | 1356917 | 924691ac288e54409236115652ad4aa250f48203de50a9e4722a6ecd48d6804a |
| umt5 tokenizer.json | /home/straughter/Wan2GP/ckpts/umt5-xxl/tokenizer.json | 16837417 | 6e197b4d3dbd71da14b4eb255f4fa91c9c1f2068b20a2de2472967ca3d22602b |
| umt5 spiece.model | /home/straughter/Wan2GP/ckpts/umt5-xxl/spiece.model | 4548313 | e3909a67b780650b35cf529ac782ad2b6b26e6d1f849d3fbb6a872905f452458 |
| umt5 tokenizer_config.json | /home/straughter/Wan2GP/ckpts/umt5-xxl/tokenizer_config.json | 61728 | ed9a3a8b0faa71a70a32847e0435fe036e6e112d4df4edb7bb48a921e344dc05 |
| umt5 special_tokens_map.json | /home/straughter/Wan2GP/ckpts/umt5-xxl/special_tokens_map.json | 6623 | 7b8a9f5040adb67b5805abdfd42c1f8d0f3d0e711f10726580eb3789cd0ad61d |
| iopath-0.1.10.tar.gz | /home/straughter/wd-ycjg-run/python-deps/src/iopath-0.1.10.tar.gz | 42226 | 3311c16a4d9137223e20f141655759933e1eda24f8bff166af834af3c645ef01 |
| portalocker-4.4.0-py3-none-any.whl | /home/straughter/wd-ycjg-run/python-deps/src/portalocker-4.4.0-py3-none-any.whl | 129647 | a8e99ea29bfb61766ee0b4008cbaf0651e8e050f7a2485ebf54316480e99226e |

The control/reference video is already local and must not be downloaded:

- /home/straughter/Downloads/HOL120_ssscdn_scail_r9_00001.mp4
- SHA-256 c71398ba3c4fe6394c83450d7cd5267187e4c65b8d9b568f9457f1a9aac03ca8
- 384x224, 9 frames, 24 fps, 0.375 s, with embedded generation provenance.

## Boundary Map
PRODUCES:
- datasets/runs/maestro-parity/WD-ycjg/ -> authorized SCAIL-2 download record and seven-cell evidence
  spec: download manifest and hashes, source/control/reference provenance, isolated Wan2GP identity, native argv/logs, outputs or exact typed boundaries, media gates, checker result, reviewer decision, and matrix transition.
- docs/video-capabilities.md -> seven SCAIL-2 target-cell updates
  event: update only the seven owned planned cells; preserve existing outpaint and upscale typed boundaries.

CONSUMES:
- datasets/runs/maestro-parity/WD-2gyw/planning/models.json -> declared SCAIL model hash and destination
  source: verify the main checkpoint hash before queue admission.
- /home/straughter/Downloads/HOL120_ssscdn_scail_r9_00001.mp4 -> local person-bearing control/reference video
  source: hash-copy into the story namespace and never mutate the source.
- scripts/verify_maestro_parity.py -> canonical evidence checker
  event: checker exit 0 is required for any host_run_verified disposition.

## Story Acceptance Criteria
1. [State] Start from current origin/main, create/push a clean story branch/worktree, record base identity, and atomically claim the story before download or host mutation.
2. [State] Record verbatim authorization and the dispatcher's SCAIL-2 decision, then download only the thirteen declared files into their exact checkpoint or story-local destinations; reject any size/hash mismatch, leave no partial file admitted, and mutate no live Python environment.
3. [State] Rehash every downloaded asset and the local control video before and after execution; record actual network bytes, destination sizes, disk before/after, and isolated Wan2GP source identity.
4. [State] Prepare a SCAIL-compatible reference frame and colored mask from the local control using the downloaded SAM3 helper without downloading any additional asset; hash every derived input.
5. [State] Give each of create, extend, blend, retake, edit, repaint, and recast its own native attempt or exact typed boundary; evidence cannot be inherited across operations.
6. [State] Every successful output records argv, native log, queue/exit state, SHA-256, ffprobe metadata, contact sheet/first frame, and an operation-appropriate objective gate.
7. [State] Every unsuccessful cell records exact exit, failing stage, missing/incompatible control, before/after GPU/source state, and an honest dependency or host-implementation boundary rather than a hardware verdict.
8. [Unwanted] No undeclared download, dependency mutation, live-tree mutation, protected-engine semantic change, threshold change, training, provider spend, or unrelated process action occurs.
9. [State] docs/video-capabilities.md mechanically changes exactly the seven owned planned cells; a transition artifact proves zero SCAIL planned cells remain and no unrelated matrix cell changes.
10. [State] Delivery passes pvg lint, targeted video/evidence tests, canonical checker after independent review, release verification with release=ready and tag_created=false, protected-file parity, and git diff --check; the story is delivered and independently accepted without self-approval.

## Testing Requirements
- Real no-mock host integration where admitted.
- Verify all downloads by exact SHA-256 and byte size.
- Rehash source and derived references before and after.
- Probe all successful media and derive objective gates mechanically.
- Run canonical checker, targeted tests, pvg lint, release verify, protected parity, and diff check.
- Preserve complete native failure tails for boundaries.

## Delivery Requirements
Record authorization/decision, download table and actual bytes, hashes, disk/GPU snapshots, source/mask derivation, commands, per-operation outputs/boundaries, matrix transition, gates, bundle size, pushed head, and PR. Stop on any undeclared network need or missing input.

## MANDATORY SKILLS
- pvg

## nd_contract
status: new

### evidence
- Authored from merged main 079651d9, live host/disk/GPU inspection, Wan2GP SCAIL model definitions, Hugging Face metadata, and the operator's "you decide" authorization.

### proof
- [ ] Pending atomic claim, bounded download, and implementation.

## USER INTENT AND DISPATCHER DECISION
The delivered bundle stores one terminal disposition for every owned SCAIL-2 cell and returns a fail-closed checker verdict rather than prose-only completion.

The operator was asked which remaining download batch to authorize first and replied verbatim: "you decide."

The dispatcher decides SCAIL-2. It is the lowest-risk next batch: its complete declared dependency set is 26,009,968,164 bytes, the host has 64,910,606,336 bytes free, the GPU is idle with 23,834 MiB free, and the batch leaves roughly 38.9 GB of disk headroom. LTX-2.3 and Wan/2GP remain later batches.

## Embedded Current State
At merged main 079651d9, the video matrix has 27 host_run_verified cells, 43 unsupported cells, 4 dependency_blocked cells, and 25 planned cells. The only planned rows are:

- LTX-2.3: 9 cells
- SCAIL-2: 7 cells
- Wan/2GP: 9 cells

This story owns exactly the seven SCAIL-2 planned cells: create, extend, blend, retake, edit, repaint, and recast. The existing typed backend boundaries for SCAIL outpaint and upscale remain unchanged.

## Exact Authorized Downloads
The operator's "you decide" authorizes this selected SCAIL-2 batch only. Planned download bytes are 26,009,968,164. Every file must be downloaded only into the existing Wan2GP checkpoint tree, hash-verified, and recorded:

| Asset | Destination | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| scail2_14B_quanto_mbf16_int8.safetensors | /home/straughter/Wan2GP/ckpts/scail2_14B_quanto_mbf16_int8.safetensors | 16644305281 | 94e4c007370587157f4ca80637fee01aaab9c700192254a6c1379d9047a14460 |
| models_t5_umt5-xxl-enc-quanto_int8.safetensors | /home/straughter/Wan2GP/ckpts/umt5-xxl/models_t5_umt5-xxl-enc-quanto_int8.safetensors | 6733337738 | 5e4961851c78838931990549810ed51c9036081b2ad80bf464c4e2603c5f922c |
| Wan2.1_VAE.safetensors | /home/straughter/Wan2GP/ckpts/Wan2.1_VAE.safetensors | 507593157 | 3ce0c02b9470532e7f63f3e2f8e83b0681fdeaa432e969c412482d2b3b78267b |
| nlf_l_multi_0.3.2.eager.safetensors | /home/straughter/Wan2GP/ckpts/pose/nlf_l_multi_0.3.2.eager.safetensors | 355296592 | 07494758eb4b7832a099dee9b3a5040288fa869b9417dc71f8dfd519c85eebd7 |
| nlf_l_multi_0.3.2.eager.meta.json | /home/straughter/Wan2GP/ckpts/pose/nlf_l_multi_0.3.2.eager.meta.json | 27222 | 1704420d3b1767d3939a32aeaa34cc6d08188109fdfea4713181eaf9b55f3c1f |
| sam3.1_multiplex_bf16.safetensors | /home/straughter/Wan2GP/ckpts/sam3/sam3.1_multiplex_bf16.safetensors | 1746597176 | 4e2cd82698b64b7d32349c8bbb4f43422e199cd1bfc9ca6b88bbef562af7e99e |
| bpe_simple_vocab_16e6.txt.gz | /home/straughter/Wan2GP/ckpts/sam3/bpe_simple_vocab_16e6.txt.gz | 1356917 | 924691ac288e54409236115652ad4aa250f48203de50a9e4722a6ecd48d6804a |
| umt5 tokenizer.json | /home/straughter/Wan2GP/ckpts/umt5-xxl/tokenizer.json | 16837417 | 6e197b4d3dbd71da14b4eb255f4fa91c9c1f2068b20a2de2472967ca3d22602b |
| umt5 spiece.model | /home/straughter/Wan2GP/ckpts/umt5-xxl/spiece.model | 4548313 | e3909a67b780650b35cf529ac782ad2b6b26e6d1f849d3fbb6a872905f452458 |
| umt5 tokenizer_config.json | /home/straughter/Wan2GP/ckpts/umt5-xxl/tokenizer_config.json | 61728 | ed9a3a8b0faa71a70a32847e0435fe036e6e112d4df4edb7bb48a921e344dc05 |
| umt5 special_tokens_map.json | /home/straughter/Wan2GP/ckpts/umt5-xxl/special_tokens_map.json | 6623 | 7b8a9f5040adb67b5805abdfd42c1f8d0f3d0e711f10726580eb3789cd0ad61d |

The control/reference video is already local and must not be downloaded:

- /home/straughter/Downloads/HOL120_ssscdn_scail_r9_00001.mp4
- SHA-256 c71398ba3c4fe6394c83450d7cd5267187e4c65b8d9b568f9457f1a9aac03ca8
- 384x224, 9 frames, 24 fps, 0.375 s, with embedded generation provenance.

## Boundary Map
PRODUCES:
- datasets/runs/maestro-parity/WD-ycjg/ -> authorized SCAIL-2 download record and seven-cell evidence
  spec: download manifest and hashes, source/control/reference provenance, isolated Wan2GP identity, native argv/logs, outputs or exact typed boundaries, media gates, checker result, reviewer decision, and matrix transition.
- docs/video-capabilities.md -> seven SCAIL-2 target-cell updates
  event: update only the seven owned planned cells; preserve existing outpaint and upscale typed boundaries.

CONSUMES:
- datasets/runs/maestro-parity/WD-2gyw/planning/models.json -> declared SCAIL model hash and destination
  source: verify the main checkpoint hash before queue admission.
- /home/straughter/Downloads/HOL120_ssscdn_scail_r9_00001.mp4 -> local person-bearing control/reference video
  source: hash-copy into the story namespace and never mutate the source.
- scripts/verify_maestro_parity.py -> canonical evidence checker
  event: checker exit 0 is required for any host_run_verified disposition.

## Story Acceptance Criteria
1. [State] Start from current origin/main, create/push a clean story branch/worktree, record base identity, and atomically claim the story before download or host mutation.
2. [State] Record verbatim authorization and the dispatcher's SCAIL-2 decision, then download only the eleven declared files into their exact destinations; reject any size/hash mismatch and leave no partial file admitted.
3. [State] Rehash every downloaded asset and the local control video before and after execution; record actual network bytes, destination sizes, disk before/after, and isolated Wan2GP source identity.
4. [State] Prepare a SCAIL-compatible reference frame and colored mask from the local control using the downloaded SAM3 helper without downloading any additional asset; hash every derived input.
5. [State] Give each of create, extend, blend, retake, edit, repaint, and recast its own native attempt or exact typed boundary; evidence cannot be inherited across operations.
6. [State] Every successful output records argv, native log, queue/exit state, SHA-256, ffprobe metadata, contact sheet/first frame, and an operation-appropriate objective gate.
7. [State] Every unsuccessful cell records exact exit, failing stage, missing/incompatible control, before/after GPU/source state, and an honest dependency or host-implementation boundary rather than a hardware verdict.
8. [Unwanted] No undeclared download, dependency mutation, live-tree mutation, protected-engine semantic change, threshold change, training, provider spend, or unrelated process action occurs.
9. [State] docs/video-capabilities.md mechanically changes exactly the seven owned planned cells; a transition artifact proves zero SCAIL planned cells remain and no unrelated matrix cell changes.
10. [State] Delivery passes pvg lint, targeted video/evidence tests, canonical checker after independent review, release verification with release=ready and tag_created=false, protected-file parity, and git diff --check; the story is delivered and independently accepted without self-approval.

## Testing Requirements
- Real no-mock host integration where admitted.
- Verify all downloads by exact SHA-256 and byte size.
- Rehash source and derived references before and after.
- Probe all successful media and derive objective gates mechanically.
- Run canonical checker, targeted tests, pvg lint, release verify, protected parity, and diff check.
- Preserve complete native failure tails for boundaries.

## Delivery Requirements
Record authorization/decision, download table and actual bytes, hashes, disk/GPU snapshots, source/mask derivation, commands, per-operation outputs/boundaries, matrix transition, gates, bundle size, pushed head, and PR. Stop on any undeclared network need or missing input.

## MANDATORY SKILLS
- pvg

## nd_contract
status: new

### evidence
- Authored from merged main 079651d9, live host/disk/GPU inspection, Wan2GP SCAIL model definitions, Hugging Face metadata, and the operator's "you decide" authorization.

### proof
- [ ] Pending atomic claim, bounded download, and implementation.

## USER INTENT AND DISPATCHER DECISION
The delivered bundle stores one terminal disposition for every owned SCAIL-2 cell and returns a fail-closed checker verdict rather than prose-only completion.

The operator was asked which remaining download batch to authorize first and replied verbatim: "you decide."

The dispatcher decides SCAIL-2. It is the lowest-risk next batch: its complete declared dependency set is 26,009,968,164 bytes, the host has 64,910,606,336 bytes free, the GPU is idle with 23,834 MiB free, and the batch leaves roughly 38.9 GB of disk headroom. LTX-2.3 and Wan/2GP remain later batches.

## Embedded Current State
At merged main 079651d9, the video matrix has 27 host_run_verified cells, 43 unsupported cells, 4 dependency_blocked cells, and 25 planned cells. The only planned rows are:

- LTX-2.3: 9 cells
- SCAIL-2: 7 cells
- Wan/2GP: 9 cells

This story owns exactly the seven SCAIL-2 planned cells: create, extend, blend, retake, edit, repaint, and recast. The existing typed backend boundaries for SCAIL outpaint and upscale remain unchanged.

## Exact Authorized Downloads
The operator's "you decide" authorizes this selected SCAIL-2 batch only. Planned download bytes are 26,009,968,164. Every file must be downloaded only into the existing Wan2GP checkpoint tree, hash-verified, and recorded:

| Asset | Destination | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| scail2_14B_quanto_mbf16_int8.safetensors | /home/straughter/Wan2GP/ckpts/scail2_14B_quanto_mbf16_int8.safetensors | 16644305281 | 94e4c007370587157f4ca80637fee01aaab9c700192254a6c1379d9047a14460 |
| models_t5_umt5-xxl-enc-quanto_int8.safetensors | /home/straughter/Wan2GP/ckpts/umt5-xxl/models_t5_umt5-xxl-enc-quanto_int8.safetensors | 6733337738 | 5e4961851c78838931990549810ed51c9036081b2ad80bf464c4e2603c5f922c |
| Wan2.1_VAE.safetensors | /home/straughter/Wan2GP/ckpts/Wan2.1_VAE.safetensors | 507593157 | 3ce0c02b9470532e7f63f3e2f8e83b0681fdeaa432e969c412482d2b3b78267b |
| nlf_l_multi_0.3.2.eager.safetensors | /home/straughter/Wan2GP/ckpts/pose/nlf_l_multi_0.3.2.eager.safetensors | 355296592 | 07494758eb4b7832a099dee9b3a5040288fa869b9417dc71f8dfd519c85eebd7 |
| nlf_l_multi_0.3.2.eager.meta.json | /home/straughter/Wan2GP/ckpts/pose/nlf_l_multi_0.3.2.eager.meta.json | 27222 | 2fce0ccda5422016c305023fd2f6c5abc7ea8e4f |
| sam3.1_multiplex_bf16.safetensors | /home/straughter/Wan2GP/ckpts/sam3/sam3.1_multiplex_bf16.safetensors | 1746597176 | 4e2cd82698b64b7d32349c8bbb4f43422e199cd1bfc9ca6b88bbef562af7e99e |
| bpe_simple_vocab_16e6.txt.gz | /home/straughter/Wan2GP/ckpts/sam3/bpe_simple_vocab_16e6.txt.gz | 1356917 | 924691ac288e54409236115652ad4aa250f48203de50a9e4722a6ecd48d6804a |
| umt5 tokenizer.json | /home/straughter/Wan2GP/ckpts/umt5-xxl/tokenizer.json | 16837417 | 6e197b4d3dbd71da14b4eb255f4fa91c9c1f2068b20a2de2472967ca3d22602b |
| umt5 spiece.model | /home/straughter/Wan2GP/ckpts/umt5-xxl/spiece.model | 4548313 | e3909a67b780650b35cf529ac782ad2b6b26e6d1f849d3fbb6a872905f452458 |
| umt5 tokenizer_config.json | /home/straughter/Wan2GP/ckpts/umt5-xxl/tokenizer_config.json | 61728 | 4e1cc1cd85599ce0b47fd0a746af188fe4043ff2a |
| umt5 special_tokens_map.json | /home/straughter/Wan2GP/ckpts/umt5-xxl/special_tokens_map.json | 6623 | 14855e7052ffbb595057dfd791d293c1c940db2c |

The control/reference video is already local and must not be downloaded:

- /home/straughter/Downloads/HOL120_ssscdn_scail_r9_00001.mp4
- SHA-256 c71398ba3c4fe6394c83450d7cd5267187e4c65b8d9b568f9457f1a9aac03ca8
- 384x224, 9 frames, 24 fps, 0.375 s, with embedded generation provenance.

## Boundary Map
PRODUCES:
- datasets/runs/maestro-parity/WD-ycjg/ -> authorized SCAIL-2 download record and seven-cell evidence
  spec: download manifest and hashes, source/control/reference provenance, isolated Wan2GP identity, native argv/logs, outputs or exact typed boundaries, media gates, checker result, reviewer decision, and matrix transition.
- docs/video-capabilities.md -> seven SCAIL-2 target-cell updates
  event: update only the seven owned planned cells; preserve existing outpaint and upscale typed boundaries.

CONSUMES:
- datasets/runs/maestro-parity/WD-2gyw/planning/models.json -> declared SCAIL model hash and destination
  source: verify the main checkpoint hash before queue admission.
- /home/straughter/Downloads/HOL120_ssscdn_scail_r9_00001.mp4 -> local person-bearing control/reference video
  source: hash-copy into the story namespace and never mutate the source.
- scripts/verify_maestro_parity.py -> canonical evidence checker
  event: checker exit 0 is required for any host_run_verified disposition.

## Story Acceptance Criteria
1. [State] Start from current origin/main, create/push a clean story branch/worktree, record base identity, and atomically claim the story before download or host mutation.
2. [State] Record verbatim authorization and the dispatcher's SCAIL-2 decision, then download only the eleven declared files into their exact destinations; reject any size/hash mismatch and leave no partial file admitted.
3. [State] Rehash every downloaded asset and the local control video before and after execution; record actual network bytes, destination sizes, disk before/after, and isolated Wan2GP source identity.
4. [State] Prepare a SCAIL-compatible reference frame and colored mask from the local control using the downloaded SAM3 helper without downloading any additional asset; hash every derived input.
5. [State] Give each of create, extend, blend, retake, edit, repaint, and recast its own native attempt or exact typed boundary; evidence cannot be inherited across operations.
6. [State] Every successful output records argv, native log, queue/exit state, SHA-256, ffprobe metadata, contact sheet/first frame, and an operation-appropriate objective gate.
7. [State] Every unsuccessful cell records exact exit, failing stage, missing/incompatible control, before/after GPU/source state, and an honest dependency or host-implementation boundary rather than a hardware verdict.
8. [Unwanted] No undeclared download, dependency mutation, live-tree mutation, protected-engine semantic change, threshold change, training, provider spend, or unrelated process action occurs.
9. [State] docs/video-capabilities.md mechanically changes exactly the seven owned planned cells; a transition artifact proves zero SCAIL planned cells remain and no unrelated matrix cell changes.
10. [State] Delivery passes pvg lint, targeted video/evidence tests, canonical checker after independent review, release verification with release=ready and tag_created=false, protected-file parity, and git diff --check; the story is delivered and independently accepted without self-approval.

## Testing Requirements
- Real no-mock host integration where admitted.
- Verify all downloads by exact SHA-256 and byte size.
- Rehash source and derived references before and after.
- Probe all successful media and derive objective gates mechanically.
- Run canonical checker, targeted tests, pvg lint, release verify, protected parity, and diff check.
- Preserve complete native failure tails for boundaries.

## Delivery Requirements
Record authorization/decision, download table and actual bytes, hashes, disk/GPU snapshots, source/mask derivation, commands, per-operation outputs/boundaries, matrix transition, gates, bundle size, pushed head, and PR. Stop on any undeclared network need or missing input.

## MANDATORY SKILLS
- pvg

## nd_contract
status: new

### evidence
- Authored from merged main 079651d9, live host/disk/GPU inspection, Wan2GP SCAIL model definitions, Hugging Face metadata, and the operator's "you decide" authorization.

### proof
- [ ] Pending atomic claim, bounded download, and implementation.

## USER INTENT AND DISPATCHER DECISION
The operator was asked which remaining download batch to authorize first and replied verbatim: "you decide."

The dispatcher decides SCAIL-2. It is the lowest-risk next batch: its complete declared dependency set is 26,009,968,164 bytes, the host has 64,910,606,336 bytes free, the GPU is idle with 23,834 MiB free, and the batch leaves roughly 38.9 GB of disk headroom. LTX-2.3 and Wan/2GP remain later batches.

## Embedded Current State
At merged main 079651d9, the video matrix has 27 host_run_verified cells, 43 unsupported cells, 4 dependency_blocked cells, and 25 planned cells. The only planned rows are:

- LTX-2.3: 9 cells
- SCAIL-2: 7 cells
- Wan/2GP: 9 cells

This story owns exactly the seven SCAIL-2 planned cells: create, extend, blend, retake, edit, repaint, and recast. The existing typed backend boundaries for SCAIL outpaint and upscale remain unchanged.

## Exact Authorized Downloads
The operator's "you decide" authorizes this selected SCAIL-2 batch only. Planned download bytes are 26,009,968,164. Every file must be downloaded only into the existing Wan2GP checkpoint tree, hash-verified, and recorded:

| Asset | Destination | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| scail2_14B_quanto_mbf16_int8.safetensors | /home/straughter/Wan2GP/ckpts/scail2_14B_quanto_mbf16_int8.safetensors | 16644305281 | 94e4c007370587157f4ca80637fee01aaab9c700192254a6c1379d9047a14460 |
| models_t5_umt5-xxl-enc-quanto_int8.safetensors | /home/straughter/Wan2GP/ckpts/umt5-xxl/models_t5_umt5-xxl-enc-quanto_int8.safetensors | 6733337738 | 5e4961851c78838931990549810ed51c9036081b2ad80bf464c4e2603c5f922c |
| Wan2.1_VAE.safetensors | /home/straughter/Wan2GP/ckpts/Wan2.1_VAE.safetensors | 507593157 | 3ce0c02b9470532e7f63f3e2f8e83b0681fdeaa432e969c412482d2b3b78267b |
| nlf_l_multi_0.3.2.eager.safetensors | /home/straughter/Wan2GP/ckpts/pose/nlf_l_multi_0.3.2.eager.safetensors | 355296592 | 07494758eb4b7832a099dee9b3a5040288fa869b9417dc71f8dfd519c85eebd7 |
| nlf_l_multi_0.3.2.eager.meta.json | /home/straughter/Wan2GP/ckpts/pose/nlf_l_multi_0.3.2.eager.meta.json | 27222 | 2fce0ccda5422016c305023fd2f6c5abc7ea8e4f |
| sam3.1_multiplex_bf16.safetensors | /home/straughter/Wan2GP/ckpts/sam3/sam3.1_multiplex_bf16.safetensors | 1746597176 | 4e2cd82698b64b7d32349c8bbb4f43422e199cd1bfc9ca6b88bbef562af7e99e |
| bpe_simple_vocab_16e6.txt.gz | /home/straughter/Wan2GP/ckpts/sam3/bpe_simple_vocab_16e6.txt.gz | 1356917 | 924691ac288e54409236115652ad4aa250f48203de50a9e4722a6ecd48d6804a |
| umt5 tokenizer.json | /home/straughter/Wan2GP/ckpts/umt5-xxl/tokenizer.json | 16837417 | 6e197b4d3dbd71da14b4eb255f4fa91c9c1f2068b20a2de2472967ca3d22602b |
| umt5 spiece.model | /home/straughter/Wan2GP/ckpts/umt5-xxl/spiece.model | 4548313 | e3909a67b780650b35cf529ac782ad2b6b26e6d1f849d3fbb6a872905f452458 |
| umt5 tokenizer_config.json | /home/straughter/Wan2GP/ckpts/umt5-xxl/tokenizer_config.json | 61728 | 4e1cc1cd85599ce0b47fd0a746af188fe4043ff2a |
| umt5 special_tokens_map.json | /home/straughter/Wan2GP/ckpts/umt5-xxl/special_tokens_map.json | 6623 | 14855e7052ffbb595057dfd791d293c1c940db2c |

The control/reference video is already local and must not be downloaded:

- /home/straughter/Downloads/HOL120_ssscdn_scail_r9_00001.mp4
- SHA-256 c71398ba3c4fe6394c83450d7cd5267187e4c65b8d9b568f9457f1a9aac03ca8
- 384x224, 9 frames, 24 fps, 0.375 s, with embedded generation provenance.

## Boundary Map
PRODUCES:
- datasets/runs/maestro-parity/WD-ycjg/ -> authorized SCAIL-2 download record and seven-cell evidence
  spec: download manifest and hashes, source/control/reference provenance, isolated Wan2GP identity, native argv/logs, outputs or exact typed boundaries, media gates, checker result, reviewer decision, and matrix transition.
- docs/video-capabilities.md -> seven SCAIL-2 target-cell updates
  event: update only the seven owned planned cells; preserve existing outpaint and upscale typed boundaries.

CONSUMES:
- datasets/runs/maestro-parity/WD-2gyw/planning/models.json -> declared SCAIL model hash and destination
  source: verify the main checkpoint hash before queue admission.
- /home/straughter/Downloads/HOL120_ssscdn_scail_r9_00001.mp4 -> local person-bearing control/reference video
  source: hash-copy into the story namespace and never mutate the source.
- scripts/verify_maestro_parity.py -> canonical evidence checker
  event: checker exit 0 is required for any host_run_verified disposition.

## Story Acceptance Criteria
1. [State] Start from current origin/main, create/push a clean story branch/worktree, record base identity, and atomically claim the story before download or host mutation.
2. [State] Record verbatim authorization and the dispatcher's SCAIL-2 decision, then download only the eleven declared files into their exact destinations; reject any size/hash mismatch and leave no partial file admitted.
3. [State] Rehash every downloaded asset and the local control video before and after execution; record actual network bytes, destination sizes, disk before/after, and isolated Wan2GP source identity.
4. [State] Prepare a SCAIL-compatible reference frame and colored mask from the local control using the downloaded SAM3 helper without downloading any additional asset; hash every derived input.
5. [State] Give each of create, extend, blend, retake, edit, repaint, and recast its own native attempt or exact typed boundary; evidence cannot be inherited across operations.
6. [State] Every successful output records argv, native log, queue/exit state, SHA-256, ffprobe metadata, contact sheet/first frame, and an operation-appropriate objective gate.
7. [State] Every unsuccessful cell records exact exit, failing stage, missing/incompatible control, before/after GPU/source state, and an honest dependency or host-implementation boundary rather than a hardware verdict.
8. [Unwanted] No undeclared download, dependency mutation, live-tree mutation, protected-engine semantic change, threshold change, training, provider spend, or unrelated process action occurs.
9. [State] docs/video-capabilities.md mechanically changes exactly the seven owned planned cells; a transition artifact proves zero SCAIL planned cells remain and no unrelated matrix cell changes.
10. [State] Delivery passes pvg lint, targeted video/evidence tests, canonical checker after independent review, release verification with release=ready and tag_created=false, protected-file parity, and git diff --check; the story is delivered and independently accepted without self-approval.

## Testing Requirements
- Real no-mock host integration where admitted.
- Verify all downloads by exact SHA-256 and byte size.
- Rehash source and derived references before and after.
- Probe all successful media and derive objective gates mechanically.
- Run canonical checker, targeted tests, pvg lint, release verify, protected parity, and diff check.
- Preserve complete native failure tails for boundaries.

## Delivery Requirements
Record authorization/decision, download table and actual bytes, hashes, disk/GPU snapshots, source/mask derivation, commands, per-operation outputs/boundaries, matrix transition, gates, bundle size, pushed head, and PR. Stop on any undeclared network need or missing input.

## MANDATORY SKILLS
- pvg

## nd_contract
status: new

### evidence
- Authored from merged main 079651d9, live host/disk/GPU inspection, Wan2GP SCAIL model definitions, Hugging Face metadata, and the operator's "you decide" authorization.

### proof
- [ ] Pending atomic claim, bounded download, and implementation.

## USER INTENT AND DISPATCHER DECISION
The operator was asked which remaining download batch to authorize first and replied verbatim: "you decide."

The dispatcher decides SCAIL-2. It is the lowest-risk next batch: its complete declared dependency set is 26,009,968,164 bytes, the host has 64,910,606,336 bytes free, the GPU is idle with 23,834 MiB free, and the batch leaves roughly 38.9 GB of disk headroom. LTX-2.3 and Wan/2GP remain later batches.

## Embedded Current State
At merged main 079651d9, the video matrix has 27 host_run_verified cells, 43 unsupported cells, 4 dependency_blocked cells, and 25 planned cells. The only planned rows are:

- LTX-2.3: 9 cells
- SCAIL-2: 7 cells
- Wan/2GP: 9 cells

This story owns exactly the seven SCAIL-2 planned cells: create, extend, blend, retake, edit, repaint, and recast. The existing typed backend boundaries for SCAIL outpaint and upscale remain unchanged.

## Exact Authorized Downloads
The operator's "you decide" authorizes this selected SCAIL-2 batch only. Planned download bytes are 26,009,968,164. Every file must be downloaded only into the existing Wan2GP checkpoint tree, hash-verified, and recorded:

| Asset | Destination | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| scail2_14B_quanto_mbf16_int8.safetensors | /home/straughter/Wan2GP/ckpts/scail2_14B_quanto_mbf16_int8.safetensors | 16644305281 | 94e4c007370587157f4ca80637fee01aaab9c700192254a6c1379d9047a14460 |
| models_t5_umt5-xxl-enc-quanto_int8.safetensors | /home/straughter/Wan2GP/ckpts/umt5-xxl/models_t5_umt5-xxl-enc-quanto_int8.safetensors | 6733337738 | 5e4961851c78838931990549810ed51c9036081b2ad80bf464c4e2603c5f922c |
| Wan2.1_VAE.safetensors | /home/straughter/Wan2GP/ckpts/Wan2.1_VAE.safetensors | 507593157 | 3ce0c02b9470532e7f63f3e2f8e83b0681fdeaa432e969c412482d2b3b78267b |
| nlf_l_multi_0.3.2.eager.safetensors | /home/straughter/Wan2GP/ckpts/pose/nlf_l_multi_0.3.2.eager.safetensors | 355296592 | 07494758eb4b7832a099dee9b3a5040288fa869b9417dc71f8dfd519c85eebd7 |
| nlf_l_multi_0.3.2.eager.meta.json | /home/straughter/Wan2GP/ckpts/pose/nlf_l_multi_0.3.2.eager.meta.json | 27222 | 2fce0ccda5422016c305023fd2f6c5abc7ea8e4f |
| sam3.1_multiplex_bf16.safetensors | /home/straughter/Wan2GP/ckpts/sam3/sam3.1_multiplex_bf16.safetensors | 1746597176 | 4e2cd82698b64b7d32349c8bbb4f43422e199cd1bfc9ca6b88bbef562af7e99e |
| bpe_simple_vocab_16e6.txt.gz | /home/straughter/Wan2GP/ckpts/sam3/bpe_simple_vocab_16e6.txt.gz | 1356917 | 924691ac288e54409236115652ad4aa250f48203de50a9e4722a6ecd48d6804a |
| umt5 tokenizer.json | /home/straughter/Wan2GP/ckpts/umt5-xxl/tokenizer.json | 16837417 | 6e197b4d3dbd71da14b4eb255f4fa91c9c1f2068b20a2de2472967ca3d22602b |
| umt5 spiece.model | /home/straughter/Wan2GP/ckpts/umt5-xxl/spiece.model | 4548313 | e3909a67b780650b35cf529ac782ad2b6b26e6d1f849d3fbb6a872905f452458 |
| umt5 tokenizer_config.json | /home/straughter/Wan2GP/ckpts/umt5-xxl/tokenizer_config.json | 61728 | 4e1cc1cd85599ce0b47fd0a746af188fe4043ff2a |
| umt5 special_tokens_map.json | /home/straughter/Wan2GP/ckpts/umt5-xxl/special_tokens_map.json | 6623 | 14855e7052ffbb595057dfd791d293c1c940db2c |

The control/reference video is already local and must not be downloaded:

- /home/straughter/Downloads/HOL120_ssscdn_scail_r9_00001.mp4
- SHA-256 c71398ba3c4fe6394c83450d7cd5267187e4c65b8d9b568f9457f1a9aac03ca8
- 384x224, 9 frames, 24 fps, 0.375 s, with embedded generation provenance.

## Boundary Map
PRODUCES:
- datasets/runs/maestro-parity/WD-VIDEO/ -> authorized SCAIL-2 download record and seven-cell evidence
  spec: download manifest and hashes, source/control/reference provenance, isolated Wan2GP identity, native argv/logs, outputs or exact typed boundaries, media gates, checker result, reviewer decision, and matrix transition.
- docs/video-capabilities.md -> seven SCAIL-2 target-cell updates
  event: update only the seven owned planned cells; preserve existing outpaint and upscale typed boundaries.

CONSUMES:
- datasets/runs/maestro-parity/WD-2gyw/planning/models.json -> declared SCAIL model hash and destination
  source: verify the main checkpoint hash before queue admission.
- /home/straughter/Downloads/HOL120_ssscdn_scail_r9_00001.mp4 -> local person-bearing control/reference video
  source: hash-copy into the story namespace and never mutate the source.
- scripts/verify_maestro_parity.py -> canonical evidence checker
  event: checker exit 0 is required for any host_run_verified disposition.

## Story Acceptance Criteria
1. [State] Start from current origin/main, create/push a clean story branch/worktree, record base identity, and atomically claim the story before download or host mutation.
2. [State] Record verbatim authorization and the dispatcher's SCAIL-2 decision, then download only the eleven declared files into their exact destinations; reject any size/hash mismatch and leave no partial file admitted.
3. [State] Rehash every downloaded asset and the local control video before and after execution; record actual network bytes, destination sizes, disk before/after, and isolated Wan2GP source identity.
4. [State] Prepare a SCAIL-compatible reference frame and colored mask from the local control using the downloaded SAM3 helper without downloading any additional asset; hash every derived input.
5. [State] Give each of create, extend, blend, retake, edit, repaint, and recast its own native attempt or exact typed boundary; evidence cannot be inherited across operations.
6. [State] Every successful output records argv, native log, queue/exit state, SHA-256, ffprobe metadata, contact sheet/first frame, and an operation-appropriate objective gate.
7. [State] Every unsuccessful cell records exact exit, failing stage, missing/incompatible control, before/after GPU/source state, and an honest dependency or host-implementation boundary rather than a hardware verdict.
8. [Unwanted] No undeclared download, dependency mutation, live-tree mutation, protected-engine semantic change, threshold change, training, provider spend, or unrelated process action occurs.
9. [State] docs/video-capabilities.md mechanically changes exactly the seven owned planned cells; a transition artifact proves zero SCAIL planned cells remain and no unrelated matrix cell changes.
10. [State] Delivery passes pvg lint, targeted video/evidence tests, canonical checker after independent review, release verification with release=ready and tag_created=false, protected-file parity, and git diff --check; the story is delivered and independently accepted without self-approval.

## Testing Requirements
- Real no-mock host integration where admitted.
- Verify all downloads by exact SHA-256 and byte size.
- Rehash source and derived references before and after.
- Probe all successful media and derive objective gates mechanically.
- Run canonical checker, targeted tests, pvg lint, release verify, protected parity, and diff check.
- Preserve complete native failure tails for boundaries.

## Delivery Requirements
Record authorization/decision, download table and actual bytes, hashes, disk/GPU snapshots, source/mask derivation, commands, per-operation outputs/boundaries, matrix transition, gates, bundle size, pushed head, and PR. Stop on any undeclared network need or missing input.

## MANDATORY SKILLS
- pvg

## nd_contract
status: new

### evidence
- Authored from merged main 079651d9, live host/disk/GPU inspection, Wan2GP SCAIL model definitions, Hugging Face metadata, and the operator's "you decide" authorization.

### proof
- [ ] Pending atomic claim, bounded download, and implementation.

## Acceptance Criteria


## Design


## Notes
## Implementation Evidence

### Byte-accounting rework
The PM rejection identified one arithmetic typo and no implementation/media defect. Corrected subtotal:

- `iopath` 42,226 bytes
- `portalocker` 129,647 bytes
- `pycocotools` 493,172 bytes
- Exact story-local total: **665,045 bytes**
- Combined session network bytes: `2,408,271,915 + 665,045 = 2,408,936,960`
- Total authorized bytes remain `28,418,905,124`.

Corrected artifacts: `host-logs/15-story-local-download-accounting.txt`, `host-logs/96_final_download_accounting.txt`, and `evidence.json.download_evidence`. No `664045` value remains in the bundle.

### CI/Test Results
Commands run:
- `/tmp/15_story_local_python_deps.sh`
- `/tmp/40_postflight.sh`
- `uv run --frozen --extra dev pytest -q tests/test_maestro_parity_evidence.py tests/test_video_capabilities.py --junitxml=datasets/runs/maestro-parity/WD-ycjg/targeted-tests.xml`
- `uv run --frozen --extra dev python scripts/verify_maestro_parity.py datasets/runs/maestro-parity/WD-ycjg`
- `pvg verify ...`
- `pvg lint --backlog`
- `uv run --frozen --extra dev wgp release verify`
- `git diff --check`
- protected-file parity from `079651d9`

Summary: targeted pytest PASS 110/110 with `errors=0`, `failures=0`, `skipped=0`; pvg verify PASS; backlog lint PASS 142 scanned, 0 errors, 0 review findings; release at clean rework head is `release=ready` and `tag_created=false`; diff and protected parity PASS. Canonical checker remains pending only independent reviewer decision/links.

Commit SHA: c10e1ee449a8e05897626457e912265e0f78fba7
Final pushed evidence head: 45465a7a27bd5a180dd7ce88f99922a536e143ba

## nd_contract
status: rejected

### evidence
- PM rejection applied via pvg story reject on 2026-09-27.

### proof
- [ ] Story requires another developer delivery before it can be accepted.


## Implementation Evidence

### Authorization, download, and isolation
- Verbatim authorization and dispatcher decision: `datasets/runs/maestro-parity/WD-ycjg/operator-authorization.md`.
- Repository base: `079651d9`; isolated Wan2GP source: `4c93b64a47b5b0a915f2abec2ce754be98227150`; final isolated-source status is only `?? ckpts`.
- Sixteen model/helper assets totaling `28,418,240,079` bytes matched exact size and SHA-256 before and after execution: `host-logs/download-report.tsv`, `host-logs/91_model_asset_hashes_after.txt`.
- Three story-local dependencies totaling `664,045` bytes (`iopath`, `portalocker`, `pycocotools`) were used only under the run directory; live Wan2GP dependencies were not mutated: `host-logs/15-story-local-download-accounting.txt`.
- Total authorized/downloaded bytes: `28,418,905,124`.
- The local control video hash remained `c71398ba3c4fe6394c83450d7cd5267187e4c65b8d9b568f9457f1a9aac03ca8`; SAM3 generated a colored one-person mask with SHA-256 `d645b15fddd51c540755697bb4ffb05949db17ea606aa0d6896f18c3175b5c9d`.

### Real outputs
- create: `outputs/create/wd_ycjg_create.mp4`; SHA-256 `1fb5689ac1647dda8ddd0806981eb0ee93a2ca641956ea3848fce65aad817a2a`; 384x224, 9 frames, 0.375 s, 24 fps.
- retake: `outputs/retake/wd_ycjg_retake.mp4`; SHA-256 `a557d6ddf16a61a8a523c1db79e9fcbf99917c831de7edfc2925e18ca72e9bdf`; PSNR versus create `11.066936 dB`.
- repaint: `outputs/repaint/wd_ycjg_repaint.mp4`; SHA-256 `86fe90785f812b1c94f2b3bb3dd4eb83c79f19d6a5d4779b4131cb36c9f0b5df`; PSNR `14.037307 dB`.
- recast: `outputs/recast/wd_ycjg_recast.mp4`; SHA-256 `9c1dc8ee2ddc69a9ecb9919fe2cba515c14bc69b4f0491bcb24f1986ecdb4636`; PSNR `14.461542 dB`.
- edit: `outputs/edit/wd_ycjg_edit.mp4`; SHA-256 `ecc3017004f7d96584f5a6a984e58589500e12793694555aa2bdec589848de42`; PSNR `19.480868 dB`.
- blend: `outputs/blend/wd_ycjg_blend.mp4`; SHA-256 `8dc7f0799efb0a16fdfade35d83b48a251eabcf6c9828c885ba2a6249c40ed5c`; authoritative retry loaded both guides via `V01AI+`; PSNR `16.512936 dB`.
- Visual review: `review/all-contact-sheets.jpg` shows six distinct nonblank operation outputs; `review/control-mask-contact-sheet.jpg` shows the stable colored person mask.

### Exact extension boundary
- `outputs/extend/wd_ycjg_extend.mp4` was generated but cannot be host_run_verified.
- Requested: 21 frames / 0.875 s. Measured: 9 frames / 0.375 s, exactly the control length.
- PSNR versus create: `46.593200 dB`, showing a near-identical non-extension.
- Boundary record: `boundary-evidence.json`; native log: `host-logs/extend.render.log`.

### CI/Test Results
Commands run:
- `ssh 3090 /tmp/10_download_preflight.sh`
- `ssh 3090 /tmp/15_story_local_python_deps.sh`
- `ssh 3090 /home/straughter/Wan2GP/venv/bin/python /tmp/20_prepare_mask.py`
- `ssh 3090 /tmp/30_run_create.sh`
- `ssh 3090 /tmp/31_run_remaining.sh`
- `ssh 3090 /tmp/32_blend_retry.sh`
- `ssh 3090 /tmp/40_postflight.sh`
- `uv run --frozen --extra dev pytest -q tests/test_maestro_parity_evidence.py tests/test_video_capabilities.py --junitxml=datasets/runs/maestro-parity/WD-ycjg/targeted-tests.xml`
- `uv run --frozen --extra dev python scripts/verify_maestro_parity.py datasets/runs/maestro-parity/WD-ycjg`
- `pvg verify docs/video-capabilities.md datasets/runs/maestro-parity/WD-ycjg/build_evidence.py datasets/runs/maestro-parity/WD-ycjg/host-scripts/*.py datasets/runs/maestro-parity/WD-ycjg/host-scripts/*.sh`
- `pvg lint --backlog`
- `uv run --frozen --extra dev wgp release verify`
- `git diff --check`
- `git diff --exit-code 079651d9 -- services/jobs/queue.py services/director/renderers/policy.py services/director/wiring.py services/jobs/preflight.py scripts/run_film.py`

Summary: targeted pytest PASS 110/110 with `errors=0`, `failures=0`, `skipped=0`; pvg verify PASS; backlog lint PASS 142 scanned, 0 errors, 0 review findings; release at clean implementation head is `release=ready` and `tag_created=false`; protected parity and diff-check PASS. Canonical checker is pending exactly and only independent reviewer decision/links.

### Matrix transition
`matrix-transition-check.json` records seven changed target cells, zero SCAIL planned cells, six host_run_verified cells, and three unsupported cells including the pre-existing typed outpaint/upscale boundaries.

### AC Verification
| AC | Result | Evidence |
| --- | --- | --- |
| 1 | PASS | Clean pushed branch/worktree and atomic claim |
| 2 | PASS | Nineteen exact downloads verified; no partial file admitted |
| 3 | PASS | Model/helper and source hashes reproduced after execution |
| 4 | PASS | SAM3 colored mask and all derived inputs hashed |
| 5 | PASS | Seven cells received native attempts; no evidence inherited |
| 6 | PASS | Six outputs have argv, logs, exit, hash, probe, contact sheet, and gates |
| 7 | PASS | Extend records exact non-extension boundary, not a false success |
| 8 | PASS | No undeclared live mutation; isolated source final status `?? ckpts` |
| 9 | PASS | Exactly seven matrix cells changed; zero target planned cells |
| 10 | PASS pending independent reviewer | Local gates pass; canonical checker awaits reviewer fields only |

### Branch and PR
Commit SHA: 588fae0959f79ea3ad9d52367794e75795263c3e
Final evidence head: 8855d1d9
Branch: `story/WD-ycjg`
PR: https://github.com/jmanhype/wangp-dspy/pull/207
Bundle: 168 files, 3,723,556 bytes.

## History
- 2026-09-27T13:24:02Z dep_added: blocks WD-fay0
- 2026-09-27T13:24:41Z status: open -> in_progress
- 2026-09-27T13:24:41Z auto-follows: linked to predecessor WD-8h6p
- 2026-09-27T13:24:41Z claimed by dev-WD-ycjg
- 2026-09-27T14:27:26Z status: in_progress -> in_progress
- 2026-09-27T14:27:26Z auto-follows: linked to predecessor WD-m25k
- 2026-09-27T14:35:40Z status: in_progress -> open
- 2026-09-27T14:35:40Z released by speed
- 2026-09-27T14:43:22Z status: open -> in_progress
- 2026-09-27T14:43:22Z auto-follows: linked to predecessor WD-obkn

## Links
- Parent: [[WD-3nod]]
- Blocks: [[WD-fay0]]
- Follows: [[WD-8h6p]], [[WD-m25k]], [[WD-obkn]]

## Comments

## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-27.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.

### 2026-09-27T14:35:41Z speed
EXPECTED: AC #3 requires rehashing every downloaded asset and recording actual network bytes and destination sizes exactly. The three story-local dependencies are declared and verified as 42,226 + 129,647 + 493,172 = 665,045 bytes. DELIVERED: All nineteen destination files independently rehash to the declared sizes and SHA-256 values on the 3090, and the total authorized size 28,418,905,124 is arithmetically correct, but host-logs/15-story-local-download-accounting.txt:2, host-logs/96_final_download_accounting.txt:2, evidence.json download_evidence.story_local_dependency_bytes, and build_evidence.py:271 incorrectly record 664,045 bytes. GAP: The delivered actual local-network byte accounting is internally inconsistent by 1,000 bytes, so the explicit AC #3 proof is not exact even though individual file hashes and sizes are valid. FIX: Correct every story-local dependency subtotal from 664045 to 665045, retain total_authorized_bytes=28418905124, and explicitly record combined session network bytes 2408271915 + 665045 = 2408936960 where applicable; rerun the builder, canonical checker after independent review, targeted tests, lint, release, diff, and protected parity, then redeliver. Do not merge or PR on this rejection.
