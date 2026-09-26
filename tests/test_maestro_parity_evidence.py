"""Real temporary-directory integration tests for parity evidence bundles."""
from __future__ import annotations

import hashlib, json, re, subprocess, sys
from pathlib import Path
from typing import Any

import pytest

from scripts.verify_maestro_parity import (
    ROOT_KEYS,
    canonical_constraints,
    canonical_field_ids,
    contract_rows,
    verify_bundle,
    verify_native_logs,
)


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
    (root / "inputs/reference-link").symlink_to(root / "inputs/reference.bin", target_is_directory=False)
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


def test_uppercase_sha256_values_match_exact_bytes_for_all_hashed_groups(
    tmp_path: Path,
) -> None:
    root = tmp_path / "uppercase"
    payload = _write_bundle(root)
    payload["reference_provenance"][0]["sha256"] = (
        payload["reference_provenance"][0]["sha256"].upper()
    )
    payload["output"][0]["sha256"] = payload["output"][0]["sha256"].upper()
    log = root / "host-logs" / "render.log"
    log.parent.mkdir()
    log.write_bytes(
        (
            ROOT / "datasets/runs/maestro-parity/WD-9t9o/host-logs/edit.render.log"
        ).read_bytes()
    )
    payload["queue_attempt"].update(
        native_logs=["host-logs/render.log"],
        native_log_sha256={
            "host-logs/render.log": hashlib.sha256(log.read_bytes()).hexdigest().upper()
        },
    )
    report = _record_and_verify(root, payload)
    assert report.passed
    assert report.diagnostics == ()
    assert [warning.code for warning in report.warnings] == [
        "WAN2GP_OPTIONAL_MUTAGEN_MISSING"
    ]


@pytest.mark.parametrize("group", ["reference", "output", "native-log"])
def test_lexical_dotdot_component_fails_closed_for_every_hashed_path(
    tmp_path: Path, group: str
) -> None:
    root = tmp_path / f"{group}-lexical-dotdot"
    payload = _write_bundle(root)
    if group == "reference":
        payload["reference_provenance"][0]["path"] = "inputs/../inputs/reference.bin"
        field = "reference_provenance[0].sha256"
        relative = payload["reference_provenance"][0]["path"]
    elif group == "output":
        payload["output"][0]["path"] = "inputs/../outputs/final.mp4"
        field = "output.sha256[0].sha256"
        relative = payload["output"][0]["path"]
    else:
        log = root / "host-logs" / "render.log"
        log.parent.mkdir()
        log.write_text("Queue completed: 1/1 tasks\n", encoding="utf-8")
        payload["queue_attempt"]["native_logs"] = [
            "host-logs/../host-logs/render.log"
        ]
        field = "queue_attempt.native_logs[0]"
        relative = payload["queue_attempt"]["native_logs"][0]
    report = _record_and_verify(root, payload)
    assert not report.passed
    diagnostic = next(item for item in report.diagnostics if item.field == field)
    assert diagnostic.message == f"path contains a lexical '..' component: {relative}"


@pytest.mark.parametrize("group", ["reference", "output", "native-log"])
def test_symlinked_parent_component_fails_closed_for_every_hashed_path(
    tmp_path: Path, group: str
) -> None:
    root = tmp_path / f"{group}-symlinked-parent"
    payload = _write_bundle(root)
    if group == "reference":
        (root / "linked-inputs").symlink_to(root / "inputs", target_is_directory=True)
        payload["reference_provenance"][0]["path"] = "linked-inputs/reference.bin"
        field = "reference_provenance[0].sha256"
    elif group == "output":
        (root / "linked-inputs").symlink_to(root / "inputs", target_is_directory=True)
        payload["output"][0].update(
            path="linked-inputs/reference.bin",
            sha256=payload["reference_provenance"][0]["sha256"],
        )
        field = "output.sha256[0].sha256"
    else:
        log = root / "host-logs" / "render.log"
        log.parent.mkdir()
        log.write_text("Queue completed: 1/1 tasks\n", encoding="utf-8")
        (root / "linked-host-logs").symlink_to(
            root / "host-logs", target_is_directory=True)
        payload["queue_attempt"]["native_logs"] = [
            "linked-host-logs/render.log"
        ]
        field = "queue_attempt.native_logs[0]"
    report = _record_and_verify(root, payload)
    assert not report.passed
    diagnostic = next(item for item in report.diagnostics if item.field == field)
    assert diagnostic.message.startswith("path contains a symlinked component: ")


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


