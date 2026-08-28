"""S2 diarization consumption surface (WD-j9nx/S2).

The repo CONSUMES out-of-repo speaker-diarization output: versioned
JSON timeline schema + deterministic validator (typed per-rule
rejections naming R1-R6) + deterministic conversion to <d>Name</d>
speaker-attribution blocks (G5-compatible shape, feeds S3's <d> gate).

Binding constraint: faster-whisper / pyannote NEVER appear in repo
code paths. This module imports neither; it is pure dict logic.

ZERO-MODEL, deterministic: same input bytes -> same output bytes.
"""
from __future__ import annotations

import math
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from predict.diarization import (  # noqa: E402
    DIARIZATION_SCHEMA_VERSION, DiarizationError, SpeakerBlock,
    diarization_to_speaker_blocks, render_attribution,
    validate_diarization,
)


def _doc(**kw):
    """A valid minimal doc; override fields per test."""
    base = {
        "schema_version": 1,
        "audio_sha256": "a" * 64,
        "duration_sec": 10.0,
        "speakers": ["SPEAKER_00", "SPEAKER_01"],
        "segments": [
            {"start": 0.0, "end": 3.2, "speaker": "SPEAKER_00",
             "text": "hello"},
            {"start": 3.5, "end": 6.0, "speaker": "SPEAKER_01"},
        ],
    }
    base.update(kw)
    return base


# ── T1: R1-R4 ───────────────────────────────────────────────────────

def test_valid_minimal_doc_passes():
    validate_diarization(_doc())  # no exception


def test_r1_schema_version_float_rejected():
    with pytest.raises(DiarizationError) as ei:
        validate_diarization(_doc(schema_version=1.0))
    assert "R1" in str(ei.value)


def test_r1_schema_version_string_rejected():
    with pytest.raises(DiarizationError) as ei:
        validate_diarization(_doc(schema_version="1"))
    assert "R1" in str(ei.value)


def test_r1_schema_version_wrong_int_rejected():
    with pytest.raises(DiarizationError) as ei:
        validate_diarization(_doc(schema_version=2))
    assert "R1" in str(ei.value)


def test_r2_sha_wrong_length_rejected():
    with pytest.raises(DiarizationError) as ei:
        validate_diarization(_doc(audio_sha256="a" * 63))
    assert "R2" in str(ei.value)


def test_r2_sha_uppercase_rejected():
    with pytest.raises(DiarizationError) as ei:
        validate_diarization(_doc(audio_sha256="A" * 64))
    assert "R2" in str(ei.value)


def test_r2_sha_non_hex_rejected():
    with pytest.raises(DiarizationError) as ei:
        validate_diarization(_doc(audio_sha256="g" * 64))
    assert "R2" in str(ei.value)


def test_r3_duration_zero_rejected():
    with pytest.raises(DiarizationError) as ei:
        validate_diarization(_doc(duration_sec=0.0))
    assert "R3" in str(ei.value)


def test_r3_duration_negative_rejected():
    with pytest.raises(DiarizationError) as ei:
        validate_diarization(_doc(duration_sec=-1.0))
    assert "R3" in str(ei.value)


def test_r3_duration_nan_rejected():
    with pytest.raises(DiarizationError) as ei:
        validate_diarization(_doc(duration_sec=float("nan")))
    assert "R3" in str(ei.value)


def test_r3_duration_inf_rejected():
    with pytest.raises(DiarizationError) as ei:
        validate_diarization(_doc(duration_sec=float("inf")))
    assert "R3" in str(ei.value)


def test_r4_speakers_empty_rejected():
    with pytest.raises(DiarizationError) as ei:
        validate_diarization(_doc(speakers=[]))
    assert "R4" in str(ei.value)


def test_r4_speakers_duplicate_rejected():
    with pytest.raises(DiarizationError) as ei:
        validate_diarization(_doc(speakers=["SPEAKER_00", "SPEAKER_00"]))
    assert "R4" in str(ei.value)


def test_r4_speakers_non_string_entry_rejected():
    with pytest.raises(DiarizationError) as ei:
        validate_diarization(_doc(speakers=["SPEAKER_00", 7]))
    assert "R4" in str(ei.value)


# ── T2: R5-R6 ───────────────────────────────────────────────────────

