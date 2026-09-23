# Finishing capability planning

`wgp finish` is a deterministic, typed, no-GPU planning surface for post-generation interpolation, spatial upsampling, film grain, codec selection, and tracked-face refinement. A successful plan proves request shape, source-byte identity, deterministic staging, and queue-record integrity only. It does not prove that a finished media file was generated or measured.

## Request contract

A request uses `wangp-dspy.finishing-request/v1`. The immutable source declaration carries its SHA-256, a declared-and-unverified ffprobe video stream, and `immutable=true`. Interpolation is limited to `x2`, `x3`, or `x4`, with a target frame rate exactly matching the declared source rate. Spatial upsampling uses the same factors; the `real_esrgan` backend additionally requires an immutable model hash. Film grain carries bounded strength, size, and temporal persistence.

Tracked-face refinement declares one or more tracks with normalized bounds, temporal bounds, confidence, provenance, license, and consent. A request with multiple tracks must name exactly one `selected_track`; out-of-bounds time or geometry is rejected. Every output path is new, has no overwrite flag, and records `planned_ffprobe_unverified` rather than a measurement.

The optional neural path may be declared only with `authorized_host=null` and `support_status=unavailable_without_authorized_host`. The no-GPU compiler then emits the typed `FINISH_NEURAL_PATH_UNAVAILABLE` rejection; it never silently falls back to another backend.

## Backends and codecs

| Backend | Interpolation | Spatial upscale | Film grain | Face refinement |
| --- | --- | --- | --- | --- |
| ffmpeg | planned | planned | planned | planned |
| rife | planned | unsupported | unsupported | unsupported |
| real_esrgan | unsupported | planned | unsupported | unsupported |
| film | unsupported | unsupported | planned | unsupported |
| neural_frame_gen | planned | planned | unsupported | planned |

Container/codec pairs are typed and fail closed: MP4 accepts H.264, HEVC, or AV1; MOV accepts H.264 or ProRes; MKV accepts H.264, HEVC, VP9, or AV1; and WebM accepts VP9. Final graph arguments are recorded per codec, including pixel format, but are never executed by this surface.

## Commands

```bash
wgp finish plan --request finishing.json --dry-run --json
wgp finish plan --request finishing.json --db run/finishing-plan.db --json
wgp finish plan --db run/finishing-plan.db --reconstruct --json
wgp finish probe --request finishing.json --json
```

`wgp finish run --request finishing.json --json` always returns typed exit 2 with `FINISH_EXECUTION_UNAUTHORIZED`. This slice performs no render, no GPU work, no host contact, no model download, and no mutation of renderer, queue, QC, AV-gate, or retry semantics.

Durable plans use only `finishing_plan_records`; the executable `jobs` table is absent. Update and delete triggers reject mutation. Records carry `plan_only=true`, `executable=false`, `queue_submitted=false`, `host_contact=false`, `media_generated=false`, and `measurement_status=unverified`. The governed admission path selects none of these records while a genuine render job remains admissible. Reconstruction reopens the exact source, rebuilds the command graph and per-backend settings from the frozen recipe, and reports all three hash comparisons plus `hidden_mutation`.

## Capability status

All rows above remain `planned`. Finished outputs, before/after ffprobe measurements, neural execution, identity-preserving face refinement, and visual quality are **not verified - requires authorized host run**. A future generation claim requires a separately authorized bundle recording operator authorization, command, repository commit, model/asset provenance, queue attempt, output hashes, objective ffprobe/QC evidence, and reviewer decision.
