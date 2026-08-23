---
id: WD-h0vk
title: "renderer-locality: remote-GPU runner support"
status: in_progress
priority: 2
type: feature
parent: WD-j9nx
created_at: 2026-08-22T23:20:40Z
created_by: speed
updated_at: 2026-08-23T03:22:04Z
content_hash: "sha256:5102918e37f6bfb3c8db0edf50a6a23fb1a5624b675f5db6ce26450f94e783a8"
assignee: dev-WD-h0vk
follows: [WD-d3b9]
---

## Description
Dogfood finding (story 6 / WD-t6i7).

_check_venv (os.path.isfile/X_OK), the settings.json write, and the readback scan all assume the Wan2GP checkout is on the LOCAL filesystem. When the GPU box is remote (3090), the dogfood had to bend the runner; paths validated locally do not exist remotely and vice versa.

Fix: introduce a renderer-locality seam — e.g. a path-mapping layer (local path <-> remote path) or an explicit remote mode where settings write, venv check, and readback go through the runner/ssh transport. Keep the current local behavior default; RED tests with a fake transport first.

## Acceptance Criteria


## Design


## Notes


## History
- 2026-08-23T03:22:04Z status: open -> in_progress
- 2026-08-23T03:22:04Z auto-follows: linked to predecessor WD-d3b9
- 2026-08-23T03:22:04Z claimed by dev-WD-h0vk

## Links
- Parent: [[WD-j9nx]]
- Follows: [[WD-d3b9]]

## Comments
