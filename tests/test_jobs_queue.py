"""services/jobs/queue — durable SQLite (WAL) job queue."""
import json
import os
import sqlite3

import pytest

from services.jobs.queue import JobQueue, JobNotFoundError, JobRecord
from services.jobs.states import InvalidTransition


@pytest.fixture
def q(tmp_path):
    queue = JobQueue(tmp_path / "jobs.db")
    yield queue
    queue.close()


def _clip(job_id="job-1", clip_index=1, status="pending"):
    return {"clip_index": clip_index, "status": status,
            "log": None, "mp4": None, "qc_verdict": None}


def test_creates_db_with_wal(q, tmp_path):
    db = tmp_path / "jobs.db"
    assert db.exists()
    mode = sqlite3.connect(db).execute(
        "PRAGMA journal_mode").fetchone()[0]
    assert mode == "wal"


def test_submit_job_pending(q):
    jid = q.submit(plan_ref="plans/p1.json",
                   clips=[_clip(), _clip(job_id="job-1", clip_index=2)])
    rec = q.get(jid)
    assert rec.state == "pending"
    assert rec.plan_ref == "plans/p1.json"
    assert len(rec.clips) == 2
    assert rec.failure_count == 0


def test_submit_rejects_job_without_clips(q):
    with pytest.raises(ValueError):
        q.submit(plan_ref="p.json", clips=[])


def test_clip_artifact_claims_require_paths(q):
    # every artifact claim in job records must carry a path — no
    # status-only fields (design constraint).
    jid = q.submit(plan_ref="p.json",
                   clips=[{"clip_index": 1, "status": "pending",
                           "log": None, "mp4": None,
                           "qc_verdict": None}])
    with pytest.raises(ValueError):
        q.update_clip(jid, 1, status="rendered", log="render-ok",
                      mp4="", qc_verdict=None)
    with pytest.raises(ValueError):
        q.update_clip(jid, 1, status="done", log="l", mp4="m",
                      qc_verdict={"verdict": "KEEP"})  # no path


def test_state_transition_persisted_and_validated(q):
    jid = q.submit(plan_ref="p.json", clips=[_clip()])
    q.set_state(jid, "preflight")
    assert q.get(jid).state == "preflight"
    with pytest.raises(InvalidTransition):
        q.set_state(jid, "done")  # preflight -> done is illegal


def test_update_clip_records_artifact_paths(q):
    jid = q.submit(plan_ref="p.json", clips=[_clip()])
    q.update_clip(jid, 1, status="rendered",
                  log="renders/job-1/clip1/render.log",
                  mp4="renders/job-1/clip1/out.mp4",
                  qc_verdict=None)
    clip = q.get(jid).clips[0]
    assert clip["mp4"].endswith("out.mp4")
    assert clip["log"].endswith("render.log")


def test_qc_verdict_carries_path(q):
    jid = q.submit(plan_ref="p.json", clips=[_clip()])
    q.update_clip(jid, 1, status="qc",
                  log="renders/job-1/clip1/render.log",
                  mp4="renders/job-1/clip1/out.mp4",
                  qc_verdict={"verdict": "KEEP",
                              "path": "qc/job-1/clip1.json"})
    clip = q.get(jid).clips[0]
    assert clip["qc_verdict"]["path"].endswith(".json")


def test_failure_class_counting_and_dead_letter(q):
    jid = q.submit(plan_ref="p.json", clips=[_clip()])
    for _ in range(3):
        q.record_failure(jid, failure_class="transient_render")
    rec = q.get(jid)
    assert rec.failure_count == 3
    assert rec.failure_class == "transient_render"
    # dead-letter after N=3 failures of the same class
    assert q.dead_letter_due(jid, max_failures=3)
    q.record_failure(jid, failure_class="other_class")
    assert not q.dead_letter_due(jid, max_failures=3)  # class reset


def test_next_pending_returns_oldest_pending(q):
    a = q.submit(plan_ref="a.json", clips=[_clip("job-a")])
    b = q.submit(plan_ref="b.json", clips=[_clip("job-b")])
    q.set_state(a, "preflight")
    assert q.next_pending() == b


def test_done_clips_skipped_on_reenqueue(q):
    # checkpoint resume: relaunch skips done clips (--skip-done)
    jid = q.submit(plan_ref="p.json",
                   clips=[_clip(clip_index=1), _clip(clip_index=2)])
    q.update_clip(jid, 1, status="done",
                  log="l1", mp4="m1",
                  qc_verdict={"verdict": "KEEP", "path": "q1"})
    pending = [c for c in q.get(jid).clips
               if c["status"] != "done"]
    assert [c["clip_index"] for c in pending] == [2]


def test_persistence_across_reopen(tmp_path):
    db = tmp_path / "jobs.db"
    jid = JobQueue(db).submit(plan_ref="p.json", clips=[_clip()])
    q1 = JobQueue(db)
    q1.set_state(jid, "preflight")
    q1.set_state(jid, "rendering")
    q1.close()
    q2 = JobQueue(db)
    assert q2.get(jid).state == "rendering"
    q2.close()


def test_list_rendered_pending_qc(q):
    jid = q.submit(plan_ref="p.json", clips=[_clip()])
    q.set_state(jid, "preflight")
    q.set_state(jid, "rendering")
    q.set_state(jid, "rendered_pending_qc")
    assert q.list_state("rendered_pending_qc") == [jid]


def test_record_serializes_to_json_with_paths(q):
    jid = q.submit(plan_ref="p.json", clips=[_clip()])
    doc = q.get(jid).to_json()
    json.dumps(doc)  # round-trippable
    assert doc["plan_ref"] == "p.json"
