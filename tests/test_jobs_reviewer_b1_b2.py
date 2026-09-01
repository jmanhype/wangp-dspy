"""B1/B2 regression tests (PR #60 reviewer findings)."""
import dspy
import pytest

from predict.pipeline import Pipeline, PipelineStageError
from services.jobs.compile_guard import (
    CompileContextError,
    _detect_2x,
    assert_not_compiling,
    in_compile_context,
)
from services.jobs.queue import JobQueue


# ---------------------------------------------------------------- B1
class BoomDirector:
    def __init__(self):
        self.called = False

    def __call__(self, intent, **kw):
        self.called = True
        raise AssertionError("director must not run in this test")


def test_b1_probe_real_adapter_trace_context_raises_before_stages():
    """The reviewer's exact scenario: dspy.context(trace=[]) + real
    adapter must raise CompileContextError BEFORE any director stage."""
    pipe = Pipeline(genre="test", director=BoomDirector(),
                    adapter=object())
    with dspy.context(trace=[]):
        with pytest.raises(CompileContextError):
            pipe.forward("a hood two-shot dialogue")
    assert not pipe.director.called


def test_b1_noop_outside_context():
    pipe = Pipeline(genre="test", director=BoomDirector(),
                    adapter=object())
    with pytest.raises(PipelineStageError):
        pipe.forward("intent")  # stage failure, NOT the guard
    assert pipe.director.called


def test_b1_fail_closed_when_signal_unreadable(monkeypatch):
    """Detection import error must NOT be swallowed: with an adapter
    present and an unreadable signal, raise conservatively."""
    import services.jobs.compile_guard as cg
    monkeypatch.setattr(cg, "_detect_3x",
                        lambda: (_ for _ in ()).throw(ImportError("x")))
    monkeypatch.setattr(cg, "_detect_2x",
                        lambda: (_ for _ in ()).throw(ImportError("x")))
    with pytest.raises(CompileContextError, match="could not read"):
        assert_not_compiling(adapter="WanGPAdapter(3090)")


def test_b1_detection_unknown_infects_in_compile_context(monkeypatch):
    import services.jobs.compile_guard as cg
    monkeypatch.setattr(cg, "_detect",
                        lambda: (cg._UNKNOWN, {}))
    assert not in_compile_context()  # informational stays False
    with pytest.raises(CompileContextError):
        assert_not_compiling(adapter="WanGPAdapter(3090)")


class _Fake2xStack:
    """Mimics dspy 2.5.26's Settings.stack_by_thread shape."""

    def __init__(self, depth):
        self.stack_by_thread = {__import__("threading").get_ident():
                                [{"trace": []} for _ in range(depth)]}


def test_b1_dspy2x_stack_depth_signal(monkeypatch):
    """dspy 2.5.26: signal = per-thread Settings stack depth > 1."""
    import sys
    import threading
    import types

    import services.jobs.compile_guard as cg
    # force the 2.x path (3.x override machinery absent)
    monkeypatch.setattr(cg, "_detect_3x",
                        lambda: (_ for _ in ()).throw(ImportError))

    mod = types.ModuleType("dsp.utils.settings")
    mod.settings = _Fake2xStack(1)
    sys.modules["dsp.utils.settings"] = mod
    assert cg._detect() == (cg._NO, {})  # depth 1: no context

    mod.settings = _Fake2xStack(3)  # inside 2 nested dspy.context
    status, _detail = cg._detect()
    assert status is cg._YES

    # explicit flag works on 2.x too
    fake = _Fake2xStack(2)
    fake.stack_by_thread[threading.get_ident()][-1][
        "wangp_compile_guard"] = True
    mod.settings = fake
    assert cg._detect()[0] is cg._YES


# ---------------------------------------------------------------- B2
def _mk_queue(tmp_path, state, clips_status, pid=None, heartbeat=None):
    q = JobQueue(tmp_path / "jobs.db")
    jid = q.submit(
        plan_ref="p.json",
        clips=[{"clip_index": 0, "status": "done",
                "log": "l0.log", "mp4": "c0.mp4",
                "qc_verdict": {"verdict": "KEEP", "path": "v0.json"}},
               {"clip_index": 1, "status": "pending",
                "log": "l1.log", "mp4": "c1.mp4",
                "qc_verdict": None}])
    # walk to the target state legally
    if state in ("rendering", "preflight", "qc"):
        q._db.execute(
            "UPDATE jobs SET state=?, owner_pid=?, last_heartbeat=? "
            "WHERE job_id=?", (state, pid, heartbeat, jid))
        q._db.commit()
    return q, jid


def test_b2_stale_rendering_job_recovered_and_resumed(tmp_path):
    """Stale 'rendering' (dead pid) -> recover -> run_once resumes
    WITHOUT redoing the done clip."""
    from services.jobs.executor import JobExecutor, RenderOutcome

    dead_pid = 99999999  # not a live process
    q, jid = _mk_queue(tmp_path, "rendering",
                       ("rendered", "pending"),
                       pid=dead_pid, heartbeat=0.0)  # ancient heartbeat
    rendered = []

    def render(clip):
        rendered.append(clip["clip_index"])
        return RenderOutcome(
            mp4=f"c{clip['clip_index']}.mp4",
            log_text="Denoising 20/20 done",
            log_path=f"l{clip['clip_index']}.log")

    class Report:
        passed = True
        detail = ""

    ex = JobExecutor(queue=q, preflight=lambda job: Report(),
                     render=render, qc=lambda clip: (True, "v.json"))
    handled = ex.run_once()
    assert handled == jid
    rec = q.get(jid)
    assert rec.state == "done"
    # only clip 1 rendered — clip 0's checkpoint was honored
    assert rendered == [1]


def test_b2_fresh_rendering_job_not_picked(tmp_path):
    """A 'rendering' job with a LIVE owner pid must NOT be recovered."""
    from services.jobs.executor import JobExecutor

    live_pid = __import__("os").getpid()
    q, jid = _mk_queue(tmp_path, "rendering", ("pending", "pending"),
                       pid=live_pid,
                       heartbeat=__import__("time").time())
    calls = []

    def render(clip):
        calls.append(clip["clip_index"])
        raise AssertionError("fresh job must not be touched")

    class Report:
        passed = True
        detail = ""

    ex = JobExecutor(queue=q, preflight=lambda job: Report(),
                     render=render, qc=lambda clip: (True, "v.json"))
    assert ex.run_once() is None
    assert q.get(jid).state == "rendering"
    assert calls == []


def test_b2_fresh_heartbeat_without_pid_protected(tmp_path):
    """No pid recorded but heartbeat is fresh -> still owned."""
    from services.jobs.executor import JobExecutor
    import time as _t

    q, jid = _mk_queue(tmp_path, "rendering", ("pending", "pending"),
                       pid=None, heartbeat=_t.time())

    class Report:
        passed = True
        detail = ""

    ex = JobExecutor(queue=q, preflight=lambda job: Report(),
                     render=lambda clip: (_ for _ in ()).throw(
                         AssertionError("must not render")),
                     qc=lambda clip: (True, "v.json"))
    assert ex.run_once() is None
    assert q.get(jid).state == "rendering"


def test_b2_legacy_orphaned_active_rows_recovered(tmp_path):
    """Legacy rows (no pid, no heartbeat column data) in active states
    are treated as stale and recovered."""
    q, jid = _mk_queue(tmp_path, "qc", ("rendered", "rendered"),
                       pid=None, heartbeat=None)
    recovered = q.recover_stale_active(staleness_s=600.0)
    assert recovered == [jid]
    assert q.get(jid).state == "pending"
