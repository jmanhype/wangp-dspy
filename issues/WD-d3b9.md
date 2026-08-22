---
id: WD-d3b9
title: "wgp exit-0 on skipped task: empty readback must be WanGPError"
status: open
priority: 2
type: bug
parent: WD-j9nx
created_at: 2026-08-22T23:20:39Z
created_by: speed
updated_at: 2026-08-22T23:20:39Z
content_hash: "sha256:486270fd809efb6b43f5d9298ac007c0bc4d50818536964458a50469ddf28fee"
---

## Description
Dogfood finding (story 6 / WD-t6i7).

OOM/skipped renders exit with rc 0 and print 'Queue completed: 0/1 (1 skipped)' on stdout — no video is produced. The adapter's success path trusts rc 0 and returns success with empty video_paths; run_pipeline then dies later at result.video_path instead of at the render step.

Fix: empty readback after rc 0 must be a typed WanGPError (parse the 'completed: N/M (K skipped)' marker or simply fail when no video file was found). RED test first: runner rc 0, 'Queue completed: 0/1 (1 skipped)' stdout, no files -> render() raises WanGPError, not success-with-empty.

## Acceptance Criteria


## Design


## Notes


## History


## Links
- Parent: [[WD-j9nx]]

## Comments
