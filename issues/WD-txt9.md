---
id: WD-txt9
title: "j9nx-4: metrics/ + GEPA optimization pass (baseline first, compile-once artifacts)"
status: in_progress
priority: 2
type: task
labels: [optimization, gepa]
parent: WD-j9nx
created_at: 2026-08-24T14:55:11Z
created_by: speed
updated_at: 2026-08-24T23:47:11Z
content_hash: "sha256:0db6d1db3bdee901b12c27e166098267f9dadf057cf144761bc471fdc538e2ca"
assignee: jmanhype-glm
follows: [WD-mhr2]
---

## Description
Optimizer research verdict: GEPA (not MIPROv2) because RenderQC already emits feedback-shaped signals — GEPA reads Prediction(score, feedback) and reflects; +10% over MIPROv2, 35x fewer rollouts (arXiv 2507.19457). Deliverables: metrics/ package with qc_feedback_metric(gold, pred, trace=None, pred_name=None, pred_trace=None) — program-level returns float, predictor-level returns Prediction(score, feedback); trace toggle: continuous at eval, binarized at opt. training/run_baseline.py (LabeledFewShot honest baseline — cost gate: if it suffices, stop) then training/run_gepa.py. Pitfalls baked in (dspy-gepa-optimization skill): clear/UUID .gepa_checkpoint_*/ log dirs every run (stale-checkpoint contamination); reflection_lm = strong model; seed pinned; verify learning by side-by-side output comparison not just scores. compiled/ holds versioned program.save() artifacts — compile once, serve many. Acceptance: baseline score recorded; GEPA compile beats baseline on valset OR documented plateau with side-by-side evidence; artifact in compiled/.

## Acceptance Criteria


## Design


## Notes


## History
- 2026-08-24T23:47:11Z status: open -> in_progress
- 2026-08-24T23:47:11Z auto-follows: linked to predecessor WD-mhr2
- 2026-08-24T23:47:11Z claimed by jmanhype-glm

## Links
- Parent: [[WD-j9nx]]
- Follows: [[WD-mhr2]]

## Comments
