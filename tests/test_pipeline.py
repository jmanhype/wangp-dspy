"""WD-pt60 e2e: Pipeline chains every stage with typed boundary
failures — stubbed LM, stubbed host, no GPU.

Proves epic AC #1 (one call, one artifact chain) and #2 (typed
failure at every boundary) at the unit level; the real-GPU proof is
WD-mhr2's job.
"""
import json

import pytest

from predict.prompt_director import RenderBrief
from predict.profile_selector import ProfileDecision
from predict.pipeline import Pipeline, PipelineStageError, PipelineResult
import tasks
from tasks import TaskSpec, register, get, all_tasks


def _brief_json(subject="a lighthouse", motion="waves crash",
                camera="slow push in", style="16mm ektachrome"):
    return json.dumps({"subject": subject, "motion": motion,
                       "camera": camera, "style": style})


class StubDirector:
    """Returns a valid brief; raisable for boundary tests."""

    def __init__(self, fail=False):
        self.fail = fail

    def __call__(self, intent):
        class _P:
            pass
        if self.fail:
            raise ValueError("bad LM output")
        p = _P()
        p.brief = RenderBrief(
            subject="a lighthouse", motion="waves crash",
            camera="slow push in", style="16mm ektachrome")
        return p


class StubSelector:
    def __init__(self, fail=False):
        self.fail = fail

    def from_brief(self, brief):
        if self.fail:
            raise ValueError("no JSON in decision")
        return type("P", (), {"decision": ProfileDecision(
            model="h3", resolution="768p", shot_length_frames=107,
            seed_policy="fixed_per_story", wangp_profile="profile3")})()


class StubRenderResult:
    def __init__(self, videos):
        self.video_paths = tuple(videos)


class StubAdapter:
    def __init__(self, videos=("out.mp4",), fail=False):
        self.videos = videos
        self.fail = fail

    def render(self, briefs, decision):
        if self.fail:
            raise RuntimeError("wgp died")
        return StubRenderResult(self.videos)


class StubQC:
    def __init__(self, genre, verdict="PASS"):
        self.genre = genre
        self.verdict = verdict

    def run(self, brief, decision, video):
        return type("V", (), {"verdict": self.verdict})()


def _pipeline(**kw):
    return Pipeline(
        genre="surreal",
        director=StubDirector(), selector=StubSelector(),
        assembler=None, adapter=None, qc_factory=None, **kw)


def test_one_call_dry_run_produces_artifact_chain():
    p = _pipeline()
    r = p.forward("a lighthouse in a storm")
    assert isinstance(r, PipelineResult)
    assert len(r.briefs) == 1 and r.briefs[0].subject == "a lighthouse"
    assert r.decisions[0].model == "h3"
    assert r.render is None and r.verdicts == []
    assert any(s.startswith("briefs:") for s in r.evidence)
    assert any(s.startswith("profile:") for s in r.evidence)


def test_full_chain_with_stubs():
    p = Pipeline(
        genre="surreal", director=StubDirector(), selector=StubSelector(),
        adapter=StubAdapter(("v1.mp4",)),
        qc_factory=lambda g: StubQC(g))
    r = p.forward("a lighthouse in a storm")
    assert r.render.video_paths == ("v1.mp4",)
    assert len(r.verdicts) == 1
    assert r.evidence[-1].startswith("qc:")


def test_briefs_boundary_is_typed():
    p = Pipeline(genre="surreal", director=StubDirector(fail=True),
                 selector=StubSelector())
    with pytest.raises(PipelineStageError) as ei:
        p.forward("x")
    assert ei.value.stage == "briefs"


def test_profile_boundary_is_typed():
    p = Pipeline(genre="surreal", director=StubDirector(),
                 selector=StubSelector(fail=True))
    with pytest.raises(PipelineStageError) as ei:
        p.forward("x")
    assert ei.value.stage == "profile"


def test_render_boundary_is_typed():
    p = Pipeline(genre="surreal", director=StubDirector(),
                 selector=StubSelector(),
                 adapter=StubAdapter(fail=True))
    with pytest.raises(PipelineStageError) as ei:
        p.forward("x")
    assert ei.value.stage == "render"


def test_qc_boundary_is_typed():
    class FailingQC:
        def run(self, *a, **k):
            raise ValueError("critic down")
    p = Pipeline(genre="surreal", director=StubDirector(),
                 selector=StubSelector(), adapter=StubAdapter(),
                 qc_factory=lambda g: FailingQC())
    with pytest.raises(PipelineStageError) as ei:
        p.forward("x")
    assert ei.value.stage == "qc"


def test_task_registry_roundtrip_and_append_only():
    assert get("surreal").genre == "surreal"
    assert {t.genre for t in all_tasks()} >= {"surreal", "music"}
    with pytest.raises(ValueError, match="append-only"):
        register(TaskSpec(genre="surreal", dataset="dup",
                          metric="qc_feedback"))
    with pytest.raises(ValueError, match="no QC profile"):
        register(TaskSpec(genre="nonexistent", dataset="x",
                          metric="qc_feedback"))
    with pytest.raises(KeyError):
        get("nonexistent")
