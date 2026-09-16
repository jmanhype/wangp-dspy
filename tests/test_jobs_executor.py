"""Executor tests — orchestration over a stubbed queue/preflight/render."""
import pytest

from services.jobs.executor import JobExecutor, RenderOutcome
from services.jobs.queue import JobQueue
from qc.audio_critic.ref2va_stage import Ref2VAQCStageError
from services.jobs.states import InvalidTransition


class FakeQueue:
    def __init__(self, jobs=None):
        self.jobs = jobs or {}
        self.state_calls = []

    def get(self, jid):
        return self.jobs[jid]

    def set_state(self, jid, state):
        from services.jobs.states import transition
        job = self.jobs[jid]
        job.state = transition(job.state, state)
        self.state_calls.append((jid, state))

    def update_clip(self, jid, clip_index, **kw):
        for c in self.jobs[jid].clips:
            if c["clip_index"] == clip_index:
                c.update(kw)

    def record_failure(self, jid, failure_class):
        j = self.jobs[jid]
        j.failure_count = (j.failure_count + 1
                           if j.failure_class == failure_class else 1)
        j.failure_class = failure_class

    def set_failure_detail(self, jid, detail):
        self.jobs[jid].failure_detail = detail

    def next_pending(self):
        for jid, j in self.jobs.items():
            if j.state == "pending":
                return jid
        return None

    def list_state(self, state):
        return [jid for jid, j in self.jobs.items() if j.state == state]

    def dead_letter_due(self, jid, max_failures=3):
        j = self.jobs[jid]
        return j.failure_class is not None and \
            j.failure_count >= max_failures


class Job:
    def __init__(self, state="pending", clips=None, plan_ref="p.json"):
        self.job_id = "job-1"
        self.state = state
        self.clips = clips or [
            {"clip_index": 1, "status": "pending", "log": None,
             "mp4": None, "qc_verdict": None}]
        self.plan_ref = plan_ref
        self.failure_count = 0
        self.failure_class = None


@pytest.fixture
def ok_render():
    """A render fn returning a log with complete step-count evidence."""
    def render(clip):
        return RenderOutcome(
            mp4=f"renders/job-1/clip{clip['clip_index']}/out.mp4",
            log_text=f"Denoising 20/20\nsaved out.mp4",
            log_path=f"renders/job-1/clip{clip['clip_index']}/render.log")
    return render


def test_happy_path_pending_to_done(tmp_path, ok_render):
    q = FakeQueue({"job-1": Job()})
    log = (tmp_path / "render.log")
    log.write_text("Denoising 20/20\n")
    ex = JobExecutor(queue=q, preflight=lambda job: _pf(True),
                     render=ok_render, qc=lambda clip: (True, "qc/1.json"))
    result = ex.run_once()
    assert result == "job-1"
    assert q.jobs["job-1"].state == "done"
    clip = q.jobs["job-1"].clips[0]
    assert clip["status"] == "done"
    assert clip["mp4"].endswith("out.mp4")
    assert clip["qc_verdict"]["path"] == "qc/1.json"


def test_preflight_failure_sends_to_failed_not_render(tmp_path):
    q = FakeQueue({"job-1": Job()})
    ex = JobExecutor(queue=q, preflight=lambda job: _pf(False,
                     detail="model hash mismatch"),
                     render=_no_render_allowed(),
                     qc=lambda clip: (True, "qc/1.json"))
    ex.run_once()
    assert q.jobs["job-1"].state == "failed"


def test_render_admission_marker_failure_is_durable(tmp_path):
    class MarkerFailureQueue(FakeQueue):
        def mark_clip_render_attempt(self, jid, clip_index):
            raise RuntimeError("database locked")

    q = MarkerFailureQueue({"job-1": Job()})
    ex = JobExecutor(
        queue=q, preflight=lambda job: _pf(True),
        render=_no_render_allowed(), qc=lambda clip: (True, "qc/1.json"))
    assert ex.run_once() == "job-1"
    job = q.jobs["job-1"]
    assert job.state == "failed"
    assert job.failure_class == "queue_admission_error"
    assert "database locked" in job.failure_detail


