---
id: WD-oa4i
title: "Dataset expansion: 22 refusal-screened labeled examples from real Pipeline.forward 3090 runs"
status: in_progress
priority: 2
type: task
parent: WD-j9nx
created_at: 2026-08-26T04:26:29Z
created_by: speed
updated_at: 2026-08-26T14:14:21Z
content_hash: "sha256:632282e65940b71906365a61636902dedc71fb60ac3229a9004d740d6c113ae7"
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

### 2026-08-26T14:14:21Z speed
sol-max amendment record (2026-08-26, run-wd-yyj9-t0): Option A stands as amended — 25 new intents + 6 curated legacy = 31 unique briefs; gate (b) NO waiver (loader enforces exact-intent + normalized-subject dedup and cross-split ValueError guard). Amendment decision record: .vault/knowledge/capture-20260826T140925Z-05a49b36-f73f-4237-88df-64e5b5fcc256.md. Governance note (P3 envelope) recorded in nd-vault: knowledge/taxonomy-decision-20260826-wd-oa4i-capture-targets.md — two capture families (.vault governed captures vs nd-vault knowledge notes), writes only via vlt / run_knowledge_capture, post-write verification mandatory, .trash is staging not destination. Restored misrouted doctrine note to knowledge/ (vlt move + files verified).
