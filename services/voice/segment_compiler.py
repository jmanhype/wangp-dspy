"""Compile typed speech requests into immutable, non-executable records."""
from __future__ import annotations

import json
import os
import re
import sqlite3
import time
import hashlib
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from host.speech_backends import backend_for
from predict.speech_capabilities import (
    SpeechCapabilityError,
    SpeechCapabilityRequest,
    backend_settings,
    canonical_sha256,
    file_sha256,
    request_digest,
)

PLAN_SCHEMA_VERSION = "wangp-dspy.speech-capability-plan/v1"
_SENTENCE = re.compile(r"(?<=[.!?…])\s+")


@dataclass(frozen=True)
class CompiledSpeechPlan:
    payload: dict[str, Any]

    def mapping(self) -> dict[str, Any]:
        return self.payload


def split_speech_text(request: SpeechCapabilityRequest) -> list[str]:
    normalized = re.sub(r"\s+", " ", request.text).strip()
    limit = request.segment_policy.max_segment_chars
    sentences = [item.strip() for item in _SENTENCE.split(normalized) if item.strip()]
    if not sentences:
        raise SpeechCapabilityError(
            "SPEECH_TEXT_INVALID",
            "speech text contains no non-whitespace characters",
            "Supply readable text; Wangp will not invent a transcript.",
        )
    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        if len(sentence) <= limit:
            candidate = sentence if not current else current + " " + sentence
            if len(candidate) <= limit:
                current = candidate
            else:
                if current:
                    chunks.append(current)
                current = sentence
            continue
        if request.segment_policy.split_on_sentence is False:
            raise SpeechCapabilityError(
                "SPEECH_SEGMENT_INVALID",
                f"segment of {len(sentence)} characters exceeds the {limit}-character limit",
                "Enable sentence splitting or shorten the over-limit segment.",
                metadata={"segment_chars": len(sentence), "limit": limit},
            )
        words = sentence.split(" ")
        if current:
            chunks.append(current)
            current = ""
        for word in words:
            if len(word) > limit:
                raise SpeechCapabilityError(
                    "SPEECH_SEGMENT_INVALID",
                    f"unsplittable token has {len(word)} characters; engine limit is {limit}",
                    "Break the token or raise the engine-compatible segment limit.",
                    metadata={"token_chars": len(word), "limit": limit},
                )
            candidate = word if not current else current + " " + word
            if len(candidate) > limit and current:
                chunks.append(current)
                current = word
            else:
                current = candidate
        if current:
            chunks.append(current)
    if current:
        chunks.append(current)
    return chunks


def _reference(index: int, reference) -> dict[str, Any]:
    path = Path(reference.path).expanduser().resolve()
    if not path.is_file():
        raise SpeechCapabilityError(
            "SPEECH_REFERENCE_MISSING",
            f"voice reference {index} is not readable: {path}",
            "Restore the authorized WAV; Wangp will not fetch source material.",
            metadata={"reference_index": index, "path": str(path)},
        )
    actual = file_sha256(path)
    if actual != reference.sha256:
        raise SpeechCapabilityError(
            "SPEECH_REFERENCE_UNUSABLE",
            f"voice reference {index} hash mismatch: expected {reference.sha256}, got {actual}",
            "Restore the exact authorized reference bytes.",
            metadata={"reference_index": index, "expected": reference.sha256, "actual": actual},
        )
    try:
        with wave.open(str(path), "rb") as audio:
            frames = audio.getnframes()
            rate = audio.getframerate()
            duration = frames / rate if rate else 0.0
    except (OSError, ValueError, wave.Error) as exc:
        raise SpeechCapabilityError(
            "SPEECH_REFERENCE_UNUSABLE",
            f"voice reference {index} is not readable RIFF/WAV audio: {exc}",
            "Supply a valid single-speaker WAV recorded by the authorized source.",
            metadata={"reference_index": index, "path": str(path)},
        ) from exc
    if abs(duration - reference.duration_s) > 0.05:
        raise SpeechCapabilityError(
            "SPEECH_REFERENCE_UNUSABLE",
            f"voice reference {index} duration is {duration:.3f}s, not declared {reference.duration_s:.3f}s",
            "Correct the declared duration or supply the exact authorized WAV.",
            metadata={"reference_index": index, "actual_duration_s": duration},
        )
    return {
        "path": str(path),
        "sha256": actual,
        "role": reference.role,
        "duration_s": reference.duration_s,
        "source": reference.source,
        "license": reference.license,
        "consent_ref": reference.consent_ref,
    }


