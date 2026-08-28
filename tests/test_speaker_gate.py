"""WD-j9nx/S3 — S3-G5a: dialogue attribution REQUIRED on briefs.

RED-first per the plan (docs/plans/s3-speaker-gate.md, Task 2):
bare quoted dialogue with no <d>Name</d> token and no explicit
silence marker is a typed rejection naming S3-G5a; proper
attribution or explicit silence passes. The S2 converter output
(<d>SPEAKER_NN</d> blocks) is the sanctioned upstream shape — the
bridge test proves it end-to-end.
"""
import pytest

from host.wangp_adapter import WanGPAdapter, WanGPError


def _brief(subject="a detective walks", motion="walks forward",
           camera="dolly in", style="16mm grain", audio_direction=""):
    from predict.prompt_director import RenderBrief
    return RenderBrief(subject=subject, motion=motion, camera=camera,
                       style=style, audio_direction=audio_direction)


def _decision():
    from predict.profile_selector import ProfileDecision
    return ProfileDecision(model="h3", resolution="768p",
                           shot_length_frames=107,
                           seed_policy="fixed_per_story",
                           wangp_profile="profile3")


class _OkRunner:
    def __init__(self):
        self.calls = []

    def __call__(self, *a, **k):
        self.calls.append((a, k))
        class R:
            exit_code = 0
            stdout = ""
            stderr = ""
        return R()


# ── S3-G5a: dialogue attribution REQUIRED ────────────────────────────

def test_bare_dialogue_rejected():
    """Quoted speech with no <d> token and no silence marker → S3-G5a."""
    a = WanGPAdapter(output_dir="/tmp/x", runner=_OkRunner())
    with pytest.raises(WanGPError, match="S3-G5a"):
        a.submit(_brief(subject='the detective says "hello there"'),
                 _decision())


def test_attributed_dialogue_passes():
    """Same quote WITH a <d>SPEAKER_00</d> token → accepted."""
    a = WanGPAdapter(output_dir="/tmp/x", runner=_OkRunner())
    b = _brief(subject='the detective says "hello there" '
                       '<d>SPEAKER_00</d>')
    # must NOT raise S3-G5a or G5
    a.submit(b, _decision())


def test_explicit_silence_passes():
    """Silence marker, no quoted speech → accepted (explicit silence)."""
    a = WanGPAdapter(output_dir="/tmp/x", runner=_OkRunner())
    b = _brief(audio_direction="[silence] — no dialogue in this shot")
    a.submit(b, _decision())


def test_silence_with_quote_rejected():
    """Silence marker AND quoted speech but no <d> token → contradiction."""
    a = WanGPAdapter(output_dir="/tmp/x", runner=_OkRunner())
    with pytest.raises(WanGPError, match="S3-G5a"):
        a.submit(_brief(subject='the detective says "hello there" [silence]'),
                 _decision())


def test_malformed_marker_precedence():
    """[John] fires the EXISTING malformed-marker rule, not S3-G5a."""
    a = WanGPAdapter(output_dir="/tmp/x", runner=_OkRunner())
    with pytest.raises(WanGPError) as exc_info:
        a.submit(_brief(subject='[John] says "hi"'), _decision())
    msg = str(exc_info.value)
    assert "S3-G5a" not in msg, f"malformed marker should win: {msg}"
    assert "G5" in msg


@pytest.mark.parametrize("field", ["motion", "camera", "style",
                                   "audio_direction"])
def test_all_fields_checked(field):
    """A bare quoted span in ANY checked field is rejected."""
    kwargs = {field: 'someone shouts "stop!"'}
    a = WanGPAdapter(output_dir="/tmp/x", runner=_OkRunner())
    with pytest.raises(WanGPError, match="S3-G5a"):
        a.submit(_brief(**kwargs), _decision())


def test_s2_bridge_shape():
    """S2 converter output (<d>SPEAKER_NN</d>) feeds S3's gate cleanly.

    End-to-end shape check: timeline doc -> validate -> convert ->
    render_attribution -> embed tokens in a brief with quoted speech
    -> submit accepts.
    """
    from predict.diarization import (validate_diarization,
                                     diarization_to_speaker_blocks,
                                     render_attribution)
    sha = "ab" * 32
    doc = {
        "schema_version": 1,
        "audio_sha256": sha,
        "duration_sec": 10.0,
        "speakers": ["SPEAKER_00", "SPEAKER_01"],
        "segments": [
            {"start": 0.0, "end": 4.0, "speaker": "SPEAKER_00",
             "text": "hello there"},
            {"start": 4.5, "end": 9.0, "speaker": "SPEAKER_01",
             "text": "who goes there"},
        ],
    }
    validate_diarization(doc)
    blocks = diarization_to_speaker_blocks(doc)
    rendered = render_attribution(blocks)
    assert "<d>SPEAKER_00</d>" in rendered
    assert "<d>SPEAKER_01</d>" in rendered

    a = WanGPAdapter(output_dir="/tmp/x", runner=_OkRunner())
    b = _brief(
        subject='the detective says "hello there" and the guard answers '
                '"who goes there" ' + rendered.replace("\n", " "))
    a.submit(b, _decision())   # must not raise


