#!/usr/bin/env python3
"""Fail-closed verifier for Maestro-parity evidence bundles."""
from __future__ import annotations
import argparse, hashlib, json, re, sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any

SCHEMA = "wangp-dspy.maestro-parity-evidence/v1"
MANIFEST = "evidence.json"
CONTRACT_FIELD_IDS = ("operator_authorization", "command", "repository.commit", "model_provenance", "reference_provenance", "queue_attempt", "output.sha256", "media_metadata", "objective_gate_results", "reviewer_verdict")
ROOT_KEYS = {"operator_authorization": "operator_authorization", "command": "command", "repository.commit": "repository", "model_provenance": "model_provenance", "reference_provenance": "reference_provenance", "queue_attempt": "queue_attempt", "output.sha256": "output", "media_metadata": "media_metadata", "objective_gate_results": "objective_gate_results", "reviewer_verdict": "reviewer_verdict"}
CONTRACT_ROWS = {
    "operator_authorization": (("auth-status", "auth-required-text", "auth-timestamp"), "Non-empty object with non-blank `text`, `scope`, RFC 3339 `timestamp`, and `approved_by`; `status` must be `approved`. Anything denied, absent, or blank fails."),
    "command": (("command-argv",), "Non-empty array containing the exact executable argv in order. Every element must be non-blank text; the checker does not reconstruct or substitute arguments."),
    "repository.commit": (("repo-commit", "repo-dirty-state"), "Object with non-blank `commit` (40 lowercase/uppercase hexadecimal characters) and `dirty_state`. `dirty_state.dirty` must be boolean and `identity_sha256` must be a 64-character hexadecimal SHA-256 that captures the dirty-state identity."),
    "model_provenance": (("model-array", "model-required-text", "model-anchor", "model-download"), "Non-empty array. Each item requires non-blank `identity`, `source`, and `license`; either `sha256` (64 hexadecimal characters) or non-blank `immutable_version`; and `download_approved: true`. A model lacking both identity anchors or download approval fails."),
    "reference_provenance": (("reference-array", "reference-path", "reference-role", "reference-hash-shape", "reference-hash-bytes", "reference-license"), "Non-empty array. Every reference requires a bundle-relative `path`, non-blank `role`, a 64-character `sha256`, and non-blank `license`. The path must identify a regular file in the bundle, and its actual SHA-256 must equal the recorded value."),
    "queue_attempt": (("queue-ids", "queue-admission", "queue-exit", "queue-native-log-warning-ownership"), "Object with non-blank durable `queue_id`, `job_id`, and `retry_id`; `admission_state` must be `admitted`; `exit_status` must be `succeeded`. Optional `native_logs` use the strict bundle path resolver and are regular files. Every `No module named`, `ModuleNotFoundError`, or `ImportError` line in a referenced native log must have exactly one unambiguous classification: only the exact successful-save Wan2GP mutagen metadata/cover-art forms and exact `optional_import_fallbacks` records for eligible `flash_attn`, `piexif`, or `postprocessing` import lines become owned warnings. Each optional record must bind the exact import and exact fallback/success marker paths, lines, kinds, and text in hash-matched native logs. Unknown modules, generic exceptions, changed hashes, malformed or unmatched records, and missing success markers fail. When present, `native_log_sha256` values are valid 64-character hexadecimal SHA-256 values (case-insensitive), its key set exactly matches deduplicated `native_logs`, and each value matches exact log bytes."),
    "output.sha256": (("output-array", "output-path", "output-hash-shape", "output-hash-bytes"), "Non-empty array with bundle-relative `path` and 64-character `sha256` for every emitted artifact. Every path must identify a regular file in the bundle, and hashing its exact bytes must reproduce the recorded value. One mismatch fails the entire bundle."),
    "media_metadata": (("media-exact-coverage", "media-kind", "media-dimensions", "media-alpha", "media-audio-present-boolean", "media-video-duration", "media-video-fps", "media-audio-properties", "media-image-duration-null", "media-image-fps-null", "media-image-audio-false"), "Non-empty array with exactly one entry for every `output.sha256` path and no others. Each entry has `path`, `kind`, positive integer `width` and `height`, non-blank `alpha_mode`, and an `audio` object whose `present` is boolean. For `kind: video`, `duration_s` and `fps` are positive numbers; when audio is present, non-blank `codec`, positive integer `sample_rate_hz`, and positive integer `channels` are required. For `kind: image`, `duration_s` and `fps` are null and `audio.present` is false."),
    "objective_gate_results": (("gate-array", "gate-name", "gate-inputs", "gate-measurements", "gate-verdict"), "Non-empty array for every declared objective gate. Each item has non-blank `name`, a non-empty `inputs` array of non-blank values, numeric `threshold`, numeric `measured`, and `verdict`. Only `pass` is acceptable for a verified parity row; failing or omitted gates fail."),
    "reviewer_verdict": (("reviewer-decision", "reviewer-links"), "Object with `decision: approved` and a non-empty `evidence_links` array of non-blank links to the reviewer's evidence."),
}
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
_MUTAGEN_METADATA = re.compile(
    r"^.*Error saving metadata to MP4 (?P<path>.+): No module named 'mutagen'$"
)
_MUTAGEN_COVER_ART = re.compile(
    r"^.*Error extracting cover art from MP4: No module named 'mutagen'$"
)
_PYTHON_IMPORT_ERROR = re.compile(r"No module named '(?P<module>[^']+)'")
_PYTHON_IMPORT_EXCEPTION = re.compile(r"\b(?:ModuleNotFoundError|ImportError)\b")
_WAN2GP_SAVE = re.compile(
    r"(?:Video file|Postprocessed video) saved to Path: (?P<path>.+)$"
)
_OPTIONAL_IMPORT_MODULES = {"flash_attn", "piexif", "postprocessing"}
_FLASH_FALLBACK_TEXTS = {
    "flash_attn not installed, disabling Flash Attention",
    "flash_attn varlen/bert_padding not available, disabling varlen attention",
}
_AUDIO_SAVE_TEXT = re.compile(r"^Audio file saved to Path: .+$")
_IMAGE_SAVE_TEXT = re.compile(r"^Image file saved to Path: .+$")
_FFMPEG_TARGET_TEXT = re.compile(r"^Output #0, mp4, to '.+\.mp4':$")
_FFMPEG_COMPLETE_TEXT = re.compile(
    r"^frame=\s+\d+\s+fps=\S+\s+q=\S+\s+Lsize=\s+\d+kB\s+time=\S+\s+.+$"
)
_OPTIONAL_IMPORT_ENTRY_KEYS = {
    "module", "import", "fallback_marker", "success_marker"
}
_OPTIONAL_IMPORT_LOCATION_KEYS = {"path", "line"}
_OPTIONAL_IMPORT_MARKER_KEYS = {"path", "line", "kind", "text"}


