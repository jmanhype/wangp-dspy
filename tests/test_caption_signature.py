"""WD-obun — caption signature + caption-aware pipeline contract.

Contract: captions are an EXPLICIT STAGE (typed CaptionSpec -> caption
artifact in PipelineResult), never prompt text. Deterministic: same
CaptionSpec + video paths -> byte-identical caption artifacts.
"""
import json
import pytest

from predict.caption import (
    CaptionCue, CaptionSpec, CaptionArtifact, CaptionValidationError,
    build_captions)
from predict.pipeline import Pipeline, PipelineStageError


# ── CaptionSpec: typed, deterministic ────────────────────────────────

def test_caption_spec_rejects_empty_text():
    with pytest.raises(CaptionValidationError, match="nonempty"):
        CaptionSpec(cues=[CaptionCue(start=0.0, end=1.0, text="  ")])


def test_caption_spec_rejects_bad_timecodes():
    with pytest.raises(CaptionValidationError, match="start < end"):
        CaptionSpec(cues=[CaptionCue(start=2.0, end=1.0, text="hi")])
    with pytest.raises(CaptionValidationError, match="non-negative"):
        CaptionSpec(cues=[CaptionCue(start=-1.0, end=1.0, text="hi")])


def test_caption_spec_rejects_overlapping_cues():
    with pytest.raises(CaptionValidationError, match="overlap"):
        CaptionSpec(cues=[CaptionCue(start=0.0, end=2.0, text="a"),
                          CaptionCue(start=1.0, end=3.0, text="b")])


def test_caption_spec_rejects_unknown_language():
    with pytest.raises(CaptionValidationError, match="language"):
        CaptionSpec(cues=[CaptionCue(start=0.0, end=1.0, text="hi")],
                    language="klingon")


def test_caption_spec_normalizes_whitespace():
    spec = CaptionSpec(cues=[CaptionCue(start=0.0, end=1.0,
                                        text="  hello   world  ")])
    assert spec.cues[0].text == "hello world"


# ── artifact: deterministic, provenance-linked ───────────────────────

def test_build_captions_deterministic_bytes():
    cues = [CaptionCue(start=0.0, end=1.5, text="first line"),
            CaptionCue(start=1.5, end=3.0, text="second line")]
    spec = CaptionSpec(cues=cues)
    a = build_captions(spec, "video1.mp4")
    b = build_captions(spec, "video1.mp4")
    assert a.to_srt() == b.to_srt()
    assert a.artifact_sha == b.artifact_sha
    assert a.source_video == "video1.mp4"


def test_artifact_sha_binds_spec_and_video():
    spec = CaptionSpec(cues=[CaptionCue(start=0.0, end=1.0, text="hi")])
    a = build_captions(spec, "v1.mp4")
    b = build_captions(spec, "v2.mp4")
    assert a.artifact_sha != b.artifact_sha


def test_srt_timecode_format():
    spec = CaptionSpec(cues=[CaptionCue(start=1.0, end=65.5, text="hi")])
    art = build_captions(spec, "v.mp4")
    srt = art.to_srt()
    assert "00:00:01,000 --> 00:01:05,500" in srt
    assert "hi" in srt


def test_to_json_roundtrip():
    spec = CaptionSpec(cues=[CaptionCue(start=0.0, end=1.0, text="hi")])
    art = build_captions(spec, "v.mp4")
    data = json.loads(art.to_json())
    assert data["source_video"] == "v.mp4"
    assert data["artifact_sha"] == art.artifact_sha


# ── pipeline wiring: explicit caption stage ──────────────────────────

class _StubBrief:
    pass


class _StubDirector:
    def __init__(self, result=None):
        self.result = result
    def __call__(self, intent, **kw):
        from predict.prompt_director import RenderBrief
        class Out:
            def __init__(self):
                self.brief = RenderBrief(subject="s", motion="m",
                                         camera="c", style="st")
        return Out()


class _StubSelector:
    def from_brief(self, brief):
        class Out:
            from predict.profile_selector import ProfileDecision
            decision = ProfileDecision(
                model="h3", resolution="768p", shot_length_frames=107,
                seed_policy="fixed_per_story", wangp_profile="profile3")
        return Out()


class _StubAdapter:
    def render(self, briefs, decision):
        class R:
            video_paths = ["out.mp4"]
        return R()


def _make_pipeline():
    return Pipeline(genre="comedy", director=_StubDirector(),
                    selector=_StubSelector(), adapter=_StubAdapter(),
                    qc_factory=None)


def test_pipeline_accepts_caption_spec_and_emits_artifact():
    spec = CaptionSpec(cues=[CaptionCue(start=0.0, end=1.0, text="hi")])
    p = _make_pipeline()
    result = p.forward("test intent", caption_spec=spec)
    assert result.captions is not None
    assert result.captions.source_video == "out.mp4"


def test_pipeline_without_caption_spec_omits_stage():
    result = _make_pipeline().forward("test intent")
    assert result.captions is None


def test_pipeline_caption_stage_failure_is_typed():
    spec = CaptionSpec(cues=[CaptionCue(start=0.0, end=1.0, text="hi")])
    p = _make_pipeline()
    # video_paths missing -> stage boundary error naming 'captions'
    class EmptyR:
        video_paths = []
    class EmptyAdapter:
        def render(self, briefs, decision):
            return EmptyR()
    p.adapter = EmptyAdapter()
    with pytest.raises(PipelineStageError, match="captions"):
        p.forward("test intent", caption_spec=spec)


def test_pipeline_captions_deterministic_across_calls():
    spec = CaptionSpec(cues=[CaptionCue(start=0.0, end=1.0, text="hi")])
    p = _make_pipeline()
    r1 = p.forward("test intent", caption_spec=spec)
    r2 = p.forward("test intent", caption_spec=spec)
    assert r1.captions.artifact_sha == r2.captions.artifact_sha