def test_r5_start_equals_end_rejected():
    with pytest.raises(DiarizationError) as ei:
        validate_diarization(_doc(segments=[{"start": 1.0, "end": 1.0,
                                             "speaker": "SPEAKER_00"}]))
    assert "R5" in str(ei.value)


def test_r5_start_greater_than_end_rejected():
    with pytest.raises(DiarizationError) as ei:
        validate_diarization(_doc(segments=[{"start": 2.0, "end": 1.0,
                                             "speaker": "SPEAKER_00"}]))
    assert "R5" in str(ei.value)


def test_r5_end_exceeds_duration_rejected():
    with pytest.raises(DiarizationError) as ei:
        validate_diarization(_doc(segments=[{"start": 9.0, "end": 11.0,
                                             "speaker": "SPEAKER_00"}]))
    assert "R5" in str(ei.value)


def test_r5_negative_start_rejected():
    with pytest.raises(DiarizationError) as ei:
        validate_diarization(_doc(segments=[{"start": -0.1, "end": 1.0,
                                             "speaker": "SPEAKER_00"}]))
    assert "R5" in str(ei.value)


def test_r5_speaker_not_in_list_rejected():
    with pytest.raises(DiarizationError) as ei:
        validate_diarization(_doc(segments=[{"start": 0.0, "end": 1.0,
                                             "speaker": "SPEAKER_99"}]))
    assert "R5" in str(ei.value)


def test_r5_text_non_string_rejected():
    with pytest.raises(DiarizationError) as ei:
        validate_diarization(_doc(segments=[{"start": 0.0, "end": 1.0,
                                             "speaker": "SPEAKER_00",
                                             "text": 42}]))
    assert "R5" in str(ei.value)


def test_r6_unsorted_segments_rejected():
    with pytest.raises(DiarizationError) as ei:
        validate_diarization(_doc(segments=[
            {"start": 5.0, "end": 6.0, "speaker": "SPEAKER_00"},
            {"start": 1.0, "end": 2.0, "speaker": "SPEAKER_01"},
        ]))
    assert "R6" in str(ei.value)


def test_r6_overlapping_different_speakers_rejected():
    with pytest.raises(DiarizationError) as ei:
        validate_diarization(_doc(segments=[
            {"start": 0.0, "end": 3.0, "speaker": "SPEAKER_00"},
            {"start": 2.5, "end": 5.0, "speaker": "SPEAKER_01"},
        ]))
    assert "R6" in str(ei.value)


def test_r6_overlapping_same_speaker_rejected():
    with pytest.raises(DiarizationError) as ei:
        validate_diarization(_doc(segments=[
            {"start": 0.0, "end": 3.0, "speaker": "SPEAKER_00"},
            {"start": 2.5, "end": 5.0, "speaker": "SPEAKER_00"},
        ]))
    assert "R6" in str(ei.value)


def test_r5_float_tolerance_at_boundary_accepted():
    """end == duration + 1e-7 is within FLOAT_TOL (1e-6)."""
    validate_diarization(_doc(segments=[{"start": 0.0,
                                         "end": 10.0 + 1e-7,
                                         "speaker": "SPEAKER_00"}]))


def test_unknown_top_level_key_rejected():
    d = _doc()
    d["extra"] = True
    with pytest.raises(DiarizationError):
        validate_diarization(d)


# ── T3: converter + determinism + G5 shape ─────────────────────────

def test_converter_one_block_per_segment_order_preserved():
    blocks = diarization_to_speaker_blocks(_doc())
    assert len(blocks) == 2
    assert blocks[0] == SpeakerBlock(0.0, 3.2, "SPEAKER_00", "hello")
    assert blocks[1] == SpeakerBlock(3.5, 6.0, "SPEAKER_01", "")


def test_converter_revalidates_invalid_doc():
    """Defensive re-validation: same typed DiarizationError, single
    authority."""
    with pytest.raises(DiarizationError) as ei:
        diarization_to_speaker_blocks(_doc(schema_version=2))
    assert "R1" in str(ei.value)


