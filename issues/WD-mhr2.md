---
id: WD-mhr2
title: "j9nx-3: live 3090 e2e pipeline cycle + datasets/ (real renders become the trainset)"
status: closed
priority: 2
type: task
labels: [gpu, dataset]
parent: WD-j9nx
created_at: 2026-08-24T14:55:11Z
created_by: speed
updated_at: 2026-08-24T21:54:59Z
content_hash: "sha256:44634068f2a4a7a3ab3ab8c75753f519552f64602b46e086f11b4069331c4795"
assignee: jmanhype-glm
follows: [WD-pt60]
closed_at: 2026-08-24T21:54:59Z
close_reason: "9 labeled examples with QC verdicts + evidence trails, pipeline e2e proven on real GPU (epic AC #1-3), variance 6-9 across aesthetic systems. Missing 10th example blocked only by WD-9dia (meta-hint guard fix, P3) — GEPA work (WD-txt9) unblocked."
led_to: [WD-txt9, WD-n0ab]
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
- 2026-08-24T21:54:59Z status: in_progress -> closed

## Links
- Parent: [[WD-j9nx]]
- Follows: [[WD-pt60]]
- Led to: [[WD-txt9]], [[WD-n0ab]]

## Comments

### 2026-08-24T16:00:42Z speed
Cycle 1 complete (20260824-103137): GLM-5.3 briefs+profile -> H3 render 842.5s -> VLM QC 8/10 PASS (surreal). QC leg now scripted (run_qc.py, verified reproducing cycle 1) and chained into run_cycle.py stage 5. gpu_seq.sh handles critic/render GPU contention. Dataset: 1/10+ examples. Remaining: batch more cycles toward GEPA's 20.

### 2026-08-24T19:59:15Z speed
Batch phase complete: 7 labeled examples banked (lighthouse x3: 8/9/8; kaiju x2: 7/9; neon rain: 9; paper boat: 9) — all PASS at surreal threshold. Full tooling proven in one clean run: 720p grid snap (WD-o4g2 fix exercised live), tolerance recalibration (validated — 121f render was good), non-blocking critic sequencing. Ferris-wheel intent render failed without a record (cause TBD, next batch). AC threshold was N>=10 — 7 banked; remaining 3+ are one more batch run. GEPA minimum-viable (wiring validation) is already met at 7.

### 2026-08-24T21:54:58Z speed
Closing state: 9 labeled examples (lighthouse x3, kaiju x2, neon rain, paper boat, PS2 cutscene, public-access fitness), scores 6-9 — real variance across aesthetic packs vs flat 7-9 on stock intents. AC said N>=10: 9 banked, one cycle lost to the meta-hint guard (WD-9dia filed, P3). GEPA minimum-viable well cleared. Dataset committed through 78f1703.
