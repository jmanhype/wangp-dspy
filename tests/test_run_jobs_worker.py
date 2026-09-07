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
        if argv[:1] == ["df"]:
            return 0, "  100G\n", ""
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


class TestExecutorNeedsGating:
    """BLOCKER regression (PR #63 review): dependency gating must live
    on the ACTUAL execution path (JobExecutor._pick_job), not only in
    the run_jobs helper. A blocked dependent that is OLDER than its
    prerequisite must stay pending while the prerequisite renders."""

    def _executor(self, q, host):
        return run_jobs.build_executor(q, host=host)

    def test_executor_never_picks_blocked_dependent(
            self, tmp_path, monkeypatch):
        q = JobQueue(str(tmp_path / "jobs.db"))
        # DEPENDENT FIRST (older) — its `needs` points at the
        # prerequisite's job id, wired in after both are submitted
        host = FakeHost()

        class _Res:
            video_path = "renders/out.mp4"
            settings_path = "renders/render"

        monkeypatch.setattr(
            "host.wangp_adapter.WanGPAdapter.render_for_job",
            lambda self, clip: _Res())
        dep_clips = [{"clip_index": 1, "status": "pending",
                      "kind": "fl2va_first_last",
                      "log": None, "mp4": None, "qc_verdict": None}]
        pre_clips = [{"clip_index": 1, "status": "pending",
                      "kind": "r2i_pose_target",
                      "log": None, "mp4": None, "qc_verdict": None}]
        dep_id = q.submit(plan_ref="dep.json", clips=dep_clips)
        pre_id = q.submit(plan_ref="pre.json", clips=pre_clips)
        # wire the dependency (clip-level `needs`)
        clips = q.get(dep_id).clips
        clips[0]["needs"] = pre_id
        q.update_clips(dep_id, clips)
        # dependent is OLDER: oldest-pending would pick it
        assert q.next_pending() == dep_id

        ex = self._executor(q, host)
        # drain once: prerequisite runs, dependent stays pending
        ran = ex.run_once()
        assert ran == pre_id
        assert q.get(pre_id).state == "done"
        assert q.get(dep_id).state == "pending"
        # ...and the drain loop keeps going for admissible jobs only
        handled = run_jobs.drain_once(q, host=host)
        assert dep_id in handled
        assert q.get(dep_id).state == "done"

    def test_executor_blocked_only_job_returns_none(self, tmp_path):
        q = JobQueue(str(tmp_path / "jobs.db"))
        dep_id = q.submit(
            plan_ref="dep.json",
            clips=[{"clip_index": 1, "status": "pending",
                    "kind": "fl2va_first_last", "needs": "nope-xyz",
                    "log": None, "mp4": None, "qc_verdict": None}])
        ex = self._executor(q, FakeHost())
        assert ex.run_once() is None
        assert q.get(dep_id).state == "pending"


