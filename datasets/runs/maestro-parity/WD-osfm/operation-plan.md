# WD-osfm operation plan

The selected model is WanGP's native LTX-2.3 Distilled 1.0 GGUF Q4_K_M Light checkpoint, not the mismatched Comfy FP8 file.

The control asset is the accepted WD-ycjg SCAIL-2 output: a local person-bearing 384x224, nine-frame, 24 fps video with SHA-256 `1fb5689ac1647dda8ddd0806981eb0ee93a2ca641956ea3848fce65aad817a2a`.

| Operation | Native plan | Expected terminal outcome |
| --- | --- | --- |
| create | LTX-2.3 distilled text-to-video | real output or exact boundary |
| extend | generated create output as continuation source | real longer output or typed boundary |
| blend | original control plus generated output as two guides | real output or typed boundary |
| retake | extracted first frame as start image | real output or typed boundary |
| edit | control video plus edit prompt | real output or typed boundary |
| outpaint | control video plus declared margins | real output or missing-LoRA boundary |
| repaint | control video plus mask | real output or missing-LoRA boundary |
| recast | alternate reference frame | real output or missing-LoRA boundary |
| upscale | native pixel-spatial upscaler path | real output or missing-LoRA boundary |
