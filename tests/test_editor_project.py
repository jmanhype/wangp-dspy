"""Real-process no-GPU coverage for the non-destructive editor surface."""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
from functools import lru_cache
from pathlib import Path
from typing import Any

import pytest

from services.editor.assembly_exporter import export_project, write_export
from services.editor.project_store import ProjectStore
from services.jobs.queue import JobQueue
from wangp.editor_project import (
    Clip,
    EditorProject,
    PROJECT_SCHEMA,
    ReviewDecision,
    ReviewMark,
    Track,
    TrackKind,
    Transition,
    TransitionKind,
)


ROOT = Path(__file__).resolve().parents[1]
VIDEO = ROOT / "datasets/runs/provenance/lf002-vibevoice-film-20260917/cut1.mp4"
AUDIO = ROOT / "datasets/runs/provenance/lf002-vibevoice-audition-20260916/audio/orin.wav"
IMAGE = ROOT / "assets/acceptance/face_soul.png"


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _environment(tmp_path: Path) -> tuple[dict[str, str], Path]:
    forbidden = tmp_path / "forbidden-bin"
    forbidden.mkdir(exist_ok=True)
    calls = tmp_path / "host-calls"
    calls.write_text("", encoding="utf-8")
    for name in ("ssh", "curl", "wget", "nvidia-smi"):
        command = forbidden / name
        command.write_text(
            f'#!/bin/sh\nprintf "%s\\n" "{name} $*" >> {calls}\nexit 99\n',
            encoding="utf-8",
        )
        command.chmod(0o755)
    environment = os.environ.copy()
    environment["PATH"] = f"{forbidden}:{environment['PATH']}"
    environment["WANGP_CONFIG"] = str(tmp_path / "absent-wangp.toml")
    for key in (
        "WANGP_SSH_TARGET", "WANGP_WGP_ROOT", "WANGP_PULL_ROOT", "WANGP_WGP_PYTHON"
    ):
        environment.pop(key, None)
    return environment, calls


