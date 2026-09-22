"""Compile typed video requests into immutable pending queue clips."""
from __future__ import annotations

import os
import json
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from predict.video_capabilities import (
    FPS,
    MAX_LONG_FORM_S,
    VideoCapabilityError,
    VideoCapabilityRequest,
    VideoOperation,
    backend_settings,
    canonical_sha256,
    file_sha256,
    parse_timecode,
    request_digest,
)
from services.jobs.queue import JobQueue


PLAN_SCHEMA_VERSION = "wangp-dspy.video-capability-plan/v1"
REFERENCE_OPERATIONS = frozenset(
    item.value for item in VideoOperation if item is not VideoOperation.create
)


@dataclass(frozen=True)
class CompiledVideoPlan:
    payload: dict[str, Any]

    def mapping(self) -> dict[str, Any]:
        return self.payload


def _validate_assets(request: VideoCapabilityRequest) -> list[dict[str, str]]:
    if request.operation.value in REFERENCE_OPERATIONS:
        for index, clip in enumerate(request.clips, start=1):
            if not clip.reference:
                raise VideoCapabilityError(
                    "VIDEO_REFERENCE_MISSING",
                    f"clip {index} has no reference for {request.operation.value}",
                    "Attach the exact readable reference asset, then rerun the plan.",
                    metadata={"clip_index": index},
                )
            reference = Path(clip.reference).expanduser()
            if not reference.is_file():
                raise VideoCapabilityError(
                    "VIDEO_REFERENCE_MISSING",
                    f"clip {index} reference is not a readable file: {reference}",
                    "Restore the referenced asset at the recorded path; Wangp will not regenerate it.",
                    metadata={"clip_index": index},
                )
    loras: list[dict[str, str]] = []
    for index, lora in enumerate(request.loras, start=1):
        path = Path(lora.path).expanduser()
        if not path.is_file():
            raise VideoCapabilityError(
                "VIDEO_LORA_UNUSABLE",
                f"LoRA {index} is not a readable file: {path}",
                "Restore the exact LoRA asset or remove it; selection cannot be a host convenience.",
                metadata={"lora_index": index},
            )
        actual = file_sha256(path)
        if actual != lora.sha256:
            raise VideoCapabilityError(
                "VIDEO_LORA_UNUSABLE",
                f"LoRA {index} hash mismatch: expected {lora.sha256}, got {actual}",
                "Restore the exact recorded LoRA bytes; Wangp will not download or repair it.",
                metadata={
                    "lora_index": index,
                    "expected": lora.sha256,
                    "actual": actual,
                },
            )
        loras.append({"path": str(path), "sha256": actual, "weight": str(lora.weight)})
    return loras


