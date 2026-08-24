"""WD-tc04 RED tests: seam-aware frame tolerance + ssh recovery.

Live evidence (WD-izly payoff render): 470f actual vs 474f expected
(3 shots / 2 concat seams -> ~2 frames lost per seam). And a live
wedge: remote wgp completed but the ssh channel child hung silently —
no pull, ~25min blocked, manual scp recovery.
"""
import os

import pytest

from prompt_director import RenderBrief
from profile_selector import ProfileDecision
from render_host import SshHost
from wangp_adapter import (
    WanGPAdapter, WanGPError, frame_tolerance,
)


def _brief(subject="shot"):
    return RenderBrief(subject=subject, motion="turn", camera="dolly",
                       style="grain")


def _decision():
    return ProfileDecision(model="h3", resolution="768p",
                           shot_length_frames=175,
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


# ── 1. seam-aware tolerance math ──────────────────────────────────

def test_frame_tolerance_scales_with_seams():
    # WD-qn1a recalibration: 2 base (fps rounding) + ceiling 3 per
    # seam. Old linear-2 values fired on a GOOD cycle-4 render
    # (diff 8 == tolerance(4)); measurements are superlinear
    # (n=3 diff 4, n=4 diff 8). See test_seam_tolerance_recalibrate.
    assert frame_tolerance(1) == 2
    assert frame_tolerance(2) == 5
    assert frame_tolerance(3) == 8   # 2 base + 2 seams * 3
    assert frame_tolerance(5) == 14


def test_live_payoff_case_no_longer_flags(tmp_path, monkeypatch):
    """470f vs 474f expected (3x175=525? no — 474 total): must PASS.
    Constructed: 3 briefs, ffprobe returns want - 4."""
    vpy, vwgp = _fake_venv(tmp_path)
    adapter = WanGPAdapter(venv_python=vpy, wgp_script=vwgp,
                           output_dir=str(tmp_path / "renders"))

    def runner(cmd, cwd, env, timeout):
        outdir = cmd[cmd.index("--output-dir") + 1]
        os.makedirs(outdir, exist_ok=True)
        with open(os.path.join(outdir, "shot.mp4"), "wb") as fh:
            fh.write(b"v")

        class R:
            pass
        r = R()
        r.returncode = 0
        r.stdout = "Queue completed: 1/1"
        r.stderr = ""
        return r

    adapter.runner = runner
    # the actual live numbers: 3 shots, 2 seams -> ~2f lost per seam.
    # (Live was 474 expected / 470 got with effective ~158f shots;
    # here effective frames are 175, so seam loss scales the same.)
    from wangp_adapter import effective_frames_per_shot
    want = 3 * effective_frames_per_shot(175)
    monkeypatch.setattr(
        WanGPAdapter, "_ffprobe_frames",
        staticmethod(lambda host, path: want - 4))
    result = adapter.render([_brief(), _brief(), _brief()],
                            _decision())
    assert result.video_paths


def test_live_cycle3_bug_still_trips(tmp_path, monkeypatch):
    """525 expected vs 172 actual (diff 353 >= tolerance(3)=6): the
    original live bug must STILL be a typed error."""
    vpy, vwgp = _fake_venv(tmp_path)

    def runner(cmd, cwd, env, timeout):
        outdir = cmd[cmd.index("--output-dir") + 1]
        os.makedirs(outdir, exist_ok=True)
        with open(os.path.join(outdir, "shot.mp4"), "wb") as fh:
            fh.write(b"v")

        class R:
            pass
        r = R()
        r.returncode = 0
        r.stdout = "Queue completed: 1/1"
        r.stderr = ""
        return r

    adapter = WanGPAdapter(venv_python=vpy, wgp_script=vwgp,
                           output_dir=str(tmp_path / "renders"),
                           runner=runner)
    monkeypatch.setattr(
        WanGPAdapter, "_ffprobe_frames",
        staticmethod(lambda host, path: 172))
    with pytest.raises(WanGPError, match="mismatch"):
        adapter.render([_brief(), _brief(), _brief()], _decision())


# ── 2. ssh keepalive options ─────────────────────────────────────

def test_ssh_argv_contains_keepalive_options(tmp_path):
    """Dead ssh channels must drop within ~5min so the pull retry can
    take over: ServerAliveInterval=30, CountMax=10, ConnectTimeout=15."""
    captured = {}

    class FakeSP:
        def __call__(self, argv, **kw):
            captured["argv"] = list(argv)

            class P:
                returncode = 0

                def communicate(self, timeout=None):
                    return (b"", b"")

                def kill(self):
                    pass

                def wait(self):
                    pass
            return P()

    host = SshHost(target="gpu3090", wgp_root="/w",
                   pull_root=str(tmp_path), sp=FakeSP())
    host.check_executable("/w/venv/bin/python")
    argv = captured["argv"]
    assert "-o" in argv
    assert "ServerAliveInterval=30" in argv
    assert "ServerAliveCountMax=10" in argv
    assert "ConnectTimeout=15" in argv


# ── 3. pull retry after channel wedge ────────────────────────────

def test_pull_retry_when_first_fetch_empty(tmp_path, monkeypatch):
    """The live wedge: command returns, first pull sees nothing, but a
    fresh remote output exists. The adapter must retry the pull once
    instead of failing."""
    vpy, vwgp = _fake_venv(tmp_path)

    def runner(cmd, cwd, env, timeout):
        outdir = cmd[cmd.index("--output-dir") + 1]
        os.makedirs(outdir, exist_ok=True)
        with open(os.path.join(outdir, "shot.mp4"), "wb") as fh:
            fh.write(b"v")

        class R:
            pass
        r = R()
        r.returncode = 0
        r.stdout = "Queue completed: 1/1"
        r.stderr = ""
        return r

    calls = {"n": 0}

    class WedgedThenOkHost:
        """First fetch returns nothing; retry materializes the file."""

        def __getattr__(self, name):
            # delegate everything else to a LocalHost-like default
            from render_host import LocalHost
            return getattr(LocalHost(), name)

        def check_executable(self, path):
            return None

        def makedirs(self, path):
            return None

        def join(self, *parts):
            return os.path.join(*parts)

        def prepare_run(self, wgp_script):
            return ".", {}

        def run(self, cmd, cwd, env, timeout, runner=None):
            return runner(cmd, cwd, env, timeout)

        def write_text(self, path, text):
            return path

        def fetch_videos(self, dirs, local_dir, newer_than):
            calls["n"] += 1
            if calls["n"] == 1:
                return ()          # wedge: pull saw nothing
            outdir = None
            for d in dirs:
                if os.path.isdir(d):
                    outdir = d
            if outdir:
                for n in os.listdir(outdir):
                    if n.endswith(".mp4"):
                        return (os.path.join(outdir, n),)
            return ()

    monkeypatch.setattr(
        WanGPAdapter, "_ffprobe_frames",
        staticmethod(lambda host, path: -1))  # unverified sentinel
    adapter = WanGPAdapter(venv_python=vpy, wgp_script=vwgp,
                           output_dir=str(tmp_path / "renders"),
                           runner=runner)
    adapter.host = WedgedThenOkHost()
    result = adapter.render([_brief()], _decision())
    assert calls["n"] == 2          # retried exactly once
    assert result.video_paths       # and recovered the file
