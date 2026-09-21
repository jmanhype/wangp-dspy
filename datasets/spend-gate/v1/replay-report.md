# Spend-gate replay (preregistered)

- Decision: **insufficient_data**
- Primary result: **infeasible_at_budget**
- Rows: 36 total / 18 complete / 5 bad
- The complete-row sample is underpowered; no production model is warranted by this run.

| Baseline | Admitted | Abstained | False admit | Avoided/run | Bootstrap 95% CI |
|---|---:|---:|---:|---:|---:|
| always_admit | 18 | 0 | 0.278 | undefined | [0.000, 0.000] |
| deterministic_preflight | 0 | 0 | undefined | undefined | undefined |
| transparent_heuristic | 0 | 0 | undefined | undefined | undefined |
| calibrated_model | 0 | 13 | undefined | undefined | undefined |

## Raw versus calibrated model

| Policy | Coverage | Correct | Incorrect | Brier | Log loss |
|---|---:|---:|---:|---:|---:|
| raw | 18/18 | 8 | 10 | 0.444 | 15.351 |
| calibrated | 5/18 | 4 | 1 | 0.254 | 0.736 |

## Explicit limits

- N=36 total rows and 18 complete rows; this replay is underpowered.
- Calibration produced no feasible policy: this is a negative calibration result.
- Threshold sweeps are exploratory and did not select the primary result.
- Queue joins are partial; unmatched attempt counts are explicitly unavailable.

## Exploratory sensitivity only

The following sweep did not select or replace the primary metric.
