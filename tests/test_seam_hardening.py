"""Seam hardening regression tests (PR feat/seam-hardening).

One live smoke run on the 3090 (2026-09-02) surfaced eleven defects,
each fixed ad-hoc on the box — these pin them in-repo, plus the two
systemic fixes (detached ssh-lifetime renders; wedged-model-load
watchdog). All fake hosts / fake clocks: NO GPU, NO SSH.
"""
import json
import os
import shlex
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from host.wangp_adapter import (
    DEFAULT_LOAD_STALL_S,
    DEFAULT_SANCTIONED_DIRS,
    WGP_QUEUE_LOCK,
    WanGPAdapter,
    WanGPError,
    WanGPLoadStallError,
    _host_path,
    build_detached_wgp_argv,
    build_wgp_lock_argv,
    default_sanctioned_dirs,
    poll_render_completion,
)
import host.wangp_adapter as adapter_mod
import predict.render_profiles as rp
from predict.render_profiles import ProfileError, Ref2VAProfile


class FakeHost:
    def __init__(self, responses=None):
        self.calls = []
        self.responses: dict = responses or {}

    def run_probe(self, argv, timeout=30):
        self.calls.append(list(argv))
        first = argv[0].split()[0] if isinstance(argv[0], str) else argv[0]
        if first in self.responses:
            return self.responses[first](self, argv)
        return 0, "", ""


# ── fix 4: the flock argv is ONE pre-joined, shlex-safe element ──────

class TestLockArgv:
    def test_single_element(self):
        argv = build_wgp_lock_argv("/run/s.json", "/run/render.log")
        assert isinstance(argv, list)
        assert len(argv) == 1
        assert isinstance(argv[0], str)

    def test_shlex_round_trip(self):
        argv = build_wgp_lock_argv("/run/s.json", "/run/render.log")
        parts = shlex.split(argv[0])
        assert parts[0] == "flock"
        assert parts[1] == WGP_QUEUE_LOCK
        assert parts[2] == "bash"
        assert parts[3] == "-c"
        inner = shlex.split(parts[4])
        assert inner[0] == "cd"

    def test_no_flock_dash_c_flag(self):
        argv = build_wgp_lock_argv("/run/s.json", "/run/render.log")
        assert " -c " not in argv[0].replace("bash -c", "BASH_C")

    def test_spaces_in_paths_quoted(self):
        argv = build_wgp_lock_argv("/run/my settings.json",
                                  "/run/my render.log")
        parts = shlex.split(argv[0])
        inner = shlex.split(parts[4])
        assert "/run/my settings.json" in inner

    def test_absolute_interpreter_and_script(self):
        argv = build_wgp_lock_argv("/run/s.json", "/run/render.log")
        inner = shlex.split(shlex.split(argv[0])[4])
        assert inner[1] == "/home/straughter/Wan2GP"
        py = [a for a in inner if a.endswith("/venv/bin/python")]
        wgp = [a for a in inner if a.endswith("/wgp.py")]
        assert py and py[0].startswith("/")
        assert wgp and wgp[0].startswith("/")
        assert "./venv" not in " ".join(inner)


# ── fix A: detached launch shape ─────────────────────────────────────

class TestDetachedLaunch:
    def test_detached_shape(self):
        argv = build_detached_wgp_argv("/run/s.json", "/run/render.log")
        assert len(argv) == 1
        s = argv[0]
        assert s.startswith("setsid nohup flock ")
        assert "& echo launched" in s
        # the inner command is still the (quoted) flock invocation
        assert "bash -c " in s

    def test_shlex_round_trip(self):
        argv = build_detached_wgp_argv("/run/s.json", "/run/render.log")
        parts = shlex.split(argv[0])
        assert parts[:2] == ["setsid", "nohup"]


# ── fix A: poll loop semantics (fake clocks) ─────────────────────────

