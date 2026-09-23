"""Compile typed audio-post requests into immutable non-executable records."""
from __future__ import annotations

import json
import os
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from host.audio_post_backends import backend_for
from predict.audio_post import (
    AudioPostCapabilityError,
    AudioPostOperation,
    AudioPostRequest,
    audio_post_next_command,
    backend_settings,
    canonical_sha256,
    file_sha256,
    request_digest,
)

PLAN_SCHEMA_VERSION = "wangp-dspy.audio-post-plan/v1"


@dataclass(frozen=True)
class CompiledAudioPostPlan:
    payload: dict[str, Any]

    def mapping(self) -> dict[str, Any]:
        return self.payload


def _readable_hash(
    path: str | Path, expected: str, *, kind: str,
    code_missing: str, code_mismatch: str, next_command: str,
) -> tuple[Path, str]:
    source = Path(path).expanduser().resolve()
    if not source.is_file():
        raise AudioPostCapabilityError(
            code_missing,
            f"{kind} is not readable: {source}",
            "Restore the exact authorized bytes; Wangp will not fetch source material.",
            next_command=next_command,
            metadata={"path": str(source)},
        )
    actual = file_sha256(source)
    if actual != expected:
        raise AudioPostCapabilityError(
            code_mismatch,
            f"{kind} hash mismatch: expected {expected}, got {actual}",
            "Restore the exact recorded bytes or correct the request provenance.",
            next_command=next_command,
            metadata={"path": str(source), "expected": expected, "actual": actual},
        )
    return source, actual


def _validate_duration(request: AudioPostRequest) -> None:
    adapter = backend_for(request.model.family)
    target_duration = request.duration_s or request.source.audio.duration_s
    if target_duration > adapter.max_duration_s:
        raise AudioPostCapabilityError(
            "AUDIO_POST_DURATION_MISMATCH",
            f"operation duration {target_duration:g}s exceeds {adapter.backend_id} ceiling {adapter.max_duration_s:g}s",
            "Request a duration within the declared backend ceiling.",
            next_command=audio_post_next_command(request.operation),
            metadata={"operation": request.operation.value, "limit": adapter.max_duration_s},
        )
    if request.operation is AudioPostOperation.sfx and request.duration_s is not None:
        if request.duration_s > request.source.audio.duration_s + 1e-6:
            raise AudioPostCapabilityError(
                "AUDIO_POST_DURATION_MISMATCH",
                f"sound-effect duration {request.duration_s:g}s exceeds source audio {request.source.audio.duration_s:g}s",
                "Keep the planned effect no longer than the existing audio stream.",
                next_command=audio_post_next_command(request.operation),
                metadata={"source_audio_duration_s": request.source.audio.duration_s},
            )


def _command_graph(request: AudioPostRequest, settings: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "program": "planned/audio-post",
        "operation": request.operation.value,
        "argv": [
            "planned/audio-post", "--operation", request.operation.value,
            "--source", request.source.path, "--source-sha256", request.source.sha256,
            "--output", request.output_path_planned,
            "--recipe-seed", str(request.recipe_seed),
        ],
        "graph": [
            {"stage": "verify_source", "source_sha256": request.source.sha256},
            {"stage": "hold_video_fixed", "copy_video_stream": True, "video_transformations": []},
            {"stage": request.operation.value, "backend_id": settings["backend"], "gpu_work": False},
            {"stage": "assemble_target", "output_path": request.output_path_planned, "output_created": False},
        ],
    }


