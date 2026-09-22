---
id: WD-6tox
title: "Video breadth: Maestro model families, operations, multi-clip, long form, and LoRA"
status: open
priority: 2
type: feature
labels: [capability, external-integration]
parent: WD-t741
created_at: 2026-09-22T20:24:43Z
created_by: speed
updated_at: 2026-09-22T20:27:35Z
content_hash: "sha256:f6df1116dd57f731dfc94419ff1d5b9d470f6beb961e427fe4ab7bd1fbda6701"
blocks: [WD-fasw, WD-tkuz, WD-8ioj, WD-eq1i, WD-gc09]
---

## Description
## USER INTENT
Observable outcome: a user can request every Maestro video generation family and operation through typed Wangp requests, see an exact governed plan without a GPU, and obtain real generated artifacts only after separate authorization.

## Context (Embedded)
- The governed repository path is plan -> durable queue -> host render -> QC gates -> assembly -> provenance/recipe; `wgp` is the stable CLI and GPU execution is never implied by planning.
- Existing first-class video depth is the MiniMax H3 / Ref2VA / Wan2GP lane under `predict/`, `host/`, `services/jobs/`, and `qc/`; this story broadens and normalizes it rather than bypassing it.
- The Maestro contract is MiniMax H3 plus H3 VDN hybrid-attention and TaoMate H3 three-step presets, KFI/Frames Injection continuity, H3 Outpaint and H3 Audio Refinement, LTX-2.5/2.3, SCAIL-2, Wan, and Hunyuan.
- The operation contract is create, extend, blend, retake, edit, outpaint, repaint, recast, and upscale; upscale also has a finishing consumer and must not fork ungoverned post-processing.
- Multi-clip requests carry per-clip prompts and explicit sliding-window overlaps. Long form supports up to 60 minutes with one-window, exact-timecode, and window-count controls.
- LoRA support includes style LoRAs and the Maestro armed-at-generation behaviour: selection and weights are part of the immutable render settings and provenance, never a hidden host convenience.

## OUT OF SCOPE
-  weakening a QC gate, retry policy, provenance field, or queue transition to make a backend appear supported.
- Naming two vendors as equivalent without separate recorded runs; provider aliases are not model parity.
- Claiming a backend or operation from settings normalization alone.

## DIFF BUDGET
Roughly 12 files, under 1,100 authored changed LOC, excluding third-party weights and generated media.

## Boundary Map
PRODUCES:
- predict/video_capabilities.py -> typed `VideoCapabilityRequest`, model/preset/LoRA/operation enums, and per-backend settings normalization
- services/video/operation_compiler.py -> create/extend/blend/retake/edit/outpaint/repaint/recast/upscale jobs with per-clip prompts, overlaps, and 60-minute long-form window controls
- host/video_backends.py -> explicit backend adapters that fail closed on missing licence, model hash, VRAM profile, or operation support
- wangp/video_cli.py -> `wgp video` command implementation and authorized submission boundary
- docs/video-capabilities.md -> request schema, backend/operation matrix, supported host profile, and no-GPU/GPU evidence rules
- tests/test_video_capabilities.py -> real-process CLI/queue/reconstruction coverage; no mocks
- datasets/runs/maestro-parity/WD-6tox/ -> recorded authorized run bundles; each bundle is generated only after operator approval

CONSUMES:
- predict/job_config.py -> purpose
  spec: existing H3 frame-grid and typed job normalization
- predict/render_profiles.py -> purpose
  spec: existing render-profile definitions
- predict/profile_selector.py -> purpose
  spec: existing governed profile selection
- services/jobs/queue.py -> purpose
  spec: durable queue record and attempt transitions
- services/jobs/preflight.py -> purpose
  spec: typed missing host/model/asset failures
- host/render_host.py -> purpose
  spec: explicit remote run/push/pull boundary
- host/wangp_adapter.py -> purpose
  spec: existing H3/WanGP adapter settings and evidence markers
- predict/assembler.py -> purpose
  spec: existing assembly contract
- predict/v3_recipe.py -> purpose
  spec: immutable recipe/provenance fields
- wangp/cli.py -> purpose
  spec: stable verb registration and exit-code contract


## Required Outcomes
### no-GPU verifiable now
- Real `wgp` tests normalize representative requests for every named family, preset, operation, LoRA arrangement, overlap, and all three long-form controls, producing deterministic JSON and exit 0.
- A real temporary durable queue records one job per clip with immutable backend, model, LoRA, reference, window, and overlap fields; queue submission remains false and no host is contacted.
- Missing model manifest/hash, unsupported operation/backend pair, invalid overlap/timecode/window count, absent reference, or an unusable LoRA produces a typed exit-2 diagnostic with exact remediation and no partial queue record.
- Dry-run reconstruction regenerates the same backend settings from the queue record and recipe seed; hash comparison proves no hidden mutation.
- The video capability matrix row for every family and operation is `planned` until a matching authorized run bundle exists.

