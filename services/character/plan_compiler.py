"""Compile portable character requests into immutable continuity plans."""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from predict.character_packages import (
    CharacterContinuityRequest,
    CharacterPackageError,
    CharacterReference,
    ContinuityMode,
    canonical_sha256,
)
from services.character.package_service import inspect_character_package

PLAN_SCHEMA_VERSION = "wangp-dspy.character-continuity-plan/v1"


@dataclass(frozen=True)
class CompiledCharacterPlan:
    payload: dict[str, Any]

    def mapping(self) -> dict[str, Any]:
        return self.payload


def load_request(path: str | Path) -> CharacterContinuityRequest:
    source = Path(path).expanduser().resolve()
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
        return CharacterContinuityRequest.model_validate(payload)
    except FileNotFoundError as exc:
        raise CharacterPackageError(
            "CHARACTER_REQUEST_MISSING",
            f"continuity request does not exist: {source}",
            "Pass an existing typed image/video character request JSON file.",
        ) from exc
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise CharacterPackageError(
            "CHARACTER_REQUEST_INVALID",
            f"cannot validate continuity request {source}: {exc}",
            "Fix the typed request, then rerun the deterministic no-GPU plan.",
        ) from exc


def _mismatch(code: str, observed: str, remediation: str, **metadata: Any) -> CharacterPackageError:
    return CharacterPackageError(
        code,
        observed,
        remediation,
        next_command="wgp character plan --request <request> --dry-run --json",
        metadata=metadata,
    )


def _validated_binding(
    request: CharacterContinuityRequest,
) -> tuple[dict[str, Any], dict[str, Any]]:
    reference = request.character
    package = Path(reference.package_path).expanduser().resolve()
    inspected = inspect_character_package(package)
    manifest = inspected["manifest"]
    if inspected["package_sha256"] != reference.package_sha256:
        raise _mismatch(
            "CHARACTER_PACKAGE_MISMATCH",
            f"character package hash mismatch: expected {reference.package_sha256}, got {inspected['package_sha256']}",
            "Restore the exact portable package bytes or update the request reference.",
            expected=reference.package_sha256,
            actual=inspected["package_sha256"],
        )
    if (
        manifest["character_id"] != reference.character_id
        or manifest["speaker_label"] != reference.speaker_label
    ):
        raise _mismatch(
            "CHARACTER_IDENTITY_MISMATCH",
            "request identity does not match the portable package",
            "Use the package character_id and speaker_label verbatim.",
            requested_character_id=reference.character_id,
            package_character_id=manifest["character_id"],
        )
    appearance = next(
        (item for item in manifest["appearance"] if item["member"] == reference.appearance_member),
        None,
    )
    if appearance is None or appearance["sha256"] != reference.appearance_sha256:
        raise _mismatch(
            "CHARACTER_APPEARANCE_MISMATCH",
            "request appearance member/hash does not match the portable package",
            "Bind the exact package appearance member and SHA-256.",
            member=reference.appearance_member,
        )
    voice = manifest["voice"]
    if (
        voice["member"] != reference.voice_member
        or voice["sha256"] != reference.voice_sha256
        or voice["voice_binding_id"] != reference.voice_binding_id
    ):
        raise _mismatch(
            "CHARACTER_VOICE_BINDING_MISMATCH",
            "request voice member/hash/binding does not match the portable package",
            "Bind the exact saved .wgpvoice member, SHA-256, and binding ID.",
            voice_binding_id=reference.voice_binding_id,
        )
    if request.mode.value not in manifest["continuity"]["modes"]:
        raise _mismatch(
            "CHARACTER_MODE_UNSUPPORTED",
            f"portable character does not declare {request.mode.value} continuity",
            "Export a character whose continuity modes include this generation mode.",
            mode=request.mode.value,
        )
    binding = {
        "package_path": str(package),
        "package_sha256": inspected["package_sha256"],
        "identity_sha256": manifest["identity_sha256"],
        "character_id": manifest["character_id"],
        "speaker_label": manifest["speaker_label"],
        "appearance": appearance,
        "voice": voice,
        "continuity": manifest["continuity"],
    }
    return binding, inspected


