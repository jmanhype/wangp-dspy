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
updated_at: 2026-09-22T20:28:47Z
content_hash: "sha256:2d51cf88ddf32684baa8bb9e1c2fde1cac41572507c3f1864209a37a2a894be6"
blocks: [WD-fasw, WD-eq1i, WD-gc09]
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
- wangp/music_cli.py -> `wgp music plan|compile|style|compare` command implementation and submit boundary
- docs/music-capabilities.md -> score schema, models, 48 kHz stereo acceptance, adaptation policy, and comparison contract
- tests/test_music_capabilities.py -> real-process score/queue/reconstruction coverage; no mocks
- datasets/runs/maestro-parity/WD-soa4/ -> authorized audio bundles including before/after style adaptation

CONSUMES:
- predict/audio_manifest.py -> typed audio metadata contract
  spec: typed audio metadata contract
- predict/audio_prep.py -> existing audio preparation behavior
  spec: existing audio preparation behavior
- services/jobs/queue.py -> durable queue record and attempt transitions
  spec: durable queue record and attempt transitions
- services/jobs/preflight.py -> typed missing model/reference failures
  spec: typed missing model/reference failures
- host/render_host.py -> authorized host execution and artifact retrieval
  spec: authorized host execution and artifact retrieval
- qc/audio_critic/profiles.py -> existing music profile provenance
  spec: existing music profile provenance
- wangp/cli.py -> stable verb registration and exit-code contract
  spec: stable verb registration and exit-code contract


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
- 2026-09-22T20:24:45Z dep_added: blocks WD-fasw
- 2026-09-22T20:24:47Z dep_added: blocks WD-eq1i
- 2026-09-22T20:27:37Z dep_added: blocks WD-gc09

## Links
- Parent: [[WD-t741]]
- Blocks: [[WD-fasw]], [[WD-eq1i]], [[WD-gc09]]

## Comments
