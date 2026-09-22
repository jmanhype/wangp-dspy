---
id: WD-soa4
title: "Music generation, ABC planning, style adaptation, and a second independent model"
status: open
priority: 2
type: feature
labels: [capability]
parent: WD-t741
created_at: 2026-09-22T20:24:44Z
created_by: speed
updated_at: 2026-09-22T20:24:44Z
content_hash: "sha256:346ee8653bcee7f4f7f2ff2c9aa6ff5cba085a01f98aa29977722571b6eed2fc"
---

## Description
## USER INTENT
Observable outcome: one governed request can plan and generate a song with melody/chord structure and ABC score, produce 48 kHz stereo output, choose an instrumental preset, adapt/train style, compare before/after audibly, and select a second independent music model.

## Context (Embedded)
- The governed repository path is plan -> durable queue -> host render -> QC gates -> assembly -> provenance/recipe; `wgp` is the stable CLI and GPU execution is never implied by planning.
- Current audio code is primarily speech/AV QC and pipeline preparation; it is not a first-class Maestro song-generation surface.
- ABC melody/chord planning can be checked deterministically without inference, but audio generation and style adaptation are host/model claims.
- Style adaptation must preserve clear provenance for training/reference inputs and must not relicense or hide upstream material.

## OUT OF SCOPE
- Redistributing source songs, stems, model weights, or generated audio without recorded upstream rights.
- Claiming 48 kHz stereo from filename or request metadata rather than measured ffprobe output.

## DIFF BUDGET
Roughly 10 files, under 800 authored changed LOC, excluding model assets and audio.

## Boundary Map
PRODUCES:
- predict/music_capabilities.py -> typed song request with lyrics/style, melody/chord plan, ABC score, instrumental preset, sample rate/channel target, model choice, and style-adaptation inputs
- services/music/song_compiler.py -> deterministic score/job records and segment/arrangement plans
- host/music_backends.py -> two independent model adapters with fail-closed manifest/provenance checks
- wangp/cli.py -> `wgp music plan|compile|style|compare` no-GPU verbs and explicit submit boundary
- docs/music-capabilities.md -> score schema, models, 48 kHz stereo acceptance, adaptation policy, and comparison contract
- datasets/runs/maestro-parity/<story-id>/ -> authorized audio bundles including before/after style adaptation

CONSUMES:
- predict/audio_manifest.py and predict/audio_prep.py -> existing typed audio metadata/preparation seams
- services/jobs/queue.py and services/jobs/preflight.py -> durable queue and typed preflight
- host/render_host.py -> authorized host execution and artifact retrieval
- qc/audio_critic/ -> existing real audio inspection patterns; no music quality claim may bypass declared gates

## Required Outcomes
### no-GPU verifiable now
- Real tests build representative ABC melody/chord plans, validate syntax and structural invariants, normalize instrumental and model selection, and emit deterministic JSON and score artifacts without inference.
- A real queue record includes score hash, arrangement, model, target `48000 Hz / 2 channels`, reference hashes, and style-adaptation mode; missing or malformed inputs fail typed.
- Dry-run reconstruction exactly reproduces score and model settings; the test explicitly asserts no audio file is created and no quality is claimed.
- Docs mark generation, second-model output, and style adaptation as planned until recorded runs exist.

### requires an authorized host render
- Separately authorized host runs generate instrumental and non-instrumental songs on each independent model, measure 48 kHz stereo with ffprobe, and retain source score/hash provenance.
- An authorized style-adaptation run records before and after audio, training/reference provenance, command/settings, and an audible A/B comparison artifact; no automatic aesthetic claim is made.

## Testing Requirements
- `uv run --frozen --extra dev pytest tests/test_music_capabilities.py -q`, real process only, no mocked ABC parser, queue, subprocess, or filesystem.
- Authorized bundles are checked with ffprobe, hashes, and real playback-candidate metadata; tests must not fabricate audio.

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


## Links
- Parent: [[WD-t741]]

## Comments
