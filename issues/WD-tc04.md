---
id: WD-tc04
title: "adapter: seam-aware frame tolerance + SshHost completion-by-outputs robustness"
status: open
priority: 2
type: task
labels: [bug]
created_at: 2026-08-23T14:56:26Z
created_by: speed
updated_at: 2026-08-23T14:56:26Z
content_hash: "sha256:db14cb71afc62bbdbd5067f05fd29e1958b7de494ea9c65ad6522666aae3cc55"
---

## Description
Two live findings from WD-izly payoff render: (1) frame tolerance is flat 2f but concat seam-trim costs ~2f per seam — measured 474 expected vs 470 actual (3 shots, 2 seams); make READBACK_FRAME_TOLERANCE scale with shot count, e.g. 2 + 2*(n_briefs-1). (2) local harness hung after remote wgp finished (ssh channel died silently, rsync pull never fired, process wedged ~25min); SshHost should detect remote completion via outputs-scan/mtime rather than trusting the ssh channel alone — or at minimum the adapter must recover when the ssh child exits without output.

## Acceptance Criteria


## Design


## Notes


## History


## Links


## Comments
