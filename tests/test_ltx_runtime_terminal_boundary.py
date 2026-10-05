from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUN_DIR = ROOT / "datasets/runs/maestro-parity/ltx-dependency-terminalization"
BOUNDARY_DIR = RUN_DIR / "runtime-repair/2026-10-03/terminal-boundary"
SUMMARY = BOUNDARY_DIR / "boundary-summary.json"
REPORT = BOUNDARY_DIR / "report.json"
STATE = BOUNDARY_DIR / "post-boundary-state.txt"


def test_runtime_repair_stops_before_network_on_probe_boundary() -> None:
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    report = json.loads(REPORT.read_text(encoding="utf-8"))

    assert summary["status"] == "failed_closed"
    assert report["boundary"]["code"] == "DECLARED_DEPENDENCY_IMPORT_FAILED"
    assert summary["boundary"]["runner_code"] == "DECLARED_DEPENDENCY_IMPORT_FAILED"
    assert summary["boundary"]["diagnostic_code"] == (
        "RUNTIME_DEPENDENCY_PROBE_METADATA_MISMATCH"
    )
    assert summary["boundary"]["module_present"] is True
    assert summary["boundary"]["top_level_distribution_metadata_present"] is False
    assert summary["boundary"]["not_a_dependency_availability_verdict"] is True
    assert summary["network_accounting"] == {
        "declared_wheel_gets": 0,
        "undeclared_requests": 0,
        "wheel_get_limit": 1,
    }
    assert report["dependency_installs"] == 0
    assert summary["artifact_state"] == {
        "runtime_directory_created": False,
        "wheel_downloaded": False,
        "extraction_started": False,
        "report_preserved": True,
    }


def test_runtime_boundary_hashes_and_terminal_host_state_are_bound() -> None:
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    state = STATE.read_text(encoding="utf-8")

    assert summary["evidence"]["report"]["sha256"] == hashlib.sha256(
        REPORT.read_bytes()
    ).hexdigest()
    assert summary["evidence"]["post_state"]["sha256"] == hashlib.sha256(
        STATE.read_bytes()
    ).hexdigest()
    assert summary["evidence"]["remote_exit"]["value"] == "2"
    assert "runtime_absent" in state
    assert "wheel_absent" in state
    assert "NVIDIA GeForce RTX 3090, 24576, 144, 23972, 0" in state
    for module in (
        "torch", "optimum.quanto", "accelerate", "safetensors", "psutil"
    ):
        assert f"{module} True" in state
    assert "mmgp False" in state
    assert summary["preservation"] == {
        "model_mutations": 0,
        "reference_mutations": 0,
        "protected_file_changes": 0,
        "evidence_source": "runner boundary counters and terminal absence checks",
    }
