"""Compile director composition requests into immutable no-GPU records."""
from __future__ import annotations

import json
import os
import sqlite3
import time
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from pydantic import ValidationError

from services.director.composition import (
    DirectorEnhancementRequest,
    DirectorError,
    DirectorMode,
    DirectorRequest,
    ENHANCEMENT_SCHEMA,
    REQUEST_SCHEMA,
    canonical_sha256,
    file_sha256,
)
from services.director.continuity import continuity_declarations
from services.director.pacing import plan_windows
from services.director.review_policy import review_policy

PLAN_SCHEMA_VERSION = "wangp-dspy.director-plan/v1"
ENHANCED_PLAN_SCHEMA_VERSION = "wangp-dspy.director-enhanced-plan/v1"
PLAN_NEXT_COMMAND = "wgp director plan --request <request> --db <plan.db> --json"
RECONSTRUCT_NEXT_COMMAND = "wgp director review --db <plan.db> --json"
ENHANCE_NEXT_COMMAND = (
    "wgp director enhance --request <request> --output-db <plans.db> --json"
)
SUPPORTED_ENHANCEMENT_INTENTS = frozenset({"replace_prompt"})
SUPPORTED_ENHANCEMENT_FIELDS = frozenset({"prompt"})
PLANNING_SURFACES: tuple[dict[str, str], ...] = (
    {"mode": "prompt", "surface": "wangp.content.build_content_request"},
    {"mode": "audio", "surface": "services.director.orchestrator.DirectorOrchestrator"},
    {"mode": "music_video", "surface": "services.chain.plan.ChainPlan"},
    {"mode": "screenplay", "surface": "services.chain.keyframes.build_fl2va_prompt"},
)


@dataclass(frozen=True)
class CompiledDirectorPlan:
    """A deterministic plan plus the records needed for later reconstruction."""

    payload: dict[str, Any]

    def mapping(self) -> dict[str, Any]:
        return self.payload


def _error(
    code: str,
    observed: str,
    remediation: str,
    *,
    next_command: str = PLAN_NEXT_COMMAND,
    **metadata: Any,
) -> DirectorError:
    return DirectorError(
        code, observed, remediation, next_command=next_command, metadata=metadata
    )


def _request_payload(request: DirectorRequest) -> dict[str, Any]:
    return request.model_dump(mode="json")


def request_digest(request: DirectorRequest) -> str:
    return canonical_sha256(_request_payload(request))


def _classify_source_shape(document: Mapping[str, Any]) -> None:
    mode = document.get("mode")
    fields = {
        "prompt": document.get("prompt"),
        "audio": document.get("audio"),
        "screenplay": document.get("screenplay"),
    }
    expected_by_mode = {
        "prompt": "prompt",
        "audio": "audio",
        "music_video": "audio",
        "screenplay": "screenplay",
    }
    if mode not in expected_by_mode:
        return
    expected = expected_by_mode[mode]
    supplied = [name for name, value in fields.items() if value is not None]
    if fields[expected] is None:
        code = {
            "prompt": "DIRECTOR_PROMPT_MISSING",
            "audio": "DIRECTOR_AUDIO_MISSING",
            "screenplay": "DIRECTOR_SCREENPLAY_MISSING",
        }[expected]
        raise _error(
            code,
            f"mode {mode} is missing its {expected} source field",
            f"Supply the immutable {expected} source for mode {mode}.",
            **{"mode": mode, "supplied_sources": supplied},
        )
    if supplied != [expected]:
        raise _error(
            "DIRECTOR_MODE_CONFLICT",
            f"mode {mode} requires only {expected}, but request supplies {supplied}",
            "Remove the conflicting source fields or select the matching mode.",
            **{
                "mode": mode,
                "supplied_sources": supplied,
                "expected_source": expected,
            },
        )


