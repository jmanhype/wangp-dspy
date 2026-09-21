"""Read-only presentation helpers over the existing durable JobQueue."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import asdict, dataclass
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from scripts.run_jobs import dry_run_report
from services.jobs.queue import JobNotFoundError, JobQueue
from services.jobs.states import JOB_STATES


_HASH_KEYS = (("path", "sha256"), ("output_path", "output_sha256"), ("video_path", "video_sha256"), ("qc_evidence_path", "qc_evidence_sha256"))


@dataclass(frozen=True)
class QueueStatus:
    """A deterministic snapshot of queue state and immutable attempts."""

    db_path: str
    state_counts: dict[str, int]
    dry_run: dict[str, Any]
    jobs: list[dict[str, Any]]
    attempts: dict[str, list[dict[str, Any]]]

    def mapping(self) -> dict[str, Any]:
        return asdict(self)


def _failure_summary(record: Any) -> str:
    if not record.failure_class:
        return "none"
    return (
        f"{record.failure_class} x{record.failure_count}: "
        f"{record.failure_detail or 'no detail recorded'}"
    )


def _job_mapping(record: Any) -> dict[str, Any]:
    return {
        "job_id": record.job_id,
        "state": record.state,
        "plan_ref": record.plan_ref,
        "failure_summary": _failure_summary(record),
        "retryable": bool(record.retryable),
        "created_at": record.created_at,
        "clips": record.clips,
    }


def _selected_ids(queue: JobQueue, job_id: str | None) -> list[str]:
    if job_id is not None:
        return [job_id]
    return [identifier for state in JOB_STATES for identifier in queue.list_state(state)]


class _ReadOnlyJobQueue(JobQueue):
    """A genuinely read-only adapter over the public JobQueue read APIs."""

    def __init__(self, db_path: str | Path):
        self.db_path = str(db_path)
        path = Path(db_path).expanduser().resolve()
        self._db = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)
        self._db.row_factory = sqlite3.Row
        self._db.execute("PRAGMA query_only=ON")

    def attempt_history(self, job_id: str) -> list[dict[str, Any]]:
        tables = {
            row["name"]
            for row in self._db.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        if not {"job_attempts", "job_attempt_failures"}.issubset(tables):
            self.get(job_id)
            history: list[dict[str, Any]] = []
            return history
        return super().attempt_history(job_id)


@contextmanager
def _read_only_queue(db_path: str | Path):
    path = Path(db_path).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"queue database does not exist: {path}")
    queue = _ReadOnlyJobQueue(path)
    try:
        yield queue
    finally:
        queue.close()


def collect_status(
    db_path: str | Path, *, job_id: str | None = None
) -> QueueStatus:
    """Read durable queue state without journal, schema, or row mutations."""

    path = Path(db_path).expanduser().resolve()
    with _read_only_queue(path) as queue:
        counts = {state: len(queue.list_state(state)) for state in JOB_STATES}
        selected = _selected_ids(queue, job_id)
        records = [queue.get(identifier) for identifier in selected]
        jobs = [_job_mapping(record) for record in records]
        attempts = {
            identifier: queue.attempt_history(identifier)
            for identifier in selected
        }
        return QueueStatus(
            db_path=str(path),
            state_counts=counts,
            dry_run=dry_run_report(queue),
            jobs=jobs,
            attempts=attempts,
        )


def queue_evidence_paths(record: Any) -> list[str]:
    """Return artifact-bearing paths referenced by one job's clips."""

    direct = [str(clip[key]) for clip in record.clips for key in ("audio_guide", "image_start", "log", "mp4") if isinstance(clip.get(key), str) and clip[key].strip()]
    verdicts = [clip["qc_verdict"]["path"] for clip in record.clips if isinstance(clip.get("qc_verdict"), dict) and isinstance(clip["qc_verdict"].get("path"), str)]
    return direct + verdicts


def collect_queue_review(
    db_path: str | Path, *, job_id: str | None = None
) -> tuple[dict[str, Any], list[str]]:
    """Return durable job clips, failures, attempts, and evidence paths."""

    evidence: list[str] = []
    path = Path(db_path).expanduser().resolve()
    with _read_only_queue(path) as queue:
        status = collect_status(path, job_id=job_id)
        if job_id is not None and not status.jobs:
            raise JobNotFoundError(job_id)
        for identifier in [job_id] if job_id is not None else [
            job["job_id"] for job in status.jobs
        ]:
            evidence.extend(queue_evidence_paths(queue.get(identifier)))
    return status.mapping(), evidence


def render_status(status: QueueStatus) -> str:
    """Render queue counts and concise per-job summaries."""

    lines = [f"queue={status.db_path}"]
    lines.extend(
        f"{state}={count}" for state, count in status.state_counts.items()
    )
    for job in status.jobs:
        attempts = status.attempts[job["job_id"]]
        lines.append(
            f"{job['job_id']} state={job['state']} "
            f"attempts={len(attempts)} "
            f"retryable={str(job['retryable']).lower()} "
            f"failure={job['failure_summary']}"
        )
    return "\n".join(lines)


