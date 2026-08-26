---
id: WD-txt9
title: "j9nx-4: metrics/ + GEPA optimization pass (baseline first, compile-once artifacts)"
status: closed
priority: 2
type: task
labels: [optimization, gepa]
parent: WD-j9nx
created_at: 2026-08-24T14:55:11Z
created_by: speed
updated_at: 2026-08-25T00:20:54Z
content_hash: "sha256:6e667bd1a676802a4d3e00f82b9fd48254dea869785b46208a8aeb0543c18be7"
assignee: jmanhype-glm
follows: [WD-mhr2]
closed_at: 2026-08-25T00:20:54Z
close_reason: "Prescription fully executed: baseline recorded, GEPA compiled (948s, full loop), side-by-side verified, plateau documented with evidence. Cost gate stop. Unlock for improvement: scale dataset."
led_to: [WD-n0ab, WD-oa4i]
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
- 2026-08-25T00:20:54Z status: in_progress -> closed

## Links
- Parent: [[WD-j9nx]]
- Follows: [[WD-mhr2]]
- Led to: [[WD-n0ab]], [[WD-oa4i]]

## Comments

### 2026-08-25T00:20:54Z speed
GEPA pass complete per prescription: baseline 0.372 -> gepa 0.372, documented plateau (AC #4 admits this). Artifacts in compiled/. Root insight: 3-example valset saturates the metric — LabeledFewShot with gold demos already reproduces craft vocabulary; discriminating GEPA improvements needs 10+ val examples. Also fixed live: gepa row-misalignment crash (4 repros) via zero-score forwards + batch padding guard. Cost gate: STOP; unlock = more renders.
