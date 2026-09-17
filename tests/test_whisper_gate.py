import json
import pathlib

import pytest

from qc.audio_critic.ref2va_stage import (
    Ref2VAQCStageError, run_ref2va_qc_stage,
)
from qc.audio_critic.whisper_gate import (
    WhisperGateError, run_whisper_gate,
)


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
        "score": 0.0, "pass_bar": 0.5, "passed": False,
    }


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


def test_qc_stage_requires_complete_pre_post_gate_inputs(tmp_path):
    with pytest.raises(Ref2VAQCStageError, match="pre_audio_path"):
        run_ref2va_qc_stage(
            _doc(tmp_path), judge=None, pre_audio_path="pre.wav",
            intended_text="line", whisper_transcriber=lambda _: "line")
