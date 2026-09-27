# WD-osfm visual and objective QC

## Emitted media

- `create`: 448x832 H.264/AAC, 33 frames, 1.375 s, SHA-256 `d489d46173a3fe54e21577353ed98c76cf351610eafa0f44e279e8241a932957`. The rooftop-sunset combat premise is visible in `create-contact-sheet.jpg`; motion is present (`freeze_events=0`).
- `extend`: 448x832 H.264/AAC, 113 frames, 4.731 s, SHA-256 `28889e82b96acf6b6b2f417e4ddb8a45b23c7c642d9d38608107932de73406c3`. First-frame SSIM versus create is `0.992708`; duration increases beyond create and `freeze_events=0`.
- `retake`: 768x448 H.264/AAC, 33 frames, 1.375 s, SHA-256 `e39904befb76d409762492f8038f153af1b7a707acbc134f4c3038febf3e7769`. First-frame SSIM against the control start frame is `0.917710`; first-to-last PSNR/SSIM are `13.116967 dB` / `0.621342`, and `freeze_events=0`.
- `edit`: 768x448 H.264/AAC, 33 frames, 1.375 s, SHA-256 `8e10fafedca771f4d90b94bf6ae1fe47c64b35b517c7aa0cfa2e5f427f7bdb60`. Visual review preserves the two-fighter rooftop staging while applying the requested edit; first-to-last PSNR/SSIM are `12.089774 dB` / `0.445682`, and `freeze_events=0`.
- `repaint`: 768x448 H.264/AAC, 33 frames, 1.375 s, SHA-256 `ba9202ddf487c0ce5c139332725d19024f2aecd6b427aa39df365fb9290fd20f`. Visual review preserves the control combatants and staging while changing appearance; first-to-last PSNR/SSIM are `11.368653 dB` / `0.423649`, and `freeze_events=0`.

`all-contact-sheets.jpg` is the direct visual review plate. Low edit/repaint first-frame similarity is not treated as failure because those operations are explicitly appearance-changing; the objective gates instead require valid media, distinct hashes, motion, and the visual review plate confirming the supplied premise remains recognizable.

## Boundaries

- `blend` fails before generation on the exact host field `reference_video_max_frames`.
- `outpaint` requests undeclared `ltx-2.3-22b-ic-lora-outpaint.safetensors`; offline mode blocks it.
- `recast` requests undeclared `ltx-2.3-22b-ic-lora-ingredients-0.9.safetensors`; offline mode blocks it.
- `upscale` requests undeclared `ltx-2.3-22b-dev_diffusion_model_quanto_int8.safetensors`; offline mode blocks it.

No boundary is promoted to a hardware-infeasibility verdict.
