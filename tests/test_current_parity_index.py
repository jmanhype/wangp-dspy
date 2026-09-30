"""Real-repository integration coverage for the current Maestro parity index."""
from __future__ import annotations

import importlib.util
import json
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any

import pytest


ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "datasets/runs/maestro-parity/WD-fay0"
VALIDATOR_PATH = BUNDLE / "validate_index.py"
INDEX_PATH = BUNDLE / "evidence-index.json"


def _load_validator() -> Any:
    spec = importlib.util.spec_from_file_location("current_parity_validator", VALIDATOR_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VALIDATOR = _load_validator()


def _index() -> dict[str, Any]:
    return json.loads(INDEX_PATH.read_text(encoding="utf-8"))


def _write_mutated_index(tmp_path: Path, mutation: Any) -> Path:
    payload = _index()
    mutation(payload)
    path = tmp_path / "evidence-index.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def test_current_matrix_is_exact_and_has_required_census() -> None:
    observed = VALIDATOR.parse_document_rows(ROOT)
    index = _index()
    rows = index["row_inventory"]["rows"]

    assert len(observed) == len(rows) == 208
    assert observed == [
        {key: row[key] for key in observed[0]}
        for row in rows
    ]
    assert Counter(row["canonical_state"] for row in rows) == Counter(
        {
            "host_run_verified": 89,
            "dependency_blocked": 7,
            "terminal_unsupported_or_fail_closed": 110,
            "not_applicable": 2,
        }
    )
    assert not [row for row in rows if row["canonical_state"] == "planned"]
    assert index["matrix_identity_sha256"] == VALIDATOR.matrix_identity(rows)


def test_exactly_seven_current_ltx_cells_and_boundary_are_recorded() -> None:
    index = _index()
    ltx = index["remaining_boundaries"]["ltx_dependency_batch"]
    rows = {
        (row["doc"], row["row"], row["cell"])
        for row in index["row_inventory"]["rows"]
        if row["canonical_state"] == "dependency_blocked"
    }

    assert len(rows) == len(ltx["cells"]) == 7
    assert rows == {tuple(cell) for cell in ltx["cells"]}
    assert ltx["source_ref"] == (
        "story/WD-28ac@fced67e1293dc2dbbdf3f29c8b615f6357012ab6"
    )
    assert ltx["sha256"] == (
        "6c881c9df3cd2a5d4ce85ee8fe5327e6631ac77cf2a2ca88c3b4579be4f05d53"
    )
    assert ltx["model_download_bytes_actual"] == 0
    assert ltx["inference_attempted"] is False
    assert ltx["not_a_hardware_verdict"] is True


def test_editor_host_run_is_verified_and_first_run_stays_incomplete() -> None:
    index = _index()
    non_matrix = {
        row["row"]: row for row in index["non_matrix_inventory"]["rows"]
    }
    editor = non_matrix["Authorized host export/media"]
    first_run = non_matrix["Generated artifact from first-run"]
    editor_bundle = ROOT / VALIDATOR.EDITOR_EVIDENCE
    evidence = json.loads(editor_bundle.read_text(encoding="utf-8"))

    assert editor["canonical_state"] == "host_run_verified"
    assert Path(editor["evidence_or_boundary"]) == VALIDATOR.EDITOR_EVIDENCE
    assert VALIDATOR.digest(editor_bundle) == index["editor_host_run_evidence_sha256"]
    assert evidence["queue_attempt"]["final_state"] == "done"
    assert evidence["reviewer_verdict"]["decision"] == "approved"
    assert all(gate["verdict"] == "pass" for gate in evidence["objective_gate_results"])

    assert first_run["canonical_state"] == "incomplete_storage_boundary"
    boundary = index["remaining_boundaries"]["first_run_generated_artifact"]
    assert boundary["generated_artifact"] is False
    assert boundary["queue_jobs_admitted"] == 0
    assert boundary["source_ref"] == (
        "story/WD-bw0h@2dfe36863e29eef02af0ea330d13d331bafdc00e"
    )
    assert boundary["sha256"] == (
        "b78f5936a227782e4c3b7866e041cd9bbcc3d60d7ed4b9ebe5418e14e3d78d5f"
    )


def test_matrix_evidence_manifest_hashes_real_bundle_bytes() -> None:
    index = _index()
    manifest = index["evidence_manifest"]
    assert len(manifest) == 39
    assert manifest == VALIDATOR.evidence_manifest(
        VALIDATOR.parse_document_rows(ROOT), ROOT
    )
    for relative_path, expected_hash in manifest.items():
        assert VALIDATOR.digest(ROOT / relative_path) == expected_hash


def test_validator_command_passes_current_repository() -> None:
    result = subprocess.run(
        ["python3", str(VALIDATOR_PATH)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(result.stdout)
    assert payload == {
        "result": "PASS",
        "matrix_rows": 208,
        "matrix_totals": {
            "dependency_blocked": 7,
            "host_run_verified": 89,
            "not_applicable": 2,
            "terminal_unsupported_or_fail_closed": 110,
        },
        "non_matrix_rows": 3,
        "ltx_dependency_cells": 7,
        "hashed_matrix_evidence_files": 39,
    }


def test_matrix_index_drift_fails_closed(tmp_path: Path) -> None:
    def mutate(payload: dict[str, Any]) -> None:
        payload["row_inventory"]["rows"][0]["documented_state"] = "planned"

    path = _write_mutated_index(tmp_path, mutate)
    with pytest.raises(AssertionError, match="index rows diverge"):
        VALIDATOR.validate_index(path, ROOT)


def test_stale_editor_planned_state_fails_closed(tmp_path: Path) -> None:
    def mutate(payload: dict[str, Any]) -> None:
        row = next(
            row
            for row in payload["non_matrix_inventory"]["rows"]
            if row["row"] == "Authorized host export/media"
        )
        row.update(
            canonical_state="planned",
            documented_state="planned",
            evidence_or_boundary="none",
        )

    path = _write_mutated_index(tmp_path, mutate)
    with pytest.raises(AssertionError, match="non_matrix_inventory"):
        VALIDATOR.validate_index(path, ROOT)


def test_wrong_remaining_ltx_count_fails_closed(tmp_path: Path) -> None:
    def mutate(payload: dict[str, Any]) -> None:
        payload["remaining_boundaries"]["ltx_dependency_batch"]["cells"].pop()

    path = _write_mutated_index(tmp_path, mutate)
    with pytest.raises(AssertionError):
        VALIDATOR.validate_index(path, ROOT)


def test_missing_verified_evidence_link_fails_closed(tmp_path: Path) -> None:
    def mutate(payload: dict[str, Any]) -> None:
        row = next(
            row
            for row in payload["row_inventory"]["rows"]
            if row["documented_state"] == "host_run_verified"
        )
        row["evidence_or_boundary"] = ""

    path = _write_mutated_index(tmp_path, mutate)
    with pytest.raises(AssertionError, match="index rows diverge"):
        VALIDATOR.validate_index(path, ROOT)
