# Maestro video capability planning

`wgp video` is a deterministic, typed, no-GPU planning surface. It reuses the governed `ProfileDecision`, `WanGPJobConfig`, compile-guard, and SQLite job-queue seams. A successful plan proves request normalization and durable queue shape only; it never proves that a model generated video.

## Request schema

Requests use `wangp-dspy.video-capability-request/v1`:

```json
{
  "schema_version": "wangp-dspy.video-capability-request/v1",
  "model": {"family": "minimax_h3", "preset": "h3_vdn_hybrid_attention"},
  "operation": "extend",
  "clips": [
    {"prompt": "clip one", "duration_s": 4.0, "reference": "clip-one.mp4"},
    {"prompt": "clip two", "duration_s": 4.0, "reference": "clip-two.mp4"}
  ],
  "overlap": {"strategy": "sliding_window", "frames": 4},
  "long_form": {
    "mode": "exact_timecode",
    "exact_timecode": {"start": "00:00:00:00", "end": "00:00:07:22"}
  },
  "loras": [
    {"path": "style.safetensors", "sha256": "64-hex-digest", "weight": 0.5}
  ],
  "render": {
    "width": 480, "height": 832, "num_inference_steps": 20,
    "guidance_scale": 1.0, "embedded_guidance_scale": 6.0,
    "force_fps": "24", "profile": "profile3"
  },
  "recipe_seed": 904
}
```

The model manifest is supplied separately and must contain the matching family/preset hash, license, explicit license acceptance, and VRAM profile. Wangp never downloads the model. References are required and hash-matched for every operation except `create`; a reference supplied with `create` is intentionally ignored and is not admitted as provenance. LoRA files must be locally readable and hash-matched. Timecodes use frames `00..23`, and `force_fps` must be `24`; the current accounting contract does not silently mix another frame rate.

Named family/preset combinations are:

- MiniMax H3: `standard`, `h3_vdn_hybrid_attention`, `taomate_three_step`, `kfi_frames_injection`, `h3_outpaint`, and `h3_audio_refinement`
- LTX: `2.5` and `2.3`
- SCAIL: `2`
- Wan: `2gp`
- Hunyuan: `standard`

Operations are `create`, `extend`, `blend`, `retake`, `edit`, `outpaint`, `repaint`, `recast`, and `upscale`. All operations except `create` require a reference. The backend matrix below determines which pairs can be planned. Long form supports `one_window`, `exact_timecode`, and `window_count` controls through 3600 seconds; overlap may be `none` or an explicit `sliding_window` frame count.

## Commands

Normalize without durable state:

```text
wgp video --request request.json --models models.json --dry-run --json
```

Persist one immutable planning record per clip in a new temporary SQLite database. The records are written to `video_plan_records`, not the executable `jobs` table, so the real governed queue and worker cannot select or render them:

```text
wgp video --request request.json --models models.json --db run/jobs.db --json
```

Reconstruct settings from recorded recipe inputs:

```text
wgp video --reconstruct --db run/jobs.db --json
```

Every plan record contains immutable model hash, license, VRAM profile, model type, LoRA path/hash/weight, reference path/hash when applicable, operation, window accounting, overlap, recipe seed, normalized settings, and a SHA-256 of those settings. The persisted backend profile tag remains the established `prompt=multishot`, while `profile` is the numeric WanGP argument (`1`, `2`, or `3`). `queue_submitted=false` means no authorized render/host submission occurred. Reconstruction requires an existing, nonempty, reconstructable database; absent, empty, non-pending, or damaged records fail closed. Reconstruction regenerates settings independently and compares the canonical SHA-256; a mismatch is `hidden_mutation=true`.

## Capability matrix

Every family/operation row is `planned`. A row can become `host_run_verified` only from a separately authorized run bundle with command, repository commit, model/LoRA provenance, queue attempt, output hashes, ffprobe metadata, QC result, and assembly/recipe linkage. A normalized settings document, deterministic plan, unit test, or vendor feature list is not generation evidence.

| Family/preset | Create | Extend | Blend | Retake | Edit | Outpaint | Repaint | Recast | Upscale |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| minimax_h3/standard | planned | planned | planned | planned | planned | planned | planned | planned | planned |
| minimax_h3/h3_vdn_hybrid_attention | planned | planned | planned | planned | planned | planned | planned | planned | planned |
| minimax_h3/taomate_three_step | planned | planned | planned | planned | planned | planned | planned | planned | planned |
| minimax_h3/kfi_frames_injection | planned | planned | planned | planned | planned | planned | planned | planned | planned |
| minimax_h3/h3_outpaint | planned | planned | planned | planned | planned | planned | planned | planned | planned |
| minimax_h3/h3_audio_refinement | planned | planned | planned | planned | planned | planned | planned | planned | planned |
| ltx/2.5 | planned | planned | planned | planned | planned | planned | planned | planned | planned |
| ltx/2.3 | planned | planned | planned | planned | planned | planned | planned | planned | planned |
| scail/2 | planned | planned | planned | planned | planned | planned | planned | planned | planned |
| wan/2gp | planned | planned | planned | planned | planned | planned | planned | planned | planned |
| hunyuan/standard | planned | planned | planned | planned | planned | planned | planned | planned | planned |

Current typed planning rejects these otherwise planned family/operation pairs: LTX blend; SCAIL outpaint and upscale; Hunyuan outpaint. Those are fail-closed backend/operation boundaries, not claims that Maestro lacks the vendor feature. Likewise, `planned` does not claim Wangp has rendered the pair.

## Authorized-render boundary

The following remain gated and are explicitly unclaimed in this delivery: endpoint smoke evidence for every family and operation, H3 VDN, TaoMate three-step, KFI continuity, H3 Outpaint, H3 Audio Refinement, long-form multi-clip execution, per-clip prompt/overlap execution, exact duration/window execution, deterministic no-rerender replay, and QC/assembly/provenance artifacts. Each batch requires separate operator authorization. No GPU, SSH, model download, paid provider, or host mutation is performed by this surface.
