from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUN_DIR = ROOT / "datasets/runs/maestro-parity/ltx-dependency-terminalization"
GATE_DIR = RUN_DIR / "jev-gates/2026-10-03"
SUMMARY = GATE_DIR / "gate-5-6-evidence.json"
AUTHORIZATION = RUN_DIR / "operator-authorization.json"


PATTERNS = {
    "openai_sk": re.compile(rb"sk-(?:proj-)?[A-Za-z0-9_-]{20,}"),
    "api_key": re.compile(rb"(?i)api[_-]?key\s*[:=]\s*[\"']?[A-Za-z0-9_-]{16,}"),
    "bearer": re.compile(rb"(?i)authorization\s*[:=]\s*[\"']?bearer\s+[A-Za-z0-9._-]{16,}"),
    "typesafe": re.compile(rb"(?i)typesafe[_-]?[A-Za-z0-9_-]{0,20}[_-]?[A-Za-z0-9_-]{20,}"),
}


def test_gate5_and_gate6_artifacts_are_hash_bound_and_secret_free() -> None:
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    gate5 = summary["gates"]["5"]
    gate6 = summary["gates"]["6"]

    assert gate5["decision"] == "GATHER_EVIDENCE"
    assert gate5["gather_confidence"] == 0.72
    assert gate5["constraint_risk"] == 0.26
    assert gate5["missing_evidence_score"] == 1.36
    assert gate5["declared_snapshot_sha256"] == (
        "91c2df7d23ec3d8a142d4419199b6326823c6e4b2047fb5789da3f6db000e9bd"
    )
    assert gate6["decision"] == "CONTINUE"
    assert gate6["confidence"] == 0.98
    assert gate6["constraint_risk"] == 0.20
    assert gate6["missing_evidence_score"] == 1.09
    assert gate6["declared_snapshot_sha256"] == (
        "f9509a57f4311c4a595e591551fe2f3fd4e55e25bf0862ee107fb263d9340aae"
    )
    assert gate6["declared_trace_sha256"] == (
        "f6ffafda422883b9f5cb5149bb3e9384c167b034ec5d4cae9e994659c6e10726"
    )
    for name, record in summary["artifacts"].items():
        raw = (GATE_DIR / name).read_bytes()
        assert len(raw) == record["size_bytes"]
        assert hashlib.sha256(raw).hexdigest() == record["sha256"]
    for path in GATE_DIR.iterdir():
        if not path.is_file():
            continue
        raw = path.read_bytes()
        for pattern in PATTERNS.values():
            assert pattern.search(raw) is None, f"{path.name}: {pattern.pattern}"


def test_gate6_binds_qc_only_scope_and_fresh_probe() -> None:
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    authorization = json.loads(AUTHORIZATION.read_text(encoding="utf-8"))
    gate6 = summary["gates"]["6"]
    auth = authorization["jev_qc_readiness_authorization"]

    assert auth["snapshot_sha256"] == gate6["declared_snapshot_sha256"]
    assert auth["trace_sha256"] == gate6["declared_trace_sha256"]
    assert auth["scope"] == "qc_readiness_only"
    assert auth["operations_authorized"] is False
    assert auth["health_endpoint"] == "http://127.0.0.1:8000/health"
    assert auth["authorized_actions"] == gate6["authorized_actions"]
    assert set(auth["prohibited_actions"]) == set(gate6["prohibited_actions"])
    assert "native_operation" in auth["prohibited_actions"]
    assert "matrix_transition" in auth["prohibited_actions"]
    fresh = GATE_DIR / "wd28ac-fresh-readonly-probe-5.txt"
    assert gate6["fresh_probe_sha256"] == hashlib.sha256(
        fresh.read_bytes()
    ).hexdigest()


def test_gate6_decision_and_trace_bindings_recompute() -> None:
    decision = json.loads(
        (GATE_DIR / "wd28ac-jev-decision-6.json").read_text(encoding="utf-8")
    )
    rows = [
        json.loads(line)
        for line in (GATE_DIR / "wd28ac-jev-trace-6.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    canonical = "\n".join(
        json.dumps(row, sort_keys=True, separators=(",", ":"))
        for row in rows
    ).encode()

    assert decision["mode"] == "live"
    assert decision["decision"] == "continue"
    assert decision["snapshot_sha256"] == (
        "f9509a57f4311c4a595e591551fe2f3fd4e55e25bf0862ee107fb263d9340aae"
    )
    assert hashlib.sha256(canonical).hexdigest() == decision["trace_sha256"]
