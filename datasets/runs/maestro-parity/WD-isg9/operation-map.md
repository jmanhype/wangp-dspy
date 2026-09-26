# WD-isg9 operation map

The canonical source is WD-2gyw `wd_2gyw_h3_standard.mp4`, SHA-256
`e8b690774b0df7a73c85505ea507277d2745641b34f68c60c24855882da88859`. Its first
frame is SHA-256
`888e32c332c922616d39f802383d66a3de8733d7bb54d5aacdb6a03560bd638b`.

| Operation | Native control | Terminal rule |
| --- | --- | --- |
| extend | `image_prompt_type=V`, `video_source`, `video_prompt_type=T`, overlap 18 | real output must be longer than the source |
| retake | `image_prompt_type=S`, accepted first frame, fresh seed | distinct first-frame-anchored output |
| edit | `video_prompt_type=GV`, control video, `audio_prompt_type=K`, denoise 0.45 | real video-to-video output |
| repaint | `video_prompt_type=GVA`, control video, mask video, audio K, masking 0.5 | real masked video-to-video output |
| upscale | WanGP `edit_postprocessing`, `spatial_upsampling=lanczos2` | measured 960x1664 output |
| blend | two-reference-video probe on FL2VA standard | terminal unsupported only from the captured runtime diagnostic |
| recast | contextual-reference probe on FL2VA standard | terminal unsupported only from the captured runtime diagnostic |
| outpaint | FL2VA standard control inventory | terminal unsupported only from the exact implementation boundary; do not execute a generic GV edit and rename it outpaint |

The repository planner remains intentionally no-GPU. Native settings below are
the audited bridge from the typed operation to the real host controls; they do
not change `predict/video_capabilities.py`.
