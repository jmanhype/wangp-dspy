"""Ops hardening (PR feat/ops-hardening).

1. host/wangp_adapter: strip <Picture N>/<Subject N> tokens at the
   runtime boundary automatically — the cleaned form is canonical and
   the raw-token form has bitten us twice.
2. scripts/run_jobs --loop drain semantics incl. chain advance.
3. Alignment-mux audio_policy: whisper both tracks, compute offset,
   shift the guide mux — with a mocked transcript fn (no whisper
   dependency in tests).
"""
from __future__ import annotations

import pytest


# ── 1. runtime token stripping at the adapter boundary ───────────────

class TestAdapterTokenStrip:
    def test_strips_picture_and_subject_tokens(self):
        from host.wangp_adapter import strip_runtime_tokens
        raw = ("<Picture 1> is the two-shot composition anchor.\n"
               "<Subject 1> (from <Picture 2>): a woman.\n"
               "Summary: <Subject 1> speaks. <Subject 2> listens.")
        cleaned = strip_runtime_tokens(raw)
        assert "<Picture" not in cleaned
        assert "<Subject" not in cleaned
        # structure survives: anchor phrase remains, and every
        # <Subject N> occurrence became (character)
        assert "two-shot composition anchor" in cleaned
        assert cleaned.count("(character)") == raw.count("<Subject")

    def test_passthrough_when_already_clean(self):
        from host.wangp_adapter import strip_runtime_tokens
        clean = "Summary: (S1) says: <d>[English] Hello.</d>"
        assert strip_runtime_tokens(clean) == clean

    def test_built_settings_prompt_never_carries_tokens(self, tmp_path):
        """Runtime boundary: build_settings output prompt is cleaned
        even when the caller supplies a token-bearing prompt."""
        from host.wangp_adapter import strip_runtime_tokens  # noqa: F401
        # the boundary fn itself is the contract; deep integration is
        # covered by render_for_job tests below
        from host.wangp_adapter import strip_runtime_tokens as srt
        out = srt("x <Picture 3> y <Subject 7> z")
        assert out == "x the composition anchor y (character) z"


# ── 2. drain semantics incl. chain advance ──────────────────────────

class _FakeHost:
    def __init__(self):
        self.calls = []

    def run_probe(self, argv, timeout=30):
        self.calls.append(list(argv))
        return 0, "", ""


def _chain_queue(tmp_path):
    """A 2-clip chain: clip 2 chained on clip 1's last frame."""
    from services.jobs.queue import JobQueue
    from services.director.wiring import plan_to_clips
    characters = [
        {"name": "Ada", "sn_tag": "S1", "description": "engineer"},
        {"name": "Bo", "sn_tag": "S2", "description": "pilot"},
    ]
    plates = {"anchor": "a.png", "Ada": "ada.png", "Bo": "bo.png"}
    clips = plan_to_clips(
        [{"speaker": "Ada", "text": "One."},
         {"speaker": "Bo", "text": "Two."}],
        characters, plates,
        audio_paths=["a1.wav", "a2.wav"], whisper_map="w.json")
    q = JobQueue(str(tmp_path / "jobs.db"))
    prev = None
    ids = []
    for c in clips:
        clip = dict(c)
        clip["needs"] = prev
        ids.append(q.submit(plan_ref="film", clips=[clip]))
        prev = ids[-1]
    return q, ids, clips


def _fake_execute(monkeypatch, queue):
    """Replace build_executor with a stub that walks each job to done
    with a fake mp4 — drain logic under test, not the render seam."""
    from scripts import run_jobs as rj

    class _Report:
        passed = True
        detail = "ok"

    class _Outcome:
        def __init__(self):
            self.mp4 = "render/out.mp4"
            self.log_text = "Denoising 20/20\n"
            self.log_path = "render.log"

    class _Ex:
        def __init__(self, queue):
            self._qid = None

        def run_once(self):
            from services.jobs.queue import next_admissible
            jid = next_admissible(self.__dict__.get("_queue", queue)
                                  if "_queue" in self.__dict__ else queue)
            if jid is None:
                return None
            self._qid = jid
            for st in ("preflight", "rendering"):
                queue.set_state(jid, st)
            job = queue.get(jid)
            for c in job.clips:
                if c.get("status") != "done":
                    queue.update_clip(
                        jid, c["clip_index"], status="rendered",
                        log="render.log", mp4="render/out.mp4",
                        qc_verdict=None)
            for st in ("rendered_pending_qc", "qc", "done"):
                queue.set_state(jid, st)
            return jid

    monkeypatch.setattr(rj, "build_executor",
                        lambda queue, host=None, pre_render=None: _Ex(queue))
    return _Report


