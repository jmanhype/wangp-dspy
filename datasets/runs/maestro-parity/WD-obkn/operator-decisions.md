# WD-obkn operator decisions

Recorded before any FFmpeg execution at 2026-09-26T21:01:30Z.

## Verbatim authorization and boundary instruction

The parent dispatcher transmitted this operator instruction:

> Measure corrected size-16/persistence-0.5 graph deterministically, capture typed neural boundary and missing face-input boundary, update only five finishing cells, run scoped/full relevant tests, lint, diff, release, checker where applicable; commit/push and deliver complete proof. This story is local/no SSH/no GPU/no download.

## Exact local FFmpeg run approval

- Approved: one deterministic corrected film-grain attempt plus its planned lossless-to-H.264 completion stages, followed by same-build replay for determinism.
- Repository commit: `2b4714bf45d8f9e9cccf4c5796ac21afa501ea5a`.
- Host: local `speeds-MacBook-Pro.local`, Darwin 27.0.0, arm64, macOS 27.0; no SSH.
- Executables: `/opt/homebrew/bin/ffmpeg` and `/opt/homebrew/bin/ffprobe`, FFmpeg 8.0.1.
- Working directory for the lossless stage: `datasets/runs/maestro-parity/WD-obkn/outputs/.wd_obkn_ffmpeg_film_grain_h264.finishing-b5941a325e9a`.
- Timeout: 300 seconds per process, synchronous execution only.
- Immutable source: `datasets/runs/maestro-parity/WD-r81u/inputs/source.mp4`, SHA-256 `e8b690774b0df7a73c85505ea507277d2745641b34f68c60c24855882da88859`.
- Controls: strength `12.0`, grain size `16`, temporal persistence `0.5`, recipe seed `8108`.
- Planned graph identity: `command_graph_sha256=0db6e426d6b96edf504131b657acac06d254c4540397a10dad3d4d18266d7722`.
- Approved corrected graph:
  `nullsrc=s=480x832:r=24/1,scale=ceil(iw/16):ceil(ih/16):flags=neighbor,split=2[grain_static_source][grain_temporal_source];[grain_static_source]noise=alls=12:all_seed=8108:allf=u[grain_static];[grain_temporal_source]noise=alls=12:all_seed=8108:allf=t+u[grain_temporal];[grain_static][grain_temporal]blend=all_mode=normal:all_opacity=0.5[grain_mixed];[grain_mixed]scale=iw*16:ih*16:flags=neighbor,crop=480:832[grain];[0:v][grain]blend=all_mode=addition:shortest=1[grained]`.
- Exact approved stage argv is retained in `current-head-plan.json`; no overwrite, source mutation, GPU, CUDA, SSH, network/model download, provider account, or dependency change is authorized.

## Terminal disposition decisions

1. `neural_frame_gen` / `interpolation`: terminate as `unsupported_host_implementation`. The named backend has no local named implementation; retain the typed exit-2 `FINISH_NEURAL_PATH_UNAVAILABLE` refusal and zero-hit evidence. Do not relabel FFmpeg/RIFE output and make no hardware-infeasibility claim.
2. `neural_frame_gen` / `spatial_upscale`: terminate as `unsupported_host_implementation`. The named backend has no local named implementation; retain the typed exit-2 `FINISH_NEURAL_PATH_UNAVAILABLE` refusal and zero-hit evidence. Do not relabel FFmpeg/Real-ESRGAN output and make no hardware-infeasibility claim.
3. `ffmpeg` / `face_refinement`: terminate as `unsupported_missing_required_input`. The source has no human face and no valid `FaceTrack` `track_id`, `identity_label`, source provenance, normalized bounds, detector result, rights/license, or consent reference exists. Do not synthesize identity, consent, or detection.
4. `neural_frame_gen` / `face_refinement`: terminate as `unsupported_missing_required_input` under the same missing-face/missing-provenance/missing-consent boundary; this is not a hardware verdict.

Only the five cells named by WD-obkn may transition. The four already verified cells and all other matrix dispositions remain unchanged.
