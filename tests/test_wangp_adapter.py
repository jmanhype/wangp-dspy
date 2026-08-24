"""WD story-5 RED tests: WanGPAdapter — render pipeline vs the local 3090.

Ground truth (probed on the 3090):
- wgp is NOT on PATH; real invocation is `<venv>/bin/python wgp.py` from the
  Wan2GP checkout, with $HOME/.local/bin prepended to PATH (nd/pvg need it).
- headless render: `wgp.py --process <settings.json> --output-dir <dir>
  --profile 3`; settings json keys: model_type, prompt="multishot", script
  (the shot text), width, height, frames_per_shot, num_inference_steps,
  guidance_scale, embedded_guidance_scale, force_fps=24, seed.
- H3 multishot scripts join per-shot prompts with '---'.
- HARD floor: frames_per_shot >= 96 (4s @ 24fps).

All subprocess/time behavior is injected (runner/sleeper); no GPU, no network.
"""
import json
import os

import pytest

from predict.prompt_director import RenderBrief
from predict.profile_selector import (
    ProfileDecision, SHOT_LENGTH_FLOOR_FRAMES,
)
from evaluate.render_qc import Verdict
from host.wangp_adapter import (
    frame_tolerance,
    H3_MODEL_TYPE,
    MULTISHOT_PROMPT_TAG,
    SCRIPT_SEPARATOR,
    WanGPAdapter,
    WanGPError,
    build_script,
    build_settings,
)

STYLE = "16mm archival grain"


def _brief(subject="astronaut, cracked visor", motion="slow head turn",
           camera="dolly in", style=STYLE):
    return RenderBrief(subject=subject, motion=motion, camera=camera,
                       style=style)


def _decision(frames=175):
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


def _brief_text(b):
    # section order matches the established pipeline: subject/motion/camera/style
    return f"{b.subject}. {b.motion}. {b.camera}. {b.style}"


# ── script join + settings json ──────────────────────────────────────────────

def test_build_script_joins_briefs_with_separator():
    b1, b2 = _brief(), _brief(subject="astronaut visor reflecting earth")
    script = build_script([_brief_text(b1), _brief_text(b2)])
    # WD-izly: separator must sit on its OWN line (wgp multishot.py:49)
    assert script == _brief_text(b1) + "\n---\n" + _brief_text(b2)


def test_build_settings_exact_shape_and_multishot_tag():
    briefs = [_brief(), _brief(subject="astronaut walking on dunes")]
    settings = build_settings(briefs, _decision())
    assert settings["model_type"] == H3_MODEL_TYPE
    assert settings["prompt"] == MULTISHOT_PROMPT_TAG
    assert settings["script"] == build_script([_brief_text(b) for b in briefs])
    assert settings["frames_per_shot"] == 175  # on-grid: snapped value (WD-u4rv)
    assert settings["force_fps"] == "24"  # string — wgp len()s it (story-6 live finding)
    # 768p vertical
    assert (settings["width"], settings["height"]) == (480, 832)
    assert isinstance(settings["seed"], int)


def test_build_settings_enforces_shot_floor():
    # ProfileDecision already rejects sub-floor; verify the adapter's own
    # defense-in-depth with a smuggled sub-floor decision.
    bad = _decision()
    object.__setattr__(bad, "shot_length_frames",
                       SHOT_LENGTH_FLOOR_FRAMES - 1)
    with pytest.raises(WanGPError, match="floor"):
        build_settings([_brief()], bad)


# ── venv / PATH handling ─────────────────────────────────────────────────────

