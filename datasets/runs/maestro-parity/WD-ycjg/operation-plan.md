# WD-ycjg operation plan

The control asset is the existing operator-owned `HOL120_ssscdn_scail_r9_00001.mp4`, a 384x224, nine-frame, 24 fps person-bearing clip with embedded generation provenance. Its SHA-256 is `c71398ba3c4fe6394c83450d7cd5267187e4c65b8d9b568f9457f1a9aac03ca8`.

Local preparation:

1. Copy the control byte-identically into this story namespace.
2. Extract a reference frame.
3. Use the downloaded SAM3 Magic Mask helper with keyword `person` to derive a stable colored one-person mask video.
4. Hash the control, reference frame, and mask before and after execution.

| Operation | Native plan | Terminal outcome |
| --- | --- | --- |
| create | SCAIL-2 one-person replacement mode from control, reference, and colored mask | real output or exact boundary |
| extend | animate/continue mode using the create output as source plus control and mask | real longer output or exact boundary |
| blend | two-guide control attempt | exact boundary if SCAIL supports only one control |
| retake | same control/reference/mask with a fresh seed and retake prompt | real output or exact boundary |
| edit | generated create output as control with an edit prompt | real output or exact boundary |
| outpaint | not owned | existing typed backend boundary remains unchanged |
| repaint | replacement mode with repaint-focused prompt and colored mask | real output or exact boundary |
| recast | alternate reference frame from the control with recast prompt | real output or exact boundary |
| upscale | not owned | existing typed backend boundary remains unchanged |
