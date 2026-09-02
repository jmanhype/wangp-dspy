"""Durable job queue: SQLite (stdlib sqlite3, WAL).

One trusted 3090 — no broker, no worker pool. Job records persist
per-chain-clip (clip_index matches services/chain plan clip ids);
every artifact claim carries a PATH (log, mp4, qc_verdict) — no
status-only fields. Relaunch skips clips already `done`.
"""
from __future__ import annotations

import json
import os
import sqlite3
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence

# ACTIVE_STATES: a job in one of these is (normally) owned by a live
# process; a crash mid-phase orphans it there (reviewer B2).
ACTIVE_STATES = ("preflight", "rendering", "qc")


def _pid_alive(pid: Optional[int]) -> bool:
    if not pid or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True  # exists, owned by someone else
    except OSError:
        return False
    return True


from services.jobs.states import ALLOWED_TRANSITIONS, InvalidTransition


class JobNotFoundError(KeyError):
    """No job with that id in the queue."""


@dataclass
class JobRecord:
    job_id: str
    state: str = "pending"
    plan_ref: str = ""
    clips: List[Dict] = field(default_factory=list)
    failure_count: int = 0
    failure_class: Optional[str] = None
    failure_detail: Optional[str] = None
    created_at: float = field(default_factory=time.time)

    def to_json(self) -> Dict:
        return {
            "job_id": self.job_id, "state": self.state,
            "plan_ref": self.plan_ref, "clips": self.clips,
            "failure_count": self.failure_count,
            "failure_class": self.failure_class,
            "failure_detail": self.failure_detail,
            "created_at": self.created_at,
        }


def _check_clip_artifacts(status: str, log, mp4, qc_verdict) -> None:
    """Design constraint: an artifact CLAIM must carry a path.

    A clip whose status claims rendering happened must have nonempty
    log/mp4 paths; a claimed QC verdict must carry its own path.
    Status-only records are rejected.
    """
    if status in ("rendered", "rendered_pending_qc", "qc", "done",
                  "failed"):
        if not (log and str(log).strip()):
            raise ValueError(
                f"clip status {status!r} claims render evidence but "
                "carries no log path — status-only fields are forbidden")
        if not (mp4 and str(mp4).strip()):
            raise ValueError(
                f"clip status {status!r} claims render evidence but "
                "carries no mp4 path — status-only fields are forbidden")
        if qc_verdict is not None and status in ("qc", "done"):
            if not isinstance(qc_verdict, dict) or not str(
                    qc_verdict.get("path", "")).strip():
                raise ValueError(
                    "qc_verdict claim must carry its artifact path "
                    "({'verdict': ..., 'path': ...})")