### requires an authorized host render
- Separate operator authorization is required for each run batch. Recorded evidence must cover each backend family and each operation family, including H3 VDN, TaoMate three-step, KFI continuity, H3 Outpaint, and H3 Audio Refinement.
- Manual real-endpoint verification smoke test: each artifact is retrieved through the governed host path and has ffprobe metadata, hashes, command, commit, model/LoRA provenance, queue attempt, relevant QC result, and assembly/recipe linkage.
- A long-form multi-clip run proves per-clip prompts, the selected overlap strategy, exact duration/window accounting, and deterministic reconstruction without re-render.

## Testing Requirements
- `uv run --frozen --extra dev pytest tests/test_video_capabilities.py -q`, plus scoped integration tests using the real CLI, real temporary SQLite queue, real filesystem, and real subprocesses.
- No mocks: unsupported/missing-host cases must call the actual configuration and preflight code and assert real exit codes/output.
- Authorized-host evidence is reviewed from the recorded bundle with ffprobe and hashes; no live GPU command is run by the no-GPU test suite.

## MANDATORY SKILLS
- pvg

## Delivery Requirements
- Developer must use `pvg story deliver`, paste real command output, and provide an AC table plus hashes for every produced artifact and read-only input.
- A GPU-dependent claim may be made only from a recorded run bundle with command, repository commit, model/asset provenance, queue record, exit status, output hashes, QC/gate evidence, and operator authorization for that run. A plan, prompt, unit test, or intention is not generation evidence.
- No story may silently download a model, contact a host, use a paid provider, or claim a capability the matrix marks unverified.

## nd_contract
status: new

### evidence
- Created 2026-09-22 under epic WD-t741 from the Maestro v2.3.0 capability inventory.

### proof
- [ ] Pending implementation and independent PM acceptance.


## USER INTENT
Observable outcome: a user can request every Maestro video generation family and operation through typed Wangp requests, see an exact governed plan without a GPU, and obtain real generated artifacts only after separate authorization.

## Context (Embedded)
- The governed repository path is plan -> durable queue -> host render -> QC gates -> assembly -> provenance/recipe; `wgp` is the stable CLI and GPU execution is never implied by planning.
- Existing first-class video depth is the MiniMax H3 / Ref2VA / Wan2GP lane under `predict/`, `host/`, `services/jobs/`, and `qc/`; this story broadens and normalizes it rather than bypassing it.
- The Maestro contract is MiniMax H3 plus H3 VDN hybrid-attention and TaoMate H3 three-step presets, KFI/Frames Injection continuity, H3 Outpaint and H3 Audio Refinement, LTX-2.5/2.3, SCAIL-2, Wan, and Hunyuan.
- The operation contract is create, extend, blend, retake, edit, outpaint, repaint, recast, and upscale; upscale also has a finishing consumer and must not fork ungoverned post-processing.
- Multi-clip requests carry per-clip prompts and explicit sliding-window overlaps. Long form supports up to 60 minutes with one-window, exact-timecode, and window-count controls.
- LoRA support includes style LoRAs and the Maestro armed-at-generation behaviour: selection and weights are part of the immutable render settings and provenance, never a hidden host convenience.

## OUT OF SCOPE
-  weakening a QC gate, retry policy, provenance field, or queue transition to make a backend appear supported.
- Naming two vendors as equivalent without separate recorded runs; provider aliases are not model parity.
- Claiming a backend or operation from settings normalization alone.

## DIFF BUDGET
Roughly 12 files, under 1,100 authored changed LOC, excluding third-party weights and generated media.

## Boundary Map
PRODUCES:
- predict/video_capabilities.py -> typed `VideoCapabilityRequest`, model/preset/LoRA/operation enums, and per-backend settings normalization
- services/video/operation_compiler.py -> create/extend/blend/retake/edit/outpaint/repaint/recast/upscale jobs with per-clip prompts, overlaps, and 60-minute long-form window controls
- host/video_backends.py -> explicit backend adapters that fail closed on missing licence, model hash, VRAM profile, or operation support
- wangp/video_cli.py -> `wgp video` command implementation and authorized submission boundary
- docs/video-capabilities.md -> request schema, backend/operation matrix, supported host profile, and no-GPU/GPU evidence rules
- tests/test_video_capabilities.py -> real-process CLI/queue/reconstruction coverage; no mocks
- datasets/runs/maestro-parity/WD-6tox/ -> recorded authorized run bundles; each bundle is generated only after operator approval

CONSUMES:
CONSUMES:
- predict/job_config.py -> purpose
  spec: existing H3 frame-grid and typed job normalization
