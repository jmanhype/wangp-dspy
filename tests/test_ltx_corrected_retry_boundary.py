from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOUNDARY = ROOT / (
    "datasets/runs/maestro-parity/ltx-dependency-terminalization/"
    "corrected-retry-boundary.json"
)
CLI = ROOT / (
    "datasets/runs/maestro-parity/ltx-dependency-terminalization/"
    "corrected-retry-downloads/outpaint.traceback.txt"
)
STATE = ROOT / (
    "datasets/runs/maestro-parity/ltx-dependency-terminalization/"
    "corrected-retry-downloads/final-download-boundary-state.json"
)


def test_corrected_retry_stops_after_accounting_failure() -> None:
    record = json.loads(BOUNDARY.read_text(encoding="utf-8"))
    attempt = record["outpaint_attempt"]

    assert record["status"] == "failed_closed"
    assert record["boundary"]["code"] == (
        "CURL_ACCOUNTING_OUTPUT_INVALID_AFTER_ONE_DECLARED_GET"
    )
    assert attempt["curl_invocations"] == 1
    assert attempt["declared_request_count"] == 1
    assert attempt["undeclared_request_count"] == 0
    assert attempt["url_effective_probe_request_count"] == 0
    assert attempt["exact_size_and_file_sha256"] is True
    assert attempt["durable_attempt_report_created"] is False
    assert attempt["redirect_count"] is None
    traceback = CLI.read_text(encoding="utf-8")
    assert "invalid literal for int()" in traceback
    assert "redirect_count" in traceback


def test_boundary_preserves_two_exact_finals_and_three_absences() -> None:
    record = json.loads(BOUNDARY.read_text(encoding="utf-8"))
    state = json.loads(STATE.read_text(encoding="utf-8"))["assets"]

    assert record["promoted_first_partial"]["curl_invocations"] == 0
    assert len(record["assets_not_requested"]) == 3
    for asset_id in (
        "ltx-2.3-22b-ic-lora-ingredients-0.9.safetensors",
        "ltx-2.3-22b-ic-lora-outpaint.safetensors",
    ):
        observed = state[asset_id]
        assert observed["final"]["exists"] is True
        assert observed["final"]["sha256"] == observed["expected"]["sha256"]
        assert observed["partial"]["exists"] is False
    for asset_id in record["assets_not_requested"]:
        assert state[asset_id]["final"]["exists"] is False
        assert state[asset_id]["partial"]["exists"] is False
    assert record["operations"] == {
        "queue_admissions": 0,
        "native_attempts": 0,
        "outputs": 0,
        "matrix_changes": 0,
    }
