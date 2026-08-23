---
id: WD-u4rv
title: "adapter: frame-quantization snapping + multishot readback frame-count verification"
status: in_progress
priority: 2
type: task
labels: [bug]
created_at: 2026-08-23T04:54:02Z
created_by: speed
updated_at: 2026-08-23T05:10:47Z
content_hash: "sha256:a0383d9debb49d5f0e5b21a2cebde9491c3f94182723958f39f891b56356315d"
---

## Description
Live WD-e4nt findings: (1) H3 pipeline quantizes frame_num via normalize_frame_count(n,5,17,5) — valid counts are 5+17k; adapter should snap/reject non-conforming frames_per_shot instead of silent drift (160f became 175f). (2) wgp concat stage can drop shots (3-shot render returned a 1-shot/172f video) with exit 0 — readback must verify output frame count vs expected n_shots*frames_per_shot and raise typed error on mismatch.

## Acceptance Criteria


## Design


## Notes


## History
- 2026-08-23T05:10:47Z status: open -> in_progress

## Links


## Comments
