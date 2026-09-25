# WD-r81u execution summary

## Authorization, transfer, and disk

The dispatcher's operator authorization is preserved verbatim in `operator-authorization.md`. `doctor-capabilities-download-plan.json` planned exactly 71,567,775 bytes: RIFE v4.26 at 24,636,301 bytes and the Real-ESRGAN portable Ubuntu archive at 46,931,474 bytes. The first synchronous attempt pulled exactly those 71,567,775 bytes. It stopped on the provisional Real-ESRGAN hash mismatch recorded in `download-hash-correction.md`; the exact archive SHA-256 is `e5aa6eb131234b87c0c51f82b89390f5e3e642b7b70f2b9bbe95b6a285a40c96`.

The derived preflight floor was 16.067 GiB: 0.067 GiB transfer + 1.0 GiB bounded working set + 15 GiB safety floor. Host free space was 41,534,517,248 bytes before transfer and 41,042,083,840 bytes after the successful run.

## Real operations

The immutable source is WD-2gyw's `wd_2gyw_h3_standard.mp4`, SHA-256 `e8b690774b0df7a73c85505ea507277d2745641b34f68c60c24855882da88859`, measured at 480x832, 56 frames, 24 fps, 2.333333 seconds, with AAC 32 kHz stereo.

- FFmpeg x2 interpolation: `minterpolate` MCI/AOBMC/bidirectional/VSBMC, 24 to 48 fps, FFV1 Matroska staging, final H.264 CRF18 yuv420p MP4.
- FFmpeg x2 spatial upscale: Lanczos to 960x1664, FFV1 Matroska staging, final H.264 CRF18 yuv420p MP4.
- FFmpeg grain: `noise=alls=12:allf=t+u:all_seed=2935`; actual pixel grain size is 1 and temporal persistence is 0 (new noise each frame).
- FFmpeg codec control: direct H.264 CRF18 yuv420p MP4 transcode with faststart.
- RIFE x2 interpolation: WanGP `postprocessing.rife.inference`, v4.26 model, CUDA, 56 source frames to 111 output frames, final 48 fps H.264.
- Film grain: WanGP `postprocessing.film_grain.add_film_grain`, intensity 0.05, saturation 0.5, seed 2936; actual pixel grain size is 1 and temporal persistence is 0.
- Real-ESRGAN x2 spatial upscale: official NCNN Vulkan runtime, x4plus model pair, scale 2, tile 128, GPU 0, one load/proc/save thread, 56 input and output PNG frames, final 24 fps H.264.

The Ubuntu FFmpeg 6.1.1 host refuses FFV1 in MP4, so lossless intermediates use Matroska. Image-sequence remuxes explicitly bind input framerate. All before/after hashes and measured ffprobe metadata are in `output-hashes.txt`, `media-qc.json`, and the `ffprobe-*.json` files.

## Boundaries

`missing-required-inputs.md` records the unresolved face and neural requirements. The consumed compass source contains no face, and no track/rights/consent input exists. `neural-frame-gen-boundary-probe.txt` finds no named `neural_frame_gen` implementation in WanGP. Those cells remain planned; they are not hardware-infeasibility claims.

`reviewer_verdict` is intentionally `pending`. No capability row is flipped until independent review and a checker-passing record.
