---
id: WD-fasw
title: "Sound effects, revoice, and audio refinement with video held fixed"
status: open
priority: 2
type: feature
labels: [capability]
parent: WD-t741
created_at: 2026-09-22T20:24:44Z
created_by: speed
updated_at: 2026-09-22T20:24:44Z
content_hash: "sha256:c1b55fee108e2e11fe056bf4b1aa54a2fbcba1e71174c3c4eff2ed58234ffef4"
blocked_by: [WD-6ml6, WD-soa4]
---

## Description
## USER INTENT
Observable outcome: Wangp can generate sound effects, revoice an existing clip while preserving its visual track, and run an audio-refinement pass that leaves video bytes fixed.

## Context (Embedded)
- The governed repository path is plan -> durable queue -> host render -> QC gates -> assembly -> provenance/recipe; `wgp` is the stable CLI and GPU execution is never implied by planning.
- This is a distinct audio-post lane: it consumes generated or committed media and must make byte-level before/after claims only with hashes and ffprobe evidence.
- Maestro’s H3 Audio Refinement belongs to the video-backend matrix; this story owns generic post-generation revoice/refinement and proves the video-fixed invariant independently.

## OUT OF SCOPE
- Changing visual encoding, cropping, frame rate, or QC decisions under the name of audio refinement.
- Replacing a failed speech generation with an unrecorded manual edit.

## DIFF BUDGET
Roughly 8 files, under 600 authored changed LOC, excluding models and media.

## Boundary Map
PRODUCES:
- predict/audio_post.py -> typed sound-effect, revoice, and refinement requests with source hashes and target stream/layout
- services/audio/post_compiler.py -> deterministic post jobs and video-fixed output naming
- host/audio_post_backends.py -> fail-closed SFX/revoice/refinement adapters
- predict/assembler.py additions or a narrowly scoped peer -> real stream replacement/mixing path with hash accounting
- wangp/cli.py -> `wgp audio sfx|revoice|refine` planning and authorized execution boundary
- docs/audio-post.md -> source/output contract, video-fixed proof, and sound-effect evidence matrix
- datasets/runs/maestro-parity/<story-id>/ -> authorized SFX/revoice/refinement bundles

CONSUMES:
- predict/audio_dataplane.py, predict/audio_manifest.py, and predict/audio_prep.py -> existing audio routing/metadata seams
- predict/speech_capabilities.py -> authorized voice/revoice engine selection
- services/jobs/queue.py and services/jobs/preflight.py -> durable queue and typed preflight
- qc/audio_critic/ -> transcript and stream-level evidence patterns

## Required Outcomes
### no-GPU verifiable now
- Real CLI tests compile SFX, revoice, and refinement requests from committed media hashes and reject absent/ambiguous streams, mismatched duration, missing voice, or invalid target layout before any host call.
- The plan explicitly marks the source video hash as immutable and names the intended output path; a real queue record preserves that invariant.
- Dry-run reconstruction reproduces command graph and source hashes; no generated audio or improved quality is claimed.

### requires an authorized host render
- Separately authorized runs generate a requested sound effect, revoice a real existing clip, and refine its audio while producing a before/after video hash showing the visual stream is byte-for-byte unchanged where the operation promises that invariant.
- Each bundle records model provenance, command, queue attempt, output hashes, ffprobe stream/layout/duration, and relevant transcript/audio gate evidence.

## Testing Requirements
- `uv run --frozen --extra dev pytest tests/test_audio_post.py -q`, real CLI/filesystem/queue only, no mocks.
- Use committed media and real ffprobe/hash inspection; corrupt one hash to prove fail-closed behavior.
- Authorized post bundles must be checked with ffprobe and source/output hashes before any matrix status becomes verified.

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
- 2026-09-22T20:24:45Z dep_added: blocked_by WD-6ml6
- 2026-09-22T20:24:45Z dep_added: blocked_by WD-soa4

## Links
- Parent: [[WD-t741]]
- Blocked by: [[WD-6ml6]], [[WD-soa4]]

## Comments
