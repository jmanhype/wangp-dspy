from __future__ import annotations

import json
from pathlib import Path
import subprocess

import pytest

from predict.content_brief import (
    CONTENT_BRIEF_SCHEMA,
    DEFAULT_DURATION_S,
    ContentBriefError,
    _check_audio_duration,
    _probe_audio_duration,
    build_run_film_inputs,
    load_content_brief,
    _probe_duration_output,
)
from scripts.run_content_brief import main
from services.director.renderers.policy import check_guide_duration


def _brief_payload() -> dict:
    return {
        "schema_version": CONTENT_BRIEF_SCHEMA,
        "title": "Harbor Signal",
        "premise": "Two keepers question an automated lighthouse.",
        "characters": [
            {"name": "Tess", "sn_tag": "S1", "description": "project architect"},
            {"name": "Rho", "sn_tag": "S2", "description": "horizon scout"},
        ],
        "dialogue": [
            {"speaker": "Tess", "text": "Tomorrow's sunrise is only a project."},
            {"speaker": "Rho", "text": "Give me a real horizon."},
            {"speaker": "Tess", "text": "The projector died at midnight."},
            {"speaker": "Rho", "text": "Then we will watch the star."},
        ],
    }


def _layout(tmp_path: Path, payload: dict | None = None) -> tuple[Path, Path]:
    brief = tmp_path / "brief.json"
    brief.write_text(json.dumps(payload or _brief_payload()), encoding="utf-8")
    plates = tmp_path / "plates"
    plates.mkdir()
    for name in ("anchor.png", "Tess.png", "Rho.png"):
        (plates / name).write_bytes(f"plate-{name}".encode())
    return brief, plates


def _write_real_wav(path: Path, duration_s: float) -> None:
    subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
            "-t", f"{duration_s:.6f}", str(path),
        ],
        check=True,
    )


def _write_video_only_mp4(path: Path, duration_s: float) -> None:
    subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-f", "lavfi",
            "-i", f"color=c=black:s=64x64:d={duration_s:.6f}:r=24",
            "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(path),
        ],
        check=True,
    )


def test_load_normalizes_and_hashes_stable_briefs(tmp_path: Path) -> None:
    first, _ = _layout(tmp_path)
    second = tmp_path / "copy.json"
    second.write_text(first.read_text(encoding="utf-8"), encoding="utf-8")

    left = load_content_brief(first)
    right = load_content_brief(second)
    assert left.title == "Harbor Signal"
    assert [line.speaker for line in left.dialogue] == ["Tess", "Rho", "Tess", "Rho"]
    assert len(left.durations_s) == 4
    assert left.brief_hash == right.brief_hash
    assert left.brief_hash == (
        "sha256:9cefe65be0f1e0510adec661cb8b1ed850af2054a"
        "1eeee7a6eb5355f25fb2fae"
    )
    assert left.mapping()["schema_version"] == CONTENT_BRIEF_SCHEMA


def test_custom_durations_and_relative_audio_resolve(tmp_path: Path) -> None:
    payload = _brief_payload()
    payload["durations_s"] = [2.5, 2.5, 2.5, 2.5]
    payload["audio_paths"] = [
        "audio/one.wav", "audio/two.wav", "audio/three.wav", "audio/four.wav"
    ]
    brief, plates = _layout(tmp_path, payload)
    audio = tmp_path / "audio"
    audio.mkdir()
    for name in ("one.wav", "two.wav", "three.wav", "four.wav"):
        _write_real_wav(audio / name, 2.5)

    inputs = build_run_film_inputs(
        load_content_brief(brief), plates, run_dir=tmp_path / "run"
    )
    assert inputs["durations"] == [2.5, 2.5, 2.5, 2.5]
    assert inputs["audio_paths"] == [
        str(audio / "one.wav"), str(audio / "two.wav"),
        str(audio / "three.wav"), str(audio / "four.wav"),
    ]
    assert inputs["script_path"].read_text(encoding="utf-8").startswith(
        "Tess: Tomorrow's sunrise is only a project.\n"
    )
    assert set(inputs["plates"]) == {"anchor", "Tess", "Rho"}


