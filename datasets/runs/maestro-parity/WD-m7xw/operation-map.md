# WD-m7xw LTX-2.5 operation map

The create output is the sole generated reference for dependent native operations.
Its MP4 SHA-256 is
`f05bc6e13ce6e25d753c9282d931a27ae73ebca3ededd409400f28181bf6441f`; its
extracted first frame anchors retake and recast.

| Operation | Native control | Terminal result |
| --- | --- | --- |
| create | text-to-video distilled generation, seed 2941, 33 frames | exit 0, hashed MP4 |
| extend | `image_prompt_type=V`, create MP4 as `video_source`, 65 frames, overlap 9 | exit 0, 4.033 s MP4 longer than the 1.375 s source |
| retake | first frame as `image_start`, fresh seed 2943 | exit 0; first-frame SSIM versus anchor 0.988417 |
| edit | create MP4 as raw control (`video_prompt_type=VG`), audio `K`, denoise 0.65 | exit 0; whole-video PSNR versus source 38.302450 dB |
| outpaint | raw control plus `video_guide_outpainting=25 25 25 25` | exit 1 before denoising: required outpaint LoRA absent |
| repaint | raw control, generated mask, `video_prompt_type=MVGA` | exit 1 before denoising: required in/outpaint LoRA absent |
| recast | first frame as reference (`image_prompt_type=I`, `video_prompt_type=I`) | exit 1 before denoising: required ingredients LoRA absent |
| upscale | `edit_postprocessing` with native `spatial_upsampling=ltx252` | exit 1 before processing: required pixel-spatial-upscaler LoRA absent |

The ffmpeg mask generation and first-frame extraction are deterministic local
preparation, not additional LTX inference operations. Exactly eight Wan2GP
native generation/postprocessing attempts were admitted.