def _seed_digest(recipe_seed: int, package_sha256: str, mode: ContinuityMode) -> str:
    value = f"{recipe_seed}:{package_sha256}:{mode.value}".encode("utf-8")
    return hashlib.sha256(value).hexdigest()


def compile_character_request(request: CharacterContinuityRequest) -> CompiledCharacterPlan:
    """Validate package identity and all binding hashes before durable state."""

    binding, inspected = _validated_binding(request)
    binding_sha256 = canonical_sha256(binding)
    seed_sha256 = _seed_digest(request.recipe_seed, binding["package_sha256"], request.mode)
    recipe = request.model_dump(mode="json")
    record = {
        "record_index": 1,
        "status": "planned",
        "kind": "character_plan_record",
        "mode": request.mode.value,
        "operation": request.operation,
        "prompt": request.prompt,
        "character": request.character.model_dump(mode="json"),
        "resolved_character": binding,
        "character_binding_sha256": binding_sha256,
        "package_sha256": binding["package_sha256"],
        "identity_sha256": binding["identity_sha256"],
        "appearance_member": binding["appearance"]["member"],
        "appearance_sha256": binding["appearance"]["sha256"],
        "voice_member": binding["voice"]["member"],
        "voice_sha256": binding["voice"]["sha256"],
        "voice_binding_id": binding["voice"]["voice_binding_id"],
        "continuity": binding["continuity"],
        "recipe": recipe,
        "recipe_sha256": canonical_sha256(recipe),
        "recipe_seed": request.recipe_seed,
        "seed_reconstruction_sha256": seed_sha256,
        "media_generated": False,
        "queue_submitted": False,
        "host_contact": False,
        "plan_only": True,
        "executable": False,
    }
    return CompiledCharacterPlan({
        "schema_version": PLAN_SCHEMA_VERSION,
        "request_sha256": canonical_sha256(recipe),
        "capability_status": "planned",
        "mode": request.mode.value,
        "operation": request.operation,
        "record_count": 1,
        "records": [record],
        "summary": {
            "gpu_work": False,
            "media_generated": False,
            "queue_submitted": False,
            "host_contact": False,
        },
        "package": {
            "path": inspected["package"],
            "sha256": inspected["package_sha256"],
            "identity_sha256": inspected["identity_sha256"],
        },
    })


