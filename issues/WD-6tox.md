---
id: WD-6tox
title: "Video breadth: Maestro model families, operations, multi-clip, long form, and LoRA"
status: in_progress
priority: 2
type: feature
labels: [capability, external-integration]
parent: WD-t741
created_at: 2026-09-22T20:24:43Z
created_by: speed
updated_at: 2026-09-22T22:32:52Z
content_hash: "sha256:6c234b55f3db1606c8a48c16fde696af0049d0b8c34b24a658a6b7fbcd0d3311"
blocks: [WD-fasw, WD-tkuz, WD-8ioj, WD-eq1i, WD-gc09]
assignee: dev-WD-6tox
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
- predict/job_config.py -> existing H3 frame-grid and typed job normalization
  spec: existing H3 frame-grid and typed job normalization
- predict/render_profiles.py -> existing render-profile definitions
  spec: existing render-profile definitions
- predict/profile_selector.py -> existing governed profile selection
  spec: existing governed profile selection
- services/jobs/queue.py -> durable queue record and attempt transitions
  spec: durable queue record and attempt transitions
- services/jobs/preflight.py -> typed missing host/model/asset failures
  spec: typed missing host/model/asset failures
- host/render_host.py -> explicit remote run/push/pull boundary
  spec: explicit remote run/push/pull boundary
- host/wangp_adapter.py -> existing H3/WanGP adapter settings and evidence markers
  spec: existing H3/WanGP adapter settings and evidence markers
- predict/assembler.py -> existing assembly contract
  spec: existing assembly contract
- predict/v3_recipe.py -> immutable recipe/provenance fields
  spec: immutable recipe/provenance fields
- wangp/cli.py -> stable verb registration and exit-code contract
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


## Acceptance Criteria


## Design


## Notes
## Implementation Evidence
Summary: Implemented the no-GPU Maestro video planning slice only: typed family/preset/request normalization, fail-closed planned backend metadata, per-clip governed queue compilation, immutable model/LoRA/reference/window/overlap/recipe fields, typed exit-2 diagnostics, deterministic recipe-seed reconstruction, and planned capability documentation. No GPU, host, SSH, paid provider, model download, or authorized render was used or claimed.
Commands run:
- uv run --frozen --extra dev pytest tests/test_video_capabilities.py -q — exit 0; 24 passed.
- uv run --frozen --extra dev pytest -q at committed rebased head — exit 0; 1,700 passed, 1 skipped (1,701 collected).
- uv build --out-dir /tmp/wd-6tox-build-ba46601 — exit 0; one wheel and one sdist.
- Real-process evidence: 11 normal family/preset/operation cases, 11 typed failure classes, one three-clip temporary queue, and reconstruction — all exit as expected; every host-call sentinel file remained empty (/tmp/wd-6tox-evidence-ba46601/index.json, SHA256 4e5ae3bfcc9aad3ba4323408d7b25afade25c69785935138b7ef87a288caff13).
- Durable queue evidence: three pending jobs, one clip each; queue_submitted=false and host_contact=false in every clip (/tmp/wd-6tox-evidence-ba46601/queue-three-clips/queue-rows.json, SHA256 b67ae449d25bf32dcfebbf7bf286e6fc30f70184c35a2608e924d051810f4d11).
- Dry-run reconstruction: three recorded/reconstructed settings hash matches, all_match=true, hidden_mutation=false (/tmp/wd-6tox-evidence-ba46601/queue-three-clips/reconstruction.json, SHA256 9c8a0fc3bf88580f8e62740ae835a030f2c5ad1bf3110f14b2263b9d86b8bdc6).
- git fetch origin main && git rebase origin/main — branch already up to date; pushed ba466011d7a8cf372ee5711a5e07e4ce5a7717ce.
- gh pr create — https://github.com/jmanhype/wangp-dspy/pull/163.
SHA: ba466011d7a8cf372ee5711a5e07e4ce5a7717ce

### CI/Test Results
- Local scoped suite: exit 0; 24 passed.
- Local full suite: exit 0; 1,700 passed, 1 skipped.
- Build: exit 0; wangp_dspy-0.1.0-py3-none-any.whl SHA256 d3ca877deabe49e0448b47cb8f90f8f70632e3b248b49448d039efc063431f37; wangp_dspy-0.1.0.tar.gz SHA256 018bcd6cf77f1ec0d70d96aeefea0d5fbb9c1dd9883fe294213187f9c4da4fd0.
- GitHub check-runs for exact head ba466011d7a8cf372ee5711a5e07e4ce5a7717ce: test completed with success.

