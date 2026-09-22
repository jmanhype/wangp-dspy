---
id: WD-8ioj
title: "Finishing: interpolation, spatial upsampling, grain, codecs, tracked-face refinement, and optional neural path"
status: open
priority: 2
type: feature
labels: [capability]
parent: WD-t741
created_at: 2026-09-22T20:24:44Z
created_by: speed
updated_at: 2026-09-22T20:28:48Z
content_hash: "sha256:9d7551c970dc66e2bc7ef24af3f4b20da855f784aacbecbb99f587269e5e688a"
blocked_by: [WD-6tox, WD-tkuz]
blocks: [WD-gc09]
---

## Description

## USER INTENT
Observable outcome: after generation, Wangp can finish media with x2/x3/x4 interpolation, spatial upsampling, film grain, codec selection, tracked-face refinement, and an optional neural rendering/frame-generation path on supported hardware.

## Context (Embedded)
- The governed repository path is plan -> durable queue -> host render -> QC gates -> assembly -> provenance/recipe; `wgp` is the stable CLI and GPU execution is never implied by planning.
- Finishing is a post-processing graph over immutable source artifacts and must retain exact source/output hashes and measured ffprobe properties.
- The optional neural path is hardware-conditional: unsupported VRAM/backend profiles must produce a typed unavailable result, not fallback silently.
- Maestro’s video upscale operation is coordinated with the video story; this story owns post-generation spatial and temporal finishing semantics.

## OUT OF SCOPE
- Changing accepted render bytes in place or replacing historical evidence.
- A quality claim without declared objective measurements and, where applicable, visual review evidence.

## DIFF BUDGET
Roughly 10 files, under 800 authored changed LOC, excluding models and media.

## Boundary Map
PRODUCES:
- predict/finishing.py -> typed finishing request for interpolation x2/x3/x4, spatial scale, grain, codec, face refinement, and optional neural path
- services/finishing/pipeline.py -> deterministic command graph, stream contracts, and staged output naming
- predict/face_tracking.py -> tracked-face metadata and refinement regions
- wangp/finish_cli.py -> `wgp finish plan|run|probe` command implementation and authorized execution boundary
- docs/finishing.md -> supported operation matrix, codec constraints, hardware profile, and before/after evidence contract
- tests/test_finishing.py -> real-process finishing graph/queue coverage; no mocks
- datasets/runs/maestro-parity/WD-8ioj/ -> finishing run bundles

CONSUMES:
- predict/assembler.py -> existing assembly contract
  spec: existing assembly contract
- predict/v3_recipe.py -> immutable recipe/provenance fields
  spec: immutable recipe/provenance fields
- predict/lf002_canary.py -> real ffprobe measurement patterns
  spec: real ffprobe measurement patterns
- predict/video_capabilities.py -> backend and upscale capability metadata
  spec: backend and upscale capability metadata
- predict/character_packages.py -> character appearance/identity metadata
  spec: character appearance/identity metadata
- services/jobs/queue.py -> durable queue record and attempt transitions
  spec: durable queue record and attempt transitions
- services/jobs/preflight.py -> typed unsupported profile/codec failures
  spec: typed unsupported profile/codec failures
- wangp/cli.py -> stable verb registration and exit-code contract
  spec: stable verb registration and exit-code contract


## Required Outcomes
### no-GPU verifiable now
- Real CLI tests compile each interpolation factor, scale, grain setting, codec, face track, and neural profile into deterministic command graphs; unsupported codecs/profiles fail typed.
- A committed media fixture can exercise deterministic local finishing graph validation and source-hash immutability without claiming GPU neural support.
- A real temporary queue preserves the source hash and target stream contract; missing source, ambiguous face track, unsupported factor/codec, or inadequate profile fails before host work.
- Dry-run reconstruction reproduces the command graph exactly from queue/recipe.

### requires an authorized host render
- Separately authorized runs produce real finished outputs for x2/x3/x4 interpolation, spatial upsampling, film grain, at least two codec targets, and tracked-face refinement, each with before/after ffprobe and hashes.
- On an authorized supported host, run the optional neural rendering/frame-generation path; on an unsupported host, retain the typed unavailability evidence instead of implying success.

## Testing Requirements
- `uv run --frozen --extra dev pytest tests/test_finishing.py -q`, real CLI/files/queue/ffprobe processes with no mocks.
- Assert real exit codes for supported and unsupported graphs and verify accepted source artifacts remain unchanged.
- Authorized finishing bundles require actual ffprobe measurements, hashes, and gate/reviewer evidence; no GPU claim may come from a command graph.

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
- 2026-09-22T20:24:46Z dep_added: blocked_by WD-6tox
- 2026-09-22T20:24:46Z dep_added: blocked_by WD-tkuz
- 2026-09-22T20:26:48Z dep_added: blocks WD-gc09

## Links
- Parent: [[WD-t741]]
- Blocks: [[WD-gc09]]
- Blocked by: [[WD-6tox]], [[WD-tkuz]]

## Comments
