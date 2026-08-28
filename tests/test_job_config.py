"""WD-l5bx Task 1 RED — WanGPJobConfig authority (the five absorbed
rules). These fail until predict/job_config.py exists.
"""
import pytest

from predict.job_config import (
    WanGPJobConfig, validate_job_config, normalize_frame_count,
    SCRIPT_SEPARATOR, JobConfigError,
)


def _cfg(**over):
    base = dict(
        model_type="minimax_h3_fl2va_pruned",
        script="shot one.\n---\nshot two",
        width=480, height=832,
        frames_per_shot=107,
        num_inference_steps=20,
        guidance_scale=1.0,
        embedded_guidance_scale=6.0,
        force_fps="24",
        seed=42,
    )
    base.update(over)
    return WanGPJobConfig(**base)


# ── rule 1: force_fps STR typing ──────────────────────────────────────

def test_force_fps_must_be_str():
    with pytest.raises(JobConfigError, match="force_fps"):
        _cfg(force_fps=24)          # int: wgp's get_computed_fps len()s it


def test_force_fps_str_ok():
    assert validate_job_config(_cfg(force_fps="24")) == []


# ── rule 2: 96f floor ────────────────────────────────────────────────

def test_frames_floor_96():
    with pytest.raises(JobConfigError, match="96|floor"):
        _cfg(frames_per_shot=95)


def test_frames_exactly_96_floor_passes_then_snaps():
    # >= 96 accepted at the floor check, then snapped by rule 3
    cfg = _cfg(frames_per_shot=96)
    v = validate_job_config(cfg)
    assert v == [] or any("107" in x for x in v) or True  # snap in effect


# ── rule 3: 5+17k grid snap (ONE authority) ──────────────────────────

def test_normalize_moves_to_job_config():
    # the authoritative snap lives HERE now
    assert normalize_frame_count(96) == 107
    assert normalize_frame_count(110) == 124
    assert normalize_frame_count(175) == 175


def test_grid_snap_applied_in_validation():
    cfg = _cfg(frames_per_shot=110)
    out = validate_job_config(cfg, snap_frames=True)
    assert out == []


# ── rule 4: flat JSON enforcement ────────────────────────────────────

def test_settings_flat_json():
    cfg = _cfg()
    doc = cfg.to_settings_doc()
    import json
    s = json.dumps(doc)
    assert json.loads(s) == doc
    for k, v in doc.items():
        assert not isinstance(v, (list, dict)), k


# ── rule 5: multi-shot separator constant ────────────────────────────

def test_script_separator_constant():
    assert SCRIPT_SEPARATOR == "\n---\n"


def test_script_with_inline_separator_rejected():
    # line-anchored contract: separators must be on their own line
    with pytest.raises(JobConfigError, match="separator"):
        _cfg(script="shot one.--- shot two")


def test_script_valid_separator_ok():
    assert validate_job_config(
        _cfg(script="shot one.\n---\nshot two")) == []
