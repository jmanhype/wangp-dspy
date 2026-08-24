"""WD-qwb8 RED tests: ProfileSelector — RenderBrief -> render profile.

Rules under test:
- model enum (h3 etc), resolution enum (720p|768p), shot length frames
  with HARD FLOOR 96f (=4s) — typed rejection below the floor,
- seed policy, WangP profile name (known set only),
- DummyLM only; round-trip with a REAL RenderBrief from story 1.
"""
import json

import dspy
import pytest

from prompt_director import RenderBrief
from profile_selector import (
    KNOWN_WANGP_PROFILES, ProfileDecision, ProfileSelector,
    ProfileSelectorSignature,
)

REAL_BRIEF = RenderBrief(
    subject="a lone astronaut in a cracked visor helmet",
    motion="slowly turns head left to right, dust drifting",
    camera="slow dolly in from wide to medium",
    style="16mm Ektachrome archival grain, warm faded tones",
)

GOOD_DECISION = {
    "model": "h3",
    "resolution": "768p",
    "shot_length_frames": 176,
    "seed_policy": "fixed_per_story",
    "wangp_profile": "profile3",
}


def _lm(decision):
    return dspy.utils.DummyLM([
        {"reasoning": "r", "decision": json.dumps(decision)}])


# ── 1: signature shape ───────────────────────────────────────────────────

def test_signature_takes_brief_inputs():
    for f in ("subject", "motion", "camera", "style"):
        assert f in ProfileSelectorSignature.input_fields, f


def test_signature_single_decision_output():
    assert set(ProfileSelectorSignature.output_fields) == {"decision"}


# ── 2: ProfileDecision schema (RED: does not exist yet) ─────────────────

def test_decision_constructs_with_valid_fields():
    d = ProfileDecision(**GOOD_DECISION)
    assert d.model == "h3" and d.shot_length_frames == 176


def test_decision_rejects_unknown_model():
    with pytest.raises(Exception):
        ProfileDecision(**{**GOOD_DECISION, "model": "sora"})


def test_decision_rejects_unknown_resolution():
    for bad in ("1080p", "4k", "720"):
        with pytest.raises(Exception):
            ProfileDecision(**{**GOOD_DECISION, "resolution": bad})


def test_decision_hard_floor_96_frames():
    """Below 96f (4s @ 24fps) is a typed rejection — HARD FLOOR."""
    with pytest.raises(Exception) as ei:
        ProfileDecision(**{**GOOD_DECISION, "shot_length_frames": 95})
    assert "96" in str(ei.value) or "floor" in str(ei.value).lower()


def test_decision_accepts_exactly_96_frames():
    d = ProfileDecision(**{**GOOD_DECISION, "shot_length_frames": 96})
    assert d.shot_length_frames == 96


def test_decision_rejects_bad_seed_policy():
    with pytest.raises(Exception):
        ProfileDecision(**{**GOOD_DECISION, "seed_policy": "random_each"})


def test_decision_rejects_unknown_wangp_profile():
    assert "profile3" in KNOWN_WANGP_PROFILES
    with pytest.raises(Exception):
        ProfileDecision(**{**GOOD_DECISION, "wangp_profile": "profileX"})


# ── 3: module with DummyLM ───────────────────────────────────────────────

def test_selector_returns_decision_from_real_brief():
    sel = ProfileSelector()
    with dspy.context(lm=_lm(GOOD_DECISION)):
        out = sel(subject=REAL_BRIEF.subject, motion=REAL_BRIEF.motion,
                  camera=REAL_BRIEF.camera, style=REAL_BRIEF.style)
    assert isinstance(out.decision, ProfileDecision)
    assert out.decision.wangp_profile == "profile3"


def test_selector_rejects_floor_violating_lm_output():
    poisoned = {**GOOD_DECISION, "shot_length_frames": 48}
    sel = ProfileSelector()
    with dspy.context(lm=_lm(poisoned)):
        with pytest.raises(Exception):
            sel(subject=REAL_BRIEF.subject, motion=REAL_BRIEF.motion,
                camera=REAL_BRIEF.camera, style=REAL_BRIEF.style)


def test_selector_rejects_unknown_profile_lm_output():
    poisoned = {**GOOD_DECISION, "wangp_profile": "profileX"}
    sel = ProfileSelector()
    with dspy.context(lm=_lm(poisoned)):
        with pytest.raises(Exception):
            sel(subject=REAL_BRIEF.subject, motion=REAL_BRIEF.motion,
                camera=REAL_BRIEF.camera, style=REAL_BRIEF.style)


def test_selector_rejects_non_json_output():
    sel = ProfileSelector()
    lm = dspy.utils.DummyLM(
        [{"reasoning": "r", "decision": "not json"}])
    with dspy.context(lm=lm):
        with pytest.raises(Exception):
            sel(subject="s", motion="m", camera="c", style="y")
