"""Compile immutable finishing requests into non-executable command graphs."""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from predict.finishing import (
    CODEC_ARGUMENTS,
    FinishingBackend,
    FinishingCapabilityError,
    FinishingRequest,
    SpatialScale,
    backend_settings,
    canonical_sha256,
    file_sha256,
    request_digest,
)


PLAN_SCHEMA_VERSION = "wangp-dspy.finishing-plan/v1"


@dataclass(frozen=True)
class CompiledFinishingPlan:
    payload: dict[str, Any]

    def mapping(self) -> dict[str, Any]:
        return self.payload


def _failure(
    code: str,
    observed: str,
    remediation: str,
    **metadata: Any,
) -> FinishingCapabilityError:
    return FinishingCapabilityError(
        code,
        observed,
        remediation,
        next_command="wgp finish plan --request <request> --dry-run --json",
        metadata=metadata,
    )


def load_request(path: str | Path) -> FinishingRequest:
    source = Path(path).expanduser().resolve()
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
        return FinishingRequest.model_validate(payload)
    except FileNotFoundError as exc:
        raise FinishingCapabilityError(
            "FINISH_REQUEST_MISSING",
            f"finishing request does not exist: {source}",
            "Pass an existing typed finishing request JSON file.",
        ) from exc
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise FinishingCapabilityError(
            "FINISH_REQUEST_INVALID",
            f"cannot validate finishing request {source}: {exc}",
            "Fix the typed request fields, then rerun the deterministic no-GPU plan.",
            metadata={"path": str(source)},
        ) from exc


def _validate_source(request: FinishingRequest) -> str:
    source = Path(request.source.path).expanduser().resolve()
    if not source.is_file():
        raise _failure(
            "FINISH_SOURCE_MISSING",
            f"finishing source is not a readable file: {source}",
            "Restore the immutable source at its recorded path; Wangp will not regenerate it.",
            path=str(source),
        )
    actual = file_sha256(source)
    if actual != request.source.sha256:
        raise _failure(
            "FINISH_SOURCE_HASH_MISMATCH",
            f"source hash mismatch: expected {request.source.sha256}, got {actual}",
            "Restore the exact source bytes or record a new immutable request.",
            expected=request.source.sha256,
            actual=actual,
        )
    return actual


def _selected_face_track(request: FinishingRequest) -> dict[str, Any] | None:
    if request.face_refinement is None:
        return None
    tracks = request.face_refinement.tracks
    selected = request.face_refinement.selected_track
    if selected is None:
        if len(tracks) != 1:
            raise _failure(
                "FINISH_FACE_TRACK_AMBIGUOUS",
                f"face refinement has {len(tracks)} tracks and no selected_track",
                "Select exactly one recorded track; this planning surface never guesses identity.",
                track_ids=[track.track_id for track in tracks],
            )
        selected = tracks[0].track_id
    matches = [track for track in tracks if track.track_id == selected]
    if len(matches) != 1:
        raise _failure(
            "FINISH_FACE_TRACK_MISMATCH",
            f"selected face track {selected!r} does not identify exactly one declaration",
            "Use one declared track_id verbatim.",
            selected_track=selected,
            track_ids=[track.track_id for track in tracks],
        )
    track = matches[0]
    if track.end_s > request.source.stream.duration_s + 1e-9:
        raise _failure(
            "FINISH_FACE_TRACK_OUT_OF_BOUNDS",
            f"face track {track.track_id} ends after the declared source duration",
            "Re-track the face against this exact immutable source.",
            track_id=track.track_id,
            source_duration_s=request.source.stream.duration_s,
            track_end_s=track.end_s,
        )
    return track.model_dump(mode="json")


def _validate_output(request: FinishingRequest) -> Path:
    output = Path(request.output.path).expanduser().resolve()
    source = Path(request.source.path).expanduser().resolve()
    if output == source:
        raise _failure(
            "FINISH_OUTPUT_INVALID",
            "planned output path equals the immutable source path",
            "Choose a new staged output path; finishing never rewrites source bytes.",
        )
    if output.exists():
        raise _failure(
            "FINISH_OUTPUT_EXISTS",
            f"planned output already exists: {output}",
            "Choose a new output path; overwrite is refused.",
            path=str(output),
        )
    return output