def test_render_ok_qc_unavailable_lands_in_rendered_pending_qc(tmp_path,
                                                                ok_render):
    # tonight's live failure mode: NOT failed, resumable
    q = FakeQueue({"job-1": Job()})
    ex = JobExecutor(queue=q, preflight=lambda job: _pf(True),
                     render=ok_render, qc=_qc_unavailable())
    ex.run_once()
    job = q.jobs["job-1"]
    assert job.state == "rendered_pending_qc"
    # artifacts recorded with paths even while parked
    assert job.clips[0]["mp4"].endswith("out.mp4")


def test_rendered_pending_qc_resumes_when_qc_returns(tmp_path, ok_render):
    q = FakeQueue({"job-1": Job(state="rendered_pending_qc", clips=[
        {"clip_index": 1, "status": "rendered", "log": "l",
         "mp4": "renders/job-1/clip1/out.mp4", "qc_verdict": None}])})
    ex = JobExecutor(queue=q, preflight=lambda job: _pf(True),
                     render=ok_render, qc=lambda clip: (True, "qc/1.json"))
    ex.run_once()
    assert q.jobs["job-1"].state == "done"


def test_truncated_render_log_fails_with_tail_captured(tmp_path):
    q = FakeQueue({"job-1": Job()})
    truncated = "Denoising 15/20\n[no save line]"

    def render(clip):
        return RenderOutcome(
            mp4="renders/job-1/clip1/out.mp4", log_text=truncated,
            log_path="renders/job-1/clip1/render.log")

    ex = JobExecutor(queue=q, preflight=lambda job: _pf(True),
                     render=render, qc=lambda clip: (True, "qc/1.json"))
    ex.run_once()
    job = q.jobs["job-1"]
    assert job.state == "failed"
    # the log tail is captured as the failure artifact
    assert "Denoising 15/20" in (job.failure_detail or "")
    assert "renders/job-1/clip1/render.log" in (job.failure_detail or "")


def test_missing_denoising_line_fails(tmp_path):
    q = FakeQueue({"job-1": Job()})

    def render(clip):
        return RenderOutcome(mp4="m.mp4", log_text="whatever",
                             log_path="l.log")

    ex = JobExecutor(queue=q, preflight=lambda job: _pf(True),
                     render=render, qc=lambda clip: (True, "qc/1.json"))
    ex.run_once()
    assert q.jobs["job-1"].state == "failed"


def test_render_exception_is_recorded_as_failed(tmp_path):
    q = FakeQueue({"job-1": Job()})

    def render(clip):
        raise RuntimeError("continuation envelope rejected")

    ex = JobExecutor(queue=q, preflight=lambda job: _pf(True),
                     render=render,
                     qc=lambda clip: pytest.fail("QC must not run"))
    result = ex.run_once()

    job = q.jobs["job-1"]
    assert result == "job-1"
    assert job.state == "failed"
    assert job.failure_class == "render_error"
    assert job.failure_count == 1
    assert "RuntimeError" in (job.failure_detail or "")
    assert "continuation envelope rejected" in (job.failure_detail or "")


def test_unresolved_chain_ref_fails_before_render(tmp_path):
    q = FakeQueue({"job-1": Job(clips=[
        {"clip_index": 1, "kind": "ref2va_render", "status": "pending",
         "image_start": "chain://clip0001/last_frame",
         "image_refs": ["chain://clip0001/last_frame", "face.png"],
         "log": None, "mp4": None, "qc_verdict": None}])})
    called = []

    def render(_clip):
        called.append(True)
        raise AssertionError("unresolved chain ref must not reach renderer")

    ex = JobExecutor(queue=q, preflight=lambda job: _pf(True),
                     render=render, ref2va_render=render,
                     qc=lambda clip: pytest.fail("QC must not run"))
    ex.run_once()
    job = q.jobs["job-1"]
    assert called == []
    assert job.state == "failed"
    assert job.failure_class == "unresolved_chain_ref"


