"""Compile typed image requests into immutable, non-executable records."""
from __future__ import annotations

import json
import os
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from predict.image_capabilities import (
    MAX_REFERENCES,
    ImageCapabilityError,
    ImageCapabilityRequest,
    backend_settings,
    canonical_sha256,
    file_sha256,
    request_digest,
)


PLAN_SCHEMA_VERSION = "wangp-dspy.image-capability-plan/v1"


@dataclass(frozen=True)
class CompiledImagePlan:
    payload: dict[str, Any]

    def mapping(self) -> dict[str, Any]:
        return self.payload


def _asset(index: int, path: str, expected: str, *, mask: bool = False) -> dict[str, str]:
    source = Path(path).expanduser()
    prefix = "mask" if mask else "reference"
    if not source.is_file():
        code = "IMAGE_MASK_MISSING" if mask else "IMAGE_REFERENCE_MISSING"
        raise ImageCapabilityError(
            code,
            f"{prefix} {index} is not a readable file: {source}",
            "Restore the exact local asset; Wangp will not download or repair it.",
            metadata={"index": index, "path": str(source)},
        )
    actual = file_sha256(source)
    if actual != expected:
        code = "IMAGE_MASK_UNUSABLE" if mask else "IMAGE_REFERENCE_UNUSABLE"
        raise ImageCapabilityError(
            code,
            f"{prefix} {index} hash mismatch: expected {expected}, got {actual}",
            "Restore the exact recorded bytes or update provenance before planning.",
            metadata={"index": index, "expected": expected, "actual": actual},
        )
    return {"path": str(source), "sha256": actual}


def compile_image_request(request: ImageCapabilityRequest) -> CompiledImagePlan:
    """Validate every local input before creating a durable record."""

    references: list[dict[str, str]] = []
    for index, reference in enumerate(request.references, start=1):
        asset = _asset(index, reference.path, reference.sha256)
        references.append({
            **asset,
            "index": index,
            "role": reference.role.value,
            "license": reference.license,
        })
    mask = None
    if request.mask is not None:
        mask = _asset(1, request.mask.path, request.mask.sha256, mask=True)
    settings = backend_settings(request)
    recipe = request.model_dump(mode="json")
    record = {
        "image_index": 1,
        "status": "pending",
        "kind": "image_plan_record",
        "operation": request.operation.value,
        "prompt": request.prompt,
        "backend": {
            "id": settings["backend_id"],
            "family": request.model.family.value,
            "preset": request.model.preset.value,
            "model_type": settings["model_type"],
            "sha256": request.model.sha256,
            "license": request.model.license,
            "vram_profile": request.model.vram_profile,
            "execution_status": "planned",
        },
        "model_sha256": request.model.sha256,
        "reference_limit": MAX_REFERENCES,
        "reference_count": len(references),
        "references": references,
        "mask": mask,
        "edit_region": request.edit_region.model_dump(mode="json") if request.edit_region else None,
        "upscale": request.upscale.model_dump(mode="json") if request.upscale else None,
        "outpaint": request.outpaint.model_dump(mode="json") if request.outpaint else None,
        "output": request.output.model_dump(mode="json"),
        "alpha_mode": settings["alpha_mode"],
        "prompt_enhancement": request.prompt_enhancement.model_dump(mode="json"),
        "identity_gate": request.identity_gate.model_dump(mode="json") if request.identity_gate else None,
        "recipe": recipe,
        "recipe_sha256": canonical_sha256(recipe),
        "recipe_seed": request.recipe_seed,
        "backend_settings": settings,
        "backend_settings_sha256": canonical_sha256(settings),
        "output_image": None,
        "queue_submitted": False,
        "host_contact": False,
        "plan_only": True,
        "executable": False,
    }
    return CompiledImagePlan({
        "schema_version": PLAN_SCHEMA_VERSION,
        "request_sha256": request_digest(request),
        "capability_status": "planned",
        "operation": request.operation.value,
        "image_count": 1,
        "records": [record],
        "summary": {"gpu_work": False, "queue_submitted": False, "host_contact": False},
    })


