from __future__ import annotations

import json
from pathlib import Path

import pytest

from predict.content_brief import (
    CONTENT_BRIEF_SCHEMA,
    ContentBriefError,
    build_run_film_inputs,
    load_content_brief,
)
from scripts.run_content_brief import main


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
        (audio / name).write_bytes(b"wav")

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
    ("mutation", "message"),
    [
        ({"schema_version": "wrong"}, "schema_version"),
        ({"title": ""}, "title"),
        ({"characters": [{"name": "Tess", "sn_tag": "S1", "description": "x"}]},
         "at least two"),
        ({"dialogue": [{"speaker": "Unknown", "text": "hello"}]}, "character roster"),
        ({"durations_s": [1.0]}, "one positive value"),
        ({"audio_paths": ["one.wav"]}, "one path"),
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
