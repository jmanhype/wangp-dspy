# WD-9t9o execution summary

The batch used zero model-download bytes. Raw live preflight evidence records
4/4 model hash and size matches, the exact VDN source hash, model mtimes, disk,
GPU, process, and QC state. Dry-run validation passed for edit, repaint, and
upscale after selecting shared-timestep mask mode; the unsupported probes were
validated as input-shaped but intentionally executed as runtime boundary probes.

Real outputs:

- edit: `outputs/edit/wd_9t9o_edit.mp4`, 2.333333 s, 480x832, 24 fps, AAC 32 kHz
  stereo, SHA-256 `2db118bcbfd8780ef0ee7d29ab842df96fc789c0e42c34f42607fd68ec762c6a`.
- repaint: `outputs/repaint/wd_9t9o_repaint.mp4`, 2.333333 s, 480x832, 24 fps,
  AAC 32 kHz stereo, SHA-256
  `6d409fb9fe367b84806f955d3788e2f0d330f37e83ab12f87e556fe3831fb0fa`.
- upscale: `outputs/upscale/wd_9t9o_upscale.mp4`, 2.334 s, 960x1664, 24 fps,
  AAC 32 kHz stereo, SHA-256
  `89a7f6cc41a8048802bce0a437fb534259e5afb95e638b26c2e8a4680effe3e0`.

Both edit and repaint logs record `[MiniMax H3] Sol-Attn enabled with Triton on
SM86`. All 39 objective gates pass.

VDN extend and retake are terminal host implementation boundaries, not hardware
verdicts. With `--attention auto` and again with `--attention sdpa`, visual
prompt encoding failed before denoising with `AssertionError: varlen only
support head_dim [64, 128]`. Removing the required VDN Sol setting might avoid
the seam but would fabricate the preset, so no such output was admitted.

The blend probe exited 1 with `KeyError: 'reference_video_max_frames'`; the
recast probe exited 1 with `ValueError: Image, video, and audio references
require the Ref2VA checkpoint`. The FL2VA outpaint control is commented out in
the hashed host implementation. Those three cells are therefore unsupported host
boundaries.

The first repaint dry-run found that grouped-row mask denoising conflicts with
Sol-Attn; the admitted repaint uses `h3_mask_mode=shared_timestep`, preserves
Sol-Attn, and still applies the mask. No model was downloaded, trained, or
deleted; no paid provider or unrelated GPU process was used.
