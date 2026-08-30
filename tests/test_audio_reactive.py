"""Closure 2 — artifact-grounded audio-reactive evaluation lane.

RED-first tests for evaluate/audio_reactive.py. No GPU, no render, no
model calls: judge is injected; artifacts are tiny fixture files.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from evaluate.audio_reactive import (
    AudioReactiveEvalError,
    AudioReactiveInput,
    compare_audio_reactive,
    evaluate_audio_artifact,
)
from predict.audio_manifest import write_audio_manifest
from predict.audio_dataplane import AudioPolicy

def _settings_doc(tmp_path: Path, *, discard: bool = True) -> dict:
    master = tmp_path / "master.wav"
    master.write_bytes(b"master-bytes")
    return {
        "script": "ignored-by-manifest",
        "audio_guide": {"track": "keeper-mix-01"},
        "audio_provenance": {
            "source_master": str(master),
            "vocal_stem": str(master),
            "whisper_map": str(master),
            "keeper_window_s": [0.0, 4.0],
        },
        "audio_policy": {
            "discard_rendered_audio": discard,
            "remux_source": "source_master",
        },
        "audio_qc": {"critic_model": "Qwen2-Audio-7B"},
    }


def _artifact(tmp_path: Path, *, with_manifest: bool = True,
              judged: bool = False, discard: bool = True) -> AudioReactiveInput:
    tmp_path = Path(tmp_path)
    tmp_path.mkdir(parents=True, exist_ok=True)
    art = tmp_path / "art"
    art.mkdir(exist_ok=True)
    render = art / "render.mp4"
    render.write_bytes(b"fake-render-bytes")  # fixture file, not a render
    doc = _settings_doc(tmp_path, discard=discard)
    settings = art / "settings.json"
    settings.write_text(json.dumps(doc), encoding="utf-8")
    if with_manifest:
        write_audio_manifest(doc, render)
    remux = art / "remux.mp4"
    remux.write_bytes(b"fake-remux-bytes")
    return AudioReactiveInput(
        render_path=render,
        settings_path=settings,
        remux_path=remux,
        audio_source=doc["audio_provenance"],
        candidate_label="cand",
        seed=7,
    )


def _judge(scores=(8.0, 9.0, 7.5, 8.5)):
    def j(*, settings_doc):
        return dict(zip(
            ("mouth_sync", "audio_fidelity",
             "visual_motion_match", "audio_artifacts"), scores))
    return j


# ---- rejections -------------------------------------------------------

def test_manifest_missing_rejected(tmp_path):
    art = _artifact(tmp_path, with_manifest=False)
    with pytest.raises(AudioReactiveEvalError, match="manifest"):
        evaluate_audio_artifact(art, judge=None)


def test_manifest_mismatch_rejected(tmp_path):
    art = _artifact(tmp_path)
    # tamper the sidecar after write
    p = art.render_path.parent / "audio_manifest.json"
    m = json.loads(p.read_text())
    m["audio_guide"]["track"] = "tampered"
    p.write_text(json.dumps(m))
    with pytest.raises(AudioReactiveEvalError, match="readback mismatch"):
        evaluate_audio_artifact(art, judge=None)


def test_missing_render_rejected(tmp_path):
    art = _artifact(tmp_path)
    art.render_path.unlink()
    with pytest.raises(AudioReactiveEvalError, match="render"):
        evaluate_audio_artifact(art, judge=None)


def test_g4_violation_rejected(tmp_path):
    art = _artifact(tmp_path, discard=False)
    with pytest.raises(AudioReactiveEvalError, match="G4"):
        evaluate_audio_artifact(art, judge=None)


# ---- unjudged honesty -------------------------------------------------

def test_unjudged_not_gepa_eligible(tmp_path):
    art = _artifact(tmp_path)
    res = evaluate_audio_artifact(art, judge=None)
    assert res["eligible_for_qc"] is False
    assert res["eligible_for_gepa"] is False
    assert res["qc"]["critic_model"] == "Qwen2-Audio-7B"
    assert res["qc"]["mouth_sync"] is None
    d = json.dumps(res)  # JSON-serializable, deterministic
    assert json.loads(d) == res


def test_judged_with_remux_eligible(tmp_path):
    art = _artifact(tmp_path)
    res = evaluate_audio_artifact(art, judge=_judge())
    assert res["eligible_for_qc"] is True
    assert res["eligible_for_gepa"] is True
    assert res["target_qc_score"] == pytest.approx(8.25)


def test_judged_without_remux_not_eligible(tmp_path):
    art = _artifact(tmp_path)
    art.remux_path.unlink()
    res = evaluate_audio_artifact(art, judge=_judge())
    assert res["eligible_for_qc"] is False
    assert res["eligible_for_gepa"] is False
    assert "remux" in res["reason"].lower()


# ---- hashes are real --------------------------------------------------

def test_hashes_are_real_sha256(tmp_path):
    art = _artifact(tmp_path)
    res = evaluate_audio_artifact(art, judge=None)
    sha = lambda b: hashlib.sha256(b).hexdigest()
    assert res["artifact_hashes"]["render"] == sha(b"fake-render-bytes")
    assert res["artifact_hashes"]["remux"] == sha(b"fake-remux-bytes")
    man = (art.render_path.parent / "audio_manifest.json").read_bytes()
    assert res["manifest_hash"] == sha(man)
    assert len(res["manifest_hash"]) == 64


# ---- comparison -------------------------------------------------------

def _judged_record(tmp_path, label, score):
    art = _artifact(tmp_path / label)
    return evaluate_audio_artifact(
        art, judge=_judge(scores=(score, score, score, score)))


def test_compare_judged_deterministic(tmp_path):
    a = _judged_record(tmp_path, "base", 7.0)
    b = _judged_record(tmp_path, "chal", 8.0)
    r1 = compare_audio_reactive(a, b)
    r2 = compare_audio_reactive(a, b)
    assert r1 == r2
    assert r1["decision"] == "challenger"
    # flipped
    assert compare_audio_reactive(b, a)["decision"] == "baseline"


def test_compare_requires_eligibility(tmp_path):
    a = _judged_record(tmp_path, "base", 7.0)
    un = evaluate_audio_artifact(_artifact(tmp_path / "un"), judge=None)
    with pytest.raises(AudioReactiveEvalError, match="eligible"):
        compare_audio_reactive(a, un)


def test_compare_rejects_text_only_scores(tmp_path):
    a = _judged_record(tmp_path, "base", 7.0)
    bad = dict(_judged_record(tmp_path, "chal", 8.0))
    bad["target_qc_score"] = "eight"
    with pytest.raises(AudioReactiveEvalError, match="numeric"):
        compare_audio_reactive(a, bad)


def test_compare_rejects_increased_gate_failures(tmp_path):
    a = _judged_record(tmp_path, "base", 7.0)
    b = _judged_record(tmp_path, "chal", 8.0)
    b["gate_failures"] = 1
    with pytest.raises(AudioReactiveEvalError, match="gate failure"):
        compare_audio_reactive(a, b)


# ---- preservation -----------------------------------------------------

def test_generic_lanes_unchanged():
    import training.run_baseline_then_gepa as m
    src = Path(m.__file__).read_text()
    assert "audio_reactive" not in src
    import metrics.qc_feedback  # noqa: F401 generic lane still imports
    import evaluate.render_qc  # noqa: F401
    src_qc = Path(evaluate.render_qc.__file__).read_text()
    src_m = Path(metrics.qc_feedback.__file__).read_text()
    assert "audio_reactive" not in src_qc
    assert "audio_reactive" not in src_m
