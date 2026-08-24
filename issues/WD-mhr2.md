---
id: WD-mhr2
title: "j9nx-3: live 3090 e2e pipeline cycle + datasets/ (real renders become the trainset)"
status: open
priority: 2
type: task
labels: [gpu, dataset]
parent: WD-j9nx
created_at: 2026-08-24T14:55:11Z
created_by: speed
updated_at: 2026-08-24T14:55:11Z
content_hash: "sha256:0e5304cbc9d4a1da26b09a66bbdb1c8a37c186af91e073298c6c240b38157809"
---

## Description
Run the PIPELINE (j9nx-1), not the adapter alone, through a real 3090 render — WD-t6i7 proved the adapter, not the chain. Each cycle yields a labeled example (briefs, decision, video, QC verdict) stored under datasets/ per-genre (dspy-gepa-example per-task data pattern; refusal-screen per dspy-gepa-optimization skill). Budget: GEPA needs 20-100 examples; each example ~1 render (~16min/shot on 3090) — 20 examples ~5+ GPU-hours; plan cycles accordingly. Sequencing per runbook: free GPU (stop critic), render, re-serve critic. Acceptance: N>=10 refusal-screened examples in datasets/ with QC verdicts; pipeline e2e run green on 3090.

## Acceptance Criteria


## Design


## Notes


## History


## Links
- Parent: [[WD-j9nx]]

## Comments