def compile_audio_post_request(request: AudioPostRequest) -> CompiledAudioPostPlan:
    """Validate all local bytes before creating one immutable plan record."""

    output = Path(request.output_path_planned).expanduser().resolve()
    if output.exists():
        raise AudioPostCapabilityError(
            "AUDIO_POST_OUTPUT_EXISTS",
            f"planned output already exists: {output}",
            "Choose a new target path; planning must not claim or overwrite media.",
            next_command=audio_post_next_command(request.operation),
            metadata={"path": str(output)},
        )
    source_path, source_hash = _readable_hash(
        request.source.path,
        request.source.sha256,
        kind="source media",
        code_missing="AUDIO_POST_SOURCE_MISSING",
        code_mismatch="AUDIO_POST_SOURCE_HASH_MISMATCH",
        next_command=audio_post_next_command(request.operation),
    )
    voice = None
    if request.voice is not None:
        voice_path, voice_hash = _readable_hash(
            request.voice.path,
            request.voice.sha256,
            kind="target voice reference",
            code_missing="AUDIO_POST_VOICE_MISSING",
            code_mismatch="AUDIO_POST_VOICE_UNUSABLE",
            next_command=audio_post_next_command(request.operation),
        )
        voice = request.voice.model_dump(mode="json") | {
            "path": str(voice_path), "sha256": voice_hash,
        }
    _validate_duration(request)
    adapter = backend_for(request.model.family)
    settings = backend_settings(request)
    record = {
        "record_index": 1,
        "kind": "audio_post_plan_record",
        "status": "planned",
        "operation": request.operation.value,
        "backend": {
            "id": adapter.backend_id,
            "family": request.model.family.value,
            "preset": request.model.preset.value,
            "model_type": adapter.model_type,
            "sha256": request.model.sha256,
            "license": request.model.license,
            "source": request.model.source,
            "usage_constraint": request.model.usage_constraint,
            "vram_profile": request.model.vram_profile,
            "execution_status": "planned",
        },
        "source": {
            "path": str(source_path), "sha256": source_hash,
            "video": request.source.video.model_dump(mode="json"),
            "audio": request.source.audio.model_dump(mode="json"),
            "immutable": True,
        },
        "video_fixed": {
            "immutable": True,
            "source_video_sha256": source_hash,
            "transformations": [],
            "video_bytes_changed": False,
            "measurement_status": "not verified - requires authorized host run",
        },
        "voice": voice,
        "refinement": request.refinement.model_dump(mode="json") if request.refinement else None,
        "output": request.output.model_dump(mode="json") | {
            "path": str(output), "audio": None, "measurement_status": "not verified - requires authorized host run",
        },
        "command_planned": _command_graph(request, settings),
        "recipe": request.model_dump(mode="json"),
        "backend_settings": settings,
        "backend_settings_sha256": canonical_sha256(settings),
        "queue_submitted": False,
        "host_contact": False,
        "plan_only": True,
        "executable": False,
    }
    return CompiledAudioPostPlan({
        "schema_version": PLAN_SCHEMA_VERSION,
        "request_sha256": request_digest(request),
        "capability_status": "planned",
        "operation": request.operation.value,
        "model": request.model.model_dump(mode="json"),
        "record_count": 1,
        "records": [record],
        "summary": {
            "gpu_work": False, "audio_created": False, "video_changed": False,
            "queue_submitted": False, "host_contact": False,
        },
    })