@pytest.mark.parametrize(
    ("output", "message"),
    [("not-a-number", "non-numeric"), ("0", "non-positive"), ("nan", "non-positive")],
)
def test_probe_output_rejects_unsafe_durations(output: str, message: str) -> None:
    with pytest.raises(ContentBriefError, match=message):
        _probe_duration_output(output, Path("guide.wav"))


def test_audio_duration_tolerance_is_one_microsecond() -> None:
    path = Path("guide.wav")
    _check_audio_duration(1, path, 2.0, 2.0000005)
    with pytest.raises(ContentBriefError, match="audio duration mismatch"):
        _check_audio_duration(1, path, 2.0, 2.0000011)


def test_probe_timeout_fails_closed_with_real_ffprobe(tmp_path: Path) -> None:
    guide = tmp_path / "guide.wav"
    _write_real_wav(guide, DEFAULT_DURATION_S)

    with pytest.raises(ContentBriefError, match="ffprobe timed out"):
        _probe_audio_duration(guide, timeout_s=0.000001)
    assert not (tmp_path / "run").exists()


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ({"schema_version": "wrong"}, "schema_version"),
        ({"title": ""}, "title"),
        ({"characters": [{"name": "Tess", "sn_tag": "S1", "description": "x"}]},
         "at least two"),
        ({"dialogue": [{"speaker": "Unknown", "text": "hello"}]}, "character roster"),
        ({"durations_s": [1.0]}, "one positive value"),
        ({"audio_paths": ["one.wav"]}, "one path"),
        ({"audio_filler_policy": {"mode": "tail_silence"}}, "unknown content-brief"),
        ({"extra": True}, "unknown content-brief"),
    ],
)
def test_invalid_briefs_fail_closed(
    tmp_path: Path, mutation: dict, message: str
) -> None:
    payload = _brief_payload() | mutation
    brief, plates = _layout(tmp_path, payload)
    run_dir = tmp_path / "run"
    with pytest.raises(ContentBriefError, match=message):
        load_content_brief(brief)
    assert not run_dir.exists()


def test_audio_duration_mismatch_fails_before_run_side_effects(tmp_path: Path) -> None:
    payload = _brief_payload()
    payload["durations_s"] = [4.458333333333333] * 4
    payload["audio_paths"] = [
        "one.wav", "two.wav", "three.wav", "four.wav"
    ]
    brief, plates = _layout(tmp_path, payload)
    for name in ("one.wav", "two.wav", "three.wav", "four.wav"):
        _write_real_wav(tmp_path / name, 2.333333)
    run_dir = tmp_path / "run"

    with pytest.raises(ContentBriefError, match="audio duration mismatch for turn 1"):
        build_run_film_inputs(
            load_content_brief(brief), plates, run_dir=run_dir
        )
    assert not run_dir.exists()


def test_cli_accepts_real_matching_guides(tmp_path: Path) -> None:
    payload = _brief_payload()
    payload["audio_paths"] = [
        "one.wav", "two.wav", "three.wav", "four.wav"
    ]
    brief, plates = _layout(tmp_path, payload)
    for name in ("one.wav", "two.wav", "three.wav", "four.wav"):
        _write_real_wav(tmp_path / name, DEFAULT_DURATION_S)
    output = tmp_path / "plans" / "plan.json"

    assert main([
        "--brief", str(brief), "--plates", str(plates), "--output", str(output)
    ]) == 0
    plan = json.loads(output.read_text(encoding="utf-8"))
    assert plan["summary"]["dry_run"] is True
    assert plan["summary"]["gpu_work"] is False
    assert plan["summary"]["queue_submitted"] is False
    for clip in plan["clips"]:
        assert clip["frames"] == 56
        assert clip["audio_length_frames"] == 56
        assert clip["audio_provenance"]["keeper_window_s"] == [0.0, DEFAULT_DURATION_S]
        check_guide_duration(
            clip["guide_duration_s"], clip["shot_duration_s"]
        )


