---
id: WD-tc04
title: "adapter: seam-aware frame tolerance + SshHost completion-by-outputs robustness"
status: closed
priority: 2
type: task
labels: [bug, delivered, accepted]
created_at: 2026-08-23T14:56:26Z
created_by: speed
updated_at: 2026-08-23T15:16:42Z
content_hash: "sha256:d9cddd4c06d51894271096eee1022f0073847103a93a885fc4e24e5aff023c55"
closed_at: 2026-08-23T15:16:42Z
close_reason: "PR #14 merged (ae6303f): seam-scaled tolerance with MEASURED_SEAM_FRAMES provenance, ssh keepalives at the _ssh_base seam, exactly-one fetch retry; Luna+Qwen PASS, 145 tests green"
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
- 2026-08-23T15:16:42Z status: in_progress -> closed

## Links


## Comments
