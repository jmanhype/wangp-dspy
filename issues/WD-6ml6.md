---
id: WD-6ml6
title: "Speech, reference voice cloning, portable character voices, and a second TTS engine"
status: open
priority: 2
type: feature
labels: [capability]
parent: WD-t741
created_at: 2026-09-22T20:24:44Z
created_by: speed
updated_at: 2026-09-22T20:26:21Z
content_hash: "sha256:47710f8fd7d8a02520f3014afd08a60b7a6077f613cc5cc2128cf721c7933d54"
blocks: [WD-fasw, WD-tkuz, WD-eq1i]
---

## Description
## USER INTENT
Observable outcome: Wangp can generate speech, clone a voice from one or two references, split longer scripts by real segment limits and assemble them, use a second independent TTS engine, and save portable character voices.

## Context (Embedded)
- The governed repository path is plan -> durable queue -> host render -> QC gates -> assembly -> provenance/recipe; `wgp` is the stable CLI and GPU execution is never implied by planning.
- Existing VibeVoice work under `predict/` and accepted speech/AV gates is the primary lane; this story turns it into a broad, portable `wgp` voice capability and adds a genuinely independent fallback engine.
- A saved character voice is a portable manifest plus consent/provenance constraints, not an opaque host path.
- Segment assembly must preserve speaker identity, ordering, silence boundaries, hashes, and downstream AV synchronization.

## OUT OF SCOPE
- Cloning a real person without recorded authorization/consent or using unrelated reference files smuggled into a worker.
- Treating a TTS vendor alias as the required second engine; the fallback must be independently implemented and separately run.

## DIFF BUDGET
Roughly 10 files, under 800 authored changed LOC, excluding voices, weights, and audio.

## Boundary Map
PRODUCES:
- predict/speech_capabilities.py -> typed speech request with text/language/style, zero/one/two references, segment policy, TTS engine, and target voice package
- services/voice/segment_compiler.py -> deterministic segment splitting at real engine limits plus ordered assembly plan
- host/speech_backends.py -> primary and independent secondary TTS adapters with fail-closed model/reference checks
- predict/voice_registry.py -> portable character-voice packages containing manifest, hashes, reference roles, consent/licence constraints, and compatibility profile
- wangp/voice_cli.py -> `wgp voice plan|generate|clone|export|import` command implementation and submit boundary
- docs/voice-capabilities.md -> engine matrix, segment limits, cloning consent, portability format, and evidence policy
- tests/test_voice_capabilities.py -> real-process voice/queue/package coverage; no mocks
- datasets/runs/maestro-parity/WD-6ml6/ -> authorized speech/clone run bundles

CONSUMES:
CONSUMES:
- predict/vibevoice.py -> purpose
  spec: existing primary speech generation seam
- predict/audio_prep.py -> purpose
  spec: existing audio preparation behavior
- predict/speaker_manifest.py -> purpose
  spec: speaker identity contract
- predict/content_brief.py -> purpose
  spec: typed character/dialogue contract
- services/jobs/queue.py -> purpose
  spec: durable queue record and attempt transitions
- services/jobs/preflight.py -> purpose
  spec: typed missing voice/model failures
- qc/audio_critic/whisper_gate.py -> purpose
  spec: real transcript evidence boundary
- qc/audio_critic/av_sync_gate.py -> purpose
  spec: real AV synchronization evidence boundary
- wangp/cli.py -> purpose
  spec: stable verb registration and exit-code contract


## Required Outcomes
### no-GPU verifiable now
- Real CLI tests normalize plain speech and one/two-reference cloning, reject missing consent or wrong reference count/format, split scripts using each engine’s declared limit, and emit an exact assembly order without synthesis.
- Portable voice export/import round-trips through a real temporary directory and verifies manifest/hashes; imported paths are namespace-safe and do not expose operator secrets.
- A real temporary queue stores text hash, segment map, engine, voice package hash, and output target; malformed text, over-limit single segments, and missing voices produce typed exit-2 failures before host contact.
- Dry-run reconstruction reproduces all segments and engine settings; docs mark synthesis and secondary-engine output unverified until runs exist.

### requires an authorized host render
- Separately authorized host runs synthesize plain speech on both engines, one-reference and two-reference clones, and one over-limit script whose real segments are assembled in order.
- Bundles retain authorization/consent provenance, references, commands, queue attempts, output hashes, ffprobe metadata, transcript evidence, and portable package linkage.

