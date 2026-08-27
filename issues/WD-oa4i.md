---
id: WD-oa4i
title: "Dataset expansion: 22 refusal-screened labeled examples from real Pipeline.forward 3090 runs"
status: closed
priority: 2
type: task
parent: WD-j9nx
created_at: 2026-08-26T04:26:29Z
created_by: speed
updated_at: 2026-08-27T16:12:52Z
content_hash: "sha256:8a702f0e6f603122b1c9aebeb186ecafb4c77c42075d384d40d0fbab28a39249"
assignee: dev-WD-oa4i
follows: [WD-txt9, WD-mhr2]
labels: [delivered, pm-accepted]
closed_at: 2026-08-27T16:12:52Z
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
2026-08-27 FINAL: Luna G1-G7 verdict = PASS (all seven gates, amendment evidenced). Dataset final: 30 kept / 4 dropped / 1 excluded, 21 train / 9 val, baseline 0.0. Cleanup nits fixed in 1b35a6e (n_kept field, newline). Story ready for delivery + PM accept.

## History
- 2026-08-26T04:50:14Z status: open -> in_progress
- 2026-08-26T04:50:14Z auto-follows: linked to predecessor WD-txt9
- 2026-08-26T04:50:14Z claimed by dev-WD-oa4i
- 2026-08-27T16:12:25Z status: in_progress -> in_progress
- 2026-08-27T16:12:25Z auto-follows: linked to predecessor WD-mhr2
- 2026-08-27T16:12:52Z status: in_progress -> closed

## Links
- Parent: [[WD-j9nx]]
- Follows: [[WD-txt9]], [[WD-mhr2]]

## Comments

### 2026-08-26T14:14:21Z speed
sol-max amendment record (2026-08-26, run-wd-yyj9-t0): Option A stands as amended — 25 new intents + 6 curated legacy = 31 unique briefs; gate (b) NO waiver (loader enforces exact-intent + normalized-subject dedup and cross-split ValueError guard). Amendment decision record: .vault/knowledge/capture-20260826T140925Z-05a49b36-f73f-4237-88df-64e5b5fcc256.md. Governance note (P3 envelope) recorded in nd-vault: knowledge/taxonomy-decision-20260826-wd-oa4i-capture-targets.md — two capture families (.vault governed captures vs nd-vault knowledge notes), writes only via vlt / run_knowledge_capture, post-write verification mandatory, .trash is staging not destination. Restored misrouted doctrine note to knowledge/ (vlt move + files verified).

### 2026-08-26T15:03:36Z speed
Design (backfilled 2026-08-26 per PH-6bhn pilot): 25-render lane architecture = run_batch_oa4i driver + local gpu_seq sequencing + Option-A key handoff; checkpoint written as per-run JSON; resume supported via --skip-done.

### 2026-08-26T15:03:36Z speed
Notes (backfilled 2026-08-26 per PH-6bhn pilot): current status — render lane relaunching after self-ssh fix; ETA ~7h. Lane is live; do not interrupt.

### 2026-08-27T15:56:52Z speed
sol-max (2026-08-27): STEP-2 curation amendment b5c8553 is now on main (merged with PR #26 cdccd7d) — cumulonimbus guard rejection evidenced, 31->30 records / 21 train - 9 val. Luna G1 blocker resolved; re-verdict pending (Luna to re-run acceptance against amended manifest).

### 2026-08-27T16:07:57Z speed
G1-G7 PASS (Luna, 2026-08-27): amendment b5c8553 + evidence verified against 3090 primary sources (log fetched over SSH, manifest recounted, loader executed, videos stat'd both hosts). Non-blocking nits fixed 1b35a6e. Verdict: deliver.

### 2026-08-27T16:12:25Z speed
PM ACCEPT (operator, 2026-08-27): G1-G7 PASS accepted. WD-oa4i delivered: 30-example dataset (21 train / 9 val), baseline 0.0, all amendments evidenced. Story closed.
