"""Gate fixes RED tests: F1 (QC seam + file readback), F4 (timeout kill),
F2 (per-render dir isolation), Luna minors a/b/c."""
import json
import os
import subprocess

import pytest

from predict.prompt_director import RenderBrief
from predict.profile_selector import (
    ProfileDecision, SHOT_LENGTH_FLOOR_FRAMES,
)
from evaluate.render_qc import QCVerdict, Verdict
from host.wangp_adapter import (
    RenderedShot, WanGPAdapter, WanGPError, build_settings,
)

STYLE = "16mm archival grain"


def _brief(subject="astronaut, cracked visor", motion="slow head turn",
           camera="dolly in", style=STYLE):
    return RenderBrief(subject=subject, motion=motion, camera=camera,
                       style=style)


def _decision(frames=176):
    return ProfileDecision(
        model="h3", resolution="768p", shot_length_frames=frames,
        seed_policy="fixed_per_story", wangp_profile="profile3")


def _fake_venv(tmp_path):
    py = tmp_path / "venv" / "bin" / "python"
    py.parent.mkdir(parents=True, exist_ok=True)
    py.write_text("#!/bin/sh\n")
    py.chmod(0o755)
    wgp = tmp_path / "wgp.py"
    wgp.write_text("# wgp\n")
    return str(py), str(wgp)


def _ok_runner(outputs=("shot.mp4",), seen=None):
    """Succeed; optionally write fake video files into the --output-dir."""
    def runner(cmd, cwd, env, timeout):
        if seen is not None:
            seen.append(cmd)
        outdir = cmd[cmd.index("--output-dir") + 1]
        if outputs:
            for name in outputs:
                p = os.path.join(outdir, name)
                os.makedirs(os.path.dirname(p), exist_ok=True)
                with open(p, "wb") as fh:
                    fh.write(b"\x00\x00\x00\x18ftyp")
        class R:
            returncode = 0
            stdout = ""
            stderr = ""
        return R()
    return runner


# ── F1: render surfaces produced files; QC seam is real ─────────────────────

def test_render_surfaces_produced_video_files(tmp_path):
    vpy, vwgp = _fake_venv(tmp_path)
    result = WanGPAdapter(venv_python=vpy, wgp_script=vwgp,
                          output_dir=str(tmp_path),
                          runner=_ok_runner(outputs=["shot_0001.mp4"])
                          ).render([_brief()], _decision())
    assert result.video_paths, "render() must surface produced files"
    assert result.video_paths[0].endswith("shot_0001.mp4")
    assert os.path.isfile(result.video_paths[0])


def test_render_readback_scopes_to_own_dir_only(tmp_path):
    # a stale partial from a previous render must NOT leak into readback
    stale = tmp_path / "stale.mp4"
    stale.write_bytes(b"old")
    vpy, vwgp = _fake_venv(tmp_path)
    result = WanGPAdapter(venv_python=vpy, wgp_script=vwgp,
                          output_dir=str(tmp_path),
                          runner=_ok_runner(outputs=["new.mp4"])
                          ).render([_brief()], _decision())
    assert [os.path.basename(p) for p in result.video_paths] == ["new.mp4"]


def test_run_pipeline_qc_receives_real_brief_and_decision(tmp_path):
    from predict.assembler import ShotPlan

    calls = []

    class RealishQC:
        def __init__(self, genre):
            pass

        def run(self, brief, decision, video=None):
            # touch the arguments — proves the seam carries real objects
            calls.append((brief.subject, brief.motion, brief.camera,
                          brief.style, decision.model,
                          decision.shot_length_frames))
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
                           runner=_ok_runner(outputs=["a.mp4"]),
                           qc_factory=RealishQC, assembler=Assembler())
    plans = [
        ShotPlan(brief=_brief(), decision=_decision(),
                 terminal_state="astronaut mid-turn stopped"),
        ShotPlan(brief=_brief(subject="astronaut at the hatch",
                              motion="astronaut mid-turn drifting"),
                 decision=_decision(),
                 terminal_state="astronaut at the hatch still"),
    ]
    adapter.run_pipeline(plans, genre="surreal")
    assert calls == [
        ("astronaut, cracked visor", "slow head turn", "dolly in", STYLE,
         "h3", 176),
        ("astronaut at the hatch", "astronaut mid-turn drifting", "dolly in",
         STYLE, "h3", 176),
    ]