def test_render_uses_venv_python_wgp_with_local_bin_path(tmp_path):
    calls = {}

    def runner(cmd, cwd, env, timeout):
        import os as _os
        calls["cmd"] = cmd
        calls["env"] = env
        outdir = cmd[cmd.index("--output-dir") + 1]
        with open(_os.path.join(outdir, "shot.mp4"), "wb") as fh:
            fh.write(b"v")
        class R:
            pass
        r = R()
        r.returncode = 0
        r.stdout = ""
        r.stderr = ""
        return r

    venv_python = tmp_path / "venv" / "bin" / "python"
    venv_python.parent.mkdir(parents=True)
    venv_python.write_text("#!/bin/sh\n")
    os.chmod(venv_python, 0o755)
    wgp = tmp_path / "wgp.py"
    wgp.write_text("# wgp\n")

    adapter = WanGPAdapter(
        venv_python=str(venv_python), wgp_script=str(wgp),
        output_dir=str(tmp_path / "out"), runner=runner)
    adapter.render([_brief()], _decision())

    cmd = calls["cmd"]
    assert cmd[0] == str(venv_python)
    assert cmd[1] == str(wgp)
    assert "--process" in cmd and "--profile" in cmd
    # settings file passed to --process is the one written to disk
    proc_idx = cmd.index("--process")
    assert os.path.isfile(cmd[proc_idx + 1])
    assert cmd[proc_idx + 1].endswith("settings.json")
    # PATH carries $HOME/.local/bin for nd/pvg
    assert calls["env"]["PATH"].startswith(
        os.path.join(os.path.expanduser("~"), ".local", "bin"))


def test_render_writes_settings_then_processes(tmp_path):
    seen = {}

    def runner(cmd, cwd, env, timeout):
        import os as _os
        seen["settings"] = json.load(open(cmd[cmd.index("--process") + 1]))
        outdir = cmd[cmd.index("--output-dir") + 1]
        with open(_os.path.join(outdir, "shot.mp4"), "wb") as fh:
            fh.write(b"v")
        class R:
            pass
        r = R()
        r.returncode = 0
        r.stdout = ""
        r.stderr = ""
        return r

    vpy, vwgp = _fake_venv(tmp_path)
    adapter = WanGPAdapter(venv_python=vpy, wgp_script=vwgp, output_dir=str(tmp_path), runner=runner)
    briefs = [_brief(), _brief(subject="astronaut at the hatch")]
    adapter.render(briefs, _decision())
    assert seen["settings"]["script"] == build_script(
        [_brief_text(b) for b in briefs])


# ── failure / retry: 504 decode-choke, 60s+ backoff ─────────────────────────

def _fail_once_with(marker, code=1):
    state = {"n": 0}

    def runner(cmd, cwd, env, timeout):
        import os as _os
        state["n"] += 1
        if state["n"] == 1:
            class R:
                pass
            r = R()
            r.returncode = code
            r.stdout = ""
            r.stderr = f"...{marker}... decode choke ..."
            return r

        outdir = cmd[cmd.index("--output-dir") + 1]
        with open(_os.path.join(outdir, "shot.mp4"), "wb") as fh:
            fh.write(b"v")
        class R2:
            pass
        r2 = R2()
        r2.returncode = 0
        r2.stdout = ""
        r2.stderr = ""
        return r2
    runner.calls = state
    return runner


def test_render_retries_on_504_with_60s_backoff_then_succeeds(tmp_path):
    sleeps = []
    runner = _fail_once_with("504 Gateway Timeout")

    vpy, vwgp = _fake_venv(tmp_path)
    adapter = WanGPAdapter(venv_python=vpy, wgp_script=vwgp, output_dir=str(tmp_path), runner=runner,
                           sleeper=sleeps.append)
    result = adapter.render([_brief()], _decision())

    assert runner.calls["n"] == 2                  # retried exactly once
    assert sleeps and sleeps[0] >= 60.0            # 60s+ backoff
    assert result.attempts == 2


def test_render_retries_on_decode_choke_marker(tmp_path):
    sleeps = []
    runner = _fail_once_with("DecodeError")
    vpy, vwgp = _fake_venv(tmp_path)
    adapter = WanGPAdapter(venv_python=vpy, wgp_script=vwgp, output_dir=str(tmp_path), runner=runner,
                           sleeper=sleeps.append)
    adapter.render([_brief()], _decision())
    assert runner.calls["n"] == 2


