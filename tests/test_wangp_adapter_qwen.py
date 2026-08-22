"""Qwen architecture-review fixes RED tests: QB1 (QC sees rendered video),
QB2 (REVISE wiring: one anchored retry, then typed escalation), minors
a/b/c (word-boundary transient regex, seed from seed_policy, timeout
hard-fail doc/policy)."""
import os
import re
import subprocess

import pytest

from wangp_dspy.prompt_director import RenderBrief
from wangp_dspy.profile_selector import ProfileDecision
from wangp_dspy.render_qc import QCVerdict, Verdict
from wangp_dspy.wangp_adapter import (
    QCEscalationError, RenderedShot, WanGPAdapter, WanGPError,
    build_settings, derive_seed,
)

STYLE = "16mm archival grain"


def _brief(subject="astronaut, cracked visor", motion="slow head turn",
           camera="dolly in", style=STYLE):
    return RenderBrief(subject=subject, motion=motion, camera=camera,
                       style=style)


def _decision(frames=176, policy="fixed_per_story"):
    return ProfileDecision(
        model="h3", resolution="768p", shot_length_frames=frames,
        seed_policy=policy, wangp_profile="profile3")


def _fake_venv(tmp_path):
    py = tmp_path / "venv" / "bin" / "python"
    py.parent.mkdir(parents=True, exist_ok=True)
    py.write_text("#!/bin/sh\n")
    py.chmod(0o755)
    wgp = tmp_path / "wgp.py"
    wgp.write_text("# wgp\n")
    return str(py), str(wgp)


def _ok_runner(outputs=None, seen=None):
    def runner(cmd, cwd, env, timeout):
        if seen is not None:
            seen.append(cmd)
        outdir = cmd[cmd.index("--output-dir") + 1]
        if outputs:
            for name in outputs:
                p = os.path.join(outdir, name)
                with open(p, "wb") as fh:
                    fh.write(b"\x00\x00\x00\x18ftyp")
        class R:
            returncode = 0
            stdout = ""
            stderr = ""
        return R()
    return runner


# ── QB1: the QC gate sees the rendered material ─────────────────────────────

def test_qc_signature_has_video_input_field():
    from wangp_dspy.render_qc import RenderQCSignature
    fields = list(RenderQCSignature.input_fields)
    names = [f if isinstance(f, str) else f.name for f in fields]
    assert "video" in names, \
        "RenderQC must accept the rendered video (path) as input"


def test_run_pipeline_passes_video_path_to_qc(tmp_path):
    """A real-ish judge that REQUIRES the video path proves the seam
    carries the render output, not just text."""
    from wangp_dspy.assembler import ShotPlan

    seen_videos = []

    class VideoQC:
        def __init__(self, genre):
            pass

        def run(self, brief, decision, video):
            assert video and os.path.isfile(video), \
                "QC must receive an existing rendered video file"
            seen_videos.append(video)
            return QCVerdict(verdict=Verdict.PASS, reason="ok", scores={})

    class Assembler:
        def assemble(self, plans):
            class Chain:
                shots = tuple(plans)
                continuity_digest = "d"
            return Chain()

    vpy, vwgp = _fake_venv(tmp_path)
    adapter = WanGPAdapter(venv_python=vpy, wgp_script=vwgp,
                           output_dir=str(tmp_path),
                           runner=_ok_runner(outputs=["shot.mp4"]),
                           qc_factory=VideoQC, assembler=Assembler())
    plans = [
        ShotPlan(brief=_brief(), decision=_decision(),
                 terminal_state="astronaut mid-turn stopped"),
        ShotPlan(brief=_brief(subject="astronaut at the hatch",
                              motion="astronaut mid-turn drifting"),
                 decision=_decision(),
                 terminal_state="astronaut at the hatch still"),
    ]
    adapter.run_pipeline(plans, genre="surreal")
    assert len(seen_videos) == 2
    for v in seen_videos:
        assert v.endswith(".mp4")