### AC Verification
| AC | Result | Evidence |
| --- | --- | --- |
| Real wgp tests normalize representative requests for every named family, preset, operation, LoRA arrangement, overlap, and all three long-form controls with deterministic JSON and exit 0 | verified | tests/test_video_capabilities.py: 24 passed; /tmp/wd-6tox-evidence-ba46601/index.json records 11 normal cases and empty host-call sentinels. |
| A real temporary durable queue records one job per clip with immutable backend, model, LoRA, reference, window, and overlap fields; queue submission remains false and no host is contacted | verified | /tmp/wd-6tox-evidence-ba46601/queue-three-clips/queue-rows.json: 3 pending jobs, one clip each, queue_submitted=false, host_contact=false; sentinel calls empty. |
| Missing manifest/hash, unsupported operation/backend pair, invalid overlap/timecode/window count, absent reference, or unusable LoRA produces typed exit 2 with remediation/next command and no partial queue | verified | /tmp/wd-6tox-evidence-ba46601/index.json: 11 failure cases, expected diagnostic code and exit 2, partial_queue_exists=false, host calls empty. |
| Dry-run reconstruction regenerates identical settings from queue record and recipe seed, proving no hidden mutation | verified | /tmp/wd-6tox-evidence-ba46601/queue-three-clips/reconstruction.json: 3/3 hash matches, all_match=true, hidden_mutation=false. |
| Capability matrix row for every family and operation remains planned until a matching authorized run bundle exists | verified | docs/video-capabilities.md marks every family/operation intersection planned and states required run-bundle evidence. |
| Recorded evidence covers every backend family and operation family with authorized host render | not verified - requires authorized host run | No run bundle exists; no GPU/host render was attempted. |
| Manual real-endpoint smoke artifacts include ffprobe metadata, hashes, command, commit, provenance, queue attempt, QC, and assembly/recipe linkage | not verified - requires authorized host run | No run bundle exists; no endpoint or host contact was attempted. |
| Long-form multi-clip authorized render proves prompts, overlap, duration/window accounting, and deterministic no-rerender replay | not verified - requires authorized host run | No run bundle exists; no GPU/host render was attempted. |

## nd_contract
status: delivered

### evidence
- Head/PR: ba466011d7a8cf372ee5711a5e07e4ce5a7717ce / https://github.com/jmanhype/wangp-dspy/pull/163.
- Scoped tests: 24 passed; full tests: 1,700 passed, 1 skipped; exact-head GitHub test check succeeded.
- Build: one wheel and one sdist; hashes recorded above.
- Real-process normal/failure/queue/reconstruction evidence: /tmp/wd-6tox-evidence-ba46601.

### proof
- [x] AC #1: Real CLI normalization covers every named family/preset/operation, LoRA, overlap, and all three long-form controls with deterministic JSON and exit 0.
- [x] AC #2: Real temporary durable queue records one immutable pending job per clip without host submission or host contact.
- [x] AC #3: Every unsupported or incomplete request class fails typed exit 2 with remediation/next command and no partial queue.
- [x] AC #4: Recipe-seed reconstruction reproduces all canonical backend-settings hashes with no hidden mutation.
- [x] AC #5: Every family/operation capability row remains planned and generation claims remain gated on recorded run bundles.

## History
- 2026-09-22T20:24:45Z dep_added: blocks WD-fasw
- 2026-09-22T20:24:45Z dep_added: blocks WD-tkuz
- 2026-09-22T20:24:46Z dep_added: blocks WD-8ioj
- 2026-09-22T20:24:46Z dep_added: blocks WD-eq1i
- 2026-09-22T20:27:36Z dep_added: blocks WD-gc09
- 2026-09-22T21:44:01Z status: open -> in_progress
- 2026-09-22T21:44:01Z claimed by dev-WD-6tox
- 2026-09-22T22:32:52Z status: in_progress -> in_progress

## Links
- Parent: [[WD-t741]]
- Blocks: [[WD-fasw]], [[WD-tkuz]], [[WD-8ioj]], [[WD-eq1i]], [[WD-gc09]]

## Comments
