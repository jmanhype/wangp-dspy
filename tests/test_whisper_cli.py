from pathlib import Path
from types import SimpleNamespace

from qc.audio_critic.whisper_cli import whisper_transcriber


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
