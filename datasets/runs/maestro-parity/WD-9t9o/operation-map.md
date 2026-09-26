# WD-9t9o operation map

The canonical source is WD-2gyw `wd_2gyw_h3_vdn_hybrid_attention.mp4`, SHA-256
`6becf70d98be579159b0e3ed6b212517ee78c7a1cc01906588c3ad6f0dfb8beb`. The first
frame is extracted from that exact source before rendering.

| Operation | Native control | Terminal rule |
| --- | --- | --- |
| extend | `image_prompt_type=V`, source video, overlap 18, Sol-Attn | terminal unsupported if visual prompt encoding fails under the required Sol path |
| retake | `image_prompt_type=S`, source first frame, fresh seed, Sol-Attn | terminal unsupported if visual prompt encoding fails under the required Sol path |
| edit | `GV`, source video, audio K, denoise 0.45, Sol-Attn | real video-to-video output and Sol-Attn log proof |
| repaint | `GVA`, source video, mask, audio K, masking 0.5, Sol-Attn | masked output and Sol-Attn log proof |
| upscale | WanGP `edit_postprocessing`, `lanczos2` | measured 960x1664 output |
| blend | two-reference-video probe on FL2VA VDN | unsupported only from captured runtime diagnostic |
| recast | contextual-reference probe on FL2VA VDN | unsupported only from captured runtime diagnostic |
| outpaint | FL2VA control inventory | unsupported only from exact implementation boundary |

Every generative VDN operation carries `override_attention: "sol"` and
`attention_sparsity: 1.0`. The host command uses `--attention auto` so the
settings are not overridden by SDPA. A render log lacking Sol-Attn proof cannot
promote a VDN cell.