def compile_speech_request(request: SpeechCapabilityRequest) -> CompiledSpeechPlan:
    """Validate every local input before creating one durable record per segment."""

    output = Path(request.output_path_planned).expanduser().resolve()
    if output.exists():
        raise SpeechCapabilityError(
            "SPEECH_OUTPUT_EXISTS",
            f"planned assembled audio path already exists: {output}",
            "Choose a new output path; planning must not claim or overwrite audio.",
        )
    references = [
        _reference(index, reference)
        for index, reference in enumerate(request.references, start=1)
    ]
    chunks = split_speech_text(request)
    adapter = backend_for(request.model.family)
    settings = backend_settings(request)
    segments: list[dict[str, Any]] = []
    cursor = 0
    for index, text in enumerate(chunks, start=1):
        end = cursor + len(text)
        segments.append({
            "segment_index": index,
            "start_char": cursor,
            "end_char": end,
            "text": text,
            "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "char_count": len(text),
            "planned_silence_after_s": request.segment_policy.silence_s if index < len(chunks) else 0.0,
        })
        cursor = end + (1 if index < len(chunks) else 0)
    assembly = {
        "operation": "ordered_concatenation",
        "order": [item["segment_index"] for item in segments],
        "inter_segment_silence_s": request.segment_policy.silence_s,
        "assembled_target": str(output),
        "assembled_audio": None,
        "planned_character_count": sum(item["char_count"] for item in segments),
        "planned_source_character_count": len(request.text),
        "planned_separator_count": max(0, len(segments) - 1),
        "planned_silence_count": max(0, len(segments) - 1),
        "planned_total_silence_s": round(request.segment_policy.silence_s * max(0, len(segments) - 1), 6),
        "measurement_status": "not verified - requires authorized host run",
    }
    records: list[dict[str, Any]] = []
    for segment in segments:
        segment_settings = dict(settings)
        segment_settings.update({
            "segment_index": segment["segment_index"],
            "segment_text": segment["text"],
            "segment_text_sha256": segment["text_sha256"],
        })
        records.append({
            "segment_index": segment["segment_index"],
            "kind": "speech_plan_record",
            "status": "planned",
            "mode": request.mode.value,
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
            "text": segment,
            "text_hash": settings["text_sha256"],
            "engine_settings": {
                "language": request.language,
                "style": request.style,
                "recipe_seed": request.recipe_seed,
            },
            "voice_package": {
                "character": request.character.model_dump(mode="json") if request.character else None,
                "sha256": canonical_sha256(request.character.model_dump(mode="json")) if request.character else None,
                "references": references,
            },
            "assembly": assembly,
            "format": {
                "sample_rate_hz": request.output_format.sample_rate_hz,
                "channels": request.output_format.channels,
                "measurement_status": "not verified - requires authorized host run",
            },
            "recipe": request.model_dump(mode="json"),
            "backend_settings": segment_settings,
            "backend_settings_sha256": canonical_sha256(segment_settings),
            "audio": None,
            "queue_submitted": False,
            "host_contact": False,
            "plan_only": True,
            "executable": False,
        })
    return CompiledSpeechPlan({
        "schema_version": PLAN_SCHEMA_VERSION,
        "request_sha256": request_digest(request),
        "capability_status": "planned",
        "mode": request.mode.value,
        "engine": request.model.model_dump(mode="json"),
        "segment_count": len(records),
        "segments": segments,
        "assembly": assembly,
        "records": records,
        "summary": {
            "gpu_work": False,
            "audio_created": False,
            "queue_submitted": False,
            "host_contact": False,
        },
    })


