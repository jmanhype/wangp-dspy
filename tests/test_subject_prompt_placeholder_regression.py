"""Regression tests: the subject_prompt placeholder bug.

The H3-Ref2VA renderer's emitted prompt must carry the REAL spoken line
inside the <d>[English] ...</d> block, never the dialogue_ref guide key
(e.g. "d1"). Planner must bind beat text into ShotPlan.dialogue_ref so
the renderer receives real content.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from services.director.schema import (
    CameraPlan,
    CharacterProfile,
    ProductionPlan,
    ShotPlan,
)
from services.director.planners.short_film import ShortFilmPlanner
from services.director.renderers.h3_ref2va import render_shot


def _plate(tmp_path: Path, name: str) -> str:
    plate = tmp_path / name
    plate.write_bytes(b"\x89PNG-fake-plate")
    plate.with_suffix(".plate.json").write_text(json.dumps({"facing": "camera"}))
    return str(plate)


def _character(tmp_path: Path) -> CharacterProfile:
    return CharacterProfile(
        name="GRANDMA",
        description="an elderly woman with gray hair in a bun, tattered brown cloak",
        master_plate_path=_plate(tmp_path, "grandma_master.png"),
        facing_requirement="camera",
    )


def _plan(tmp_path: Path, shot: ShotPlan) -> ProductionPlan:
    return ProductionPlan(film_id="film-x", characters=(_character(tmp_path),),
                          shots=(shot,))


def _shot(tmp_path: Path, dialogue_ref: str) -> ShotPlan:
    return ShotPlan(
        index=1, speaker="GRANDMA", dialogue_ref=dialogue_ref,
        camera_plan=CameraPlan(framing="wide", movement="static",
                               lighting="bright"),
        start_image_ref=_plate(tmp_path, "grandma_master.png"),
        audio_guide_ref={"path": str(tmp_path / "line.wav"),
                         "duration_s": 107 / 24},
        duration_s=107 / 24,
    )


def test_rendered_prompt_carries_real_line_not_ref_key(tmp_path):
    # If dialogue_ref holds the raw guide key, the renderer must REJECT
    # rather than emit a placeholder-looking <d> block.
    shot = _shot(tmp_path, "d1")
    with pytest.raises(ValueError, match="dialogue_ref"):
        render_shot(_plan(tmp_path, shot), shot)


def test_rendered_prompt_binds_bound_line(tmp_path):
    shot = _shot(tmp_path, "d1: You wicked boy.")
    job = render_shot(_plan(tmp_path, shot), shot)
    assert "<d>[English] You wicked boy.</d>" in job["prompt"]
    assert "d1" not in job["prompt"]


# ── planner: pass-2 must bind real beat text into dialogue_ref ─────────

class FakeLLM:
    def __init__(self):
        self.calls = []

    def __call__(self, pass_tag: str, system: str, user: str) -> str:
        self.calls.append(pass_tag)
        if pass_tag == "pass1":
            return json.dumps({"beats": [
                {"index": 1, "speaker": "GRANDMA",
                 "text": "You wicked boy.", "section": "act1"}]})
        if pass_tag == "pass2":
            return json.dumps({"shots": [{
                "index": 1, "speaker": "GRANDMA", "dialogue_ref": "d1",
                "framing": "wide", "movement": "static", "lighting": "bright",
                "start_image_ref": "PLATE",
                "audio_guide_ref": {"path": "GUIDE", "duration_s": 107 / 24},
                "duration_s": 107 / 24, "section": "act1"}]})
        if pass_tag == "pass3":
            return json.dumps({"notes": "ok"})
        raise AssertionError(pass_tag)


def test_planner_binds_beat_text_into_dialogue_ref(tmp_path):
    plan = ShortFilmPlanner(llm=FakeLLM()).plan(
        script="s",
        characters=[_character(tmp_path)],
        plate_paths={"GRANDMA": _plate(tmp_path, "grandma_master.png")},
        guide_paths={"d1": (str(tmp_path / "line.wav"), 107 / 24)},
    )
    # dialogue_ref must now carry the REAL line, prefixed by its guide key
    assert plan.shots[0].dialogue_ref == "d1: You wicked boy."
    job = render_shot(plan, plan.shots[0])
    assert "<d>[English] You wicked boy.</d>" in job["prompt"]


# ── F1 (PR #57 review): multi-beat speaker must bind per guide-key ──────

class MultiBeatLLM:
    """One speaker, TWO beats — d1 and d2 must each get their OWN line."""

    def __init__(self):
        self.calls = []

    def __call__(self, pass_tag: str, system: str, user: str) -> str:
        self.calls.append(pass_tag)
        if pass_tag == "pass1":
            return json.dumps({"beats": [
                {"index": 1, "speaker": "GRANDMA",
                 "text": "You wicked boy.", "section": "act1"},
                {"index": 2, "speaker": "GRANDMA",
                 "text": "Bring me the cane.", "section": "act1"}]})
        if pass_tag == "pass2":
            return json.dumps({"shots": [
                {"index": 1, "speaker": "GRANDMA", "dialogue_ref": "d1",
                 "framing": "wide", "movement": "static", "lighting": "bright",
                 "start_image_ref": "PLATE",
                 "audio_guide_ref": {"path": "GUIDE", "duration_s": 107 / 24},
                 "duration_s": 107 / 24, "section": "act1"},
                {"index": 2, "speaker": "GRANDMA", "dialogue_ref": "d2",
                 "framing": "medium", "movement": "static", "lighting": "bright",
                 "start_image_ref": "PLATE",
                 "audio_guide_ref": {"path": "GUIDE", "duration_s": 107 / 24},
                 "duration_s": 107 / 24, "section": "act1"}]})
        if pass_tag == "pass3":
            return json.dumps({"notes": "ok"})
        raise AssertionError(pass_tag)


def test_multi_beat_speaker_binds_own_line_per_shot(tmp_path):
    plan = ShortFilmPlanner(llm=MultiBeatLLM()).plan(
        script="s",
        characters=[_character(tmp_path)],
        plate_paths={"GRANDMA": _plate(tmp_path, "grandma_master.png")},
        guide_paths={"d1": (str(tmp_path / "line1.wav"), 107 / 24),
                     "d2": (str(tmp_path / "line2.wav"), 107 / 24)},
    )
    assert len(plan.shots) == 2
    assert plan.shots[0].dialogue_ref == "d1: You wicked boy."
    assert plan.shots[1].dialogue_ref == "d2: Bring me the cane."
    # Each rendered shot's <d> block carries its OWN line (F1 regression:
    # the old speaker-first-match bound shot 2 to the FIRST beat).
    j1 = render_shot(plan, plan.shots[0])
    j2 = render_shot(plan, plan.shots[1])
    assert "<d>[English] You wicked boy.</d>" in j1["prompt"]
    assert "<d>[English] Bring me the cane.</d>" in j2["prompt"]
    assert "Bring me the cane." not in j1["prompt"]
    assert "You wicked boy." not in j2["prompt"]