def _image(payload: dict[str, Any]) -> None:
    payload["media_metadata"][0].update(kind="image", duration_s=None, fps=None, audio={"present": False})


CONSTRAINT_CASES = (
    ("auth-status", lambda p: p["operator_authorization"].update(status="denied"), ("operator_authorization.status",)),
    ("auth-required-text", lambda p: p["operator_authorization"].update(text=" ", scope="", approved_by=None), ("operator_authorization.text", "operator_authorization.scope", "operator_authorization.approved_by")),
    ("auth-timestamp", lambda p: p["operator_authorization"].update(timestamp="2026-09-24"), ("operator_authorization.timestamp",)),
    ("command-argv", lambda p: p.__setitem__("command", ["uv", " "]), ("command",)),
    ("repo-commit", lambda p: p["repository"].update(commit="not-hex"), ("repository.commit.commit",)),
    ("repo-dirty-state", lambda p: p["repository"].update(dirty_state={"dirty": "false", "identity_sha256": "short"}), ("repository.commit.dirty_state.dirty", "repository.commit.dirty_state.identity_sha256")),
    ("model-array", lambda p: p.__setitem__("model_provenance", []), ("model_provenance",)),
    ("model-required-text", lambda p: p["model_provenance"][0].update(identity="", source=" ", license=None), ("model_provenance[0].identity", "model_provenance[0].source", "model_provenance[0].license")),
    ("model-anchor", lambda p: p["model_provenance"][0].update(sha256="short", immutable_version=""), ("model_provenance[0].sha256_or_immutable_version",)),
    ("model-download", lambda p: p["model_provenance"][0].update(download_approved=False), ("model_provenance[0].download_approved",)),
    ("reference-array", lambda p: p.__setitem__("reference_provenance", []), ("reference_provenance",)),
    ("reference-path", lambda p: p["reference_provenance"][0].update(path="../outside.bin"), ("reference_provenance[0].sha256",)),
    ("reference-role", lambda p: p["reference_provenance"][0].update(role=" "), ("reference_provenance[0].role",)),
    ("reference-hash-shape", lambda p: p["reference_provenance"][0].update(sha256="short"), ("reference_provenance[0].sha256",)),
    ("reference-hash-bytes", lambda p: p["reference_provenance"][0].update(sha256="0" * 64), ("reference_provenance[0].sha256",)),
    ("reference-license", lambda p: p["reference_provenance"][0].update(license=""), ("reference_provenance[0].license",)),
    ("queue-ids", lambda p: p["queue_attempt"].update(queue_id="", job_id=" ", retry_id=None), ("queue_attempt.queue_id", "queue_attempt.job_id", "queue_attempt.retry_id")),
    ("queue-admission", lambda p: p["queue_attempt"].update(admission_state="rejected"), ("queue_attempt.admission_state",)),
    ("queue-exit", lambda p: p["queue_attempt"].update(exit_status="failed"), ("queue_attempt.exit_status",)),
    ("queue-native-log-warning-ownership", lambda p: p["queue_attempt"].update(native_logs=["host-logs/render.log"]), ("queue_attempt.native_logs[0]",)),
    ("output-array", lambda p: p.__setitem__("output", []), ("output.sha256",)),
    ("output-path", lambda p: p["output"][0].update(path="/outside.mp4"), ("output.sha256[0].sha256",)),
    ("output-hash-shape", lambda p: p["output"][0].update(sha256="short"), ("output.sha256[0].sha256",)),
    ("output-hash-bytes", lambda p: p["output"][0].update(sha256="0" * 64), ("output.sha256[0].sha256",)),
    ("media-exact-coverage", lambda p: p["media_metadata"].append(dict(p["media_metadata"][0], path="outputs/extra.mp4")), ("media_metadata.path",)),
    ("media-kind", lambda p: p["media_metadata"][0].update(kind="audio"), ("media_metadata[0].kind",)),
    ("media-dimensions", lambda p: p["media_metadata"][0].update(width=0, height=-1), ("media_metadata[0].width", "media_metadata[0].height")),
    ("media-alpha", lambda p: p["media_metadata"][0].update(alpha_mode=" "), ("media_metadata[0].alpha_mode",)),
    ("media-audio-present-boolean", lambda p: p["media_metadata"][0]["audio"].update(present="yes"), ("media_metadata[0].audio.present",)),
    ("media-video-duration", lambda p: p["media_metadata"][0].update(duration_s=None), ("media_metadata[0].duration_s",)),
    ("media-video-fps", lambda p: p["media_metadata"][0].update(fps=0), ("media_metadata[0].fps",)),
    ("media-audio-properties", lambda p: p["media_metadata"][0]["audio"].update(codec="", sample_rate_hz=0, channels=-1), ("media_metadata[0].audio.codec", "media_metadata[0].audio.sample_rate_hz", "media_metadata[0].audio.channels")),
    ("media-image-duration-null", lambda p: (_image(p), p["media_metadata"][0].update(duration_s=4.0)), ("media_metadata[0].duration_s",)),
    ("media-image-fps-null", lambda p: (_image(p), p["media_metadata"][0].update(fps=24.0)), ("media_metadata[0].fps",)),
    ("media-image-audio-false", lambda p: (_image(p), p["media_metadata"][0]["audio"].update(present=True)), ("media_metadata[0].audio.present",)),
    ("gate-array", lambda p: p.__setitem__("objective_gate_results", []), ("objective_gate_results",)),
    ("gate-name", lambda p: p["objective_gate_results"][0].update(name=""), ("objective_gate_results[0].name",)),
    ("gate-inputs", lambda p: p["objective_gate_results"][0].update(inputs=[]), ("objective_gate_results[0].inputs",)),
    ("gate-measurements", lambda p: p["objective_gate_results"][0].update(threshold="0.9", measured=True), ("objective_gate_results[0].threshold", "objective_gate_results[0].measured")),
    ("gate-verdict", lambda p: p["objective_gate_results"][0].update(verdict="fail"), ("objective_gate_results[0].verdict",)),
    ("reviewer-decision", lambda p: p["reviewer_verdict"].update(decision="rejected"), ("reviewer_verdict.decision",)),
    ("reviewer-links", lambda p: p["reviewer_verdict"].update(evidence_links=[]), ("reviewer_verdict.evidence_links",)),
)


