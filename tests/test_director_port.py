"""Maestro Director architecture port — RED-first tests.

Proves: schema round-trips; 3-pass planner with injected fake LLMs and
call order; H3-Ref2VA renderer policy (facing / framing / duration
grid / guide-duration equality) + subject_prompt-format prompts;
orchestrator lineage hashes stable; purity (no training/metrics/
evaluate imports).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from services.director.schema import (
    CameraPlan,
    CharacterProfile,
    DialogueBeat,
    ProductionPlan,
    ShotPlan,
)
from services.director.planners.short_film import ShortFilmPlanner
from services.director.renderers.h3_ref2va import (
    FacingError,
    FramingError,
    GuideDurationError,
    GridError,
    H3Ref2VARenderer,
    render_shot,
)
from services.director.orchestrator import DirectorOrchestrator


# ── fixtures ─────────────────────────────────────────────────────────

def _plate(tmp_path: Path, name: str = "master.png", facing: str = "camera"):
    """Create a master plate + facing sidecar; return its path."""
    plate = tmp_path / name
    plate.write_bytes(b"\x89PNG-fake-plate")
    meta = {"facing": facing}
    plate.with_suffix(".plate.json").write_text(json.dumps(meta))
    return plate


def _guide(tmp_path: Path, name: str = "line.wav", dur: float = 5.0):
    g = tmp_path / name
    g.write_bytes(b"RIFF-fake-guide")
    return g


def _character(tmp_path: Path, name: str = "GRANDMA", facing: str = "camera"):
    return CharacterProfile(
        name=name,
        description="an elderly woman with gray hair in a bun, tattered brown cloak",
        master_plate_path=str(_plate(tmp_path, f"{name.lower()}_master.png", facing)),
        facing_requirement=facing,
    )


def _shot(tmp_path: Path, **over):
    kw = dict(
        index=1,
        speaker="GRANDMA",
        dialogue_ref="d1: You wicked boy.",
        camera_plan=CameraPlan(framing="wide", movement="static",
                               lighting="bright"),
        start_image_ref=str(_plate(tmp_path, "grandma_master.png", "camera")),
        audio_guide_ref={"path": str(_guide(tmp_path)), "duration_s": 107/24},
        duration_s=107/24,
        section="act1",
    )
    kw.update(over)
    return ShotPlan(**kw)


def _plan(tmp_path: Path, shots=None):
    return ProductionPlan(
        film_id="film-x",
        characters=(_character(tmp_path),),
        shots=tuple(shots or [_shot(tmp_path)]),
    )


# ── schema ──────────────────────────────────────────────────────────

def test_schema_round_trip(tmp_path):
    plan = _plan(tmp_path)
    doc = plan.to_json()
    rt = ProductionPlan.from_json(doc)
    assert rt == plan
    # also via string form
    rt2 = ProductionPlan.from_json(json.loads(json.dumps(doc)))
    assert rt2 == plan


def test_schema_frozen():
    plan = _plan(Path("/tmp"))
    with pytest.raises(Exception):
        plan.film_id = "other"


def test_shotplan_rejects_bad_duration():
    with pytest.raises(ValueError):
        _shot(Path("/tmp"), duration_s=0)


# ── planner: 3 passes, injected fakes, call order ───────────────────

class FakeLLM:
    """Records (pass_tag, user_len); returns canned per-pass responses."""

    def __init__(self, pass2_shots=None, pass3_polish=None):
        self.calls = []
        self.pass2_shots = pass2_shots or [{
            "index": 1, "speaker": "GRANDMA", "dialogue_ref": "d1",
            "framing": "wide", "movement": "static", "lighting": "bright",
            "start_image_ref": "PLATE", "audio_guide_ref": {"path": "GUIDE",
                                                            "duration_s": 107/24},
            "duration_s": 107/24, "section": "act1",
        }]
        self.pass3_polish = pass3_polish or {"notes": "polished"}

    def __call__(self, pass_tag: str, system: str, user: str) -> str:
        self.calls.append(pass_tag)
        if pass_tag == "pass1":
            return json.dumps({"beats": [
                {"index": 1, "speaker": "GRANDMA", "text": "You wicked boy.",
                 "section": "act1"}]})
        if pass_tag == "pass2":
            return json.dumps({"shots": self.pass2_shots})
        if pass_tag == "pass3":
            return json.dumps(self.pass3_polish)
        raise AssertionError(f"unexpected pass tag {pass_tag}")


def test_planner_three_passes_in_order(tmp_path):
    fake = FakeLLM()
    planner = ShortFilmPlanner(llm=fake)
    plan = planner.plan(
        script="Grandma scolds the prisoner.",
        characters=[_character(tmp_path)],
        plate_paths={"GRANDMA": str(_plate(tmp_path))},
        guide_paths={"d1": (str(_guide(tmp_path)), 107/24)},
    )
    assert fake.calls == ["pass1", "pass2", "pass3"]
    assert isinstance(plan, ProductionPlan)
    assert plan.shots[0].speaker == "GRANDMA"
    assert plan.shots[0].start_image_ref == str(_plate(tmp_path))
    assert abs(plan.shots[0].duration_s - 107/24) < 1e-9


def test_planner_deterministic(tmp_path):
    def mk():
        f = FakeLLM()
        p = ShortFilmPlanner(llm=f).plan(
            script="s", characters=[_character(tmp_path)],
            plate_paths={"GRANDMA": str(_plate(tmp_path))},
            guide_paths={"d1": (str(_guide(tmp_path)), 107/24)})
        return p
    assert mk() == mk()


def test_planner_no_llm_rejects():
    with pytest.raises(TypeError):
        ShortFilmPlanner()  # llm callable is REQUIRED, no default endpoint


def test_planner_rejects_off_grid_shot(tmp_path):
    fake = FakeLLM(pass2_shots=[{
        "index": 1, "speaker": "GRANDMA", "dialogue_ref": "d1",
        "framing": "wide", "movement": "static", "lighting": "bright",
        "start_image_ref": "PLATE", "audio_guide_ref": {"path": "GUIDE",
                                                        "duration_s": 6.0},
        "duration_s": 6.0, "section": "act1"}])
    with pytest.raises(GridError):
        ShortFilmPlanner(llm=fake).plan(
            script="s", characters=[_character(tmp_path)],
            plate_paths={"GRANDMA": str(_plate(tmp_path))},
            guide_paths={"d1": (str(_guide(tmp_path)), 107/24)})


# ── renderer ────────────────────────────────────────────────────────

def test_renderer_emits_subject_prompt_format(tmp_path):
    from predict.subject_prompt import build_subject_prompt  # noqa: F401
    shot = _shot(tmp_path)
    plan = _plan(tmp_path, [shot])
    job = render_shot(plan, shot)
    prompt = job["prompt"]
    assert "<Subject 1> (from <Picture 1>):" in prompt
    assert "(S1) says: <d>[English]" in prompt
    assert "Non-diegetic music:" in prompt
    assert job["audio_prompt_type"] == "A"
    assert job["video_prompt_type"] == "I"
    assert job["multi_prompts_gen_type"] == "FG"
    assert job["guide_slice"] == {"start_s": 0.0, "end_s": 107/24,
                                  "duration_s": 107/24}
    assert job["image_refs"] == [shot.start_image_ref]


def test_renderer_rejects_wrong_facing_master(tmp_path):
    char = _character(tmp_path, facing="profile")  # sidecar says not camera
    shot = _shot(tmp_path, start_image_ref=char.master_plate_path)
    plan = ProductionPlan(film_id="f", characters=(char,), shots=(shot,))
    with pytest.raises(FacingError):
        render_shot(plan, shot)


def test_renderer_rejects_missing_plate(tmp_path):
    shot = _shot(tmp_path, start_image_ref=str(tmp_path / "nope.png"))
    with pytest.raises(FacingError):
        render_shot(_plan(tmp_path, [shot]), shot)


def test_renderer_rejects_off_grid_duration(tmp_path):
    shot = _shot(tmp_path, duration_s=5.0,
                 audio_guide_ref={"path": str(_guide(tmp_path)),
                                  "duration_s": 5.0})
    with pytest.raises(GridError):
        render_shot(_plan(tmp_path, [shot]), shot)


def test_renderer_rejects_guide_duration_mismatch(tmp_path):
    shot = _shot(tmp_path,
                 audio_guide_ref={"path": str(_guide(tmp_path)),
                                  "duration_s": 5.2})
    with pytest.raises(GuideDurationError):
        render_shot(_plan(tmp_path, [shot]), shot)


def test_renderer_rejects_tight_or_dim_framing(tmp_path):
    for framing, lighting in (("close", "bright"), ("wide", "dim")):
        shot = _shot(tmp_path, camera_plan=CameraPlan(
            framing=framing, movement="static", lighting=lighting))
        with pytest.raises(FramingError):
            render_shot(_plan(tmp_path, [shot]), shot)


def test_renderer_is_pure_class():
    r = H3Ref2VARenderer()
    assert callable(r.render)


# ── orchestrator ────────────────────────────────────────────────────

def test_orchestrator_emits_jobs_and_manifests(tmp_path):
    orch = DirectorOrchestrator()
    result = orch.execute(_plan(tmp_path))
    assert len(result.jobs) == 1
    job = result.jobs[0]
    assert job["audio_prompt_type"] == "A"
    man = result.manifests[0]
    assert set(man) >= {"shot_index", "plan_sha256", "job_sha256",
                        "guide_sha256", "plate_sha256", "lineage"}


def test_orchestrator_lineage_stable(tmp_path):
    a = DirectorOrchestrator().execute(_plan(tmp_path))
    b = DirectorOrchestrator().execute(_plan(tmp_path))
    assert a.manifests == b.manifests
    assert a.jobs == b.jobs


def test_orchestrator_no_gpu_side_effects(tmp_path):
    # emission only: no renders dir created, no subprocess attr on module
    import services.director.orchestrator as orch_mod
    assert not hasattr(orch_mod, "subprocess")
    orch = DirectorOrchestrator()
    plan = _plan(tmp_path)
    before = set(tmp_path.iterdir())
    orch.execute(plan)
    assert set(tmp_path.iterdir()) == before


# ── purity ──────────────────────────────────────────────────────────

def test_no_training_metrics_evaluate_imports():
    import subprocess, sys
    root = Path(__file__).resolve().parent.parent / "services"
    files = [p for p in root.rglob("*.py")]
    assert files
    bad = []
    for p in files:
        src = p.read_text()
        for banned in ("from training", "import training",
                       "from metrics", "import metrics",
                       "from evaluate", "import evaluate"):
            if banned in src:
                bad.append((str(p), banned))
    assert not bad
