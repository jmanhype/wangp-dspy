# WD-8h6p operation plan

| Operation | Native plan | Expected terminal outcome |
| --- | --- | --- |
| extend | accepted Hunyuan source as video continuation control | exact host boundary if T2V runtime rejects source conditioning |
| blend | two accepted sources as guide controls | exact host boundary if two-guide blending is absent |
| retake | extracted first frame as start image | exact host boundary if I2V conditioning is absent |
| edit | accepted source as guide with denoise control | exact host boundary if guide editing is absent |
| repaint | accepted source plus existing mask | exact host boundary if mask editing is absent |
| recast | existing reference image | exact host boundary if reference recast is absent |
| upscale | deterministic postprocessing with `lanczos2` | real hashed output |

The accepted WD-2gyw Hunyuan create output is the sole source video. Its first frame is extracted locally with ffmpeg and hashed before execution.
