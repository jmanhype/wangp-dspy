"""services/jobs/queue — durable SQLite (WAL) job queue."""
import json
import os
import sqlite3

import pytest

from services.jobs.queue import (JobQueue, JobNotFoundError, JobRecord,
                                 JobRetryError, effective_render_fingerprint)
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


def test_submit_rejects_orphaned_chain_placeholder(q):
    clip = _clip()
    clip.update({"kind": "ref2va_render",
                 "image_start": "chain://clip0001/last_frame",
                 "image_refs": ["chain://clip0001/last_frame", "face.png"]})
    with pytest.raises(ValueError, match="chain.*needs"):
        q.submit(plan_ref="p.json", clips=[clip])


def test_failed_render_fingerprint_requires_change_or_explicit_replay(q):
    base = {"clip_index": 1, "status": "pending", "log": None,
            "mp4": None, "qc_verdict": None,
            "kind": "ref2va_render", "prompt": "same prompt",
            "seed": 904, "image_start": "seed.png",
            "image_refs": ["seed.png", "silent.png"],
            "audio_guide": "turn.wav", "video_length": 56}
    first = q.submit(plan_ref="failed-run", clips=[dict(base)])
    q.set_state(first, "preflight")
    q.set_state(first, "rendering")
    q.set_state(first, "failed")
    assert q.get(first).clips[0]["render_fingerprint"] == (
        effective_render_fingerprint(base))

    with pytest.raises(ValueError, match="deterministic replay"):
        q.submit(plan_ref="fake-regen", clips=[dict(base)])

    changed = dict(base, seed=905)
    second = q.submit(plan_ref="real-regen", clips=[changed])
    assert q.get(second).clips[0]["render_fingerprint"] != (
        q.get(first).clips[0]["render_fingerprint"])

    explicit = dict(base, allow_deterministic_replay=True)
    third = q.submit(plan_ref="explicit-replay", clips=[explicit])
    assert q.get(third).clips[0]["allow_deterministic_replay"] is True


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


# -- stale-active recovery (reviewer B2 regression tests) --------------
def _orphan_rendering(q, *, hb=None, pid=None):
    jid = q.submit(plan_ref="p.json", clips=[_clip()])
    q.set_state(jid, "preflight")
    q.set_state(jid, "rendering")
    q._db.execute(
        "UPDATE jobs SET owner_pid=?, last_heartbeat=? WHERE job_id=?",
        (pid, hb, jid))
    q._db.commit()
    return jid


def test_stale_rendering_job_is_requeued(q):
    # crashed mid-render: dead pid, no heartbeat -> back to pending
    jid = _orphan_rendering(q, hb=None, pid=999999)
    alive = {999999: False}
    assert q.recover_stale_active(staleness_s=600.0,
                                  pid_is_alive=alive.get) == [jid]
    assert q.get(jid).state == "pending"


def test_stale_heartbeat_without_pid_is_requeued(q):
    # legacy row: no owner_pid recorded, heartbeat older than timeout
    jid = _orphan_rendering(q, hb=0.0, pid=None)
    assert q.recover_stale_active(staleness_s=600.0) == [jid]
    assert q.get(jid).state == "pending"
    rec = q.get(jid)
    row = q._db.execute(
        "SELECT owner_pid, last_heartbeat FROM jobs WHERE job_id=?",
        (jid,)).fetchone()
    assert row["owner_pid"] is None and row["last_heartbeat"] is None


def test_live_owner_rendering_job_is_not_picked(q):
    # a LIVE owner pid holds the job — recovery must leave it alone
    jid = _orphan_rendering(q, hb=None, pid=4242)
    alive = {4242: True}
    assert q.recover_stale_active(staleness_s=600.0,
                                  pid_is_alive=alive.get) == []
    assert q.get(jid).state == "rendering"