@pytest.mark.parametrize(
    ("story", "expected"),
    [
        (
            "WD-9t9o",
            {
                "host-logs/edit.render.log": (
                    39,
                    "231e61e337b000739786a58609c06ea3e8b4f546208148f8ef9fe3ea59fab64f",
                    ("mp4_metadata",),
                ),
                "host-logs/repaint.render.log": (
                    40,
                    "7bae39cb07ac15d5697253879e1f9313dfa23981a9dfa017baa3eb864901ca0a",
                    ("mp4_metadata",),
                ),
                "host-logs/upscale.render.log": (
                    12,
                    "91146c81e34bf1f73c214fe6766988d3245de28025b35092f2b2f9802bc4a101",
                    ("mp4_cover_art", "mp4_metadata"),
                ),
            },
        ),
        (
            "WD-isg9",
            {
                "host-logs/edit.render.log": (
                    38,
                    "8de14ecd509f4e163233f2c83caa849e4d2fd85eff6a89d0587f81862f9bd39d",
                    ("mp4_metadata",),
                ),
                "host-logs/repaint.render.log": (
                    39,
                    "46e3fba34575c9f0b539aa6b1971763844dcfa774466009b45c61b3b6d1f1ce3",
                    ("mp4_metadata",),
                ),
                "host-logs/upscale.render.log": (
                    12,
                    "a8ee74be2c9ddaabfedd8128ebd2f06c402881157a711b54872cafb3e2b547a4",
                    ("mp4_cover_art", "mp4_metadata"),
                ),
            },
        ),
    ],
    ids=["WD-9t9o-real-bytes", "WD-isg9-real-bytes"],
)
def test_real_wan2gp_mutagen_logs_are_hashed_and_explicitly_owned(
    story: str, expected: dict[str, tuple[int, str, tuple[str, ...]]]
) -> None:
    """Integrate against committed accepted log bytes, hashes, and warnings."""

    bundle = ROOT / "datasets/runs/maestro-parity" / story
    queue_attempt = {
        "native_logs": list(expected),
        "native_log_sha256": {path: item[1] for path, item in expected.items()},
    }
    warnings, diagnostics = verify_native_logs(bundle, queue_attempt)
    assert diagnostics == ()
    assert [warning.code for warning in warnings] == [
        "WAN2GP_OPTIONAL_MUTAGEN_MISSING" for _ in range(sum(len(item[2]) for item in expected.values()))
    ]
    observed: dict[str, list[tuple[int, str, str]]] = {}
    for warning in warnings:
        observed.setdefault(warning.path, []).append(
            (warning.line, warning.sha256, warning.message)
        )
    for path, (first_line, digest, kinds) in expected.items():
        assert [item[0] for item in observed[path]] == list(
            range(first_line, first_line + len(kinds))
        )
        assert {item[1] for item in observed[path]} == {digest}
        for kind, item in zip(kinds, observed[path], strict=True):
            assert f"Wan2GP {kind} enhancement failed" in item[2]


