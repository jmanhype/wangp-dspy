"""Real temporary-directory integration tests for parity evidence bundles."""
from __future__ import annotations

import hashlib, json, re, subprocess, sys
from pathlib import Path
from typing import Any

import pytest

from scripts.verify_maestro_parity import ROOT_KEYS, canonical_field_ids, verify_bundle


ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts/verify_maestro_parity.py"
CONTRACT = ROOT / "docs/maestro-parity-evidence-contract.md"


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write_bundle(root: Path) -> dict[str, Any]:
    root.mkdir(parents=True)
    (root / "inputs").mkdir()
    (root / "outputs").mkdir()
    reference = b"operator-owned reference bytes"
    artifact = b"fixture output bytes"
    (root / "inputs/reference.bin").write_bytes(reference)
    (root / "outputs/final.mp4").write_bytes(artifact)
    payload: dict[str, Any] = {
        "schema": "wangp-dspy.maestro-parity-evidence/v1",
        "operator_authorization": {"status": "approved", "text": "Authorized WD-fixture run only", "scope": "WD-651z fixture capability", "timestamp": "2026-09-24T14:41:31Z", "approved_by": "operator@example.test"},
        "command": ["uv", "run", "--frozen", "wgp", "fixture", "--no-network"],
        "repository": {"commit": "40f8c2b373dec1c84ca5a596c821b740934af6fb", "dirty_state": {"dirty": False, "identity_sha256": "a" * 64}},
        "model_provenance": [{"identity": "fixture/model-v1", "source": "operator-managed local store", "immutable_version": "1.2.3", "license": "fixture license", "download_approved": True}],
        "reference_provenance": [{"path": "inputs/reference.bin", "role": "style", "sha256": _digest(reference), "license": "reference license"}],
        "queue_attempt": {"queue_id": "queue-fixture", "job_id": "job-fixture", "admission_state": "admitted", "exit_status": "succeeded", "retry_id": "retry-0"},
        "output": [{"path": "outputs/final.mp4", "sha256": _digest(artifact)}],
        "media_metadata": [{"path": "outputs/final.mp4", "kind": "video", "width": 1280, "height": 720, "duration_s": 4.0, "fps": 24.0, "audio": {"present": True, "codec": "aac", "sample_rate_hz": 48000, "channels": 2}, "alpha_mode": "none"}],
        "objective_gate_results": [{"name": "fixture-quality", "inputs": ["outputs/final.mp4", "inputs/reference.bin"], "threshold": 0.9, "measured": 0.95, "verdict": "pass"}],
        "reviewer_verdict": {"decision": "approved", "evidence_links": ["evidence.json"]},
    }
    _write_record(root, payload)
    return payload


def _write_record(root: Path, payload: dict[str, Any]) -> None:
    path = root / "evidence.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _snapshot(root: Path) -> dict[str, bytes]:
    return {str(path.relative_to(root)): path.read_bytes() for path in sorted(root.rglob("*")) if path.is_file()}


def _diagnostic_fields(report: object) -> list[str]:
    return [item.field for item in report.diagnostics]


def _verify_unmodified(root: Path) -> object:
    before = _snapshot(root)
    report = verify_bundle(root)
    assert before == _snapshot(root)
    return report


def _record_and_verify(
    root: Path, payload: dict[str, Any]) -> object:
    _write_record(root, payload)
    before = _snapshot(root)
    report = verify_bundle(root)
    assert before == _snapshot(root)
    return report


def test_complete_authorized_bundle_passes_without_mutation(tmp_path: Path) -> None:
    root = tmp_path / "complete"
    _write_bundle(root)
    report = _record_and_verify(root, json.loads(
        (root / "evidence.json").read_text(encoding="utf-8")))
    assert report.passed
    assert report.diagnostics == ()