class TestPollLoop:
    def _clock(self, responses=None):
        host = FakeHost(responses or {})
        t = {"t": 0.0}

        def now():
            return t["t"]

        def sleeper(s):
            t["t"] += max(s, 0.05)

        return host, now, sleeper

    def test_accepts_complete_log(self, monkeypatch):
        monkeypatch.setenv("WANGP_LOAD_STALL_S", "1")
        host, now, sleeper = self._clock(
            {"cat": lambda h, a: (0, "Denoising 20/20\n", "")})
        log = poll_render_completion(host, "/run/render.log", 20,
                                     timeout_s=60, sleeper=sleeper, now=now)
        assert "20/20" in log

    def test_rejects_truncated_log(self, monkeypatch):
        monkeypatch.setenv("WANGP_LOAD_STALL_S", "1")
        host, now, sleeper = self._clock(
            {"cat": lambda h, a: (0, "Denoising 12/20\nKilled", "")})
        with pytest.raises(WanGPError, match="mid-denoise crash"):
            poll_render_completion(host, "/run/render.log", 20,
                                   timeout_s=60, sleeper=sleeper, now=now)

    def test_times_out(self, monkeypatch):
        monkeypatch.setenv("WANGP_LOAD_STALL_S", "100000")
        host, now, sleeper = self._clock(
            {"cat": lambda h, a: (0, "loading...\n", "")})
        with pytest.raises(WanGPError, match="timed out"):
            poll_render_completion(host, "/run/render.log", 20,
                                   timeout_s=60, sleeper=sleeper, now=now)


# ── fix B: wedged-model-load watchdog ────────────────────────────────

class TestLoadStallWatchdog:
    def _clock(self, responses=None):
        host = FakeHost(responses or {})
        t = {"t": 0.0}
        return (host,
                lambda: t["t"],
                lambda s: t.__setitem__("t", t["t"] + max(s, 0.05)))

    def test_stall_before_denoise_kills_and_fails_load_stall(
            self, monkeypatch):
        monkeypatch.setenv("WANGP_LOAD_STALL_S", "5")
        host, now, sleeper = self._clock(
            {"cat": lambda h, a: (0, "Loading Model\n", ""),
             "nvidia-smi": lambda h, a: (0, "16384 MiB / 24576 MiB\n", "")})
        with pytest.raises(WanGPLoadStallError, match="load_stall"):
            poll_render_completion(host, "/run/render.log", 20,
                                   timeout_s=600, sleeper=sleeper, now=now)
        # the wgp pid was killed on the host
        heads = [c[0].split()[0] if isinstance(c[0], str) else c[0]
                 for c in host.calls]
        assert "pgrep" in heads
        assert "nvidia-smi" in heads

    def test_load_stall_is_retryable_class(self):
        # WanGPLoadStallError is a WanGPError (typed surface); the
        # executor-facing failure class string is carried in the
        # message prefix, which is what retry policies key on
        assert issubclass(WanGPLoadStallError, WanGPError)
        assert "load_stall" in str(WanGPLoadStallError("load_stall: x"))

    def test_default_and_env_stall_window(self, monkeypatch):
        monkeypatch.delenv("WANGP_LOAD_STALL_S", raising=False)
        assert adapter_mod._load_stall_s() == DEFAULT_LOAD_STALL_S == 300.0
        monkeypatch.setenv("WANGP_LOAD_STALL_S", "17")
        assert adapter_mod._load_stall_s() == 17.0
        monkeypatch.setenv("WANGP_LOAD_STALL_S", "not-a-number")
        assert adapter_mod._load_stall_s() == 300.0

    def test_progress_resets_the_watchdog(self, monkeypatch):
        monkeypatch.setenv("WANGP_LOAD_STALL_S", "5")
        logs = ["Loading Model\n", "Loading Model\ncheckpoint 1\n",
                "Loading Model\ncheckpoint 1\nDenoising 20/20\n"]
        state = {"i": 0}
        host, now, sleeper = self._clock(
            {"cat": lambda h, a: (0, logs[min(state["i"],
                                               len(logs) - 1)], "")})
        real_sleeper = sleeper

        def advancing_sleeper(s):
            state["i"] += 1
            real_sleeper(s)
        out = poll_render_completion(host, "/run/render.log", 20,
                                     timeout_s=600,
                                     sleeper=advancing_sleeper, now=now)
        assert "20/20" in out
        heads = [c[0].split()[0] if isinstance(c[0], str) else c[0]
                 for c in host.calls]
        assert "pgrep" not in heads  # never fired


# ── fix 2: sanctioned asset roots ────────────────────────────────────

class TestSanctionedDirs:
    def test_defaults_include_asset_roots(self, monkeypatch):
        monkeypatch.delenv("WANGP_SANCTIONED_DIRS", raising=False)
        dirs = default_sanctioned_dirs()
        assert "/home/straughter/Wan2GP/outputs" in dirs
        assert any(d.startswith("/mnt/bulk/") for d in dirs)
        assert set(DEFAULT_SANCTIONED_DIRS) == set(dirs)

    def test_env_overrides(self, monkeypatch):
        monkeypatch.setenv("WANGP_SANCTIONED_DIRS", "/a:/b")
        assert default_sanctioned_dirs() == ["/a", "/b"]

    def test_env_empty_falls_back_to_defaults(self, monkeypatch):
        monkeypatch.setenv("WANGP_SANCTIONED_DIRS", "  ")
        assert default_sanctioned_dirs() == list(DEFAULT_SANCTIONED_DIRS)