def test_unrelated_python_import_error_is_not_mislabeled_as_mutagen(tmp_path: Path) -> None:
    source = ROOT / "datasets/runs/maestro-parity/WD-9t9o/host-logs/edit.render.log"
    target = tmp_path / "render.log"
    target.write_bytes(
        source.read_bytes().replace(
            b"No module named 'mutagen'", b"No module named 'some_dependency'"
        )
    )
    warnings, diagnostics = verify_native_logs(tmp_path, {"native_logs": ["render.log"]})
    assert warnings == ()
    assert diagnostics[0].field == "queue_attempt.native_logs[0]"
    assert "unclassified Python import failure 'some_dependency'" in diagnostics[0].message


def test_secondary_import_failure_fails_closed_even_with_owned_mutagen(
    tmp_path: Path,
) -> None:
    source = ROOT / "datasets/runs/maestro-parity/WD-9t9o/host-logs/edit.render.log"
    target = tmp_path / "render.log"
    target.write_bytes(
        source.read_bytes()
        + b"\nNo module named 'secondary_dependency'\n"
    )
    warnings, diagnostics = verify_native_logs(tmp_path, {"native_logs": ["render.log"]})
    secondary = next(
        item for item in diagnostics
        if "unclassified Python import failure 'secondary_dependency'" in item.message
    )
    assert secondary.field == "queue_attempt.native_logs[0]"
    assert warnings


def test_import_error_spelling_fails_closed_as_unclassified_import_failure(
    tmp_path: Path,
) -> None:
    target = tmp_path / "render.log"
    target.write_text(
        "Video file saved to Path: /run/output.mp4\n"
        "ImportError: No module named 'some_dependency'\n",
        encoding="utf-8",
    )
    warnings, diagnostics = verify_native_logs(tmp_path, {"native_logs": ["render.log"]})
    assert warnings == ()
    assert diagnostics[0].field == "queue_attempt.native_logs[0]"
    assert (
        "unclassified Python import failure 'some_dependency' at line 2"
        in diagnostics[0].message
    )


def test_multiple_no_module_named_occurrences_on_one_line_are_ambiguous(
    tmp_path: Path,
) -> None:
    target = tmp_path / "render.log"
    target.write_text(
        "Video file saved to Path: /run/output.mp4\n"
        "No module named 'mutagen' and No module named 'other_module'\n",
        encoding="utf-8",
    )
    warnings, diagnostics = verify_native_logs(tmp_path, {"native_logs": ["render.log"]})
    assert warnings == ()
    assert diagnostics[0].field == "queue_attempt.native_logs[0]"
    assert diagnostics[0].message == (
        "multiple or ambiguous Python import failures at line 2"
    )


def test_missing_native_log_fails_closed(tmp_path: Path) -> None:
    warnings, diagnostics = verify_native_logs(
        tmp_path, {"native_logs": ["host-logs/edit.render.log"]})
    assert warnings == ()
    assert len(diagnostics) == 1
    assert diagnostics[0].field == "queue_attempt.native_logs[0]"
    assert diagnostics[0].message == "file does not exist: host-logs/edit.render.log"