def enqueue_plan(plan: Mapping[str, Any], database: str | Path) -> str:
    """Atomically persist one plan-only image record, never a ``jobs`` row."""

    destination = Path(database).expanduser().resolve()
    if destination.exists():
        raise ImageCapabilityError(
            "IMAGE_QUEUE_EXISTS",
            f"queue database already exists: {destination}",
            "Select a new database path for this no-GPU plan.",
        )
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = destination.parent / f".{destination.name}.{os.urandom(8).hex()}.tmp"
    record_id = f"image-plan-{int(time.time() * 1000)}-{os.urandom(4).hex()}"
    connection: sqlite3.Connection | None = None
    try:
        connection = sqlite3.connect(staging)
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute(
            "CREATE TABLE image_plan_records ("
            " record_id TEXT PRIMARY KEY,"
            " plan_ref TEXT NOT NULL,"
            " image_index INTEGER NOT NULL,"
            " record TEXT NOT NULL,"
            " created_at REAL NOT NULL)"
        )
        record = plan["records"][0]
        connection.execute(
            "INSERT INTO image_plan_records "
            "(record_id, plan_ref, image_index, record, created_at) VALUES (?,?,?,?,?)",
            (record_id, str(plan["request_sha256"]), 1, json.dumps(record, sort_keys=True), time.time()),
        )
        connection.commit()
        connection.close()
        connection = None
        os.replace(staging, destination)
        return record_id
    except Exception:
        if connection is not None:
            connection.close()
        for suffix in ("", "-wal", "-shm"):
            Path(str(staging) + suffix).unlink(missing_ok=True)
        destination.unlink(missing_ok=True)
        raise


def reconstruct_image_settings(record: Mapping[str, Any]) -> dict[str, Any]:
    """Regenerate settings from the frozen typed recipe, not stored settings."""

    request = ImageCapabilityRequest.model_validate(record["recipe"])
    return backend_settings(request)


def reconstruct_plan_database(database: str | Path) -> list[dict[str, Any]]:
    path = Path(database).expanduser().resolve()
    if not path.is_file():
        raise ImageCapabilityError(
            "IMAGE_RECONSTRUCTION_DATABASE_MISSING",
            f"plan database does not exist: {path}",
            "Pass the SQLite database emitted by wgp image.",
            next_command="wgp image plan --db <plan.db> --reconstruct --json",
        )
    connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if "image_plan_records" not in tables:
            raise ImageCapabilityError(
                "IMAGE_RECONSTRUCTION_RECORDS_MISSING",
                f"database {path} has no image_plan_records table",
                "Use a database emitted by wgp image.",
            )
        rows = connection.execute(
            "SELECT record_id, record FROM image_plan_records ORDER BY image_index, created_at, record_id"
        ).fetchall()
    finally:
        connection.close()
    if not rows:
        raise ImageCapabilityError(
            "IMAGE_RECONSTRUCTION_RECORDS_MISSING",
            f"database {path} contains zero image plan records",
            "Reconstruct a nonempty wgp image plan.",
        )
    results: list[dict[str, Any]] = []
    for record_id, raw in rows:
        try:
            record = json.loads(raw)
            if record.get("kind") != "image_plan_record":
                raise ValueError(f"unexpected kind {record.get('kind')!r}")
            reconstructed = reconstruct_image_settings(record)
        except Exception as exc:
            raise ImageCapabilityError(
                "IMAGE_RECONSTRUCTION_RECORD_INVALID",
                f"plan record {record_id} cannot be reconstructed: {exc}",
                "Restore the unedited wgp image record or regenerate the no-GPU plan.",
                metadata={"record_id": record_id},
            ) from exc
        original_hash = record["backend_settings_sha256"]
        reconstructed_hash = canonical_sha256(reconstructed)
        results.append({
            "record_id": record_id,
            "operation": record["operation"],
            "recipe_seed": record["recipe_seed"],
            "recorded_settings_sha256": original_hash,
            "reconstructed_settings_sha256": reconstructed_hash,
            "match": original_hash == reconstructed_hash,
            "hidden_mutation": original_hash != reconstructed_hash,
        })
    return results


__all__ = [
    "CompiledImagePlan",
    "PLAN_SCHEMA_VERSION",
    "compile_image_request",
    "enqueue_plan",
    "reconstruct_image_settings",
    "reconstruct_plan_database",
]
