"""WD-a1d9 RED — Ref2VA audio data plane: provenance + policy + QC.

Fails until predict/audio_dataplane.py exists. Spec:
docs/specs/s2-ref2va-audio-dataplane.md
"""
import dataclasses
import json
import pathlib

import pytest

from predict.audio_dataplane import (
    AudioDataPlaneError,
    AudioGuideProvenance,
    AudioPolicy,
    Ref2VAAudioQC,
)


def _files(tmp_path, n=3):
    """Create n readable files, return (master, stem, whisper_map)."""
    names = ["master.wav", "vocal.wav", "whisper.json"]
    paths = []
    for i in range(n):
        f = pathlib.Path(tmp_path) / names[i]
        f.write_bytes(b"x" * 8)
        paths.append(str(f))
    return tuple(paths)


def _prov(tmp_path, **over):
    master, stem, wmap = _files(tmp_path)
    d = dict(source_master=master, vocal_stem=stem, whisper_map=wmap,
             keeper_window_s=(1.0, 5.0))
    d.update(over)
    return AudioGuideProvenance(**d)


# ── AudioGuideProvenance ────────────────────────────────────────────

def test_provenance_valid(tmp_path):
    p = _prov(tmp_path)
    assert p.keeper_window_s == (1.0, 5.0)
    assert p.source_master.endswith("master.wav")


def test_provenance_missing_master_rejected(tmp_path):
    with pytest.raises(AudioDataPlaneError, match="source_master"):
        _prov(tmp_path, source_master="/nonexistent/master.wav")


def test_provenance_missing_stem_rejected(tmp_path):
    with pytest.raises(AudioDataPlaneError, match="vocal_stem"):
        _prov(tmp_path, vocal_stem="/nonexistent/vocal.wav")


def test_provenance_missing_whisper_map_rejected(tmp_path):
    with pytest.raises(AudioDataPlaneError, match="whisper_map"):
        _prov(tmp_path, whisper_map="/nonexistent/wmap.json")


def test_provenance_window_end_le_start_rejected(tmp_path):
    with pytest.raises(AudioDataPlaneError, match="keeper_window"):
        _prov(tmp_path, keeper_window_s=(5.0, 5.0))


def test_provenance_window_end_lt_start_rejected(tmp_path):
    with pytest.raises(AudioDataPlaneError, match="keeper_window"):
        _prov(tmp_path, keeper_window_s=(6.0, 5.0))


def test_provenance_negative_start_rejected(tmp_path):
    with pytest.raises(AudioDataPlaneError, match="keeper_window"):
        _prov(tmp_path, keeper_window_s=(-1.0, 5.0))


def test_provenance_zero_start_ok_master_duration_unchecked(tmp_path):
    """Start 0 is fine; master duration is NOT checkable offline, so
    end beyond master length cannot be rejected — documented in spec."""
    p = _prov(tmp_path, keeper_window_s=(0.0, 5.0))
    assert p.keeper_window_s == (0.0, 5.0)


# ── AudioPolicy ─────────────────────────────────────────────────────

def test_policy_defaults():
    pol = AudioPolicy(remux_window=(1.0, 5.0))
    assert pol.discard_rendered_audio is True
    assert pol.remux_source == "source_master"


def test_policy_rejects_bad_remux_source():
    with pytest.raises(AudioDataPlaneError, match="remux_source"):
        AudioPolicy(remux_source="gibberish", remux_window=(0.0, 1.0))


def test_policy_accepts_both_enum_values():
    for src in ("source_master", "vocal_stem"):
        assert AudioPolicy(
            remux_source=src, remux_window=(0.0, 1.0)).remux_source == src


def test_policy_to_dict():
    pol = AudioPolicy(remux_window=(1.0, 5.0))
    d = pol.to_dict()
    assert d == {"discard_rendered_audio": True,
                 "remux_source": "source_master",
                 "remux_window": [1.0, 5.0]}


# ── Ref2VAAudioQC ───────────────────────────────────────────────────

def test_qc_empty_default_critic_model():
    qc = Ref2VAAudioQC.empty()
    assert qc.critic_model == "Qwen2-Audio-7B"
    assert qc.critic_version is None
    assert qc.mouth_sync is None
    assert qc.notes == ""


def test_qc_to_dict_round_trip():
    qc = Ref2VAAudioQC(
        critic_version="v1", mouth_sync=8.5, audio_fidelity=7.0,
        visual_motion_match=6.5, audio_artifacts=3.0, notes="solid")
    d = qc.to_dict()
    assert json.dumps(d)  # JSON-serializable
    rt = Ref2VAAudioQC.from_dict(d)
    assert rt == qc


def test_qc_none_scores_allowed():
    qc = Ref2VAAudioQC.empty()
    d = qc.to_dict()
    assert d["mouth_sync"] is None  # not yet judged
    assert Ref2VAAudioQC.from_dict(d) == qc


def test_qc_score_bounds():
    with pytest.raises(AudioDataPlaneError, match="mouth_sync"):
        Ref2VAAudioQC(mouth_sync=11.0)
    with pytest.raises(AudioDataPlaneError, match="audio_fidelity"):
        Ref2VAAudioQC(audio_fidelity=-0.5)