def test_render_gives_up_after_max_attempts(tmp_path):
    sleeps = []

    def always_fail(cmd, cwd, env, timeout):
        class R:
            returncode = 1
            stdout = ""
            stderr = "504 Gateway Timeout"
        return R()

    vpy, vwgp = _fake_venv(tmp_path)
    adapter = WanGPAdapter(venv_python=vpy, wgp_script=vwgp,
                           output_dir=str(tmp_path), runner=always_fail,
                           sleeper=sleeps.append, max_attempts=3)
    with pytest.raises(WanGPError, match="504"):
        adapter.render([_brief()], _decision())
    assert sleeps == [60.0, 60.0]                  # backoff between 3 attempts


def test_render_hard_failure_does_not_retry(tmp_path):
    sleeps = []
    n = {"n": 0}

    def runner(cmd, cwd, env, timeout):
        n["n"] += 1
        class R:
            returncode = 2
            stdout = ""
            stderr = "CUDA out of memory"
        return R()

    vpy, vwgp = _fake_venv(tmp_path)
    adapter = WanGPAdapter(venv_python=vpy, wgp_script=vwgp, output_dir=str(tmp_path), runner=runner,
                           sleeper=sleeps.append)
    with pytest.raises(WanGPError, match="failed"):
        adapter.render([_brief()], _decision())
    assert n["n"] == 1                             # no retry on hard failure
    assert sleeps == []


# ── pipeline: render -> RenderQC -> keepers -> Assembler ────────────────────

def _pipeline_qc(verdict, monkeypatch=None):
    """RenderQC stub: one verdict for every shot."""
    from evaluate.render_qc import QCVerdict
    qc = {}

    class FakeQC:
        def __init__(self, genre):
            qc["genre"] = genre

        def run(self, brief, decision, video=None):
            qc.setdefault("calls", 0)
            qc["calls"] += 1
            return QCVerdict(verdict=verdict,
                             reason="stub", scores={})

    return FakeQC, qc


def test_run_pipeline_passes_keepers_to_assembler(tmp_path):
    from predict.assembler import ShotPlan
    from host.wangp_adapter import RenderedShot

    def runner(cmd, cwd, env, timeout):
        outdir = cmd[cmd.index("--output-dir") + 1]
        with open(os.path.join(outdir, "shot.mp4"), "wb") as fh:
            fh.write(b"v")
        class R:
            returncode = 0
            stdout = ""
            stderr = ""
        return R()

    FakeQC, qc_state = _pipeline_qc(Verdict.PASS)
    assembled = {"n": 0}

    class FakeAssembler:
        def assemble(self, plans):
            assembled["n"] = len(plans)
            assembled["plans"] = plans
            class Chain:
                shots = tuple(plans)
                continuity_digest = "digest"
            return Chain()

    vpy, vwgp = _fake_venv(tmp_path)
    adapter = WanGPAdapter(venv_python=vpy, wgp_script=vwgp, output_dir=str(tmp_path), runner=runner,
                           qc_factory=FakeQC, assembler=FakeAssembler())
    briefs = [
        _brief(subject="astronaut mid-turn, visor cracked"),
        _brief(subject="astronaut exits the lander hatch",
               motion="astronaut mid-turn drifting left"),
    ]
    decisions = [_decision(), _decision()]
    plans = [
        ShotPlan(brief=b, decision=d, terminal_state=t)
        for b, d, t in zip(
            briefs, decisions,
            ["astronaut mid-turn stopped", "astronaut at the hatch still"])
    ]
    chain = adapter.run_pipeline(plans, genre="surreal")

    assert assembled["n"] == 2                     # both keepers assembled
    assert qc_state["calls"] == 2                  # QC saw both shots
    assert chain.continuity_digest == "digest"


