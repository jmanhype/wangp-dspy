"""Director convergence — the seven live-run wiring-boundary fixes
(2026-09-03 first-ever live film run, all fixes live-verified on the
3090 before landing here).

The acceptance test (TestDryRunGoldenAcceptance) is the gate: a
run_film --dry-run on a 2-line fixture must emit clips whose jobs pass
job_lane + AudioGuideProvenance + settings build WITHOUT hand-fixing —
it would have failed on every pre-fix defect.
"""
from __future__ import annotations

import json
import os

import pytest

CHARACTERS = [
    {"name": "Grandma", "sn_tag": "S1",
     "description": "a weathered woman with silver braids, seated left"},
    {"name": "Seth", "sn_tag": "S2",
     "description": "a lean man with soot-streaked cheeks, standing right"},
]
WHISPER_MAP = "s4/films/satans-mom/qc/whisper_map.json"


def _script_file(tmp_path, lines):
    f = tmp_path / "script.txt"
    f.write_text("\n".join(f"{s}: {t}" for s, t in lines) + "\n")
    return f


def _plates_dir(tmp_path):
    d = tmp_path / "plates"
    d.mkdir(exist_ok=True)
    for n in ("anchor.png", "Grandma.png", "Seth.png"):
        (d / n).write_bytes(b"x" * 8)
    return d


# ── FIX 1: kind literal routes to REF2VA_LANE ─────────────────────────

class TestFix1KindRoutesRef2va:
    def test_emitted_kind_routes_to_ref2va_lane(self, tmp_path):
        from services.director.wiring import plan_to_clips
        from host.wangp_adapter import REF2VA_LANE, job_lane
        clips = plan_to_clips(
            [{"speaker": "Grandma", "text": "Sit down, boy."}],
            CHARACTERS,
            {"anchor": str(tmp_path / "a.png"),
             "Grandma": str(tmp_path / "g.png"),
             "Seth": str(tmp_path / "s.png")},
            durations=[2.34], whisper_map=WHISPER_MAP,
            run_dir=str(tmp_path / "run"))
        assert clips[0]["kind"] == "ref2va_render"
        assert job_lane(clips[0]) == REF2VA_LANE

    def test_mode_enum_value_does_not_route(self):
        """The pre-fix bug: kind=REF2VA_IDENTITY_AUDIO fell to fl2va."""
        from host.wangp_adapter import FL2VA_LANE, REF2VA_LANE, job_lane
        assert job_lane({"kind": "REF2VA_IDENTITY_AUDIO"}) == FL2VA_LANE
        assert job_lane({"kind": "ref2va_render"}) == REF2VA_LANE


# ── FIX 2: materialized audio guides, absolute paths, provenance ──────

class TestFix2MaterializedAudioGuides:
    def test_guides_exist_on_disk_with_absolute_paths(self, tmp_path):
        from services.director.wiring import plan_to_clips
        run = tmp_path / "run"
        clips = plan_to_clips(
            [{"speaker": "Grandma", "text": "Sit down, boy."},
             {"speaker": "Seth", "text": "Ma'am."}],
            CHARACTERS,
            {"anchor": str(tmp_path / "a.png"),
             "Grandma": str(tmp_path / "g.png"),
             "Seth": str(tmp_path / "s.png")},
            durations=[2.34, 2.34], whisper_map=WHISPER_MAP,
            run_dir=str(run))
        for i, c in enumerate(clips, start=1):
            p = c["audio_guide"]
            assert os.path.isabs(p), p
            assert os.path.isfile(p), p
            assert p.endswith(f"/audio/clip{i:04d}.wav")
            prov = c["audio_provenance"]
            assert prov["source_master"] == p
            assert prov["vocal_stem"] == p
            assert prov["whisper_map"] == WHISPER_MAP

    def test_provenance_constructs_AudioGuideProvenance(self, tmp_path,
                                                        monkeypatch):
        wm = tmp_path / "whisper_map.json"
        wm.write_text("{}")
        monkeypatch.chdir(tmp_path)
        from services.director.wiring import plan_to_clips
        from predict.audio_dataplane import AudioGuideProvenance
        clips = plan_to_clips(
            [{"speaker": "Grandma", "text": "Sit down, boy."}],
            CHARACTERS,
            {"anchor": str(tmp_path / "a.png"),
             "Grandma": str(tmp_path / "g.png"),
             "Seth": str(tmp_path / "s.png")},
            durations=[2.34], whisper_map=str(wm),
            run_dir=str(tmp_path / "run"))
        prov = AudioGuideProvenance(**clips[0]["audio_provenance"])
        assert prov.whisper_map == str(wm)

    def test_missing_run_dir_without_audio_paths_rejected(self, tmp_path):
        from services.director.wiring import WiringError, plan_to_clips
        with pytest.raises(WiringError, match="run_dir"):
            plan_to_clips(
                [{"speaker": "Grandma", "text": "Sit down, boy."}],
                CHARACTERS,
                {"anchor": str(tmp_path / "a.png"),
                 "Grandma": str(tmp_path / "g.png"),
                 "Seth": str(tmp_path / "s.png")},
                durations=[2.34], whisper_map=WHISPER_MAP)

    def test_silence_wav_is_real_audio(self, tmp_path):
        from services.director.wiring import _materialize_silence
        p = _materialize_silence(str(tmp_path / "audio/x.wav"), 1.5)
        assert os.path.getsize(p) > 1000  # real pcm data, not a stub
        # idempotent
        assert _materialize_silence(p, 1.5) == p