def _planned_stage(
    stage_id: str,
    backend: FinishingBackend,
    command: tuple[str, ...],
    source: Path,
    destination: Path,
    *,
    purpose: str,
    input_path: Path | None = None,
) -> dict[str, Any]:
    return {
        "stage_id": stage_id,
        "purpose": purpose,
        "backend": backend.value,
        "command": list(command),
        "input": str(input_path or source),
        "output": str(destination),
        "execution_status": "planned",
        "executed": False,
        "measurement": "unverified",
    }


def _command_graph(
    request: FinishingRequest,
    source: Path,
    output: Path,
    face_track: Mapping[str, Any] | None,
) -> list[dict[str, Any]]:
    digest = request_digest(request)
    stage_root = output.parent / f".{output.stem}.finishing-{digest[:12]}"
    probe_output = stage_root / "0001-source-ffprobe.json"
    stages: list[dict[str, Any]] = [
        _planned_stage(
            "probe",
            FinishingBackend.ffmpeg,
            (
                "ffprobe", "-v", "error", "-print_format", "json", "-show_format",
                "-show_streams", str(source),
            ),
            source,
            probe_output,
            purpose="record before/after metadata when separately authorized",
        )
    ]
    current = source
    width = request.source.stream.width
    height = request.source.stream.height
    stage_index = 2

    if request.interpolation is not None:
        destination = stage_root / f"{stage_index:04d}-interpolation.mp4"
        fps = request.interpolation.target_fps
        if request.backend is FinishingBackend.ffmpeg:
            command = (
                "ffmpeg", "-nostdin", "-i", str(current), "-an", "-vf",
                f"minterpolate=fps={fps:g}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1",
                "-c:v", "ffv1", destination.name,
            )
        else:
            command = (
                "rife-ncnn-vulkan", "--input", str(current), "--output", str(destination),
                "--model", f"rife-{request.interpolation.factor.value}",
                "--fps", f"{fps:g}",
            )
        stages.append(_planned_stage(
            "interpolation", request.backend, command, source, destination,
            purpose=f"declare {request.interpolation.factor.value} temporal interpolation",
            input_path=current,
        ))
        current = destination
        stage_index += 1

    if request.spatial_upscale is not None:
        destination = stage_root / f"{stage_index:04d}-spatial-upscale.mp4"
        scale = request.spatial_upscale.scale.multiplier
        if request.backend is FinishingBackend.ffmpeg:
            command = (
                "ffmpeg", "-nostdin", "-i", str(current), "-an", "-vf",
                f"scale=iw*{scale}:ih*{scale}:flags=lanczos",
                "-c:v", "ffv1", destination.name,
            )
        else:
            command = (
                "realesrgan-ncnn-vulkan", "-i", str(current), "-o", str(destination),
                "-s", str(SpatialScale(request.spatial_upscale.scale.value).multiplier),
                "-n", "realesrgan-x4plus",
            )
        stages.append(_planned_stage(
            "spatial_upscale", request.backend, command, source, destination,
            purpose=f"declare {request.spatial_upscale.scale.value} spatial upsampling",
            input_path=current,
        ))
        current = destination
        width *= scale
        height *= scale
        stage_index += 1

    if request.film_grain is not None:
        destination = stage_root / f"{stage_index:04d}-film-grain.mp4"
        command = (
            "ffmpeg", "-nostdin", "-i", str(current), "-an", "-vf",
            f"noise=alls={request.film_grain.strength:g}:allf=t+u",
            "-c:v", "ffv1", destination.name,
        )
        stages.append(_planned_stage(
            "film_grain", request.backend, command, source, destination,
            purpose="declare deterministic temporal film grain",
            input_path=current,
        ))
        current = destination
        stage_index += 1

    if face_track is not None:
        destination = stage_root / f"{stage_index:04d}-tracked-face-refinement.mp4"
        x = max(0, round(float(face_track["x"]) * width))
        y = max(0, round(float(face_track["y"]) * height))
        region_width = max(2, round(float(face_track["width"]) * width))
        region_height = max(2, round(float(face_track["height"]) * height))
        enable = f"between(t,{float(face_track['start_s']):.6f},{float(face_track['end_s']):.6f})"
        graph = (
            f"[0:v]crop={region_width}:{region_height}:{x}:{y},"
            f"unsharp=5:5:{request.face_refinement.strength if request.face_refinement else 0:g}"
            f"[face];[0:v][face]overlay={x}:{y}:enable='{enable}'"
        )
        command = (
            "ffmpeg", "-nostdin", "-i", str(current), "-an", "-filter_complex", graph,
            "-c:v", "ffv1", destination.name,
        )
        stages.append(_planned_stage(
            "face_refinement", request.backend, command, source, destination,
            purpose="declare one consented tracked-face refinement region",
            input_path=current,
        ))
        current = destination
        stage_index += 1

    codec_arguments = CODEC_ARGUMENTS[request.output.codec]
    stages.append(_planned_stage(
        "codec", request.backend,
        (
            "ffmpeg", "-nostdin", "-i", str(source), "-i", str(current),
            "-map", "1:v:0", "-map", "0:a?", *codec_arguments,
            "-movflags", "+faststart", str(output),
        ),
        source,
        output,
        purpose="declare the target codec and immutable stream contract",
        input_path=current,
    ))
    return stages


