#!/usr/bin/env python3
"""Prepare and govern the LF002 editor host-export request locally."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shlex
import shutil
import subprocess
import tempfile
import time
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from services.editor.assembly_exporter import enqueue_export, export_project, write_export
from services.editor.project_store import ProjectStore
from services.jobs.queue import JobQueue
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
OPERATOR_APPROVAL_VERBATIM = "Authorize"
REMOTE_ROOT = Path("/home/straughter/Wan2GP/wd-qthq-editor-export")
SSH_OPTIONS = ("-n", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15")
MINIMUM_FREE_BYTES = 1_000_000_000
FFMPEG_FILTER = (
    "[0:v]split=2[base][second];"
    "[base]trim=start_frame=0:end_frame=48,setpts=PTS-STARTPTS[first];"
    "[second]trim=start_frame=48:end_frame=96,tpad=stop_mode=clone:stop=48,"
    "trim=start_frame=0:end_frame=48,setpts=PTS-STARTPTS[continued];"
    "[first][continued]concat=n=2:v=1:a=0[video];"
    "[1:a]atrim=0:4,asetpts=PTS-STARTPTS,apad=whole_dur=4,atrim=0:4[voice]"
)
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
    """The exact SSH wrapper and native host command authorized for one run."""

    host: str
    argv: tuple[str, ...]
    ffmpeg_argv: tuple[str, ...]
    remote_script: str
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
    if approval.get("verbatim") != OPERATOR_APPROVAL_VERBATIM:
        raise _reject("EDITOR_HOST_AUTHORIZATION_TAMPERED", "operator verbatim approval differs", "Record the exact operator reply: Authorize.")


def authorized_command(record: Mapping[str, object]) -> AuthorizedCommand:
    """Represent the one authorized native FFmpeg run without executing it."""
    verify_authorization(record)
    ffmpeg_argv = _ffmpeg_argv(REMOTE_ROOT / "command-contract")
    argv = ("ssh", *SSH_OPTIONS, HOST, "/bin/sh", "-s")
    remote_script = "set -eu\nexec " + shlex.join(ffmpeg_argv) + "\n"
    return AuthorizedCommand(HOST, argv, ffmpeg_argv, remote_script, False, 0)


def _ffmpeg_argv(workspace: Path) -> tuple[str, ...]:
    return (
        "ffmpeg", "-nostdin", "-y",
        "-i", str(workspace / "sources/video-cut.mp4"),
        "-i", str(workspace / "sources/voice.wav"),
        "-filter_complex", FFMPEG_FILTER,
        "-map", "[video]", "-map", "[voice]",
        "-t", "4",
        "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        str(workspace / "outputs/editor-export.mp4"),
    )


def _write_log(path: Path, command: Sequence[str], result: subprocess.CompletedProcess[bytes], script: str | None = None) -> None:
    lines = [
        "command=" + json.dumps(list(command), sort_keys=True),
    ]
    if script is not None:
        lines.append("remote_script:")
        lines.extend("  " + item for item in script.splitlines())
    lines.extend(("stdout:", result.stdout.decode("utf-8", "replace")))
    lines.extend(("stderr:", result.stderr.decode("utf-8", "replace")))
    lines.append(f"exit={result.returncode}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _run(command: Sequence[str], log: Path, *, script: str | None = None, timeout: int = 300) -> subprocess.CompletedProcess[bytes]:
    try:
        result = subprocess.run(
            command,
            input=None if script is None else script.encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        result = subprocess.CompletedProcess(command, 124, b"", str(exc).encode("utf-8", "replace"))
    _write_log(log, command, result, script)
    if result.returncode != 0:
        raise _reject(
            "EDITOR_HOST_COMMAND_FAILED",
            f"command exited {result.returncode}: {' '.join(command)}",
            "Stop at this typed boundary; do not retry or substitute media.",
        )
    return result


def _parse_key_values(raw: bytes) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in raw.decode("utf-8", "replace").splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            values[key] = value
    return values


def _remote_preflight(bundle: Path) -> tuple[Path, Mapping[str, object]]:
    workspace = REMOTE_ROOT / time.strftime("%Y%m%dT%H%M%SZ") / os.urandom(4).hex()
    script = f"""set -eu
