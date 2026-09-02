"""Queue worker entrypoint tests (scripts/run_jobs.py).

Dependency order, r2i last-frame extraction call shape, --once /
--dry-run. Host interactions via injected fakes — NO GPU, NO SSH.
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts import run_jobs  # noqa: E402
from services.jobs.queue import JobQueue  # noqa: E402


class FakeHost:
    def __init__(self):
        self.calls = []

    def run_probe(self, argv, timeout=30):
        self.calls.append(list(argv))
        if argv[:2] == ["ffmpeg", "-y"] and argv[2] == "-sseof":
            return 0, "", ""
        if argv[:1] == ["cat"]:
            return 0, "Denoising 20/20\n", ""
        return 0, "", ""


def _queue(tmp_path, jobs=()):
    q = JobQueue(str(tmp_path / "jobs.db"))
    for plan_ref, clips in jobs:
        q.submit(plan_ref=plan_ref, clips=clips)
    return q


class TestDependencyOrder:
    def test_blocked_job_stays_pending(self, tmp_path):
        q = _queue(tmp_path, [(
            "B.json", [{"clip_index": 1, "status": "pending",
                        "kind": "fl2va_first_last",
                        "needs": "r2i-clip0002", "log": None,
                        "mp4": None, "qc_verdict": None}])])
        assert run_jobs.next_admissible(q) is None
        # and it stays pending — never picked, never failed
        assert q.list_state("pending")

    def test_runs_after_need_completes(self, tmp_path):
        q = _queue(tmp_path, [(
            "B.json", [{"clip_index": 1, "status": "pending",
                        "kind": "fl2va_first_last",
                        "needs": "r2i-clip0002", "log": None,
                        "mp4": None, "qc_verdict": None}])])
        # mark the dependency done
        q.submit(plan_ref="A.json", clips=[
            {"clip_index": 1, "status": "pending",
             "kind": "r2i_pose_target", "log": None, "mp4": None,
             "qc_verdict": None}])
        a_id = q.next_pending()
        q.set_state(a_id, "preflight")
        q.set_state(a_id, "rendering")
        q.set_state(a_id, "rendered_pending_qc")
        q.set_state(a_id, "qc")
        q.set_state(a_id, "done")
        # now B is admissible
        b_id = [j for j in q.list_state("pending")][0]
        assert run_jobs.next_admissible(q) == b_id


class TestR2ILastFrame:
    def test_extraction_argv_shape(self):
        argv = run_jobs.extract_last_frame_argv(
            "/run/render/clip0002/r2i.mp4",
            "/run/render/clip0002/r2i-clip0002_last_frame.png")
        assert argv == [
            "ffmpeg", "-y", "-sseof", "-0.1",
            "-i", "/run/render/clip0002/r2i.mp4",
            "-frames:v", "1",
            "/run/render/clip0002/r2i-clip0002_last_frame.png"]

    def test_extraction_failure_raises(self):
        class Bad:
            def run_probe(self, argv, timeout=30):
                return 1, "", "boom"
        with pytest.raises(RuntimeError, match="last-frame extraction"):
            run_jobs.extract_last_frame(
                Bad(), "a.mp4", "a.png")

    def test_record_last_frame_persists(self, tmp_path):
        q = _queue(tmp_path, [(
            "A.json", [{"clip_index": 2, "status": "done",
                        "kind": "r2i_pose_target", "log": "l",
                        "mp4": "m.mp4",
                        "qc_verdict": {"verdict": "KEEP", "path": "q"}}])])
        jid = q.list_state("done")[0] if q.list_state("done") \
            else q.next_pending()
        job = q.get(jid)
        run_jobs.record_last_frame(q, job, "/run/lf.png")
        assert any(c.get("last_frame") == "/run/lf.png"
                   for c in q.get(jid).clips)

    def test_png_path_convention(self):
        class J:
            job_id = "r2i-clip0002-abc"
            clips = [{"clip_index": 2}]
        png = run_jobs.r2i_last_frame_png("/run", J())
        assert png == ("/run/render/clip0002/"
                       "r2i-clip0002-abc_last_frame.png")


class TestDryRunAndOnce:
    def test_dry_run_no_host_calls_no_state_mutation(self, tmp_path, capsys):
        q = _queue(tmp_path, [(
            "A.json", [{"clip_index": 1, "status": "pending",
                        "kind": "fl2va_first_last", "log": None,
                        "mp4": None, "qc_verdict": None}])])
        rc = run_jobs.main(["--db", str(tmp_path / "jobs.db"),
                            "--dry-run"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "would run" in out or "job_id" in out
        # state untouched
        q2 = JobQueue(str(tmp_path / "jobs.db"))
        assert q2.list_state("pending")

    def test_dry_run_marks_blocked(self, tmp_path):
        q = _queue(tmp_path, [(
            "B.json", [{"clip_index": 1, "status": "pending",
                        "kind": "fl2va_first_last",
                        "needs": "missing", "log": None, "mp4": None,
                        "qc_verdict": None}])])
        report = run_jobs.dry_run_report(q)
        assert len(report["would_run"]) == 1
        entry = report["would_run"][0]
        assert entry["blocked_by"] == "missing"

    def test_once_exits_after_one(self, tmp_path, monkeypatch, capsys):
        # two admissible jobs; --once runs exactly one
        q = _queue(tmp_path, [
            ("A.json", [{"clip_index": 1, "status": "pending",
                         "log": None, "mp4": None, "qc_verdict": None}]),
            ("B.json", [{"clip_index": 1, "status": "pending",
                         "log": None, "mp4": None, "qc_verdict": None}]),
        ])
        # fake the executor so no host is touched
        import services.jobs.executor as ex_mod

        class FakeEx:
            def __init__(self, **kw):
                pass

            def run_once(self):
                jid = None
                return jid
        monkeypatch.setattr(
            "scripts.run_jobs.build_executor",
            lambda queue, host=None: FakeEx())
        rc = run_jobs.main(["--db", str(tmp_path / "jobs.db"),
                            "--once"])
        assert rc == 0
        q2 = JobQueue(str(tmp_path / "jobs.db"))
        ran = capsys.readouterr().out
        assert "ran " in ran
        # exactly one job left fully pending-ish (not both consumed)
        # (FakeEx did nothing, but only ONE job was targeted)
        assert ran.count("ran ") == 1


class TestDryRunReportShape:
    def test_report_lists_pending(self, tmp_path):
        q = _queue(tmp_path, [(
            "A.json", [{"clip_index": 1, "status": "pending",
                        "kind": "r2i_pose_target", "log": None,
                        "mp4": None, "qc_verdict": None}])])
        report = run_jobs.dry_run_report(q)
        assert len(report["would_run"]) == 1
        assert report["would_run"][0]["kinds"] == ["r2i_pose_target"]
        json.dumps(report)  # serializable
