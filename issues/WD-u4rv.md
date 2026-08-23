---
id: WD-u4rv
title: "adapter: frame-quantization snapping + multishot readback frame-count verification"
status: in_progress
priority: 2
type: task
labels: [bug, delivered]
created_at: 2026-08-23T04:54:02Z
created_by: speed
updated_at: 2026-08-23T05:10:48Z
content_hash: "sha256:096a11bbbc6f1789d936f2e7395bca06d5e643d16254072aa20be4174e14429d"
---

## Description
Live WD-e4nt findings: (1) H3 pipeline quantizes frame_num via normalize_frame_count(n,5,17,5) — valid counts are 5+17k; adapter should snap/reject non-conforming frames_per_shot instead of silent drift (160f became 175f). (2) wgp concat stage can drop shots (3-shot render returned a 1-shot/172f video) with exit 0 — readback must verify output frame count vs expected n_shots*frames_per_shot and raise typed error on mismatch.

## Acceptance Criteria


## Design


## Notes


## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-08-23.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## History
- 2026-08-23T05:10:47Z status: open -> in_progress

## Links


## Comments
