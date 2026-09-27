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
| minimax_h3/standard | host_run_verified ([WD-2gyw evidence](../datasets/runs/maestro-parity/WD-2gyw/evidence.json)) | host_run_verified ([WD-isg9 evidence](../datasets/runs/maestro-parity/WD-isg9/evidence.json)) | unsupported ([WD-isg9 host boundary](../datasets/runs/maestro-parity/WD-isg9/host-logs/blend-probe.render.log)) | host_run_verified ([WD-isg9 evidence](../datasets/runs/maestro-parity/WD-isg9/evidence.json)) | host_run_verified ([WD-isg9 evidence](../datasets/runs/maestro-parity/WD-isg9/evidence.json)) | unsupported ([WD-isg9 host boundary](../datasets/runs/maestro-parity/WD-isg9/boundary-code-evidence.txt)) | host_run_verified ([WD-isg9 evidence](../datasets/runs/maestro-parity/WD-isg9/evidence.json)) | unsupported ([WD-isg9 host boundary](../datasets/runs/maestro-parity/WD-isg9/host-logs/recast-probe.render.log)) | host_run_verified ([WD-isg9 evidence](../datasets/runs/maestro-parity/WD-isg9/evidence.json)) |
| minimax_h3/h3_vdn_hybrid_attention | host_run_verified ([WD-2gyw evidence](../datasets/runs/maestro-parity/WD-2gyw/evidence.json)) | unsupported ([WD-9t9o host boundary](../datasets/runs/maestro-parity/WD-9t9o/host-logs/extend.render.log)) | unsupported ([WD-9t9o host boundary](../datasets/runs/maestro-parity/WD-9t9o/host-logs/blend-probe.render.log)) | unsupported ([WD-9t9o host boundary](../datasets/runs/maestro-parity/WD-9t9o/host-logs/retake.render.log)) | host_run_verified ([WD-9t9o evidence](../datasets/runs/maestro-parity/WD-9t9o/evidence.json)) | unsupported ([WD-9t9o host boundary](../datasets/runs/maestro-parity/WD-9t9o/boundary-code-evidence.txt)) | host_run_verified ([WD-9t9o evidence](../datasets/runs/maestro-parity/WD-9t9o/evidence.json)) | unsupported ([WD-9t9o host boundary](../datasets/runs/maestro-parity/WD-9t9o/host-logs/recast-probe.render.log)) | host_run_verified ([WD-9t9o evidence](../datasets/runs/maestro-parity/WD-9t9o/evidence.json)) |
| minimax_h3/taomate_three_step | unsupported ([WD-43tj host boundary](../datasets/runs/maestro-parity/WD-43tj/taomate-boundary.md)) | unsupported ([WD-43tj host boundary](../datasets/runs/maestro-parity/WD-43tj/taomate-boundary.md)) | unsupported ([WD-43tj host boundary](../datasets/runs/maestro-parity/WD-43tj/taomate-boundary.md)) | unsupported ([WD-43tj host boundary](../datasets/runs/maestro-parity/WD-43tj/taomate-boundary.md)) | unsupported ([WD-43tj host boundary](../datasets/runs/maestro-parity/WD-43tj/taomate-boundary.md)) | unsupported ([WD-43tj host boundary](../datasets/runs/maestro-parity/WD-43tj/taomate-boundary.md)) | unsupported ([WD-43tj host boundary](../datasets/runs/maestro-parity/WD-43tj/taomate-boundary.md)) | unsupported ([WD-43tj host boundary](../datasets/runs/maestro-parity/WD-43tj/taomate-boundary.md)) | unsupported ([WD-43tj host boundary](../datasets/runs/maestro-parity/WD-43tj/taomate-boundary.md)) |
| minimax_h3/kfi_frames_injection | unsupported ([WD-m25k host boundary](../datasets/runs/maestro-parity/WD-m25k/boundary-evidence.json)) | unsupported ([WD-m25k host boundary](../datasets/runs/maestro-parity/WD-m25k/boundary-evidence.json)) | unsupported ([WD-m25k host boundary](../datasets/runs/maestro-parity/WD-m25k/boundary-evidence.json)) | host_run_verified ([WD-2gyw evidence](../datasets/runs/maestro-parity/WD-2gyw/evidence.json)) | unsupported ([WD-m25k host boundary](../datasets/runs/maestro-parity/WD-m25k/boundary-evidence.json)) | unsupported ([WD-m25k host boundary](../datasets/runs/maestro-parity/WD-m25k/boundary-evidence.json)) | host_run_verified ([WD-m25k evidence](../datasets/runs/maestro-parity/WD-m25k/evidence.json)) | unsupported ([WD-m25k host boundary](../datasets/runs/maestro-parity/WD-m25k/boundary-evidence.json)) | host_run_verified ([WD-m25k evidence](../datasets/runs/maestro-parity/WD-m25k/evidence.json)) |
| minimax_h3/h3_outpaint | unsupported ([WD-5k28 host boundary](../datasets/runs/maestro-parity/WD-5k28/h3-outpaint-boundary.md)) | unsupported ([WD-5k28 host boundary](../datasets/runs/maestro-parity/WD-5k28/h3-outpaint-boundary.md)) | unsupported ([WD-5k28 host boundary](../datasets/runs/maestro-parity/WD-5k28/h3-outpaint-boundary.md)) | unsupported ([WD-5k28 host boundary](../datasets/runs/maestro-parity/WD-5k28/h3-outpaint-boundary.md)) | unsupported ([WD-5k28 host boundary](../datasets/runs/maestro-parity/WD-5k28/h3-outpaint-boundary.md)) | unsupported ([WD-5k28 host boundary](../datasets/runs/maestro-parity/WD-5k28/h3-outpaint-boundary.md)) | unsupported ([WD-5k28 host boundary](../datasets/runs/maestro-parity/WD-5k28/h3-outpaint-boundary.md)) | unsupported ([WD-5k28 host boundary](../datasets/runs/maestro-parity/WD-5k28/h3-outpaint-boundary.md)) | unsupported ([WD-5k28 host boundary](../datasets/runs/maestro-parity/WD-5k28/h3-outpaint-boundary.md)) |
| minimax_h3/h3_audio_refinement | unsupported ([WD-m25k host boundary](../datasets/runs/maestro-parity/WD-m25k/boundary-evidence.json)) | unsupported ([WD-m25k host boundary](../datasets/runs/maestro-parity/WD-m25k/boundary-evidence.json)) | unsupported ([WD-m25k host boundary](../datasets/runs/maestro-parity/WD-m25k/boundary-evidence.json)) | unsupported ([WD-m25k host boundary](../datasets/runs/maestro-parity/WD-m25k/boundary-evidence.json)) | host_run_verified ([WD-2gyw evidence](../datasets/runs/maestro-parity/WD-2gyw/evidence.json)) | unsupported ([WD-m25k host boundary](../datasets/runs/maestro-parity/WD-m25k/boundary-evidence.json)) | host_run_verified ([WD-m25k evidence](../datasets/runs/maestro-parity/WD-m25k/evidence.json)) | unsupported ([WD-m25k host boundary](../datasets/runs/maestro-parity/WD-m25k/boundary-evidence.json)) | host_run_verified ([WD-m25k evidence](../datasets/runs/maestro-parity/WD-m25k/evidence.json)) |
| ltx/2.5 | host_run_verified ([WD-m7xw evidence](../datasets/runs/maestro-parity/WD-m7xw/evidence.json)) | host_run_verified ([WD-m7xw evidence](../datasets/runs/maestro-parity/WD-m7xw/evidence.json)) | unsupported ([typed backend](../datasets/runs/maestro-parity/WD-2gyw/planning/boundaries/ltx-2.5-blend.result.json)) | host_run_verified ([WD-m7xw evidence](../datasets/runs/maestro-parity/WD-m7xw/evidence.json)) | host_run_verified ([WD-m7xw evidence](../datasets/runs/maestro-parity/WD-m7xw/evidence.json)) | dependency_blocked ([WD-m7xw dependency boundary](../datasets/runs/maestro-parity/WD-m7xw/dependency-boundaries.md)) | dependency_blocked ([WD-m7xw dependency boundary](../datasets/runs/maestro-parity/WD-m7xw/dependency-boundaries.md)) | dependency_blocked ([WD-m7xw dependency boundary](../datasets/runs/maestro-parity/WD-m7xw/dependency-boundaries.md)) | dependency_blocked ([WD-m7xw dependency boundary](../datasets/runs/maestro-parity/WD-m7xw/dependency-boundaries.md)) |
| ltx/2.3 | planned | planned | planned | planned | planned | planned | planned | planned | planned |
| scail/2 | host_run_verified ([WD-ycjg evidence](../datasets/runs/maestro-parity/WD-ycjg/evidence.json)) | unsupported ([WD-ycjg host boundary](../datasets/runs/maestro-parity/WD-ycjg/boundary-evidence.json)) | host_run_verified ([WD-ycjg evidence](../datasets/runs/maestro-parity/WD-ycjg/evidence.json)) | host_run_verified ([WD-ycjg evidence](../datasets/runs/maestro-parity/WD-ycjg/evidence.json)) | host_run_verified ([WD-ycjg evidence](../datasets/runs/maestro-parity/WD-ycjg/evidence.json)) | unsupported ([typed backend](../datasets/runs/maestro-parity/WD-2gyw/planning/boundaries/scail-2-outpaint.result.json)) | host_run_verified ([WD-ycjg evidence](../datasets/runs/maestro-parity/WD-ycjg/evidence.json)) | host_run_verified ([WD-ycjg evidence](../datasets/runs/maestro-parity/WD-ycjg/evidence.json)) | unsupported ([typed backend](../datasets/runs/maestro-parity/WD-2gyw/planning/boundaries/scail-2-upscale.result.json)) |
| wan/2gp | planned | planned | planned | planned | planned | planned | planned | planned | planned |
| hunyuan/standard | host_run_verified ([WD-2gyw evidence](../datasets/runs/maestro-parity/WD-2gyw/evidence.json)) | host_run_verified ([WD-8h6p evidence](../datasets/runs/maestro-parity/WD-8h6p/evidence.json)) | unsupported ([WD-8h6p host boundary](../datasets/runs/maestro-parity/WD-8h6p/boundary-evidence.json)) | host_run_verified ([WD-8h6p evidence](../datasets/runs/maestro-parity/WD-8h6p/evidence.json)) | host_run_verified ([WD-8h6p evidence](../datasets/runs/maestro-parity/WD-8h6p/evidence.json)) | unsupported ([typed backend](../datasets/runs/maestro-parity/WD-2gyw/planning/boundaries/hunyuan-standard-outpaint.result.json)) | host_run_verified ([WD-8h6p evidence](../datasets/runs/maestro-parity/WD-8h6p/evidence.json)) | host_run_verified ([WD-8h6p evidence](../datasets/runs/maestro-parity/WD-8h6p/evidence.json)) | host_run_verified ([WD-8h6p evidence](../datasets/runs/maestro-parity/WD-8h6p/evidence.json)) |