def test_cli_rejects_bad_guides_without_artifacts(tmp_path: Path) -> None:
    cases: dict[str, tuple[dict, str]] = {
        "mismatch": (
            {
                "durations_s": [4.458333333333333] * 4,
                "audio_paths": ["one.wav", "two.wav", "three.wav", "four.wav"],
            },
            "audio duration mismatch for turn 1",
        ),
        "missing": (
            {"audio_paths": ["one.wav", "two.wav", "three.wav", "four.wav"]},
            "missing audio file",
        ),
        "corrupt": (
            {"audio_paths": ["one.wav", "two.wav", "three.wav", "four.wav"]},
            "cannot probe audio duration",
        ),
        "video_only": (
            {"audio_paths": ["one.wav", "two.wav", "three.wav", "four.mp4"]},
            "no audio stream",
        ),
    }
    for label, (mutation, message) in cases.items():
        case_dir = tmp_path / label
        case_dir.mkdir()
        brief, plates = _layout(case_dir, _brief_payload() | mutation)
        if label != "missing":
            for name in ("one.wav", "two.wav", "three.wav"):
                _write_real_wav(case_dir / name, DEFAULT_DURATION_S)
            if label == "mismatch":
                _write_real_wav(case_dir / "four.wav", 2.333333)
            elif label == "video_only":
                _write_video_only_mp4(case_dir / "four.mp4", DEFAULT_DURATION_S)
            else:
                (case_dir / "four.wav").write_bytes(b"not a wav")
        output = case_dir / "plans" / "plan.json"
        run_dir = case_dir / "run"

        with pytest.raises(ContentBriefError, match=message):
            main([
                "--brief", str(brief), "--plates", str(plates),
                "--output", str(output), "--run-dir", str(run_dir),
            ])
        assert not output.exists()
        assert not run_dir.exists()
        assert not (run_dir / "run_ledger.json").exists()
        assert not (run_dir / "jobs.db").exists()


def test_missing_plate_or_audio_fails_before_run_side_effects(tmp_path: Path) -> None:
    payload = _brief_payload()
    payload["audio_paths"] = ["missing.wav", "missing.wav", "missing.wav", "missing.wav"]
    brief, plates = _layout(tmp_path, payload)
    run_dir = tmp_path / "run"
    with pytest.raises(ContentBriefError, match="missing audio"):
        build_run_film_inputs(load_content_brief(brief), plates, run_dir=run_dir)
    assert not run_dir.exists()

    (plates / "Rho.png").unlink()
    with pytest.raises(ContentBriefError, match="missing plate for 'Rho'"):
        build_run_film_inputs(load_content_brief(brief), plates, run_dir=run_dir)
    assert not run_dir.exists()


def test_cli_creates_canonical_no_gpu_plan_without_queue(tmp_path: Path) -> None:
    brief, plates = _layout(tmp_path)
    output = tmp_path / "plans" / "plan.json"
    assert main([
        "--brief", str(brief), "--plates", str(plates), "--output", str(output)
    ]) == 0
    plan = json.loads(output.read_text(encoding="utf-8"))
    assert plan["schema_version"] == "wangp-dspy.content-plan/v1"
    assert plan["summary"] == {
        "clip_count": 4,
        "speakers": ["Tess", "Rho", "Tess", "Rho"],
        "planned_duration_s": 9.332,
        "dry_run": True,
        "gpu_work": False,
        "queue_submitted": False,
    }
    assert plan["repository"]["commit_sha"]
    assert plan["brief_hash"].startswith("sha256:")
    assert len(plan["clips"]) == 4
    assert output.parent.joinpath("run", "run_ledger.json").is_file()
    assert not output.parent.joinpath("run", "jobs.db").exists()