def _validate_long_form(request: VideoCapabilityRequest) -> tuple[float, list[float]]:
    durations = [clip.duration_s for clip in request.clips]
    overlap_s = request.overlap.frames / FPS
    accounted = sum(durations) - overlap_s * max(0, len(durations) - 1)
    control = request.long_form
    if control.mode.value == "one_window":
        if len(request.clips) != 1 or control.one_window is not True:
            raise VideoCapabilityError(
                "VIDEO_WINDOW_COUNT_INVALID",
                f"one_window requires exactly one clip, got {len(request.clips)}",
                "Use one prompt/window or select exact_timecode/window_count.",
            )
    elif control.mode.value == "exact_timecode":
        if control.exact_timecode is None:
            raise VideoCapabilityError(
                "VIDEO_TIMECODE_INVALID",
                "exact_timecode control is absent",
                "Supply both start and end timecodes.",
            )
        try:
            start = parse_timecode(control.exact_timecode.start)
            end = parse_timecode(control.exact_timecode.end)
        except VideoCapabilityError as exc:
            exc.metadata["mode"] = "exact_timecode"
            raise
        total = end - start
        if total <= 0:
            raise VideoCapabilityError(
                "VIDEO_TIMECODE_INVALID",
                f"end timecode must follow start timecode (start={start}s, end={end}s)",
                "Correct the HH:MM:SS:FF interval.",
            )
        if abs(total - accounted) > 1 / FPS:
            raise VideoCapabilityError(
                "VIDEO_TIMECODE_INVALID",
                f"timecode interval {total:.6f}s does not match clip/overlap accounting {accounted:.6f}s",
                "Adjust clip durations or the explicit overlap so the interval is exact.",
                metadata={"expected_s": total, "accounted_s": accounted},
            )
    elif control.window_count != len(request.clips):
        raise VideoCapabilityError(
            "VIDEO_WINDOW_COUNT_INVALID",
            f"window_count {control.window_count} does not match {len(request.clips)} clips",
            "Use exactly one prompt and window per requested clip.",
            metadata={"requested": control.window_count, "clips": len(request.clips)},
        )
    if accounted > MAX_LONG_FORM_S:
        raise VideoCapabilityError(
            "VIDEO_WINDOW_COUNT_INVALID",
            f"long-form accounting is {accounted}s, above the 3600s limit",
            "Split the request into separately governed batches.",
            metadata={"accounted_s": accounted},
        )
    return accounted, durations


def _windows(request: VideoCapabilityRequest) -> list[dict[str, float | int]]:
    cursor = 0.0
    overlap_s = request.overlap.frames / FPS
    windows: list[dict[str, float | int]] = []
    for index, clip in enumerate(request.clips, start=1):
        end = cursor + clip.duration_s
        windows.append({
            "index": index,
            "start_s": round(cursor, 6),
            "end_s": round(end, 6),
            "duration_s": clip.duration_s,
            "overlap_frames": request.overlap.frames if index < len(request.clips) else 0,
        })
        cursor = end - (overlap_s if index < len(request.clips) else 0)
    return windows


def compile_video_request(request: VideoCapabilityRequest) -> CompiledVideoPlan:
    """Validate all inputs before any durable record is created."""

    loras = _validate_assets(request)
    accounted, _ = _validate_long_form(request)
    windows = _windows(request)
    clips: list[dict[str, Any]] = []
    for source, window in zip(request.clips, windows, strict=True):
        settings = backend_settings(
            model=request.model,
            operation=request.operation,
            prompt=source.prompt,
            duration_s=source.duration_s,
            render=request.render,
            recipe_seed=request.recipe_seed,
        )
        recipe = {
            "schema_version": "wangp-dspy.video-recipe-input/v1",
            "family": request.model.family.value,
            "preset": request.model.preset.value,
            "operation": request.operation.value,
            "prompt": source.prompt,
            "duration_s": source.duration_s,
            "render": request.render.model_dump(mode="json"),
            "recipe_seed": request.recipe_seed,
        }
        reference = None
        if (
            source.reference is not None
            and request.operation is not VideoOperation.create
        ):
            reference_path = Path(source.reference).expanduser()
            reference = {
                "path": str(reference_path),
                "sha256": file_sha256(reference_path),
            }
        clips.append({
            "clip_index": window["index"],
            "status": "pending",
            "log": None,
            "mp4": None,
            "qc_verdict": None,
            "kind": "video_plan_record",
            "operation": request.operation.value,
            "prompt": source.prompt,
            "backend": {
                "id": request.model.family.value,
                "preset": request.model.preset.value,
                "model_type": settings["model_type"],
                "sha256": request.model.sha256,
                "license": request.model.license,
                "vram_profile": request.model.vram_profile,
                "execution_status": "planned",
            },
            "model_type": settings["model_type"],
            "model_sha256": request.model.sha256,
            "loras": loras,
            "reference": reference,
            "window": window,
            "overlap": request.overlap.model_dump(mode="json"),
            "recipe": recipe,
            "recipe_seed": request.recipe_seed,
            "backend_settings": settings,
            "backend_settings_sha256": canonical_sha256(settings),
            "queue_submitted": False,
            "host_contact": False,
            "plan_only": True,
            "executable": False,
        })
    digest = request_digest(request)
    return CompiledVideoPlan({
        "schema_version": PLAN_SCHEMA_VERSION,
        "request_sha256": digest,
        "capability_status": "planned",
        "operation": request.operation.value,
        "clip_count": len(clips),
        "accounted_duration_s": round(accounted, 6),
        "overlap_strategy": request.overlap.strategy.value,
        "long_form_mode": request.long_form.mode.value,
        "clips": clips,
        "summary": {
            "gpu_work": False,
            "queue_submitted": False,
            "host_contact": False,
        },
    })