# ── fix 6: _host_path verifies-or-raises ─────────────────────────────

class TestHostPath:
    def test_mapped_path_used(self):
        class H:
            def map_path(self, p):
                return "/remote/" + p
        assert _host_path(H(), "x.json") == "/remote/x.json"

    def test_local_host_passthrough(self):
        class H:
            pass
        assert _host_path(H(), "x.json") == "x.json"

    def _raising_map_host(self, responses):
        host = FakeHost(responses)

        def boom(p):
            raise RuntimeError("escapes pull_root")
        host.map_path = boom
        return host

    def test_unmappable_but_present_absolutized(self):
        host = self._raising_map_host({"test": lambda h, a: (0, "", "")})
        out = _host_path(host, "rel/path.json")
        assert os.path.isabs(out)
        assert out == os.path.abspath("rel/path.json")

    def test_neither_mapped_nor_present_raises(self):
        host = self._raising_map_host({"test": lambda h, a: (1, "", "nope")})
        with pytest.raises(WanGPError, match="wrong-host"):
            _host_path(host, "rel/path.json")


# ── fix 1: audio_source_path defaults to the job audio_guide ─────────

class TestAudioSourceDefault:
    def test_none_falls_back_to_job_audio_guide(self):
        from host.wangp_adapter import _job_field
        job = {"audio_guide": "/assets/g.wav"}
        assert (_job_field(job, "audio_guide")
                == "/assets/g.wav")
        # the wiring itself: None -> job field happens in
        # _run_ref2va_job's _build_ref2va_runtime_input call
        import inspect
        src = inspect.getsource(adapter_mod._run_ref2va_job)
        assert "audio_source_path=audio_source_path" in src
        assert '_job_field(job, "audio_guide")' in src


# ── fix 3: qc_url default ────────────────────────────────────────────

class TestQcUrlDefault:
    def test_default_is_real_url(self, monkeypatch):
        monkeypatch.delenv("WANGP_QC_URL", raising=False)
        import scripts.run_jobs as rj
        assert rj.DEFAULT_QC_URL == "http://localhost:8000/health"
        assert rj.DEFAULT_QC_URL  # never empty

    def test_env_overridable(self, monkeypatch):
        import scripts.run_jobs as rj
        monkeypatch.setenv("WANGP_QC_URL", "http://qc:9999/healthz")
        seen = {}

        class H:
            def run_probe(self, argv, timeout=30):
                if argv[0] == "curl":
                    seen["url"] = argv[-1]
                return 0, "ok", ""
        rj.build_executor(queue=_FakeQueue(), host=H()).preflight({})
        assert seen["url"] == "http://qc:9999/healthz"

    def test_default_preflight_has_real_model_and_disk_gates(self,
                                                              monkeypatch):
        monkeypatch.delenv("WANGP_PREFLIGHT_MODELS_JSON", raising=False)
        monkeypatch.delenv("WANGP_PREFLIGHT_DISK_PATH", raising=False)
        monkeypatch.delenv("WANGP_MIN_FREE_GB", raising=False)
        import scripts.run_jobs as rj
        assert rj.DEFAULT_PREFLIGHT_MODELS
        assert {m["model_type"] for m in rj.DEFAULT_PREFLIGHT_MODELS} == {
            "minimax_h3_ref2va_pruned", "minimax_h3_fl2va_pruned"}
        assert all(len(m["sha256"]) == 64
                   for m in rj.DEFAULT_PREFLIGHT_MODELS)
        assert rj.DEFAULT_PREFLIGHT_DISK_PATH == "/mnt/bulk"
        assert rj.DEFAULT_MIN_FREE_GB > 0

    def test_job_mode_selects_matching_checkpoint(self):
        import scripts.run_jobs as rj
        ref = {"clips": [{"kind": "ref2va_render"}]}
        fl = {"clips": [{"kind": "fl2va_first_last"}]}
        assert rj._preflight_models_for_job(ref,
                                             rj.DEFAULT_PREFLIGHT_MODELS)[0][
                                                 "model_type"] == \
            "minimax_h3_ref2va_pruned"
        assert rj._preflight_models_for_job(fl,
                                             rj.DEFAULT_PREFLIGHT_MODELS)[0][
                                                 "model_type"] == \
            "minimax_h3_fl2va_pruned"

    def test_model_override_requires_sha256(self, monkeypatch):
        import scripts.run_jobs as rj
        monkeypatch.setenv(
            "WANGP_PREFLIGHT_MODELS_JSON",
            '[{"path":"/m.safetensors","sha256":"bad"}]')
        with pytest.raises(ValueError, match="invalid sha256"):
            rj.build_executor(queue=_FakeQueue(), host=object())