def test_render_qc_run_accepts_video(tmp_path):
    """Story-3 RenderQC.run itself takes the video path."""
    import dspy

    from wangp_dspy.render_qc import RenderQC

    captured = {}

    class CapturingLM(dspy.utils.DummyLM):
        def forward(self, prompt=None, messages=None, **kw):
            captured["messages"] = messages or [prompt]
            return super().forward(prompt=prompt, messages=messages, **kw)

    crit = ("{\"coherence\": 8, \"brief_adherence\": 8, "
            "\"concept_encoding\": 8, \"scores\": {}, \"notes\": \"\"}")
    lm = CapturingLM([{"reasoning": "r", "critique": crit}])
    qc = RenderQC("surreal")
    with dspy.context(lm=lm):
        verdict = qc.run(_brief(), _decision(), video="/renders/shot.mp4")
    blob = str(captured["messages"])
    assert "video" in blob and "/renders/shot.mp4" in blob
    assert verdict.verdict == Verdict.PASS


# ── QB2: REVISE gets ONE anchored retry, then typed escalation ──────────────

class _StubAssembler:
    def assemble(self, plans):
        class Chain:
            shots = tuple(plans)
            continuity_digest = "d"
        return Chain()


def test_revise_gets_one_retry_then_passes(tmp_path):
    from wangp_dspy.assembler import ShotPlan

    state = {"qc_calls": 0}

    class ReviseThenPassQC:
        def __init__(self, genre):
            pass

        def run(self, brief, decision, video):
            state["qc_calls"] += 1
            if state["qc_calls"] == 1:
                return QCVerdict(verdict=Verdict.REVISE, reason="weak",
                                 anchor_field="coherence", scores={})
            return QCVerdict(verdict=Verdict.PASS, reason="ok", scores={})

    class Assembler:
        def assemble(self, plans):
            class Chain:
                shots = tuple(plans)
                continuity_digest = "d"
            return Chain()

    vpy, vwgp = _fake_venv(tmp_path)
    adapter = WanGPAdapter(venv_python=vpy, wgp_script=vwgp,
                           output_dir=str(tmp_path),
                           runner=_ok_runner(outputs=["s.mp4"]),
                           qc_factory=ReviseThenPassQC, assembler=Assembler())
    plans = [
        ShotPlan(brief=_brief(), decision=_decision(),
                 terminal_state="astronaut mid-turn stopped"),
        ShotPlan(brief=_brief(subject="astronaut at the hatch",
                              motion="astronaut mid-turn drifting"),
                 decision=_decision(),
                 terminal_state="astronaut at the hatch still"),
    ]
    chain = adapter.run_pipeline(plans, genre="surreal")
    assert len(chain.shots) == 2


def test_revise_persists_after_retry_escalates(tmp_path):
    from wangp_dspy.assembler import ShotPlan

    class AlwaysReviseQC:
        def __init__(self, genre):
            pass

        def run(self, brief, decision, video):
            return QCVerdict(verdict=Verdict.REVISE, reason="weak",
                             anchor_field="coherence", scores={})

    vpy, vwgp = _fake_venv(tmp_path)
    adapter = WanGPAdapter(venv_python=vpy, wgp_script=vwgp,
                           output_dir=str(tmp_path),
                           runner=_ok_runner(outputs=["s.mp4"]),
                           qc_factory=AlwaysReviseQC,
                           assembler=_StubAssembler())
    plans = [ShotPlan(brief=_brief(), decision=_decision(),
                      terminal_state="astronaut done")]
    with pytest.raises(QCEscalationError, match="human"):
        adapter.run_pipeline(plans, genre="surreal")


def test_revise_retry_count_is_bounded_at_one(tmp_path):
    from wangp_dspy.assembler import ShotPlan

    state = {"qc": 0, "renders": 0}

    def runner(cmd, cwd, env, timeout):
        state["renders"] += 1
        outdir = cmd[cmd.index("--output-dir") + 1]
        with open(os.path.join(outdir, "s.mp4"), "wb") as fh:
            fh.write(b"v")
        class R:
            returncode = 0
            stdout = ""
            stderr = ""
        return R()

    class ReviseQC:
        def __init__(self, genre):
            pass

        def run(self, brief, decision, video):
            state["qc"] += 1
            return QCVerdict(verdict=Verdict.REVISE, reason="weak",
                             anchor_field="coherence", scores={})

    vpy, vwgp = _fake_venv(tmp_path)
    adapter = WanGPAdapter(venv_python=vpy, wgp_script=vwgp,
                           output_dir=str(tmp_path), runner=runner,
                           qc_factory=ReviseQC, assembler=_StubAssembler())
    plans = [ShotPlan(brief=_brief(), decision=_decision(),
                      terminal_state="astronaut done")]
    with pytest.raises(QCEscalationError):
        adapter.run_pipeline(plans, genre="surreal")
    # one initial QC + one retry QC; one initial render + one re-render
    assert state["qc"] == 2
    assert state["renders"] == 2


