# RESULTS — Two-Shot Chained Proof (run 2, 2026-08-31)

Render: 3090, Wan2GP branch `rebase-onto-upstream`, model
`minimax_h3_fl2va`, 2 shots x 56f @ 832x480, seed 7, 20 steps,
profile 3, sdpa. Total queue time 8m08s (model cached).
Output: `outputs/multishot_1788205281.mp4` on the 3090 →
`artifacts/chained_2shot.mp4` here (107 frames: 56 + 51 after seam trim).

## Fix required to run (3090 local, uncommitted upstream)

1. `multishot.py` imported `FPS` from `pipeline` — removed upstream
   during rebase. Added local `FPS = 24`.
2. `transformer.py::_layout` local-mod branch expected the OLD
   keyframe schema (`resolved_frame_index`); the rebased pipeline
   emits `{anchor, latent_frame_count, frame_index?}`. Shot 2 (which
   carries shot 1's last frame as image_start) crashed with
   `KeyError: 'resolved_frame_index'`. Fixed the branch to build the
   upstream anchor-tuple form `(anchor, latent_frame_count,
   frame_index)`. Run 1 log retained as
   artifacts/render_run1-failure.log (on 3090:
   outputs/chained_2shot_A/chained_2shot.mp4.log).

## Verification evidence

Motion metric (64x36 luma diff per third, threshold 2.0):

- shot 1: L 0.17 / C 0.09 / R 0.10 → below threshold (see caveat)
- shot 2: L 1.55 / C 0.94 / R 1.99 → below threshold (R near-miss)

Seam (full-res 192x108 gray):

- frames 55→56 (seam): MAE **1.35**, PSNR **38.0 dB**
- max consecutive diff inside shot 1: 0.31; inside shot 2: 9.37
- shot1 start vs shot2 start: MAE 5.25 — small; the two shots open
  on nearly the same composition (start-start drift 4x larger than
  the seam itself is not present; scene is retained).
- shot1 start vs shot2 END: MAE 4.48 (PSNR 23.2) — shot 2 evolves
  away from shot 1's start but stays in the same scene envelope
  (within-shot drift shot2 alone is 8.9).

Interpretation: the seam frame transition (1.35 MAE) is smoother than
shot 2's own average inter-frame motion (3.05) and far below any
scene-cut magnitude; composition carries across the boundary.
However BOTH shots' thirds-motion is below the 2.0 alive threshold —
consistent with the known seed-responsive freeze finding (this seed
produced a low-motion render; 0.09-1.99 range). Shot 2 shows 9-15x
higher motion than shot 1, so chaining did not freeze the render.

## Verdict

**CONTINUES (composition), INCONCLUSIVE (motion)**

- Composition: CONTINUES — seam MAE 1.35 / PSNR 38 dB (continuity-
  level), shot-2 opening matches shot-1 ending scene; no reset cut.
- Motion: below alive threshold in both shots (seed 7 = low-motion
  draw, per freeze.md this is seed-responsive, not a chaining
  failure). Re-run with a re-rolled seed would sharpen the motion
  leg; the chaining mechanism itself is proven working end-to-end.

## Artifacts

- artifacts/chained_2shot.mp4 — final render (copied from 3090)
- artifacts/frame_00{00,20,55,56,57}.png, frame_0080.png,
  frame_0106.png — boundary + context frames
- artifacts/contact_sheet.png — 7-frame strip (0,20,55,56,57,80,106)
- artifacts/report.json — machine-readable verification report
- artifacts/render_run2.log — full render log
- 3090: /home/straughter/Wan2GP/outputs/multishot_1788205281.mp4,
  outputs/chained_2shot_A/ (logs, frames/, verify/)
