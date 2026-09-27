# WD-28i5 operator authorization and dispatcher decision

Verbatim operator input:

> you decide

Decision:

- Selected batch: `Wan/2GP`
- Decided by: `/root` dispatcher
- Decision time: `2026-09-27T15:07:00Z`
- Rationale: accepted WD-ycjg installed every shared Wan text/VAE/CLIP helper. Only the main Wan 2.1 14B int8 checkpoint remains absent. Its exact size is `14,903,022,013` bytes; host free space is `36,303,777,792` bytes and the GPU has `23,848 MiB` free. This leaves roughly `21.4 GB`, while LTX-2.3 remains larger.

Exact scope:

- Download only `wan2.1_text2video_14B_quanto_mbf16_int8.safetensors`.
- Rehash, but do not download, the shared Wan dependencies already installed by WD-ycjg.
- Own all nine Wan/2GP cells: create, extend, blend, retake, edit, outpaint, repaint, recast, and upscale.
- Use the accepted local WD-ycjg create output as the person-bearing control/reference asset.
- Use an isolated Wan2GP worktree and mutate no live dependency or source file.
- Stop on undeclared network need, hash mismatch, insufficient disk/GPU, source mismatch, or media-gate failure.

Out of scope:

- LTX-2.3 downloads and LTX-2.5 specialized LoRA downloads.
- Any live dependency/provider mutation, training, publication, threshold change, protected-engine change, or unrelated process action.
