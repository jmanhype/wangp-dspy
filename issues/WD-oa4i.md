---
id: WD-oa4i
title: "Dataset expansion: 22 refusal-screened labeled examples from real Pipeline.forward 3090 runs"
status: in_progress
priority: 2
type: task
parent: WD-j9nx
created_at: 2026-08-26T04:26:29Z
created_by: speed
updated_at: 2026-08-26T04:50:14Z
content_hash: "sha256:9f1517d2da63561dc2d42cf6174641efbf8a5df48f63f8a6f5a3e28b7d63cc60"
assignee: dev-WD-oa4i
follows: [WD-txt9]
---

## Description
Bank 22 new labeled examples from real Pipeline.forward 3090 runs, each retaining brief, profile decision, rendered video, typed QC verdict, and replayable evidence under datasets/runs/. Grows the bank from 9 to 31 examples, yielding 21 train / 10 validation under the existing 70/30 loader (metrics/qc_feedback.py). Explicitly NO GEPA run in this story.

Acceptance criteria:
(a) dataset manifest with source run, intent, QC score, provenance, curation status for all 31; (b) dedup + no train/val leakage incl. duplicate briefs; (c) independent held-out validation set; (d) baseline eval recorded before any future GEPA; (e) no GPU render during optimization

## Acceptance Criteria


## Design


## Notes


## History
- 2026-08-26T04:50:14Z status: open -> in_progress
- 2026-08-26T04:50:14Z auto-follows: linked to predecessor WD-txt9
- 2026-08-26T04:50:14Z claimed by dev-WD-oa4i

## Links
- Parent: [[WD-j9nx]]
- Follows: [[WD-txt9]]

## Comments
