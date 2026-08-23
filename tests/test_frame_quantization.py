"""WD-u4rv RED tests: H3 frame quantization + readback verification.

Measured rule (3090 source + dogfood outputs, NOT guessed):
- Wan2GP/models/minimax_h3/minimax_h3_handler.py pins
  frames_minimum=107, frames_steps=17, frames_offset=5.
- normalize_frame_count (shared/utils/frame_scheduler.py) CEILs to
  5+17k; floor_frame_count rounds DOWN but line 6953 applies
  normalize (ceil) to the computed video length.
- Dogfood H3 outputs measured with ffprobe -count_frames: exactly
  107f, 124f, 175f (= 5+17k). 96f requests render as 107f on H3 —
  the adapter's 96f floor predates the H3 pin and now SNAPS UP to 107.
- Cycle-3 evidence: 160f requested -> 175f out ((160-5)/17=9.1 ->
  ceil k=10 -> 5+17*10=175).
"""
import pytest

from wangp_dspy.prompt_director import RenderBrief
from wangp_dspy.profile_selector import ProfileDecision
from wangp_dspy.wangp_adapter import (
    WanGPAdapter, WanGPError, build_settings, effective_frames_per_shot,
    normalize_frame_count,
)


def _brief():
    return RenderBrief(subject="astronaut, cracked visor",
                       motion="slow head turn", camera="dolly in",
                       style="16mm archival grain")


def _decision(frames):
    return ProfileDecision(model="h3", resolution="768p",
                           shot_length_frames=frames,
                           seed_policy="fixed_per_story",
                           wangp_profile="profile3")


# ── quantization helper math ───────────────────────────────────────

def test_normalize_math_matches_wgp_ceil():
    # grid: 5+17k, but CLAMPED to the H3 minimum of 107 (wgp
    # frame_scheduler: frame_count = max(minimum, frame_count) first)
    assert normalize_frame_count(5) == 107     # clamps up to minimum
    assert normalize_frame_count(22) == 107
    assert normalize_frame_count(96) == 107    # measured: H3 min
    assert normalize_frame_count(107) == 107   # already on-grid
    assert normalize_frame_count(160) == 175   # cycle-3 evidence
    assert normalize_frame_count(175) == 175
    assert normalize_frame_count(176) == 192   # 5+17*11
    assert normalize_frame_count(3) == 107


def test_effective_frames():
    assert effective_frames_per_shot(96) == 107
    assert effective_frames_per_shot(175) == 175


# ── build_settings validation ─────────────────────────────────────

def test_build_settings_snaps_offgrid_to_effective():
    # 96 passes the legacy 96f floor but is below the H3 minimum;
    # 110 is above-min but off-grid -> snaps UP to 124 (5+17*7)
    s = build_settings([_brief()], _decision(110))
    assert s["frames_per_shot"] == 124  # snapped to 5+17k grid


def test_build_settings_ongrid_unchanged():
    s = build_settings([_brief()], _decision(175))
    assert s["frames_per_shot"] == 175


def test_build_settings_rejects_below_h3_min():
    # below H3 min 107 but above the legacy 96 floor -> typed reject
    # (ProfileDecision itself rejects below 96 at construction)
    with pytest.raises(WanGPError, match="H3 minimum"):
        build_settings([_brief()], _decision(100))


# ── readback verification (fake ffprobe) ──────────────────────────

def _fake_venv(tmp_path):
    py = tmp_path / "wan2gp" / "venv" / "bin" / "python"
    py.parent.mkdir(parents=True, exist_ok=True)
    py.write_text("#!/bin/sh\n")
    py.chmod(0o755)
    wgp = tmp_path / "wan2gp" / "wgp.py"
    wgp.write_text("# wgp\n")
    return str(py), str(wgp)


def _mk_runner(frames_written, expected=None):
    def runner(cmd, cwd, env, timeout):
        import os
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
    runner.frames_written = frames_written
    return runner


def _ffprobe_factory(counts):
    """Fake host ffprobe: returns the given frame count per path."""
    def probe(path):
        return counts.get(path, 0)
    return probe


def test_readback_ok_when_frames_match(tmp_path, monkeypatch):
    vpy, vwgp = _fake_venv(tmp_path)
    adapter = WanGPAdapter(venv_python=vpy, wgp_script=vwgp,
                           output_dir=str(tmp_path / "renders"),
                           runner=_mk_runner(None))
    monkeypatch.setattr(
        WanGPAdapter, "_ffprobe_frames",
        staticmethod(lambda host, path: 107))
    result = adapter.render([_brief()], _decision(107))
    assert result.video_paths


def test_readback_raises_on_frame_mismatch(tmp_path, monkeypatch):
    """The live bug: 3 briefs x 175f expected = 525f, actual 172f."""
    vpy, vwgp = _fake_venv(tmp_path)
    adapter = WanGPAdapter(venv_python=vpy, wgp_script=vwgp,
                           output_dir=str(tmp_path / "renders"),
                           runner=_mk_runner(None))
    monkeypatch.setattr(
        WanGPAdapter, "_ffprobe_frames",
        staticmethod(lambda host, path: 172))
    with pytest.raises(WanGPError, match="525") as ei:
        adapter.render(
            [_brief(), _brief(), _brief()], _decision(175))
    assert "172" in str(ei.value)


def test_readback_tolerates_small_rounding(tmp_path, monkeypatch):
    vpy, vwgp = _fake_venv(tmp_path)
    adapter = WanGPAdapter(venv_python=vpy, wgp_script=vwgp,
                           output_dir=str(tmp_path / "renders"),
                           runner=_mk_runner(None))
    monkeypatch.setattr(
        WanGPAdapter, "_ffprobe_frames",
        staticmethod(lambda host, path: 175 - 1))  # 1 frame off: OK
    result = adapter.render([_brief()], _decision(175))
    assert result.video_paths


def test_readback_multiple_briefs_single_file(tmp_path, monkeypatch):
    """One output file for N briefs: expected = N * effective frames."""
    vpy, vwgp = _fake_venv(tmp_path)
    adapter = WanGPAdapter(venv_python=vpy, wgp_script=vwgp,
                           output_dir=str(tmp_path / "renders"),
                           runner=_mk_runner(None))
    monkeypatch.setattr(
        WanGPAdapter, "_ffprobe_frames",
        staticmethod(lambda host, path: 350))
    result = adapter.render([_brief(), _brief()], _decision(175))
    assert result.video_paths  # 2 x 175 = 350 exact: OK
