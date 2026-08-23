---
id: WD-5zti
title: "wgp --output-dir ignored: readback must scan Wan2GP/outputs/"
status: in_progress
priority: 2
type: bug
parent: WD-j9nx
created_at: 2026-08-22T23:20:27Z
created_by: speed
updated_at: 2026-08-23T03:20:50Z
content_hash: "sha256:3abc924ffd7f5a85dd018f1f5ac6845e137e984449d6f31f28079fff27ff104e"
assignee: dev-WD-5zti
follows: [WD-t6i7]
---

## Description
Dogfood finding (story 6 / WD-t6i7, PR #7 follow-up).

The adapter passes --output-dir <attempt-dir> to wgp, but wgp ignores it at this pin: renders land under Wan2GP/outputs/ regardless (only save_path in the settings json may control destination). Readback therefore returns empty video_paths even though the render succeeded.

Fix: readback must scan the actual output location (Wan2GP/outputs/ and/or the settings save_path) — RED test first: runner succeeds, no file in attempt-dir but a file in the real output location -> video_paths must find it.

## Acceptance Criteria


## Design


## Notes


## History
- 2026-08-23T03:20:47Z status: open -> in_progress
- 2026-08-23T03:20:47Z auto-follows: linked to predecessor WD-t6i7
- 2026-08-23T03:20:47Z claimed by dev-WD-5zti
- 2026-08-23T03:20:50Z status: in_progress -> in_progress

## Links
- Parent: [[WD-j9nx]]
- Follows: [[WD-t6i7]]

## Comments