@pytest.mark.parametrize("field", list(ROOT_KEYS), ids=list(ROOT_KEYS))
def test_every_missing_field_group_fails_by_exact_name(
    tmp_path: Path, field: str
) -> None:
    root = tmp_path / field.replace(".", "-")
    payload = _write_bundle(root)
    del payload[ROOT_KEYS[field]]
    report = _record_and_verify(root, payload)
    assert not report.passed
    assert field in _diagnostic_fields(report)


@pytest.mark.parametrize(
    ("change", "expected"),
    [
        (lambda p: p["operator_authorization"].update(text=" "), "operator_authorization.text"),
        (lambda p: p.__setitem__("command", [""]), "command"),
        (lambda p: p["repository"].update(commit="not-a-commit"), "repository.commit.commit"),
        (lambda p: p["model_provenance"][0].update(identity=""), "model_provenance[0].identity"),
        (lambda p: p["reference_provenance"][0].update(role=""), "reference_provenance[0].role"),
        (lambda p: p["queue_attempt"].update(job_id=""), "queue_attempt.job_id"),
        (lambda p: p["output"][0].update(path=""), "output.sha256[0].path"),
        (lambda p: p["media_metadata"][0].update(width=0), "media_metadata[0].width"),
        (lambda p: p["objective_gate_results"][0].update(threshold="0.9"), "objective_gate_results[0].threshold"),
        (lambda p: p["reviewer_verdict"].update(evidence_links=[""]), "reviewer_verdict.evidence_links[0]"),
    ],
)
def test_blank_or_mismatched_value_in_each_field_group_fails(
    tmp_path: Path, change: Any, expected: str
) -> None:
    root = tmp_path / "invalid"
    payload = _write_bundle(root)
    change(payload)
    report = _record_and_verify(root, payload)
    assert not report.passed
    assert expected in _diagnostic_fields(report)


@pytest.mark.parametrize(
    ("relative", "replacement", "field"),
    [
        ("outputs/final.mp4", b"hand-edited output bytes", "output.sha256[0].sha256"),
        ("inputs/reference.bin", b"changed reference", "reference_provenance[0].sha256"),
    ],
    ids=["output", "reference"],
)
def test_tampered_artifact_hash_fails_by_exact_field(
    tmp_path: Path, relative: str, replacement: bytes, field: str
) -> None:
    root = tmp_path / field
    _write_bundle(root)
    (root / relative).write_bytes(replacement)
    report = _verify_unmodified(root)
    assert not report.passed
    assert field in _diagnostic_fields(report)
    if field.startswith("output"):
        assert _digest(replacement) in report.diagnostics[0].message


def test_denied_authorization_never_passes(tmp_path: Path) -> None:
    root = tmp_path / "unauthorized"
    payload = _write_bundle(root)
    payload["operator_authorization"]["status"] = "denied"
    report = _record_and_verify(root, payload)
    assert not report.passed
    assert "operator_authorization.status" in _diagnostic_fields(report)


def test_contract_and_checker_field_lists_cannot_diverge() -> None:
    text = CONTRACT.read_text(encoding="utf-8")
    assert text.count("## Canonical required field groups") == 1
    match = re.search(r"^## Canonical required field groups$(.*?)(?=^## )", text, re.M | re.S)
    assert match is not None, "canonical field section is missing"
    fields = re.findall(r"^\| `([^`]+)` \|", match.group(1), flags=re.MULTILINE)
    assert fields, "contract has no canonical field table"
    assert tuple(fields) == canonical_field_ids()


def test_cli_reports_exact_nonzero_failure_without_repair(tmp_path: Path) -> None:
    root = tmp_path / "cli-failure"
    payload = _write_bundle(root)
    payload["output"][0]["sha256"] = "0" * 64
    _write_record(root, payload)
    before = _snapshot(root)
    result = subprocess.run([sys.executable, str(CHECKER), str(root)], capture_output=True, text=True, timeout=10, check=False)
    after = _snapshot(root)
    assert result.returncode == 1
    expected = f"FAIL output.sha256[0].sha256: recorded {'0' * 64} but artifact bytes hash {_digest(b'fixture output bytes')}\n"
    assert result.stderr == expected
    assert before == after
