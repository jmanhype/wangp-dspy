# WD-isg9 execution summary

The batch used zero new model-download bytes. Live preflight passed SSH, all
four selected H3 model hashes, 61G free at the derived 24G floor, an idle RTX
3090, and CPU-only QC health at `127.0.0.1:8377`.

The original preflight command is recorded in `preflight-original-command.txt`.
The first PM review correctly observed that its JSON summarized model-file
validation as a boolean. The committed rerunnable
`host-scripts/wd_isg9_preflight_hash_probe.sh` now preserves exact `sha256sum
-c` output, all four raw hashes and sizes, mtimes that predate the render,
disk/GPU state, unrelated process state, and QC health in
`preflight-model-hash-rerun.txt`. `preflight-model-hash-summary.json` reports
4/4 hash and size matches.

Dry-run validation passed for extend, retake, edit, repaint, and upscale. The
serial render then emitted five distinct MP4s:

- extend: `outputs/extend/wd_isg9_extend.mp4`, 6.791667 s, 480x832, 24 fps,
  AAC 32 kHz stereo, SHA-256
  `489f8aae72b41b669df2259182eb287ca805ff3033d2b7ed93a130b903c00cef`.
- retake: `outputs/retake/wd_isg9_retake.mp4`, 2.333333 s, 480x832, 24 fps,
  AAC 32 kHz stereo, SHA-256
  `4a75cccc6aefe55cbf3cb65e276f9783a3430635cbbc65e140ab5d7b30dd864b`.
- edit: `outputs/edit/wd_isg9_edit.mp4`, 2.333333 s, 480x832, 24 fps, AAC
  32 kHz stereo, SHA-256
  `93acbbd1c4d432555d14135dad2648b88f19bec7a1ec40457ce6e17978158f1c`.
- repaint: `outputs/repaint/wd_isg9_repaint.mp4`, 2.333333 s, 480x832,
  24 fps, AAC 32 kHz stereo, SHA-256
  `3f14efa860a0a3564abbb4a39fcc56a380731d7f5595991639dc2cfc08fa9416`.
- upscale: `outputs/upscale/wd_isg9_upscale.mp4`, 2.334 s, 960x1664,
  24 fps, AAC 32 kHz stereo, SHA-256
  `ee703d736fc6a065b6d546d8756838fa2edd5feeebd4755d304463f33dbe505a`.

All 43 objective gates pass. Operation-specific measurements include source
prefix PSNR 47.611382 dB for extend, first-frame anchor PSNR 38.456445 dB for
retake, an edit visual-change margin of 35.548160 dB, repaint outside/inside
PSNR of 29.053942/15.754074 dB, and upscaled dimensions of 960x1664.

The FL2VA-standard blend probe loaded the real model and exited 1 with
`KeyError: 'reference_video_max_frames'`; the two-reference controls are
declared only in the Ref2VA branch. The recast probe loaded the real model and
exited 1 with `ValueError: Image, video, and audio references require the
Ref2VA checkpoint`. The FL2VA outpaint control is commented out in the hashed
host model definition. These three cells are therefore terminal host
implementation boundaries, not hardware-infeasibility claims and not generic
renders.

A first dispatcher attempt was stopped before denoising when host snapshot
paths were malformed; its remote files were quarantined and are not evidence.
The QC service started for this batch is CPU-only on port 8377. No unrelated
GPU process was killed, no model was downloaded or deleted, and no paid
provider or training run was used.

Test-output ownership: the dirty-tree release suite's two failures are its
intentional clean-tree gate checking an uncommitted evidence worktree; the
pushed PR/CI runs the suite after commit. The suite also emits the existing
FastAPI `StarletteDeprecationWarning` when importing Starlette's test client.
That warning is unrelated to WD-isg9 and is explicitly recorded here rather
than dismissed.
