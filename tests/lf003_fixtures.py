"""Validated portable evidence fixtures for the LF003/AV suites."""

from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Mapping


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "tests/fixtures/lf003-v3-evidence.json"
SCHEMA = "wangp-dspy.lf003-v3-evidence-fixtures/v1"


class FixtureVerificationError(AssertionError):
    """Raised when portable evidence bytes are absent or altered."""


@dataclass(frozen=True)
class LF003Fixture:
    key: str
    path: Path
    size_bytes: int
    sha256: str


@dataclass(frozen=True)
class LF003FixtureSet:
    jobs_db_source_root: str
    jobs_db_job_id: str
    artifacts: dict[str, LF003Fixture]

    def __getitem__(self, key: str) -> LF003Fixture:
        return self.artifacts[key]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _load_manifest(manifest_path: Path) -> dict:
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FixtureVerificationError(
            f"LF003 fixture manifest unreadable: {manifest_path}: {exc}"
        ) from exc
    if not isinstance(payload, Mapping) or payload.get("schema") != SCHEMA:
        raise FixtureVerificationError(
            f"LF003 fixture manifest has unexpected schema: {manifest_path}")
    return dict(payload)


def verify_lf003_fixtures(
        *, manifest_path: Path = MANIFEST_PATH) -> LF003FixtureSet:
    """Verify every declared evidence artifact before tests consume it."""
    payload = _load_manifest(manifest_path)
    source_root = payload.get("jobs_db_source_root")
    job_id = payload.get("jobs_db_job_id")
    if not isinstance(source_root, str) or not source_root.strip():
        raise FixtureVerificationError("jobs_db_source_root must be nonempty")
    if not isinstance(job_id, str) or not job_id.strip():
        raise FixtureVerificationError("jobs_db_job_id must be nonempty")
    entries = payload.get("artifacts")
    if not isinstance(entries, list) or not entries:
        raise FixtureVerificationError("LF003 fixture manifest is empty")

    artifacts: dict[str, LF003Fixture] = {}
    seen_paths: set[Path] = set()
    for index, entry in enumerate(entries):
        if not isinstance(entry, Mapping):
            raise FixtureVerificationError(
                f"artifacts[{index}] must be an object")
        key = entry.get("key")
        relative = entry.get("path")
        expected_size = entry.get("size_bytes")
        expected_hash = entry.get("sha256")
        if (not isinstance(key, str) or not key.strip()
                or key in artifacts):
            raise FixtureVerificationError(
                f"artifacts[{index}].key must be unique and nonempty")
        if (not isinstance(relative, str) or not relative.strip()
                or PurePosixPath(relative).is_absolute()
                or ".." in PurePosixPath(relative).parts):
            raise FixtureVerificationError(
                f"{key}: manifest path must be relative to the repository")
        if (isinstance(expected_size, bool)
                or not isinstance(expected_size, int)
                or expected_size < 0):
            raise FixtureVerificationError(
                f"{key}: size_bytes must be a nonnegative integer")
        if (not isinstance(expected_hash, str)
                or len(expected_hash) != 64
                or any(char not in "0123456789abcdef"
                       for char in expected_hash)):
            raise FixtureVerificationError(
                f"{key}: sha256 must be a lowercase hexadecimal digest")

        path = ROOT / Path(*PurePosixPath(relative).parts)
        try:
            resolved = path.resolve(strict=True)
        except OSError as exc:
            raise FixtureVerificationError(
                f"{key}: LF003 fixture is missing: {path}") from exc
        if not resolved.is_relative_to(ROOT.resolve()) or not resolved.is_file():
            raise FixtureVerificationError(
                f"{key}: LF003 fixture is not a repository file: {path}")
        if resolved in seen_paths:
            raise FixtureVerificationError(
                f"{key}: fixture path is declared more than once: {relative}")
        seen_paths.add(resolved)
        try:
            actual_size = resolved.stat().st_size
        except OSError as exc:
            raise FixtureVerificationError(
                f"{key}: LF003 fixture is unreadable: {resolved}") from exc
        if actual_size != expected_size:
            raise FixtureVerificationError(
                f"{key}: LF003 fixture size mismatch: expected "
                f"{expected_size}, got {actual_size}")
        try:
            actual_hash = _sha256(resolved)
        except OSError as exc:
            raise FixtureVerificationError(
                f"{key}: LF003 fixture is unreadable: {resolved}") from exc
        if actual_hash != expected_hash:
            raise FixtureVerificationError(
                f"{key}: LF003 fixture SHA-256 mismatch: expected "
                f"{expected_hash}, got {actual_hash}")
        artifacts[key] = LF003Fixture(
            key=key, path=resolved, size_bytes=actual_size,
            sha256=actual_hash)

    return LF003FixtureSet(
        jobs_db_source_root=source_root.rstrip("/"),
        jobs_db_job_id=job_id,
        artifacts=artifacts,
    )


def _rebase_paths(value, old_root: str, new_root: str):
    if isinstance(value, str):
        return value.replace(old_root + "/", new_root + "/")
    if isinstance(value, list):
        return [_rebase_paths(item, old_root, new_root) for item in value]
    if isinstance(value, dict):
        return {
            key: _rebase_paths(item, old_root, new_root)
            for key, item in value.items()
        }
    return value


def stage_lf003_jobs_db(destination: Path, *,
                        fixtures: LF003FixtureSet) -> dict:
    """Copy the evidence DB and deterministically rebase embedded roots."""
    source = fixtures["jobs-db"].path
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
    old_root = fixtures.jobs_db_source_root
    new_root = str(ROOT)
    try:
        with sqlite3.connect(destination) as db:
            row = db.execute(
                "SELECT clips FROM jobs WHERE job_id=?",
                (fixtures.jobs_db_job_id,),
            ).fetchone()
            if row is None:
                raise FixtureVerificationError(
                    "LF003 jobs DB fixture does not contain recorded job "
                    f"{fixtures.jobs_db_job_id!r}")
            clips = _rebase_paths(json.loads(row[0]), old_root, new_root)
            db.execute(
                "UPDATE jobs SET clips=? WHERE job_id=?",
                (json.dumps(clips), fixtures.jobs_db_job_id),
            )
    except (OSError, sqlite3.Error, json.JSONDecodeError) as exc:
        raise FixtureVerificationError(
            f"LF003 jobs DB could not be staged portably: {exc}") from exc
    return {
        "jobs_db": str(destination),
        "job_id": fixtures.jobs_db_job_id,
    }
