from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import scripts.review_ltx_operations as reviewer


ROOT = Path(__file__).resolve().parents[1]
RUN_DIR = ROOT / "datasets/runs/maestro-parity/ltx-dependency-terminalization"
GATE = RUN_DIR / "jev-gates/2026-10-03/gate-7-evidence.json"
AUTH = RUN_DIR / "operator-authorization.json"


def test_gate7_artifacts_are_hash_bound_and_secret_free() -> None:
    gate = json.loads(GATE.read_text(encoding="utf-8"))
    auth = json.loads(AUTH.read_text(encoding="utf-8"))

    assert gate["decision"] == "CONTINUE"
    assert gate["confidence"] == 0.80
    assert gate["constraint_risk"] == 0.37
    assert gate["missing_evidence_score"] == 1.16
    assert gate["declared_snapshot_sha256"] == (
        "ed82d6d2fbb2cf7f9745a55625ec8850d2cb1ff9c70514634ce9698b85f9091c"
    )
    assert gate["declared_trace_sha256"] == (
        "21709889328392ed0e33a76ccadd16eeb284fd45278ea36b94a6161b4a9bf7b7"
    )
    assert auth["jev_final_operations_authorization"]["snapshot_sha256"] == (
        gate["declared_snapshot_sha256"]
    )
    assert gate["raw_api_key_scan"]["matches"] == 0
    for name, record in gate["artifacts"].items():
        raw = (GATE.parent / name).read_bytes()
        assert len(raw) == record["size_bytes"]
        assert hashlib.sha256(raw).hexdigest() == record["sha256"]
    patterns = (
        re.compile(rb"sk-(?:proj-)?[A-Za-z0-9_-]{20,}"),
        re.compile(rb"(?i)api[_-]?key\s*[:=]"),
        re.compile(rb"(?i)authorization\s*[:=]\s*[\"']?bearer"),
        re.compile(rb"(?:Signature=|Policy=|X-Amz-Signature=|access_token=)", re.I),
    )
    for path in GATE.parent.iterdir():
        if path.is_file():
            for pattern in patterns:
                assert pattern.search(path.read_bytes()) is None, path.name


def test_independent_review_parser_is_strict_and_uses_accepted_threshold() -> None:
    approved = reviewer.parse_review(
        '{"score":8,"verdict":"approve","summary":"clean","artifacts":[]}'
    )
    artifact = reviewer.parse_review(
        '{"score":9,"verdict":"approve","summary":"broken","artifacts":["blank frame"]}'
    )
    low_score = reviewer.parse_review(
        '{"score":7,"verdict":"approve","summary":"weak","artifacts":[]}'
    )

    assert approved["decision"] == "approved"
    assert artifact["decision"] == "rejected"
    assert low_score["decision"] == "rejected"
    assert reviewer.THRESHOLD == 8.0
