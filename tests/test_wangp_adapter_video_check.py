"""Luna delta: video path must exist before QC judges it."""
import os

import pytest

from wangp_dspy.prompt_director import RenderBrief
from wangp_dspy.profile_selector import ProfileDecision
from wangp_dspy.render_qc import QCVerdict, Verdict
from wangp_dspy.wangp_adapter import WanGPAdapter, WanGPError


def _brief(subject="astronaut, cracked visor"):
    return RenderBrief(subject=subject, motion="slow head turn",
                       camera="dolly in", style="16mm archival grain")


def _decision():
    return ProfileDecision(model="h3", resolution="768p",
                           shot_length_frames=176,
                           seed_policy="fixed_per_story",
                           wangp_profile="profile3")


def _fake_venv(tmp_path):
    py = tmp_path / "venv" / "bin" / "python"
    py.parent.mkdir(parents=True, exist_ok=True)
    py.write_text("#!/bin/sh\n")
    py.chmod(0o755)
    wgp = tmp_path / "wgp.py"
    wgp.write_text("# wgp\n")
    return str(py), str(wgp)


class _Stub:
    def assemble(self, plans):
        raise AssertionError("should not reach assembler")


def test_qc_not_called_and_typed_error_when_video_missing(tmp_path):
    """run_pipeline must pre-check the readback video exists; a missing
    file is a typed failure, never silently text-only critiqued."""
    from wangp_dspy.assembler import ShotPlan

    def runner(cmd, cwd, env, timeout):
        # succeeds but produces NO video files
        class R:
            returncode = 0
            stdout = ""
            stderr = ""
        return R()

    qc_calls = {"n": 0}

    class TrapQC:
        def __init__(self, genre):
            pass

        def run(self, *a, **kw):
            qc_calls["n"] += 1
            return QCVerdict(verdict=Verdict.PASS, reason="x", scores={})

    vpy, vwgp = _fake_venv(tmp_path)
    adapter = WanGPAdapter(venv_python=vpy, wgp_script=vwgp,
                           output_dir=str(tmp_path), runner=runner,
                           qc_factory=TrapQC, assembler=_Stub())
    plans = [ShotPlan(brief=_brief(), decision=_decision(),
                      terminal_state="astronaut done")]
    # genuine Luna case: readback produced a path, but the file does not
    # exist on disk — QC must never be invoked on it
    from wangp_dspy.wangp_adapter import RenderResult
    adapter.render = lambda briefs, decision: RenderResult(
        attempts=1, settings_path="/dev/null", output_dir=str(tmp_path),
        video_paths=(str(tmp_path / "phantom.mp4"),))
    with pytest.raises(WanGPError, match="video"):
        adapter.run_pipeline(plans, genre="surreal")
    assert qc_calls["n"] == 0, "QC must never see a missing file"