Current typed planning rejects these family/operation pairs exactly as recorded above: LTX blend; SCAIL outpaint and upscale; Hunyuan outpaint. Those are fail-closed backend/operation boundaries, not claims that Maestro lacks the vendor feature and not hardware verdicts. Likewise, `planned` does not claim Wangp has rendered the pair.

The thirty-three `host_run_verified` cells above are bound to real hashed MP4s: five in the authorized [WD-2gyw bundle](../datasets/runs/maestro-parity/WD-2gyw/evidence.json) (H3 standard create, H3 VDN hybrid-attention create with Sol-Attn enabled on SM86, H3 KFI frame-injection retake, H3 audio-refinement edit, and Hunyuan 1.5 standard create); H3 standard extend, retake, edit, repaint, and upscale in [WD-isg9](../datasets/runs/maestro-parity/WD-isg9/evidence.json); H3 VDN edit, repaint, and upscale in [WD-9t9o](../datasets/runs/maestro-parity/WD-9t9o/evidence.json); LTX-2.5 create, extend, retake, and edit in [WD-m7xw](../datasets/runs/maestro-parity/WD-m7xw/evidence.json); H3 KFI repaint/upscale plus H3 audio-refinement repaint/upscale in [WD-m25k](../datasets/runs/maestro-parity/WD-m25k/evidence.json); Hunyuan extend, retake, edit, repaint, recast, and upscale in [WD-8h6p](../datasets/runs/maestro-parity/WD-8h6p/evidence.json); and SCAIL-2 create, blend, retake, edit, repaint, and recast in [WD-ycjg](../datasets/runs/maestro-parity/WD-ycjg/evidence.json). Other cells in those rows are terminal boundaries and must not inherit another operation's evidence. The original authorized LTX-2.5 int8 attempt is recorded in [`ltx25.failure.log`](../datasets/runs/maestro-parity/WD-2gyw/ltx25.failure.log): model loading reached the Gemma4 tokenizer, then failed with `TypeError: 'tokenizers.pre_tokenizers.Split' object does not support item assignment`; that dependency failure is not hardware infeasibility. WD-m7xw later deployed the accepted tokenizer fix and recorded exact no-download `dependency_blocked` boundaries for LTX-2.5 outpaint, repaint, recast, and upscale because their required LoRA assets are absent; those cells are not hardware or capability verdicts. FL2VA-standard blend and recast are terminal host implementation boundaries from the WD-isg9 runtime probes. WD-m25k adds exact FL2VA boundaries for KFI create/extend/blend/edit/outpaint/recast and audio-refinement create/extend/blend/retake/outpaint/recast: KFI requires a reference and currently fails on `resolved_frame_index`, audio refinement requires a control video, FL2VA blend lacks `reference_video_max_frames`, recast requires Ref2VA, and audio outpaint did not enlarge the 480x832 source. WD-8h6p records the analogous Hunyuan two-guide blend boundary (`reference_video_max_frames` absent); its other six operations have real hashed outputs. WD-ycjg records an exact SCAIL-2 extension boundary: a 21-frame request returned the nine-frame/0.375-second control length and was nearly identical to its source at 46.593200 dB PSNR; its other six operations have real hashed outputs. VDN extend and retake are terminal WD-9t9o host boundaries because required visual conditioning under the Sol path fails in SageAttention before denoising; all nine TaoMate cells are terminal WD-43tj implementation boundaries because neither active host tree implements the named preset; all nine cells in the separate H3 Outpaint preset row are terminal WD-5k28 implementation boundaries because the named preset has no active runtime identity and its distinguishing control is disabled. LTX-2.3 and Wan remain planned for the reasons recorded in [`row-dispositions.json`](../datasets/runs/maestro-parity/WD-2gyw/row-dispositions.json).

## Authorized-render boundary

The following remain gated and are explicitly unclaimed by the planning surface itself: endpoint smoke evidence for families without an authorized evidence bundle, TaoMate three-step, H3 Outpaint, long-form multi-clip execution, per-clip prompt/overlap execution, exact duration/window execution, deterministic no-rerender replay, and QC/assembly/provenance artifacts beyond the cited evidence bundles. Each new host batch requires separate operator authorization. The deterministic `wgp video` planner still performs no GPU, SSH, model download, paid-provider, or host-mutation work.