# ── G3 named at run_pipeline QC call path (carried nit from S1) ───────

def _pipeline_plan(tmp_path):
    from predict.assembler import ShotPlan
    return ShotPlan(brief=_brief(), decision=_decision(),
                    terminal_state="stopped")


def _fake_venv(tmp_path):
    """Minimal fake WanGP venv (copied pattern from
    tests/test_wangp_adapter.py — the adapter only needs the paths to
    exist, the runner is injected)."""
    py = tmp_path / "venv" / "bin" / "python"
    py.parent.mkdir(parents=True, exist_ok=True)
    py.write_text("#!/bin/sh\n")
    py.chmod(0o755)
    wgp = tmp_path / "wgp.py"
    wgp.write_text("# wgp\n")
    return str(py), str(wgp)


class _VideoRunner:
    """runner that exits 0 and writes a real shot.mp4 into the outdir
    (so render()'s readback passes); the artifact's fate after that is
    controlled by the FakeQC below."""
    def __call__(self, cmd, cwd, env, timeout):
        outdir = cmd[cmd.index("--output-dir") + 1]
        import os as _os
        with open(_os.path.join(outdir, "shot.mp4"), "wb") as fh:
            fh.write(b"v")
        class R:
            returncode = 0
            stdout = ""
            stderr = ""
        return R()


def test_run_pipeline_missing_video_raises_named_g3(tmp_path):
    """First QC call site: the rendered file is gone by the time
    _checked_video runs → typed G3 error naming the gate
    (artifact-not-spec), not a generic message.

    Seam: the runner writes a real .mp4 (render() passes its own
    readback), then the adapter's video_paths entry is emptied before
    run_pipeline so res.video_path resolves to a nonexistent path —
    exactly the state _checked_video guards."""
    from evaluate.render_qc import Verdict

    class FakeQC:
        def __init__(self, genre):
            pass

        def run(self, brief, decision, video=None):
            raise AssertionError("QC must never run without an artifact")

    vpy, vwgp = _fake_venv(tmp_path)
    adapter = WanGPAdapter(venv_python=vpy, wgp_script=vwgp,
                           output_dir=str(tmp_path),
                           runner=_VideoRunner(),
                           qc_factory=FakeQC, assembler=object())
    # Simulate: render produced no readable artifact for QC. The
    # video_paths tuple is replaced with a path that does not exist —
    # video_path (the property) then returns it, and _checked_video's
    # os.path.isfile check fails → G3 fires.
    orig_render = adapter.render

    def render_no_artifact(briefs, decision):
        res = orig_render(briefs, decision)
        import dataclasses
        return dataclasses.replace(
            res, video_paths=(str(tmp_path / "vanished.mp4"),))
    adapter.render = render_no_artifact

    with pytest.raises(WanGPError) as exc_info:
        adapter.run_pipeline([_pipeline_plan(tmp_path)], genre="surreal")
    msg = str(exc_info.value)
    assert "G3" in msg, f"G3 gate identity missing: {msg}"
    assert "artifact-not-spec" in msg, f"gate name missing: {msg}"


def test_run_pipeline_revise_retry_missing_video_also_g3(tmp_path):
    """REVISE retry path: the second QC call site must fire the SAME
    named G3 when its render produced no readable file.

    Seam: first render yields a real artifact (QC returns REVISE);
    the retry render yields none → _checked_video on the retry must
    name G3."""
    from evaluate.render_qc import Verdict, QCVerdict

    class FakeQC:
        def __init__(self, genre):
            self.calls = 0

        def run(self, brief, decision, video=None):
            self.calls += 1
            return QCVerdict(verdict=Verdict.REVISE, reason="stub",
                             scores={}, anchor_field="concept_encoding")

    vpy, vwgp = _fake_venv(tmp_path)
    adapter = WanGPAdapter(venv_python=vpy, wgp_script=vwgp,
                           output_dir=str(tmp_path),
                           runner=_VideoRunner(),
                           qc_factory=FakeQC, assembler=object())
    calls = {"n": 0}
    orig_render = adapter.render

    def render_second_time_empty(briefs, decision):
        calls["n"] += 1
        res = orig_render(briefs, decision)
        if calls["n"] >= 2:   # the REVISE retry produces no artifact
            import dataclasses
            return dataclasses.replace(
                res, video_paths=(str(tmp_path / "vanished.mp4"),))
        return res
    adapter.render = render_second_time_empty

    with pytest.raises(WanGPError) as exc_info:
        adapter.run_pipeline([_pipeline_plan(tmp_path)], genre="surreal")
    msg = str(exc_info.value)
    assert "G3" in msg, f"G3 gate identity missing on retry: {msg}"
    assert "artifact-not-spec" in msg, f"gate name missing: {msg}"