def test_dead_letter_after_three_same_class_failures(tmp_path):
    q = FakeQueue({"job-1": Job()})

    def render(clip):
        return RenderOutcome(mp4="m.mp4", log_text="Denoising 15/20",
                             log_path="l.log")

    ex = JobExecutor(queue=q, preflight=lambda job: _pf(True),
                     render=render, qc=lambda clip: (True, "qc/1.json"),
                     max_failures=3)
    # attempt 1: failed
    ex.run_once()
    assert q.jobs["job-1"].state == "failed"
    # retry 1 -> failed (2nd same-class failure)
    q.jobs["job-1"].state = "pending"
    ex.run_once()
    # retry 2 -> 3rd same-class failure => dead_letter
    q.jobs["job-1"].state = "pending"
    ex.run_once()
    assert q.jobs["job-1"].state == "dead_letter"


def test_done_clips_skipped(tmp_path, ok_render):
    q = FakeQueue({"job-1": Job(clips=[
        {"clip_index": 1, "status": "done", "log": "l1", "mp4": "m1",
         "qc_verdict": {"verdict": "KEEP", "path": "q1"}},
        {"clip_index": 2, "status": "pending", "log": None,
         "mp4": None, "qc_verdict": None}])})
    ex = JobExecutor(queue=q, preflight=lambda job: _pf(True),
                     render=ok_render, qc=lambda clip: (True, "qc/2.json"))
    ex.run_once()
    assert q.jobs["job-1"].state == "done"
    assert q.jobs["job-1"].clips[0]["mp4"] == "m1"  # untouched


def test_rendered_clip_is_regated_without_second_gpu_render(tmp_path):
    q = FakeQueue({"job-1": Job(clips=[
        {"clip_index": 1, "status": "rendered", "log": "l",
         "mp4": "renders/job-1/clip1/out.mp4", "qc_verdict": None}])})

    def render_must_not_run(_clip):
        raise AssertionError("already-rendered adoption must not rerender")

    ex = JobExecutor(queue=q, preflight=lambda job: _pf(True),
                     render=render_must_not_run,
                     qc=lambda clip: (True, "qc/1.json"))
    ex.run_once()
    assert q.jobs["job-1"].state == "done"
    assert q.jobs["job-1"].clips[0]["status"] == "done"


def test_no_pending_jobs_returns_none(tmp_path):
    q = FakeQueue({})
    ex = JobExecutor(queue=q, preflight=lambda job: _pf(True),
                     render=lambda clip: None,
                     qc=lambda clip: (True, "x"))
    assert ex.run_once() is None


def _pf(passed, detail=""):
    from services.jobs.preflight import PreflightReport
    return PreflightReport(passed=passed, checks=[], detail=detail)


def _no_render_allowed():
    def render(clip):
        raise AssertionError("render must not run when preflight fails")
    return render


def _qc_unavailable():
    def qc(clip):
        raise ConnectionError("QC service unavailable")
    return qc


