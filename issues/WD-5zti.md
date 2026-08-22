---
id: WD-5zti
title: "wgp --output-dir ignored: readback must scan Wan2GP/outputs/"
status: open
priority: 2
type: bug
parent: WD-j9nx
created_at: 2026-08-22T23:20:27Z
created_by: speed
updated_at: 2026-08-22T23:20:27Z
content_hash: "sha256:2a9e5559e77aeb78b5dfaf894d85766c757ae5aa55c557bd8d75f9dbe0434a0b"
---

## Description
Dogfood finding (story 6 / WD-t6i7, PR #7 follow-up).

The adapter passes --output-dir <attempt-dir> to wgp, but wgp ignores it at this pin: renders land under Wan2GP/outputs/ regardless (only save_path in the settings json may control destination). Readback therefore returns empty video_paths even though the render succeeded.

Fix: readback must scan the actual output location (Wan2GP/outputs/ and/or the settings save_path) — RED test first: runner succeeds, no file in attempt-dir but a file in the real output location -> video_paths must find it.

## Acceptance Criteria


## Design


## Notes


## History


## Links
- Parent: [[WD-j9nx]]

## Comments
