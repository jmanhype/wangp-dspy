"""WD-5zti RED tests: wgp ignores --output-dir; readback must scan the
wgp outputs dir (<wgp_root>/outputs/ by default, constructor param)."""
import os

import pytest

from wangp_dspy.prompt_director import RenderBrief
from wangp_dspy.profile_selector import ProfileDecision
from wangp_dspy.wangp_adapter import WanGPAdapter, WanGPError


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
    return str(py), str(wgp), tmp_path / "wan2gp"


def test_readback_finds_video_in_wgp_outputs_dir(tmp_path):
    """Real behavior: wgp IGNORES --output-dir and writes into
    <wgp_root>/outputs/. A fake wgp emulating that proves the readback
    must scan the outputs dir (mtime-newest first)."""
    vpy, vwgp, wgp_root = _fake_venv(tmp_path)
    seen = {}

    def runner(cmd, cwd, env, timeout):
        seen["output_dir_arg"] = cmd[cmd.index("--output-dir") + 1]
        # wgp writes to its OWN outputs dir regardless
        out = os.path.join(str(wgp_root), "outputs")
        os.makedirs(out, exist_ok=True)
        with open(os.path.join(out, "shot_0001.mp4"), "wb") as fh:
            fh.write(b"v")

        class R:
            returncode = 0
            stdout = ""
            stderr = ""
        return R()

    adapter = WanGPAdapter(venv_python=vpy, wgp_script=vwgp,
                           output_dir=str(tmp_path / "renders"),
                           runner=runner)
    result = adapter.render([_brief()], _decision())
    assert len(result.video_paths) == 1
    assert result.video_paths[0].endswith("shot_0001.mp4")
    assert os.path.isfile(result.video_paths[0])
    # --output-dir stays in the argv (harmless, keeps future wgp honest)
    assert seen["output_dir_arg"].startswith(str(tmp_path / "renders"))


def test_outputs_dir_is_constructor_param(tmp_path):
    vpy, vwgp, wgp_root = _fake_venv(tmp_path)
    custom = tmp_path / "custom-outputs"
    custom.mkdir()

    def runner(cmd, cwd, env, timeout):
        with open(os.path.join(str(custom), "a.mp4"), "wb") as fh:
            fh.write(b"v")

        class R:
            returncode = 0
            stdout = ""
            stderr = ""
        return R()

    adapter = WanGPAdapter(venv_python=vpy, wgp_script=vwgp,
                           output_dir=str(tmp_path / "renders"),
                           wgp_outputs_dir=str(custom), runner=runner)
    result = adapter.render([_brief()], _decision())
    assert result.video_paths[0] == str(custom / "a.mp4")
