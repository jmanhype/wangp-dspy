import json

import pytest


CHARACTER_ARGS = ("--characters", "Mara:S1:keeper", "Ivo:S2:engineer")


def _layout(tmp_path, *, audios=6, durations=6):
    script = tmp_path / "dialogue.txt"
    speakers = ("Mara", "Ivo")
    script.write_text("\n".join(
        f"{speakers[i % 2]}: Turn {i + 1} is ready."
        for i in range(6)))
    plates = tmp_path / "plates"
    plates.mkdir()
    for name in ("anchor.png", "Mara.png", "Ivo.png"):
        (plates / name).write_bytes(b"plate")
    audio = [tmp_path / f"turn{i + 1}.wav" for i in range(audios)]
    for path in audio:
        path.write_bytes(b"wav")
    return script, plates, [str(p) for p in audio], [56 / 24] * durations


def _args(script, plates, audio=None, durations=None):
    args = [
        "--script", str(script), "--plates", str(plates), *CHARACTER_ARGS,
        "--dry-run", "--continuation",
    ]
    if audio is not None:
        args += [item for path in audio for item in ("--audio", path)]
    if durations is not None:
        args += [item for value in durations
                 for item in ("--duration-s", str(value))]
    return args


def _fake_clips():
    return [{"clip_index": i, "speaker": "Mara", "frames": 56,
             "chain": {"re_anchor": i == 0}} for i in range(6)]


def test_parser_preserves_repeated_audio_and_duration_order():
    from scripts.run_film import build_parser

    args = build_parser().parse_args([
        "--script", "film.txt", "--plates", "plates",
        *CHARACTER_ARGS, "--continuation",
        "--audio", "one.wav", "--audio", "two.wav",
        "--duration-s", "1.5", "--duration-s", "2.5",
    ])
    assert args.audio == ["one.wav", "two.wav"]
    assert args.duration_s == [1.5, 2.5]


def test_cli_bridge_passes_continuation_inputs_to_run_film(
        tmp_path, monkeypatch):
    import scripts.run_film as module

    script, plates, audio, durations = _layout(tmp_path)
    captured = {}

    def fake_run_film(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        return _fake_clips()

    monkeypatch.setattr(module, "run_film", fake_run_film)
    assert module.main(_args(script, plates, audio, durations)) == 0
    assert captured["args"] == (str(script), str(plates))
    assert captured["kwargs"]["audio_paths"] == audio
    assert captured["kwargs"]["durations"] == durations
    assert captured["kwargs"]["continuation_mode"] is True


@pytest.mark.parametrize(
    "audios,duration_override,expected_error",
    [
        (None, None, "--continuation requires one --audio PATH"),
        (5, None, "expected 6, got 5"),
        (6, [56 / 24] * 5, "expected 6, got 5"),
        (6, [0], "positive finite number"),
    ],
    ids=["missing-audio", "audio-count", "duration-count", "duration-value"],
)
def test_invalid_continuation_inputs_fail_before_run_film(
        tmp_path, monkeypatch, capsys, audios, duration_override,
        expected_error):
    import scripts.run_film as module

    script, plates, audio, durations = _layout(
        tmp_path, audios=audios if audios is not None else 6)
    if duration_override is not None:
        durations = duration_override
    called = False

    def forbidden(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("run_film must not run")

    monkeypatch.setattr(module, "run_film", forbidden)
    with pytest.raises(SystemExit) as caught:
        module.main(_args(
            script, plates, audio if audios is not None else None, durations))
    assert caught.value.code == 2
    assert not called
    assert expected_error in capsys.readouterr().err


def test_non_continuation_cli_keeps_existing_defaults(tmp_path, monkeypatch):
    import scripts.run_film as module

    script, plates, _, _ = _layout(tmp_path)
    captured = {}

    def fake_run_film(*args, **kwargs):
        captured["kwargs"] = kwargs
        return _fake_clips()

    monkeypatch.setattr(module, "run_film", fake_run_film)
    args = _args(script, plates)
    args.remove("--continuation")
    assert module.main(args) == 0
    assert captured["kwargs"]["audio_paths"] is None
    assert captured["kwargs"]["durations"] is None
    assert captured["kwargs"]["continuation_mode"] is False


def test_cli_dry_run_reaches_existing_continuation_path(tmp_path, capsys):
    from scripts.run_film import main

    script, plates, audio, durations = _layout(tmp_path)
    assert main(_args(script, plates, audio, durations)) == 0
    output = capsys.readouterr().out
    summary = json.loads("\n".join(output.splitlines()[:4]))
    assert summary == {"clips": 6, "dry_run": True}
    assert output.count("clip 000") == 6
