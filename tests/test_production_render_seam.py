"""Production render seam tests (PR feat/production-render-seam).

All host interaction through an injected fake host — NO GPU, NO SSH.
The real seam gets exercised by the operator's vertical slice.
"""
import json
import shlex
import time
from pathlib import Path

import pytest

from host.wangp_adapter import (
    WGP_QUEUE_LOCK,
    WanGPAdapter,
    WanGPError,
    build_wgp_lock_argv,
    copy_newest_output_mp4,
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
        # single pre-joined elements (ssh-joins-with-spaces rule):
        # dispatch on the first WORD
        first = (argv[0].split()[0] if isinstance(argv[0], str)
                 and argv[0] else argv[0])
        if first in self.responses:
            rc, out, err = self.responses[first](self, argv)
            return rc, out, err
        if argv[:2] == ["ls", "-t"]:
            return 0, self.outputs + "\n", ""
        if argv[:1] == ["stat"]:
            return 0, f"{time.time()}\n", ""
        return 0, "", ""


def _settings(path: Path, *, steps=20, audio=None, video_length=None) -> Path:
    doc = {"num_inference_steps": steps}
    if audio:
        doc["audio_guide"] = str(audio)
    if video_length is not None:
        doc["video_length"] = video_length
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


def test_chain_pull_asset_falls_back_to_host_path_mapping(tmp_path):
    from host.wangp_adapter import _host_asset_path

    class Host:
        def map_asset(self, path):
            raise RuntimeError("not a source asset")

        def map_path(self, path):
            return "/remote/wgp/" + str(path).split("/pull/", 1)[-1]

    local = str(tmp_path / "pull" / "acceptance" / "chain.png")
    assert _host_asset_path(Host(), local) == \
        "/remote/wgp/acceptance/chain.png"


def test_ref2va_render_dir_skips_existing_dirs_after_worker_restart(
        tmp_path, monkeypatch):
    """A fresh worker process must not reset to render-0000 and overwrite
    an earlier cut's pulled artifact/provenance bundle."""
    import host.wangp_adapter as adapter_module
    from host.wangp_adapter import _next_render_dir

    (tmp_path / "render-0000").mkdir()
    monkeypatch.setattr(adapter_module, "_RENDER_SEQ", [0])
    assert _next_render_dir(tmp_path).name == "render-0001"


GOOD_LOG = ("loading model\nDenoising 20/20\nsaved\n"
            "Queue completed: 1/1 tasks in 1s\n")


class TestCommandShape:
    def test_lock_argv_shape(self):
        argv = build_wgp_lock_argv(
            "/run/settings.json", "/run/render.log",
            wangp_dir="/home/straughter/Wan2GP")
        # ssh joins argv elements with spaces before the remote shell
        # parses: ONE pre-joined element, shlex-quoted, round-trips.
        assert isinstance(argv, list) and len(argv) == 1
        parts = shlex.split(argv[0])
        assert parts[0] == "flock"
        assert parts[1] == WGP_QUEUE_LOCK == "/tmp/wgp_queue.lock"
        assert parts[2:4] == ["bash", "-c"]
        shell = parts[4]
        assert shell.startswith("cd /home/straughter/Wan2GP && ")
        assert "PYTHONUNBUFFERED=1" in shell
        assert "PYTORCH_ALLOC_CONF=expandable_segments:True" in shell
        # ABSOLUTE interpreter + script paths (ssh cwd != Wan2GP)
        assert "/home/straughter/Wan2GP/venv/bin/python" in shell
        assert "/home/straughter/Wan2GP/wgp.py --process " \
               "/run/settings.json" in shell
        assert "--profile 3" in shell
        assert "--attention sdpa" in shell
        assert shell.endswith("> /run/render.log 2>&1")
        # the pre-joined element must re-parse to the same semantics
        assert shlex.split(parts[4])[0] == "cd"

    def test_seam_launches_detached_and_mkdirs_first(self, tmp_path):
        host = FakeHost()
        s = _settings(tmp_path, steps=20)
        host.responses = {
            "setsid": lambda h, a: (0, "launched\n", ""),
            "cat": lambda h, a: (0, GOOD_LOG, ""),
        }
        production_ref2va_render(
            _adapter(host, tmp_path), _Inp(s, tmp_path / "raw.mp4"))
        # mkdir -p happens BEFORE the launch (log redirect needs it)
        launch_idx = next(i for i, c in enumerate(host.calls)
                          if c[0].startswith("setsid"))
        mkdir_idx = next(i for i, c in enumerate(host.calls)
                         if c[:2] == ["mkdir", "-p"])
        assert mkdir_idx < launch_idx
        launch = host.calls[launch_idx][0]
        assert launch.startswith("setsid nohup flock /tmp/wgp_queue.lock")
        assert launch.endswith("& echo launched")
        # ONE pre-joined element
        assert len(host.calls[launch_idx]) == 1

    def test_fresh_remote_directory_is_created_before_settings_push(
            self, tmp_path):
        """The SshHost contract must mkdir -p before rsync settings.

        A real rsync destination rejects a missing parent; this fake models
        that boundary and therefore catches a settings push that happens
        before the host seam's idempotent directory creation.
        """
        class FreshDirHost(FakeHost):
            def __init__(self):
                super().__init__()
                self.created = set()
                self.pushed = False

            def map_path(self, path):
                return "/remote/wgp/acceptance/" + Path(path).name

            def makedirs(self, path):
                self.calls.append(["makedirs", path])
                self.created.add(path)

            def write_text(self, path, text):
                parent = path.rsplit("/", 1)[0]
                if parent not in self.created:
                    raise RuntimeError("rsync destination parent missing")
                self.calls.append(["write_text", path])
                self.pushed = True
                return path

        host = FreshDirHost()
        s = _settings(tmp_path, steps=20)
        host.responses = {
            "setsid": lambda h, a: (0, "launched\n", ""),
            "cat": lambda h, a: (0, GOOD_LOG, ""),
        }
        production_ref2va_render(
            _adapter(host, tmp_path), _Inp(s, tmp_path / "raw.mp4"))

        mkdir_idx = next(i for i, c in enumerate(host.calls)
                         if c[0] == "makedirs")
        write_idx = next(i for i, c in enumerate(host.calls)
                         if c[0] == "write_text")
        assert mkdir_idx < write_idx
        assert host.pushed is True


class TestVerifyBeforeTrust:
    def test_complete_log_accepted(self):
        assert verify_denoise_steps(GOOD_LOG, 20)

    def test_truncated_log_rejected(self):
        assert not verify_denoise_steps("Denoising 17/20\ncrash", 20)

    def test_mismatched_steps_rejected(self):
        # a 20/20 line does not satisfy a steps=30 config
        assert not verify_denoise_steps(GOOD_LOG, 30)

    def test_seam_rejects_truncated_log(self, tmp_path, monkeypatch):
        monkeypatch.setenv("WANGP_LOAD_STALL_S", "0")
        host = FakeHost()
        s = _settings(tmp_path, steps=20)
        host.responses = {
            "setsid": lambda h, a: (0, "launched\n", ""),
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
        host.responses = {"setsid": lambda h, a: (1, "", "boom")}
        with pytest.raises(WanGPError, match="detached wgp launch failed"):
            production_ref2va_render(
                _adapter(host, tmp_path),
                _Inp(s, tmp_path / "raw.mp4"))


class TestCopyAndMux:
    def test_settings_assets_are_host_resolved_before_launch(self, tmp_path):
        class MappedHost(FakeHost):
            def __init__(self):
                super().__init__()
                self.pushed = None

            def map_path(self, path):
                return "/remote/wgp/acceptance/" + Path(path).name

            def map_asset(self, path):
                return "/home/u/acceptance/" + Path(path).name

            def write_text(self, path, text):
                self.pushed = json.loads(text)
                return path

        host = MappedHost()
        guide = tmp_path / "turn1.wav"
        guide.write_bytes(b"RIFF")
        settings = _settings(tmp_path, audio=guide)
        host.responses = {
            "setsid": lambda h, a: (0, "launched\n", ""),
            "cat": lambda h, a: (0, GOOD_LOG, ""),
        }

        production_ref2va_render(
            _adapter(host, tmp_path), _Inp(settings, tmp_path / "raw.mp4"))

        assert host.pushed["audio_guide"] == "/home/u/acceptance/turn1.wav"

    def test_newest_output_copied_to_target(self, tmp_path):
        host = FakeHost(outputs="out00042.mp4")
        s = _settings(tmp_path)  # no audio
        host.responses = {
            "setsid": lambda h, a: (0, "launched\n", ""),
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
        s = _settings(tmp_path, audio=guide, video_length=56)
        real_probe = host.run_probe
        def probe(argv, timeout=30):
            if argv[:1] == ["ffprobe"]:
                return 0, "56\n", ""
            return real_probe(argv, timeout=timeout)
        host.run_probe = probe
        host.responses = {
            "setsid": lambda h, a: (0, "launched\n", ""),
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
        assert "-shortest" not in argv
        assert "-t" in argv
        assert argv[argv.index("-t") + 1] == "2.333333"
        assert str(out).endswith(".mux.mp4")

    def test_no_mux_without_audio_guide(self, tmp_path):
        host = FakeHost()
        s = _settings(tmp_path)
        host.responses = {
            "setsid": lambda h, a: (0, "launched\n", ""),
            "cat": lambda h, a: (0, GOOD_LOG, ""),
        }
        production_ref2va_render(
            _adapter(host, tmp_path), _Inp(s, tmp_path / "raw.mp4"))
        assert not any(c[0] == "ffmpeg" for c in host.calls)

    @pytest.mark.parametrize(("actual", "raises"), [(45, True), (56, False)])
    def test_continuation_frame_grid_is_strict(self, tmp_path, actual, raises):
        class FrameHost(FakeHost):
            def run_probe(self, argv, timeout=30):
                if argv[:1] == ["ffprobe"]:
                    self.calls.append(list(argv))
                    return 0, f"{actual}\n", ""
                return super().run_probe(argv, timeout=timeout)

        host = FrameHost()
        s = _settings(tmp_path, video_length=56)
        host.responses = {
            "setsid": lambda h, a: (0, "launched\n", ""),
            "cat": lambda h, a: (0, GOOD_LOG, ""),
        }
        if raises:
            with pytest.raises(WanGPError, match="frame-count validation"):
                production_ref2va_render(
                    _adapter(host, tmp_path),
                    _Inp(s, tmp_path / "raw.mp4"))
        else:
            out = production_ref2va_render(
                _adapter(host, tmp_path), _Inp(s, tmp_path / "raw.mp4"))
            assert str(out).endswith("raw.mp4")


class TestNewestOutput:
    def test_discovery_ignores_prompt_text_and_requires_real_file(
            self, tmp_path):
        host = FakeHost(outputs="... as something.mp4\n"
                        "multishot_1788810830.mp4")
        found = newest_output_mp4(
            host, "/home/straughter/Wan2GP/outputs",
            newer_than=time.time() - 1)
        assert found.endswith("multishot_1788810830.mp4")
        assert not found.endswith("something.mp4")

    def test_discovery_rejects_stale_output_by_host_mtime(self):
        class MtimeHost(FakeHost):
            def run_probe(self, argv, timeout=30):
                if argv[:1] == ["stat"]:
                    return (0, "1\n" if argv[-1].endswith("old.mp4")
                            else "9999999999\n", "")
                return super().run_probe(argv, timeout=timeout)

        host = MtimeHost(outputs="old.mp4\nfresh.mp4")
        assert newest_output_mp4(
            host, "/w/outputs", newer_than=100.0).endswith("fresh.mp4")

    def test_copy_revalidates_when_selected_output_changes(self):
        class RacingHost(FakeHost):
            def __init__(self):
                super().__init__(outputs="first.mp4")
                self.lists = 0
                self.copies = []

            def run_probe(self, argv, timeout=30):
                if argv[:2] == ["ls", "-t"]:
                    self.lists += 1
                    return (0, "first.mp4\n" if self.lists == 1
                            else "second.mp4\n", "")
                if argv[:1] == ["cp"]:
                    self.copies.append(argv[1])
                    return (1, "", "first output raced away") \
                        if len(self.copies) == 1 else (0, "", "")
                return super().run_probe(argv, timeout=timeout)

        host = RacingHost()
        source = copy_newest_output_mp4(
            host, "/w/outputs", "/w/render/raw.mp4")
        assert source.endswith("second.mp4")
        assert host.copies == ["/w/outputs/first.mp4",
                               "/w/outputs/second.mp4"]

    def test_copy_waits_for_strict_output_after_queue_completion(self):
        class DelayedOutputHost(FakeHost):
            def __init__(self):
                super().__init__(outputs="")
                self.polls = 0

            def run_probe(self, argv, timeout=30):
                if argv[:2] == ["ls", "-t"]:
                    self.polls += 1
                    return (0, "" if self.polls < 2 else "fresh.mp4\n", "")
                return super().run_probe(argv, timeout=timeout)

        host = DelayedOutputHost()
        clock = {"t": 0.0}
        found = copy_newest_output_mp4(
            host, "/w/outputs", "/w/render/raw.mp4",
            wait_timeout_s=5.0, poll_interval_s=1.0,
            sleeper=lambda seconds: clock.__setitem__(
                "t", clock["t"] + seconds),
            now=lambda: clock["t"])
        assert found.endswith("fresh.mp4")
        assert host.polls == 2

    def test_no_mp4_is_typed_failure(self):
        host = FakeHost(outputs="notes.txt")
        with pytest.raises(WanGPError, match="no .mp4 outputs"):
            newest_output_mp4(host, "/w/outputs")

    def test_ls_failure_is_typed(self):
        host = FakeHost()
        host.responses = {"ls": lambda h, a: (2, "", "No such dir")}
        with pytest.raises(WanGPError, match="cannot list"):
            newest_output_mp4(host, "/w/outputs")
