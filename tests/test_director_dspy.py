"""DSPy-native short-film planner — RED-first tests (follow-up to the
Maestro port PR #54).

Proves: signatures/director.py exposes the three pass contracts with
the legacy strict-JSON descriptors carried verbatim; ShortFilmPlanner
is a dspy.Module with named submodules (GEPA-targetable); the
injected-callable constructor still works unchanged; and the DSPy
path (dspy.utils.DummyLM) produces an IDENTICAL ProductionPlan from
the same scripted responses (golden behavior).
"""
from __future__ import annotations

import json
from pathlib import Path

import dspy
import pytest

from services.director.schema import CharacterProfile, ProductionPlan
from services.director.planners.short_film import (
    DSPY_LLM, PlannerError, ShortFilmPlanner,
)
from signatures.director import ScreenplayBeats, ShotBreakdown, ShotPolish


# ── fixtures (mirror tests/test_director_port.py) ────────────────────

def _plate(tmp_path: Path, name: str = "master.png"):
    plate = tmp_path / name
    plate.write_bytes(b"\x89PNG-fake-plate")
    plate.with_suffix(".plate.json").write_text(json.dumps({"facing": "camera"}))
    return plate


def _guide(tmp_path: Path):
    g = tmp_path / "line.wav"
    g.write_bytes(b"RIFF-fake-guide")
    return g


def _character(tmp_path: Path, name="GRANDMA"):
    return CharacterProfile(
        name=name,
        description="an elderly woman with gray hair in a bun",
        master_plate_path=str(_plate(tmp_path, f"{name.lower()}_master.png")),
        facing_requirement="camera",
    )


PASS1_JSON = json.dumps({"beats": [
    {"index": 1, "speaker": "GRANDMA", "text": "You wicked boy.",
     "section": "act1"}]})
PASS2_JSON = json.dumps({"shots": [{
    "index": 1, "speaker": "GRANDMA", "dialogue_ref": "d1",
    "framing": "wide", "movement": "static", "lighting": "bright",
    "start_image_ref": "PLATE",
    "audio_guide_ref": {"path": "GUIDE", "duration_s": 107/24},
    "duration_s": 107/24, "section": "act1"}]})
PASS3_JSON = json.dumps({"notes": "polished", "approved": True})

LEGACY_SYSTEMS = {
    "pass1": (
        "You are a screenwriter. Read the script and character list. "
        "Return STRICT JSON: {\"beats\": [{\"index\": int (1..N in order), "
        "\"speaker\": str (a character name), \"text\": str (the spoken "
        "line), \"section\": str}]}. One beat per spoken line. Creative and "
        "performance-focused."),
    "pass2": (
        "You are a shot-breakdown artist for a single-character-per-shot "
        "dialogue film. Input: screenplay beats, characters, plate paths "
        "(camera-facing master plates), audio guides with durations. "
        "Return STRICT JSON: {\"shots\": [{\"index\": int, \"speaker\": str, "
        "\"dialogue_ref\": str (guide key), \"framing\": \"wide\"|"
        "\"medium-wide\"|\"medium\", \"movement\": \"static\", \"lighting\": "
        "\"bright\"|\"natural\", \"start_image_ref\": str (plate path), "
        "\"audio_guide_ref\": {\"path\": str, \"duration_s\": float}, "
        "\"duration_s\": float (MUST equal the guide duration and be on "
        "the 5/22/39/56/73/90/107/...s grid), \"section\": str}]}."),
    "pass3": (
        "You are a script doctor. Review the shot list for pacing, "
        "redundancy, and emotional arc. Return STRICT JSON: {\"notes\": "
        "str, \"approved\": bool}. Do NOT alter the shot structure."),
}


class FakeLLM:
    """Legacy injected callable — same as test_director_port.FakeLLM."""

    def __init__(self):
        self.calls = []

    def __call__(self, pass_tag, system, user):
        self.calls.append((pass_tag, system))
        return {"pass1": PASS1_JSON, "pass2": PASS2_JSON,
                "pass3": PASS3_JSON}[pass_tag]


def _plan_kwargs(tmp_path):
    return dict(
        script="Grandma scolds the prisoner.",
        characters=[_character(tmp_path)],
        plate_paths={"GRANDMA": str(_plate(tmp_path))},
        guide_paths={"d1": (str(_guide(tmp_path)), 107/24)},
    )


# ── 1: signatures ────────────────────────────────────────────────────

def test_signature_input_output_fields_typed():
    for sig, inputs, outputs in (
        (ScreenplayBeats, {"script", "characters"}, {"beats"}),
        (ShotBreakdown,
         {"beats", "characters", "plates", "guides", "duration_grid"},
         {"shots"}),
        (ShotPolish, {"beats", "shots"}, {"notes"}),
    ):
        assert set(sig.input_fields) == inputs, sig.__name__
        assert set(sig.output_fields) == outputs, sig.__name__


@pytest.mark.parametrize("sig,out_field,tag", [
    (ScreenplayBeats, "beats", "pass1"),
    (ShotBreakdown, "shots", "pass2"),
    (ShotPolish, "notes", "pass3"),
])
def test_strict_json_descriptors_carried_verbatim(sig, out_field, tag):
    # the legacy STRICT JSON contract text survives verbatim in the
    # signature (instructions docstring or output-field descriptor)
    legacy = LEGACY_SYSTEMS[tag]
    idx = legacy.index("Return STRICT JSON")
    strict = legacy[idx:]
    field = sig.output_fields[out_field]
    desc = getattr(field, "desc", "") or ""
    assert strict in sig.__doc__ or strict in desc, (
        f"{sig.__name__} lost the strict-JSON contract")