class TestRenderForJobWiring:
    def test_build_executor_fails_closed_without_per_job_renderer(
            self, monkeypatch):
        """A production adapter without render_for_job must be rejected
        before a queue job can be claimed; legacy render() is not a bridge.
        """
        import scripts.run_jobs as run_jobs

        class LegacyOnlyAdapter:
            def __init__(self, host=None):
                self.host = host

            def render(self, *args, **kwargs):
                return None

        monkeypatch.setattr(run_jobs, "WanGPAdapter", LegacyOnlyAdapter,
                            raising=False)
        # build_executor imports the adapter inside the function, so patch
        # the module that owns the constructor as well.
        monkeypatch.setattr("host.wangp_adapter.WanGPAdapter",
                            LegacyOnlyAdapter)
        with pytest.raises(TypeError, match="render_for_job"):
            run_jobs.build_executor(queue=None, host=object())

    def test_ref2va_qc_wiring_runs_pre_and_post_whisper(self, tmp_path):
        import scripts.run_jobs as run_jobs
        guide = Path(tmp_path) / "guide.wav"
        guide.write_bytes(b"wav")
        source = Path(tmp_path) / "source.wav"
        source.write_bytes(b"wav")
        wmap = Path(tmp_path) / "whisper.json"
        wmap.write_text("{}")
        clip = {
            "clip_index": 1, "kind": "ref2va_render",
            "audio_guide": str(guide), "mp4": str(Path(tmp_path) / "cut.mp4"),
            "dialogue_text": "The gate is open",
            "audio_provenance": {
                "source_master": str(source), "vocal_stem": str(source),
                "whisper_map": str(wmap), "keeper_window_s": [0.0, 2.0],
            },
            "audio_policy": {"discard_rendered_audio": True},
            "speaker_sn": "S1",
            "action": "turns toward gate",
        }
        ex = run_jobs.build_executor(
            queue=None, host=FakeHost(),
            whisper_transcriber=lambda _: "The gate is open",
            vision_judge=lambda **_: {
                "mouth_sync": 0.9, "action_match": 0.9,
                "speaker_attribution": 0.9,
            })
        ok, evidence = ex.qc(clip)
        assert ok is True
        assert evidence["whisper_gates"]["pre"]["passed"] is True
        assert evidence["whisper_gates"]["post"]["phase"] == "post"
        assert evidence["vision_judge"]["passed"] is True

    def test_ref2va_qc_wiring_rejects_missing_vision_judge(self, tmp_path):
        """A ref2va job cannot produce a ledger KEEP without visual evidence."""
        from qc.audio_critic.ref2va_stage import Ref2VAQCStageError

        guide = Path(tmp_path) / "guide.wav"
        guide.write_bytes(b"wav")
        source = Path(tmp_path) / "source.wav"
        source.write_bytes(b"wav")
        wmap = Path(tmp_path) / "whisper.json"
        wmap.write_text("{}")
        clip = {
            "clip_index": 1, "kind": "ref2va_render",
            "audio_guide": str(guide), "mp4": str(Path(tmp_path) / "cut.mp4"),
            "dialogue_text": "The gate is open",
            "speaker_sn": "S1", "action": "turns toward gate",
            "audio_provenance": {
                "source_master": str(source), "vocal_stem": str(source),
                "whisper_map": str(wmap), "keeper_window_s": [0.0, 2.0],
            },
            "audio_policy": {"discard_rendered_audio": True},
        }
        ex = run_jobs.build_executor(
            queue=None, host=FakeHost(),
            whisper_transcriber=lambda _: "The gate is open")
        with pytest.raises(Ref2VAQCStageError, match="vision judge is not wired"):
            ex.qc(clip)


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
        q = _queue(tmp_path, [
            ("A.json", [{"clip_index": 1, "status": "pending",
                         "kind": "r2i_pose_target", "log": None,
                         "mp4": None, "qc_verdict": None}]),
            ("B.json", [{"clip_index": 1, "status": "pending",
                         "kind": "fl2va_first_last",
                         "needs": "missing", "log": None, "mp4": None,
                         "qc_verdict": None}]),
        ])
        a_id, b_id = q.list_state("pending")
        report = run_jobs.dry_run_report(q)
        entries = {e["job_id"]: e for e in report["would_run"]}
        # the blocked job is FLAGGED with its unmet dependency
        assert entries[b_id]["blocked_by"] == "missing"
        # the admissible job is not flagged as blocked
        assert entries[a_id]["blocked_by"] is None
        # and the dry-run PLAN would execute only the admissible job
        assert run_jobs.dry_run_plan(q) == [a_id]

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

    def test_once_recovers_stale_prerequisite_before_needs_gate(
            self, tmp_path, monkeypatch):
        q = JobQueue(str(tmp_path / "jobs.db"))
        prerequisite = q.submit(
            plan_ref="pre.json",
            clips=[{"clip_index": 1, "status": "pending",
                    "kind": "r2i_pose_target", "log": None,
                    "mp4": None, "qc_verdict": None}],
        )
        dependent = q.submit(
            plan_ref="dep.json",
            clips=[{"clip_index": 2, "status": "pending",
                    "kind": "ref2va_render", "needs": prerequisite,
                    "log": None, "mp4": None, "qc_verdict": None}],
        )
        # Simulate a worker crash after claiming the prerequisite.  The
        # missing heartbeat/owner makes this immediately recoverable.
        q.set_state(prerequisite, "preflight")
        q.set_state(prerequisite, "rendering")
        seen = []

        class FakeEx:
            def run_once(self):
                seen.append(run_jobs.next_admissible(q))
                return seen[-1]

        monkeypatch.setattr(run_jobs, "_default_host", lambda: FakeHost())
        monkeypatch.setattr(run_jobs, "build_executor",
                            lambda queue, host=None: FakeEx())
        rc = run_jobs.main(["--db", str(tmp_path / "jobs.db"), "--once"])

        assert rc == 0
        assert seen == [prerequisite]
        assert q.get(prerequisite).state == "pending"
        assert q.get(dependent).state == "pending"

    def test_retry_failed_prerequisite_with_dependents(self, tmp_path,
                                                       monkeypatch, capsys):
        """--retry-failed appends an attempt and unblocks only the
        prerequisite; its dependent remains pending until completion."""
        q = JobQueue(str(tmp_path / "jobs.db"))
        prerequisite = q.submit(
            plan_ref="pre.json",
            clips=[{"clip_index": 1, "status": "pending",
                    "kind": "r2i_pose_target", "log": None,
                    "mp4": None, "qc_verdict": None}],
        )
        dependent = q.submit(
            plan_ref="dep.json",
            clips=[{"clip_index": 2, "status": "pending",
                    "kind": "ref2va_render", "needs": prerequisite,
                    "log": None, "mp4": None, "qc_verdict": None}],
        )
        q.set_state(prerequisite, "preflight")
        q.set_state(prerequisite, "rendering")
        q.record_failure(prerequisite, failure_class="render_error")
        q.set_failure_detail(prerequisite, "old render failure")
        q.set_state(prerequisite, "failed")
        q.close()

        seen = []
        class FakeEx:
            def run_once(self):
                seen.append(run_jobs.next_admissible(
                    JobQueue(str(tmp_path / "jobs.db"))))
                return seen[-1]

        monkeypatch.setattr(run_jobs, "_default_host", lambda: FakeHost())
        monkeypatch.setattr(run_jobs, "build_executor",
                            lambda queue, host=None: FakeEx())
        rc = run_jobs.main(["--db", str(tmp_path / "jobs.db"),
                            "--retry-failed", "--once"])
        assert rc == 0
        assert seen == [prerequisite]
        q2 = JobQueue(str(tmp_path / "jobs.db"))
        assert q2.get(prerequisite).state == "pending"
        assert q2.get(dependent).state == "pending"
        history = q2.attempt_history(prerequisite)
        assert len(history) == 2
        assert history[1]["parent_attempt_id"] == history[0]["attempt_id"]
        assert "requeued 1 failed job" in capsys.readouterr().out

    def test_retry_dead_letter_requires_audited_reason(self, tmp_path, capsys,
                                                       monkeypatch):
        q = JobQueue(str(tmp_path / "jobs.db"))
        jid = q.submit(
            plan_ref="p.json",
            clips=[{"clip_index": 1, "status": "pending",
                    "log": None, "mp4": None, "qc_verdict": None}],
        )
        q.set_state(jid, "preflight")
        q.set_state(jid, "rendering")
        q.record_failure(jid, failure_class="render_error")
        q.set_failure_detail(jid, "boom")
        q.set_state(jid, "failed")
        q.record_failure(jid, failure_class="render_error")
        q.record_failure(jid, failure_class="render_error")
        q.set_state(jid, "dead_letter")
        q.close()

        rc = run_jobs.main(["--db", str(tmp_path / "jobs.db"),
                            "--retry-dead-letter",
                            "--reason", "operator reopened after fix",
                            "--dry-run"])
        assert rc == 2
        assert "cannot be combined" in capsys.readouterr().err

        class FakeEx:
            def run_once(self):
                return jid

        monkeypatch.setattr(run_jobs, "_default_host", lambda: FakeHost())
        monkeypatch.setattr(run_jobs, "build_executor",
                            lambda queue, host=None: FakeEx())
        rc = run_jobs.main(["--db", str(tmp_path / "jobs.db"),
                            "--retry-dead-letter",
                            "--reason", "operator reopened after fix",
                            "--once"])
        assert rc == 0
        q2 = JobQueue(str(tmp_path / "jobs.db"))
        assert q2.get(jid).state == "pending"
        assert q2.attempt_history(jid)[-1]["reopen_reason"] == (
            "operator reopened after fix")

    def test_drain_recovers_stale_prerequisite_before_needs_gate(
            self, tmp_path, monkeypatch):
        q = JobQueue(str(tmp_path / "jobs.db"))
        prerequisite = q.submit(
            plan_ref="pre.json",
            clips=[{"clip_index": 1, "status": "pending",
                    "kind": "r2i_pose_target", "log": None,
                    "mp4": None, "qc_verdict": None}],
        )
        dependent = q.submit(
            plan_ref="dep.json",
            clips=[{"clip_index": 2, "status": "pending",
                    "kind": "ref2va_render", "needs": prerequisite,
                    "log": None, "mp4": None, "qc_verdict": None}],
        )
        q.set_state(prerequisite, "preflight")
        q.set_state(prerequisite, "rendering")
        picked = []

        class FakeEx:
            def run_once(self):
                picked.append(run_jobs.next_admissible(q))
                return picked[-1]

        monkeypatch.setattr(run_jobs, "build_executor",
                            lambda queue, host=None: FakeEx())
        handled = run_jobs.drain_once(q, host=FakeHost(), limit=1)

        assert handled == [prerequisite]
        assert picked == [prerequisite]
        assert q.get(prerequisite).state == "pending"
        assert q.get(dependent).state == "pending"


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
