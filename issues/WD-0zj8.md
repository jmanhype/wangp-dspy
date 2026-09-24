---
id: WD-0zj8
title: "Clean-machine generated install"
status: open
priority: 1
type: feature
labels: [install, evidence, external-integration]
parent: WD-3nod
created_at: 2026-09-24T14:14:09Z
created_by: speed
updated_at: 2026-09-24T14:31:09Z
content_hash: "sha256:0811cf346656495a4a560a69b9ccd4ba4b7c7db9f70ce7d543a43a55b1cf6507"
blocked_by: [WD-651z, WD-m0r5]
blocks: [WD-fay0]
---

## Description
Temporary creation body; authoritative body is installed immediately after ID assignment.

## Acceptance Criteria


## Design


## Notes
## MANDATORY SKILLS
- pvg

Observable outcome: the clean-machine check returns an install evidence bundle under datasets/runs/maestro-parity/WD-0zj8/ with command, commit, environment, and hashes, or a fail-closed blocked record; no GPU batch is authorized by this story and explicit future per-batch operator authorization remains required.

## History
- 2026-09-24T14:14:09Z dep_added: blocked_by WD-651z
- 2026-09-24T14:14:09Z dep_added: blocked_by WD-m0r5
- 2026-09-24T14:14:10Z dep_added: blocks WD-fay0

## Links
- Parent: [[WD-3nod]]
- Blocks: [[WD-fay0]]
- Blocked by: [[WD-651z]], [[WD-m0r5]]

## Comments