# ── F4: TimeoutExpired -> typed error + child killed ────────────────────────

def test_default_runner_timeout_kills_child_and_raises_typed(tmp_path):
    import host.wangp_adapter as mod

    events = []

    class FakeProc:
        returncode = None

        def communicate(self, timeout=None):
            events.append("communicate")
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

    monkeypatch_target = mod.subprocess
    real_popen = monkeypatch_target.Popen

    class PopenShim:
        def __new__(cls, cmd, **kw):
            return FakePopen(cmd, **kw)

    monkeypatch_target.Popen = PopenShim
    try:
        vpy, vwgp = _fake_venv(tmp_path)
        adapter = WanGPAdapter(venv_python=vpy, wgp_script=vwgp,
                               output_dir=str(tmp_path))
        with pytest.raises(WanGPError, match="timed out"):
            adapter.render([_brief()], _decision())
    finally:
        monkeypatch_target.Popen = real_popen
    assert events == ["popen", "communicate", "kill", "wait"]


# ── F2: per-render subdirectory isolation ───────────────────────────────────

def test_each_render_gets_its_own_subdir_and_settings(tmp_path):
    seen = []
    vpy, vwgp = _fake_venv(tmp_path)
    adapter = WanGPAdapter(venv_python=vpy, wgp_script=vwgp,
                           output_dir=str(tmp_path),
                           runner=_ok_runner(seen=seen))
    adapter.render([_brief()], _decision())
    adapter.render([_brief()], _decision())
    dirs = [c[c.index("--output-dir") + 1] for c in seen]
    settings = [c[c.index("--process") + 1] for c in seen]
    assert dirs[0] != dirs[1], "retries/renders must not share a dir"
    for d, s in zip(dirs, settings):
        assert os.path.isfile(s)
        # settings sit in the render dir, one level above the attempt dir
        assert os.path.dirname(s) == os.path.dirname(d)


def test_retry_does_not_read_prior_attempt_partials(tmp_path):
    state = {"n": 0}

    def runner(cmd, cwd, env, timeout):
        state["n"] += 1
        outdir = cmd[cmd.index("--output-dir") + 1]
        if state["n"] == 1:
            # partial output from the choked attempt
            with open(os.path.join(outdir, "partial.mp4"), "wb") as fh:
                fh.write(b"x")
            class R:
                returncode = 1
                stdout = ""
                stderr = "504 Gateway Timeout"
            return R()
        with open(os.path.join(outdir, "good.mp4"), "wb") as fh:
            fh.write(b"y")
        class R:
            returncode = 0
            stdout = ""
            stderr = ""
        return R()

    vpy, vwgp = _fake_venv(tmp_path)
    adapter = WanGPAdapter(venv_python=vpy, wgp_script=vwgp,
                           output_dir=str(tmp_path), runner=runner,
                           sleeper=lambda s: None)
    result = adapter.render([_brief()], _decision())
    assert result.attempts == 2
    assert [os.path.basename(p) for p in result.video_paths] == ["good.mp4"]


# ── Luna minors ──────────────────────────────────────────────────────────────

def test_missing_venv_python_is_typed_error(tmp_path):
    adapter = WanGPAdapter(
        venv_python=str(tmp_path / "nope" / "bin" / "python"),
        wgp_script=str(tmp_path / "wgp.py"),
        output_dir=str(tmp_path / "out"))
    with pytest.raises(WanGPError, match="venv"):
        adapter.render([_brief()], _decision())


def test_non_executable_venv_python_is_typed_error(tmp_path):
    py = tmp_path / "python"
    py.write_text("#!/bin/sh\n")           # exists but NOT executable
    adapter = WanGPAdapter(
        venv_python=str(py), wgp_script=str(tmp_path / "wgp.py"),
        output_dir=str(tmp_path / "out"))
    with pytest.raises(WanGPError, match="venv"):
        adapter.render([_brief()], _decision())


