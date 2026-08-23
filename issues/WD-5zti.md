---
id: WD-5zti
title: "wgp --output-dir ignored: readback must scan Wan2GP/outputs/"
status: closed
priority: 2
type: bug
parent: WD-j9nx
created_at: 2026-08-22T23:20:27Z
created_by: speed
updated_at: 2026-08-23T03:21:36Z
content_hash: "sha256:a32484e038374c6298149d20e64be0f129a6e06134cb97a61c7c0dfdf8a4fb61"
assignee: dev-WD-5zti
follows: [WD-t6i7]
labels: [accepted]
closed_at: 2026-08-23T03:21:33Z
close_reason: "wgp ignores --output-dir; adapter readback now scans the wgp outputs dir (ctor param, default <wgp_root>/outputs) with mtime filter. Merged PR #8 (46cbff4). Luna+GLM PASS; RED verified on main."
---

## Description
Dogfood finding (story 6 / WD-t6i7, PR #7 follow-up).

The adapter passes --output-dir <attempt-dir> to wgp, but wgp ignores it at this pin: renders land under Wan2GP/outputs/ regardless (only save_path in the settings json may control destination). Readback therefore returns empty video_paths even though the render succeeded.

Fix: readback must scan the actual output location (Wan2GP/outputs/ and/or the settings save_path) — RED test first: runner succeeds, no file in attempt-dir but a file in the real output location -> video_paths must find it.

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
- 2026-08-23T03:20:47Z status: open -> in_progress
- 2026-08-23T03:20:47Z auto-follows: linked to predecessor WD-t6i7
- 2026-08-23T03:20:47Z claimed by dev-WD-5zti
- 2026-08-23T03:20:50Z status: in_progress -> in_progress
- 2026-08-23T03:21:20Z status: in_progress -> in_progress
- 2026-08-23T03:21:33Z status: in_progress -> closed

## Links
- Parent: [[WD-j9nx]]
- Follows: [[WD-t6i7]]

## Comments
