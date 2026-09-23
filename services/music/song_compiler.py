"""Compile typed music requests into immutable, non-executable plans."""
from __future__ import annotations

import json
import os
import re
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from predict.music_capabilities import (
    MusicCapabilityError,
    MusicCapabilityRequest,
    backend_settings,
    canonical_sha256,
    file_sha256,
    request_digest,
)

PLAN_SCHEMA_VERSION = "wangp-dspy.music-capability-plan/v1"
_CHORD = re.compile(r"^[A-G][b#]?(?:maj|min|m|dim|aug|sus2|sus4|7|maj7|m7|dim7|aug7)?(?:/[A-G][b#]?)?$")
_NOTE = re.compile(r"^(?:[A-Ga-gzZ][',]*\d*|-|\(|\))$")


@dataclass(frozen=True)
class CompiledMusicPlan:
    payload: dict[str, Any]

    def mapping(self) -> dict[str, Any]:
        return self.payload


def _validate_melody(section_name: str, melody: str) -> list[str]:
    lines = [line.strip() for line in melody.replace("\r\n", "\n").splitlines() if line.strip()]
    if not lines:
        raise MusicCapabilityError(
            "MUSIC_SCORE_INVALID", f"section {section_name!r} melody_abc is empty",
            "Supply at least one complete ABC music line.",
        )
    for line_number, line in enumerate(lines, start=1):
        if not line.startswith("|") or not line.endswith("|"):
            raise MusicCapabilityError(
                "MUSIC_SCORE_INVALID",
                f"section {section_name!r} line {line_number} must begin and end with a bar line",
                "Use complete |...| ABC bars.",
            )
        bars = [bar.strip() for bar in line.strip("|").split("|")]
        if any(not bar for bar in bars):
            raise MusicCapabilityError(
                "MUSIC_SCORE_INVALID", f"section {section_name!r} line {line_number} has an empty bar",
                "Remove empty bars or complete each bar with ABC notes/rests.",
            )
        for bar in bars:
            tokens = [token for token in re.split(r"\s+", bar) if token]
            if len(tokens) < 2 or any(_NOTE.fullmatch(token) is None for token in tokens):
                raise MusicCapabilityError(
                    "MUSIC_SCORE_INVALID",
                    f"section {section_name!r} line {line_number} contains a non-ABC token",
                    "Use ABC notes/rests, duration digits, octave marks, ties, and bar separators only.",
                )
    return lines


def _validate_chords(section_name: str, chords: list[str]) -> None:
    for chord in chords:
        if _CHORD.fullmatch(chord) is None:
            raise MusicCapabilityError(
                "MUSIC_SCORE_INVALID", f"section {section_name!r} has invalid chord symbol {chord!r}",
                "Use lead-sheet symbols such as C, Am, Fmaj7, or G/B.",
            )


def normalize_score(request: MusicCapabilityRequest) -> str:
    blocks: list[str] = [
        f"X:1\nT:{request.title}\nC:operator request\nM:{request.meter}\nL:1/4",
        f"Q:1/4={request.tempo_bpm}\nK:{request.key}",
    ]
    for section in request.sections:
        melody = _validate_melody(section.name, section.melody_abc)
        _validate_chords(section.name, list(section.chords))
        chord_line = " ".join(f'"{chord}" z4' for chord in section.chords)
        blocks.append(
            f"%section {section.name} {section.duration_s:g}s\n"
            + "\n".join(melody) + f"\n%chords\n{chord_line}|"
        )
    return "\n".join(blocks) + "\n"


