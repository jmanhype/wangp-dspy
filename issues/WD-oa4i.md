---
id: WD-oa4i
title: "Dataset expansion: 22 refusal-screened labeled examples from real Pipeline.forward 3090 runs"
status: in_progress
priority: 2
type: task
parent: WD-j9nx
created_at: 2026-08-26T04:26:29Z
created_by: speed
updated_at: 2026-08-27T15:56:52Z
content_hash: "sha256:3ccb33b69486e76ed16764b22d51835269d235394c27bf06e847f3e1f1aa81d3"
assignee: dev-WD-oa4i
follows: [WD-txt9]
---

## Description
Bank 22 new labeled examples from real Pipeline.forward 3090 runs, each retaining brief, profile decision, rendered video, typed QC verdict, and replayable evidence under datasets/runs/. Grows the bank from 9 to 31 examples, yielding 21 train / 10 validation under the existing 70/30 loader (metrics/qc_feedback.py). Explicitly NO GEPA run in this story.

Acceptance criteria:
(a) dataset manifest with source run, intent, QC score, provenance, curation status for all 31; (b) dedup + no train/val leakage incl. duplicate briefs; (c) independent held-out validation set; (d) baseline eval recorded before any future GEPA; (e) no GPU render during optimization

## Acceptance Criteria
- [ ] (a) dataset manifest with source run, intent, QC score, provenance, curation status for all 31
- [ ] (b) dedup + no train/val leakage incl. duplicate briefs
- [ ] (c) independent held-out validation set
- [ ] (d) baseline eval recorded before any future GEPA
- [ ] (e) no GPU render during optimization
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

### 2026-08-26T15:03:36Z speed
Design (backfilled 2026-08-26 per PH-6bhn pilot): 25-render lane architecture = run_batch_oa4i driver + local gpu_seq sequencing + Option-A key handoff; checkpoint written as per-run JSON; resume supported via --skip-done.

### 2026-08-26T15:03:36Z speed
Notes (backfilled 2026-08-26 per PH-6bhn pilot): current status — render lane relaunching after self-ssh fix; ETA ~7h. Lane is live; do not interrupt.

### 2026-08-27T15:56:52Z speed
sol-max (2026-08-27): STEP-2 curation amendment b5c8553 is now on main (merged with PR #26 cdccd7d) — cumulonimbus guard rejection evidenced, 31->30 records / 21 train - 9 val. Luna G1 blocker resolved; re-verdict pending (Luna to re-run acceptance against amended manifest).
