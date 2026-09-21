# Spend-gate replay (preregistered)

- Decision: **insufficient_data**
- Primary result: **infeasible_at_budget**
- Rows: 36 total / 18 complete / 5 bad
- The complete-row sample is underpowered; no production model is warranted by this run.

| Baseline | Admitted | Abstained | False admit | Avoided/run | Bootstrap 95% CI |
|---|---:|---:|---:|---:|---:|
| always_admit | 18 | 0 | 0.278 | undefined | [0.000, 0.000] |
| deterministic_preflight | 0 | 0 | undefined | undefined | undefined |
| transparent_heuristic | 18 | 0 | 0.278 | undefined | [0.000, 0.000] |
| calibrated_model | 0 | 13 | undefined | undefined | undefined |

## Raw versus calibrated model

| Policy | Coverage | Correct | Incorrect | Brier | Log loss |
|---|---:|---:|---:|---:|---:|
| raw | 18/18 | 8 | 10 | 0.444 | 15.351 |
| calibrated | 5/18 | 4 | 1 | 0.254 | 0.736 |

Clipped probability rows: raw 18, calibrated 0 (clip epsilon 1e-15).

## Deterministic preflight decisions and reasons

The first baseline replays the production preflight invariants. A rejection means the recorded
run contradicts its own plan, not that the render was artistically bad.

| Reason | Rows |
|---|---:|
| delivered_resolution_contradicts_envelope | 18 |

## Explicit limits

- N=36 total rows and 18 complete rows; this replay is underpowered.
- Calibration produced no feasible policy: this is a negative calibration result.
- Threshold sweeps are exploratory and did not select the primary result.
- Queue joins are partial; unmatched attempt counts are explicitly unavailable.
- Plate-facing sidecars are absent for every recorded row, so the facing sub-check is unevaluated in replay; production falls back to the character's declared requirement.
- Probabilities are clipped at 1e-15 for log loss; the count of clipped rows is reported per policy so a large log loss is attributable to the clip.
- The deterministic preflight rejects every complete row, and does so for a single reason: the delivered resolution contradicts the resolution recorded in the run's own plan/envelope. The envelope resolution field is therefore untrustworthy for all recorded runs; the preflight cannot be used as a usable admission baseline until that field is corrected.
- The committed corpus is all-local: 15 of its 36 rows come from source media that are not tracked by git (delivered remux.mp4 is untracked for 12 rows, 16 rows have at least one untracked artifact, 20 rows have all ten artifacts tracked). A fresh clone can REPLAY the committed corpus but cannot REBUILD it; a tracked rebuild yields 21 rows / 13 complete.
- PREREGISTRATION AMENDMENT: the transparent heuristic's duration tolerance was corrected from the frozen 1e-9 to the production 1e-6 after first results, because 1e-9 was itself a defect that rejected every recorded row. The amendment is recorded in preregistration.json `amendments`; the primary metric, decision rule, budget, seed and folds were not changed.
- The production QC seam that would emit a live row during a run is deliberately NOT implemented here: services/ must not depend on training/, and a recording hook inside the QC loop could fail a render attempt. The recording guarantee is satisfied by the standalone post-run recorder plus the indexer; the in-run seam needs its own story.

## Exploratory sensitivity only

The following sweep did not select or replace the primary metric.
