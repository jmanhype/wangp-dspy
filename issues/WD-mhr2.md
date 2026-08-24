---
id: WD-mhr2
title: "j9nx-3: live 3090 e2e pipeline cycle + datasets/ (real renders become the trainset)"
status: in_progress
priority: 2
type: task
labels: [gpu, dataset]
parent: WD-j9nx
created_at: 2026-08-24T14:55:11Z
created_by: speed
updated_at: 2026-08-24T15:21:13Z
content_hash: "sha256:f05d7ce0882ade2d2535676cff81ab6490328fd9ad9e79c66f2d1d5931460881"
assignee: jmanhype-glm
follows: [WD-pt60]
---

## Description
Run the PIPELINE (j9nx-1), not the adapter alone, through a real 3090 render — WD-t6i7 proved the adapter, not the chain. Each cycle yields a labeled example (briefs, decision, video, QC verdict) stored under datasets/ per-genre (dspy-gepa-example per-task data pattern; refusal-screen per dspy-gepa-optimization skill). Budget: GEPA needs 20-100 examples; each example ~1 render (~16min/shot on 3090) — 20 examples ~5+ GPU-hours; plan cycles accordingly. Sequencing per runbook: free GPU (stop critic), render, re-serve critic. Acceptance: N>=10 refusal-screened examples in datasets/ with QC verdicts; pipeline e2e run green on 3090.

## Acceptance Criteria


## Design


## Notes


## History
- 2026-08-24T15:21:14Z status: open -> in_progress
- 2026-08-24T15:21:14Z auto-follows: linked to predecessor WD-pt60
- 2026-08-24T15:21:14Z claimed by jmanhype-glm

## Links
- Parent: [[WD-j9nx]]
- Follows: [[WD-pt60]]

## Comments
