# WD-2gyw feasible-subset execution summary

All host operations ran synchronously with explicit local and remote timeouts.
The host began at 83 MiB GPU used / 24,034 MiB free and 106,745,708,544 bytes
free on `/`. The dispatcher-authorized download plan selected 26 LTX-2.5 and
Hunyuan-1.5 assets totalling 57,801,926,853 bytes, below the 60,000,000,000
byte lane ceiling. `aria2c` exited 0; all 26 size and SHA-256 checks passed.
Final free space was 48,921,567,232 bytes.

The lane-derived pre-download floor was 77.832239334 GiB: 53.832239334 GiB of
selected downloads + 4 GiB render/output working set + 20 GiB safety margin.
The existing preflight passed at that floor. After download, the derived floor
was 24 GiB (4 GiB working set + 20 GiB margin), and preflight passed with all
40 selected/present model files hash-verified, idle GPU, reachable QC health,
and 46G free.

Real emitted MP4s:

1. H3 standard create: `outputs/wd_2gyw_h3_standard.mp4`, 2.333333 s, 480x832, 24 fps, AAC 32 kHz stereo.
2. H3 VDN hybrid attention create: `outputs/wd_2gyw_h3_vdn_hybrid_attention.mp4`; the log records Sol-Attn enabled with Triton on SM86.
3. H3 KFI frame-injection retake: `outputs/wd_2gyw_h3_kfi_frames_injection.mp4`; first attempt used frame position `0`, was skipped as invalid, and the recorded retry used position `1`.
4. H3 audio-refinement edit: `outputs/wd_2gyw_h3_audio_refinement.mp4`; the control-video audio-generation mode emitted a new AAC track.
5. Hunyuan 1.5 standard create: `outputs/wd_2gyw_hunyuan.mp4`, 2.541667 s, 832x480, 24 fps, no audio stream.

Authorized LTX-2.5 int8 attempt: model and Gemma4 loading began, then the run
failed before generation with `TypeError: 'tokenizers.pre_tokenizers.Split'
object does not support item assignment`. The exact traceback is in
`ltx25.failure.log`. This is a host dependency failure, not hardware
infeasibility, so LTX-2.5 remains planned.

No OOM occurred. TaoMate remains planned because no implementation exists in
either host tree. H3 outpaint remains planned because the host model definition
comments out its outpaint control. LTX-2.3 remains planned because the only
local checkpoint is a hash-mismatched Comfy FP8 package. SCAIL-2 and Wan remain
planned because either main model alone exceeds the 2,198,073,147 bytes left
under the authorized 60 GB lane download ceiling. The four pre-existing typed
backend boundaries were re-captured with exit 2 diagnostics and remain distinct
from hardware verdicts.

Human review is pending. `reviewer_verdict.decision` is therefore `pending`,
and the canonical checker is expected to fail only that required approval field
at delivery.