def enqueue_audio_post_plan(plan: Mapping[str, Any], database: str | Path) -> list[str]:
    """Atomically persist plan records outside the executable jobs table."""

    destination = Path(database).expanduser().resolve()
    if destination.exists():
        raise AudioPostCapabilityError(
            "AUDIO_POST_QUEUE_EXISTS", f"queue database already exists: {destination}",
            "Select a new database path for this no-GPU plan.",
            next_command=audio_post_next_command(plan.get("operation")),
        )
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = destination.parent / f".{destination.name}.{os.urandom(8).hex()}.tmp"
    ids: list[str] = []
    connection: sqlite3.Connection | None = None
    try:
        connection = sqlite3.connect(staging)
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute(
            "CREATE TABLE audio_post_plan_records ("
            "record_id TEXT PRIMARY KEY, plan_ref TEXT NOT NULL, record_index INTEGER NOT NULL, "
            "record TEXT NOT NULL, created_at REAL NOT NULL)"
        )
        connection.execute(
            "CREATE TRIGGER audio_post_plan_records_immutable_update "
            "BEFORE UPDATE ON audio_post_plan_records "
            "BEGIN SELECT RAISE(ABORT, 'audio post plan records are immutable'); END"
        )
        connection.execute(
            "CREATE TRIGGER audio_post_plan_records_immutable_delete "
            "BEFORE DELETE ON audio_post_plan_records "
            "BEGIN SELECT RAISE(ABORT, 'audio post plan records are immutable'); END"
        )
        for record in plan["records"]:
            record_id = f"audio-post-plan-{int(time.time() * 1000)}-{os.urandom(4).hex()}"
            connection.execute(
                "INSERT INTO audio_post_plan_records VALUES (?,?,?,?,?)",
                (record_id, str(plan["request_sha256"]), int(record["record_index"]),
                 json.dumps(record, sort_keys=True), time.time()),
            )
            ids.append(record_id)
        connection.commit()
        connection.close()
        connection = None
        os.replace(staging, destination)
        return ids
    except Exception:
        if connection is not None:
            connection.close()
        for suffix in ("", "-wal", "-shm"):
            Path(str(staging) + suffix).unlink(missing_ok=True)
        destination.unlink(missing_ok=True)
        raise


def reconstruct_audio_post_settings(record: Mapping[str, Any]) -> dict[str, Any]:
    request = AudioPostRequest.model_validate(record["recipe"])
    if int(record.get("record_index", 0)) != 1:
        raise ValueError("audio-post records are singleton records with record_index=1")
    return backend_settings(request)


def reconstruct_audio_post_database(database: str | Path) -> list[dict[str, Any]]:
    path = Path(database).expanduser().resolve()
    if not path.is_file():
        raise AudioPostCapabilityError(
            "AUDIO_POST_RECONSTRUCTION_DATABASE_MISSING", f"plan database does not exist: {path}",
            "Pass a SQLite database emitted by wgp sfx.",
            next_command="wgp sfx plan --db <plan.db> --reconstruct --json",
        )
    connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if "audio_post_plan_records" not in tables:
            raise AudioPostCapabilityError(
                "AUDIO_POST_RECONSTRUCTION_RECORDS_MISSING", f"database {path} has no audio-post plan records",
                "Use a database emitted by wgp sfx planning.",
            )
        rows = connection.execute(
            "SELECT record_id, record FROM audio_post_plan_records ORDER BY record_index, created_at, record_id"
        ).fetchall()
    finally:
        connection.close()
    if not rows:
        raise AudioPostCapabilityError(
            "AUDIO_POST_RECONSTRUCTION_RECORDS_MISSING", f"database {path} contains zero audio-post plan records",
            "Compile a nonempty wgp sfx plan.",
        )
    results: list[dict[str, Any]] = []
    for record_id, raw in rows:
        try:
            record = json.loads(raw)
            if record.get("kind") != "audio_post_plan_record":
                raise ValueError(f"unexpected kind {record.get('kind')!r}")
            reconstructed = reconstruct_audio_post_settings(record)
        except Exception as exc:
            raise AudioPostCapabilityError(
                "AUDIO_POST_RECONSTRUCTION_RECORD_INVALID",
                f"plan record {record_id} cannot be reconstructed: {exc}",
                "Regenerate the no-GPU audio-post plan; do not edit immutable records.",
                metadata={"record_id": record_id},
            ) from exc
        recorded = record["backend_settings_sha256"]
        actual = canonical_sha256(reconstructed)
        results.append({
            "record_id": record_id,
            "operation": record["operation"],
            "recipe_seed": record["recipe"]["recipe_seed"],
            "recorded_settings_sha256": recorded,
            "reconstructed_settings_sha256": actual,
            "recorded_command_sha256": canonical_sha256(record["command_planned"]),
            "match": recorded == actual,
            "hidden_mutation": recorded != actual,
        })
    return results


__all__ = [
    "CompiledAudioPostPlan", "PLAN_SCHEMA_VERSION", "compile_audio_post_request",
    "enqueue_audio_post_plan", "reconstruct_audio_post_database",
]
