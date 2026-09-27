# WD-28i5 operation plan

The control asset is the accepted WD-ycjg SCAIL-2 create output: a local person-bearing 384x224, nine-frame, 24 fps video. Its SHA-256 is `1fb5689ac1647dda8ddd0806981eb0ee93a2ca641956ea3848fce65aad817a2a`.

| Operation | Native plan | Expected terminal outcome |
| --- | --- | --- |
| create | Wan 2.1 text-to-video from a bounded prompt | real output or exact boundary |
| extend | accepted control as continuation source | real longer output or typed T2V boundary |
| blend | original control plus generated create output as two guides | real output or typed T2V boundary |
| retake | extracted first frame as start image | real output or typed T2V boundary |
| edit | accepted control as guide | real output or typed T2V boundary |
| outpaint | accepted control plus declared margins | real output or typed T2V boundary |
| repaint | accepted control plus colored mask | real output or typed T2V boundary |
| recast | extracted alternate reference image | real output or typed T2V boundary |
| upscale | deterministic `lanczos2` postprocessing of create output | real output or exact boundary |