@dataclass(frozen=True)
class Diagnostic:
    field: str
    message: str


@dataclass(frozen=True)
class EvidenceWarning:
    """One classified, explicitly owned nonfatal condition in native evidence."""

    code: str
    path: str
    line: int
    sha256: str
    message: str


@dataclass(frozen=True)
class VerificationReport:
    bundle: Path
    passed: bool
    diagnostics: tuple[Diagnostic, ...]
    warnings: tuple[EvidenceWarning, ...] = ()


@dataclass(frozen=True)
class _NativeLogContext:
    lines: tuple[str, ...]
    sha256: str
    hash_matches: bool


@dataclass(frozen=True)
class _OptionalImportFallback:
    module: str
    path: str
    line: int


def _exact_keys(value: Any, expected: set[str], field: str,
                diagnostics: list[Diagnostic]) -> bool:
    if not isinstance(value, dict) or set(value) != expected:
        diagnostics.append(Diagnostic(
            field, f"must be an object with exactly {sorted(expected)}"
        ))
        return False
    return True


def _positive_line(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _marker_text(
    marker: dict[str, Any], field: str, contexts: dict[str, _NativeLogContext],
    diagnostics: list[Diagnostic],
) -> tuple[str, int, str] | None:
    path = marker.get("path")
    line_number = marker.get("line")
    text = marker.get("text")
    if not isinstance(path, str) or path not in contexts:
        diagnostics.append(Diagnostic(
            field + ".path", f"must name a referenced hash-matched native log: {path}"
        ))
        return None
    if not _positive_line(line_number) or line_number > len(contexts[path].lines):
        diagnostics.append(Diagnostic(field + ".line", "must name an existing log line"))
        return None
    if not isinstance(text, str) or not text.strip():
        diagnostics.append(Diagnostic(field + ".text", "must be non-blank text"))
        return None
    if text not in contexts[path].lines[line_number - 1]:
        diagnostics.append(Diagnostic(
            field + ".text", "recorded marker text is absent from the named native log line"
        ))
        return None
    return path, line_number, text


def _validate_optional_marker(
    value: Any, field: str, expected_kind: str,
    contexts: dict[str, _NativeLogContext], diagnostics: list[Diagnostic],
) -> tuple[str, int, str] | None:
    if not _exact_keys(
            value, _OPTIONAL_IMPORT_MARKER_KEYS, field, diagnostics):
        return None
    assert isinstance(value, dict)
    if value.get("kind") != expected_kind:
        diagnostics.append(Diagnostic(
            field + ".kind", f"must be {expected_kind}"
        ))
        return None
    marker = _marker_text(value, field, contexts, diagnostics)
    if marker is None:
        return None
    _, _, text = marker
    matches = (
        text in _FLASH_FALLBACK_TEXTS
        if expected_kind == "flash_attention_disabled"
        else {
            "image_metadata_save_failed": text == (
                "Error saving metadata: No module named 'piexif'"
            ),
            "audio_file_saved": bool(_AUDIO_SAVE_TEXT.fullmatch(text)),
            "image_file_saved": bool(_IMAGE_SAVE_TEXT.fullmatch(text)),
            "ffmpeg_output_target": bool(_FFMPEG_TARGET_TEXT.fullmatch(text)),
            "ffmpeg_encode_complete": bool(_FFMPEG_COMPLETE_TEXT.fullmatch(text)),
        }.get(expected_kind, False)
    )
    if not matches:
        diagnostics.append(Diagnostic(
            field,
            f"marker kind {expected_kind} does not match text"
        ))
        return None
    return marker


def _validate_optional_import_fallback(
    index: int, value: Any, raw_logs: list[Any],
    contexts: dict[str, _NativeLogContext],
    diagnostics: list[Diagnostic],
) -> _OptionalImportFallback | None:
    field = f"queue_attempt.optional_import_fallbacks[{index}]"
    if not _exact_keys(
            value, _OPTIONAL_IMPORT_ENTRY_KEYS, field, diagnostics):
        return None
    assert isinstance(value, dict)
    module = value.get("module")
    if not isinstance(module, str) or not module.strip():
        diagnostics.append(Diagnostic(field + ".module", "must be non-blank text"))
        return None
    if module not in _OPTIONAL_IMPORT_MODULES:
        diagnostics.append(Diagnostic(
            field + ".module",
            f"module {module!r} is not eligible for optional import fallback classification"
        ))
        return None
    import_location = value.get("import")
    if not _exact_keys(
            import_location, _OPTIONAL_IMPORT_LOCATION_KEYS,
            field + ".import", diagnostics):
        return None
    assert isinstance(import_location, dict)
    path = import_location.get("path")
    line_number = import_location.get("line")
    if not isinstance(path, str) or path not in contexts:
        diagnostics.append(Diagnostic(
            field + ".import.path",
            f"must name a referenced hash-matched native log: {path}"
        ))
        return None
    if not _positive_line(line_number) or line_number > len(contexts[path].lines):
        diagnostics.append(Diagnostic(
            field + ".import.line", "must name an existing native log line"
        ))
        return None
    line = contexts[path].lines[line_number - 1]
    import_match = _PYTHON_IMPORT_ERROR.search(line)
    if import_match is None or import_match.group("module") != module:
        diagnostics.append(Diagnostic(
            field + ".import",
            "named line is not the exact declared Python import failure"
        ))
        return None

    fallback = _validate_optional_marker(
        value.get("fallback_marker"),
        field + ".fallback_marker",
        {
            "flash_attn": "flash_attention_disabled",
            "piexif": "image_metadata_save_failed",
            "postprocessing": "ffmpeg_output_target",
        }[module],
        contexts,
        diagnostics,
    )
    success = _validate_optional_marker(
        value.get("success_marker"),
        field + ".success_marker",
        {
            "flash_attn": "audio_file_saved",
            "piexif": "image_file_saved",
            "postprocessing": "ffmpeg_encode_complete",
        }[module],
        contexts,
        diagnostics,
    )
    if fallback is None or success is None:
        return None
    if module in {"flash_attn", "piexif"}:
        fallback_valid = (
            fallback[0] == path
            and fallback[1] == line_number + (module == "flash_attn")
            and fallback[1] <= success[1]
            and line_number <= success[1]
        )
    else:
        fallback_valid = (
            fallback[0] == path
            and success[0] == path
            and fallback[1] < success[1] < line_number
        )
    if not fallback_valid:
        diagnostics.append(Diagnostic(
            field,
            "fallback and success markers do not establish the required output boundary"
        ))
        return None
    return _OptionalImportFallback(module, path, line_number)


def canonical_field_ids() -> tuple[str, ...]:
    """Return the canonical field-group list shared with the contract."""
    return CONTRACT_FIELD_IDS


def canonical_constraints() -> tuple[str, ...]:
    """Return every normative constraint ID shared by code, document, and tests."""
    return tuple(item for row in CONTRACT_ROWS.values() for item in row[0])


def contract_rows() -> dict[str, tuple[tuple[str, ...], str]]:
    """Return the machine-readable contract rows rendered by the document."""
    return CONTRACT_ROWS


def _safe_bundle_file(
    root: Path, relative: Any, field: str, diagnostics: list[Diagnostic]
) -> Path | None:
    """Resolve one strict bundle-relative regular file or fail closed."""

    if not isinstance(relative, str) or not relative.strip():
        diagnostics.append(Diagnostic(
            field, "must be a non-blank bundle-relative path"))
        return None
    posix_relative = PurePosixPath(relative)
    if posix_relative.is_absolute() or Path(relative).is_absolute():
        diagnostics.append(Diagnostic(
            field, f"path must be bundle-relative, not absolute: {relative}"))
        return None
    parts = posix_relative.parts
    if ".." in parts:
        diagnostics.append(Diagnostic(
            field, f"path contains a lexical '..' component: {relative}"))
        return None

    inspected = root
    try:
        for component in parts:
            inspected /= component
            if inspected.is_symlink():
                diagnostics.append(Diagnostic(
                    field, f"path contains a symlinked component: {relative}"))
                return None
        path = (root / Path(*parts)).resolve()
        path.relative_to(root)
    except (OSError, ValueError, RuntimeError):
        diagnostics.append(Diagnostic(
            field, f"path is not a safe bundle file: {relative}"))
        return None
    if not path.is_file():
        diagnostics.append(Diagnostic(field, f"file does not exist: {relative}"))
        return None
    return path


def _normalized_sha256(value: Any) -> str | None:
    if not _valid(value, "sha256"):
        return None
    return str(value).lower()


def verify_native_logs(
    root: Path, queue_attempt: Any
) -> tuple[tuple[EvidenceWarning, ...], tuple[Diagnostic, ...]]:
    """Classify Wan2GP native logs read-only and own every known warning.

    A missing or non-regular referenced log, a mutagen warning without a
    successful media-save marker, and an unrelated Python import error all
    fail closed. The two observed Wan2GP ``mutagen`` failures are warnings,
    not ordinary success output: they are returned with stable ownership
    metadata and the exact log SHA-256, and Wangp never installs anything.
    """

    if not isinstance(queue_attempt, dict):
        return (), ()
    raw_logs = queue_attempt.get("native_logs", [])
    expected_hashes = queue_attempt.get("native_log_sha256")
    if not isinstance(raw_logs, list):
        return (), (Diagnostic(
            "queue_attempt.native_logs", "must be an array of bundle-relative paths"
        ),)
    if expected_hashes is not None and not isinstance(expected_hashes, dict):
        return (), (Diagnostic(
            "queue_attempt.native_log_sha256", "must be an object keyed by log path"
        ),)

    warnings: list[EvidenceWarning] = []
    diagnostics: list[Diagnostic] = []
    if isinstance(expected_hashes, dict):
        declared_logs = {
            value for value in raw_logs
            if isinstance(value, str) and value.strip()
        }
        hash_keys = set(expected_hashes)
        if hash_keys != declared_logs:
            missing = sorted(declared_logs - hash_keys)
            extras = sorted(hash_keys - declared_logs)
            details = []
            if missing:
                details.append(f"missing {missing}")
            if extras:
                details.append(f"extra {extras}")
            diagnostics.append(Diagnostic(
                "queue_attempt.native_log_sha256",
                "key set must exactly match deduplicated native_logs: "
                + "; ".join(details),
            ))
        for key, value in expected_hashes.items():
            if _normalized_sha256(value) is None:
                diagnostics.append(Diagnostic(
                    f"queue_attempt.native_log_sha256[{key}]",
                    "must be a 64-character hex SHA-256",
                ))

    contexts: dict[str, _NativeLogContext] = {}
    seen: set[str] = set()
    for index, relative in enumerate(raw_logs):
        field = f"queue_attempt.native_logs[{index}]"
        if not isinstance(relative, str) or not relative.strip():
            diagnostics.append(Diagnostic(field, "must be a non-blank bundle-relative path"))
            continue
        if relative in seen:
            diagnostics.append(Diagnostic(field, f"duplicate native log path: {relative}"))
            continue
        seen.add(relative)
        path = _safe_bundle_file(root, relative, field, diagnostics)
        if path is None:
            continue
        data = path.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        hash_matches = True
        if isinstance(expected_hashes, dict):
            expected = expected_hashes.get(relative)
            normalized_expected = _normalized_sha256(expected)
            if normalized_expected is None or normalized_expected != digest:
                hash_matches = False
                diagnostics.append(Diagnostic(
                    f"{field}.sha256",
                    f"recorded {expected} but native log bytes hash {digest}",
                ))
        text = data.decode("utf-8", errors="replace")
        contexts[relative] = _NativeLogContext(
            tuple(text.split("\n")), digest, hash_matches
        )
        if not hash_matches:
            continue

    optional_imports: dict[tuple[str, str, int], _OptionalImportFallback] = {}
    optional_declarations = queue_attempt.get("optional_import_fallbacks")
    if optional_declarations is not None:
        if not isinstance(optional_declarations, list):
            diagnostics.append(Diagnostic(
                "queue_attempt.optional_import_fallbacks",
                "must be an array of exact import ownership records",
            ))
        elif expected_hashes is None:
            diagnostics.append(Diagnostic(
                "queue_attempt.optional_import_fallbacks",
                "requires native_log_sha256 for every referenced native log",
            ))
        else:
            for index, declaration in enumerate(optional_declarations):
                fallback = _validate_optional_import_fallback(
                    index, declaration, raw_logs, contexts, diagnostics
                )
                if fallback is None:
                    continue
                key = (fallback.module, fallback.path, fallback.line)
                if key in optional_imports:
                    diagnostics.append(Diagnostic(
                        f"queue_attempt.optional_import_fallbacks[{index}]",
                        f"duplicate optional import classification: {key}",
                    ))
                    continue
                optional_imports[key] = fallback

    used_optional_imports: set[tuple[str, str, int]] = set()
    for relative, context in contexts.items():
        if not context.hash_matches:
            continue
        field = f"queue_attempt.native_logs[{raw_logs.index(relative)}]"
        saved_paths: set[str] = set()
        for line in context.lines:
            save_match = _WAN2GP_SAVE.search(line)
            if save_match is not None:
                saved_paths.add(save_match.group("path"))
        for line_number, line in enumerate(context.lines, start=1):
            import_failures = list(_PYTHON_IMPORT_ERROR.finditer(line))
            import_exceptions = list(_PYTHON_IMPORT_EXCEPTION.finditer(line))
            if not import_failures and not import_exceptions:
                continue
            if len(import_failures) > 1 or len(import_exceptions) > 1:
                diagnostics.append(Diagnostic(
                    field,
                    f"multiple or ambiguous Python import failures at line {line_number}",
                ))
                continue
            if not import_failures:
                diagnostics.append(Diagnostic(
                    field,
                    f"unclassified Python import exception at line {line_number}: {line.strip()}",
                ))
                continue
            module = import_failures[0].group("module")
            metadata_match = _MUTAGEN_METADATA.search(line)
            cover_match = _MUTAGEN_COVER_ART.search(line)
            if module == "mutagen" and metadata_match:
                kind = "mp4_metadata"
            elif module == "mutagen" and cover_match:
                kind = "mp4_cover_art"
            elif module == "mutagen":
                diagnostics.append(Diagnostic(
                    field,
                    f"unrecognized mutagen import failure at line {line_number}: {line.strip()}",
                ))
                continue
            elif (module, relative, line_number) in optional_imports:
                used_optional_imports.add((module, relative, line_number))
                warnings.append(EvidenceWarning(
                    code="OPTIONAL_IMPORT_FALLBACK",
                    path=relative,
                    line=line_number,
                    sha256=context.sha256,
                    message=(
                        f"optional {module} import fallback is explicitly owned; "
                        "exact fallback and successful output markers are hash-bound "
                        "in immutable native logs"
                    ),
                ))
                continue
            else:
                diagnostics.append(Diagnostic(
                    field,
                    f"unclassified Python import failure {module!r} at line {line_number}",
                ))
                continue
            media_path = (
                metadata_match.group("path") if metadata_match
                else next(iter(saved_paths), None)
            )
            if media_path is None or media_path not in saved_paths:
                diagnostics.append(Diagnostic(
                    field,
                    f"{kind} mutagen warning has no successful media-save marker",
                ))
                continue
            warnings.append(EvidenceWarning(
                code="WAN2GP_OPTIONAL_MUTAGEN_MISSING",
                path=relative,
                line=line_number,
                sha256=context.sha256,
                message=(
                    f"Wan2GP {kind} enhancement failed because the active "
                    "Wan2GP venv lacks mutagen; saved media bytes remain the "
                    "success boundary and no ad hoc host install is authorized"
                ),
                ))
    extras = set(optional_imports) - used_optional_imports
    if extras:
        diagnostics.append(Diagnostic(
            "queue_attempt.optional_import_fallbacks",
            f"unmatched classifications: {sorted(extras)}",
        ))
    return tuple(warnings), tuple(diagnostics)


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
    warnings, log_diagnostics = verify_native_logs(
        root, payload.get("queue_attempt"))
    diagnostics.extend(log_diagnostics)
    return VerificationReport(
        bundle, not diagnostics, tuple(diagnostics), warnings)


def _bundle_identity_sha256(bundle: Path) -> str:
    """Hash a stable path-and-byte identity for every immutable bundle file."""

    identity = hashlib.sha256()
    for path in sorted(bundle.rglob("*")):
        relative = path.relative_to(bundle).as_posix().encode("utf-8")
        if path.is_symlink():
            raise ValueError(f"bundle identity requires regular files only: {relative}")
        if not path.is_file():
            continue
        identity.update(relative)
        identity.update(b"\0")
        identity.update(hashlib.sha256(path.read_bytes()).hexdigest().encode("ascii"))
        identity.update(b"\0")
    return identity.hexdigest()


def verify_checker_receipt(
    repository_root: Path, receipt_path: Path
) -> VerificationReport:
    """Fail closed when the canonical lane receipt drifts from repository bytes."""

    root = repository_root.resolve()
    diagnostics: list[Diagnostic] = []
    try:
        payload = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return VerificationReport(receipt_path, False, (Diagnostic("receipt", str(exc)),))
    required_keys = {
        "schema", "machine", "checker_commit", "checker_sha256", "lanes"
    }
    if not isinstance(payload, dict) or set(payload) != required_keys:
        return VerificationReport(receipt_path, False, (Diagnostic(
            "receipt", f"must be an object with exactly {sorted(required_keys)}"
        ),))
    if payload.get("schema") != "wangp-dspy.maestro-parity-checker-receipt/v1":
        diagnostics.append(Diagnostic(
            "receipt.schema", "must be wangp-dspy.maestro-parity-checker-receipt/v1"
        ))
    machine = payload.get("machine")
    if not isinstance(machine, dict) or not (
        _valid(machine.get("host"), "text")
        and _valid(machine.get("python"), "text")
    ):
        diagnostics.append(Diagnostic(
            "receipt.machine", "requires non-blank host and python"
        ))
    if not _valid(payload.get("checker_commit"), "commit"):
        diagnostics.append(Diagnostic(
            "receipt.checker_commit", "must be a 40-character hex commit"
        ))
    checker = root / "scripts/verify_maestro_parity.py"
    try:
        actual_checker_hash = hashlib.sha256(checker.read_bytes()).hexdigest()
    except OSError as exc:
        return VerificationReport(receipt_path, False, (Diagnostic(
            "receipt.checker_sha256", str(exc)
        ),))
    if payload.get("checker_sha256") != actual_checker_hash:
        diagnostics.append(Diagnostic(
            "receipt.checker_sha256",
            f"recorded {payload.get('checker_sha256')} but checker bytes hash "
            f"{actual_checker_hash}",
        ))

    lanes = payload.get("lanes")
    if not isinstance(lanes, list):
        diagnostics.append(Diagnostic("receipt.lanes", "must be an array"))
        lanes = []
    expected_lanes = (
        "WD-2gyw", "WD-bxhc", "WD-cpow", "WD-m0r5", "WD-r81u",
        "WD-rous", "consent-closeout", "WD-dmf2",
    )
    lane_ids = [lane.get("lane") if isinstance(lane, dict) else None for lane in lanes]
    if tuple(lane_ids) != expected_lanes:
        diagnostics.append(Diagnostic(
            "receipt.lanes", f"lane order and membership must be {expected_lanes}"
        ))
    for index, lane in enumerate(lanes):
        field = f"receipt.lanes[{index}]"
        if not isinstance(lane, dict) or set(lane) != {
            "lane", "command", "result", "exit_code", "warnings",
            "diagnostics", "bundle_identity_sha256",
        }:
            diagnostics.append(Diagnostic(
                field, "receipt lane has an unexpected shape"
            ))
            continue
        lane_id = lane.get("lane")
        bundle = root / "datasets/runs/maestro-parity" / str(lane_id)
        expected_command = [
            "python3", "scripts/verify_maestro_parity.py",
            f"datasets/runs/maestro-parity/{lane_id}",
        ]
        if lane.get("command") != expected_command:
            diagnostics.append(Diagnostic(
                field + ".command", f"must be {expected_command}"
            ))
        try:
            actual_identity = _bundle_identity_sha256(bundle)
        except (OSError, ValueError) as exc:
            diagnostics.append(Diagnostic(
                field + ".bundle_identity_sha256", str(exc)
            ))
        else:
            if lane.get("bundle_identity_sha256") != actual_identity:
                diagnostics.append(Diagnostic(
                    field + ".bundle_identity_sha256",
                    f"recorded {lane.get('bundle_identity_sha256')} but bundle "
                    f"bytes hash {actual_identity}",
                ))
        report = verify_bundle(bundle)
        expected_result = "pass" if report.passed else "fail"
        expected_exit = 0 if report.passed else 1
        if lane.get("result") != expected_result or lane.get("exit_code") != expected_exit:
            diagnostics.append(Diagnostic(
                field + ".result",
                f"must be result={expected_result} exit_code={expected_exit}",
            ))
        actual_warnings = [
            {
                "code": warning.code,
                "path": warning.path,
                "line": warning.line,
                "sha256": warning.sha256,
            }
            for warning in report.warnings
        ]
        if lane.get("warnings") != actual_warnings:
            diagnostics.append(Diagnostic(
                field + ".warnings", "must exactly match checker warnings"
            ))
        actual_diagnostics = [
            {"field": item.field, "message": item.message}
            for item in report.diagnostics
        ]
        if lane.get("diagnostics") != actual_diagnostics:
            diagnostics.append(Diagnostic(
                field + ".diagnostics", "must exactly match checker diagnostics"
            ))
    return VerificationReport(receipt_path, not diagnostics, tuple(diagnostics))


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
        path = _safe_bundle_file(root, relative, field, diagnostics)
        if path is None:
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        normalized = _normalized_sha256(entry.get("sha256"))
        if normalized is None or normalized != actual:
            diagnostics.append(Diagnostic(
                field, f"recorded {entry.get('sha256')} but artifact bytes hash {actual}"))
    return paths


def _validate_media(
    value: Any, output_paths: list[str], diagnostics: list[Diagnostic]) -> None:
    entries = value if isinstance(value, list) else []
    paths = [entry.get("path") for entry in entries if isinstance(entry, dict)
             and isinstance(entry.get("path"), str) and entry["path"].strip()]
    if len(paths) != len(set(paths)) or sorted(paths) != sorted(output_paths):
        diagnostics.append(Diagnostic(
            "media_metadata.path",
            "must describe every output artifact and no other path"))
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict) or not isinstance(entry.get("audio"), dict):
            continue
        prefix = f"media_metadata[{index}].audio"
        audio = entry["audio"]
        if entry.get("kind") == "video":
            for key in ("duration_s", "fps"):
                if not _valid(entry.get(key), "positive_number"):
                    diagnostics.append(Diagnostic(
                        f"media_metadata[{index}].{key}", _message("positive_number")))
        if entry.get("kind") == "image" and audio.get("present") is not False:
            diagnostics.append(Diagnostic(
                f"{prefix}.present", "must be false for an image"))
        if audio.get("present") is not False:
            for key, kind in (("codec", "text"), ("sample_rate_hz", "positive_integer"),
                              ("channels", "positive_integer")):
                if not _valid(audio.get(key), kind):
                    diagnostics.append(Diagnostic(f"{prefix}.{key}", _message(kind)))
        for key in ("duration_s", "fps"):
            if entry.get("kind") == "image" and entry.get(key) is not None:
                diagnostics.append(Diagnostic(
                    f"media_metadata[{index}].{key}", "must be null for an image"))


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
            pattern = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$"
            return bool(text and re.match(pattern, value)
                        and datetime.fromisoformat(value.replace("Z", "+00:00")) is not None)
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
        print(
            f"PASS {SCHEMA} {arguments.bundle} "
            f"owned_warnings={len(report.warnings)}"
        )
        for warning in report.warnings:
            print(
                f"WARNING {warning.code} {warning.path}:{warning.line} "
                f"sha256={warning.sha256} {warning.message}"
            )
        return 0
    for diagnostic in report.diagnostics:
        print(f"FAIL {diagnostic.field}: {diagnostic.message}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
