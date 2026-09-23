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
| `stable_audio/sound_effect` | planned | unsupported | unsupported | none |
| `vibevoice/revoice` | unsupported | planned | unsupported | none |
| `deepfilternet/refinement` | unsupported | unsupported | planned | none |

All executable rows remain `planned` and **not verified - requires authorized host run**. A row may become `host_run_verified` only from a separately authorized bundle recording operator authorization, command, repository commit, model and reference provenance, queue attempt, exit status, output hashes, ffprobe stream/layout/duration, and applicable transcript/audio evidence, plus before/after hashes proving the unchanged video stream where promised. No such bundle exists in this slice.
