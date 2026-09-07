import pathlib
from types import SimpleNamespace

import pytest

from predict.audio_prep import (
    AudioPreparationError, prepare_turn_audio,
)


def test_prepare_turn_audio_trims_boosts_and_verifies(tmp_path):
    source = pathlib.Path(tmp_path) / "raw turn.wav"
    output = pathlib.Path(tmp_path) / "prepared" / "cut01.wav"
    source.write_bytes(b"raw")
    calls = []

    def run(argv):
        calls.append(list(argv))
        if argv[0] == "ffmpeg" and "volumedetect" in argv:
            return SimpleNamespace(returncode=0,
                                   stdout="",
                                   stderr="[Parsed_volumedetect] mean_volume: -18.4 dB")
        if argv[0] == "ffmpeg":
            output.parent.mkdir(exist_ok=True)
            output.write_bytes(b"wav")
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        return SimpleNamespace(returncode=0, stdout="2.000000\n", stderr="")

    prepared = prepare_turn_audio(
        str(source), str(output), speaker_id="S1", runner=run)
    assert prepared.measured_duration_s == 2.0
    assert prepared.boost_db == 9.0
    assert prepared.rms_db == -18.4
    assert calls[1][:4] == ["ffmpeg", "-y", "-i", str(source)]
    assert "volume=9.00dB" in calls[1]
    assert "-t" in calls[1] and "2.000000" in calls[1]
    assert calls[1][-1] == str(output)


def test_prepare_turn_audio_rejects_short_source(tmp_path):
    source = pathlib.Path(tmp_path) / "short.wav"
    source.write_bytes(b"raw")

    def run(argv):
        return SimpleNamespace(returncode=0, stdout="1.25\n", stderr="")

    with pytest.raises(AudioPreparationError, match="shorter"):
        prepare_turn_audio(str(source), str(tmp_path / "out.wav"),
                           speaker_id="S1", runner=run)


def test_prepare_turn_audio_rejects_multispeaker_or_silent(tmp_path):
    source = pathlib.Path(tmp_path) / "raw.wav"
    source.write_bytes(b"raw")
    with pytest.raises(AudioPreparationError, match="exactly one speaker"):
        prepare_turn_audio(str(source), str(tmp_path / "out.wav"),
                           speaker_id="S1", single_speaker=False,
                           runner=lambda _: None)

    def run(argv):
        if argv[0] == "ffmpeg" and "volumedetect" in argv:
            return SimpleNamespace(returncode=0, stdout="",
                                   stderr="mean_volume: -72.0 dB")
        if argv[0] == "ffmpeg":
            pathlib.Path(argv[-1]).write_bytes(b"wav")
        return SimpleNamespace(returncode=0, stdout="2.0\n", stderr="")

    with pytest.raises(AudioPreparationError, match="rms_db"):
        prepare_turn_audio(str(source), str(tmp_path / "out.wav"),
                           speaker_id="S1", runner=run)
