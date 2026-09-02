"""Production render seam tests (PR feat/production-render-seam).

All host interaction through an injected fake host — NO GPU, NO SSH.
The real seam gets exercised by the operator's vertical slice.
"""
import json
from pathlib import Path

import pytest

from host.wangp_adapter import (
    WGP_QUEUE_LOCK,
    WanGPAdapter,
    WanGPError,
    build_wgp_lock_argv,
    newest_output_mp4,
    production_ref2va_render,
    verify_denoise_steps,
)


class FakeHost:
    """Records run_probe argv; canned responses per argv head."""

    def __init__(self, responses=None, outputs="new.mp4"):
        self.calls = []
        self.responses: dict = responses or {}
        self.outputs = outputs

    def run_probe(self, argv, timeout=30):
        self.calls.append(list(argv))
        key = " ".join(argv[:2])
        if argv[0] in self.responses:
            rc, out, err = self.responses[argv[0]](self, argv)
            return rc, out, err
        if argv[:2] == ["ls", "-t"]:
            return 0, self.outputs + "\n", ""
        return 0, "", ""


def _settings(path: Path, *, steps=20, audio=None) -> Path:
    doc = {"num_inference_steps": steps}
    if audio:
        doc["audio_guide"] = str(audio)
    p = path / "settings.json"
    p.write_text(json.dumps(doc))
    return p


class _Inp:
    def __init__(self, settings_path, raw_render_path):
        self.settings_path = Path(settings_path)
        self.raw_render_path = Path(raw_render_path)


def _adapter(host, tmp_path):
    return WanGPAdapter(host=host, output_dir=str(tmp_path / "out"),
                        wgp_outputs_dir="/home/straughter/Wan2GP/outputs",
                        runner=lambda *a: None)


GOOD_LOG = "loading model\nDenoising 20/20\nsaved\n"


class TestCommandShape:
    def test_lock_argv_shape(self):
        argv = build_wgp_lock_argv(
            "/run/settings.json", "/run/render.log",
            wangp_dir="/home/straughter/Wan2GP")
        assert argv[0] == "flock"
        assert argv[1] == WGP_QUEUE_LOCK == "/tmp/wgp_queue.lock"
        assert argv[2] == "-c"
        shell = argv[3]
        assert shell.startswith("cd /home/straughter/Wan2GP && ")
        assert "PYTHONUNBUFFERED=1" in shell
        assert "PYTORCH_ALLOC_CONF=expandable_segments:True" in shell
        assert "./venv/bin/python wgp.py --process /run/settings.json" \
            in shell
        assert "--profile 3" in shell
        assert "--attention sdpa" in shell
        assert shell.endswith("> /run/render.log 2>&1")

    def test_seam_uses_the_lock_invocation(self, tmp_path):
        host = FakeHost()
        s = _settings(tmp_path, steps=20)
        host.responses = {
            "flock": lambda h, a: (0, "", ""),
            "cat": lambda h, a: (0, GOOD_LOG, ""),
        }
        production_ref2va_render(
            _adapter(host, tmp_path), _Inp(s, tmp_path / "raw.mp4"))
        flock_calls = [c for c in host.calls if c[0] == "flock"]
        assert len(flock_calls) == 1
        assert flock_calls[0][1] == "/tmp/wgp_queue.lock"


class TestVerifyBeforeTrust:
    def test_complete_log_accepted(self):
        assert verify_denoise_steps(GOOD_LOG, 20)

    def test_truncated_log_rejected(self):
        assert not verify_denoise_steps("Denoising 17/20\ncrash", 20)

    def test_mismatched_steps_rejected(self):
        # a 20/20 line does not satisfy a steps=30 config
        assert not verify_denoise_steps(GOOD_LOG, 30)

    def test_seam_rejects_truncated_log(self, tmp_path):
        host = FakeHost()
        s = _settings(tmp_path, steps=20)
        host.responses = {
            "flock": lambda h, a: (0, "", ""),
            "cat": lambda h, a: (0, "Denoising 12/20\nKilled", ""),
        }
        with pytest.raises(WanGPError, match="verify-before-trust"):
            production_ref2va_render(
                _adapter(host, tmp_path),
                _Inp(s, tmp_path / "raw.mp4"))
        # nothing was copied off the outputs dir
        assert not any(c[0] in ("cp", "ffmpeg") for c in host.calls)

    def test_nonzero_wgp_rc_is_typed_failure(self, tmp_path):
        host = FakeHost()
        s = _settings(tmp_path)
        host.responses = {"flock": lambda h, a: (1, "", "boom")}
        with pytest.raises(WanGPError, match="wgp invocation failed"):
            production_ref2va_render(
                _adapter(host, tmp_path),
                _Inp(s, tmp_path / "raw.mp4"))


class TestCopyAndMux:
    def test_newest_output_copied_to_target(self, tmp_path):
        host = FakeHost(outputs="out00042.mp4")
        s = _settings(tmp_path)  # no audio
        host.responses = {
            "flock": lambda h, a: (0, "", ""),
            "cat": lambda h, a: (0, GOOD_LOG, ""),
        }
        out = production_ref2va_render(
            _adapter(host, tmp_path),
            _Inp(s, tmp_path / "raw.mp4"))
        cp = [c for c in host.calls if c[0] == "cp"]
        assert cp == [["cp", "/home/straughter/Wan2GP/outputs/"
                       "out00042.mp4", str(tmp_path / "raw.mp4")]]
        assert str(out) == str(tmp_path / "raw.mp4")

    def test_mux_only_with_audio_guide(self, tmp_path):
        host = FakeHost()
        guide = tmp_path / "guide.wav"
        guide.write_bytes(b"RIFF")
        s = _settings(tmp_path, audio=guide)
        host.responses = {
            "flock": lambda h, a: (0, "", ""),
            "cat": lambda h, a: (0, GOOD_LOG, ""),
        }
        out = production_ref2va_render(
            _adapter(host, tmp_path),
            _Inp(s, tmp_path / "raw.mp4"))
        ff = [c for c in host.calls if c[0] == "ffmpeg"]
        assert len(ff) == 1
        argv = ff[0]
        assert argv[:2] == ["ffmpeg", "-y"]
        maps = [argv[i + 1] for i, a in enumerate(argv) if a == "-map"]
        assert maps == ["0:v", "1:a"]
        assert argv[argv.index("-c:v") + 1] == "copy"
        assert argv[argv.index("-c:a") + 1] == "aac"
        assert argv[-1] == "-shortest" or "-shortest" in argv
        assert str(out).endswith(".mux.mp4")

    def test_no_mux_without_audio_guide(self, tmp_path):
        host = FakeHost()
        s = _settings(tmp_path)
        host.responses = {
            "flock": lambda h, a: (0, "", ""),
            "cat": lambda h, a: (0, GOOD_LOG, ""),
        }
        production_ref2va_render(
            _adapter(host, tmp_path), _Inp(s, tmp_path / "raw.mp4"))
        assert not any(c[0] == "ffmpeg" for c in host.calls)


class TestNewestOutput:
    def test_no_mp4_is_typed_failure(self):
        host = FakeHost(outputs="notes.txt")
        with pytest.raises(WanGPError, match="no .mp4 outputs"):
            newest_output_mp4(host, "/w/outputs")

    def test_ls_failure_is_typed(self):
        host = FakeHost()
        host.responses = {"ls": lambda h, a: (2, "", "No such dir")}
        with pytest.raises(WanGPError, match="cannot list"):
            newest_output_mp4(host, "/w/outputs")