def _classify_screenplay(document: Mapping[str, Any]) -> None:
    if document.get("mode") != "screenplay":
        return
    screenplay = document.get("screenplay")
    if not isinstance(screenplay, Mapping):
        return
    roster = [
        character.get("name")
        for character in screenplay.get("characters", [])
        if isinstance(character, Mapping)
    ]
    if len(roster) != len(set(roster)):
        raise _error(
            "DIRECTOR_CHARACTER_REFERENCE_UNKNOWN",
            "screenplay roster contains duplicate character names",
            "Use one canonical roster entry per character identity.",
        )
    known = set(roster)
    for scene in screenplay.get("scenes", []):
        if not isinstance(scene, Mapping):
            continue
        unknown = sorted(set(scene.get("characters", [])) - known)
        if unknown:
            raise _error(
                "DIRECTOR_CHARACTER_REFERENCE_UNKNOWN",
                f"scene {scene.get('scene_index')} references unknown characters {unknown}",
                "Add an explicit roster entry and appearance/voice state for every character.",
                **{"scene_index": scene.get("scene_index"), "characters": unknown},
            )


def load_request(path: str | Path) -> DirectorRequest:
    """Read and classify one typed request before Pydantic's generic rejection."""

    source = Path(path).expanduser().resolve()
    try:
        document = json.loads(source.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise _error(
            "DIRECTOR_REQUEST_MISSING",
            f"request does not exist: {source}",
            "Pass an existing director request JSON file.",
        ) from exc
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise _error(
            "DIRECTOR_REQUEST_INVALID",
            f"cannot read request {source}: {exc}",
            "Fix the request JSON encoding and syntax.",
        ) from exc
    if not isinstance(document, dict):
        raise _error(
            "DIRECTOR_REQUEST_INVALID",
            "request JSON must be an object",
            "Use the director request schema documented in director-capabilities.md.",
        )
    _classify_source_shape(document)
    _classify_screenplay(document)
    try:
        request = DirectorRequest.model_validate(document)
    except ValidationError as exc:
        raise _error(
            "DIRECTOR_REQUEST_INVALID",
            f"request validation failed: {exc.error_count()} field errors",
            "Fix the typed request, then rerun deterministic planning.",
            errors=[
                {
                    "path": ".".join(str(part) for part in error["loc"]),
                    "message": error["msg"],
                }
                for error in exc.errors()
            ],
        ) from exc
    if request.queue_enhancement is not None:
        unsupported = (
            set(request.queue_enhancement.allowed_fields)
            - SUPPORTED_ENHANCEMENT_FIELDS
        )
        if (
            request.queue_enhancement.intent not in SUPPORTED_ENHANCEMENT_INTENTS
            or unsupported
        ):
            raise _error(
                "DIRECTOR_QUEUE_ENHANCEMENT_UNSUPPORTED",
                "only intent replace_prompt and field prompt are supported",
                "Use replace_prompt with allowed_fields=['prompt'].",
                **{
                    "intent": request.queue_enhancement.intent,
                    "allowed_fields": sorted(unsupported),
                },
            )
    return request


def load_enhancement_request(path: str | Path) -> DirectorEnhancementRequest:
    source = Path(path).expanduser().resolve()
    try:
        document = json.loads(source.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise _error(
            "DIRECTOR_ENHANCEMENT_REQUEST_MISSING",
            f"request does not exist: {source}",
            "Pass an existing director enhancement request JSON file.",
            next_command=ENHANCE_NEXT_COMMAND,
        ) from exc
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise _error(
            "DIRECTOR_ENHANCEMENT_REQUEST_INVALID",
            f"cannot read enhancement request {source}: {exc}",
            "Fix the enhancement request JSON.",
            next_command=ENHANCE_NEXT_COMMAND,
        ) from exc
    try:
        return DirectorEnhancementRequest.model_validate(document)
    except ValidationError as exc:
        raise _error(
            "DIRECTOR_ENHANCEMENT_REQUEST_INVALID",
            f"enhancement validation failed: {exc.error_count()} field errors",
            "Fix the typed enhancement request.",
            next_command=ENHANCE_NEXT_COMMAND,
        ) from exc


def _verify_audio(request: DirectorRequest) -> None:
    if request.audio is None:
        return
    source = Path(request.audio.path).expanduser().resolve()
    if not source.is_file():
        raise _error(
            "DIRECTOR_AUDIO_MISSING",
            f"audio source is not readable: {source}",
            "Restore the authorized committed audio; Wangp will not fetch source material.",
            **{"path": str(source), "expected_sha256": request.audio.sha256},
        )
    actual_hash = file_sha256(source)
    if actual_hash != request.audio.sha256:
        raise _error(
            "DIRECTOR_AUDIO_HASH_MISMATCH",
            f"audio hash mismatch: expected {request.audio.sha256}, got {actual_hash}",
            "Restore the exact committed bytes or correct the declared provenance.",
            **{
                "path": str(source),
                "expected": request.audio.sha256,
                "actual": actual_hash,
            },
        )
    if abs(request.audio.duration_s - request.pacing.target_duration_s) > 1e-6:
        raise _error(
            "DIRECTOR_AUDIO_DURATION_MISMATCH",
            (
                f"audio duration {request.audio.duration_s:.9f}s does not match "
                f"target {request.pacing.target_duration_s:.9f}s"
            ),
            "Set pacing.target_duration_s to the declared measured audio duration.",
            **{
                "audio_duration_s": request.audio.duration_s,
                "target_duration_s": request.pacing.target_duration_s,
            },
        )


def _clip_prompt(
    request: DirectorRequest, clip_index: int, window: Mapping[str, Any]
) -> str:
    prefix = f"{request.title} -- deterministic clip {clip_index}"
    timing = (
        f"window {window['start_s']:.9f}s to {window['end_s']:.9f}s "
        f"({window['duration_s']:.9f}s)"
    )
    if request.mode is DirectorMode.prompt:
        assert request.prompt is not None
        return f"{prefix}: {request.prompt} | {timing}"
    if request.mode is DirectorMode.audio:
        assert request.audio is not None
        return (
            f"{prefix}: audio-guided continuation from {request.audio.sha256} "
            f"| {timing}"
        )
    if request.mode is DirectorMode.music_video:
        beat_count = len(window["beat_evidence"])
        return f"{prefix}: beat-aware music-video shot over {beat_count} beats | {timing}"
    assert request.screenplay is not None
    scene_index = window["scene_index"]
    scene = request.screenplay.scenes[int(scene_index) - 1]
    states = "; ".join(
        f"{state.name}: appearance={state.appearance}, voice={state.voice}"
        for state in sorted(scene.states, key=lambda item: item.name)
    )
    return f"{prefix}: {scene.slugline} | {scene.action} | {states} | {timing}"


def compile_director_request(request: DirectorRequest) -> CompiledDirectorPlan:
    """Validate all local evidence, then emit one ordered non-executable plan."""

    _verify_audio(request)
    windows = plan_windows(request)
    continuity = continuity_declarations(request, windows)
    review = review_policy(request)
    request_value = _request_payload(request)
    request_hash = canonical_sha256(request_value)
    clips: list[dict[str, Any]] = []
    for window in windows:
        mapping = window.mapping()
        clip_index = window.index
        prompt = _clip_prompt(request, clip_index, mapping)
        clips.append(
            {
                "kind": "director_plan_clip",
                "clip_index": clip_index,
                "status": "planned",
                "prompt": prompt,
                "recipe_seed": (
                    request.recipe_seed + clip_index * 104_729
                ) % 2_147_483_647,
                "window": mapping,
                "overlap": {
                    "strategy": "six_frame_sliding_window",
                    "frames": 6 if window.index < len(windows) else 0,
                    "frames_on_24fps_grid": True,
                },
                "continuity": continuity["clips"][clip_index - 1],
                "review": {
                    "mode": review["mode"],
                    "checkpoint": "after_clip",
                    "mandatory_gates": review["mandatory_gates"],
                    "bypasses_gate": False,
                },
                "media": None,
                "quality_verdict": None,
                "planning_only": True,
            }
        )
    duration_s = sum(clip["window"]["duration_s"] for clip in clips)
    payload = {
        "schema_version": PLAN_SCHEMA_VERSION,
        "request_schema_version": REQUEST_SCHEMA,
        "request_sha256": request_hash,
        "capability_status": "planned",
        "mode": request.mode.value,
        "title": request.title,
        "planning_surfaces": [
            item for item in PLANNING_SURFACES if item["mode"] == request.mode.value
        ],
        "clip_count": len(clips),
        "duration_s": round(duration_s, 9),
        "source_duration_preserved": (
            abs(duration_s - request.pacing.target_duration_s) <= 1e-6
        ),
        "continuity": continuity,
        "pacing": {
            "strategy": request.pacing.strategy,
            "target_duration_s": request.pacing.target_duration_s,
            "windows": [window.mapping() for window in windows],
        },
        "review": review,
        "queue_enhancement": (
            request.queue_enhancement.model_dump(mode="json")
            if request.queue_enhancement is not None
            else None
        ),
        "clips": clips,
        "recipe": {
            "schema_version": "wangp-dspy.director-recipe-input/v1",
            "request": request_value,
        },
        "summary": {
            "gpu_work": False,
            "host_contact": False,
            "queue_submitted": False,
            "media_generated": False,
            "generated_media_reviewed": False,
        },
    }
    return CompiledDirectorPlan(payload)


def _create_immutable_table(connection: sqlite3.Connection, table: str) -> None:
    connection.execute(
        f"CREATE TABLE {table} (record_id TEXT PRIMARY KEY, "
        "request_sha256 TEXT NOT NULL, clip_index INTEGER NOT NULL, "
        "record TEXT NOT NULL, created_at REAL NOT NULL)"
    )
    connection.execute(
        f"CREATE TRIGGER {table}_immutable_update BEFORE UPDATE ON {table} "
        "BEGIN SELECT RAISE(ABORT, 'director plan records are immutable'); END"
    )
    connection.execute(
        f"CREATE TRIGGER {table}_immutable_delete BEFORE DELETE ON {table} "
        "BEGIN SELECT RAISE(ABORT, 'director plan records are immutable'); END"
    )


def _new_database(
    destination: Path,
    table: str,
    records: list[tuple[int, Mapping[str, Any]]],
    request_hash: str,
    *,
    code_exists: str,
) -> list[str]:
    if destination.exists():
        raise _error(
            code_exists,
            f"database already exists: {destination}",
            "Choose a new database path; this surface never overwrites records.",
            next_command=PLAN_NEXT_COMMAND,
            path=str(destination),
        )
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = destination.parent / f".{destination.name}.{os.urandom(8).hex()}.tmp"
    ids: list[str] = []
    connection: sqlite3.Connection | None = None
    try:
        connection = sqlite3.connect(staging)
        connection.execute("PRAGMA journal_mode=WAL")
        _create_immutable_table(connection, table)
        for clip_index, record in records:
            record_id = f"director-plan-{int(time.time() * 1000)}-{os.urandom(4).hex()}"
            connection.execute(
                f"INSERT INTO {table} VALUES (?,?,?,?,?)",
                (
                    record_id,
                    request_hash,
                    clip_index,
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


def enqueue_director_plan(
    plan: Mapping[str, Any], database: str | Path
) -> list[str]:
    """Persist clips outside the executable jobs table without draining them."""

    destination = Path(database).expanduser().resolve()
    records = []
    for clip in plan["clips"]:
        records.append(
            (
                int(clip["clip_index"]),
                {
                    "kind": "director_plan_record",
                    "schema_version": PLAN_SCHEMA_VERSION,
                    "request_sha256": plan["request_sha256"],
                    "clip": clip,
                    "recipe": plan["recipe"],
                    "plan_only": True,
                    "executable": False,
                    "queue_submitted": False,
                    "host_contact": False,
                    "media_generated": False,
                },
            )
        )
    return _new_database(
        destination,
        "director_plan_records",
        records,
        str(plan["request_sha256"]),
        code_exists="DIRECTOR_QUEUE_EXISTS",
    )


def _open_records(
    database: str | Path, *, expected_kind: str
) -> list[tuple[str, Mapping[str, Any]]]:
    path = Path(database).expanduser().resolve()
    if not path.is_file():
        raise _error(
            "DIRECTOR_RECONSTRUCTION_DATABASE_MISSING",
            f"database does not exist: {path}",
            "Pass a SQLite database emitted by wgp director plan or enhance.",
            next_command=RECONSTRUCT_NEXT_COMMAND,
        )
    connection: sqlite3.Connection | None = None
    try:
        connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        table = next(
            (
                name
                for name in (
                    "director_plan_records",
                    "director_enhancement_records",
                )
                if name in tables
            ),
            None,
        )
        if table is None:
            raise DirectorError(
                "DIRECTOR_RECONSTRUCTION_RECORDS_MISSING",
                f"database {path} has no director records",
                "Use a database emitted by wgp director plan or enhance.",
                next_command=RECONSTRUCT_NEXT_COMMAND,
            )
        rows = connection.execute(
            f"SELECT record_id, record FROM {table} "
            "ORDER BY clip_index, created_at, record_id"
        ).fetchall()
    except sqlite3.Error as exc:
        raise _error(
            "DIRECTOR_RECONSTRUCTION_DATABASE_INVALID",
            f"cannot open database {path}: {exc}",
            "Use an undamaged database emitted by wgp director.",
            next_command=RECONSTRUCT_NEXT_COMMAND,
        ) from exc
    finally:
        if connection is not None:
            connection.close()
    if not rows:
        raise _error(
            "DIRECTOR_RECONSTRUCTION_RECORDS_MISSING",
            f"database {path} contains zero director records",
            "Plan a nonempty director request before reconstruction.",
            next_command=RECONSTRUCT_NEXT_COMMAND,
        )
    parsed: list[tuple[str, Mapping[str, Any]]] = []
    for record_id, raw in rows:
        try:
            record = json.loads(raw)
            if record.get("kind") != expected_kind:
                raise ValueError(f"unexpected kind {record.get('kind')!r}")
        except Exception as exc:
            raise _error(
                "DIRECTOR_RECONSTRUCTION_RECORD_INVALID",
                f"record {record_id} cannot be parsed: {exc}",
                "Regenerate the plan; do not edit immutable director records.",
                next_command=RECONSTRUCT_NEXT_COMMAND,
                record_id=record_id,
            ) from exc
        parsed.append((record_id, record))
    return parsed


def reconstruct_director_database(database: str | Path) -> list[dict[str, Any]]:
    """Independently recompile every seed recipe and compare canonical hashes."""

    rows = _open_records(database, expected_kind="director_plan_record")
    results: list[dict[str, Any]] = []
    for record_id, record in rows:
        try:
            request = DirectorRequest.model_validate(record["recipe"]["request"])
            plan = compile_director_request(request).mapping()
            index = int(record["clip"]["clip_index"])
            reconstructed_clip = plan["clips"][index - 1]
        except Exception as exc:
            raise _error(
                "DIRECTOR_RECONSTRUCTION_RECORD_INVALID",
                f"record {record_id} cannot be reconstructed: {exc}",
                "Regenerate the plan from the original typed request.",
                next_command=RECONSTRUCT_NEXT_COMMAND,
                record_id=record_id,
            ) from exc
        recorded_clip_hash = canonical_sha256(record["clip"])
        reconstructed_clip_hash = canonical_sha256(reconstructed_clip)
        recorded_request_hash = str(record["request_sha256"])
        reconstructed_request_hash = str(plan["request_sha256"])
        match = (
            recorded_clip_hash == reconstructed_clip_hash
            and recorded_request_hash == reconstructed_request_hash
        )
        results.append(
            {
                "record_id": record_id,
                "clip_index": int(record["clip"]["clip_index"]),
                "recorded_request_sha256": recorded_request_hash,
                "reconstructed_request_sha256": reconstructed_request_hash,
                "recorded_clip_sha256": recorded_clip_hash,
                "reconstructed_clip_sha256": reconstructed_clip_hash,
                "match": match,
                "hidden_mutation": not match,
            }
        )
    return results


def _source_records(
    request: DirectorEnhancementRequest,
) -> list[tuple[str, Mapping[str, Any]]]:
    return _open_records(request.source_db, expected_kind="director_plan_record")


def enhance_director_database(
    request: DirectorEnhancementRequest, destination: str | Path
) -> dict[str, Any]:
    """Copy a plan with one authorized prompt change and preserved original hash."""

    output = Path(destination).expanduser().resolve()
    rows = _source_records(request)
    records: list[tuple[int, Mapping[str, Any]]] = []
    original_hashes: set[str] = set()
    changed_hashes: set[str] = set()
    for _record_id, source in rows:
        try:
            original_request = DirectorRequest.model_validate(
                source["recipe"]["request"]
            )
            intent = original_request.queue_enhancement
            if (
                intent is None
                or intent.intent not in SUPPORTED_ENHANCEMENT_INTENTS
                or "prompt" not in intent.allowed_fields
            ):
                raise ValueError("source request did not authorize replace_prompt")
            changed_value = original_request.model_dump(mode="json")
            changed_value["prompt"] = request.changes.prompt
            changed_request = DirectorRequest.model_validate(changed_value)
            changed_plan = compile_director_request(changed_request).mapping()
        except DirectorError:
            raise
        except Exception as exc:
            raise _error(
                "DIRECTOR_QUEUE_ENHANCEMENT_INVALID",
                f"source record cannot be enhanced: {exc}",
                "Enhance a valid plan whose request authorizes prompt replacement.",
                next_command=ENHANCE_NEXT_COMMAND,
            ) from exc
        original_hashes.add(str(source["request_sha256"]))
        changed_hashes.add(str(changed_plan["request_sha256"]))
        clip = changed_plan["clips"][int(source["clip"]["clip_index"]) - 1]
        records.append(
            (
                int(clip["clip_index"]),
                {
                    "kind": "director_enhancement_record",
                    "schema_version": ENHANCED_PLAN_SCHEMA_VERSION,
                    "request_schema_version": ENHANCEMENT_SCHEMA,
                    "original_request_sha256": source["request_sha256"],
                    "enhanced_request_sha256": changed_plan["request_sha256"],
                    "clip_index": clip["clip_index"],
                    "clip": clip,
                    "original_recipe": source["recipe"],
                    "changes": request.changes.model_dump(mode="json"),
                    "provenance_reason": request.provenance_reason,
                    "changed_fields": ["prompt"],
                    "plan_only": True,
                    "executable": False,
                    "queue_submitted": False,
                    "host_contact": False,
                    "media_generated": False,
                },
            )
        )
    if len(original_hashes) != 1 or len(changed_hashes) != 1:
        raise _error(
            "DIRECTOR_QUEUE_ENHANCEMENT_INVALID",
            "enhancement source contains mixed requests",
            "Enhance one complete director plan emitted from one request.",
            next_command=ENHANCE_NEXT_COMMAND,
        )
    ids = _new_database(
        output,
        "director_enhancement_records",
        records,
        next(iter(changed_hashes)),
        code_exists="DIRECTOR_QUEUE_OUTPUT_EXISTS",
    )
    return {
        "schema_version": ENHANCED_PLAN_SCHEMA_VERSION,
        "source_database": str(Path(request.source_db).expanduser().resolve()),
        "output_database": str(output),
        "original_request_sha256": next(iter(original_hashes)),
        "enhanced_request_sha256": next(iter(changed_hashes)),
        "changed_fields": ["prompt"],
        "provenance_reason": request.provenance_reason,
        "record_ids": ids,
        "source_mutated": False,
        "executable_jobs": 0,
        "queue_submitted": False,
        "host_contact": False,
        "media_generated": False,
    }


def reconstruct_enhancement_database(
    database: str | Path,
) -> list[dict[str, Any]]:
    """Reapply only the recorded prompt change and compare both request hashes."""

    rows = _open_records(database, expected_kind="director_enhancement_record")
    results: list[dict[str, Any]] = []
    for record_id, record in rows:
        try:
            original = DirectorRequest.model_validate(
                record["original_recipe"]["request"]
            )
            changed_value = original.model_dump(mode="json")
            changed_value["prompt"] = record["changes"]["prompt"]
            changed = DirectorRequest.model_validate(changed_value)
            changed_plan = compile_director_request(changed).mapping()
            expected_clip = changed_plan["clips"][int(record["clip_index"]) - 1]
        except Exception as exc:
            raise _error(
                "DIRECTOR_RECONSTRUCTION_RECORD_INVALID",
                f"enhancement record {record_id} cannot be reconstructed: {exc}",
                "Regenerate the enhancement from its original typed request.",
                next_command=RECONSTRUCT_NEXT_COMMAND,
                record_id=record_id,
            ) from exc
        original_hash = canonical_sha256(original.model_dump(mode="json"))
        changed_hash = canonical_sha256(changed.model_dump(mode="json"))
        clip_match = canonical_sha256(record["clip"]) == canonical_sha256(
            expected_clip
        )
        original_match = original_hash == record["original_request_sha256"]
        changed_match = changed_hash == record["enhanced_request_sha256"]
        match = clip_match and original_match and changed_match
        results.append(
            {
                "record_id": record_id,
                "clip_index": int(record["clip_index"]),
                "recorded_original_request_sha256": record[
                    "original_request_sha256"
                ],
                "reconstructed_original_request_sha256": original_hash,
                "recorded_enhanced_request_sha256": record[
                    "enhanced_request_sha256"
                ],
                "reconstructed_enhanced_request_sha256": changed_hash,
                "recorded_clip_sha256": canonical_sha256(record["clip"]),
                "reconstructed_clip_sha256": canonical_sha256(expected_clip),
                "changed_fields": list(record["changed_fields"]),
                "match": match,
                "hidden_mutation": not match,
            }
        )
    return results


def reconstruct_director_records(database: str | Path) -> list[dict[str, Any]]:
    """Reconstruct either an original or enhanced immutable director database."""

    path = Path(database).expanduser().resolve()
    if not path.is_file():
        raise _error(
            "DIRECTOR_RECONSTRUCTION_DATABASE_MISSING",
            f"database does not exist: {path}",
            "Pass a SQLite database emitted by wgp director plan or enhance.",
            next_command=RECONSTRUCT_NEXT_COMMAND,
        )
    connection: sqlite3.Connection | None = None
    try:
        connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
    except sqlite3.Error as exc:
        raise _error(
            "DIRECTOR_RECONSTRUCTION_DATABASE_INVALID",
            f"cannot inspect database {path}: {exc}",
            "Use an undamaged database emitted by wgp director.",
            next_command=RECONSTRUCT_NEXT_COMMAND,
        ) from exc
    finally:
        if connection is not None:
            connection.close()
    if "director_enhancement_records" in tables:
        return reconstruct_enhancement_database(path)
    return reconstruct_director_database(path)


def inspect_queue_database(database: str | Path) -> dict[str, Any]:
    """Use the real admission selector without mutating the plan database."""

    from services.jobs.queue import JobQueue
    import shutil

    path = Path(database).expanduser().resolve()
    rows = _open_records(path, expected_kind="director_plan_record")
    with tempfile.TemporaryDirectory(prefix="wangp-director-admission-") as temporary:
        admission_copy = Path(temporary) / "admission-copy.db"
        shutil.copy2(path, admission_copy)
        queue = JobQueue(admission_copy)
        try:
            pending = queue.list_state("pending")
            selected = queue.next_admissible()
        finally:
            queue.close()
    return {
        "schema_version": "wangp-dspy.director-queue-inspection/v1",
        "database": str(path),
        "record_count": len(rows),
        "table": "director_plan_records",
        "real_admission_selector": (
            "services.jobs.queue.JobQueue.next_admissible"
        ),
        "pending_jobs": pending,
        "selected_job": selected,
        "executable_jobs": 0,
        "drainable": selected is not None,
        "queue_submitted": False,
        "host_contact": False,
        "mutation_performed": False,
    }


__all__ = [
    "CompiledDirectorPlan",
    "ENHANCED_PLAN_SCHEMA_VERSION",
    "PLAN_SCHEMA_VERSION",
    "compile_director_request",
    "enhance_director_database",
    "enqueue_director_plan",
    "inspect_queue_database",
    "load_enhancement_request",
    "load_request",
    "reconstruct_director_records",
    "reconstruct_director_database",
    "reconstruct_enhancement_database",
    "request_digest",
]