def enqueue_plan(plan: Mapping[str, Any], database: str | Path) -> list[str]:
    """Atomically persist one non-executable plan record per clip.

    This is deliberately not the ``jobs`` table drained by the governed
    worker.  A plan-only artifact cannot become renderer admission work.
    """

    destination = Path(database).expanduser().resolve()
    if destination.exists():
        raise VideoCapabilityError(
            "VIDEO_QUEUE_EXISTS",
            f"queue database already exists: {destination}",
            "Select a new database path for this no-GPU plan.",
        )
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = destination.parent / f".{destination.name}.{os.urandom(8).hex()}.tmp"
    record_ids: list[str] = []
    connection: sqlite3.Connection | None = None
    try:
        connection = sqlite3.connect(staging)
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute(
            "CREATE TABLE video_plan_records ("
            " record_id TEXT PRIMARY KEY,"
            " plan_ref TEXT NOT NULL,"
            " clip_index INTEGER NOT NULL,"
            " record TEXT NOT NULL,"
            " created_at REAL NOT NULL)"
        )
        for clip in plan["clips"]:
            record_id = (
                f"plan-{int(time.time() * 1000)}-{os.urandom(4).hex()}"
            )
            connection.execute(
                "INSERT INTO video_plan_records "
                "(record_id, plan_ref, clip_index, record, created_at) "
                "VALUES (?,?,?,?,?)",
                (
                    record_id,
                    str(plan["request_sha256"]),
                    int(clip["clip_index"]),
                    json.dumps(clip, sort_keys=True),
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


def reconstruct_clip_settings(record: Mapping[str, Any]) -> dict[str, Any]:
    """Regenerate settings from the recipe seed, not the stored settings."""

    recipe = record["recipe"]
    from predict.video_capabilities import (
        RenderControls,
        VideoFamily,
        VideoModelRef,
        VideoOperation,
        VideoPreset,
    )

    model = VideoModelRef(
        family=VideoFamily(recipe["family"]),
        preset=VideoPreset(recipe["preset"]),
        sha256=record["model_sha256"],
        license=record["backend"]["license"],
        license_accepted=True,
        vram_profile=record["backend"]["vram_profile"],
    )
    return backend_settings(
        model=model,
        operation=VideoOperation(recipe["operation"]),
        prompt=recipe["prompt"],
        duration_s=float(recipe["duration_s"]),
        render=RenderControls.model_validate(recipe["render"]),
        recipe_seed=int(recipe["recipe_seed"]),
    )


def reconstruct_queue_records(queue: JobQueue) -> list[dict[str, Any]]:
    """Fail-closed legacy reconstruction for pending queue records."""

    state_counts = {
        state: len(queue.list_state(state))
        for state in (
            "pending", "preflight", "rendering", "rendered_pending_qc",
            "qc", "done", "failed", "dead_letter",
        )
    }
    pending = queue.list_state("pending")
    if not pending:
        raise VideoCapabilityError(
            "VIDEO_RECONSTRUCTION_RECORDS_MISSING",
            "queue contains no reconstructable pending records",
            "Reconstruct a nonempty wgp video plan; an empty set is not success.",
            metadata={"state_counts": state_counts},
        )
    results: list[dict[str, Any]] = []
    for job_id in pending:
        record = queue.get(job_id).clips[0]
        try:
            reconstructed = reconstruct_clip_settings(record)
        except Exception as exc:
            raise VideoCapabilityError(
                "VIDEO_RECONSTRUCTION_RECORD_INVALID",
                f"queue record {job_id} cannot be reconstructed: {exc}",
                "Restore the unedited wgp video record or regenerate the no-GPU plan.",
                metadata={"job_id": job_id},
            ) from exc
        original_hash = record["backend_settings_sha256"]
        reconstructed_hash = canonical_sha256(reconstructed)
        results.append({
            "job_id": job_id,
            "clip_index": record["clip_index"],
            "recipe_seed": record["recipe_seed"],
            "recorded_settings_sha256": original_hash,
            "reconstructed_settings_sha256": reconstructed_hash,
            "match": original_hash == reconstructed_hash,
            "hidden_mutation": original_hash != reconstructed_hash,
        })
    return results


def reconstruct_plan_database(database: str | Path) -> list[dict[str, Any]]:
    """Fail-closed reconstruction over a nonempty plan-only database."""

    path = Path(database).expanduser().resolve()
    if not path.is_file():
        raise VideoCapabilityError(
            "VIDEO_RECONSTRUCTION_DATABASE_MISSING",
            f"plan database does not exist: {path}",
            "Pass the SQLite database emitted by wgp video.",
            next_command="wgp video --db <plan.db> --reconstruct --json",
        )
    connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    rows: list[tuple[str, str]] | None = None
    try:
        tables = {
            row[0] for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        if "video_plan_records" in tables:
            rows = connection.execute(
                "SELECT record_id, record FROM video_plan_records "
                "ORDER BY clip_index, created_at, record_id"
            ).fetchall()
    finally:
        connection.close()
    if rows is None:
        if "jobs" in tables:
            queue = JobQueue(path)
            try:
                return reconstruct_queue_records(queue)
            finally:
                queue.close()
        raise VideoCapabilityError(
            "VIDEO_RECONSTRUCTION_RECORDS_MISSING",
            f"database {path} has no video plan records or jobs table",
            "Use a database emitted by wgp video.",
        )
    if not rows:
        raise VideoCapabilityError(
            "VIDEO_RECONSTRUCTION_RECORDS_MISSING",
            f"database {path} contains zero video plan records",
            "Reconstruct a nonempty wgp video plan; an empty set is not success.",
        )
    results: list[dict[str, Any]] = []
    for record_id, raw in rows:
        try:
            record = json.loads(raw)
            if record.get("kind") != "video_plan_record":
                raise ValueError(f"unexpected kind {record.get('kind')!r}")
            reconstructed = reconstruct_clip_settings(record)
        except Exception as exc:
            raise VideoCapabilityError(
                "VIDEO_RECONSTRUCTION_RECORD_INVALID",
                f"plan record {record_id} cannot be reconstructed: {exc}",
                "Restore the unedited wgp video record or regenerate the no-GPU plan.",
                metadata={"record_id": record_id},
            ) from exc
        original_hash = record["backend_settings_sha256"]
        reconstructed_hash = canonical_sha256(reconstructed)
        results.append({
            "record_id": record_id,
            "clip_index": record["clip_index"],
            "recipe_seed": record["recipe_seed"],
            "recorded_settings_sha256": original_hash,
            "reconstructed_settings_sha256": reconstructed_hash,
            "match": original_hash == reconstructed_hash,
            "hidden_mutation": original_hash != reconstructed_hash,
        })
    return results


__all__ = [
    "CompiledVideoPlan",
    "PLAN_SCHEMA_VERSION",
    "compile_video_request",
    "enqueue_plan",
    "reconstruct_clip_settings",
    "reconstruct_plan_database",
    "reconstruct_queue_records",
]
