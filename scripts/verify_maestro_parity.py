#!/usr/bin/env python3
"""Fail-closed verifier for Maestro-parity evidence bundles."""
from __future__ import annotations
import argparse, hashlib, json, sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

SCHEMA = "wangp-dspy.maestro-parity-evidence/v1"
MANIFEST = "evidence.json"
CONTRACT_FIELD_IDS = ("operator_authorization", "command", "repository.commit", "model_provenance", "reference_provenance", "queue_attempt", "output.sha256", "media_metadata", "objective_gate_results", "reviewer_verdict")
ROOT_KEYS = {"operator_authorization": "operator_authorization", "command": "command", "repository.commit": "repository", "model_provenance": "model_provenance", "reference_provenance": "reference_provenance", "queue_attempt": "queue_attempt", "output.sha256": "output", "media_metadata": "media_metadata", "objective_gate_results": "objective_gate_results", "reviewer_verdict": "reviewer_verdict"}
ARRAY, OBJECT, VALUE = "array", "object", "value"
RULES = {
    "operator_authorization": (OBJECT, {"status": (VALUE, "approved"), "text": "text", "scope": "text", "timestamp": "timestamp", "approved_by": "text"}),
    "command": "argv",
    "repository": (OBJECT, {"commit": "commit", "dirty_state": (OBJECT, {"dirty": "boolean", "identity_sha256": "sha256"})}),
    "model_provenance": (ARRAY, (OBJECT, {"identity": "text", "source": "text", "license": "text", "download_approved": (VALUE, True)})),
    "reference_provenance": (ARRAY, (OBJECT, {"path": "text", "role": "text", "sha256": "sha256", "license": "text"})),
    "queue_attempt": (OBJECT, {"queue_id": "text", "job_id": "text", "admission_state": (VALUE, "admitted"), "exit_status": (VALUE, "succeeded"), "retry_id": "text"}),
    "output": (ARRAY, (OBJECT, {"path": "text", "sha256": "sha256"})),
    "media_metadata": (ARRAY, (OBJECT, {"path": "text", "kind": (VALUE, ("image", "video")), "width": "positive_integer", "height": "positive_integer", "duration_s": "nullable_positive_number", "fps": "nullable_positive_number", "audio": (OBJECT, {"present": "boolean"}), "alpha_mode": "text"})),
    "objective_gate_results": (ARRAY, (OBJECT, {"name": "text", "inputs": (ARRAY, "text"), "threshold": "number", "measured": "number", "verdict": (VALUE, "pass")})),
    "reviewer_verdict": (OBJECT, {"decision": (VALUE, "approved"), "evidence_links": (ARRAY, "text")}),
}


@dataclass(frozen=True)
class Diagnostic:
    field: str
    message: str


@dataclass(frozen=True)
class VerificationReport:
    bundle: Path
    passed: bool
    diagnostics: tuple[Diagnostic, ...]


def canonical_field_ids() -> tuple[str, ...]:
    """Return the canonical field-group list shared with the contract."""
    return CONTRACT_FIELD_IDS


