---
id: WD-d3b9
title: "wgp exit-0 on skipped task: empty readback must be WanGPError"
status: in_progress
priority: 2
type: bug
parent: WD-j9nx
created_at: 2026-08-22T23:20:39Z
created_by: speed
updated_at: 2026-08-23T03:21:38Z
content_hash: "sha256:a489988a7eccb8a6262a1abf970b96bc24f5114de41ab53497b3bf0c88443fcb"
assignee: dev-WD-d3b9
follows: [WD-5zti]
---

## Description
Dogfood finding (story 6 / WD-t6i7).

OOM/skipped renders exit with rc 0 and print 'Queue completed: 0/1 (1 skipped)' on stdout — no video is produced. The adapter's success path trusts rc 0 and returns success with empty video_paths; run_pipeline then dies later at result.video_path instead of at the render step.

Fix: empty readback after rc 0 must be a typed WanGPError (parse the 'completed: N/M (K skipped)' marker or simply fail when no video file was found). RED test first: runner rc 0, 'Queue completed: 0/1 (1 skipped)' stdout, no files -> render() raises WanGPError, not success-with-empty.

## Acceptance Criteria


## Design


## Notes


## History
- 2026-08-23T03:21:38Z status: open -> in_progress
- 2026-08-23T03:21:38Z auto-follows: linked to predecessor WD-5zti
- 2026-08-23T03:21:38Z claimed by dev-WD-d3b9

## Links
- Parent: [[WD-j9nx]]
- Follows: [[WD-5zti]]

## Comments