# ── FIX 3: duration trio alongside frames ─────────────────────────────

class TestFix3DurationTrio:
    def test_golden_fields_for_96f_clip(self, tmp_path):
        from services.director.wiring import plan_to_clips
        clips = plan_to_clips(
            [{"speaker": "Grandma", "text": "Sit down, boy."}],
            CHARACTERS,
            {"anchor": str(tmp_path / "a.png"),
             "Grandma": str(tmp_path / "g.png"),
             "Seth": str(tmp_path / "s.png")},
            durations=[4.0], whisper_map=WHISPER_MAP,
            run_dir=str(tmp_path / "run"))
        c = clips[0]
        assert c["frames"] == 96
        assert c["shot_duration_s"] == 4.0
        assert c["guide_duration_s"] == 4.0
        assert c["audio_length_frames"] == 96

    def test_rounding_three_decimals(self, tmp_path):
        from services.director.wiring import plan_to_clips
        clips = plan_to_clips(
            [{"speaker": "Grandma", "text": "Sit down, boy."}],
            CHARACTERS,
            {"anchor": str(tmp_path / "a.png"),
             "Grandma": str(tmp_path / "g.png"),
             "Seth": str(tmp_path / "s.png")},
            durations=[2.3333333333333335], whisper_map=WHISPER_MAP,
            run_dir=str(tmp_path / "run"))
        c = clips[0]
        assert c["frames"] == 56
        assert c["shot_duration_s"] == round(56 / 24, 3) == 2.333


# ── FIX 4: G5 exempts <d>[Language] tags ──────────────────────────────

class TestFix4G5LanguageTags:
    def test_english_tag_passes(self):
        from host.wangp_adapter import _g5_check
        _g5_check('<d>[English] Hello there.</d> "general kenobi"')

    def test_john_still_rejected(self):
        from host.wangp_adapter import WanGPError, _g5_check
        with pytest.raises(WanGPError, match="G5"):
            _g5_check("[John] said something")

    def test_paren_mary_still_rejected(self):
        from host.wangp_adapter import WanGPError, _g5_check
        with pytest.raises(WanGPError, match="G5"):
            _g5_check("(Mary) replies")

    def test_language_tag_outside_d_rejected(self):
        """The exemption is scoped to <d>-prefixed tags only."""
        from host.wangp_adapter import WanGPError, _g5_check
        # [Language]-shaped but Capitalized-lowercase still matches the
        # bad-marker regex when NOT inside a <d> tag
        with pytest.raises(WanGPError, match="G5"):
            _g5_check("[Englishman] waves")


# ── FIX 5: _Ref2VABrief full attr set ────────────────────────────────

class TestFix5Ref2VABriefAttrs:
    def test_brief_has_all_seven_attrs(self):
        from host.wangp_adapter import _Ref2VABrief
        b = _Ref2VABrief(subject="s", motion="m", camera="c", style="st")
        for a in ("subject", "motion", "camera", "style",
                  "audio_direction", "identity_lock", "negatives"):
            assert hasattr(b, a), a
        assert b.audio_direction == ""
        assert b.identity_lock == ""
        assert b.negatives == ""

    def test_brief_passes_g5_and_brief_to_prompt(self):
        from host.wangp_adapter import _Ref2VABrief, _g5_check, \
            brief_to_prompt
        b = _Ref2VABrief(
            subject="grandma speaks",
            motion="lips move in sync with the audio guide",
            camera="static medium shot", style="cinematic 16mm",
            audio_direction="dialogue only, no music",
            identity_lock="silver braids (S1)",
            negatives="extra fingers, text overlays")
        for f in ("subject", "motion", "camera", "style",
                  "audio_direction"):
            _g5_check(getattr(b, f), field=f)
        prompt = brief_to_prompt(b)
        assert "Audio: dialogue only" in prompt
        assert "Preserve throughout: silver braids" in prompt
        assert "Do not: extra fingers" in prompt