class _FakeQueue:
    def list_state(self, state):
        return []


# ── fix 9: no ref2va_lip_sync emitted as model_type anywhere ─────────

class TestModelTypeCrossCheck:
    def test_profiles_and_adapter_agree_on_pruned_name(self):
        assert rp.REF2VA_MODEL_TYPE == "minimax_h3_ref2va_pruned"
        assert rp.REF2VA_MODEL_TYPE == adapter_mod.REF2VA_MODEL_TYPE

    def test_no_emitted_ref2va_lip_sync_model_type(self, tmp_path):
        # a built ref2va settings doc never carries the rejected name
        doc = _build_ref2va_doc(tmp_path)
        assert doc["model_type"] == "minimax_h3_ref2va_pruned"
        assert "ref2va_lip_sync" not in json.dumps(doc)

    def test_source_scan_no_emission_sites(self):
        # the only in-repo mentions of the bare name are aliases or
        # the runtime accept-set — never an EMITTED model_type value
        import subprocess
        out = subprocess.run(
            ["grep", "-rn", "ref2va_lip_sync",
             "predict/", "host/", "services/", "scripts/"],
            capture_output=True, text=True).stdout
        for line in out.splitlines():
            if "=" not in line and "_KNOWN" not in line:
                continue
            assert '"ref2va_lip_sync"' not in line.split("#")[0] or \
                "LEGACY" in line or "_KNOWN_MODEL_TYPES" in line


def _ref2va_kwargs(tmp_path, subject="a subject", motion="speaks"):
    from predict.audio_dataplane import AudioGuideProvenance
    from predict.prompt_director import RenderBrief
    from predict.profile_selector import ProfileDecision
    files = []
    for name in ("guide.wav", "master.wav", "vocal.wav", "wmap.json"):
        f = Path(tmp_path) / name
        f.write_bytes(b"x" * 8)
        files.append(str(f))
    guide, master, stem, wmap = files
    ref = Path(tmp_path) / "ref1.png"
    ref.write_bytes(b"x")
    brief = RenderBrief(subject=subject, motion=motion,
                        camera="static", style="grain")
    decision = ProfileDecision(model="h3", resolution="768p",
                               shot_length_frames=192,
                               seed_policy="fixed_per_story",
                               wangp_profile="profile3")
    return dict(briefs=[brief], decision=decision,
                image_refs=[str(ref)], audio_prompt_type="A",
                guide_duration_s=8.0, shot_duration_s=8.0,
                audio_guide=guide,
                audio_provenance=AudioGuideProvenance(
                    source_master=master, vocal_stem=stem,
                    whisper_map=wmap, keeper_window_s=(1.0, 5.0)))


def _build_ref2va_doc(tmp_path, subject="a subject", motion="speaks"):
    return Ref2VAProfile().build_settings(
        **_ref2va_kwargs(tmp_path, subject=subject, motion=motion))


# ── fix 10: prompt-shape keys ride in extra= ─────────────────────────

class TestPromptShapeKeys:
    def test_settings_doc_contains_both_keys(self, tmp_path):
        doc = _build_ref2va_doc(tmp_path)
        assert doc["video_prompt_type"] == "I"
        assert doc["multi_prompts_gen_type"] == "FG"

    def test_jobconfig_has_no_such_fields(self):
        from predict.job_config import WanGPJobConfig
        import dataclasses
        names = {f.name for f in dataclasses.fields(WanGPJobConfig)}
        assert "video_prompt_type" not in names
        assert "multi_prompts_gen_type" not in names


# ── fix 11: renderer-template token boundary ─────────────────────────

class TestBriefTokenBoundary:
    def test_subject_token_in_brief_raises(self, tmp_path):
        with pytest.raises(ProfileError, match="renderer-level template"):
            _build_ref2va_doc(tmp_path, subject="render <Subject 1> speaking")

    def test_subject_token_in_motion_raises(self, tmp_path):
        with pytest.raises(ProfileError, match="renderer-level template"):
            _build_ref2va_doc(tmp_path, motion="moves as <Subject 2>")

    def test_plain_brief_still_builds(self, tmp_path):
        assert _build_ref2va_doc(tmp_path)["model_type"]
