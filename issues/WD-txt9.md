---
id: WD-txt9
title: "j9nx-4: metrics/ + GEPA optimization pass (baseline first, compile-once artifacts)"
status: open
priority: 2
type: task
labels: [optimization, gepa]
parent: WD-j9nx
created_at: 2026-08-24T14:55:11Z
created_by: speed
updated_at: 2026-08-24T14:55:11Z
content_hash: "sha256:1305b7e9ef3984a4c037c03c44d5c6879209f0baa8c491d784a2273fa37a5b2f"
---

## Description
Optimizer research verdict: GEPA (not MIPROv2) because RenderQC already emits feedback-shaped signals — GEPA reads Prediction(score, feedback) and reflects; +10% over MIPROv2, 35x fewer rollouts (arXiv 2507.19457). Deliverables: metrics/ package with qc_feedback_metric(gold, pred, trace=None, pred_name=None, pred_trace=None) — program-level returns float, predictor-level returns Prediction(score, feedback); trace toggle: continuous at eval, binarized at opt. training/run_baseline.py (LabeledFewShot honest baseline — cost gate: if it suffices, stop) then training/run_gepa.py. Pitfalls baked in (dspy-gepa-optimization skill): clear/UUID .gepa_checkpoint_*/ log dirs every run (stale-checkpoint contamination); reflection_lm = strong model; seed pinned; verify learning by side-by-side output comparison not just scores. compiled/ holds versioned program.save() artifacts — compile once, serve many. Acceptance: baseline score recorded; GEPA compile beats baseline on valset OR documented plateau with side-by-side evidence; artifact in compiled/.

## Acceptance Criteria


## Design


## Notes


## History


## Links
- Parent: [[WD-j9nx]]

## Comments
