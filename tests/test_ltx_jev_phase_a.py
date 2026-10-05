from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUN_DIR = ROOT / "datasets/runs/maestro-parity/ltx-dependency-terminalization"
SUMMARY = RUN_DIR / "phase-a-downloads/download-summary.json"
POSTFLIGHT = RUN_DIR / "host-preflight-phase-a/phase-a-postflight.json"


FORBIDDEN = (
    re.compile(r"sk-(?:proj-)?[A-Za-z0-9_-]{20,}"),
    re.compile(r"(?i)api[_-]?key\s*[:=]\s*[\"']?[A-Za-z0-9_-]{16,}"),
    re.compile(r"(?i)authorization\s*[:=]\s*[\"']?bearer\s+[A-Za-z0-9._-]{16,}"),
    re.compile(r"(?:Signature=|Policy=|X-Amz-Signature=|access_token=)", re.I),
)


def test_phase_a_used_exactly_three_declared_curl_invocations() -> None:
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))

    assert summary["aggregate_request_accounting"] == {
        "curl_invocations": 3,
        "declared_request_count": 3,
        "undeclared_request_count": 0,
        "url_effective_probe_request_count": 0,
        "redirect_count": 3,
        "network_request_count": 6,
    }
    assert len(summary["downloads"]) == 3
    for download in summary["downloads"]:
        assert download["curl_exit"] == 0
        assert download["http_code"] == "200"
        assert download["url_effective_source"] == "declared_curl_write_out"
        assert download["redirect_count"] == 1
        assert download["connection_count"] == 2
        assert download["size_match"] is True
        assert download["file_sha256_match"] is True
        assert download["promoted"] is True
        assert download["request_accounting"] == {
            "curl_invocations": 1,
            "declared_request_count": 1,
            "undeclared_request_count": 0,
            "url_effective_probe_request_count": 0,
            "redirect_count": 1,
            "network_request_count": 2,
        }


def test_phase_a_postflight_verifies_all_five_finals_and_no_partials() -> None:
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    postflight = json.loads(POSTFLIGHT.read_text(encoding="utf-8"))

    assert len(summary["verified_finals"]) == 5
    assert len(postflight["assets"]) == 5
    for asset_id, expected in summary["verified_finals"].items():
        observed = postflight["assets"][asset_id]
        assert observed["size_match"] is True
        assert observed["sha256_match"] is True
        assert observed["partial_absent"] is True
        assert expected["size_bytes"] == observed["final"]["size_bytes"]
        assert expected["sha256"] == observed["final"]["sha256"]
    assert summary["phase_boundary"] == {
        "qc_contacted": False,
        "queue_admissions": 0,
        "renders": 0,
        "matrix_transitions": 0,
        "stopped_for": "Jev Gate #3",
    }


def test_phase_a_committed_reports_are_credential_redacted_and_hash_bound() -> None:
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    postflight = json.loads(POSTFLIGHT.read_text(encoding="utf-8"))

    for download in summary["downloads"]:
        path = SUMMARY.parent / download["sanitized_report"]
        raw_text = path.read_text(encoding="utf-8")
        for pattern in FORBIDDEN:
            assert pattern.search(raw_text) is None, pattern.pattern
        report = json.loads(raw_text)
        assert report["url_effective"].endswith("?REDACTED_SIGNED_QUERY")
        assert report["credential_redaction"]["raw_report_sha256"] == (
            download["raw_report_sha256"]
        )
        remote_name = download["asset_id"] + ".attempt.json"
        assert postflight["report_files"][remote_name] == {
            "size_bytes": download["raw_report_size_bytes"],
            "sha256": download["raw_report_sha256"],
        }