def test_native_log_hash_mismatch_fails_closed(tmp_path: Path) -> None:
    source = ROOT / "datasets/runs/maestro-parity/WD-9t9o/host-logs/edit.render.log"
    target = tmp_path / "render.log"
    target.write_bytes(source.read_bytes())
    warnings, diagnostics = verify_native_logs(tmp_path, {
        "native_logs": ["render.log"],
        "native_log_sha256": {"render.log": "0" * 64},
    })
    assert warnings == ()
    assert diagnostics[0].field == "queue_attempt.native_logs[0].sha256"
    assert diagnostics[0].message.startswith(
        "recorded 0000000000000000000000000000000000000000000000000000000000000000 "
        "but native log bytes hash "
    )


def test_extra_native_log_hash_key_fails_closed(tmp_path: Path) -> None:
    source = ROOT / "datasets/runs/maestro-parity/WD-9t9o/host-logs/edit.render.log"
    target = tmp_path / "render.log"
    target.write_bytes(source.read_bytes())
    warnings, diagnostics = verify_native_logs(tmp_path, {
        "native_logs": ["render.log"],
        "native_log_sha256": {
            "render.log": hashlib.sha256(target.read_bytes()).hexdigest(),
            "host-logs/extra.render.log": "A" * 64,
        },
    })
    key_set = next(
        item for item in diagnostics
        if item.field == "queue_attempt.native_log_sha256"
    )
    assert key_set.message == (
        "key set must exactly match deduplicated native_logs: "
        "extra ['host-logs/extra.render.log']"
    )
    assert warnings


def test_mutagen_warning_without_media_save_marker_fails_closed(tmp_path: Path) -> None:
    source = ROOT / "datasets/runs/maestro-parity/WD-9t9o/host-logs/upscale.render.log"
    target = tmp_path / "render.log"
    target.write_bytes(
        source.read_bytes().replace(b"Postprocessed video saved to Path: ", b"removed: ")
    )
    warnings, diagnostics = verify_native_logs(tmp_path, {"native_logs": ["render.log"]})
    assert warnings == ()
    assert len(diagnostics) == 2
    assert {diagnostic.message for diagnostic in diagnostics} == {
        "mp4_cover_art mutagen warning has no successful media-save marker",
        "mp4_metadata mutagen warning has no successful media-save marker",
    }


@pytest.mark.parametrize(("constraint", "change", "expected"), CONSTRAINT_CASES, ids=[case[0] for case in CONSTRAINT_CASES])
def test_contract_constraint_violations_fail(
    tmp_path: Path, constraint: str, change: Any, expected: tuple[str, ...]
) -> None:
    root = tmp_path / constraint
    payload = _write_bundle(root)
    change(payload)
    report = _record_and_verify(root, payload)
    assert not report.passed
    assert set(expected) <= set(_diagnostic_fields(report))


def test_every_documented_constraint_has_a_real_violation_test() -> None:
    assert tuple(case[0] for case in CONSTRAINT_CASES) == canonical_constraints()


@pytest.mark.parametrize(
    ("group", "path"),
    [("reference", "inputs/reference-link"), ("output", "inputs/reference-link")],
    ids=["reference-symlink", "output-symlink"],
)
def test_paths_must_be_regular_files_not_symlinks(
    tmp_path: Path, group: str, path: str
) -> None:
    root = tmp_path / f"{group}-symlink"
    payload = _write_bundle(root)
    reference_hash = payload["reference_provenance"][0]["sha256"]
    if group == "reference":
        payload["reference_provenance"][0]["path"] = path
    else:
        payload["output"][0].update(path=path, sha256=reference_hash)
    report = _record_and_verify(root, payload)
    assert not report.passed
    prefix = "reference_provenance" if group == "reference" else "output.sha256"
    assert f"{prefix}[0].sha256" in _diagnostic_fields(report)


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
    rows = re.findall(r"^\| `([^`]+)` \| ([^|]+) \| (.+) \|$", match.group(1), flags=re.MULTILINE)
    fields = tuple(row[0] for row in rows)
    assert fields, "contract has no canonical field table"
    assert tuple(fields) == canonical_field_ids()
    for field, raw_ids, statement in rows:
        ids = tuple(item.strip("` ") for item in raw_ids.split(","))
        assert ids == contract_rows()[field][0]
        assert statement == contract_rows()[field][1]


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
