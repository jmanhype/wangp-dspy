---
id: WD-d3b9
title: "wgp exit-0 on skipped task: empty readback must be WanGPError"
status: in_progress
priority: 2
type: bug
parent: WD-j9nx
created_at: 2026-08-22T23:20:39Z
created_by: speed
updated_at: 2026-08-23T03:21:42Z
content_hash: "sha256:45adf20d27b23a3bdc9fd3ef57c32d0e7682e1a62cc0388d27abbe54ab6ac126"
assignee: dev-WD-d3b9
follows: [WD-5zti, WD-t6i7]
labels: [delivered]
---

## Description
Dogfood finding (story 6 / WD-t6i7).

OOM/skipped renders exit with rc 0 and print 'Queue completed: 0/1 (1 skipped)' on stdout — no video is produced. The adapter's success path trusts rc 0 and returns success with empty video_paths; run_pipeline then dies later at result.video_path instead of at the render step.

Fix: empty readback after rc 0 must be a typed WanGPError (parse the 'completed: N/M (K skipped)' marker or simply fail when no video file was found). RED test first: runner rc 0, 'Queue completed: 0/1 (1 skipped)' stdout, no files -> render() raises WanGPError, not success-with-empty.

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
- 2026-08-23T03:21:38Z status: open -> in_progress
- 2026-08-23T03:21:38Z auto-follows: linked to predecessor WD-5zti
- 2026-08-23T03:21:38Z claimed by dev-WD-d3b9
- 2026-08-23T03:21:39Z status: in_progress -> in_progress
- 2026-08-23T03:21:39Z auto-follows: linked to predecessor WD-t6i7

## Links
- Parent: [[WD-j9nx]]
- Follows: [[WD-5zti]], [[WD-t6i7]]

## Comments