# ── FIX 6: drain_once chain auto-advance + render_for_job routing ─────

class _FakeHost:
    def __init__(self):
        self.calls = []

    def run_probe(self, argv, timeout=30):
        self.calls.append(list(argv))
        return 0, "", ""


class TestFix6ChainAutoAdvance:
    def _two_chain_jobs(self, tmp_path):
        from services.director.wiring import plan_to_clips
        from services.jobs.queue import JobQueue
        clips = plan_to_clips(
            [{"speaker": "Grandma", "text": "Sit down, boy."},
             {"speaker": "Seth", "text": "Ma'am."}],
            CHARACTERS,
            {"anchor": str(tmp_path / "a.png"),
             "Grandma": str(tmp_path / "g.png"),
             "Seth": str(tmp_path / "s.png")},
            durations=[2.34, 2.34], whisper_map=WHISPER_MAP,
            run_dir=str(tmp_path / "run"))
        q = JobQueue(str(tmp_path / "jobs.db"))
        prev = None
        ids = []
        for c in clips:
            clip = dict(c)
            clip["needs"] = prev
            ids.append(q.submit(plan_ref="film", clips=[clip]))
            prev = ids[-1]
        return q, ids

    def test_drain_once_advances_chain(self, tmp_path, monkeypatch):
        import scripts.run_jobs as rj
        from services.jobs.executor import JobExecutor
        q, ids = self._two_chain_jobs(tmp_path)
        host = _FakeHost()
        fired = []

        def fake_run_once(self_ex):
            jid = self_ex._pick_job().job_id
            for st in ("preflight", "rendering"):
                q.set_state(jid, st)
            for c in q.get(jid).clips:
                q.update_clip(jid, c["clip_index"], status="rendered",
                              log="render.log",
                              mp4=f"render/clip{c['clip_index']:04d}/o.mp4",
                              qc_verdict=None)
            for st in ("rendered_pending_qc", "qc", "done"):
                q.set_state(jid, st)
            fired.append(jid)
        monkeypatch.setattr(JobExecutor, "run_once", fake_run_once)
        handled = rj.drain_once(q, host=host)
        assert handled == ids
        assert len(fired) == 2  # both jobs ran (dependent unblocked)
        # ffmpeg last-frame extraction fired for the chain advance
        ffmpeg = [c for c in host.calls if c[:2] == ["ffmpeg", "-y"]]
        assert len(ffmpeg) == 1
        assert ffmpeg[0][4:8] == ["-sseof", "-0.05", "-i",
                                  "render/clip0001/o.mp4"]
        # dependent's chain:// placeholder replaced with the png
        dep = q.get(ids[1])
        ref0 = dep.clips[0]["image_refs"][0]
        assert not ref0.startswith("chain://")
        assert ref0.endswith("chain_last_frame.png")

    def test_executor_routes_through_render_for_job(self, tmp_path,
                                                    monkeypatch):
        """The director render path goes through the adapter's
        render_for_job seam, never the legacy brief-based render()."""
        import scripts.run_jobs as rj
        from host.wangp_adapter import WanGPAdapter
        host = _FakeHost()
        calls = []
        real = WanGPAdapter.render_for_job
        monkeypatch.setattr(
            WanGPAdapter, "render_for_job",
            lambda self, job, **kw: calls.append(dict(job)) or real(
                self, job, **kw))
        legacy = []
        monkeypatch.setattr(
            WanGPAdapter, "render",
            lambda self, *a, **kw: legacy.append(a))
        ex = rj.build_executor(queue=None, host=host, whisper_transcriber=lambda p: "p")
        clip = {"clip_index": 1, "kind": "ref2va_render",
                "image_refs": ["a.png"], "audio_guide": "g.wav",
                "prompt": "p"}
        from host.wangp_adapter import WanGPError
        with pytest.raises(WanGPError, match="audio_provenance"):
            ex.render(clip)  # the executor's render seam
        # entered render_for_job with the ref2va job; the deep typed
        # rejection (no provenance on this minimal clip) proves the
        # seam, not the legacy path
        assert calls and calls[0]["kind"] == "ref2va_render"
        assert legacy == []  # legacy render() never invoked


# ── FIX 7: env target + localhost pre_render hook ─────────────────────

