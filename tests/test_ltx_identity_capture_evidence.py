from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE = (
    ROOT
    / "datasets/runs/maestro-parity/ltx-dependency-terminalization"
    / "identity-capture-f654-20261011"
)


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def preserved(path: str) -> Path:
    remote = (
        "/home/straughter/wd-28ac-run/"
        "phase-b-gate22-corrected-retry-identity-capture-f654-20261011/"
    )
    return BASE / path.removeprefix(remote)


def test_ltx_identity_evidence_manifest_hashes_every_preserved_file() -> None:
    manifest = json.loads((BASE / "sha256-manifest.json").read_text(encoding="utf-8"))

    assert len(manifest) == 86
    for relative, expected in manifest.items():
        path = BASE / relative
        assert path.is_file()
        assert path.stat().st_size == expected["size_bytes"]
        assert digest(path) == expected["sha256"]


def test_ltx_identity_evidence_discloses_unretained_launcher_diagnostic() -> None:
    summary = json.loads((BASE / "run-summary.json").read_text(encoding="utf-8"))

    assert summary["launcher_setup_note"] == (
        "A preliminary launcher attempt was observed in dispatcher tooling with "
        "ModuleNotFoundError before runner import, but its complete diagnostic "
        "was not retained in this bundle. The corrected PYTHONPATH completed "
        "the same authorized batch. The preserved queue begins with the seven "
        "corrected admissions; this bundle does not independently establish "
        "the preliminary attempt's queue or admission state."
    )
    assert (BASE / "batch.stderr").read_bytes() == b""


def test_ltx_identity_native_log_whitespace_exemption_is_path_scoped() -> None:
    attributes = (ROOT / ".gitattributes").read_text(encoding="utf-8")

    assert (
        "datasets/runs/maestro-parity/ltx-dependency-terminalization/"
        "identity-capture-f654-20261011/**/native.log -whitespace\n"
    ) in attributes
    assert "*.log -whitespace" not in attributes


def test_ltx_identity_run_proves_seven_one_attempt_native_operations() -> None:
    summary = json.loads((BASE / "run-summary.json").read_text(encoding="utf-8"))
    stage = json.loads((BASE / "stage-inventory.json").read_text(encoding="utf-8"))
    authorization = json.loads(
        (BASE / "operator-authorization.json").read_text(encoding="utf-8")
    )
    operations = summary["operations"]

    assert summary["status"] == "all_native_renders_complete"
    assert summary["operation_count"] == 7
    assert summary["rendered_pending_qc_count"] == 7
    assert summary["failed_count"] == 0
    assert summary["retry_attempted"] is False
    assert summary["matrix_promotion"] is False
    assert summary["proposal_sha256"] == (
        "146b41ca4b204e73d0a51de4fc33937cc6cca3096ef50c7d5eea608ad13564c8"
    )
    assert summary["authorization_canonical_sha256"] == (
        "2e32b060cfa6c2f529e3aa2c0f73ff7862a8103dcf043c66790e0db161bab3b8"
    )
    assert stage["repository"]["commit_sha"] == authorization["base_commit"] == (
        "f6548f03528b058476367349a5f481614cfa35be"
    )
    assert stage["repository"]["status_porcelain_v1"] == ""
    assert stage["repository"]["clean_tree"] is True
    assert stage["file_count"] == 13
    assert [row["operation_id"] for row in operations] == [
        "ltx25-outpaint",
        "ltx25-repaint",
        "ltx25-recast",
        "ltx25-upscale",
        "ltx23-outpaint",
        "ltx23-recast",
        "ltx23-upscale",
    ]
    for row in operations:
        assert row["status"] == "rendered_pending_qc"
        assert row["attempt"] == 1
        assert row["native_exit"] == 0
        assert row["output_size_bytes"] > 0
        output = preserved(row["output"])
        assert row["output_sha256"] == digest(output)
        assert row["settings_sha256"] == digest(output.parent.parent / "settings.json")


def test_ltx_identity_queue_is_rendered_pending_qc_without_failures() -> None:
    database = BASE / "jobs.db"
    connection = sqlite3.connect(
        f"file:{database}?mode=ro&immutable=1", uri=True
    )
    try:
        rows = connection.execute(
            "SELECT state, failure_count FROM jobs ORDER BY created_at"
        ).fetchall()
    finally:
        connection.close()

    assert len(rows) == 7
    assert rows == [("rendered_pending_qc", 0)] * 7
