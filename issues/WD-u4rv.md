---
id: WD-u4rv
title: "adapter: frame-quantization snapping + multishot readback frame-count verification"
status: closed
priority: 2
type: task
labels: [bug, delivered]
created_at: 2026-08-23T04:54:02Z
created_by: speed
updated_at: 2026-08-23T05:10:50Z
content_hash: "sha256:13a53fcc3ab177eb7117a2261ede73a9545d0bdcd201a2bddd56c3cf23ad5d0c"
closed_at: 2026-08-23T05:10:50Z
close_reason: "PR #12 merged (63b6445): measured H3 grid 107+17k, snap-up with visible effective_frames, readback ffprobe frame verification catching the live 525-vs-172 concat-drop bug; triple-gated Qwen+Luna+GLM PASS"
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
- 2026-08-23T05:10:50Z status: in_progress -> closed

## Links


## Comments