def render_queue_review(
    payload: dict[str, Any], evidence: list[str]
) -> str:
    """Render clips, failures, attempts, and referenced evidence paths."""

    lines = [f"queue={payload['db_path']}"]
    for job in payload["jobs"]:
        lines.append(
            f"{job['job_id']} state={job['state']} "
            f"failure={job['failure_summary']}"
        )
        for attempt in payload["attempts"][job["job_id"]]:
            reason = attempt["reopen_reason"] or attempt["attempt_reason"]
            lines.append(
                f"  attempt={attempt['attempt_no']} status={attempt['status']} "
                f"class={attempt['failure_class'] or 'none'} "
                f"detail={attempt['failure_detail'] or 'none'} "
                f"reason={reason or 'none'}"
            )
        for clip in job["clips"]:
            lines.append(
                f"  clip={clip.get('clip_index')} kind={clip.get('kind')} "
                f"mp4={clip.get('mp4', '')} log={clip.get('log', '')}"
            )
    if evidence:
        lines.append("evidence:")
        lines.extend(f"  {path}" for path in evidence)
    return "\n".join(lines)


def _provenance_pairs(value: Any) -> list[tuple[str, str]]:
    if isinstance(value, dict):
        direct = [(value[key], value[digest]) for key, digest in _HASH_KEYS if isinstance(value.get(key), str) and isinstance(value.get(digest), str)]
        return direct + [
            pair for child in value.values() for pair in _provenance_pairs(child)
        ]
    if isinstance(value, list):
        return [pair for child in value for pair in _provenance_pairs(child)]
    return list[tuple[str, str]]()


def _resolve_artifact(path: str, run: Path) -> Path:
    candidate = Path(path).expanduser()
    if candidate.is_file() or "datasets/" not in path:
        return candidate
    mapped = Path(__file__).resolve().parents[1] / "datasets" / path.split("datasets/", 1)[1]
    return mapped if mapped.is_file() else candidate


def review_run(run: str | Path) -> dict[str, Any]:
    bundle = Path(run).expanduser().resolve()
    if bundle.is_file() and bundle.name == "final-provenance.json":
        bundle = bundle.parent
    provenance = bundle / "final-provenance.json"
    if not bundle.is_dir():
        raise FileNotFoundError(f"run review bundle does not exist: {bundle}")
    if not provenance.is_file():
        raise FileNotFoundError(f"final-provenance.json is missing: {provenance}")
    checks: list[dict[str, str]] = []
    if provenance.is_file():
        try:
            payload = json.loads(provenance.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"cannot read final provenance {provenance}: {exc}") from exc
        for path, expected in _provenance_pairs(payload):
            artifact = _resolve_artifact(path, bundle)
            if not artifact.is_file():
                status, detail = "failed", "artifact is missing"
            else:
                artifact_digest = hashlib.sha256()
                with artifact.open("rb") as artifact_file:
                    for chunk in iter(lambda: artifact_file.read(1024 * 1024), b""):
                        artifact_digest.update(chunk)
                matches = artifact_digest.hexdigest() == expected
                status, detail = ("pass", "sha256 matches") if matches else (
                    "failed", "sha256 mismatch"
                )
            checks.append({
                "path": artifact.as_posix(),
                "expected_sha256": expected,
                "status": status,
                "detail": detail,
            })
    if not checks:
        raise ValueError(
            f"final provenance has no recognized path/sha256 pairs: {provenance}"
        )
    return {
        "run": bundle.as_posix(),
        "film": (bundle / "assembled.mp4").as_posix(),
        "probe": (bundle / "probe.json").as_posix(),
        "contact_sheets": [path.as_posix() for path in sorted(bundle.glob("review/*.contact_sheet.jpg"))],
        "provenance": provenance.as_posix(),
        "hash_checks": checks,
        "all_hashes_match": bool(checks)
        and all(item["status"] == "pass" for item in checks),
    }


def render_run_review(payload: dict[str, Any]) -> str:
    lines = [
        f"run={payload['run']}", f"film={payload['film']}",
        f"probe={payload['probe']}", f"provenance={payload['provenance']}",
    ]
    lines.extend(f"contact_sheet={path}" for path in payload["contact_sheets"])
    lines.append(
        f"hash_checks={len(payload['hash_checks'])} "
        f"passed={str(payload['all_hashes_match']).lower()}"
    )
    lines.extend(
        f"  {item['status']} {item['path']} {item['detail']}"
        for item in payload["hash_checks"]
    )
    return "\n".join(lines)


__all__ = [
    "QueueStatus",
    "collect_queue_review",
    "collect_status",
    "queue_evidence_paths",
    "render_run_review",
    "render_queue_review",
    "render_status",
    "review_run",
]
