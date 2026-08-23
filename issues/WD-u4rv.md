---
id: WD-u4rv
title: "adapter: frame-quantization snapping + multishot readback frame-count verification"
status: open
priority: 2
type: task
labels: [bug]
created_at: 2026-08-23T04:54:02Z
created_by: speed
updated_at: 2026-08-23T04:54:02Z
content_hash: "sha256:6d4faad7dec1f9c8293377b9180faccbd39d81ec20061e893ac4482fa8b2ee7f"
---

## Description
Live WD-e4nt findings: (1) H3 pipeline quantizes frame_num via normalize_frame_count(n,5,17,5) — valid counts are 5+17k; adapter should snap/reject non-conforming frames_per_shot instead of silent drift (160f became 175f). (2) wgp concat stage can drop shots (3-shot render returned a 1-shot/172f video) with exit 0 — readback must verify output frame count vs expected n_shots*frames_per_shot and raise typed error on mismatch.

## Acceptance Criteria


## Design


## Notes


## History


## Links


## Comments
