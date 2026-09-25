# Sound effects and audio-post capability planning

`wgp sfx` is a deterministic, typed, no-GPU planning surface for sound effects, revoice, and audio refinement. A successful plan proves request shape, source bytes, target stream layout, and durable planning only; it never proves generated or improved audio.

## Contract

Requests use `wangp-dspy.audio-post-request/v1`. The planned engine slots are `stable_audio/sound_effect`, `vibevoice/revoice`, and `deepfilternet/refinement`. `--models` must record each slot's SHA-256, license and explicit acceptance, source, usage constraint, and VRAM profile. Wangp never downloads a model, contacts a host, invokes a provider, or mutates renderer or queue semantics.

Every request carries a committed source MP4 hash plus declared ffprobe video/audio streams. The source video contract is immutable and has no transformations. Sound effects require a prompt and duration no longer than the existing audio stream, output 48 kHz stereo WAV, and a new planned WAV path. Revoice requires an authorized, hash-bound target voice, output MP4, and no refinement or replacement duration. Refinement requires explicit denoise/loudness controls and output MP4. A request that crops, scales, retimes, re-encodes, or otherwise marks the held-fixed video mutable is refused with typed exit 2.

## Commands

```text
wgp sfx effect --request sfx.json --models models.json --json
wgp sfx revoice --request revoice.json --models models.json --db run/plans.db --json
wgp sfx refine --request refine.json --models models.json --db run/plans.db --json
wgp sfx plan --db run/plans.db --reconstruct --json
```

Planning validates local source and voice hashes before writing one record to `audio_post_plan_records`, never the executable `jobs` table. Update and delete triggers reject mutation. Each record has `plan_only=true`, `executable=false`, `queue_submitted=false`, and `host_contact=false`. The real admission path therefore drains none of these records while a genuine render job remains admissible.

Each immutable record carries model provenance, source/video/audio hashes and stream declarations, target voice or refinement controls, a seed-bearing command graph with an explicit `hold_video_fixed` stage, 48 kHz stereo target, planned output path, and `video_bytes_changed=false`. Reconstruction independently validates the frozen recipe, regenerates backend settings, and compares canonical SHA-256 values. Absent, empty, malformed, or edited databases fail closed with exit 2 and report hidden mutation.

## Capability matrix

| Engine / mode | Sound effect | Revoice | Refinement | Generation evidence |
| --- | --- | --- | --- | --- |
| `stable_audio/sound_effect` | unsupported_on_this_hardware ([WD-cpow measured 44.1 kHz](../datasets/runs/maestro-parity/WD-cpow/stable-audio-infeasibility.md)) | unsupported | unsupported | Real authorized attempt emitted 2.25 s stereo WAV at 44.1 kHz, not the fixed 48 kHz target |
| `vibevoice/revoice` | unsupported | planned ([WD-cpow evidence pending review](../datasets/runs/maestro-parity/WD-cpow/evidence.json)) | unsupported | Real revoice MP4, transcript gate, source/target hashes, and unchanged video-stream hash are recorded; human reviewer verdict remains pending |
| `deepfilternet/refinement` | unsupported | unsupported | planned ([WD-cpow evidence pending review](../datasets/runs/maestro-parity/WD-cpow/evidence.json)) | Real refinement MP4, 48 kHz metadata, loudness gate, audible A/B delta, and unchanged video-stream hash are recorded; human reviewer verdict remains pending |

The authorized [WD-cpow bundle](../datasets/runs/maestro-parity/WD-cpow/evidence.json) records the real Stable Audio attempt and complete VibeVoice/DeepFilterNet artifacts. Its canonical checker validates every field group except `reviewer_verdict.decision`, which correctly remains `pending`; neither successful diagonal row is promoted to `host_run_verified` before that review. Stable Audio is terminally `unsupported_on_this_hardware` because its measured native output is 44.1 kHz. A successful row may become `host_run_verified` only after reviewer approval and a checker-passing bundle recording operator authorization, command, repository commit, model and reference provenance, queue attempt, exit status, output hashes, ffprobe stream/layout/duration, and applicable transcript/audio evidence, plus before/after packet-stream hashes proving the unchanged video where promised.