def test_visual_gate_retries_with_seed_bump_and_append_only_history(tmp_path):
    """A stochastic attribution miss gets two fresh seeds, then stops.

    The old render/log are retained in clip history, while the queue gets a
    new immutable attempt row for each retry.  A third visual miss is
    terminal and records the final seed rather than looping forever.
    """
    q = JobQueue(str(tmp_path / "jobs.db"))
    jid = q.submit(plan_ref="acceptance", clips=[{
        "clip_index": 2, "status": "pending", "seed": 41,
        "log": None, "mp4": None, "qc_verdict": None,
    }])

    def visual_miss(_clip):
        raise Ref2VAQCStageError(
            "visual gate failed: mouth/action/speaker attribution below pass bar",
            vision_scores={"mouth_sync": 0.2, "action_match": 0.8,
                           "speaker_attribution": 0.1},
            vision_raw_response=(
                '{"mouth_sync": 0.2, "action_match": 0.8, '
                '"speaker_attribution": 0.1}'))

    ex = JobExecutor(queue=q, preflight=lambda job: _pf(True),
                     render=lambda clip: None, qc=visual_miss)

    def mark_rendered_for_qc():
        q.set_state(jid, "preflight")
        q.set_state(jid, "rendering")
        rec = q.get(jid)
        clip = rec.clips[0]
        clip.update({"status": "rendered", "log": "render.log",
                     "mp4": f"cut-seed-{clip['seed']}.mp4",
                     "qc_verdict": None})
        q.update_clips(jid, rec.clips)
        q.set_state(jid, "rendered_pending_qc")
        q.set_state(jid, "qc")

    # First miss: seed 41 -> 42, attempt 2 is queued.
    mark_rendered_for_qc()
    ex._qc_clips(q.get(jid))
    rec = q.get(jid)
    assert rec.state == "pending"
    assert rec.clips[0]["seed"] == 42
    assert rec.clips[0]["status"] == "pending"
    assert rec.clips[0]["vision_retry_count"] == 1
    assert rec.clips[0]["vision_retry_history"][0]["mp4"] == (
        "cut-seed-41.mp4")
    assert rec.clips[0]["vision_rejections"][0]["scores"][
        "speaker_attribution"] == 0.1
    assert '"mouth_sync": 0.2' in rec.clips[0]["vision_rejections"][0][
        "raw_response"]
    history = q.attempt_history(jid)
    assert [row["status"] for row in history] == ["failed", "queued"]
    assert "seed 41 -> 42" in history[-1]["attempt_reason"]

    # Second miss: seed 42 -> 43, another immutable attempt is appended.
    mark_rendered_for_qc()
    ex._qc_clips(q.get(jid))
    rec = q.get(jid)
    assert rec.state == "pending"
    assert rec.clips[0]["seed"] == 43
    assert rec.clips[0]["vision_retry_count"] == 2
    history = q.attempt_history(jid)
    assert [row["status"] for row in history] == [
        "failed", "failed", "queued"]
    assert "seed 42 -> 43" in history[-1]["attempt_reason"]

    # Third miss: retry budget exhausted; no fourth attempt is created.
    mark_rendered_for_qc()
    ex._qc_clips(q.get(jid))
    rec = q.get(jid)
    assert rec.state == "dead_letter"
    assert rec.clips[0]["seed"] == 43
    assert len(rec.clips[0]["vision_rejections"]) == 3
    assert all(item["raw_response"] for item in
               rec.clips[0]["vision_rejections"])
    assert len(q.attempt_history(jid)) == 3
    assert q.attempt_history(jid)[-1]["failure_detail"].endswith("seed=43")
    q.close()


def test_non_visual_qc_failure_does_not_seed_retry(tmp_path):
    q = JobQueue(str(tmp_path / "jobs.db"))
    jid = q.submit(plan_ref="acceptance", clips=[{
        "clip_index": 1, "status": "rendered", "seed": 9,
        "log": "render.log", "mp4": "cut.mp4", "qc_verdict": None,
    }])
    q.set_state(jid, "preflight")
    q.set_state(jid, "rendering")
    q.set_state(jid, "rendered_pending_qc")
    q.set_state(jid, "qc")

    def judge_timeout(_clip):
        raise Ref2VAQCStageError("vision judge failed: timeout")

    ex = JobExecutor(queue=q, preflight=lambda job: _pf(True),
                     render=lambda clip: None, qc=judge_timeout)
    ex._qc_clips(q.get(jid))
    assert q.get(jid).state == "failed"
    assert q.get(jid).clips[0]["seed"] == 9
    assert q.attempt_history(jid)[0]["status"] == "failed"
    q.close()