- predict/render_profiles.py -> purpose
  spec: existing render-profile definitions
- predict/profile_selector.py -> purpose
  spec: existing governed profile selection
- services/jobs/queue.py -> purpose
  spec: durable queue record and attempt transitions
- services/jobs/preflight.py -> purpose
  spec: typed missing host/model/asset failures
- host/render_host.py -> purpose
  spec: explicit remote run/push/pull boundary
- host/wangp_adapter.py -> purpose
  spec: existing H3/WanGP adapter settings and evidence markers
- predict/assembler.py -> purpose
  spec: existing assembly contract
- predict/v3_recipe.py -> purpose
  spec: immutable recipe/provenance fields
- wangp/cli.py -> purpose
  spec: stable verb registration and exit-code contract


## Required Outcomes
### no-GPU verifiable now
- Real `wgp` tests normalize representative requests for every named family, preset, operation, LoRA arrangement, overlap, and all three long-form controls, producing deterministic JSON and exit 0.
- A real temporary durable queue records one job per clip with immutable backend, model, LoRA, reference, window, and overlap fields; queue submission remains false and no host is contacted.
- Missing model manifest/hash, unsupported operation/backend pair, invalid overlap/timecode/window count, absent reference, or an unusable LoRA produces a typed exit-2 diagnostic with exact remediation and no partial queue record.
- Dry-run reconstruction regenerates the same backend settings from the queue record and recipe seed; hash comparison proves no hidden mutation.
- The video capability matrix row for every family and operation is `planned` until a matching authorized run bundle exists.

### requires an authorized host render
- Separate operator authorization is required for each run batch. Recorded evidence must cover each backend family and each operation family, including H3 VDN, TaoMate three-step, KFI continuity, H3 Outpaint, and H3 Audio Refinement.
- Manual real-endpoint verification smoke test: each artifact is retrieved through the governed host path and has ffprobe metadata, hashes, command, commit, model/LoRA provenance, queue attempt, relevant QC result, and assembly/recipe linkage.
- A long-form multi-clip run proves per-clip prompts, the selected overlap strategy, exact duration/window accounting, and deterministic reconstruction without re-render.

## Testing Requirements
- `uv run --frozen --extra dev pytest tests/test_video_capabilities.py -q`, plus scoped integration tests using the real CLI, real temporary SQLite queue, real filesystem, and real subprocesses.
- No mocks: unsupported/missing-host cases must call the actual configuration and preflight code and assert real exit codes/output.
- Authorized-host evidence is reviewed from the recorded bundle with ffprobe and hashes; no live GPU command is run by the no-GPU test suite.

## MANDATORY SKILLS
- pvg

## Delivery Requirements
- Developer must use `pvg story deliver`, paste real command output, and provide an AC table plus hashes for every produced artifact and read-only input.
- A GPU-dependent claim may be made only from a recorded run bundle with command, repository commit, model/asset provenance, queue record, exit status, output hashes, QC/gate evidence, and operator authorization for that run. A plan, prompt, unit test, or intention is not generation evidence.
- No story may silently download a model, contact a host, use a paid provider, or claim a capability the matrix marks unverified.

## nd_contract
status: new

### evidence
- Created 2026-09-22 under epic WD-t741 from the Maestro v2.3.0 capability inventory.

### proof
- [ ] Pending implementation and independent PM acceptance.

## USER INTENT
Observable outcome: a user can request every Maestro video generation family and operation through typed Wangp requests, see an exact governed plan without a GPU, and obtain real generated artifacts only after separate authorization.

## Context (Embedded)
- The governed repository path is plan -> durable queue -> host render -> QC gates -> assembly -> provenance/recipe; `wgp` is the stable CLI and GPU execution is never implied by planning.
- Existing first-class video depth is the MiniMax H3 / Ref2VA / Wan2GP lane under `predict/`, `host/`, `services/jobs/`, and `qc/`; this story broadens and normalizes it rather than bypassing it.
- The Maestro contract is MiniMax H3 plus H3 VDN hybrid-attention and TaoMate H3 three-step presets, KFI/Frames Injection continuity, H3 Outpaint and H3 Audio Refinement, LTX-2.5/2.3, SCAIL-2, Wan, and Hunyuan.
- The operation contract is create, extend, blend, retake, edit, outpaint, repaint, recast, and upscale; upscale also has a finishing consumer and must not fork ungoverned post-processing.
- Multi-clip requests carry per-clip prompts and explicit sliding-window overlaps. Long form supports up to 60 minutes with one-window, exact-timecode, and window-count controls.
- LoRA support includes style LoRAs and the Maestro armed-at-generation behaviour: selection and weights are part of the immutable render settings and provenance, never a hidden host convenience.

