# Finishing capability planning

`wgp finish` is a deterministic, typed, no-GPU planning surface for post-generation interpolation, spatial upsampling, film grain, codec selection, and tracked-face refinement. A successful plan proves request shape, source-byte identity, deterministic staging, and queue-record integrity only. It does not prove that a finished media file was generated or measured.

## Request contract

A request uses `wangp-dspy.finishing-request/v1`. The immutable source declaration carries its SHA-256, a declared-and-unverified ffprobe video stream, and `immutable=true`. Interpolation is limited to `x2`, `x3`, or `x4`, with a target frame rate exactly matching the declared source rate. Spatial upsampling uses the same factors; the `real_esrgan` backend additionally requires an immutable model hash. Film grain carries bounded strength, size, and temporal persistence.

Tracked-face refinement declares one or more tracks with normalized bounds, temporal bounds, confidence, provenance, license, and consent. A request with multiple tracks must name exactly one `selected_track`; out-of-bounds time or geometry is rejected. Every output path is new, has no overwrite flag, and records `planned_ffprobe_unverified` rather than a measurement.

The optional neural path may be declared only with `authorized_host=null` and `support_status=unavailable_without_authorized_host`. The no-GPU compiler then emits the typed `FINISH_NEURAL_PATH_UNAVAILABLE` rejection; it never silently falls back to another backend.

## Backends and codecs

| Backend | Interpolation | Spatial upscale | Film grain | Face refinement |
| --- | --- | --- | --- | --- |
| ffmpeg | host_run_verified ([WD-r81u evidence](../datasets/runs/maestro-parity/WD-r81u/evidence.json)) | host_run_verified ([WD-r81u evidence](../datasets/runs/maestro-parity/WD-r81u/evidence.json)) | host_run_verified ([WD-r81u evidence](../datasets/runs/maestro-parity/WD-r81u/evidence.json)) | planned |
| rife | host_run_verified ([WD-r81u evidence](../datasets/runs/maestro-parity/WD-r81u/evidence.json)) | unsupported | unsupported | unsupported |
| real_esrgan | unsupported | host_run_verified ([WD-r81u evidence](../datasets/runs/maestro-parity/WD-r81u/evidence.json)) | unsupported | unsupported |
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

Typed exit-2 failures cover missing or invalid requests, missing refinement operations, unsupported backend/operation pairs, invalid interpolation or spatial controls, unsupported container/codec pairs, invalid or ambiguous tracked faces, missing or hash-mismatched sources, invalid or existing outputs, unauthorized neural execution, missing or existing plan databases, and missing, empty, or damaged reconstruction records.

Durable plans use only `finishing_plan_records`; the executable `jobs` table is absent. Update and delete triggers reject mutation. Records carry `plan_only=true`, `executable=false`, `queue_submitted=false`, `host_contact=false`, `media_generated=false`, and `measurement_status=unverified`. The governed admission path selects none of these records while a genuine render job remains admissible. Reconstruction reopens the exact source, rebuilds the command graph and per-backend settings from the frozen recipe, and reports all three hash comparisons plus `hidden_mutation`.

## Capability status

The five `host_run_verified` cells above are bound to real hashed outputs in the independently approved [WD-r81u bundle](../datasets/runs/maestro-parity/WD-r81u/evidence.json): FFmpeg x2 interpolation, FFmpeg x2 spatial upscale, FFmpeg grain, RIFE x2 interpolation, and Real-ESRGAN x2 spatial upscale. Other cells in those rows do not inherit that evidence. The real film-grain output remains `planned` because its measured pixel-grain size 1 and temporal persistence 0 contradict the planned controls 16 and 0.5. Face refinement remains `planned` because the compass source has no human face and no track identity, bounds, rights, or consent was supplied. `neural_frame_gen` remains `planned` because no named host implementation exists; that absence is not hardware infeasibility. Finished neural execution, identity-preserving face refinement, and unresolved visual-quality claims therefore remain **not verified - requires authorized host run or required input**.