def enqueue_speech_plan(plan: Mapping[str, Any], database: str | Path) -> list[str]:
    """Atomically persist immutable segment records outside the executable jobs table."""

    destination = Path(database).expanduser().resolve()
    if destination.exists():
        raise SpeechCapabilityError(
            "SPEECH_QUEUE_EXISTS",
            f"queue database already exists: {destination}",
            "Select a new database path for this no-GPU speech plan.",
        )
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = destination.parent / f".{destination.name}.{os.urandom(8).hex()}.tmp"
    ids: list[str] = []
    connection: sqlite3.Connection | None = None
    try:
        connection = sqlite3.connect(staging)
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute(
            "CREATE TABLE speech_plan_records ("
            "record_id TEXT PRIMARY KEY, plan_ref TEXT NOT NULL, segment_index INTEGER NOT NULL, "
            "record TEXT NOT NULL, created_at REAL NOT NULL)"
        )
        connection.execute(
            "CREATE TRIGGER speech_plan_records_immutable_update BEFORE UPDATE ON speech_plan_records "
            "BEGIN SELECT RAISE(ABORT, 'speech plan records are immutable'); END"
        )
        connection.execute(
            "CREATE TRIGGER speech_plan_records_immutable_delete BEFORE DELETE ON speech_plan_records "
            "BEGIN SELECT RAISE(ABORT, 'speech plan records are immutable'); END"
        )
        for record in plan["records"]:
            record_id = f"speech-plan-{int(time.time() * 1000)}-{os.urandom(4).hex()}"
            connection.execute(
                "INSERT INTO speech_plan_records VALUES (?,?,?,?,?)",
                (record_id, str(plan["request_sha256"]), int(record["segment_index"]),
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


def reconstruct_speech_settings(record: Mapping[str, Any]) -> dict[str, Any]:
    request = SpeechCapabilityRequest.model_validate(record["recipe"])
    chunks = split_speech_text(request)
    settings = backend_settings(request)
    index = int(record["segment_index"])
    if index < 1 or index > len(chunks):
        raise ValueError(f"segment index {index} outside reconstructed range")
    settings.update({
        "segment_index": index,
        "segment_text": chunks[index - 1],
        "segment_text_sha256": hashlib.sha256(chunks[index - 1].encode("utf-8")).hexdigest(),
    })
    return settings


def reconstruct_speech_database(database: str | Path) -> list[dict[str, Any]]:
    path = Path(database).expanduser().resolve()
    if not path.is_file():
        raise SpeechCapabilityError(
            "SPEECH_RECONSTRUCTION_DATABASE_MISSING",
            f"plan database does not exist: {path}",
            "Pass a SQLite database emitted by wgp voice clone/plan.",
            next_command="wgp voice plan --db <plan.db> --reconstruct --json",
        )
    connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if "speech_plan_records" not in tables:
            raise SpeechCapabilityError(
                "SPEECH_RECONSTRUCTION_RECORDS_MISSING",
                f"database {path} has no speech_plan_records table",
                "Use a database emitted by wgp voice.",
            )
        rows = connection.execute(
            "SELECT record_id, record FROM speech_plan_records ORDER BY segment_index, created_at, record_id"
        ).fetchall()
    finally:
        connection.close()
    if not rows:
        raise SpeechCapabilityError(
            "SPEECH_RECONSTRUCTION_RECORDS_MISSING",
            f"database {path} contains zero speech plan records",
            "Compile a nonempty wgp voice plan.",
        )
    results: list[dict[str, Any]] = []
    for record_id, raw in rows:
        try:
            record = json.loads(raw)
            if record.get("kind") != "speech_plan_record":
                raise ValueError(f"unexpected kind {record.get('kind')!r}")
            reconstructed = reconstruct_speech_settings(record)
        except Exception as exc:
            raise SpeechCapabilityError(
                "SPEECH_RECONSTRUCTION_RECORD_INVALID",
                f"plan record {record_id} cannot be reconstructed: {exc}",
                "Restore the unedited wgp voice record or regenerate the no-GPU plan.",
                metadata={"record_id": record_id},
            ) from exc
        original = record["backend_settings_sha256"]
        actual = canonical_sha256(reconstructed)
        results.append({
            "record_id": record_id,
            "segment_index": record["segment_index"],
            "recipe_seed": record["engine_settings"]["recipe_seed"],
            "recorded_settings_sha256": original,
            "reconstructed_settings_sha256": actual,
            "match": original == actual,
            "hidden_mutation": original != actual,
        })
    return results


__all__ = [
    "CompiledSpeechPlan",
    "PLAN_SCHEMA_VERSION",
    "compile_speech_request",
    "enqueue_speech_plan",
    "reconstruct_speech_database",
    "reconstruct_speech_settings",
    "split_speech_text",
]