## OUT OF SCOPE
-  weakening a QC gate, retry policy, provenance field, or queue transition to make a backend appear supported.
- Naming two vendors as equivalent without separate recorded runs; provider aliases are not model parity.
- Claiming a backend or operation from settings normalization alone.

## DIFF BUDGET
Roughly 12 files, under 1,100 authored changed LOC, excluding third-party weights and generated media.

## Boundary Map
PRODUCES:
- predict/video_capabilities.py -> typed `VideoCapabilityRequest`, model/preset/LoRA/operation enums, and per-backend settings normalization
- services/video/operation_compiler.py -> create/extend/blend/retake/edit/outpaint/repaint/recast/upscale jobs with per-clip prompts, overlaps, and 60-minute long-form window controls
- host/video_backends.py -> explicit backend adapters that fail closed on missing licence, model hash, VRAM profile, or operation support
- wangp/cli.py -> stable `wgp video ...` planning and authorized submission verbs
- docs/video-capabilities.md -> request schema, backend/operation matrix, supported host profile, and no-GPU/GPU evidence rules
- datasets/runs/maestro-parity/<story-id>/ -> recorded authorized run bundles; each bundle is generated only after operator approval

CONSUMES:
- predict/job_config.py -> existing H3 frame-grid and typed job normalization
- predict/render_profiles.py and predict/profile_selector.py -> governed profile selection
- services/jobs/queue.py and services/jobs/preflight.py -> durable queue and typed preflight failures
- host/render_host.py and host/wangp_adapter.py -> explicit remote execution and backend adapter boundary
- predict/assembler.py and predict/v3_recipe.py -> assembly and immutable recipe/provenance

## Required Outcomes
### no-GPU verifiable now
- Real `wgp` tests normalize representative requests for every named family, preset, operation, LoRA arrangement, overlap, and all three long-form controls, producing deterministic JSON and exit 0.
- A real temporary durable queue records one job per clip with immutable backend, model, LoRA, reference, window, and overlap fields; queue submission remains false and no host is contacted.
- Missing model manifest/hash, unsupported operation/backend pair, invalid overlap/timecode/window count, absent reference, or an unusable LoRA produces a typed exit-2 diagnostic with exact remediation and no partial queue record.
- Dry-run reconstruction regenerates the same backend settings from the queue record and recipe seed; hash comparison proves no hidden mutation.
- The video capability matrix row for every family and operation is `planned` until a matching authorized run bundle exists.

### requires an authorized host render
- Separate operator authorization is required for each run batch. Recorded evidence must cover each backend family and each operation family, including H3 VDN, TaoMate three-step, KFI continuity, H3 Outpaint, and H3 Audio Refinement.
- Each artifact is retrieved through the governed host path and has ffprobe metadata, hashes, command, commit, model/LoRA provenance, queue attempt, relevant QC result, and assembly/recipe linkage.
- A long-form multi-clip run proves per-clip prompts, the selected overlap strategy, exact duration/window accounting, and deterministic reconstruction without re-render.

## Testing Requirements
- `uv run --frozen --extra dev pytest tests/test_video_capabilities.py -q`, plus scoped integration tests using the real CLI, real temporary SQLite queue, real filesystem, and real subprocesses.
- No mocks: unsupported/missing-host cases must call the actual configuration and preflight code and assert real exit codes/output.
- Authorized-host evidence is reviewed from the recorded bundle with ffprobe and hashes; no live GPU command is run by the no-GPU test suite.

## MANDATORY SKILLS
- pvg

## Delivery Requirements
- Developer must use `pvg story deliver`, paste real command output, and provide an AC table plus hashes for every produced artifact and read-only input.
- A GPU-dependent claim may be made only from a recorded run bundle with command, repository commit, model/asset provenance, queue record, exit status, output hashes, QC/gate evidence, and operator authorization for that run. A plan, prompt, unit test, or intention is not generation evidence.
- No story may silently download a model, contact a host, use a paid provider, or claim a capability the matrix marks unverified.

## nd_contract
status: new

### evidence
- Created 2026-09-22 under epic WD-t741 from the Maestro v2.3.0 capability inventory.

### proof
- [ ] Pending implementation and independent PM acceptance.

## Acceptance Criteria


## Design


## Notes


## History
- 2026-09-22T20:24:45Z dep_added: blocks WD-fasw
- 2026-09-22T20:24:45Z dep_added: blocks WD-tkuz
- 2026-09-22T20:24:46Z dep_added: blocks WD-8ioj
- 2026-09-22T20:24:46Z dep_added: blocks WD-eq1i
- 2026-09-22T20:27:36Z dep_added: blocks WD-gc09

## Links
- Parent: [[WD-t741]]
- Blocks: [[WD-fasw]], [[WD-tkuz]], [[WD-8ioj]], [[WD-eq1i]], [[WD-gc09]]

## Comments
