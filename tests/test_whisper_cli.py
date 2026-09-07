from pathlib import Path
from types import SimpleNamespace

from qc.audio_critic.whisper_cli import (host_whisper_transcriber,
                                          whisper_transcriber)


def test_whisper_cli_uses_argv_and_reads_transcript_artifact(tmp_path):
    calls = []
    output_dir = str(tmp_path / "whisper")

    def run(argv):
        calls.append(list(argv))
        if argv[0] == "cat":
            return (0, "The gate is open\n", "")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    text = whisper_transcriber(
        "/remote/turn 1.wav", runner=run, output_dir=output_dir)
    assert text == "The gate is open"
    assert calls[0] == ["mkdir", "-p", output_dir]
    assert calls[1][0] == "whisper"
    assert "--output_format" in calls[1]
    assert calls[2] == ["cat", str(Path(output_dir) / "turn 1.txt")]


def test_host_whisper_maps_assets_and_isolates_attempt_outputs(tmp_path):
    calls = []

    class Host:
        def map_asset(self, path):
            if path.startswith("assets/"):
                return "/home/straughter/acceptance/" + Path(path).name
            raise ValueError("not an asset")

        def map_path(self, path):
            return "/home/straughter/Wan2GP/acceptance/" + Path(path).name

        def run_probe(self, argv, timeout=900):
            calls.append(list(argv))
            if argv[0] == "cat":
                return 0, "The gate is open\n", ""
            return 0, "", ""

    transcribe = host_whisper_transcriber(
        Host(), output_dir="/tmp/wangp-whisper")
    assert transcribe("assets/test_only/turn1.wav") == "The gate is open"
    assert transcribe(
        str(tmp_path / "render" / "remux.mp4")) == "The gate is open"

    whisper_calls = [c for c in calls if c[0] == "whisper"]
    assert whisper_calls[0][1] == "/home/straughter/acceptance/turn1.wav"
    assert whisper_calls[1][1].endswith("/remux.mp4")
    dirs = [c[c.index("--output_dir") + 1] for c in whisper_calls]
    assert dirs == ["/tmp/wangp-whisper/attempt-0001",
                    "/tmp/wangp-whisper/attempt-0002"]


def test_host_whisper_prefers_existing_local_pull_artifact(tmp_path):
    """Post-gate QC must read the pulled remux, not a guessed host path."""
    calls = []
    remux = tmp_path / "render-0000" / "remux.mp4"
    remux.parent.mkdir()
    remux.write_bytes(b"local remux")

    class Host:
        def map_asset(self, path):
            raise AssertionError("local artifact must not be mapped remotely")

        def map_path(self, path):
            raise AssertionError("local artifact must not be mapped remotely")

        def run_probe(self, argv, timeout=900):
            raise AssertionError("local QC must not call the remote host")

    def local_runner(argv):
        calls.append(list(argv))
        if argv[0] == "cat":
            return 0, "Oh hush now, dear. Have a cookie.\n", ""
        return 0, "", ""

    transcribe = host_whisper_transcriber(
        Host(), output_dir=str(tmp_path / "whisper"),
        local_runner=local_runner)
    assert transcribe.map_audio_path(str(remux)) == str(remux)
    assert transcribe(str(remux)) == "Oh hush now, dear. Have a cookie."
    whisper_call = next(c for c in calls if c[0] == "whisper")
    assert whisper_call[1] == str(remux)
    assert not any(c[0] == "ssh" for c in calls)


def test_host_whisper_falls_back_to_remote_for_host_only_asset(tmp_path):
    """A source WAV present only on the GPU still uses the host seam."""
    calls = []

    class Host:
        def map_asset(self, path):
            return "/home/straughter/acceptance/turn1.wav"

        def run_probe(self, argv, timeout=900):
            calls.append(list(argv))
            if argv[0] == "cat":
                return 0, "Oh hush now, dear. Have a cookie.\n", ""
            return 0, "", ""

    def local_runner(_argv):
        raise AssertionError("host-only source must not use local runner")

    transcribe = host_whisper_transcriber(
        Host(), output_dir=str(tmp_path / "whisper"),
        local_runner=local_runner)
    assert transcribe("/host-only/turn1.wav")
    whisper_call = next(c for c in calls if c[0] == "whisper")
    assert whisper_call[1] == "/home/straughter/acceptance/turn1.wav"
