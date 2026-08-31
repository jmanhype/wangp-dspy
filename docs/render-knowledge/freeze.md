# Seed-Responsive Freeze — `verified`

**Freeze is seed-responsive, not beat-density-driven.**

Controlled A/B (2026-08-30/31): identical prompt+params, different seed
produced frozen renders (**0.11-0.39 motion/third**) vs alive renders
(**2.03-5.06 motion/third**).

- Beat-density hypothesis **REJECTED**: same frozen seed with HALF the
  beats produced identical frozen metrics — the prompt was not the
  cause.
- Fix: **motion gate + seed re-roll** on freeze detection.

## Motion metric (implemented in `gates/motion_gate.py`)

- 64x36 luma diff between consecutive frames, mean absolute diff,
  averaged per screen third (left / center / right).
- `MOTION_ALIVE_THRESHOLD = 2.0` — separates the frozen cluster
  (≤0.39) from the alive cluster (≥2.03) with wide margin.
- `alive := min(thirds) >= threshold`.

## Evidence

- CONTROLLED-SEED-AB (full numeric clusters above).
- `gates/motion_gate.py` + `tests/test_motion_gate.py` (RED-GREEN TDD,
  synthetic fixtures).