def test_render_attribution_g5_shape():
    """G5 rejects bracketed/parenthesized labels; <d>Name</d> is the
    sanctioned form. Every token must match ^<d>[^<>]+</d>$."""
    import re
    blocks = diarization_to_speaker_blocks(_doc())
    rendered = render_attribution(blocks)
    lines = rendered.splitlines()
    assert len(lines) == 2
    for line in lines:
        assert re.match(r"^<d>[^<>]+</d>$", line), line
    # no bracketed/parenthesized label forms anywhere
    assert "[" not in rendered and "(" not in rendered
    assert lines[0] == "<d>SPEAKER_00</d>"
    assert lines[1] == "<d>SPEAKER_01</d>"


def test_determinism_double_run_byte_equality():
    doc = _doc()
    b1 = diarization_to_speaker_blocks(doc)
    b2 = diarization_to_speaker_blocks(doc)
    r1 = render_attribution(b1)
    r2 = render_attribution(b2)
    assert b1 == b2
    assert r1.encode("utf-8") == r2.encode("utf-8")


# ── T4: edge cases ──────────────────────────────────────────────────

def test_empty_segments_list_valid():
    """Zero dialogue is a valid timeline."""
    validate_diarization(_doc(segments=[]))
    assert diarization_to_speaker_blocks(_doc(segments=[])) == []


def test_large_doc_performance_sanity():
    """1000 segments must validate + convert in < 1s."""
    import time
    segs = [{"start": i * 0.01, "end": i * 0.01 + 0.005,
             "speaker": "SPEAKER_00" if i % 2 == 0 else "SPEAKER_01"}
            for i in range(1000)]
    doc = _doc(duration_sec=10.0, segments=segs)
    t0 = time.monotonic()
    validate_diarization(doc)
    blocks = diarization_to_speaker_blocks(doc)
    assert len(blocks) == 1000
    assert time.monotonic() - t0 < 1.0


def test_unicode_speaker_ids():
    doc = _doc(speakers=["说话人甲", "Speaker_B"],
               segments=[{"start": 0.0, "end": 1.0, "speaker": "说话人甲"},
                         {"start": 2.0, "end": 3.0, "speaker": "Speaker_B"}])
    blocks = diarization_to_speaker_blocks(doc)
    rendered = render_attribution(blocks)
    assert "<d>说话人甲</d>" in rendered


def test_text_with_embedded_d_like_substring_passthrough():
    """text fragments are opaque passthrough — never parsed."""
    doc = _doc(segments=[{"start": 0.0, "end": 1.0,
                          "speaker": "SPEAKER_00",
                          "text": "she said <d>X</d> literally"}])
    blocks = diarization_to_speaker_blocks(doc)
    assert blocks[0].text_hint == "she said <d>X</d> literally"
    # the embedded substring does NOT leak into attribution output
    assert render_attribution(blocks) == "<d>SPEAKER_00</d>"


# ── T5: CLI (subprocess) ────────────────────────────────────────────

import json  # noqa: E402
import subprocess  # noqa: E402

CLI = REPO / "scripts" / "check_diarization.py"
FIXTURES = REPO / "tests" / "fixtures"
PY = sys.executable


def _run_cli(*args):
    return subprocess.run(
        [PY, str(CLI), *args], capture_output=True, text=True, timeout=60)


def test_cli_valid_fixture_exit_0_summary():
    r = _run_cli(str(FIXTURES / "diarization_valid.json"))
    assert r.returncode == 0
    assert r.stdout.startswith("OK: 2 speakers, 4 segments, 12.5s")


def test_cli_convert_flag_prints_attribution():
    r = _run_cli(str(FIXTURES / "diarization_valid.json"), "--convert")
    assert r.returncode == 0
    lines = r.stdout.splitlines()
    assert lines[0].startswith("OK:")
    assert "<d>SPEAKER_00</d>" in lines
    assert "<d>SPEAKER_01</d>" in lines


def test_cli_invalid_r5_fixture_exit_1_typed_error():
    r = _run_cli(str(FIXTURES / "diarization_invalid_r5.json"))
    assert r.returncode == 1
    assert "R5" in r.stderr


def test_cli_missing_file_exit_1_no_traceback():
    r = _run_cli("/nonexistent/path/diarization.json")
    assert r.returncode == 1
    assert "Traceback" not in r.stderr
    assert "file not found" in r.stderr


def test_cli_bad_json_exit_1_no_traceback(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    r = _run_cli(str(bad))
    assert r.returncode == 1
    assert "Traceback" not in r.stderr
    assert "invalid JSON" in r.stderr
