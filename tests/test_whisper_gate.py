import inspect
import json
import pathlib

import pytest

from qc.audio_critic.ref2va_stage import (
    Ref2VAQCStageError, run_ref2va_qc_stage,
)
from qc.audio_critic.whisper_gate import (
    DEFAULT_WHISPER_PASS_BAR, WhisperGateError, run_whisper_gate,
)
from predict.vibevoice import supply_vibevoice_turns, supply_vibevoice_turns_remote


def _doc(tmp_path):
    paths = []
    for name in ("guide.wav", "master.wav", "stem.wav", "map.json"):
        p = pathlib.Path(tmp_path) / name
        p.write_bytes(b"x")
        paths.append(str(p))
    return {
        "audio_guide": paths[0],
        "audio_provenance": {
            "source_master": paths[1], "vocal_stem": paths[2],
            "whisper_map": paths[3], "keeper_window_s": [0.0, 2.0],
        },
        "audio_policy": {"discard_rendered_audio": True},
    }


def test_whisper_gate_records_phase_and_score():
    evidence = run_whisper_gate(
        "/tmp/turn.wav", "No, the gate is open", phase="pre",
        transcriber=lambda _: {"text": "No the gate is open"})
    assert evidence.passed is True
    assert evidence.phase == "pre"
    assert evidence.score == 1.0


def test_whisper_gate_rejects_mismatch():
    with pytest.raises(WhisperGateError, match="below pass bar") as caught:
        run_whisper_gate(
            "/tmp/turn.wav", "the gate is open", phase="post",
            transcriber=lambda _: "unrelated words")
    assert caught.value.evidence.to_dict() == {
        "phase": "post", "audio_path": "/tmp/turn.wav",
        "intended_text": "the gate is open", "transcript": "unrelated words",
        "score": 0.0, "pass_bar": DEFAULT_WHISPER_PASS_BAR, "passed": False,
    }


def test_default_whisper_pass_bar_is_production_strict():
    assert DEFAULT_WHISPER_PASS_BAR == 0.6


def test_vibevoice_suppliers_use_the_gate_default():
    for function in (run_whisper_gate, supply_vibevoice_turns,
                     supply_vibevoice_turns_remote):
        default = inspect.signature(function).parameters["pass_bar"].default
        assert default is DEFAULT_WHISPER_PASS_BAR


def test_whisper_gate_transport_failure_does_not_fabricate_evidence():
    def failed(_):
        raise RuntimeError("unavailable")
    with pytest.raises(WhisperGateError) as caught:
        run_whisper_gate("a.wav", "hello", phase="pre", transcriber=failed)
    assert caught.value.evidence is None


def test_qc_stage_runs_both_gates_and_persists_evidence(tmp_path):
    doc = _doc(tmp_path)
    evidence_path = pathlib.Path(tmp_path) / "qc" / "whisper.json"
    qc = run_ref2va_qc_stage(
        doc, judge=None, pre_audio_path="pre.wav", post_audio_path="post.wav",
        intended_text="The gate is open", whisper_transcriber=lambda _: {
            "text": "the gate is open"}, evidence_path=str(evidence_path))
    assert qc.whisper_gates["pre"]["passed"] is True
    assert qc.whisper_gates["post"]["phase"] == "post"
    payload = json.loads(evidence_path.read_text())
    assert payload["whisper_gates"]["pre"]["score"] == 1.0


def test_qc_stage_persists_scored_post_rejection_evidence(tmp_path):
    doc = _doc(tmp_path)
    evidence_path = pathlib.Path(tmp_path) / "qc" / "whisper.json"

    def transcriber(path):
        if pathlib.Path(path).name == "pre.wav":
            return "the gate is open"
        return "unrelated mountain"

    with pytest.raises(Ref2VAQCStageError) as caught:
        run_ref2va_qc_stage(
            doc, judge=None, pre_audio_path="pre.wav",
            post_audio_path="post.wav", intended_text="the gate is open",
            whisper_transcriber=transcriber,
            evidence_path=str(evidence_path))

    assert caught.value.whisper_evidence["pre"]["passed"] is True
    assert caught.value.whisper_evidence["post"]["passed"] is False
    payload = json.loads(evidence_path.read_text())
    assert payload["whisper_gates"]["pre"]["score"] == 1.0
    assert payload["whisper_gates"]["post"]["transcript"] == "unrelated mountain"
    assert payload["whisper_gates"]["post"]["passed"] is False


def test_qc_stage_requires_complete_pre_post_gate_inputs(tmp_path):
    with pytest.raises(Ref2VAQCStageError, match="pre_audio_path"):
        run_ref2va_qc_stage(
            _doc(tmp_path), judge=None, pre_audio_path="pre.wav",
            intended_text="line", whisper_transcriber=lambda _: "line")
