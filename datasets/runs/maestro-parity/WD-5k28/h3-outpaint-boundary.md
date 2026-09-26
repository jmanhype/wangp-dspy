# WD-5k28 H3 outpaint host boundary

On 2026-09-26 at `2026-09-26T19:25:29Z`, a read-only inventory on host
`straughter-Z690-Steel-Legend` found no active `h3_outpaint` runtime identity:
the targeted Wan2GP/Maestro implementation search exited `1`, and no filename
matched the H3-outpaint preset.

The hashed active MiniMax H3 handler contains the control declaration as
comments:

```text
# "video_guide_outpainting": [0],
# "video_guide_outpainting_label": "Enable Spatial Outpainting on the H3 Control Video",
"outpainting_quantize_margins": 32,
```

The adjacent margin setting does not re-enable the commented control. The
handler hash is
`e5c470257bac14f49aa2d5dba2feb257d838efababa0a2e387227fedf4765ae6`; `wgp.py`
is hashed as
`28720ae526c09fa502c406c5eace16ec833fa9e026e170701245a3f8b5632907`.

A broad search found `h3_outpaint` only in the nested Wangp planner enum at
`/home/straughter/Wan2GP/wd-dmf2/repo/predict/video_capabilities.py`. That is
the same typed-planner boundary class as WD-43tj, not an active host runtime
implementation. Its SHA-256 is
`3111b78ad110493a9ba8d5c26ed1fdee0a8183f432cedd37be986495cd65d04b`.

Therefore all nine `minimax_h3/h3_outpaint` cells are `unsupported` host
implementation boundaries. Other H3 operations can render, but they cannot
proxy for this named preset while its distinguishing outpaint control is
disabled. This is not a 24-GiB hardware verdict and does not claim Maestro
lacks the vendor feature.