def _style_payload(request: MusicCapabilityRequest) -> dict[str, Any] | None:
    adaptation = request.style_adaptation
    if adaptation is None:
        return None
    references: list[dict[str, str]] = []
    for index, reference in enumerate(adaptation.references, start=1):
        path = Path(reference.path).expanduser()
        if not path.is_file():
            raise MusicCapabilityError(
                "MUSIC_STYLE_REFERENCE_MISSING", f"style reference {index} is not readable: {path}",
                "Restore the authorized reference bytes; Wangp will not fetch source material.",
                metadata={"reference_index": index},
            )
        actual = file_sha256(path)
        if actual != reference.sha256:
            raise MusicCapabilityError(
                "MUSIC_STYLE_REFERENCE_UNUSABLE",
                f"style reference {index} hash mismatch: expected {reference.sha256}, got {actual}",
                "Restore the exact authorized reference bytes.",
                metadata={"reference_index": index, "expected": reference.sha256, "actual": actual},
            )
        references.append({"path": str(path), "sha256": actual, "source": reference.source, "rights": reference.rights})
    before = Path(adaptation.comparison.before.path).expanduser()
    if not before.is_file() or file_sha256(before) != adaptation.comparison.before.sha256:
        raise MusicCapabilityError(
            "MUSIC_STYLE_BASELINE_MISSING", f"comparison before-audio is missing or hash-mismatched: {before}",
            "Restore the exact authorized baseline audio and hash.",
        )
    after = Path(adaptation.comparison.after_path_planned).expanduser()
    if after.exists():
        raise MusicCapabilityError(
            "MUSIC_STYLE_OUTPUT_ALREADY_PRESENT", f"planned after-audio already exists: {after}",
            "Choose a new output path; planning must not claim or overwrite existing audio.",
        )
    return {
        "mode": "style_adaptation",
        "execution_status": "planned",
        "training_executed": False,
        "references": references,
        "comparison": {
            "mode": adaptation.comparison.mode,
            "before": {"path": str(before), "sha256": adaptation.comparison.before.sha256, "audio_claimed": False},
            "after_planned": {"path": str(after), "sha256": None, "audio_claimed": False},
            "audible_ab_artifact": "planned",
            "aesthetic_verdict": None,
        },
        "command_planned": adaptation.command_planned,
    }


def compile_music_request(request: MusicCapabilityRequest) -> CompiledMusicPlan:
    """Validate all local inputs before creating a plan or durable record."""

    score = normalize_score(request)
    score_hash = backend_settings(request, score_abc=score)["score_sha256"]
    style = _style_payload(request)
    cursor = 0.0
    sections: list[dict[str, Any]] = []
    for index, section in enumerate(request.sections, start=1):
        end = cursor + section.duration_s
        sections.append({
            "index": index, "name": section.name, "start_s": round(cursor, 6),
            "end_s": round(end, 6), "duration_s": section.duration_s,
            "chords": list(section.chords), "melody_abc": section.melody_abc,
        })
        cursor = end
    settings = backend_settings(request, score_abc=score)
    tracks: list[dict[str, Any]] = []
    for section in sections:
        tracks.append({
            "track_index": section["index"], "kind": "music_plan_record", "status": "planned",
            "audio": None, "quality_verdict": None, "operation": request.mode.value,
            "backend": {
                "id": request.model.family.value, "preset": request.model.preset.value,
                "model_type": settings["model_type"], "sha256": request.model.sha256,
                "license": request.model.license, "source": request.model.source,
                "usage_constraint": request.model.usage_constraint,
                "vram_profile": request.model.vram_profile, "execution_status": "planned",
            },
            "score": {"abc": score, "sha256": score_hash, "format": "abc"},
            "section": section, "arrangement": sections,
            "format": {
                "sample_rate_hz": request.output_format.sample_rate_hz,
                "channels": request.output_format.channels,
                "measurement_status": "not verified - requires authorized host run",
            },
            "style_adaptation": style, "recipe": {
                "schema_version": "wangp-dspy.music-recipe-input/v1",
                "request": request.model_dump(mode="json"),
            },
            "backend_settings": settings, "backend_settings_sha256": canonical_sha256(settings),
            "score_settings_sha256": score_hash, "queue_submitted": False,
            "host_contact": False, "plan_only": True, "executable": False,
        })
    return CompiledMusicPlan({
        "schema_version": PLAN_SCHEMA_VERSION, "request_sha256": request_digest(request),
        "capability_status": "planned", "operation": request.mode.value,
        "model": request.model.model_dump(mode="json"), "track_count": len(tracks),
        "duration_s": request.duration_s, "sections": sections, "score_abc": score,
        "score_sha256": score_hash, "tracks": tracks, "summary": {
            "gpu_work": False, "training_executed": False, "audio_created": False,
            "queue_submitted": False, "host_contact": False,
        },
    })