def test_run_pipeline_revise_and_reject_not_assembled(tmp_path):
    from predict.assembler import ShotPlan

    verdicts = iter([])

    def runner(cmd, cwd, env, timeout):
        outdir = cmd[cmd.index("--output-dir") + 1]
        with open(os.path.join(outdir, "shot.mp4"), "wb") as fh:
            fh.write(b"v")
        class R:
            returncode = 0
            stdout = ""
            stderr = ""
        return R()

    class FakeQC:
        def __init__(self, genre):
            pass

        def run(self, brief, decision, video=None):
            v = next(FakeQC.seq)
            from evaluate.render_qc import QCVerdict
            return QCVerdict(verdict=v, reason="stub", scores={})

    # REVISE now earns exactly ONE anchored retry (story-3 contract), so
    # the sequence is: PASS, REJECT, REVISE->retry PASS. Keepers: 1st and 3rd.
    FakeQC.seq = iter([Verdict.PASS, Verdict.REJECT, Verdict.REVISE,
                       Verdict.PASS])

    assembled = {"n": 0}

    class FakeAssembler:
        def assemble(self, plans):
            assembled["n"] = len(plans)
            class Chain:
                shots = tuple(plans)
                continuity_digest = "d"
            return Chain()

    vpy, vwgp = _fake_venv(tmp_path)
    adapter = WanGPAdapter(venv_python=vpy, wgp_script=vwgp, output_dir=str(tmp_path), runner=runner,
                           qc_factory=FakeQC, assembler=FakeAssembler())
    from predict.assembler import ShotPlan
    plans = []
    for i, subj in enumerate([
            "astronaut mid-turn, visor cracked",
            "astronaut exits the lander",
            "astronaut plants the flag"]):
        plans.append(ShotPlan(
            brief=_brief(subject=subj), decision=_decision(),
            terminal_state=f"astronaut step {i} done"))

    chain = adapter.run_pipeline(plans, genre="surreal")
    # PASS keeper + the REVISE shot whose single anchored retry passed;
    # only the REJECT shot is excluded
    assert assembled["n"] == 2
    subjects = [p.brief.subject for p in chain.shots]
    assert "astronaut exits the lander" not in subjects
    assert chain.shots[0].brief.subject == plans[0].brief.subject


def test_run_pipeline_too_few_keepers_hits_assembler_bounds(tmp_path):
    """Keeper-count bounds are the REAL assembler's typed domain."""
    from predict.assembler import (
        ChainValidationError, MultiShotAssembler, ShotPlan,
    )

    def runner(cmd, cwd, env, timeout):
        outdir = cmd[cmd.index("--output-dir") + 1]
        with open(os.path.join(outdir, "shot.mp4"), "wb") as fh:
            fh.write(b"v")
        class R:
            returncode = 0
            stdout = ""
            stderr = ""
        return R()

    class FakeQC:
        def __init__(self, genre):
            pass

        def run(self, brief, decision, video=None):
            from evaluate.render_qc import QCVerdict
            return QCVerdict(verdict=Verdict.REJECT, reason="stub",
                             scores={})

    vpy, vwgp = _fake_venv(tmp_path)
    adapter = WanGPAdapter(venv_python=vpy, wgp_script=vwgp, output_dir=str(tmp_path), runner=runner,
                           qc_factory=FakeQC,
                           assembler=MultiShotAssembler())
    plans = [ShotPlan(brief=_brief(), decision=_decision(),
                      terminal_state="astronaut done")]
    with pytest.raises(ChainValidationError, match="at least"):
        adapter.run_pipeline(plans, genre="surreal")


# ── command construction details ────────────────────────────────────────────

def test_render_command_shape_and_profile(tmp_path):
    seen = {}

    def runner(cmd, cwd, env, timeout):
        import os as _os
        seen["cmd"] = cmd
        outdir = cmd[cmd.index("--output-dir") + 1]
        with open(_os.path.join(outdir, "shot.mp4"), "wb") as fh:
            fh.write(b"v")
        class R:
            pass
        r = R()
        r.returncode = 0
        r.stdout = ""
        r.stderr = ""
        return r

    vpy, vwgp = _fake_venv(tmp_path)
    adapter = WanGPAdapter(venv_python=vpy, wgp_script=vwgp, output_dir=str(tmp_path), runner=runner)
    adapter.render([_brief()], _decision())
    cmd = seen["cmd"]
    # wgp.py + --process + --profile <wangp profile number> + --output-dir
    assert cmd[cmd.index("--profile") + 1] == "3"
    assert cmd[cmd.index("--output-dir") + 1].startswith(str(tmp_path))


