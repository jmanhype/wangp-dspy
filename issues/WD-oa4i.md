---
id: WD-oa4i
title: "Dataset expansion: 22 refusal-screened labeled examples from real Pipeline.forward 3090 runs"
status: open
priority: 2
type: task
parent: WD-j9nx
created_at: 2026-08-26T04:26:29Z
created_by: speed
updated_at: 2026-08-26T04:26:29Z
content_hash: "sha256:118917b1fcb1df66458e6b63a90048f759544be2dd0d3a776360dcfa55620684"
---

## Description
Bank 22 new labeled examples from real Pipeline.forward 3090 runs, each retaining brief, profile decision, rendered video, typed QC verdict, and replayable evidence under datasets/runs/. Grows the bank from 9 to 31 examples, yielding 21 train / 10 validation under the existing 70/30 loader (metrics/qc_feedback.py). Explicitly NO GEPA run in this story.

Acceptance criteria:
(a) dataset manifest with source run, intent, QC score, provenance, curation status for all 31; (b) dedup + no train/val leakage incl. duplicate briefs; (c) independent held-out validation set; (d) baseline eval recorded before any future GEPA; (e) no GPU render during optimization

## Acceptance Criteria


## Design


## Notes


## History


## Links
- Parent: [[WD-j9nx]]

## Comments