def verify_bundle(bundle: Path) -> VerificationReport:
    """Validate a bundle read-only and report every named failure possible."""
    root = bundle.resolve()
    if not root.is_dir():
        return VerificationReport(bundle, False, (Diagnostic("bundle", "not a directory"),))
    try:
        payload = json.loads((root / MANIFEST).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return VerificationReport(bundle, False, (Diagnostic("manifest", str(exc)),))
    if not isinstance(payload, dict):
        return VerificationReport(bundle, False, (Diagnostic("manifest", "root must be an object"),))
    diagnostics: list[Diagnostic] = []
    if payload.get("schema") != SCHEMA:
        diagnostics.append(Diagnostic("schema", f"must be {SCHEMA}"))
    for field, key in ROOT_KEYS.items():
        if key not in payload:
            diagnostics.append(Diagnostic(field, "missing required field group"))
        else:
            _validate(payload[key], RULES[key], field, diagnostics)
    for index, model in enumerate(_items(payload, "model_provenance")):
        if isinstance(model, dict) and not (
            _valid(model.get("sha256"), "sha256")
            or _valid(model.get("immutable_version"), "text")
        ):
            diagnostics.append(Diagnostic(
                f"model_provenance[{index}].sha256_or_immutable_version",
                "requires a SHA-256 or non-blank immutable version"))
    _hash_entries(root, _items(payload, "reference_provenance"),
                  "reference_provenance", diagnostics)
    output_paths = _hash_entries(
        root, _items(payload, "output"), "output.sha256", diagnostics)
    _validate_media(payload.get("media_metadata"), output_paths, diagnostics)
    return VerificationReport(bundle, not diagnostics, tuple(diagnostics))


def _items(payload: dict[str, Any], key: str) -> list[Any]:
    value = payload.get(key)
    return value if isinstance(value, list) else []


def _hash_entries(
    root: Path, entries: list[Any], prefix: str, diagnostics: list[Diagnostic]) -> list[str]:
    paths: list[str] = []
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            continue
        relative = entry.get("path")
        field = f"{prefix}[{index}].sha256"
        if not isinstance(relative, str) or not relative.strip():
            continue
        paths.append(relative)
        path = (root / relative).resolve()
        try:
            path.relative_to(root)
        except ValueError:
            diagnostics.append(Diagnostic(field, f"path escapes bundle: {relative}"))
            continue
        if not path.is_file():
            diagnostics.append(Diagnostic(field, f"file does not exist: {relative}"))
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != entry.get("sha256"):
            diagnostics.append(Diagnostic(
                field, f"recorded {entry.get('sha256')} but artifact bytes hash {actual}"))
    return paths


def _validate_media(
    value: Any, output_paths: list[str], diagnostics: list[Diagnostic]) -> None:
    entries = value if isinstance(value, list) else []
    paths = [entry.get("path") for entry in entries if isinstance(entry, dict)
             and isinstance(entry.get("path"), str) and entry["path"].strip()]
    if sorted(paths) != sorted(output_paths):
        diagnostics.append(Diagnostic(
            "media_metadata.path",
            "must describe every output artifact and no other path"))
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict) or not isinstance(entry.get("audio"), dict):
            continue
        prefix = f"media_metadata[{index}].audio"
        audio = entry["audio"]
        if audio.get("present") is not False:
            for key, kind in (("codec", "text"), ("sample_rate_hz", "positive_integer"),
                              ("channels", "positive_integer")):
                if not _valid(audio.get(key), kind):
                    diagnostics.append(Diagnostic(f"{prefix}.{key}", _message(kind)))
        if entry.get("kind") == "image" and (
            entry.get("duration_s") is not None or entry.get("fps") is not None
        ):
            diagnostics.append(Diagnostic(
                f"media_metadata[{index}].duration_s/fps",
                "must be null for an image"))


def _validate(value: Any, rule: Any, field: str, diagnostics: list[Diagnostic]) -> None:
    if rule == "argv":
        if not isinstance(value, list) or not value or any(
            not isinstance(item, str) or not item.strip() for item in value
        ):
            diagnostics.append(Diagnostic(field, "must be a non-empty text argv array"))
    elif isinstance(rule, str):
        if not _valid(value, rule):
            diagnostics.append(Diagnostic(field, _message(rule)))
    elif rule[0] == VALUE:
        expected = rule[1]
        valid = value in expected if isinstance(expected, tuple) else value == expected
        if not valid:
            diagnostics.append(Diagnostic(field, f"must be {expected}"))
    elif rule[0] == OBJECT:
        if not isinstance(value, dict):
            diagnostics.append(Diagnostic(field, "must be an object"))
            return
        for key, nested in rule[1].items():
            _validate(value.get(key), nested, f"{field}.{key}", diagnostics)
    elif rule[0] == ARRAY:
        if not isinstance(value, list) or not value:
            diagnostics.append(Diagnostic(field, "must be a non-empty array"))
            return
        for index, item in enumerate(value):
            _validate(item, rule[1], f"{field}[{index}]", diagnostics)


def _valid(value: Any, kind: str) -> bool:
    text = isinstance(value, str) and bool(value.strip())
    if kind == "text":
        return text
    if kind == "timestamp":
        try:
            return text and datetime.fromisoformat(value.replace("Z", "+00:00")) is not None
        except ValueError:
            return False
    if kind in {"commit", "sha256"}:
        size = 40 if kind == "commit" else 64
        return text and len(value) == size and all(
            character in "0123456789abcdefABCDEF" for character in value)
    if kind == "boolean":
        return isinstance(value, bool)
    if kind == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if kind == "positive_integer":
        return isinstance(value, int) and not isinstance(value, bool) and value > 0
    if kind == "nullable_positive_number":
        return value is None or _valid(value, "positive_number")
    return isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0


def _message(kind: str) -> str:
    return {
        "text": "must be non-blank text", "timestamp": "must be RFC 3339",
        "commit": "must be a 40-character hex SHA",
        "sha256": "must be a 64-character hex SHA-256",
        "boolean": "must be true or false", "number": "must be numeric",
        "positive_integer": "must be a positive integer",
        "positive_number": "must be a positive number",
        "nullable_positive_number": "must be null or a positive number",
    }[kind]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path)
    arguments = parser.parse_args(argv)
    report = verify_bundle(arguments.bundle)
    if report.passed:
        print(f"PASS {SCHEMA} {arguments.bundle}")
        return 0
    for diagnostic in report.diagnostics:
        print(f"FAIL {diagnostic.field}: {diagnostic.message}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