def write_score_artifact(plan: Mapping[str, Any], destination: str | Path) -> Path:
    path = Path(destination).expanduser().resolve()
    if path.exists():
        raise MusicCapabilityError(
            "MUSIC_SCORE_OUTPUT_EXISTS", f"score artifact already exists: {path}",
            "Choose a new deterministic .abc output path.",
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(plan["score_abc"], encoding="utf-8")
    return path


def enqueue_music_plan(plan: Mapping[str, Any], database: str | Path) -> list[str]:
    """Persist immutable plan records outside the executable jobs table."""

    destination = Path(database).expanduser().resolve()
    if destination.exists():
        raise MusicCapabilityError(
            "MUSIC_QUEUE_EXISTS", f"queue database already exists: {destination}",
            "Select a new database path for this no-GPU plan.",
        )
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = destination.parent / f".{destination.name}.{os.urandom(8).hex()}.tmp"
    ids: list[str] = []
    connection: sqlite3.Connection | None = None
    try:
        connection = sqlite3.connect(staging)
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute(
            "CREATE TABLE music_plan_records (record_id TEXT PRIMARY KEY, plan_ref TEXT NOT NULL, "
            "track_index INTEGER NOT NULL, record TEXT NOT NULL, created_at REAL NOT NULL)"
        )
        connection.execute(
            "CREATE TRIGGER music_plan_records_immutable_update BEFORE UPDATE ON music_plan_records "
            "BEGIN SELECT RAISE(ABORT, 'music plan records are immutable'); END"
        )
        connection.execute(
            "CREATE TRIGGER music_plan_records_immutable_delete BEFORE DELETE ON music_plan_records "
            "BEGIN SELECT RAISE(ABORT, 'music plan records are immutable'); END"
        )
        for track in plan["tracks"]:
            record_id = f"music-plan-{int(time.time() * 1000)}-{os.urandom(4).hex()}"
            connection.execute(
                "INSERT INTO music_plan_records VALUES (?,?,?,?,?)",
                (record_id, str(plan["request_sha256"]), int(track["track_index"]),
                 json.dumps(track, sort_keys=True), time.time()),
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


def _reconstruct(record: Mapping[str, Any]) -> tuple[dict[str, Any], str]:
    request = MusicCapabilityRequest.model_validate(record["recipe"]["request"])
    score = normalize_score(request)
    settings = backend_settings(request, score_abc=score)
    return settings, score


def reconstruct_music_database(database: str | Path) -> list[dict[str, Any]]:
    path = Path(database).expanduser().resolve()
    if not path.is_file():
        raise MusicCapabilityError(
            "MUSIC_RECONSTRUCTION_DATABASE_MISSING", f"plan database does not exist: {path}",
            "Pass a SQLite database emitted by wgp music compile.",
            next_command="wgp music compare --db <plan.db> --json",
        )
    connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if "music_plan_records" not in tables:
            raise MusicCapabilityError(
                "MUSIC_RECONSTRUCTION_RECORDS_MISSING", f"database {path} has no music plan records",
                "Use a database emitted by wgp music compile.",
            )
        rows = connection.execute(
            "SELECT record_id, record FROM music_plan_records ORDER BY track_index, created_at, record_id"
        ).fetchall()
    finally:
        connection.close()
    if not rows:
        raise MusicCapabilityError(
            "MUSIC_RECONSTRUCTION_RECORDS_MISSING", f"database {path} contains zero music plan records",
            "Compile a nonempty music plan; an empty reconstruction is not success.",
        )
    results: list[dict[str, Any]] = []
    for record_id, raw in rows:
        try:
            record = json.loads(raw)
            if record.get("kind") != "music_plan_record":
                raise ValueError(f"unexpected kind {record.get('kind')!r}")
            settings, score = _reconstruct(record)
        except Exception as exc:
            raise MusicCapabilityError(
                "MUSIC_RECONSTRUCTION_RECORD_INVALID",
                f"plan record {record_id} cannot be reconstructed: {exc}",
                "Regenerate the no-GPU music plan; do not edit immutable records.",
                metadata={"record_id": record_id},
            ) from exc
        settings_match = canonical_sha256(settings) == record["backend_settings_sha256"]
        score_hash = record["score"]["sha256"]
        score_match = settings["score_sha256"] == score_hash
        results.append({
            "record_id": record_id, "track_index": record["track_index"],
            "recorded_settings_sha256": record["backend_settings_sha256"],
            "reconstructed_settings_sha256": canonical_sha256(settings),
            "recorded_score_sha256": score_hash, "reconstructed_score_sha256": settings["score_sha256"],
            "match": settings_match and score_match,
            "hidden_mutation": not (settings_match and score_match),
        })
    return results


__all__ = [
    "CompiledMusicPlan", "PLAN_SCHEMA_VERSION", "compile_music_request", "enqueue_music_plan",
    "normalize_score", "reconstruct_music_database", "write_score_artifact",
]