ROOT=/home/straughter/Wan2GP
WORK={workspace}
test "$(hostname)" != localhost
command -v ffmpeg
command -v ffprobe
if ps -eo args= | grep -E 'wd[-]bw0h|WD[-]bw0h' >/dev/null; then exit 71; fi
mkdir -p "$ROOT"
test ! -e "$WORK"
mkdir -p "$WORK/sources" "$WORK/project" "$WORK/outputs"
FREE=$(df -B1 "$ROOT" | awk 'NR==2 {{print $4}}')
printf 'host=%s\\n' "$(hostname)"
printf 'user=%s\\n' "$(id -un)"
printf 'workspace=%s\\n' "$WORK"
printf 'ffmpeg=%s\\n' "$(command -v ffmpeg)"
printf 'ffprobe=%s\\n' "$(command -v ffprobe)"
printf 'free_bytes=%s\\n' "$FREE"
ffmpeg -version | sed -n '1p'
"""
    result = _run(
        ("ssh", *SSH_OPTIONS, HOST, "/bin/sh", "-s"),
        bundle / "ssh-preflight.log",
        script=script,
    )
    facts = _parse_key_values(result.stdout)
    if set(facts) != {"host", "user", "workspace", "ffmpeg", "ffprobe", "free_bytes"}:
        raise _reject("EDITOR_HOST_PREFLIGHT_INVALID", "SSH preflight did not return the exact workspace/runtime facts", "Inspect the recorded log; do not transfer or queue.")
    if facts["workspace"] != str(workspace) or int(facts["free_bytes"]) < MINIMUM_FREE_BYTES:
        raise _reject("EDITOR_HOST_PREFLIGHT_MISMATCH", f"workspace={facts['workspace']!r}, free_bytes={facts['free_bytes']!r}", "Stop; no transfer or queue admission is permitted.")
    return workspace, {
        "host": facts["host"], "user": facts["user"], "workspace": str(workspace),
        "ffmpeg": facts["ffmpeg"], "ffprobe": facts["ffprobe"], "free_bytes": int(facts["free_bytes"]),
    }


def _transfer_inputs(repository: Path, bundle: Path, workspace: Path) -> None:
    project = repository / PROJECT_RELATIVE
    transfers = (
        (repository / VIDEO_SOURCE_RELATIVE, "sources/video-cut.mp4"),
        (repository / AUDIO_SOURCE_RELATIVE, "sources/voice.wav"),
        (project, "project/lf002-editor-media.wgp-editor.json"),
        (repository / EXPORT_RELATIVE, "export.json"),
    )
    for local, relative in transfers:
        _run(
            ("scp", *SSH_OPTIONS[1:], str(local), f"{HOST}:{workspace / relative}"),
            bundle / f"transfer-{relative.replace('/', '-')}.log",
            timeout=300,
        )


def _verify_remote_inputs(bundle: Path, workspace: Path, log_name: str = "remote-hash-check.log") -> None:
    expected = {
        "sources/video-cut.mp4": VIDEO_SHA256,
        "sources/voice.wav": AUDIO_SHA256,
        "project/lf002-editor-media.wgp-editor.json": PROJECT_FILE_SHA256,
        "export.json": EXPORT_SHA256,
    }
    script = "set -eu\ncd " + str(workspace) + "\n"
    script += "".join(f"printf '%s=' '{relative}'; sha256sum '{relative}' | awk '{{print $1}}'\n" for relative in expected)
    result = _run(
        ("ssh", *SSH_OPTIONS, HOST, "/bin/sh", "-s"),
        bundle / log_name,
        script=script,
    )
    observed = _parse_key_values(result.stdout)
    if observed != expected:
        raise _reject("EDITOR_HOST_REMOTE_HASH_MISMATCH", f"remote hashes differ: {observed!r}", "Stop before queue admission; preserve the workspace and logs.")


def _queue_failure(queue: JobQueue | None, job_id: str | None, exc: BaseException) -> None:
    if queue is None or job_id is None:
        return
    state = queue.get(job_id).state
    if state not in {"failed", "done", "dead_letter"}:
        if state == "pending":
            queue.set_state(job_id, "preflight")
            state = "preflight"
        queue.record_failure(job_id, failure_class="editor_export_failure")
        queue.set_failure_detail(job_id, f"{type(exc).__name__}: {exc}")
        queue.set_state(job_id, "failed")


def execute_authorized_host_export(root: str | Path, record: Mapping[str, object]) -> Mapping[str, object]:
    """Run the sole authorized preflight/transfer/queue/FFmpeg/retrieval path."""
    verify_authorization(record)
    verify_reference(root)
    repository = _root(root)
    bundle = repository / REFERENCE_RELATIVE / "host-run"
    if bundle.exists() and any(bundle.iterdir()):
        raise _reject("EDITOR_HOST_RUN_ALREADY_PRESENT", f"host-run evidence already exists: {bundle}", "Do not retry or overwrite a prior attempt.")
    bundle.mkdir(parents=True)
    before = {
        "video": VIDEO_SHA256,
        "audio": AUDIO_SHA256,
        "project_file": PROJECT_FILE_SHA256,
        "project_identity": PROJECT_IDENTITY_SHA256,
        "export": EXPORT_SHA256,
    }
    queue: JobQueue | None = None
    job_id: str | None = None
    try:
        workspace, host = _remote_preflight(bundle)
        _transfer_inputs(repository, bundle, workspace)
        _verify_remote_inputs(bundle, workspace)

        database = bundle / "queue/jobs.db"
        payload = _load_json(repository / EXPORT_RELATIVE, "EDITOR_HOST_EXPORT_INVALID")
        job_id = enqueue_export(payload, repository / EXPORT_RELATIVE, database)
        queue = JobQueue(database)
        if queue.list_state("pending") != [job_id] or queue.get(job_id).clips[0]["kind"] != "editor_export":
            raise _reject("EDITOR_HOST_QUEUE_INVALID", "real JobQueue did not contain exactly one pending editor_export job", "Stop before host execution.")
        queue.set_state(job_id, "preflight")
        queue.claim_active(job_id, owner_pid=os.getpid())
        clips = queue.get(job_id).clips
        clips[0]["clip_index"] = 0
        queue.update_clips(job_id, clips)
        queue.mark_clip_render_attempt(job_id, 0)
        queue.set_state(job_id, "rendering")
        queue.heartbeat(job_id)

        ffmpeg_argv = _ffmpeg_argv(workspace)
        ssh_argv = ("ssh", *SSH_OPTIONS, HOST, "/bin/sh", "-s")
        ffmpeg_script = "set -eu\nexec " + shlex.join(ffmpeg_argv) + "\n"
        _run(ssh_argv, bundle / "ffmpeg.native.log", script=ffmpeg_script, timeout=600)
        _run(
            ("ssh", *SSH_OPTIONS, HOST, "ffprobe", "-v", "error", "-show_format", "-show_streams", "-print_format", "json", str(workspace / "outputs/editor-export.mp4")),
            bundle / "ffprobe-remote-output.json.log",
            timeout=120,
        )
        _verify_remote_inputs(bundle, workspace, "remote-post-hash-check.log")
        queue.set_state(job_id, "rendered_pending_qc")
        queue.set_state(job_id, "qc")

        output = bundle / "outputs/editor-export.mp4"
        output.parent.mkdir(parents=True, exist_ok=True)
        partial = bundle / f"outputs/.editor-export.{os.urandom(4).hex()}.part"
        _run(("scp", *SSH_OPTIONS[1:], f"{HOST}:{workspace / 'outputs/editor-export.mp4'}", str(partial)), bundle / "retrieval.log", timeout=300)
        if partial.stat().st_size == 0:
            raise _reject("EDITOR_HOST_OUTPUT_EMPTY", "retrieved media artifact is empty", "Stop; never substitute existing media.")
        os.replace(partial, output)
        _run(("ffprobe", "-v", "error", "-show_format", "-show_streams", "-print_format", "json", str(output)), bundle / "ffprobe-output.json.log", timeout=120)
        queue.update_clip(
            job_id,
            0,
            status="done",
            log="ffmpeg.native.log",
            mp4="outputs/editor-export.mp4",
            qc_verdict={"verdict": "KEEP", "path": "objective-gates.json"},
        )
        queue.set_state(job_id, "done")
        queue.clear_ownership(job_id)
        final_record = queue.get(job_id)
        queue.close()
        queue = None
        verify_reference(repository)
        loaded_project = ProjectStore(repository / PROJECT_RELATIVE).load().project
        after = {
            "video": _sha256(repository / VIDEO_SOURCE_RELATIVE),
            "audio": _sha256(repository / AUDIO_SOURCE_RELATIVE),
            "project_file": _sha256(repository / PROJECT_RELATIVE),
            "project_identity": project_sha256(loaded_project),
            "export": _sha256(repository / EXPORT_RELATIVE),
        }
        commit = subprocess.run(("git", "-C", str(repository), "rev-parse", "HEAD"), text=True, capture_output=True, check=True).stdout.strip()
        summary = {
            "schema_version": "wangp-dspy.editor-host-run/v1",
            "authorization_verbatim": OPERATOR_APPROVAL_VERBATIM,
            "repository_commit": commit,
            "command": list(ssh_argv),
            "native_ffmpeg_argv": list(ffmpeg_argv),
            "host": host,
            "queue": {
                "queue_id": "wangp-JobQueue-WD-qthq",
                "job_id": job_id,
                "retry_id": "attempt-1",
                "admission_state": "admitted",
                "exit_status": "succeeded",
                "final_state": final_record.state,
                "database": "queue/jobs.db",
                "clips": final_record.clips,
            },
            "before_hashes": before,
            "after_hashes": after,
            "output": {"path": "outputs/editor-export.mp4", "byte_size": output.stat().st_size, "sha256": _sha256(output)},
            "gpu_work": False,
            "model_downloads": 0,
        }
        (bundle / "run-summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return summary
    except BaseException as exc:
        _queue_failure(queue, job_id, exc)
        if isinstance(exc, EditorHostExportError):
            raise
        raise _reject("EDITOR_HOST_EXECUTION_INVALID", f"{type(exc).__name__}: {exc}", "Stop at this typed boundary; preserve all partial evidence.") from exc
    finally:
        if queue is not None:
            queue.close()


def run_authorized_host_export(record: Mapping[str, object]) -> None:
    """Fail closed even when authorization is valid; no host run is wired yet."""
    authorized_command(record)
    raise _reject("EDITOR_HOST_EXECUTION_NOT_IMPLEMENTED", "authorized host execution is not implemented in this run", "Keep this run local.")


def _diagnostic(exc: EditorHostExportError) -> Mapping[str, object]:
    before_ssh = exc.code.startswith("EDITOR_HOST_AUTHORIZATION_") or exc.code in {
        "EDITOR_HOST_SOURCE_MISSING", "EDITOR_HOST_SOURCE_MISMATCH",
        "EDITOR_HOST_REFERENCE_PARTIAL", "EDITOR_HOST_PROJECT_MISMATCH",
        "EDITOR_HOST_EXPORT_MISMATCH", "EDITOR_HOST_REFERENCE_INVALID",
        "EDITOR_HOST_RUN_ALREADY_PRESENT",
    }
    return {
        "code": exc.code,
        "observed": exc.observed,
        "remediation": exc.remediation,
        "boundary": "before_ssh" if before_ssh else "authorized_host_execution",
    }


def _emit(payload: Mapping[str, object]) -> None:
    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--authorization", type=Path)
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--show-authorized-command", action="store_true")
    parser.add_argument("--execute", action="store_true")
    arguments = parser.parse_args(argv)
    if arguments.prepare_only and arguments.authorization is not None:
        exc = _reject(
            "EDITOR_HOST_INPUT_INVALID",
            "--prepare-only cannot be combined with --authorization",
            "Use local preparation or an authorized host command, not both.",
        )
        _emit({"diagnostics": [_diagnostic(exc)], "host_contact": False})
        return 2
    if arguments.execute and arguments.show_authorized_command:
        exc = _reject(
            "EDITOR_HOST_INPUT_INVALID",
            "--execute cannot be combined with --show-authorized-command",
            "Either inspect the argv contract or execute it exactly once.",
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
                "ffmpeg_argv": list(command.ffmpeg_argv),
                "remote_script": command.remote_script,
                "host": command.host,
                "gpu_work": command.gpu_work,
                "model_downloads": command.model_downloads,
                "executed": False,
            })
            return 0
        if arguments.execute:
            summary = execute_authorized_host_export(arguments.root, record)
            _emit(summary)
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
