---
id: WD-e4nt
title: "cycle 3: 3-shot multishot MV chain through SshHost (assembler lane first remote run)"
status: closed
priority: 2
type: task
labels: [dogfood, delivered, accepted]
created_at: 2026-08-23T04:20:17Z
created_by: speed
updated_at: 2026-08-23T04:43:48Z
content_hash: "sha256:b3e0165db4f1e3e0b7ba1cc33b5e0f865517c299eba43e83339373285aa04cd9"
assignee: dev-WD-e4nt
closed_at: 2026-08-23T04:43:48Z
close_reason: "cycle 3: first 3-shot multishot through SshHost green (558s, 7.29s video, mtime in window); three real constraints mapped; all through plugin ops with evidence"
---

## Description
First multishot chain through the remote path: 3 shots x 480f (20s cap), last-frame chaining, keeper remux. Exercises assembler + multishot lane on SshHost which has only seen single 96f smokes.

## Acceptance Criteria


## Design


## Notes


## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-08-22.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## History
- 2026-08-23T04:21:03Z status: open -> in_progress
- 2026-08-23T04:21:03Z claimed by dev-WD-e4nt
- 2026-08-23T04:43:45Z status: in_progress -> in_progress
- 2026-08-23T04:43:48Z status: in_progress -> closed

## Links


## Comments