# ── minor a: word-boundary transient regex, class attr ─────────────────────

def test_transient_markers_are_word_boundary_regex_class_attr():
    import wangp_dspy.wangp_adapter as mod
    assert hasattr(WanGPAdapter, "TRANSIENT_RE")
    assert WanGPAdapter.TRANSIENT_RE.search("HTTP 504 Gateway Timeout")
    assert WanGPAdapter.TRANSIENT_RE.search("DecodeError in sampler")
    # coincidental digits/ids must NOT match
    assert not WanGPAdapter.TRANSIENT_RE.search(
        "frame 1504 saved to /tmp/504abc.mp4")
    assert not WanGPAdapter.TRANSIENT_RE.search("step 504/1000")


def test_render_does_not_retry_on_coincidental_504(tmp_path):
    n = {"n": 0}

    def runner(cmd, cwd, env, timeout):
        n["n"] += 1
        class R:
            returncode = 1
            stdout = ""
            stderr = "wrote frame 1504 to out504.mp4"
        return R()

    vpy, vwgp = _fake_venv(tmp_path)
    adapter = WanGPAdapter(venv_python=vpy, wgp_script=vwgp,
                           output_dir=str(tmp_path), runner=runner,
                           sleeper=lambda s: None)
    with pytest.raises(WanGPError, match="failed"):
        adapter.render([_brief()], _decision())
    assert n["n"] == 1


# ── minor b: seed derived from seed_policy, not hardcoded 42 ────────────────

def test_derive_seed_deterministic_per_story():
    s1 = derive_seed("fixed_per_story", [_brief()])
    s2 = derive_seed("fixed_per_story", [_brief()])
    other = derive_seed("fixed_per_story",
                        [_brief(subject="different subject")])
    assert s1 == s2
    assert s1 != other
    assert isinstance(s1, int)


def test_derive_seed_unknown_policy_rejected():
    with pytest.raises(WanGPError, match="seed_policy"):
        derive_seed("bogus", [_brief()])


def test_settings_uses_derived_seed():
    settings = build_settings([_brief()], _decision(policy="derived_from_brief"))
    expected = derive_seed("derived_from_brief", [_brief()])
    assert settings["seed"] == expected
    # and two renders of different stories produce different seeds
    s2 = build_settings([_brief(subject="other subject entirely")],
                        _decision(policy="derived_from_brief"))
    assert s2["seed"] != settings["seed"]


# ── minor c: timeout is hard-fail, never retried ────────────────────────────

def test_timeout_is_hard_fail_no_retry(tmp_path):
    from wangp_dspy import wangp_adapter as mod

    events = []

    class FakeProc:
        returncode = None

        def communicate(self, timeout=None):
            raise subprocess.TimeoutExpired(cmd=["wgp"], timeout=timeout)

        def kill(self):
            events.append("kill")
            self.returncode = -9

        def wait(self, timeout=None):
            events.append("wait")

    class FakePopen:
        def __init__(self, cmd, **kw):
            events.append("popen")
            self.p = FakeProc()

        def __getattr__(self, name):
            return getattr(self.p, name)

    real_popen = mod.subprocess.Popen
    mod.subprocess.Popen = lambda cmd, **kw: FakePopen(cmd, **kw)
    try:
        vpy, vwgp = _fake_venv(tmp_path)
        adapter = WanGPAdapter(venv_python=vpy, wgp_script=vwgp,
                               output_dir=str(tmp_path))
        with pytest.raises(WanGPError, match="timed out"):
            adapter.render([_brief()], _decision())
    finally:
        mod.subprocess.Popen = real_popen
    # one attempt only: timeout is a HARD failure, policy is no-retry
    assert events.count("popen") == 1
