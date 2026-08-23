---
id: WD-tc04
title: "adapter: seam-aware frame tolerance + SshHost completion-by-outputs robustness"
status: in_progress
priority: 2
type: task
labels: [bug, delivered]
created_at: 2026-08-23T14:56:26Z
created_by: speed
updated_at: 2026-08-23T15:16:39Z
content_hash: "sha256:73285a83c934ea4d50bbbd74a6fca7c2b1c8a074b85835d90bfccb4430811810"
---

## Description
Two live findings from WD-izly payoff render: (1) frame tolerance is flat 2f but concat seam-trim costs ~2f per seam — measured 474 expected vs 470 actual (3 shots, 2 seams); make READBACK_FRAME_TOLERANCE scale with shot count, e.g. 2 + 2*(n_briefs-1). (2) local harness hung after remote wgp finished (ssh channel died silently, rsync pull never fired, process wedged ~25min); SshHost should detect remote completion via outputs-scan/mtime rather than trusting the ssh channel alone — or at minimum the adapter must recover when the ssh child exits without output.

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
- 2026-08-23T15:16:38Z status: open -> in_progress

## Links


## Comments