def _wgp(
    *args: str, cwd: Path = ROOT, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    selected = os.environ.copy() if env is None else env
    return subprocess.run(
        ["uv", "run", "--frozen", "--extra", "dev", "wgp", *args],
        cwd=cwd,
        env=selected,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )


@lru_cache(maxsize=1)
def _live_verbs() -> frozenset[str]:
    result = _wgp("--help")
    assert result.returncode == 0, result.stdout + result.stderr
    match = re.search(r"usage: wgp .*?\{([^}]+)\}", result.stdout, flags=re.DOTALL)
    assert match is not None
    return frozenset(match.group(1).split(","))


@lru_cache(maxsize=1)
def _live_editor_verbs() -> frozenset[str]:
    result = _wgp("editor", "--help")
    assert result.returncode == 0, result.stdout + result.stderr
    match = re.search(r"usage: wgp editor .*?\{([^}]+)\}", result.stdout, flags=re.DOTALL)
    assert match is not None
    return frozenset(match.group(1).split(","))


def _assert_next_command_resolves(command: str) -> None:
    tokens = command.split()
    assert len(tokens) >= 3, command
    assert tokens[:2] == ["wgp", "editor"], command
    assert tokens[0:2][1] in _live_verbs(), command
    assert tokens[2] in _live_editor_verbs(), command
    expected = {
        "validate": {"--project"},
        "export": {"--project", "--out"},
    }[tokens[2]]
    assert expected <= set(tokens), command


def _workspace(tmp_path: Path) -> tuple[ProjectStore, EditorProject, dict[str, str], dict[str, Path]]:
    original_hashes = {path: _hash(path) for path in (VIDEO, AUDIO, IMAGE)}
    project_path = tmp_path / "project" / "lf002-edit.wgp-editor.json"
    store = ProjectStore(project_path)
    video = store.import_source(VIDEO, TrackKind.video, "video-cut")
    audio = store.import_source(AUDIO, TrackKind.audio, "voice")
    image = store.import_source(IMAGE, TrackKind.image, "plate")
    copied = {
        asset.asset_id: store.resolve_source(asset)
        for asset in (video, audio, image)
    }
    copied_hashes = {path: _hash(path) for path in copied.values()}
    project = EditorProject(
        schema_version=PROJECT_SCHEMA,
        name="LF002 governed edit",
        reviewer="operator",
        revision=0,
        sources=(video, audio, image),
        tracks=(
            Track(
                track_id="video", kind=TrackKind.video, name="picture", order=0,
                clips=(
                    Clip(clip_id="video-1", kind=TrackKind.video, source_id=video.asset_id, label="opening observatory", timeline_start_s=0.0, timeline_duration_s=2.0, source_in_s=0.0, source_out_s=2.0),
                    Clip(clip_id="video-2", kind=TrackKind.video, source_id=video.asset_id, label="continuation observatory", timeline_start_s=2.0, timeline_duration_s=2.0, source_in_s=2.0, source_out_s=4.0),
                ),
            ),
            Track(track_id="audio", kind=TrackKind.audio, name="voice", order=1, clips=(Clip(clip_id="audio-1", kind=TrackKind.audio, source_id=audio.asset_id, label="voice take", timeline_start_s=0.0, timeline_duration_s=4.0, source_in_s=0.0, source_out_s=4.0),)),
            Track(track_id="image", kind=TrackKind.image, name="still", order=2, clips=(Clip(clip_id="image-1", kind=TrackKind.image, source_id=image.asset_id, label="identity plate", timeline_start_s=0.0, timeline_duration_s=4.0, source_in_s=0.0, source_out_s=4.0),)),
            Track(track_id="text", kind=TrackKind.text, name="captions", order=3, clips=(
                Clip(clip_id="text-1", kind=TrackKind.text, label="caption one", text="First decision", timeline_start_s=0.0, timeline_duration_s=2.0, source_in_s=0.0, source_out_s=2.0),
                Clip(clip_id="text-2", kind=TrackKind.text, label="caption two", text="Second decision", timeline_start_s=2.0, timeline_duration_s=2.0, source_in_s=2.0, source_out_s=4.0),
            )),
        ),
        transitions=(Transition(transition_id="video-cut", kind=TransitionKind.cut, from_clip_id="video-1", to_clip_id="video-2", duration_s=0.0),),
        review_marks=(ReviewMark(mark_id="review-1", clip_id="video-1", decision=ReviewDecision.comment, reviewer="operator", comment="hold original framing", revision=0),),
    )
    store = ProjectStore.create(project_path, project)
    return store, project, {**original_hashes, **copied_hashes}, copied


def test_round_trip_history_edits_and_non_destruction(tmp_path: Path) -> None:
    store, initial, before, copied = _workspace(tmp_path)
    assert store.source_manifest() == {
        source.asset_id: source.sha256 for source in initial.sources
    }

    moved = store.edit("move caption", lambda project: project.move_clip("text-2", 3.0))
    trimmed = store.edit("trim second shot", lambda project: project.trim_clip("video-2", 2.0, 3.5, 1.5))
    reordered = store.edit("reorder captions", lambda project: project.reorder_track("text", ("text-2", "text-1")))
    assert [entry.operation for entry in reordered.history] == ["import", "move caption", "trim second shot", "reorder captions"]
    assert reordered.project.revision == 3
    assert reordered.history[2].project.sources == initial.sources
    assert reordered.history[2].project.review_marks == initial.review_marks
    assert reordered.project.tracks[3].clips[0].clip_id == "text-2"
    assert reordered.project.tracks[3].clips[0].timeline_start_s == 0.0
    assert reordered.project.tracks[3].clips[1].timeline_start_s == 3.0

    undone = store.undo()
    assert undone.project == trimmed.project
    undone_again = store.undo()
    assert undone_again.project == moved.project
    redone = store.redo()
    assert redone.project == trimmed.project
    reloaded = store.load()
    assert reloaded.project == trimmed.project
    assert {path: _hash(path) for path in (*copied.values(), VIDEO, AUDIO, IMAGE)} == before


def test_deterministic_export_round_trip_and_real_queue_consumption(tmp_path: Path) -> None:
    environment, calls = _environment(tmp_path)
    store, _, _, _ = _workspace(tmp_path)
    store.edit("move caption", lambda project: project.move_clip("text-2", 3.0))
    current = store.load().project
    first = write_export(export_project(store, current), tmp_path / "exports/one.json")
    second = write_export(export_project(store, current), tmp_path / "exports/two.json")
    round_trip_root = tmp_path / "roundtrip"
    shutil.copytree(tmp_path / "project", round_trip_root)
    round_trip_store = ProjectStore(round_trip_root / "lf002-edit.wgp-editor.json")
    round_trip = write_export(export_project(round_trip_store), tmp_path / "exports/round-trip.json")
    assert first.read_bytes() == second.read_bytes() == round_trip.read_bytes()
    payload = json.loads(first.read_text(encoding="utf-8"))
    assert payload["director"]["import"] == "services.director.plan_compiler.compile_director_request"
    assert payload["director"]["invoked"] is True
    assert payload["director"]["plan"]["base_planner"]["invoked"] is True
    assert payload["assembly"]["import"] == "predict.assembler.MultiShotAssembler.assemble"
    assert len(payload["assembly"]["continuity_digest"]) == 64
    assert payload["summary"] == {
        "gpu_work": False, "host_contact": False, "media_generated": False,
        "generated_media_reviewed": False, "non_destructive": True,
    }
    assert calls.read_text(encoding="utf-8") == ""

    queue_path = tmp_path / "queue/jobs.db"
    queued = _wgp(
        "editor", "export", "--project", str(store.path), "--out", str(tmp_path / "exports/cli.json"),
        "--queue-db", str(queue_path), "--json", env=environment,
    )
    assert queued.returncode == 0, queued.stdout + queued.stderr
    assert (tmp_path / "exports/cli.json").read_bytes() == first.read_bytes()
    result = json.loads(queued.stdout)
    assert result["export"]["queue_submitted"] is True
    queue = JobQueue(queue_path)
    try:
        pending = queue.list_state("pending")
        selected = queue.next_admissible()
    finally:
        queue.close()
    assert pending == [result["export"]["queue_job_id"]]
    assert selected == result["export"]["queue_job_id"]
    assert calls.read_text(encoding="utf-8") == ""


def test_export_changes_when_upstream_editor_input_changes(tmp_path: Path) -> None:
    store, _, _, _ = _workspace(tmp_path)
    project = store.load().project
    before = export_project(store, project)
    renamed = project.model_copy(update={"name": "LF002 revised edit"})
    after_name = export_project(store, renamed)
    assert before["director"]["request"]["title"] != after_name["director"]["request"]["title"]
    assert before["director"]["plan"]["request_sha256"] != after_name["director"]["plan"]["request_sha256"]

    changed_clip = next(clip for clip in project.tracks[0].clips if clip.clip_id == "video-2").model_copy(update={"label": "later observatory"})
    relabelled = project.replace_clip(changed_clip)
    after_label = export_project(store, relabelled)
    assert before["assembly"]["continuity_digest"] != after_label["assembly"]["continuity_digest"]
    assert before["project_sha256"] != after_label["project_sha256"]


def test_cli_success_and_every_typed_failure_has_live_next_command(tmp_path: Path) -> None:
    environment, calls = _environment(tmp_path)
    store, _, _, copied = _workspace(tmp_path)
    store.edit("move caption", lambda project: project.move_clip("text-2", 3.0))
    human_validate = _wgp("editor", "validate", "--project", str(store.path), env=environment)
    json_validate = _wgp("editor", "validate", "--project", str(store.path), "--json", env=environment)
    assert human_validate.returncode == json_validate.returncode == 0
    assert "sources=3 verified=true" in human_validate.stdout
    validation = json.loads(json_validate.stdout)
    assert validation["sources_verified"] is True
    assert validation["source_count"] == 3

    human_export = _wgp("editor", "export", "--project", str(store.path), "--out", str(tmp_path / "human-export.json"), env=environment)
    json_export = _wgp("editor", "export", "--project", str(store.path), "--out", str(tmp_path / "json-export.json"), "--json", env=environment)
    assert human_export.returncode == json_export.returncode == 0
    assert "queue_submitted=false" in human_export.stdout
    exported = json.loads(json_export.stdout)
    assert exported["schema_version"] == "wangp-dspy.editor-export/v1"

    missing_project = _wgp("editor", "validate", "--project", str(tmp_path / "absent.json"), "--json", env=environment)
    assert missing_project.returncode == 2
    missing_diagnostic = json.loads(missing_project.stdout)["diagnostics"][0]
    assert missing_diagnostic["code"] == "EDITOR_PROJECT_MISSING"
    _assert_next_command_resolves(missing_diagnostic["next_command"])

    unsupported_root = tmp_path / "unsupported"
    shutil.copytree(tmp_path / "project", unsupported_root)
    unsupported_path = unsupported_root / "lf002-edit.wgp-editor.json"
    unsupported = json.loads(unsupported_path.read_text(encoding="utf-8"))
    unsupported["history"][0]["project"]["schema_version"] = "wangp-dspy.editor-project/v0"
    unsupported_path.write_text(json.dumps(unsupported), encoding="utf-8")
    schema_result = _wgp("editor", "validate", "--project", str(unsupported_path), "--json", env=environment)
    assert schema_result.returncode == 2
    schema_diagnostic = json.loads(schema_result.stdout)["diagnostics"][0]
    assert schema_diagnostic["code"] == "EDITOR_PROJECT_SCHEMA_UNSUPPORTED"
    _assert_next_command_resolves(schema_diagnostic["next_command"])

    copied["voice"].unlink()
    source_missing = _wgp("editor", "validate", "--project", str(store.path), "--json", env=environment)
    assert source_missing.returncode == 2
    source_diagnostic = json.loads(source_missing.stdout)["diagnostics"][0]
    assert source_diagnostic["code"] == "EDITOR_SOURCE_MISSING"
    _assert_next_command_resolves(source_diagnostic["next_command"])
    shutil.copyfile(AUDIO, copied["voice"])

    with copied["plate"].open("ab") as plate:
        plate.write(b"mutation")
    mutated = _wgp("editor", "export", "--project", str(store.path), "--out", str(tmp_path / "failed.json"), "--json", env=environment)
    assert mutated.returncode == 2
    assert not (tmp_path / "failed.json").exists()
    mutation_diagnostic = json.loads(mutated.stdout)["diagnostics"][0]
    assert mutation_diagnostic["code"] == "EDITOR_SOURCE_HASH_MISMATCH"
    _assert_next_command_resolves(mutation_diagnostic["next_command"])
    shutil.copyfile(IMAGE, copied["plate"])
    assert calls.read_text(encoding="utf-8") == ""


def test_editor_model_rejects_overlap_and_bad_references(tmp_path: Path) -> None:
    _, project, _, _ = _workspace(tmp_path)
    overlapping = project.tracks[0].clips[1].model_copy(update={"timeline_start_s": 1.0})
    with pytest.raises(ValueError, match="overlap"):
        project.replace_clip(overlapping)
    bad_transition = project.model_copy(update={
        "transitions": (Transition(transition_id="bad", kind=TransitionKind.cut, from_clip_id="audio-1", to_clip_id="video-2", duration_s=0.0),),
    })
    with pytest.raises(ValueError, match="video transitions"):
        EditorProject.model_validate(bad_transition.model_dump())