def _build_record(request: FinishingRequest) -> dict[str, Any]:
    actual_source_hash = _validate_source(request)
    face_track = _selected_face_track(request)
    output = _validate_output(request)
    if request.neural_path is not None:
        raise _failure(
            "FINISH_NEURAL_PATH_UNAVAILABLE",
            "the optional neural path has no authorized host in this no-GPU request",
            "Keep the declaration unavailable here and request a separately authorized host run.",
            backend_profile=request.neural_path.backend_profile,
            minimum_vram_gb=request.neural_path.minimum_vram_gb,
        )
    graph = _command_graph(request, Path(request.source.path).expanduser().resolve(), output, face_track)
    settings = backend_settings(request)
    recipe = request.model_dump(mode="json")
    seed_value = (
        f"{request.recipe_seed}:{actual_source_hash}:{request.backend.value}:"
        f"{request.output.container.value}:{request.output.codec.value}"
    ).encode("utf-8")
    return {
        "record_index": 1,
        "status": "planned",
        "kind": "finishing_plan_record",
        "backend": request.backend.value,
        "operations": [stage["purpose"] for stage in graph],
        "source": {
            "path": str(Path(request.source.path).expanduser().resolve()),
            "sha256": actual_source_hash,
            "stream_index": request.source.stream.index,
        },
        "selected_face_track": face_track,
        "output": {
            "path": str(output),
            "container": request.output.container.value,
            "codec": request.output.codec.value,
        },
        "command_graph": graph,
        "command_graph_sha256": canonical_sha256({"stages": graph}),
        "backend_settings": settings,
        "backend_settings_sha256": canonical_sha256(settings),
        "recipe": recipe,
        "recipe_sha256": canonical_sha256(recipe),
        "recipe_seed": request.recipe_seed,
        "seed_reconstruction_sha256": hashlib.sha256(seed_value).hexdigest(),
        "measurement_status": "unverified",
        "media_generated": False,
        "gpu_work": False,
        "queue_submitted": False,
        "host_contact": False,
        "plan_only": True,
        "executable": False,
    }


def compile_finishing_request(request: FinishingRequest) -> CompiledFinishingPlan:
    """Validate immutable inputs before any durable record is created."""

    record = _build_record(request)
    return CompiledFinishingPlan({
        "schema_version": PLAN_SCHEMA_VERSION,
        "request_sha256": request_digest(request),
        "capability_status": "planned",
        "backend": request.backend.value,
        "record_count": 1,
        "records": [record],
        "summary": {
            "gpu_work": False,
            "media_generated": False,
            "queue_submitted": False,
            "host_contact": False,
        },
    })


