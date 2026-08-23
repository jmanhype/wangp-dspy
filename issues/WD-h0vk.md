---
id: WD-h0vk
title: "renderer-locality: remote-GPU runner support"
status: closed
priority: 2
type: feature
parent: WD-j9nx
created_at: 2026-08-22T23:20:40Z
created_by: speed
updated_at: 2026-08-23T03:22:15Z
content_hash: "sha256:c0b52f3c2d999414f81c087bcf21e1c63fedbcd6448f0a71201227c17c6b3de2"
assignee: dev-WD-h0vk
follows: [WD-d3b9, WD-5zti]
labels: [accepted]
closed_at: 2026-08-23T03:22:13Z
close_reason: "Renderer-locality: RenderHost seam (LocalHost/SshHost), remote render via ssh+rsync, remote-side timeout kill, escape guards. Merged PR #10 (f00c70b) + PR #11 (50e1065, four live-T0 fixes + GLM guard). Live acceptance: 96f render through SshHost green, keeper mtime +384s in window. Qwen design PASS."
---

## Description
Dogfood finding (story 6 / WD-t6i7).

_check_venv (os.path.isfile/X_OK), the settings.json write, and the readback scan all assume the Wan2GP checkout is on the LOCAL filesystem. When the GPU box is remote (3090), the dogfood had to bend the runner; paths validated locally do not exist remotely and vice versa.

Fix: introduce a renderer-locality seam — e.g. a path-mapping layer (local path <-> remote path) or an explicit remote mode where settings write, venv check, and readback go through the runner/ssh transport. Keep the current local behavior default; RED tests with a fake transport first.

## Acceptance Criteria


## Design


## Notes


## nd_contract
status: accepted

### evidence
- PM closeout applied via pvg story accept on 2026-08-22.

### proof
- [x] Story closed after accepted label was applied.


## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-08-22.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## History
- 2026-08-23T03:22:04Z status: open -> in_progress
- 2026-08-23T03:22:04Z auto-follows: linked to predecessor WD-d3b9
- 2026-08-23T03:22:04Z claimed by dev-WD-h0vk
- 2026-08-23T03:22:05Z status: in_progress -> in_progress
- 2026-08-23T03:22:05Z auto-follows: linked to predecessor WD-5zti
- 2026-08-23T03:22:13Z status: in_progress -> closed

## Links
- Parent: [[WD-j9nx]]
- Follows: [[WD-d3b9]], [[WD-5zti]]

## Comments