## Testing Requirements
- `uv run --frozen --extra dev pytest tests/test_voice_capabilities.py -q` with real files/CLI/queue and no mocks.
- Use real reference audio fixtures and deliberately exceed one declared segment limit to test actual typed splitting.
- Authorized speech bundles are verified by ffprobe, hashes, and existing transcript tooling; no synthetic audio is committed to pass tests.

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
Observable outcome: Wangp can generate speech, clone a voice from one or two references, split longer scripts by real segment limits and assemble them, use a second independent TTS engine, and save portable character voices.

## Context (Embedded)
- The governed repository path is plan -> durable queue -> host render -> QC gates -> assembly -> provenance/recipe; `wgp` is the stable CLI and GPU execution is never implied by planning.
- Existing VibeVoice work under `predict/` and accepted speech/AV gates is the primary lane; this story turns it into a broad, portable `wgp` voice capability and adds a genuinely independent fallback engine.
- A saved character voice is a portable manifest plus consent/provenance constraints, not an opaque host path.
- Segment assembly must preserve speaker identity, ordering, silence boundaries, hashes, and downstream AV synchronization.

## OUT OF SCOPE
- Cloning a real person without recorded authorization/consent or using unrelated reference files smuggled into a worker.
- Treating a TTS vendor alias as the required second engine; the fallback must be independently implemented and separately run.

## DIFF BUDGET
Roughly 10 files, under 800 authored changed LOC, excluding voices, weights, and audio.

## Boundary Map
PRODUCES:
- predict/speech_capabilities.py -> typed speech request with text/language/style, zero/one/two references, segment policy, TTS engine, and target voice package
- services/voice/segment_compiler.py -> deterministic segment splitting at real engine limits plus ordered assembly plan
- host/speech_backends.py -> primary and independent secondary TTS adapters with fail-closed model/reference checks
- predict/voice_registry.py -> portable character-voice packages containing manifest, hashes, reference roles, consent/licence constraints, and compatibility profile
- wangp/cli.py -> `wgp voice plan|generate|clone|export|import` no-GPU verbs and explicit submit boundary
- docs/voice-capabilities.md -> engine matrix, segment limits, cloning consent, portability format, and evidence policy
- datasets/runs/maestro-parity/<story-id>/ -> authorized speech/clone run bundles

CONSUMES:
- predict/vibevoice.py and predict/audio_prep.py -> existing speech/audio preparation seams
- predict/speaker_manifest.py and predict/content_brief.py -> speaker identity and typed brief contracts
- services/jobs/queue.py and services/jobs/preflight.py -> durable queue and typed preflight
- qc/audio_critic/whisper_gate.py and qc/audio_critic/av_sync_gate.py -> real downstream speech/AV evidence patterns

## Required Outcomes
### no-GPU verifiable now
- Real CLI tests normalize plain speech and one/two-reference cloning, reject missing consent or wrong reference count/format, split scripts using each engine’s declared limit, and emit an exact assembly order without synthesis.
- Portable voice export/import round-trips through a real temporary directory and verifies manifest/hashes; imported paths are namespace-safe and do not expose operator secrets.
- A real temporary queue stores text hash, segment map, engine, voice package hash, and output target; malformed text, over-limit single segments, and missing voices produce typed exit-2 failures before host contact.
- Dry-run reconstruction reproduces all segments and engine settings; docs mark synthesis and secondary-engine output unverified until runs exist.

### requires an authorized host render
- Separately authorized host runs synthesize plain speech on both engines, one-reference and two-reference clones, and one over-limit script whose real segments are assembled in order.
- Bundles retain authorization/consent provenance, references, commands, queue attempts, output hashes, ffprobe metadata, transcript evidence, and portable package linkage.

## Testing Requirements
- `uv run --frozen --extra dev pytest tests/test_voice_capabilities.py -q` with real files/CLI/queue and no mocks.
- Use real reference audio fixtures and deliberately exceed one declared segment limit to test actual typed splitting.
- Authorized speech bundles are verified by ffprobe, hashes, and existing transcript tooling; no synthetic audio is committed to pass tests.

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
- 2026-09-22T20:24:47Z dep_added: blocks WD-eq1i

## Links
- Parent: [[WD-t741]]
- Blocks: [[WD-fasw]], [[WD-tkuz]], [[WD-eq1i]]

## Comments