def test_default_runner_constructs_subprocess_cmd(tmp_path, monkeypatch):
    """The REAL runner (no injection) builds the venv-python command."""
    captured = {}

    class FakePopen:
        def __init__(self, cmd, **kw):
            self.cmd = cmd
            captured["cmd"] = cmd
            captured["kw"] = kw
            self.returncode = 0

        def communicate(self, timeout=None):
            outdir = self.cmd[self.cmd.index("--output-dir") + 1] \
                if hasattr(self, "cmd") else None
            import os as _os
            if outdir:
                with open(_os.path.join(outdir, "shot.mp4"), "wb") as fh:
                    fh.write(b"v")
            return (b"", b"")

    import host.wangp_adapter as mod
    monkeypatch.setattr(mod.subprocess, "Popen", FakePopen)
    vpy, vwgp = _fake_venv(tmp_path)
    adapter = WanGPAdapter(venv_python=vpy, wgp_script=vwgp,
                           output_dir=str(tmp_path))
    adapter.render([_brief()], _decision())
    assert captured["cmd"][0].endswith("python")
    assert any(a.endswith("wgp.py") for a in captured["cmd"][:2])
    assert captured["kw"]["cwd"]  # runs inside the Wan2GP checkout


def test_render_retries_on_decoding_error_variant(tmp_path):
    """GLM M1 follow-up: wgp also emits 'decoding error' — must retry."""
    sleeps = []
    runner = _fail_once_with("decoding error in VAEBatchDecode")
    vpy, vwgp = _fake_venv(tmp_path)
    adapter = WanGPAdapter(venv_python=vpy, wgp_script=vwgp,
                           output_dir=str(tmp_path), runner=runner,
                           sleeper=sleeps.append)
    adapter.render([_brief()], _decision())
    assert runner.calls["n"] == 2


def test_settings_force_fps_is_string():
    """Story-6 live finding: real wgp get_computed_fps does len(force_fps)
    — an int crashes validation. Probe-verified against a known-good
    settings file on the 3090 (force_fps: "24")."""
    briefs = [_brief()]
    settings = build_settings(briefs, _decision())
    assert settings["force_fps"] == "24"
    assert isinstance(settings["force_fps"], str)


def test_unverified_sentinel_skips_verification_not_passes():
    """Luna PR#12 residual: pin the sentinel-skip semantics — the
    sentinel must SKIP verification, never satisfy a mismatch."""
    from host.wangp_adapter import (FRAME_COUNT_UNVERIFIED,
                                          frame_tolerance)
    want = 3 * 175  # the live cycle-3 expectation
    tol = frame_tolerance(3)  # WD-tc04: seam-scaled, not flat 2
    # sentinel never trips the mismatch branch...
    got = FRAME_COUNT_UNVERIFIED
    assert not (got != FRAME_COUNT_UNVERIFIED
                and abs(got - want) >= tol)
    # ...while the live-bug count and worse do trip it
    for real in (172, 0):
        assert abs(real - want) >= tol, real


def test_render_result_carries_effective_frames():
    """Qwen PR#12 required finding: the H3 grid snap must be visible
    to consumers, not silent."""
    from host.wangp_adapter import effective_frames_per_shot, RenderResult
    assert effective_frames_per_shot(160) == 175
    r = RenderResult(attempts=1, settings_path="s", output_dir="o",
                     video_paths=("v",), effective_frames=175)
    assert r.effective_frames == 175


def test_720p_snapped_to_h3_grid_wdo4g2():
    """WD-o4g2: portrait 720x1280 is off H3's latent grid (90/2=45 odd);
    build_settings must snap to the supported 480x832 grid instead of
    emitting settings that deterministically crash patchify."""
    from host.wangp_adapter import build_settings
    from predict.prompt_director import RenderBrief
    from predict.profile_selector import ProfileDecision
    brief = RenderBrief(subject="s", motion="m", camera="c", style="st")
    d = ProfileDecision(model="h3", resolution="720p",
                        shot_length_frames=124,
                        seed_policy="fixed_per_story",
                        wangp_profile="profile3")
    s = build_settings([brief], d)
    assert (s["width"], s["height"]) == (480, 832)