def enqueue_plan(plan: Mapping[str, Any], database: str | Path) -> list[str]:
    """Persist immutable records outside the executable governed queue."""

    destination = Path(database).expanduser().resolve()
    if destination.exists():
        raise CharacterPackageError(
            "CHARACTER_QUEUE_EXISTS",
            f"queue database already exists: {destination}",
            "Select a new database path for this no-GPU continuity plan.",
        )
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = destination.parent / f".{destination.name}.{os.urandom(8).hex()}.tmp"
    ids: list[str] = []
    connection: sqlite3.Connection | None = None
    try:
        connection = sqlite3.connect(staging)
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute(
            "CREATE TABLE character_plan_records ("
            "record_id TEXT PRIMARY KEY, plan_ref TEXT NOT NULL, record_index INTEGER NOT NULL, "
            "record TEXT NOT NULL, created_at REAL NOT NULL)"
        )
        connection.execute(
            "CREATE TRIGGER character_plan_records_immutable_update "
            "BEFORE UPDATE ON character_plan_records "
            "BEGIN SELECT RAISE(ABORT, 'character plan records are immutable'); END"
        )
        connection.execute(
            "CREATE TRIGGER character_plan_records_immutable_delete "
            "BEFORE DELETE ON character_plan_records "
            "BEGIN SELECT RAISE(ABORT, 'character plan records are immutable'); END"
        )
        for record in plan["records"]:
            record_id = f"character-plan-{int(time.time() * 1000)}-{os.urandom(4).hex()}"
            connection.execute(
                "INSERT INTO character_plan_records VALUES (?,?,?,?,?)",
                (
                    record_id,
                    str(plan["request_sha256"]),
                    int(record["record_index"]),
                    json.dumps(record, sort_keys=True),
                    time.time(),
                ),
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


def _reconstruct_record(record: Mapping[str, Any]) -> dict[str, Any]:
    request = CharacterContinuityRequest.model_validate(record["recipe"])
    binding, _inspected = _validated_binding(request)
    return {
        "character_binding_sha256": canonical_sha256(binding),
        "seed_reconstruction_sha256": _seed_digest(
            request.recipe_seed, binding["package_sha256"], request.mode
        ),
    }


def reconstruct_plan_database(database: str | Path) -> list[dict[str, Any]]:
    path = Path(database).expanduser().resolve()
    if not path.is_file():
        raise CharacterPackageError(
            "CHARACTER_RECONSTRUCTION_DATABASE_MISSING",
            f"plan database does not exist: {path}",
            "Pass a SQLite database emitted by wgp character plan.",
            next_command="wgp character plan --db <plan.db> --reconstruct --json",
        )
    connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        tables = {
            row[0] for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        if "character_plan_records" not in tables:
            raise CharacterPackageError(
                "CHARACTER_RECONSTRUCTION_RECORDS_MISSING",
                f"database {path} has no character_plan_records table",
                "Use a database emitted by wgp character plan.",
                next_command="wgp character plan --db <plan.db> --reconstruct --json",
            )
        rows = connection.execute(
            "SELECT record_id, record FROM character_plan_records "
            "ORDER BY record_index, created_at, record_id"
        ).fetchall()
    finally:
        connection.close()
    if not rows:
        raise CharacterPackageError(
            "CHARACTER_RECONSTRUCTION_RECORDS_MISSING",
            f"database {path} contains zero character plan records",
            "Plan a nonempty portable character request before reconstruction.",
            next_command="wgp character plan --request <request> --db <plan.db> --json",
        )
    results: list[dict[str, Any]] = []
    for record_id, raw in rows:
        try:
            record = json.loads(raw)
            if record.get("kind") != "character_plan_record":
                raise ValueError(f"unexpected kind {record.get('kind')!r}")
            reconstructed = _reconstruct_record(record)
        except Exception as exc:
            raise CharacterPackageError(
                "CHARACTER_RECONSTRUCTION_RECORD_INVALID",
                f"plan record {record_id} cannot be reconstructed: {exc}",
                "Restore the unedited wgp character record or regenerate the no-GPU plan.",
                metadata={"record_id": record_id},
            ) from exc
        binding_match = (
            record["character_binding_sha256"] == reconstructed["character_binding_sha256"]
        )
        seed_match = (
            record["seed_reconstruction_sha256"] == reconstructed["seed_reconstruction_sha256"]
        )
        results.append({
            "record_id": record_id,
            "mode": record["mode"],
            "operation": record["operation"],
            "recipe_seed": record["recipe_seed"],
            "recorded_binding_sha256": record["character_binding_sha256"],
            "reconstructed_binding_sha256": reconstructed["character_binding_sha256"],
            "recorded_seed_sha256": record["seed_reconstruction_sha256"],
            "reconstructed_seed_sha256": reconstructed["seed_reconstruction_sha256"],
            "match": binding_match and seed_match,
            "hidden_mutation": not (binding_match and seed_match),
        })
    return results


__all__ = [
    "CompiledCharacterPlan",
    "PLAN_SCHEMA_VERSION",
    "compile_character_request",
    "enqueue_plan",
    "load_request",
    "reconstruct_plan_database",
]
