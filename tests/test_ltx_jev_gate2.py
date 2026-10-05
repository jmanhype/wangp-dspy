from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUN_DIR = ROOT / "datasets/runs/maestro-parity/ltx-dependency-terminalization"
GATE_DIR = RUN_DIR / "jev-gates/2026-10-03"
SUMMARY = GATE_DIR / "gate-evidence.json"
AUTHORIZATION = RUN_DIR / "operator-authorization.json"


PATTERNS = {
    "openai_sk": re.compile(rb"sk-(?:proj-)?[A-Za-z0-9_-]{20,}"),
    "api_key_assignment": re.compile(
        rb"(?i)api[_-]?key\s*[:=]\s*[\"']?[A-Za-z0-9_-]{16,}"
    ),
    "bearer_assignment": re.compile(
        rb"(?i)authorization\s*[:=]\s*[\"']?bearer\s+[A-Za-z0-9._-]{16,}"
    ),
    "typesafe_token": re.compile(
        rb"(?i)typesafe[_-]?[A-Za-z0-9_-]{0,20}[_-]?[A-Za-z0-9_-]{20,}"
    ),
}


def test_gate2_artifacts_hashes_and_decision_are_bound() -> None:
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    decision = json.loads(
        (GATE_DIR / "wd28ac-jev-decision-2.json").read_text(encoding="utf-8")
    )

    assert summary["gate"] == 2
    assert summary["recorded_scope"] == "PHASE_A_DOWNLOADS_ONLY"
    assert summary["declared_snapshot_sha256"] == decision["snapshot_sha256"] == (
        "1e7d3349996543e8cf1ae9d3f66711be26ab73fa1d8b49d866fafb2ec13cbdf2"
    )
    assert decision["decision"] == "continue"
    assert decision["mode"] == "live"
    assert summary["decision"] == "CONTINUE"
    assert summary["confidence"] == 0.96
    assert summary["constraint_risk"] == 0.21
    assert summary["missing_evidence_score"] == 1.25
    for name, record in summary["artifacts"].items():
        raw = (GATE_DIR / name).read_bytes()
        assert len(raw) == record["size_bytes"]
        assert hashlib.sha256(raw).hexdigest() == record["sha256"]
    trace_raw = (GATE_DIR / "wd28ac-jev-trace-2.jsonl").read_text(encoding="utf-8")
    records = [json.loads(line) for line in trace_raw.splitlines() if line.strip()]
    canonical = "\n".join(
        json.dumps(item, sort_keys=True, separators=(",", ":"))
        for item in records
    ).encode()
    assert hashlib.sha256(canonical).hexdigest() == decision["trace_sha256"]


def test_gate2_persisted_artifacts_contain_no_raw_api_key_patterns() -> None:
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    assert summary["raw_api_key_scan"] == {
        "status": "PASS",
        "patterns_checked": sorted(PATTERNS),
        "matches": 0,
    }
    for path in GATE_DIR.iterdir():
        if not path.is_file():
            continue
        raw = path.read_bytes()
        for label, pattern in PATTERNS.items():
            assert pattern.search(raw) is None, f"{label} found in {path.name}"


def test_authorization_binds_gate2_phase_a_scope() -> None:
    authorization = json.loads(AUTHORIZATION.read_text(encoding="utf-8"))
    gate = authorization["jev_phase_a_authorization"]
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))

    assert gate["snapshot_sha256"] == summary["declared_snapshot_sha256"]
    assert gate["trace_sha256"] == summary["declared_trace_sha256"]
    assert gate["decision"] == "CONTINUE"
    assert gate["confidence"] == 0.96
    assert gate["phase"] == "downloads_only"
    assert gate["expected_existing_finals"] == [
        "ltx-2.3-22b-ic-lora-ingredients-0.9.safetensors",
        "ltx-2.3-22b-ic-lora-outpaint.safetensors",
    ]
    assert len(gate["assets"]) == 3
    assert set(gate["assets"]) == {
        "ltx-2.3-22b-ic-lora-in-outpainting-0.9.safetensors",
        "ltx-2.5-22b-ic-lora-pixel-spatial-upscaler-x2-1.0.safetensors",
        "ltx-2.3-22b-dev_diffusion_model_quanto_int8.safetensors",
    }
    assert gate["max_curl_invocations_per_asset"] == 1
    assert gate["stop_before"] == "Jev Gate #3"