def test_fresh_heartbeat_rendering_job_is_not_picked(q):
    # fresh heartbeat even with dead pid: worker may be between
    # heartbeats with an unreadable pid — leave it alone
    import time as _t
    jid = _orphan_rendering(q, hb=_t.time(), pid=999999)
    alive = {999999: False}
    assert q.recover_stale_active(staleness_s=600.0,
                                  pid_is_alive=alive.get) == []
    assert q.get(jid).state == "rendering"


def test_recovered_job_requeues_with_clip_checkpoints(q):
    # done clips survive recovery: no re-render of finished work
    jid = q.submit(plan_ref="p.json",
                   clips=[_clip(clip_index=1), _clip(clip_index=2)])
    q.set_state(jid, "preflight")
    q.set_state(jid, "rendering")
    q.update_clip(jid, 1, status="done",
                  log="l1", mp4="m1",
                  qc_verdict={"verdict": "KEEP", "path": "q1"})
    q.recover_stale_active(staleness_s=600.0,
                           pid_is_alive=lambda p: False)
    rec = q.get(jid)
    assert rec.state == "pending"
    assert [c["clip_index"] for c in rec.clips
            if c["status"] == "done"] == [1]
    assert q.next_pending() == jid  # immediately re-pickable


def _failed_job(q):
    jid = q.submit(plan_ref="p.json", clips=[_clip()])
    q.set_state(jid, "preflight")
    q.set_state(jid, "rendering")
    q.record_failure(jid, failure_class="render_error")
    q.set_failure_detail(jid, "containment violation")
    q.set_state(jid, "failed")
    return jid


def test_requeue_failed_preserves_append_only_attempt_history(q):
    jid = _failed_job(q)
    first = q.attempt_history(jid)
    assert first == []  # pre-Finding-21 failure has no history yet

    attempt_id = q.requeue_failed(jid)
    assert q.get(jid).state == "pending"
    history = q.attempt_history(jid)
    assert len(history) == 2
    assert history[0]["status"] == "failed"
    assert history[0]["failure_detail"] == "containment violation"
    assert history[1]["status"] == "queued"
    assert history[1]["attempt_id"] == attempt_id
    assert history[1]["parent_attempt_id"] == history[0]["attempt_id"]


def test_same_failure_after_requeue_disables_retry_loop(q):
    jid = _failed_job(q)
    q.requeue_failed(jid)
    q.record_failure(jid, failure_class="render_error")
    q.set_failure_detail(jid, "containment violation")
    assert q.record_attempt_failure(
        jid, failure_class="render_error",
        failure_detail="containment violation") is True
    q.set_state(jid, "preflight")
    q.set_state(jid, "rendering")
    q.set_state(jid, "failed")
    assert q.get(jid).retryable is False
    with pytest.raises(JobRetryError, match="repeated"):
        q.requeue_failed(jid)
    history = q.attempt_history(jid)
    assert [h["status"] for h in history] == ["failed", "failed"]
    assert [h["failure_detail"] for h in history] == [
        "containment violation", "containment violation"]


def test_dead_letter_reopen_is_explicit_and_audited(q):
    jid = _failed_job(q)
    q.record_failure(jid, failure_class="render_error")
    q.record_failure(jid, failure_class="render_error")
    q.set_state(jid, "dead_letter")
    with pytest.raises(InvalidTransition):
        q.set_state(jid, "pending")

    attempt_id = q.reopen_dead_letter(
        jid, reason="operator reopened after output-discovery fix")
    assert q.get(jid).state == "pending"
    history = q.attempt_history(jid)
    assert history[-1]["attempt_id"] == attempt_id
    assert history[-1]["status"] == "reopened"
    assert history[-1]["reopen_reason"] == (
        "operator reopened after output-discovery fix")


def test_dead_letter_reopen_requires_reason(q):
    jid = _failed_job(q)
    q.record_failure(jid, failure_class="render_error")
    q.record_failure(jid, failure_class="render_error")
    q.set_state(jid, "dead_letter")
    with pytest.raises(JobRetryError, match="reason"):
        q.reopen_dead_letter(jid, reason=" ")