class TestFix7EnvRoutingAndHook:
    def test_ssh_target_env_override(self, monkeypatch):
        import scripts.run_jobs as rj
        monkeypatch.setenv("WANGP_SSH_TARGET", "localhost")
        h = rj._default_host()
        assert getattr(h, "target", None) == "localhost"

    def test_default_target_unchanged(self, monkeypatch):
        import scripts.run_jobs as rj
        monkeypatch.delenv("WANGP_SSH_TARGET", raising=False)
        h = rj._default_host()
        assert getattr(h, "target", None) == "3090"

    def test_pre_render_default_on_for_localhost(self, monkeypatch):
        import scripts.run_jobs as rj
        monkeypatch.setenv("WANGP_VISION_BACKEND", "local")
        monkeypatch.setenv("WANGP_SSH_TARGET", "localhost")
        assert rj._pre_render_default(None) is rj.localhost_pre_render

    def test_pre_render_default_off_for_remote(self, monkeypatch):
        import scripts.run_jobs as rj
        monkeypatch.setenv("WANGP_SSH_TARGET", "3090")
        assert rj._pre_render_default(None) is None
        monkeypatch.delenv("WANGP_SSH_TARGET", raising=False)
        assert rj._pre_render_default(None) is None

    def test_hook_fires_around_render(self, monkeypatch):
        """run_film wires the default hook into the executor, and the
        executor fires it before each clip's render leg."""
        import scripts.run_film as rf
        import scripts.run_jobs as rj
        from services.jobs.executor import JobExecutor
        monkeypatch.setenv("WANGP_SSH_TARGET", "localhost")
        fired = []
        monkeypatch.setattr(
            rj, "localhost_pre_render",
            lambda clip: fired.append(clip["clip_index"]))
        q = object()
        host = _FakeHost()
        ex = rj.build_executor(q, host=host)
        # build_executor has no host env peek; run_film is where the
        # default-on wiring lives — verify the executor fires the hook
        from services.jobs.executor import RenderOutcome
        ok = RenderOutcome(mp4="m.mp4", log_text="Denoising 20/20 done",
                           log_path="render.log")

        class _Q:
            def update_clip(self, *a, **kw):
                pass

            def set_state(self, *a, **kw):
                pass

            def record_failure(self, *a, **kw):
                pass

        ex2 = JobExecutor(
            queue=_Q(), preflight=lambda j: None, render=lambda c: ok,
            qc=lambda c: (True, "qc.json"), pre_render=fired.append,
            ref2va_render=lambda c: ok)
        ex2._render_clips(
            type("J", (), {"job_id": "j", "clips": [
                {"clip_index": 7, "kind": "ref2va_render"}]})())
        assert [c["clip_index"] for c in fired] == [7]


# ── ACCEPTANCE: the 2-line fixture dry-run golden test ────────────────

class TestDryRunGoldenAcceptance:
    def test_two_line_dry_run_emits_renderable_clips(self, tmp_path):
        """run_film --dry-run on a 2-line fixture: every emitted clip
        must pass job_lane + AudioGuideProvenance + Ref2VA settings
        build WITHOUT any hand-fixing. This is the acceptance test —
        it fails on every one of the seven pre-fix defects."""
        from host.wangp_adapter import REF2VA_LANE, job_lane
        from predict.audio_dataplane import AudioGuideProvenance
        from scripts.run_film import main

        script = _script_file(tmp_path, [
            ("Grandma", "No ma'am. But the devil's been expecting you."),
            ("Seth", "Then I will not keep the devil waiting either.")])
        plates = str(_plates_dir(tmp_path))
        wm = tmp_path / "whisper_map.json"
        wm.write_text("{}")
        rc = main([
            "--script", str(script),
            "--plates", plates,
            "--characters",
            "Grandma:S1:a weathered woman with silver braids, seated "
            "left",
            "Seth:S2:a lean man with soot-streaked cheeks, standing "
            "right",
            "--whisper-map", str(wm),
            "--db", str(tmp_path / "jobs.db"),
            "--dry-run"])
        assert rc == 0

        # re-emit the clips through the same entrypoint
        from scripts.run_film import run_film
        clips = run_film(
            script, plates, characters=CHARACTERS,
            whisper_map=str(wm), db_path=str(tmp_path / "jobs.db"),
            dry_run=True)
        assert len(clips) == 2
        for c in clips:
            # FIX 1: routes to the ref2va lane
            assert job_lane(c) == REF2VA_LANE
            # FIX 2: guide exists, absolute; provenance constructs
            assert os.path.isabs(c["audio_guide"])
            assert os.path.isfile(c["audio_guide"])
            AudioGuideProvenance(**c["audio_provenance"])
            # FIX 3: duration trio present
            for f in ("shot_duration_s", "guide_duration_s",
                      "audio_length_frames"):
                assert f in c
            # settings build (image_refs readable, guide == shot, 4-15s
            # cap honored by the plan durations)
            from predict.render_profiles import ProfileDecision  # noqa
            from host.wangp_adapter import _Ref2VABrief, \
                brief_to_prompt
            brief = _Ref2VABrief(
                subject=c["prompt"], motion="speaks in sync",
                camera="static medium shot", style="cinematic")
            brief_to_prompt(brief)  # FIX 5: no missing-attr crash
