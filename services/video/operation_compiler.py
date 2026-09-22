"""Compile typed video requests into immutable pending queue clips."""
from __future__ import annotations

import os
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
        if source.reference is not None:
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
            "kind": "video_capability_plan",
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
    """Atomically create one durable job per clip without draining it."""

    destination = Path(database).expanduser().resolve()
    if destination.exists():
        raise VideoCapabilityError(
            "VIDEO_QUEUE_EXISTS",
            f"queue database already exists: {destination}",
            "Select a new database path for this no-GPU plan.",
        )
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = destination.parent / f".{destination.name}.{os.urandom(8).hex()}.tmp"
    queue: JobQueue | None = None
    job_ids: list[str] = []
    try:
        queue = JobQueue(staging)
        for clip in plan["clips"]:
            job_ids.append(
                queue.submit(plan_ref=plan["request_sha256"], clips=[clip])
            )
        queue.close()
        queue = None
        os.replace(staging, destination)
        return job_ids
    except Exception:
        if queue is not None:
            queue.close()
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
    results: list[dict[str, Any]] = []
    for job_id in queue.list_state("pending"):
        record = queue.get(job_id).clips[0]
        reconstructed = reconstruct_clip_settings(record)
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


__all__ = [
    "CompiledVideoPlan",
    "PLAN_SCHEMA_VERSION",
    "compile_video_request",
    "enqueue_plan",
    "reconstruct_clip_settings",
    "reconstruct_queue_records",
]
