import json

import pytest

from predict import audio_prep


def test_cli_calls_recovered_recipe(monkeypatch, tmp_path, capsys):
    source = tmp_path / "raw.wav"
    source.write_bytes(b"fixture")
    output = tmp_path / "guide.wav"
    calls = []

    def prepare(src, dst, *, speaker_id):
        calls.append((src, dst, speaker_id))
        return {"guide_sha256": "recorded"}

    monkeypatch.setattr(audio_prep, "prepare_v3_turn_audio", prepare)
    assert audio_prep.main(["--source", str(source), "--output", str(output),
                            "--speaker", "Nell"]) == 0
    assert calls == [(str(source), str(output), "Nell")]
    assert json.loads(capsys.readouterr().out)["guide_sha256"] == "recorded"


@pytest.mark.parametrize("existing", ["guide.wav", "guide.prep.json", "raw.wav"])
def test_cli_refuses_overwrite(monkeypatch, tmp_path, existing):
    source = tmp_path / "raw.wav"
    source.write_bytes(b"original")
    (tmp_path / existing).write_bytes(b"original")
    output = source if existing == "raw.wav" else tmp_path / "guide.wav"
    monkeypatch.setattr(audio_prep, "prepare_v3_turn_audio",
                        lambda *a, **k: pytest.fail("must refuse before prep"))
    with pytest.raises(SystemExit) as exc:
        audio_prep.main(["--source", str(source), "--output", str(output),
                        "--speaker", "Nell"])
    assert exc.value.code == 2
    assert source.read_bytes() == b"original"


def test_cli_prep_failure_is_nonzero(monkeypatch, tmp_path, capsys):
    def refuse(*a, **k):
        raise audio_prep.AudioPreparationError("too short")

    monkeypatch.setattr(audio_prep, "prepare_v3_turn_audio", refuse)
    assert audio_prep.main(["--source", str(tmp_path / "raw.wav"),
                            "--output", str(tmp_path / "guide.wav"),
                            "--speaker", "Nell"]) == 2
    assert "too short" in capsys.readouterr().err
