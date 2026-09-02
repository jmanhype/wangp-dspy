"""RED tests — executor dispatch by job kind; run_cycle --lane; guard
covers the ref2va lane. No GPU, all stubs."""
import pytest
from types import SimpleNamespace

import services.jobs.executor as exec_mod
from services.jobs.executor import JobExecutor, RenderOutcome, render_lane_for


class FakeQueue:
    def __init__(self, jobs=None):
        self.jobs = jobs or {}
        self.updates = []

    def get(self, jid):
        return self.jobs[jid]

    def set_state(self, jid, state):
        from services.jobs.states import transition
        job = self.jobs[jid]
        job.state = transition(job.state, state)

    def update_clip(self, jid, clip_index, **kw):
        self.updates.append((jid, clip_index, kw))
        for c in self.jobs[jid].clips:
            if c["clip_index"] == clip_index:
                c.update(kw)

    def record_failure(self, jid, failure_class):
        j = self.jobs[jid]
        j.failure_count = (j.failure_count + 1
                           if j.failure_class == failure_class else 1)
        j.failure_class = failure_class

    def set_failure_detail(self, jid, detail):
        pass

    def next_pending(self):
        for jid, j in self.jobs.items():
            if j.state == "pending":
                return jid
        return None

    def list_state(self, state):
        return [jid for jid, j in self.jobs.items() if j.state == state]

    def dead_letter_due(self, jid, max_failures=3):
        return False


class Job:
    def __init__(self, state="pending", clips=None, kind="fl2va_render"):
        self.job_id = "job-1"
        self.state = state
        self.kind = kind
        self.clips = clips or [
            {"clip_index": 1, "status": "pending", "log": None,
             "mp4": None, "qc_verdict": None, "kind": kind}]
        self.failure_count = 0
        self.failure_class = None


def _pf(ok):
    return SimpleNamespace(passed=ok, detail="" if ok else "bad")


class TestDispatch:
    def test_render_lane_for_table(self):
        assert render_lane_for("ref2va_render") == "ref2va"
        assert render_lane_for("shot1_three_ref_recipe") == "fl2va"
        assert render_lane_for("first_frame_continuation") == "fl2va"
        assert render_lane_for("fl2va_render") == "fl2va"
        assert render_lane_for(None) == "fl2va"

    def test_dispatches_ref2va_job_to_ref2va_renderer(self, ok_log):
        q = FakeQueue({"job-1": Job(kind="ref2va_render")})
        lanes = []

        def r2va(clip):
            lanes.append(("ref2va", clip))
            return RenderOutcome(mp4="out.mp4", log_text=ok_log,
                                 log_path="render.log")

        def fl2va(clip):
            lanes.append(("fl2va", clip))
            return RenderOutcome(mp4="out.mp4", log_text=ok_log,
                                 log_path="render.log")

        ex = JobExecutor(
            queue=q, preflight=lambda j: _pf(True),
            render=fl2va, ref2va_render=r2va,
            qc=lambda c: (True, "qc/1.json"))
        ex.run_once()
        assert [l for l, _ in lanes] == ["ref2va"]

    def test_fl2va_job_unchanged(self, ok_log):
        q = FakeQueue({"job-1": Job(kind="first_frame_continuation")})
        lanes = []

        def r2va(clip):
            lanes.append("ref2va")
            return RenderOutcome(mp4="o", log_text=ok_log, log_path="l")

        def fl2va(clip):
            lanes.append("fl2va")
            return RenderOutcome(mp4="o", log_text=ok_log, log_path="l")

        ex = JobExecutor(
            queue=q, preflight=lambda j: _pf(True),
            render=fl2va, ref2va_render=r2va,
            qc=lambda c: (True, "qc/1.json"))
        ex.run_once()
        assert lanes == ["fl2va"]

    def test_job_record_logs_lane(self, ok_log):
        q = FakeQueue({"job-1": Job(kind="ref2va_render")})

        def r2va(clip):
            return RenderOutcome(mp4="o.mp4", log_text=ok_log,
                                 log_path="l")

        ex = JobExecutor(
            queue=q, preflight=lambda j: _pf(True),
            render=lambda c: pytest.fail("fl2va fired on ref2va job"),
            ref2va_render=r2va,
            qc=lambda c: (True, "qc/1.json"))
        ex.run_once()
        # the clip record carries which lane rendered it
        jid, idx, kw = q.updates[0]
        assert kw.get("lane") == "ref2va"


@pytest.fixture
def ok_log():
    return "Denoising 20/20\nsaved"


class TestRunCycleLane:
    def test_lane_flag_parsing(self, capsys):
        import scripts.run_cycle as rc
        assert rc.parse_lane(["--lane", "ref2va"]) == "ref2va"
        assert rc.parse_lane([]) == "fl2va"
        assert rc.parse_lane(["--lane", "fl2va"]) == "fl2va"
        with pytest.raises(SystemExit):
            rc.parse_lane(["--lane", "bogus"])


class TestGuardCoversRef2va:
    def test_ref2va_lane_refuses_under_compile_context(self):
        import dspy
        from services.jobs.compile_guard import CompileContextError
        from host.wangp_adapter import WanGPAdapter, WanGPError
        adapter = WanGPAdapter.__new__(WanGPAdapter)
        with dspy.context(trace=[]):
            with pytest.raises(CompileContextError):
                adapter.render_for_job({"kind": "ref2va_render"})