def test_floor_check_rejects_bool(tmp_path):
    bad = _decision()
    object.__setattr__(bad, "shot_length_frames", True)  # bool is int subclass
    # sole authority: WanGPJobConfig rejects the bool typing, wrapped
    # adapter-typed (the inline duplicate was deleted, WD-l5bx)
    with pytest.raises(WanGPError, match="int"):
        build_settings([_brief()], bad)


# ── WD-l5bx review fold-ins: regression coverage ──────────────────

def test_g5_covers_camera_style_audio_direction_at_build():
    # review strong-rec 5: the <d>-or-silence scan must cover ALL
    # brief text fields, not just subject/motion — exercised at the
    # build/render layer (not only submit) so render() callers cannot
    # bypass.
    from predict.prompt_director import RenderBrief
    base = dict(subject="a detective", motion="walks",
                camera="dolly in", style="16mm grain")
    for bad_text in ("[John] pans", "(Mary) handheld"):
        for field in ("camera", "style", "audio_direction"):
            b = RenderBrief(**{**base, field: bad_text})
            with pytest.raises(WanGPError, match="G5"):
                build_settings([b], _decision())


def test_g5_rejected_at_render_entry_point(tmp_path):
    # review strong-rec 4: G1/G4/G5 live in submit() only — make the
    # render()/build_settings enforcement deliberate: a malformed
    # speaker token on ANY brief field is rejected before any wgp run.
    vpy, vwgp = _fake_venv(tmp_path)
    from predict.prompt_director import RenderBrief
    b = RenderBrief(subject="a detective", motion="walks",
                    camera="dolly in", style="[Narrator] grain")
    adapter = WanGPAdapter(venv_python=vpy, wgp_script=vwgp,
                           output_dir=str(tmp_path),
                           runner=_ok_runner())
    with pytest.raises(WanGPError, match="G5"):
        adapter.render([b], _decision())


def test_separator_single_constant():
    # review nit: one definition — adapter, job_config and render
    # profiles all bind the SAME object.
    import predict.job_config as jc
    import host.wangp_adapter as ad
    import predict.render_profiles as rp
    assert (ad.SCRIPT_SEPARATOR is jc.SCRIPT_SEPARATOR
            and rp.SCRIPT_SEPARATOR is jc.SCRIPT_SEPARATOR)


def test_ref2va_image_refs_inside_validated_shape(tmp_path):
    # review strong-rec 6: rule 4 (flat JSON) is scoped to the generic
    # lane; the Ref2VA doc carries image_refs as a sanctioned extension
    # via to_settings_doc(extra=...) — and the generic lane still
    # rejects nested values.
    import pathlib
    from predict.job_config import WanGPJobConfig, JobConfigError
    from predict.render_profiles import Ref2VAProfile
    refs = [str(pathlib.Path(tmp_path) / "ref1.png")]
    pathlib.Path(refs[0]).write_bytes(b"x")
    # WD-a1d9: audio_plane kwargs required (audio_guide readable +
    # provenance); supplied via the shared helper shape
    import pathlib as _pl
    from predict.audio_dataplane import AudioGuideProvenance
    afiles = []
    for nm in ("guide.wav", "master.wav", "vocal.wav", "wmap.json"):
        f = _pl.Path(tmp_path) / nm
        f.write_bytes(b"x" * 8)
        afiles.append(str(f))
    p = Ref2VAProfile()
    doc = p.build_settings([_brief()], _decision(),
                           image_refs=refs, audio_prompt_type="A",
                           guide_duration_s=8.0, shot_duration_s=8.0,
                           audio_guide=afiles[0],
                           audio_provenance=AudioGuideProvenance(
                               source_master=afiles[1],
                               vocal_stem=afiles[2],
                               whisper_map=afiles[3],
                               keeper_window_s=(1.0, 5.0)))
    assert doc["image_refs"] == refs
    assert doc["audio_prompt_type"] == "A"
    # generic lane still enforces flatness (extra nested value is
    # caught by the validated shape, not appended after validation)
    cfg = WanGPJobConfig(
        model_type="m", script="s", width=480, height=832,
        frames_per_shot=107, force_fps="24")
    with pytest.raises(JobConfigError, match="flat|nested"):
        cfg.to_settings_doc(extra={"bad_list": [1, 2]})
