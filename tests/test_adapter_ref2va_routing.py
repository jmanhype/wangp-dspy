"""RED tests — Ref2VA adapter-mode routing (per-job model_type dispatch).

Spec: host/wangp_adapter.py gains per-job routing. render_for_job()
accepts a job dict (manifest clip entry, PR #59/#60 shape) whose
"recipe"/"model_type" selects the lane:
- fl2va (default, backward compat) -> existing build_settings + wgp
- ref2va -> the EXISTING host/ref2va_runtime.run_ref2va_runtime
  (never duplicated), carrying image_refs / audio_guide / prompt from
  the #57 recipe envelope.

All collaborators are stubbed — no GPU, no ssh, no ffmpeg.
"""
import json
from types import SimpleNamespace

import pytest

from host import wangp_adapter as wa
from host.ref2va_runtime import Ref2VARuntimeError
from predict.audio_dataplane import AudioGuideProvenance
from predict.prompt_director import RenderBrief
from predict.profile_selector import ProfileDecision


def _brief():
    return RenderBrief(subject="<Picture 1> a man", motion="speaks",
                       camera="medium two-shot", style="16mm grain")


def _decision():
    return ProfileDecision(model="h3", resolution="768p",
                           shot_length_frames=96, seed_policy="fixed_per_story",
                           wangp_profile="profile3")


def _write(path, data=b"x"):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return str(path)


class _FakeHost:
    """Minimal host seam: join/makedirs/write_text passthrough."""

    def __init__(self, root):
        self.root = root

    def join(self, *parts):
        import os
        return os.path.join(*parts)

    def makedirs(self, d):
        import os
        os.makedirs(d, exist_ok=True)

    def write_text(self, path, text):
        with open(path, "w") as f:
            f.write(text)
        return path


class TestJobLane:
    def test_job_lane_default_is_fl2va(self):
        assert wa.job_lane({}) == "fl2va"
        assert wa.job_lane({"kind": "first_frame_continuation"}) == "fl2va"
        assert wa.job_lane({"kind": "shot1_three_ref_recipe"}) == "fl2va"

    def test_job_lane_ref2va(self):
        assert wa.job_lane({"kind": "ref2va_render"}) == "ref2va"
        assert wa.job_lane(
            {"kind": "shot1_three_ref_recipe",
             "model_type": "ref2va_lip_sync"}) == "ref2va"

    def test_unknown_lane_typed_rejection(self):
        with pytest.raises(wa.WanGPError):
            wa.job_lane({"kind": "ref2va_render",
                         "model_type": "bogus_lane"})


class TestRenderForJob:
    def test_ref2va_job_routes_to_ref2va_runtime(self, tmp_path,
                                                 monkeypatch):
        audio = _write(tmp_path / "audio" / "guide.wav")
        image = _write(tmp_path / "images" / "plate.png")
        monkeypatch.setattr(wa, "_run_ref2va_job",
                            lambda adapter, job, **kw: SimpleNamespace(
                                lane="ref2va", ok=True))
        calls = []
        monkeypatch.setattr(wa, "_run_fl2va_job",
                            lambda adapter, job: calls.append(job))
        adapter = wa.WanGPAdapter(host=_FakeHost(tmp_path))
        job = {"kind": "ref2va_render", "prompt": "p",
               "image_refs": [image], "audio_guide": audio,
               "shot_duration_s": 5.0}
        out = adapter.render_for_job(job)
        assert out.lane == "ref2va"
        assert calls == []  # fl2va path untouched

    def test_fl2va_job_routes_to_existing_path(self, tmp_path,
                                               monkeypatch):
        monkeypatch.setattr(
            wa, "_run_fl2va_job",
            lambda adapter, job: SimpleNamespace(lane="fl2va", ok=True))
        adapter = wa.WanGPAdapter(host=_FakeHost(tmp_path))
        out = adapter.render_for_job({"kind": "first_frame_continuation"})
        assert out.lane == "fl2va"

    def test_ref2va_job_carries_recipe_envelope(self, tmp_path):
        """A ref2va job builds Ref2VARuntimeInput from the #57 recipe
        envelope (image_refs/audio_guide/prompt) — stubbed render,
        stubbed runner, real runtime validation of the shaped settings."""
        pytest.importorskip("host.ref2va_runtime")
        from host.ref2va_runtime import Ref2VARuntimeInput

        wav = tmp_path / "guide.wav"
        wav.write_bytes(b"RIFF")
        img = tmp_path / "plate.png"
        img.write_bytes(b"png")
        master = _write(tmp_path / "master.wav")

        prov = AudioGuideProvenance(
            source_master=str(master), vocal_stem=str(master),
            whisper_map=str(master), keeper_window_s=(0.0, 5.0))
        job = {
            "kind": "ref2va_render",
            "prompt": "<Picture 1> speaker talks",
            "image_refs": [str(img)],
            "audio_guide": str(wav),
            "shot_duration_s": 5.0,
            "audio_provenance": prov,
        }
        adapter = wa.WanGPAdapter(host=_FakeHost(tmp_path))
        # stub the wgp render inside the runtime input: raw render file
        raw = tmp_path / "renders" / "raw.mp4"
        raw.parent.mkdir(exist_ok=True)
        raw.write_bytes(b"mp4")
        remux = tmp_path / "renders" / "remux.mp4"

        def _render(inp):
            return str(raw)

        def _runner(argv):
            remux.write_bytes(b"mp4")
            return 0

        inp = wa._build_ref2va_runtime_input(
            adapter, job, render=_render, runner=_runner,
            raw_render_path=raw, audio_source_path=master,
            remux_output_path=remux,
            settings_path=tmp_path / "renders" / "settings.json",
            sanctioned_dirs=[str(tmp_path)])
        assert isinstance(inp, Ref2VARuntimeInput)
        doc = inp.profile_build_kwargs
        assert doc["image_refs"] == [str(img)]
        assert doc["audio_prompt_type"] == "A"
        assert doc["guide_duration_s"] == 5.0
        assert doc["shot_duration_s"] == 5.0

    def test_ref2va_job_without_recipe_fields_typed_error(self,
                                                          tmp_path):
        adapter = wa.WanGPAdapter(host=_FakeHost(tmp_path))
        with pytest.raises(wa.WanGPError):
            adapter.render_for_job({"kind": "ref2va_render"})

    def test_render_settings_model_type_default_unchanged(self):
        """Backward compat: build_settings still pins FL2VA."""
        s = wa.build_settings([_brief()], _decision())
        assert s["model_type"] == "minimax_h3_fl2va_pruned"