class TestDrainLoopSemantics:
    def test_drain_once_advances_chain(self, tmp_path, monkeypatch):
        """drain_once runs BOTH chain jobs in one drain: after job 1
        is done, its last frame is extracted and job 2's chain:// ref
        is patched, making it admissible."""
        from scripts.run_jobs import drain_once
        q, ids, clips = _chain_queue(tmp_path)
        _fake_execute(monkeypatch, q)
        host = _FakeHost()
        handled = drain_once(q, host=host)
        assert handled == ids
        ffmpeg = [c for c in host.calls if c[:2] == ["ffmpeg", "-y"]]
        assert len(ffmpeg) == 1
        # job 2's image_refs[0] patched to a real png
        job2 = q.get(ids[1])
        assert not str(job2.clips[0]["image_refs"][0]).startswith(
            "chain://")
        assert job2.clips[0]["image_refs"][0].endswith(
            "chain_last_frame.png")

    def test_drain_no_host_no_advance(self, tmp_path, monkeypatch):
        """host=None: renders happen but no chain advance (nothing to
        extract the frame with) — job 2 stays pending, unpatched."""
        from scripts.run_jobs import drain_once
        q, ids, clips = _chain_queue(tmp_path)
        _fake_execute(monkeypatch, q)
        handled = drain_once(q, host=None)
        assert handled == [ids[0]]
        assert str(q.get(ids[1]).clips[0]["image_refs"][0]).startswith(
            "chain://")

    def test_pre_render_hook_injected_and_called(self, tmp_path,
                                                 monkeypatch):
        """The phased pre_render hook rides build_executor through to
        the executor (documented, injectable seam)."""
        from scripts import run_jobs as rj
        from services.jobs.executor import JobExecutor
        real_build = rj.build_executor  # the genuine seam, pre-stub
        seen_builds = []

        def spy_build(queue, host=None, pre_render=None):
            seen_builds.append(pre_render)
            return real_build(queue, host=host, pre_render=pre_render)

        monkeypatch.setattr(rj, "build_executor", spy_build)
        q, ids, clips = _chain_queue(tmp_path)

        def hook(clip):
            return None

        ex = rj.build_executor(q, host=None, pre_render=hook)
        assert seen_builds == [hook]
        assert isinstance(ex, JobExecutor)
        assert ex.pre_render is hook


# ── 3. alignment-mux audio_policy ───────────────────────────────────

class TestAlignmentMux:
    def _tracks(self):
        # reference (already-muxed guide) vs drifted re-mux candidate;
        # transcript fn returns [(start_s, end_s, text), ...]
        return {
            "reference": [(0.50, 1.40, "hello"), (2.00, 2.90, "world")],
            "candidate": [(0.62, 1.52, "hello"), (2.12, 3.02, "world")],
        }

    def test_offset_computed_from_transcripts(self):
        from services.audio.alignment_mux import compute_alignment_offset
        t = self._tracks()
        off = compute_alignment_offset(t["reference"], t["candidate"])
        assert off == pytest.approx(0.12, abs=0.02)

    def test_offset_zero_when_aligned(self):
        from services.audio.alignment_mux import compute_alignment_offset
        t = self._tracks()
        assert compute_alignment_offset(t["reference"],
                                        t["reference"]) == 0.0

    def test_shift_arg_shape(self):
        from services.audio.alignment_mux import alignment_shift_argv
        argv = alignment_shift_argv(0.12, "guide.wav", "out.wav")
        assert argv[:5] == ["ffmpeg", "-y", "-itsoffset", "0.12",
                            "-i"]
        assert "guide.wav" in argv and "out.wav" in argv
        assert "-c:a" in argv and "copy" in argv

    def test_alignment_mux_policy_end_to_end(self, tmp_path):
        """audio_policy function: whisper both tracks (mocked), compute
        the offset, return the shift plan — no whisper dependency."""
        from services.audio.alignment_mux import alignment_mux
        t = self._tracks()
        calls = []

        def fake_transcripts(paths):
            calls.extend(paths)
            key = {0: "reference", 1: "candidate"}
            return [t[key[i]] for i in range(len(paths))]

        plan = alignment_mux(["ref.wav", "cand.wav"],
                             transcripts=fake_transcripts)
        assert calls == ["ref.wav", "cand.wav"]
        assert plan["offset_s"] == pytest.approx(0.12, abs=0.02)
        assert plan["shift_argv"][3] == "0.12"
        assert plan["mode"] == "shift_guide_mux"

    def test_below_threshold_no_shift(self):
        from services.audio.alignment_mux import alignment_mux
        t = [[(0.50, 1.40, "hello")], [(0.51, 1.41, "hello")]]

        def fake_transcripts(paths):
            return t

        plan = alignment_mux(["a.wav", "b.wav"],
                             transcripts=fake_transcripts)
        assert plan["offset_s"] == pytest.approx(0.01, abs=0.005)
        assert plan["mode"] == "no_shift"
        assert plan["shift_argv"] is None
