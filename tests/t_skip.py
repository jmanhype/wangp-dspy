"""WD-d3b9 RED tests: wgp exits 0 on skipped tasks ('Queue completed:
0/1 tasks (1 skipped)') — empty readback must be a typed WanGPError
with the stdout tail, never success-with-empty."""
import os

import pytest

from predict.prompt_director import RenderBrief
from predict.profile_selector import ProfileDecision
from host.wangp_adapter import WanGPAdapter, WanGPError


def _brief():
    return RenderBrief(subject="astronaut, cracked visor",
                       motion="slow head turn", camera="dolly in",
                       style="16mm archival grain")


def _decision():
    return ProfileDecision(model="h3", resolution="768p",
                           shot_length_frames=96,
                           seed_policy="fixed_per_story",
                           wangp_profile="profile3")


def _fake_venv(tmp_path):
    py = tmp_path / "wan2gp" / "venv" / "bin" / "python"
    py.parent.mkdir(parents=True, exist_ok=True)
    py.write_text("#!/bin/sh\n")
    py.chmod(0o755)
    wgp = tmp_path / "wan2gp" / "wgp.py"
    wgp.write_text("# wgp\n")
    return str(py), str(wgp)


def _skip_runner(stdout="Queue completed: 0/1 tasks (1 skipped)"):
    def runner(cmd, cwd, env, timeout):
        class R:
            pass
        r = R()
        r.returncode = 0
        r.stdout = stdout
        r.stderr = ""
        return r
    return runner


def test_exit0_skipped_task_raises_typed_error(tmp_path):
    vpy, vwgp = _fake_venv(tmp_path)
    adapter = WanGPAdapter(venv_python=vpy, wgp_script=vwgp,
                           output_dir=str(tmp_path / "renders"),
                           runner=_skip_runner())
    with pytest.raises(WanGPError, match="skipped"):
        adapter.render([_brief()], _decision())


def test_error_carries_stdout_tail(tmp_path):
    vpy, vwgp = _fake_venv(tmp_path)
    adapter = WanGPAdapter(venv_python=vpy, wgp_script=vwgp,
                           output_dir=str(tmp_path / "renders"),
                           runner=_skip_runner(
                               "line1\nline2\nQueue completed: 0/1 "
                               "tasks (1 skipped)\n"))
    with pytest.raises(WanGPError, match="Queue completed"):
        adapter.render([_brief()], _decision())


def test_exit0_with_real_video_still_succeeds(tmp_path):
    """rc 0 + produced file = success; the guard only fires on EMPTY
    readback."""
    vpy, vwgp = _fake_venv(tmp_path)

    def runner(cmd, cwd, env, timeout):
        outdir = cmd[cmd.index("--output-dir") + 1]
        with open(os.path.join(outdir, "shot.mp4"), "wb") as fh:
            fh.write(b"v")

        class R:
            returncode = 0
            stdout = "Queue completed: 1/1 tasks"
            stderr = ""
        return R()

    adapter = WanGPAdapter(venv_python=vpy, wgp_script=vwgp,
                           output_dir=str(tmp_path / "renders"),
                           runner=runner)
    result = adapter.render([_brief()], _decision())
    assert result.video_paths and result.video_paths[0].endswith(".mp4")