# ── 2: module shape / GEPA readiness ─────────────────────────────────

def test_planner_is_dspy_module_with_named_submodules():
    planner = ShortFilmPlanner(llm=DSPY_LLM)
    assert isinstance(planner, dspy.Module)
    for name, sig in (("pass_beats", ScreenplayBeats),
                      ("pass_shots", ShotBreakdown),
                      ("pass_polish", ShotPolish)):
        sub = getattr(planner, name)
        assert isinstance(sub, dspy.BaseModule), name
        assert sub.signature == sig, name


def test_named_submodules_reachable_via_named_predictors():
    # GEPA teleprompt targets: named predictors are discoverable
    planner = ShortFilmPlanner(llm=DSPY_LLM)
    assert planner.pass_beats.signature is ScreenplayBeats


# ── 3: back-compat shim ──────────────────────────────────────────────

def test_injected_callable_constructor_unchanged(tmp_path):
    fake = FakeLLM()
    planner = ShortFilmPlanner(llm=fake)
    plan = planner.plan(**_plan_kwargs(tmp_path))
    assert isinstance(plan, ProductionPlan)
    assert [c[0] for c in fake.calls] == ["pass1", "pass2", "pass3"]
    # legacy system prompts byte-identical (behavior must not change)
    assert [c[1] for c in fake.calls] == [
        LEGACY_SYSTEMS["pass1"], LEGACY_SYSTEMS["pass2"],
        LEGACY_SYSTEMS["pass3"]]


def test_no_llm_still_rejects():
    with pytest.raises(TypeError):
        ShortFilmPlanner()


def test_non_callable_llm_rejects():
    with pytest.raises(TypeError):
        ShortFilmPlanner(llm="not-a-callable")


# ── 4: DSPy path with DummyLM ────────────────────────────────────────

def _dspy_planner():
    return ShortFilmPlanner(llm=DSPY_LLM)


def test_dspy_path_runs_under_settings_lm(tmp_path):
    lm = dspy.utils.DummyLM([
        {"beats": PASS1_JSON},
        {"shots": PASS2_JSON},
        {"notes": PASS3_JSON},
    ])
    planner = _dspy_planner()
    with dspy.context(lm=lm):
        plan = planner.plan(**_plan_kwargs(tmp_path))
    assert isinstance(plan, ProductionPlan)
    assert plan.shots[0].speaker == "GRANDMA"
    assert abs(plan.shots[0].duration_s - 107/24) < 1e-9
    assert plan.shots[0].start_image_ref == str(_plate(tmp_path))


def test_dspy_path_planner_error_on_bad_json(tmp_path):
    lm = dspy.utils.DummyLM([
        {"beats": "not json at all"},
    ])
    with dspy.context(lm=lm):
        with pytest.raises(PlannerError):
            _dspy_planner().plan(**_plan_kwargs(tmp_path))


def test_dspy_path_pass2_grid_error(tmp_path):
    bad = json.dumps({"shots": [{
        "index": 1, "speaker": "GRANDMA", "dialogue_ref": "d1",
        "framing": "wide", "movement": "static", "lighting": "bright",
        "start_image_ref": "PLATE",
        "audio_guide_ref": {"path": "GUIDE", "duration_s": 5.0},
        "duration_s": 5.0, "section": "act1"}]})
    lm = dspy.utils.DummyLM([
        {"beats": PASS1_JSON}, {"shots": bad}, {"notes": PASS3_JSON},
    ])
    from services.director.renderers.h3_ref2va import GridError
    with dspy.context(lm=lm):
        with pytest.raises(GridError):
            _dspy_planner().plan(**_plan_kwargs(tmp_path))


# ── 5: golden behavior — same scripted responses, same plan ──────────

def test_golden_identical_plan_before_after_refactor(tmp_path):
    """The acceptance proof: the legacy callable path and the DSPy
    path, fed the SAME scripted responses, produce IDENTICAL
    ProductionPlans (which also equal the pre-refactor construction —
    trusted local mappings, not LLM paths, resolve refs)."""
    legacy_plan = ShortFilmPlanner(llm=FakeLLM()).plan(**_plan_kwargs(tmp_path))
    lm = dspy.utils.DummyLM([
        {"beats": PASS1_JSON}, {"shots": PASS2_JSON},
        {"notes": PASS3_JSON},
    ])
    with dspy.context(lm=lm):
        dspy_plan = _dspy_planner().plan(**_plan_kwargs(tmp_path))
    assert dspy_plan == legacy_plan
    # and equal to the direct (pre-refactor) schema construction
    from services.director.schema import CameraPlan, ShotPlan
    expected = ProductionPlan(
        film_id="film",
        characters=(_character(tmp_path),),
        shots=(ShotPlan(
            index=1, speaker="GRANDMA", dialogue_ref="d1",
            camera_plan=CameraPlan(framing="wide", movement="static",
                                   lighting="bright"),
            start_image_ref=str(_plate(tmp_path)),
            audio_guide_ref={"path": str(_guide(tmp_path)),
                             "duration_s": 107/24},
            duration_s=107/24, section="act1"),))
    assert legacy_plan == expected


# ── 6: no hard-coded endpoints ───────────────────────────────────────

def test_no_hardcoded_endpoints_in_planner():
    src = Path("services/director/planners/short_film.py").read_text()
    for banned in ("api.z.ai", "api_base", "GLM_API_KEY", "11434",
                   "api.openai"):
        assert banned not in src