def enqueue_plan(plan: Mapping[str, Any], database: str | Path) -> list[str]:
    """Persist immutable records outside the executable governed queue."""

    destination = Path(database).expanduser().resolve()
    if destination.exists():
        raise _failure(
            "FINISH_QUEUE_EXISTS",
            f"queue database already exists: {destination}",
            "Select a new database path for this no-GPU finishing plan.",
            path=str(destination),
        )
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = destination.parent / f".{destination.name}.{os.urandom(8).hex()}.tmp"
    record_ids: list[str] = []
    connection: sqlite3.Connection | None = None
    try:
        connection = sqlite3.connect(staging)
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute(
            "CREATE TABLE finishing_plan_records ("
            "record_id TEXT PRIMARY KEY, plan_ref TEXT NOT NULL, record_index INTEGER NOT NULL, "
            "record TEXT NOT NULL, created_at REAL NOT NULL)"
        )
        connection.execute(
            "CREATE TRIGGER finishing_plan_records_immutable_update "
            "BEFORE UPDATE ON finishing_plan_records "
            "BEGIN SELECT RAISE(ABORT, 'finishing plan records are immutable'); END"
        )
        connection.execute(
            "CREATE TRIGGER finishing_plan_records_immutable_delete "
            "BEFORE DELETE ON finishing_plan_records "
            "BEGIN SELECT RAISE(ABORT, 'finishing plan records are immutable'); END"
        )
        for record in plan["records"]:
            record_id = f"finishing-plan-{int(time.time() * 1000)}-{os.urandom(4).hex()}"
            connection.execute(
                "INSERT INTO finishing_plan_records VALUES (?,?,?,?,?)",
                (
                    record_id,
                    str(plan["request_sha256"]),
                    int(record["record_index"]),
                    json.dumps(record, sort_keys=True),
                    time.time(),
                ),
            )
            record_ids.append(record_id)
        connection.commit()
        connection.close()
        connection = None
        os.replace(staging, destination)
        return record_ids
    except Exception:
        if connection is not None:
            connection.close()
        for suffix in ("", "-wal", "-shm"):
            Path(str(staging) + suffix).unlink(missing_ok=True)
        destination.unlink(missing_ok=True)
        raise


def _reconstruct_record(record: Mapping[str, Any]) -> dict[str, Any]:
    request = FinishingRequest.model_validate(record["recipe"])
    rebuilt = _build_record(request)
    return {
        "command_graph_sha256": rebuilt["command_graph_sha256"],
        "backend_settings_sha256": rebuilt["backend_settings_sha256"],
        "seed_reconstruction_sha256": rebuilt["seed_reconstruction_sha256"],
    }


def reconstruct_plan_database(database: str | Path) -> list[dict[str, Any]]:
    """Rebuild command hashes from the frozen recipe and exact source bytes."""

    path = Path(database).expanduser().resolve()
    if not path.is_file():
        raise FinishingCapabilityError(
            "FINISH_RECONSTRUCTION_DATABASE_MISSING",
            f"plan database does not exist: {path}",
            "Pass a SQLite database emitted by wgp finish plan.",
            next_command="wgp finish plan --db <plan.db> --reconstruct --json",
        )
    connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        tables = {
            row[0] for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        if "finishing_plan_records" not in tables:
            raise FinishingCapabilityError(
                "FINISH_RECONSTRUCTION_RECORDS_MISSING",
                f"database {path} has no finishing_plan_records table",
                "Use a database emitted by wgp finish plan.",
                next_command="wgp finish plan --db <plan.db> --reconstruct --json",
            )
        rows = connection.execute(
            "SELECT record_id, record FROM finishing_plan_records "
            "ORDER BY record_index, created_at, record_id"
        ).fetchall()
    finally:
        connection.close()
    if not rows:
        raise FinishingCapabilityError(
            "FINISH_RECONSTRUCTION_RECORDS_MISSING",
            f"database {path} contains zero finishing plan records",
            "Plan a nonempty finishing request before reconstruction.",
            next_command="wgp finish plan --request <request> --db <plan.db> --json",
        )
    results: list[dict[str, Any]] = []
    for record_id, raw in rows:
        try:
            record = json.loads(raw)
            if record.get("kind") != "finishing_plan_record":
                raise ValueError(f"unexpected kind {record.get('kind')!r}")
            reconstructed = _reconstruct_record(record)
        except Exception as exc:
            raise FinishingCapabilityError(
                "FINISH_RECONSTRUCTION_RECORD_INVALID",
                f"plan record {record_id} cannot be reconstructed: {exc}",
                "Restore the unedited wgp finish record or regenerate the no-GPU plan.",
                metadata={"record_id": record_id},
            ) from exc
        keys = (
            "command_graph_sha256",
            "backend_settings_sha256",
            "seed_reconstruction_sha256",
        )
        match = all(record[key] == reconstructed[key] for key in keys)
        results.append({
            "record_id": record_id,
            "backend": record["backend"],
            "recipe_seed": record["recipe_seed"],
            **{f"recorded_{key}": record[key] for key in keys},
            **{f"reconstructed_{key}": reconstructed[key] for key in keys},
            "match": match,
            "hidden_mutation": not match,
        })
    return results


__all__ = [
    "CompiledFinishingPlan",
    "PLAN_SCHEMA_VERSION",
    "compile_finishing_request",
    "enqueue_plan",
    "load_request",
    "reconstruct_plan_database",
]
