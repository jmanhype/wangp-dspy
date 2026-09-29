#!/usr/bin/env python3
"""Prepare and govern the LF002 editor host-export request locally."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import tempfile
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from services.editor.assembly_exporter import export_project, write_export
from services.editor.project_store import ProjectStore
from wangp.editor_project import (
    PROJECT_SCHEMA,
    Clip,
    EditorProject,
    Track,
    TrackKind,
    project_sha256,
)


AUTHORIZATION_SCHEMA = "wangp-dspy.editor-host-authorization/v1"
REFERENCE_RELATIVE = Path("datasets/runs/maestro-parity/editor-host-export")
PROJECT_RELATIVE = REFERENCE_RELATIVE / "project/lf002-editor-media.wgp-editor.json"
EXPORT_RELATIVE = REFERENCE_RELATIVE / "export.json"
VIDEO_SOURCE_RELATIVE = Path("datasets/runs/provenance/lf002-vibevoice-film-20260917/cut1.mp4")
AUDIO_SOURCE_RELATIVE = Path("datasets/runs/provenance/lf002-vibevoice-audition-20260916/audio/orin.wav")
VIDEO_SHA256 = "b53e5d37457f61db8c1bfa31d11d8d873139bf0aabddf97e0efa245de4d702a3"
AUDIO_SHA256 = "f3d66cac4458d0d33870ff6dc97df75eff95d57b154180dd303be4f955c91857"
PROJECT_FILE_SHA256 = "e3ac1c1b973fc2e398b083d4e22eee98ed973cf0b8f09ca338c1d9848d35341e"
PROJECT_IDENTITY_SHA256 = "66dcc7acbca38fbeece2bbe478621f61bf9ac5dd166219b335f5c9a5242bed27"
EXPORT_SHA256 = "ef2786b17d71c45a4931d4de88e03b129e040930bd63ad22185ad65df2fa9f12"
DIRECTOR_REQUEST_SHA256 = "765eda5c737982c9fb9f2f72c8ad0a10a8cc205ca518a7aa25e8ff992dd82d46"
CONTINUITY_DIGEST = "2d13c6c05ee59f9d63807bf36de1c1eb600fd5e00e3679bfb4fcaf78b55887c2"
TEMPLATE_PATH = Path(__file__).resolve().parents[1] / REFERENCE_RELATIVE / "operator-authorization.template.json"
TEMPLATE = json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))
HOST = str(TEMPLATE["host"])
REQUIRED_VERBATIM = str(TEMPLATE["authorization"]["required_verbatim"])
EXPECTED_SOURCES: Mapping[str, Mapping[str, object]] = {
    "video-cut": {
        "role": "video", "repository_path": VIDEO_SOURCE_RELATIVE.as_posix(),
        "workspace_path": "sources/video-cut.mp4", "sha256": VIDEO_SHA256, "byte_size": 1_421_376,
    },
    "voice": {
        "role": "audio", "repository_path": AUDIO_SOURCE_RELATIVE.as_posix(),
        "workspace_path": "sources/voice.wav", "sha256": AUDIO_SHA256, "byte_size": 102_444,
    },
}
EXPECTED_PROJECT: Mapping[str, object] = {
    "path": "project/lf002-editor-media.wgp-editor.json", "file_sha256": PROJECT_FILE_SHA256,
    "identity_sha256": PROJECT_IDENTITY_SHA256,
}
EXPECTED_EXPORT: Mapping[str, object] = {
    "path": "export.json", "sha256": EXPORT_SHA256,
}
EXPECTED_JOBS: Sequence[Mapping[str, object]] = (
    {"kind": "editor_export", "count": 1},
)
EXPECTED_EXECUTION: Mapping[str, object] = {
    "gpu_work": False, "model_downloads": 0,
}


class EditorHostExportError(ValueError):
    """Typed fail-closed editor host-export rejection."""

    def __init__(self, code: str, observed: str, remediation: str) -> None:
        super().__init__(observed)
        self.code = code
        self.observed = observed
        self.remediation = remediation
        self.ssh_contacted = False


@dataclass(frozen=True)
class AuthorizedCommand:
    """An argv-only representation; the current runner never executes it."""

    host: str
    argv: tuple[str, ...]
    gpu_work: bool
    model_downloads: int


def _reject(code: str, observed: str, remediation: str) -> EditorHostExportError:
    return EditorHostExportError(code, observed, remediation)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _root(root: str | Path) -> Path:
    return Path(root).expanduser().resolve()


def _verify_source(path: Path, expected: Mapping[str, object]) -> None:
    if not path.is_file():
        raise _reject(
            "EDITOR_HOST_SOURCE_MISSING",
            f"declared source is absent: {path}",
            "Restore the exact committed source before preparing host export.",
        )
    expected_size = int(expected["byte_size"])
    if path.stat().st_size != expected_size or _sha256(path) != expected["sha256"]:
        raise _reject(
            "EDITOR_HOST_SOURCE_MISMATCH",
            f"source hash mismatch for {path}",
            "Restore the exact committed source bytes; no substitute is accepted.",
        )


def verify_sources(root: str | Path) -> tuple[Path, Path]:
    """Verify both immutable repository inputs before any authorization check."""
    repository = _root(root)
    video = repository / VIDEO_SOURCE_RELATIVE
    audio = repository / AUDIO_SOURCE_RELATIVE
    _verify_source(video, EXPECTED_SOURCES["video-cut"])
    _verify_source(audio, EXPECTED_SOURCES["voice"])
    return video, audio


def _build_project(store: ProjectStore, repository: Path) -> EditorProject:
    video = store.import_source(repository / VIDEO_SOURCE_RELATIVE, TrackKind.video, "video-cut")
    audio = store.import_source(repository / AUDIO_SOURCE_RELATIVE, TrackKind.audio, "voice")
    return EditorProject(
        schema_version=PROJECT_SCHEMA,
        name="LF002 authorized editor media export",
        reviewer="operator",
        revision=0,
        sources=(video, audio),
        tracks=(
            Track(track_id="video", kind=TrackKind.video, name="picture", order=0, clips=(
                Clip(clip_id="video-1", kind=TrackKind.video, source_id=video.asset_id, label="opening observatory", timeline_start_s=0.0, timeline_duration_s=2.0, source_in_s=0.0, source_out_s=2.0),
                Clip(clip_id="video-2", kind=TrackKind.video, source_id=video.asset_id, label="continuation observatory", timeline_start_s=2.0, timeline_duration_s=2.0, source_in_s=2.0, source_out_s=4.0),
            )),
            Track(track_id="audio", kind=TrackKind.audio, name="voice", order=1, clips=(
                Clip(clip_id="audio-1", kind=TrackKind.audio, source_id=audio.asset_id, label="voice take", timeline_start_s=0.0, timeline_duration_s=4.0, source_in_s=0.0, source_out_s=4.0),
            )),
        ),
        transitions=(),
        review_marks=(),
    )


def _load_json(path: Path, code: str) -> Mapping[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise _reject(code, f"cannot read JSON {path}: {exc}", "Supply valid local JSON input.") from exc
    if not isinstance(value, dict):
        raise _reject(code, f"JSON root is not an object: {path}", "Supply the documented JSON object.")
    return value


def verify_reference(root: str | Path) -> Path:
    """Verify the canonical project/export through the real editor APIs."""
    verify_sources(root)
    repository = _root(root)
    project_path = repository / PROJECT_RELATIVE
    export_path = repository / EXPORT_RELATIVE
    required = (
        project_path,
        export_path,
        project_path.parent / EXPECTED_SOURCES["video-cut"]["workspace_path"],
        project_path.parent / EXPECTED_SOURCES["voice"]["workspace_path"],
    )
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise _reject(
            "EDITOR_HOST_REFERENCE_PARTIAL",
            f"reference inputs are absent: {', '.join(missing)}",
            "Run the local prepare command in a complete repository checkout.",
        )
    if _sha256(project_path) != PROJECT_FILE_SHA256:
        raise _reject("EDITOR_HOST_PROJECT_MISMATCH", f"project file hash mismatch: {project_path}", "Restore the canonical immutable project.")
    if _sha256(export_path) != EXPORT_SHA256:
        raise _reject("EDITOR_HOST_EXPORT_MISMATCH", f"export file hash mismatch: {export_path}", "Restore the canonical immutable export.")
    for asset_id in EXPECTED_SOURCES:
        _verify_source(project_path.parent / EXPECTED_SOURCES[asset_id]["workspace_path"], EXPECTED_SOURCES[asset_id])
    store = ProjectStore(project_path)
    try:
        project = store.load().project
        store.verify_sources(project)
        reproduced = export_project(store, project)
    except Exception as exc:
        raise _reject(
            "EDITOR_HOST_REFERENCE_INVALID",
            f"canonical reference failed real editor verification: {exc}",
            "Restore the exact project/workspace bytes; do not edit them manually.",
        ) from exc
    identity = project_sha256(project)
    if identity != PROJECT_IDENTITY_SHA256:
        raise _reject("EDITOR_HOST_PROJECT_MISMATCH", f"project identity mismatch: got {identity}", "Restore the exact canonical project.")
    recorded = _load_json(export_path, "EDITOR_HOST_EXPORT_INVALID")
    if recorded != reproduced:
        raise _reject(
            "EDITOR_HOST_EXPORT_MISMATCH",
            "recorded export differs from real export_project output",
            "Restore the exact canonical export; upstream export drift is not accepted.",
        )
    if recorded["director"]["plan"]["request_sha256"] != DIRECTOR_REQUEST_SHA256 or recorded["assembly"]["continuity_digest"] != CONTINUITY_DIGEST:
        raise _reject("EDITOR_HOST_EXPORT_MISMATCH", "director request or continuity digest differs", "Restore the canonical export.")
    return project_path


def prepare_reference(root: str | Path) -> Path:
    """Construct the exact local reference without overwriting existing bytes."""
    repository = _root(root)
    verify_sources(repository)
    destination = repository / REFERENCE_RELATIVE
    existing = [path for path in (destination / "project", destination / "export.json") if path.exists()]
    if existing:
        return verify_reference(repository)
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".editor-host-export-", dir=destination.parent))
    try:
        project_path = staging / "project/lf002-editor-media.wgp-editor.json"
        store = ProjectStore(project_path)
        store = ProjectStore.create(project_path, _build_project(store, repository))
        payload = export_project(store)
        write_export(payload, staging / "export.json")
        candidate = staging
        if _sha256(candidate / "project/lf002-editor-media.wgp-editor.json") != PROJECT_FILE_SHA256:
            raise _reject("EDITOR_HOST_REFERENCE_INVALID", "generated project hash drifted", "Investigate upstream editor changes before export.")
        if _sha256(candidate / "export.json") != EXPORT_SHA256:
            raise _reject("EDITOR_HOST_REFERENCE_INVALID", "generated export hash drifted", "Investigate upstream editor changes before export.")
        os.replace(staging, destination)
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    return verify_reference(repository)


def _require_keys(value: Mapping[str, Any], expected: set[str], code: str, label: str) -> None:
    observed = set(value)
    if observed != expected:
        missing = sorted(expected - observed)
        extra = sorted(observed - expected)
        detail = f"{label} keys differ (missing={missing}, extra={extra})"
        raise _reject(code, detail, "Supply the complete authorization document without extra fields.")


def verify_authorization(record: Mapping[str, object]) -> None:
    """Reject absent, partial, ambiguous, tampered, or mismatched authorization."""
    if not record:
        raise _reject("EDITOR_HOST_AUTHORIZATION_ABSENT", "authorization record is absent or empty", "Record verbatim operator approval separately.")
    _require_keys(
        record,
        {"schema_version", "status", "host", "sources", "project", "export", "jobs", "execution", "authorization"},
        "EDITOR_HOST_AUTHORIZATION_TAMPERED",
        "authorization",
    )
    if record.get("schema_version") != AUTHORIZATION_SCHEMA:
        raise _reject("EDITOR_HOST_AUTHORIZATION_TAMPERED", f"authorization schema is {record.get('schema_version')!r}", f"Use {AUTHORIZATION_SCHEMA} exactly.")
    if record.get("status") == "not_authorized":
        raise _reject("EDITOR_HOST_AUTHORIZATION_NOT_AUTHORIZED", "authorization status is not_authorized", "Obtain explicit operator approval first.")
    if record.get("status") != "authorized":
        raise _reject("EDITOR_HOST_AUTHORIZATION_AMBIGUOUS", f"authorization status is {record.get('status')!r}", "Use authorized or not_authorized only.")
    if record.get("host") != HOST:
        raise _reject("EDITOR_HOST_AUTHORIZATION_HOST_MISMATCH", f"authorized host is {record.get('host')!r}", f"Only host {HOST!r} is authorized.")
    sources = record.get("sources")
    if not isinstance(sources, dict) or sources != EXPECTED_SOURCES:
        raise _reject("EDITOR_HOST_AUTHORIZATION_SOURCE_MISMATCH", "source manifest differs from the two declared sources", "Bind both exact paths, sizes, and hashes.")
    if record.get("project") != EXPECTED_PROJECT or record.get("export") != EXPECTED_EXPORT:
        raise _reject("EDITOR_HOST_AUTHORIZATION_PROJECT_MISMATCH", "project/export identity differs", "Bind the exact project and export hashes.")
    jobs = record.get("jobs")
    if not isinstance(jobs, list) or len(jobs) != 1 or jobs[0] != EXPECTED_JOBS[0]:
        raise _reject("EDITOR_HOST_AUTHORIZATION_JOB_MISMATCH", "jobs do not cover exactly one editor_export", "Record one editor_export job only.")
    if record.get("execution") != EXPECTED_EXECUTION:
        raise _reject("EDITOR_HOST_AUTHORIZATION_EXECUTION_MISMATCH", "execution constraints differ", "Require gpu_work=false and model_downloads=0.")
    authorization = record.get("authorization")
    if not isinstance(authorization, dict):
        raise _reject("EDITOR_HOST_AUTHORIZATION_PARTIAL", "authorization object is absent", "Fill authorization.record after approval.")
    _require_keys(authorization, {"required_verbatim", "record"}, "EDITOR_HOST_AUTHORIZATION_TAMPERED", "authorization")
    if authorization.get("required_verbatim") != REQUIRED_VERBATIM:
        raise _reject("EDITOR_HOST_AUTHORIZATION_TAMPERED", "required_verbatim differs", "Use the committed phrase without edits.")
    approval = authorization.get("record")
    if not isinstance(approval, dict):
        raise _reject("EDITOR_HOST_AUTHORIZATION_PARTIAL", "operator approval record is absent", "Record verbatim approval.")
    _require_keys(approval, {"operator", "recorded_utc", "verbatim"}, "EDITOR_HOST_AUTHORIZATION_TAMPERED", "approval")
    if not isinstance(approval.get("operator"), str) or not approval["operator"].strip():
        raise _reject("EDITOR_HOST_AUTHORIZATION_PARTIAL", "approval operator is absent", "Record the approving operator.")
    if not isinstance(approval.get("recorded_utc"), str) or not approval["recorded_utc"].strip():
        raise _reject("EDITOR_HOST_AUTHORIZATION_PARTIAL", "approval timestamp is absent", "Record approval time.")
    if approval.get("verbatim") != REQUIRED_VERBATIM:
        raise _reject("EDITOR_HOST_AUTHORIZATION_TAMPERED", "operator verbatim approval differs", "Record the required phrase exactly.")


def authorized_command(record: Mapping[str, object]) -> AuthorizedCommand:
    """Represent a future host run as argv only; never execute it here."""
    verify_authorization(record)
    argv = ("ssh", HOST, "--", "python3", "-m", "scripts.run_editor_host_export", "--prepare-only")
    return AuthorizedCommand(HOST, argv, False, 0)


def run_authorized_host_export(record: Mapping[str, object]) -> None:
    """Fail closed even when authorization is valid; no host run is wired yet."""
    authorized_command(record)
    raise _reject("EDITOR_HOST_EXECUTION_NOT_IMPLEMENTED", "authorized host execution is not implemented in this run", "Keep this run local.")


def _diagnostic(exc: EditorHostExportError) -> Mapping[str, object]:
    return {
        "code": exc.code,
        "observed": exc.observed,
        "remediation": exc.remediation,
        "boundary": "before_ssh",
    }


def _emit(payload: Mapping[str, object]) -> None:
    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--authorization", type=Path)
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--show-authorized-command", action="store_true")
    arguments = parser.parse_args(argv)
    if arguments.prepare_only and arguments.authorization is not None:
        exc = _reject(
            "EDITOR_HOST_INPUT_INVALID",
            "--prepare-only cannot be combined with --authorization",
            "Use local preparation or an authorized host command, not both.",
        )
        _emit({"diagnostics": [_diagnostic(exc)], "host_contact": False})
        return 2
    try:
        if arguments.prepare_only:
            project = prepare_reference(arguments.root)
            _emit({
                "schema_version": "wangp-dspy.editor-host-local-preparation/v1",
                "project": str(project),
                "project_sha256": PROJECT_IDENTITY_SHA256,
                "project_file_sha256": PROJECT_FILE_SHA256,
                "export_sha256": EXPORT_SHA256,
                "ssh_contact": False,
                "gpu_work": False,
                "model_downloads": 0,
                "queue_submitted": False,
            })
            return 0
        project = verify_reference(arguments.root)
        if arguments.authorization is None:
            raise _reject(
                "EDITOR_HOST_AUTHORIZATION_ABSENT",
                f"authorization path is absent for {project}",
                "Provide an explicitly authorized record; local preparation alone cannot contact a host.",
            )
        record = _load_json(arguments.authorization, "EDITOR_HOST_AUTHORIZATION_INVALID")
        command = authorized_command(record)
        if arguments.show_authorized_command:
            _emit({
                "schema_version": "wangp-dspy.editor-host-command-contract/v1",
                "argv": list(command.argv),
                "host": command.host,
                "gpu_work": command.gpu_work,
                "model_downloads": command.model_downloads,
                "executed": False,
            })
            return 0
        run_authorized_host_export(record)
        return 3
    except EditorHostExportError as exc:
        _emit({
            "diagnostics": [_diagnostic(exc)],
            "ssh_contact": False,
            "workspace_transfer": False,
            "queue_submitted": False,
            "model_downloads": 0,
        })
        return 3


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
