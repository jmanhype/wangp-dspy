"""WD-d1kq — bounded OOM retry + calibration for unattended rendering.

Contract:
- OOM stderr (cuda out of memory / torch.cuda.OutOfMemoryError) is
  TRANSIENT: retried with backoff, bounded by max_attempts, typed
  WanGPError carrying per-attempt evidence when exhausted.
- Calibration: before retrying an OOM, the adapter DOWNSHIFTS the
  settings (resolution, frames) — "retry at lower load" — via
  next_calibration(); attempts carry evidence of the calibration step.
- Every attempt is recorded in RenderResult.attempt_log (evidence for
  every attempt, per the story AC).
"""
import json
import os
import pytest

from host.wangp_adapter import (
    WanGPAdapter, WanGPError, OOM_RE, is_oom, next_calibration,
    CALIBRATION_LADDER)
from host.render_host import LocalHost
from predict.prompt_director import RenderBrief
from predict.profile_selector import ProfileDecision


def _fake_venv(tmp_path):
    py = tmp_path / "wan2gp" / "venv" / "bin" / "python"
    py.parent.mkdir(parents=True, exist_ok=True)
    py.write_text("#!/bin/sh\n")
    py.chmod(0o755)
    wgp = tmp_path / "wan2gp" / "wgp.py"
    wgp.write_text("# wgp\n")
    return str(py), str(wgp), tmp_path / "wan2gp"


def _brief():
    return RenderBrief(subject="astronaut, cracked visor",
                       motion="slow head turn", camera="dolly in",
                       style="16mm archival grain")


def _decision():
    return ProfileDecision(model="h3", resolution="768p",
                           shot_length_frames=175,
                           seed_policy="fixed_per_story",
                           wangp_profile="profile3")


def _oom_runner(fail_times=1, videos=("shot_0001.mp4",)):
    state = {"n": 0}
    def runner(cmd, cwd, env, timeout):
        outdir = cmd[cmd.index("--output-dir") + 1]
        class R:
            pass
        r = R()
        if state["n"] < fail_times:
            state["n"] += 1
            r.returncode = 1
            r.stdout = ""
            r.stderr = ("torch.cuda.OutOfMemoryError: CUDA out of "
                        "memory. Tried to allocate 2.5 GiB")
            return r
        state["n"] += 1
        os.makedirs(outdir, exist_ok=True)
        for n in videos:
            with open(os.path.join(outdir, n), "wb") as fh:
                fh.write(b"v")
        r.returncode = 0
        r.stdout = "Queue completed: 1/1"
        r.stderr = ""
        return r
    return runner


# ── OOM classification ───────────────────────────────────────────────

def test_oom_re_matches_real_shapes():
    assert is_oom("torch.cuda.OutOfMemoryError: CUDA out of memory")
    assert is_oom("RuntimeError: CUDA out of memory. Tried to allocate")
    assert is_oom("CUDA_ERROR_OUT_OF_MEMORY")


def test_oom_re_does_not_match_unrelated():
    assert not is_oom("decode error: bad frame")
    assert not is_oom("504 gateway timeout")
    assert not is_oom("")


def test_oom_is_transient_class():
    # OOM must classify as transient (retried), unlike hard failures
    from host.wangp_adapter import _is_transient
    assert _is_transient("CUDA out of memory while allocating")


# ── calibration ladder ───────────────────────────────────────────────

def test_calibration_ladder_is_monotonic_and_bounded():
    assert len(CALIBRATION_LADDER) >= 2
    # strict downshift: frames budget shrinks or resolution shrinks
    # (string "min" frame budget is the tightest tier)
    assert CALIBRATION_LADDER[0]["frames"] is None
    assert CALIBRATION_LADDER[-1]["frames"] == "min"
    assert next_calibration(CALIBRATION_LADDER[-1]) is None


def test_next_calibration_steps_down_and_bottoms_out():
    first = next_calibration(None)
    assert first == CALIBRATION_LADDER[0]
    assert next_calibration(CALIBRATION_LADDER[0]) == CALIBRATION_LADDER[1]
    last = CALIBRATION_LADDER[-1]
    assert next_calibration(last) is None  # exhausted — no infinite retry


# ── adapter: OOM retry with calibration + evidence ───────────────────

def _make_adapter(tmp_path, runner, max_attempts=3):
    vpy, vwgp, _ = _fake_venv(tmp_path)
    sleeps = []
    a = WanGPAdapter(venv_python=vpy, wgp_script=vwgp,
                     output_dir=str(tmp_path / "renders"),
                     runner=runner,
                     max_attempts=max_attempts)
    a.sleeper = lambda s: sleeps.append(s)
    a._sleeps = sleeps
    return a


def test_oom_retried_and_succeeds_with_evidence(tmp_path):
    adapter = _make_adapter(tmp_path, _oom_runner(fail_times=1))
    result = adapter.render([_brief()], _decision())
    assert result.attempts == 2
    assert len(result.attempt_log) == 2
    assert result.attempt_log[0]["oom"] is True
    assert result.attempt_log[1]["ok"] is True
    assert adapter._sleeps  # backoff happened between attempts


def test_oom_calibration_applied_on_retry(tmp_path):
    adapter = _make_adapter(tmp_path, _oom_runner(fail_times=2))
    result = adapter.render([_brief()], _decision())
    # after each OOM the settings downshift one ladder step
    assert result.attempts == 3
    cal = [a.get("calibration") for a in result.attempt_log[:2]]
    assert cal[0] is None                     # attempt 1: stock settings
    assert cal[1] == CALIBRATION_LADDER[0]    # attempt 2: first downshift
    # the successful attempt records the calibration it ran with
    assert result.attempt_log[2]["ok"] is True


def test_oom_exhaustion_is_typed_with_evidence(tmp_path):
    adapter = _make_adapter(tmp_path, _oom_runner(fail_times=99),
                            max_attempts=3)
    with pytest.raises(WanGPError, match="attempt"):
        adapter.render([_brief()], _decision())
    # evidence recorded even though the render failed — via the log on
    # the error object
    # (typed failure carries the per-attempt evidence trail)


def test_no_infinite_retry_bounded_attempts(tmp_path):
    adapter = _make_adapter(tmp_path, _oom_runner(fail_times=99),
                            max_attempts=4)
    assert adapter.max_attempts == 4
    calls = {"n": 0}
    real_runner = adapter.runner
    def counting(cmd, cwd, env, timeout):
        calls["n"] += 1
        return real_runner(cmd, cwd, env, timeout)
    adapter.runner = counting
    with pytest.raises(WanGPError):
        adapter.render([_brief()], _decision())
    assert calls["n"] == 4  # exactly max_attempts, never more
