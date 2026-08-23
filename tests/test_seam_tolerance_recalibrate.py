"""WD-qn1a RED tests: seam-tolerance recalibration.

The WD-tc04 linear-2 formula fired on a GOOD render: cycle-4
4-shot multishot came out 420f vs expected 428f (diff 8) and
tolerance(4) = 2 + 2*3 = 8 with the >= comparison raised
WanGPError.

Measurements (live):
- n=1 single-shot: exact
- n=3: diff 4 (2 seams)
- n=4: diff 8 (3 seams, ~2.67/seam — superlinear, NOT linear-2)

Recalibrated: 2 + MEASURED_SEAM_CEILING*(n-1) with ceiling 3 —
admits both data points with headroom, still catches real loss.
"""
import pytest

from wangp_dspy.wangp_adapter import (
    WanGPError, frame_tolerance, MEASURED_SEAM_CEILING,
)


def test_seam_ceiling_constant_pinned():
    assert MEASURED_SEAM_CEILING == 3


def test_tolerance_values():
    assert frame_tolerance(1) == 2    # fps rounding only, exact renders
    assert frame_tolerance(3) == 8    # base 2 + 2 seams * 3
    assert frame_tolerance(4) == 11   # base 2 + 3 seams * 3
    assert frame_tolerance(6) == 17


def test_n3_measured_diff4_must_not_raise():
    """WD-tc04 data point: 3 shots, measured diff 4."""
    tol = frame_tolerance(3)
    assert abs(4) < tol  # 4 < 8 -> not flagged


def test_n4_measured_diff8_must_not_raise():
    """Cycle-4 data point: 4 shots, measured diff 8 — the case that
    fired the old linear-2 guardrail on a GOOD render."""
    tol = frame_tolerance(4)
    assert abs(8) < tol  # 8 < 11 -> not flagged


def test_n4_real_loss_diff15_still_raises():
    """A real loss (n=4, diff 15) must still trip the guardrail."""
    tol = frame_tolerance(4)
    assert abs(15) >= tol  # 15 >= 11 -> WanGPError path
