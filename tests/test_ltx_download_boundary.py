from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUN_DIR = ROOT / "datasets/runs/maestro-parity/ltx-dependency-terminalization"
BOUNDARY = RUN_DIR / "download-boundary.json"
REPORT = RUN_DIR / "host-download-boundary/remote/download-report.tsv"
CURL_STDERR = RUN_DIR / (
    "host-download-boundary/remote/"
    "ltx-2.3-22b-ic-lora-ingredients-0.9.safetensors.curl.stderr"
)
RAW_REPORT_HASH = RUN_DIR / "host-download-boundary/remote/download-report.raw.sha256"
RAW_REMOTE_STATE_HASH = RUN_DIR / "download-boundary-remote-state.raw.sha256"


def test_first_declared_download_fails_closed_on_hash_mismatch() -> None:
    record = json.loads(BOUNDARY.read_text(encoding="utf-8"))

    assert record["schema_version"] == "wangp-dspy.wd-28ac.download-boundary/v1"
    assert record["status"] == "failed_closed"
    assert record["boundary"]["code"] == (
        "DECLARED_ASSET_HASH_MISMATCH_AFTER_UNDECLARED_URL_PROBE"
    )
    attempt = record["download_attempt"]["declared_get"]
    assert attempt["size_matches"] is True
    assert attempt["hash_matches"] is False
    assert attempt["promoted"] is False
    assert attempt["observed_size_bytes"] == 1_308_778_338
    assert attempt["observed_sha256"] == (
        "515e4e139001ac6282357a5b35372e42e98b3affd5fcc886a52242abeed19559"
    )
    assert attempt["expected_sha256"] == (
        "4647f4f18c87208f949b6f473d49af679ddd87532b40718480e5153852f1f1ba"
    )


def test_undeclared_probe_bytes_are_owned_not_erased() -> None:
    record = json.loads(BOUNDARY.read_text(encoding="utf-8"))
    probe = record["download_attempt"]["undeclared_url_effective_probe"]

    assert probe["authorized"] is False
    assert probe["curl_exit"] == 28
    assert probe["reported_payload_bytes"] == 172_109
    assert "172109" in CURL_STDERR.read_text(encoding="utf-8")
    assert record["download_attempt"]["undeclared_bytes_claim"].startswith(
        "The boundary cannot claim zero undeclared bytes"
    )


def test_boundary_stops_before_substitution() -> None:
    record = json.loads(BOUNDARY.read_text(encoding="utf-8"))

    assert record["boundary"]["substitution_attempted"] is False
    assert record["boundary"]["retry_attempted"] is False
    assert record["boundary"]["deletion_attempted"] is False
    assert record["operations"] == {
        "queue_admissions": 0,
        "native_attempts": 0,
        "outputs": 0,
        "matrix_changes": 0,
    }
    assert len(record["download_attempt"]["assets_not_requested"]) == 4
    assert REPORT.is_file()


def test_signed_cdn_queries_are_not_published() -> None:
    report = REPORT.read_text(encoding="utf-8")
    remote_state = (RUN_DIR / "download-boundary-remote-state.txt").read_text(
        encoding="utf-8"
    )
    record = json.loads(BOUNDARY.read_text(encoding="utf-8"))

    assert "REDACTED_SIGNED_QUERY" in report
    assert "REDACTED_SIGNED_QUERY" in remote_state
    assert "Signature=" not in report
    assert "Signature=" not in remote_state
    assert RAW_REPORT_HASH.read_text(encoding="utf-8").strip() == (
        "8fe341e8e78021122bdaf72ba05d196c96a7ea787d44422975975f1323984a28"
    )
    assert RAW_REMOTE_STATE_HASH.read_text(encoding="utf-8").strip() == (
        "e70e3c391447394ad05419594fc424572c8034770d24fb4523f6c05bcc0c2a0d"
    )
    assert record["credential_redaction"]["committed_report_is_redacted"] is True
