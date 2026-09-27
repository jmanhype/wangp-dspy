---
id: WD-ycjg
title: "SCAIL-2 authorized download video batch"
status: open
priority: 1
type: task
labels: [capability, video, evidence, external-integration]
parent: WD-3nod
created_at: 2026-09-27T13:24:01Z
created_by: speed
updated_at: 2026-09-27T13:24:02Z
content_hash: "sha256:06b329e7eda70ba477c0f689573785e4483e9dd66966eabe9df666ef81f85ebe"
---

## Description
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


## History


## Links
- Parent: [[WD-3nod]]

## Comments
