"""Night two convergence — the second wave of live-run fixes
(2026-09-03 strict FL2VA chain attempt, all live-verified on the
3090 before landing here).

The acceptance test (TestNight2Acceptance) is the gate: a dry-run +
fake-host golden for the exact 2-clip strict chain (clip 1 Ref2VA
56f, clip 2 first_frame_continuation FL2VA) — clip 2's emitted
settings carry image_start (the materialized frame path), the
FL2VA-lane route hits the DETACHED seam argv, and
poll_render_completion accepts a faked 20/20 log. Every pre-fix
defect fails it.
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
LOG_20_20 = "loading model\nDenoising 20/20\nQueue completed: 1/1"


class _FakeHost:
    """Scripted host seam: probes recorded; the detached launch seeds
    the faked 20/20 render.log for the settings path it carries."""

    def __init__(self, log_text=LOG_20_20):
        import re as _re
        self.calls = []
        self.files = {}  # path -> text served to `cat`
        self._log_text = log_text
        self._proc_re = _re.compile(r"--process (\S+) --profile")

    def run_probe(self, argv, timeout=30):
        self.calls.append(list(argv))
        if len(argv) == 1 and argv[0].startswith("setsid nohup"):
            m = self._proc_re.search(argv[0])
            if m:
                log = m.group(1).rsplit("/", 1)[0] + "/render.log"
                self.files[log] = self._log_text
            return 0, "launched", ""
        if argv[:1] == ["cat"] and len(argv) == 2:
            return 0, self.files.get(argv[1], ""), ""
        return 0, "out.mp4\n", ""

    # adapter render-path niceties (never needed on the fl2va seam)
    def map_path(self, path):
        return path


# ── FIX 1: FL2VA lane rides the detached production seam ──────────────

class TestFix1Fl2vaDetachedSeam:
    def test_fl2va_job_emits_one_element_detached_argv(self, tmp_path):
        from host.wangp_adapter import WanGPAdapter
        host = _FakeHost()
        host.files["/r/render.log"] = LOG_20_20
        adapter = WanGPAdapter(host=host, output_dir=str(tmp_path))
        job = {"kind": "first_frame_continuation", "prompt": "p",
               "frames": 56,
               "image_start": "chain_last_frame.png"}
        res = adapter.render_for_job(job)
        assert res.lane == "fl2va"
        # ONE pre-joined detached element: setsid nohup ... flock ... bash -c
        detached = [c for c in host.calls
                    if len(c) == 1 and c[0].startswith("setsid nohup")]
        assert len(detached) == 1
        argv = detached[0][0]
        assert "flock /tmp/wgp_queue.lock" in argv
        assert "bash -c" in argv
        assert argv.rstrip().endswith("& echo launched")
        assert "--process" in argv and "--profile 3" in argv
        # run_dir mkdir fired before the launch
        mkdirs = [c for c in host.calls if c[:2] == ["mkdir", "-p"]]
        assert mkdirs, "run dir must be created before the launch"
        first_detached = host.calls.index(detached[0])
        assert any(host.calls.index(m) < first_detached for m in mkdirs)
        # verify-before-trust ran: the 20/20 log was read (cat) and the
        # newest output copied to the job target
        cats = [c for c in host.calls if c[:1] == ["cat"]]
        assert any(len(c) == 2 and c[1].endswith("render.log")
                   for c in cats)
        cps = [c for c in host.calls
               if c[:1] == ["cp"] and c[1].endswith("out.mp4")]
        assert cps and cps[0][2].endswith("output.mp4")

    def test_continuation_kind_routes_fl2va_then_hardened_path(self):
        from host.wangp_adapter import FL2VA_LANE, job_lane
        assert job_lane({"kind": "first_frame_continuation"}) == FL2VA_LANE

    def test_legacy_render_never_fires_for_fl2va_job(self, tmp_path,
                                                     monkeypatch):
        from host.wangp_adapter import WanGPAdapter
        legacy = []
        monkeypatch.setattr(
            WanGPAdapter, "render",
            lambda self, *a, **kw: legacy.append(a))
        host = _FakeHost()
        host.files["/r/render.log"] = LOG_20_20
        adapter = WanGPAdapter(host=host, output_dir=str(tmp_path))
        adapter.render_for_job({"kind": "first_frame_continuation",
                                "prompt": "p"})
        assert legacy == []

    def test_incomplete_log_rejected(self, tmp_path):
        from host.wangp_adapter import WanGPAdapter, WanGPError
        host = _FakeHost(log_text="Denoising 12/20\n")
        adapter = WanGPAdapter(
            host=host, output_dir=str(tmp_path),
            sleeper=lambda s: None)
        # drain the poll loop's stall budget fast: shrink the watchdog
        monkeypatch_env = {"WANGP_LOAD_STALL_S": "0.05",
                           "WANGP_QC_URL": "http://127.0.0.1:1/health"}
        old = {k: os.environ.get(k) for k in monkeypatch_env}
        os.environ.update(monkeypatch_env)
        try:
            with pytest.raises(WanGPError):
                adapter.render_for_job(
                    {"kind": "first_frame_continuation", "prompt": "p"})
        finally:
            for k, v in old.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v


# ── FIX 2: localhost_pre_render shape ─────────────────────────────────

class TestFix2LocalhostPreRender:
    def _patch_subprocess(self, monkeypatch, curl_ok=None):
        """Patch subprocess.run inside run_jobs; record argv lists."""
        import scripts.run_jobs as rj
        ran = []

        class _P:
            def __init__(self, rc):
                self.returncode = rc

        def fake_run(argv, capture_output=True, timeout=60, **kw):
            ran.append(list(argv))
            if argv and argv[0] == "curl":
                ok = curl_ok() if callable(curl_ok) else curl_ok
                return _P(0 if ok else 1)
            return _P(0)

        import subprocess
        monkeypatch.setattr(subprocess, "run", fake_run)
        return ran

    def test_fallback_argv_and_health_wait(self, monkeypatch):
        import scripts.run_jobs as rj
        monkeypatch.setenv("WANGP_QC_URL", "http://localhost:8000/health")
        # health fails on the first probe, passes afterwards
        state = {"healthy": False}

        def flip():
            if state["healthy"]:
                return True
            state["healthy"] = True
            return False

        ran = self._patch_subprocess(monkeypatch, curl_ok=flip)
        monkeypatch.setattr(rj, "_LLAMA_HEALTH_RETRIES", 3)
        monkeypatch.setattr(rj, "_LLAMA_HEALTH_INTERVAL_S", 0.0)
        rj.localhost_pre_render({"clip_index": 1})
        curl = [a for a in ran if a and a[0] == "curl"]
        assert curl and curl[0][1:3] == ["-fsS", "-m"]
        assert curl[0][-1] == "http://localhost:8000/health"
        # health waited: at least 2 curl probes (one fail, one pass)
        assert len(curl) >= 2
        # systemd attempt fired
        assert ["systemctl", "--user", "start", "qc-stack"] in ran

    def test_fallback_launches_llama_server_when_unhealthy(self,
                                                            monkeypatch):
        import scripts.run_jobs as rj
        # health NEVER passes -> direct llama-server fallback fires
        ran = self._patch_subprocess(monkeypatch, curl_ok=False)
        monkeypatch.setattr(rj, "_LLAMA_HEALTH_RETRIES", 1)
        monkeypatch.setattr(rj, "_LLAMA_HEALTH_INTERVAL_S", 0.0)
        rj.localhost_pre_render({"clip_index": 1})
        launches = [a for a in ran
                    if "llama-server" in " ".join(map(str, a))]
        assert launches, "direct llama-server fallback must fire"
        joined = " ".join(map(str, launches[0]))
        assert "setsid" in joined and "nohup" in joined
        assert "llama-server.log" in joined
        assert joined.rstrip().endswith("&")

    def test_no_pkill_in_pre_render_phase(self, monkeypatch):
        import scripts.run_jobs as rj
        ran = self._patch_subprocess(monkeypatch, curl_ok=True)
        rj.localhost_pre_render({"clip_index": 1})
        assert not [a for a in ran
                    if "pkill" in " ".join(map(str, a))], \
            "pre-preflight phase must NOT kill (kill is render-leg)"

    def test_llama_server_argv_shape(self):
        import scripts.run_jobs as rj
        argv = rj.llama_server_argv()
        assert argv[:3] == ["setsid", "nohup", "llama-server"]
        assert argv[-1].endswith("&")


# ── FIX 3: render-leg free_vram_for_render ────────────────────────────

class TestFix3RenderLegKill:
    def _wire(self, monkeypatch):
        """Wire build_executor with a fake adapter class + fake log
        reader so ex.render() exercises the localhost VRAM kill."""
        import scripts.run_jobs as rj
        from services.jobs.executor import RenderOutcome
        killed = []
        adapter_calls = []

        class _ProbeHost:
            def run_probe(self, argv, timeout=30):
                killed.append(list(argv))
                return 0, "", ""

        class _Adapter:
            def __init__(self, host=None):
                pass

            def render_for_job(self, clip):
                adapter_calls.append(clip["clip_index"])
                return RenderOutcome(
                    mp4="m.mp4", log_text="Denoising 20/20",
                    log_path="render.log")

        import host.wangp_adapter as _wa
        monkeypatch.setattr(_wa, "WanGPAdapter", _Adapter)
        monkeypatch.setattr(rj, "_read_host_log",
                            lambda host, log: "Denoising 20/20")
        return rj, killed, _ProbeHost

    def test_render_wrapper_kills_pre_render_localhost_only(self,
                                                            monkeypatch):
        rj, killed, _ProbeHost = self._wire(monkeypatch)
        monkeypatch.setenv("WANGP_SSH_TARGET", "localhost")
        ex = rj.build_executor(queue=None, host=_ProbeHost())
        outcome = ex.render({"clip_index": 1})
        assert outcome.log_text == "Denoising 20/20"
        pkills = [c for c in killed if c[:2] == ["pkill", "-f"]]
        assert pkills and pkills[0][2] == "llama-server"
        assert [c for c in killed if c[:1] == ["sleep"]]

        # remote lane: no kill
        killed.clear()
        monkeypatch.setenv("WANGP_SSH_TARGET", "3090")
        ex2 = rj.build_executor(queue=None, host=_ProbeHost())
        ex2.render({"clip_index": 2})
        assert not [c for c in killed if c and c[0] == "pkill"], \
            "remote lane must not run the localhost VRAM dance"

    def test_free_vram_for_render_argv(self):
        import scripts.run_jobs as rj
        seen = []

        class _H:
            def run_probe(self, argv, timeout=30):
                seen.append(list(argv))
                return 0, "", ""

        rj.free_vram_for_render(_H())
        assert seen[0][:2] == ["pkill", "-f"]
        assert seen[0][2] == "llama-server"
        assert seen[1] == ["sleep", "3"]


# ── FIX 4: pre_render fires BEFORE preflight ──────────────────────────

class TestFix4PreRenderBeforePreflight:
    def test_hook_called_before_preflight_probe(self):
        from services.jobs.executor import JobExecutor
        order = []

        class _Q:
            def set_state(self, jid, st):
                order.append(("state", st))

            def get(self, jid):
                return type("J", (), {"job_id": jid, "state": "pending",
                                      "clips": [{"clip_index": 1,
                                                 "kind": None}]})()

        ok = type("R", (), {"passed": True, "detail": ""})()
        ex = JobExecutor(
            queue=_Q(),
            preflight=lambda job: order.append("preflight") or ok,
            render=lambda c: None, qc=lambda c: (True, "qc.json"),
            pre_render=lambda clip: order.append("pre_render"))
        job = _Q().get("j1")
        ex._drive(job, "j1")
        # pending phase: pre_render fires BEFORE the preflight probe
        assert order.index("pre_render") < order.index("preflight")


# ── FIX 5: Ref2VAProfile 56f floor ────────────────────────────────────

class TestFix5Ref2vaFloor:
    def _profile(self):
        from predict.render_profiles import Ref2VAProfile
        return Ref2VAProfile()

    def test_floor_is_2_33(self):
        from predict.render_profiles import REF2VA_MIN_SHOT_S
        from fractions import Fraction
        assert REF2VA_MIN_SHOT_S == 2.33
        assert REF2VA_MIN_SHOT_S < float(Fraction(56, 24))

    def test_2_333_passes_2_32_fails_15_passes(self):
        assert self._profile() is not None  # profile constructs
        # direct boundary assertions on the module constants used by
        # build_settings' cap check
        from predict.render_profiles import (
            REF2VA_MIN_SHOT_S, REF2VA_MAX_SHOT_S)
        assert REF2VA_MIN_SHOT_S <= 2.333 <= REF2VA_MAX_SHOT_S
        assert not (REF2VA_MIN_SHOT_S <= 2.32)
        assert REF2VA_MIN_SHOT_S <= 15.0 <= REF2VA_MAX_SHOT_S

    def test_settings_build_accepts_2_333(self, tmp_path):
        from predict.render_profiles import Ref2VAProfile, ProfileError
        from predict.prompt_director import RenderBrief
        from predict.profile_selector import ProfileDecision
        from predict.audio_dataplane import AudioGuideProvenance
        img = tmp_path / "p.png"
        img.write_bytes(b"x")
        wav = tmp_path / "g.wav"
        wav.write_bytes(b"x")
        brief = RenderBrief(subject="s", motion="m", camera="c",
                            style="st")
        dec = ProfileDecision(model="h3", resolution="768p",
                              shot_length_frames=56,
                              seed_policy="fixed_per_shot",
                              wangp_profile="profile3")
        prov = AudioGuideProvenance(
            source_master=str(wav), vocal_stem=str(wav),
            whisper_map=str(wav), keeper_window_s=(0.0, 2.333))
        doc = Ref2VAProfile().build_settings(
            [brief], dec, image_refs=[str(img)],
            audio_prompt_type="A", guide_duration_s=2.333,
            shot_duration_s=2.333, audio_guide=str(wav),
            audio_provenance=prov, audio_length_frames=56)
        assert doc["frames_per_shot"] == 107  # 5+17k grid snap
        assert doc["requested_frames"] == 56  # FIX 6 below
        assert doc["video_length"] == 107    # snapped (FIX 6)

    def test_2_32_rejected(self, tmp_path):
        from predict.render_profiles import Ref2VAProfile, ProfileError
        from predict.prompt_director import RenderBrief
        from predict.profile_selector import ProfileDecision
        from predict.audio_dataplane import AudioGuideProvenance
        img = tmp_path / "p.png"
        img.write_bytes(b"x")
        wav = tmp_path / "g.wav"
        wav.write_bytes(b"x")
        brief = RenderBrief(subject="s", motion="m", camera="c",
                            style="st")
        dec = ProfileDecision(model="h3", resolution="768p",
                              shot_length_frames=56,
                              seed_policy="fixed_per_shot",
                              wangp_profile="profile3")
        prov = AudioGuideProvenance(
            source_master=str(wav), vocal_stem=str(wav),
            whisper_map=str(wav), keeper_window_s=(0.0, 2.32))
        with pytest.raises(ProfileError, match="cap"):
            Ref2VAProfile().build_settings(
                [brief], dec, image_refs=[str(img)],
                audio_prompt_type="A", guide_duration_s=2.32,
                shot_duration_s=2.32, audio_guide=str(wav),
                audio_provenance=prov)


# ── FIX 6: snapped video_length + requested_frames ────────────────────

class TestFix6SnappedFrames:
    def test_56f_request_emits_snapped_video_length(self, tmp_path):
        from host.wangp_adapter import (
            WanGPAdapter, _build_fl2va_settings_doc,
            _default_fl2va_decision)
        host = _FakeHost()
        adapter = WanGPAdapter(host=host, output_dir=str(tmp_path))
        job = {"kind": "first_frame_continuation", "prompt": "p",
               "frames": 56}
        dec = _default_fl2va_decision(job)
        settings, requested = _build_fl2va_settings_doc(job, dec)
        assert requested == 56
        assert settings["requested_frames"] == 56
        assert settings["video_length"] == 107  # 5+17k snap
        # frames_per_shot itself snapped by WanGPJobConfig
        assert settings["frames_per_shot"] == 107

    def test_ref2va_profile_snaps_video_length(self, tmp_path):
        from predict.render_profiles import Ref2VAProfile
        from predict.prompt_director import RenderBrief
        from predict.profile_selector import ProfileDecision
        from predict.audio_dataplane import AudioGuideProvenance
        img = tmp_path / "p.png"
        img.write_bytes(b"x")
        wav = tmp_path / "g.wav"
        wav.write_bytes(b"x")
        brief = RenderBrief(subject="s", motion="m", camera="c",
                            style="st")
        dec = ProfileDecision(model="h3", resolution="768p",
                              shot_length_frames=56,
                              seed_policy="fixed_per_shot",
                              wangp_profile="profile3")
        prov = AudioGuideProvenance(
            source_master=str(wav), vocal_stem=str(wav),
            whisper_map=str(wav), keeper_window_s=(0.0, 2.333))
        doc = Ref2VAProfile().build_settings(
            [brief], dec, image_refs=[str(img)],
            audio_prompt_type="A", guide_duration_s=2.333,
            shot_duration_s=2.333, audio_guide=str(wav),
            audio_provenance=prov, audio_length_frames=56)
        assert doc["video_length"] == 107
        assert doc["requested_frames"] == 56


# ── FIX 7: WANGP_SSH_TARGET env override ──────────────────────────────

class TestFix7EnvTarget:
    def test_env_override_yields_localhost_sshhost(self, monkeypatch):
        import scripts.run_jobs as rj
        from host.render_host import SshHost
        monkeypatch.setenv("WANGP_SSH_TARGET", "localhost")
        h = rj._default_host()
        assert isinstance(h, SshHost)
        assert h.target == "localhost"

    def test_default_unchanged(self, monkeypatch):
        import scripts.run_jobs as rj
        monkeypatch.delenv("WANGP_SSH_TARGET", raising=False)
        assert rj._default_host().target == "3090"


# ── FIX 8: no SyntaxWarning in job_config ─────────────────────────────

class TestFix8SyntaxWarning:
    def test_job_config_compiles_clean(self):
        import warnings
        src = open("predict/job_config.py", encoding="utf-8").read()
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            compile(src, "job_config.py", "exec")
        bad = [x for x in w
               if "invalid escape" in str(x.message).lower()]
        assert bad == []


# ── ACCEPTANCE: the strict-chain 2-clip golden ────────────────────────

class TestNight2Acceptance:
    def test_two_clip_strict_chain_golden(self, tmp_path, monkeypatch):
        """The exact path the strict run needs: clip 1 Ref2VA 56f,
        clip 2 first_frame_continuation FL2VA on the detached seam,
        with clip 2's settings carrying image_start and
        poll_render_completion accepting a faked 20/20 log."""
        from services.director.wiring import plan_to_clips
        from host.wangp_adapter import (
            FL2VA_LANE, REF2VA_LANE, WanGPAdapter, job_lane,
            verify_denoise_steps)

        # dry-run plan: clip 1 via the proven plan_to_clips (56f)
        monkeypatch.chdir(tmp_path)
        clips = plan_to_clips(
            [{"speaker": "Grandma", "text": "Sit down, boy."},
             {"speaker": "Seth", "text": "Ma'am."}],
            CHARACTERS,
            {"anchor": str(tmp_path / "a.png"),
             "Grandma": str(tmp_path / "g.png"),
             "Seth": str(tmp_path / "s.png")},
            durations=[2.333, 2.333], whisper_map=WHISPER_MAP,
            run_dir=str(tmp_path / "run"))
        assert len(clips) == 2
        clip1, clip2 = clips
        assert job_lane(clip1) == REF2VA_LANE
        assert clip1["frames"] == 56

        # clip 2 as the strict chain emits it: continuation kind,
        # materialized frame path in image_start
        cont = {
            "clip_index": 2,
            "kind": "first_frame_continuation",
            "prompt": clip2["prompt"],
            "frames": 56,
            "image_start": {
                "kind": "last_frame", "clip_index": 1,
                "frame": str(tmp_path / "run/render/clip0001/"
                                     "chain_last_frame.png"),
            },
        }
        assert job_lane(cont) == FL2VA_LANE

        # fake host: the detached launch seeds the faked 20/20
        # render.log for the settings path it carries (see _FakeHost);
        # the newest output listing returns one strict-run mp4
        host = _FakeHost()
        _orig_probe = host.run_probe

        def run_probe(argv, timeout=30):
            if argv[:2] == ["ls", "-t"]:
                host.calls.append(list(argv))
                return 0, "strict_0002.mp4\n", ""
            return _orig_probe(argv, timeout=timeout)

        host.run_probe = run_probe
        adapter = WanGPAdapter(host=host, output_dir=str(tmp_path))

        # clip 2 executes on the FL2VA lane through the hardened seam
        res2 = adapter.render_for_job(dict(cont))
        assert res2.lane == FL2VA_LANE
        # emitted settings carry image_start (materialized frame path)
        with open(res2.settings_path, encoding="utf-8") as f:
            settings = json.load(f)
        assert settings["image_start"] == cont["image_start"]["frame"]
        assert settings["requested_frames"] == 56
        assert settings["video_length"] == 107
        # the detached seam argv fired (one element, setsid+flock)
        detached = [c for c in host.calls
                    if len(c) == 1 and c[0].startswith("setsid nohup")]
        assert len(detached) == 1
        assert "flock /tmp/wgp_queue.lock" in detached[0][0]
        # poll accepted the faked 20/20 log
        assert verify_denoise_steps(LOG_20_20, 20)
        # output copied to the job target
        cps = [c for c in host.calls
               if c[:1] == ["cp"] and c[1].endswith("strict_0002.mp4")]
        assert cps and cps[0][2].endswith("output.mp4")
        assert res2.video_path.endswith("output.mp4")
