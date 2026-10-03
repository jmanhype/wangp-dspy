from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUN_DIR = ROOT / "datasets/runs/maestro-parity/ltx-dependency-terminalization"
REPORT = RUN_DIR / "qc-readiness/report.json"
EXIT = RUN_DIR / "qc-readiness/remote.exit"
GATE = RUN_DIR / "jev-gates/2026-10-03/gate-5-6-evidence.json"
AUTH = RUN_DIR / "operator-authorization.json"


def test_qc_readiness_start_health_stop_passes_exact_boundaries() -> None:
    report = json.loads(REPORT.read_text(encoding="utf-8"))

    assert EXIT.read_text(encoding="utf-8").strip() == "0"
    assert report["status"] == "passed"
    assert report["scope"] == "qc_readiness_only"
    assert report["gate"] == 6
    assert report["prestart"]["health"]["reachable"] is False
    assert report["prestart"]["gpu_apps"]["stdout"].strip() == ""
    assert report["prestart"]["judge_processes"]["returncode"] == 1
    assert report["start_command"]["argv"] == [
        "/home/straughter/marathon/bin/judge_ctl.sh", "start"
    ]
    assert report["start_command"]["returncode"] == 0
    assert report["start_command"]["stdout"].strip() == "judge up after 20s"
    assert report["health_reached"] is True
    assert report["health_poll"][-1]["http_status"] == 200
    assert report["health_poll"][-1]["body"] == '{"status":"ok"}'


def test_healthy_state_and_clean_stop_are_measured() -> None:
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    healthy = report["healthy_state"]
    poststop = report["poststop_state"]

    assert healthy["health"]["body"] == '{"status":"ok"}'
    assert healthy["gpu_query"]["stdout"].strip() == (
        "NVIDIA GeForce RTX 3090, 24576, 7901, 16215, 0"
    )
    assert "1495102" in healthy["judge_processes"]["stdout"]
    assert "llama-server" in healthy["gpu_apps"]["stdout"]
    assert report["stop_command"]["argv"] == [
        "/home/straughter/marathon/bin/judge_ctl.sh", "stop"
    ]
    assert report["stop_command"]["returncode"] == 0
    assert report["stop_command"]["stdout"].strip() == "judge stopped: 0 remaining"
    assert report["stop_verified"] is True
    assert poststop["health"]["reachable"] is False
    assert poststop["gpu_apps"]["stdout"].strip() == ""
    assert poststop["judge_processes"]["returncode"] == 1
    assert poststop["gpu_query"]["stdout"].strip() == (
        "NVIDIA GeForce RTX 3090, 24576, 144, 23972, 0"
    )


def test_qc_phase_preserves_models_references_and_prohibitions() -> None:
    report = json.loads(REPORT.read_text(encoding="utf-8"))

    assert len(report["prestart_protected"]) == 5
    assert len(report["poststop_protected"]) == 5
    assert len(report["prestart_references"]) == 6
    assert len(report["poststop_references"]) == 6
    assert report["protected_files_unchanged"] is True
    assert report["references_unchanged"] is True
    assert report["phase_bounds"] == {
        "native_operations": 0,
        "queue_admissions": 0,
        "renders": 0,
        "retrievals": 0,
        "network_model_gets": 0,
        "model_mutations": 0,
        "reference_mutations": 0,
        "unrelated_process_actions": 0,
        "matrix_transitions": 0,
    }


def test_qc_report_contains_no_credential_patterns() -> None:
    raw = REPORT.read_bytes()
    patterns = (
        re.compile(rb"sk-(?:proj-)?[A-Za-z0-9_-]{20,}"),
        re.compile(rb"(?i)api[_-]?key\s*[:=]"),
        re.compile(rb"(?i)authorization\s*[:=]\s*[\"']?bearer"),
        re.compile(rb"(?:Signature=|Policy=|X-Amz-Signature=|access_token=)", re.I),
    )
    for pattern in patterns:
        assert pattern.search(raw) is None