class JobQueue:
    """SQLite-backed durable queue (WAL; stdlib only)."""

    def __init__(self, db_path):
        self.db_path = str(db_path)
        self._db = sqlite3.connect(self.db_path)
        self._db.row_factory = sqlite3.Row
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.execute(
            "CREATE TABLE IF NOT EXISTS jobs ("
            " job_id TEXT PRIMARY KEY,"
            " state TEXT NOT NULL,"
            " plan_ref TEXT NOT NULL,"
            " clips TEXT NOT NULL,"
            " failure_count INTEGER NOT NULL DEFAULT 0,"
            " failure_class TEXT,"
            " failure_detail TEXT,"
            " created_at REAL NOT NULL)")
        self._migrate()
        self._db.commit()

    def _migrate(self) -> None:
        """Stale-active recovery bookkeeping (reviewer B2).

        owner_pid: pid of the process driving an active-state job;
        last_heartbeat: wall-clock of its last progress write. A job in
        an active state whose owner is dead (or whose heartbeat is
        older than the staleness timeout) is orphaned crash debris.
        """
        cols = {r["name"] for r in self._db.execute("PRAGMA table_info(jobs)")}
        if "owner_pid" not in cols:
            self._db.execute(
                "ALTER TABLE jobs ADD COLUMN owner_pid INTEGER")
        if "last_heartbeat" not in cols:
            self._db.execute(
                "ALTER TABLE jobs ADD COLUMN last_heartbeat REAL")

    # -- lifecycle --------------------------------------------------
    def close(self) -> None:
        self._db.close()

    # -- writes -----------------------------------------------------
    def submit(self, *, plan_ref: str, clips: Sequence[Dict]) -> str:
        if not plan_ref or not str(plan_ref).strip():
            raise ValueError("plan_ref must be nonempty")
        if not clips:
            raise ValueError("a job needs at least one clip")
        job_id = f"job-{int(time.time() * 1000)}-{os.urandom(4).hex()}"
        for c in clips:
            _check_clip_artifacts(c.get("status", "pending"),
                                  c.get("log"), c.get("mp4"),
                                  c.get("qc_verdict"))
        self._db.execute(
            "INSERT INTO jobs (job_id, state, plan_ref, clips, "
            "failure_count, failure_class, failure_detail, created_at) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (job_id, "pending", plan_ref, json.dumps(list(clips)),
             0, None, None, time.time()))
        self._db.commit()
        return job_id

    def set_state(self, job_id: str, state: str) -> None:
        rec = self.get(job_id)
        if state not in ALLOWED_TRANSITIONS.get(rec.state, frozenset()):
            raise InvalidTransition(
                f"illegal job state transition {rec.state!r} -> "
                f"{state!r}")
        self._db.execute("UPDATE jobs SET state=? WHERE job_id=?",
                         (state, job_id))
        self._db.commit()

    def claim_active(self, job_id: str, *, owner_pid: int) -> None:
        """Mark this process as the live owner of an active-state job."""
        self._db.execute(
            "UPDATE jobs SET owner_pid=?, last_heartbeat=? "
            "WHERE job_id=?",
            (int(owner_pid), time.time(), job_id))
        self._db.commit()

    def heartbeat(self, job_id: str) -> None:
        self._db.execute(
            "UPDATE jobs SET last_heartbeat=? WHERE job_id=?",
            (time.time(), job_id))
        self._db.commit()

    def clear_ownership(self, job_id: str) -> None:
        self._db.execute(
            "UPDATE jobs SET owner_pid=NULL, last_heartbeat=NULL "
            "WHERE job_id=?", (job_id,))
        self._db.commit()

    def update_clip(self, job_id: str, clip_index: int, *,
                    status: str, log, mp4, qc_verdict,
                    lane=None) -> None:
        _check_clip_artifacts(status, log, mp4, qc_verdict)
        rec = self.get(job_id)
        clips = rec.clips
        for c in clips:
            if c["clip_index"] == clip_index:
                c.update({"status": status, "log": log, "mp4": mp4,
                          "qc_verdict": qc_verdict})
                # which lane rendered this clip (fl2va | ref2va);
                # None keeps legacy records unchanged
                if lane is not None:
                    c["lane"] = lane
                break
        else:
            raise JobNotFoundError(
                f"clip {clip_index} not in job {job_id}")
        self._db.execute("UPDATE jobs SET clips=? WHERE job_id=?",
                         (json.dumps(clips), job_id))
        self._db.commit()

    def record_failure(self, job_id: str, *, failure_class: str) -> None:
        rec = self.get(job_id)
        count = (rec.failure_count + 1
                 if rec.failure_class == failure_class else 1)
        self._db.execute(
            "UPDATE jobs SET failure_count=?, failure_class=? "
            "WHERE job_id=?", (count, failure_class, job_id))
        self._db.commit()

    def set_failure_detail(self, job_id: str, detail: str) -> None:
        self._db.execute(
            "UPDATE jobs SET failure_detail=? WHERE job_id=?",
            (detail, job_id))
        self._db.commit()

    # -- reads ------------------------------------------------------
    def get(self, job_id: str) -> JobRecord:
        row = self._db.execute(
            "SELECT * FROM jobs WHERE job_id=?", (job_id,)).fetchone()
        if row is None:
            raise JobNotFoundError(job_id)
        return JobRecord(
            job_id=row["job_id"], state=row["state"],
            plan_ref=row["plan_ref"],
            clips=json.loads(row["clips"]),
            failure_count=row["failure_count"],
            failure_class=row["failure_class"],
            failure_detail=row["failure_detail"],
            created_at=row["created_at"])

    def next_pending(self) -> Optional[str]:
        row = self._db.execute(
            "SELECT job_id FROM jobs WHERE state='pending' "
            "ORDER BY created_at LIMIT 1").fetchone()
        return row["job_id"] if row else None

    # -- stale-active recovery (reviewer B2) --------------------------
    def recover_stale_active(self, *, staleness_s: float = 600.0,
                             pid_is_alive=None) -> List[str]:
        """Requeue orphaned active-state jobs (B2).

        A crash mid-render leaves a job stuck in 'rendering' (or
        'preflight'/'qc') with no live owner; _pick_job() only selects
        pending/rendered_pending_qc, so the job is orphaned forever.
        Recovery: an active-state job whose owner_pid is not a live
        process AND whose last_heartbeat is older than staleness_s
        (or absent — legacy rows) transitions *->pending and re-enters
        the queue. Per-clip checkpoints are untouched, so the resume
        does NOT redo clips already `done`/`rendered`.

        A job with a LIVE owner pid or a FRESH heartbeat is left alone.
        Returns the recovered job ids.
        """
        alive = pid_is_alive or _pid_alive
        now = time.time()
        recovered: List[str] = []
        for state in ACTIVE_STATES:
            rows = self._db.execute(
                "SELECT job_id, owner_pid, last_heartbeat FROM jobs "
                "WHERE state=?", (state,)).fetchall()
            for row in rows:
                jid = row["job_id"]
                pid = row["owner_pid"]
                hb = row["last_heartbeat"]
                owner_live = bool(pid) and alive(pid)
                hb_fresh = (hb is not None
                            and (now - float(hb)) < staleness_s)
                if owner_live or hb_fresh:
                    continue  # someone owns this job — leave it alone
                self.set_state(jid, "pending")
                self._db.execute(
                    "UPDATE jobs SET owner_pid=NULL, "
                    "last_heartbeat=NULL WHERE job_id=?", (jid,))
                self._db.commit()
                recovered.append(jid)
        return recovered

    def list_state(self, state: str) -> List[str]:
        rows = self._db.execute(
            "SELECT job_id FROM jobs WHERE state=? ORDER BY created_at",
            (state,)).fetchall()
        return [r["job_id"] for r in rows]

    def dead_letter_due(self, job_id: str, *, max_failures: int = 3) -> bool:
        rec = self.get(job_id)
        return (rec.failure_class is not None
                and rec.failure_count >= max_failures)


__all__ = ["JobQueue", "JobRecord", "JobNotFoundError"]
