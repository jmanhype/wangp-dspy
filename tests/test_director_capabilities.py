"""Real-process no-GPU coverage for governed director composition."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
from functools import lru_cache
from pathlib import Path
from typing import Any

import pytest

from services.jobs.queue import JobQueue


ROOT = Path(__file__).resolve().parents[1]
AUDIO = (
    ROOT
    / "datasets/runs/provenance/lf002-vibevoice-audition-20260916/audio/orin.wav"
)
AUDIO_SHA256 = "f3d66cac4458d0d33870ff6dc97df75eff95d57b154180dd303be4f955c91857"
AUDIO_DURATION = 2.1333333333333333
HOST_KEYS = (
    "WANGP_SSH_TARGET",
    "WANGP_WGP_ROOT",
    "WANGP_PULL_ROOT",
    "WANGP_WGP_PYTHON",
)


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        digest.update(str(path.relative_to(root)).encode() + b"\0")
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _environment(tmp_path: Path) -> tuple[dict[str, str], Path]:
    forbidden = tmp_path / "forbidden-bin"
    forbidden.mkdir()
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
    for key in HOST_KEYS:
        environment.pop(key, None)
    return environment, calls


def _wgp(*args: str, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["uv", "run", "--frozen", "--extra", "dev", "wgp", *args],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )


@lru_cache(maxsize=1)
def _live_cli_verbs() -> frozenset[str]:
    result = _wgp("--help", env=os.environ.copy())
    assert result.returncode == 0, result.stdout + result.stderr
    line = next(
        item
        for item in result.stdout.splitlines()
        if item.strip().startswith("{") and item.strip().endswith("}")
    )
    return frozenset(line.strip().strip("{}").split(","))


@lru_cache(maxsize=1)
def _live_director_verbs() -> frozenset[str]:
    result = _wgp("director", "--help", env=os.environ.copy())
    assert result.returncode == 0, result.stdout + result.stderr
    line = next(
        item
        for item in result.stdout.splitlines()
        if item.strip().startswith("{") and item.strip().endswith("}")
    )
    return frozenset(line.strip().strip("{}").split(","))


def _assert_next_command_resolves(command: str) -> None:
    tokens = command.split()
    assert tokens[0] == "wgp"
    assert tokens[1] in _live_cli_verbs(), command
    assert tokens[1] == "director"
    assert tokens[2] in _live_director_verbs(), command
    expected = {
        "plan": {"--request", "--db"},
        "enhance": {"--request", "--output-db"},
        "queue": {"--db"},
        "review": {"--db"},
    }[tokens[2]]
    assert expected <= set(tokens), command


def _audio_payload() -> dict[str, Any]:
    return {
        "path": str(AUDIO),
        "sha256": AUDIO_SHA256,
        "duration_s": AUDIO_DURATION,
    }


def _request_payload(mode: str = "prompt") -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_version": "wangp-dspy.director-request/v1",
        "mode": mode,
        "title": "Signal Room",
        "recipe_seed": 914,
        "review": {
            "mode": "auto" if mode == "music_video" else "manual",
            "manual_checkpoint_required": mode != "music_video",
            "reviewer": "operator",
        },
    }
    if mode == "prompt":
        payload.update(
            {
                "prompt": "A projected sunrise fails over an observatory dome.",
                "pacing": {
                    "strategy": "even",
                    "target_duration_s": 4.666666666666667,
                    "clip_count": 2,
                },
                "queue_enhancement": {
                    "intent": "replace_prompt",
                    "allowed_fields": ["prompt"],
                    "reason": "operator requested a narrower establishing idea",
                },
            }
        )
    elif mode in {"audio", "music_video"}:
        audio = _audio_payload()
        if mode == "music_video":
            audio["beats"] = [
                {
                    "time_s": 0.5,
                    "confidence": 0.99,
                    "measurement": "measured: committed fixture beat detector run",
                },
                {
                    "time_s": 1.2,
                    "confidence": 0.98,
                    "measurement": "measured: committed fixture beat detector run",
                },
            ]
        payload.update(
            {
                "audio": audio,
                "pacing": {
                    "strategy": "beat" if mode == "music_video" else "window_count",
                    "target_duration_s": AUDIO_DURATION,
                    **({"clip_count": 2} if mode == "audio" else {}),
                },
            }
        )
    else:
        payload.update(
            {
                "screenplay": {
                    "title": "Signal Room",
                    "characters": [
                        {"name": "Rho", "appearance": "silver coat", "voice": "calm analytical"},
                        {"name": "Tess", "appearance": "grey scarf", "voice": "brisk"},
                    ],
                    "scenes": [
                        {
                            "scene_index": 1,
                            "slugline": "INT. SIGNAL ROOM - NIGHT",
                            "duration_s": 2.0,
                            "characters": ["Rho", "Tess"],
                            "location": "signal room",
                            "states": [
                                {"name": "Rho", "appearance": "silver coat", "voice": "calm analytical"},
                                {"name": "Tess", "appearance": "grey scarf", "voice": "brisk"},
                            ],
                            "action": "Rho isolates the repeating signal.",
                        },
                        {
                            "scene_index": 2,
                            "slugline": "EXT. OBSERVATORY DOME - DAWN",
                            "duration_s": 2.666666666666667,
                            "characters": ["Rho", "Tess"],
                            "location": "observatory dome",
                            "states": [
                                {"name": "Rho", "appearance": "rain cloak", "voice": "calm analytical"},
                                {"name": "Tess", "appearance": "grey scarf", "voice": "brisk"},
                            ],
                            "action": "Tess points at the failing projection.",
                        },
                    ],
                },
                "pacing": {"strategy": "even", "target_duration_s": 4.666666666666667},
            }
        )
    return payload


def _write_request(path: Path, payload: dict[str, Any]) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


@pytest.mark.parametrize("mode", ("prompt", "audio", "music_video", "screenplay"))
def test_every_mode_emits_deterministic_ordered_plans_in_human_and_json_modes(
    tmp_path: Path, mode: str
) -> None:
    environment, calls = _environment(tmp_path)
    request = _write_request(tmp_path / "request.json", _request_payload(mode))
    human_db = tmp_path / "human.db"
    first_db = tmp_path / "first.db"
    second_db = tmp_path / "second.db"
    human = _wgp(
        "director", "plan", "--request", str(request), "--db", str(human_db),
        env=environment,
    )
    first = _wgp(
        "director", "plan", "--request", str(request), "--db", str(first_db),
        "--json", env=environment,
    )
    second = _wgp(
        "director", "plan", "--request", str(request), "--db", str(second_db),
        "--json", env=environment,
    )
    assert human.returncode == first.returncode == second.returncode == 0, (
        human.stdout + human.stderr + first.stdout + first.stderr
    )
    assert "media_generated=false queue_submitted=false host_contact=false" in human.stdout
    first_payload = json.loads(first.stdout)
    second_payload = json.loads(second.stdout)
    first_payload.pop("queue")
    second_payload.pop("queue")
    assert second_payload == first_payload
    assert first_payload["mode"] == mode
    assert first_payload["capability_status"] == "planned"
    assert first_payload["summary"] == {
        "gpu_work": False,
        "host_contact": False,
        "queue_submitted": False,
        "media_generated": False,
        "generated_media_reviewed": False,
    }
    clips = first_payload["clips"]
    assert [clip["clip_index"] for clip in clips] == list(range(1, len(clips) + 1))
    assert [clip["overlap"]["frames"] for clip in clips] == [6] * (len(clips) - 1) + [0]
    assert all(clip["media"] is None for clip in clips)
    assert first_payload["planning_surfaces"][0] == {
        "import": "wangp.content",
        "function": "build_content_request",
        "call_path": (
            "wangp.content.build_content_request -> scripts.run_content_brief.main "
            "-> scripts.run_film.run_film -> services.director.wiring.plan_to_clips"
        ),
        "invoked": True,
        "consumed_output": "clips",
    }
    assert first_payload["source_duration_preserved"] is True
    if mode == "music_video":
        assert [clip["window"]["beat_evidence"] for clip in clips] == [
            [],
            [clips[1]["window"]["beat_evidence"][0]],
            [clips[2]["window"]["beat_evidence"][0]],
        ]
        assert first_payload["review"]["auto_advancement"] is True
    if mode == "screenplay":
        assert clips[1]["continuity"]["changes"] == [
            {
                "character": "Rho",
                "appearance": "rain cloak",
                "voice": "calm analytical",
                "from": {"appearance": "silver coat", "voice": "calm analytical"},
            }
        ]
        assert clips[1]["continuity"]["carried_forward"] == ["Tess"]
    assert calls.read_text(encoding="utf-8") == ""


@pytest.mark.parametrize("strategy", ("exact_timecode", "window_count"))
def test_exact_and_window_pacing_preserve_the_complete_target(
    tmp_path: Path, strategy: str
) -> None:
    environment, _calls = _environment(tmp_path)
    payload = _request_payload("prompt")
    if strategy == "exact_timecode":
        payload["pacing"] = {
            "strategy": strategy,
            "target_duration_s": 4.0,
            "exact_start_s": 0.0,
            "exact_end_s": 4.0,
        }
    else:
        payload["pacing"] = {
            "strategy": strategy,
            "target_duration_s": 4.0,
            "clip_count": 3,
        }
    request = _write_request(tmp_path / "request.json", payload)
    result = _wgp(
        "director", "plan", "--request", str(request),
        "--db", str(tmp_path / "plan.db"), "--json", env=environment,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    plan = json.loads(result.stdout)
    expected_count = 1 if strategy == "exact_timecode" else 3
    assert plan["clip_count"] == expected_count
    assert plan["duration_s"] == pytest.approx(4.0)
    assert [window["start_s"] for window in plan["pacing"]["windows"]] == (
        [0.0]
        if expected_count == 1
        else pytest.approx([0.0, 4 / 3, 8 / 3])
    )


def test_shot_plan_consumes_content_planner_output_and_changes_with_planner_input() -> None:
    from services.director.composition import DirectorRequest
    from services.director.plan_compiler import compile_director_request

    def compiled(prompt: str):
        payload = _request_payload("prompt")
        payload["prompt"] = prompt
        request = DirectorRequest.model_validate(payload)
        return compile_director_request(request).mapping()

    first = compiled("A projected sunrise fails over the observatory.")
    second = compiled("A hard rain closes the observatory.")
    assert first["base_planner"]["import"] == "wangp.content"
    assert first["base_planner"]["function"] == "build_content_request"
    assert first["base_planner"]["invoked"] is True
    assert first["base_planner"]["brief_hash"] != second["base_planner"]["brief_hash"]
    assert len(first["base_planner"]["clips"]) == len(first["clips"]) == 2
    for director_clip, planner_clip in zip(
        first["clips"], first["base_planner"]["clips"], strict=True
    ):
        assert director_clip["prompt"] == planner_clip["prompt"]
        assert director_clip["planner_clip"] == planner_clip
        assert "projected sunrise" in planner_clip["prompt"]
    assert all(
        left["identity"] != right["identity"]
        for left, right in zip(
            first["base_planner"]["clips"],
            second["base_planner"]["clips"],
            strict=True,
        )
    )
    assert all(
        "hard rain" in clip["prompt"]
        for clip in second["base_planner"]["clips"]
    )
    assert first["request_sha256"] != second["request_sha256"]
    assert first["base_planner"]["duration_accounting"][
        "planner_total_frames"
    ] == sum(clip["planner_clip"]["frames"] for clip in first["clips"])


def test_plan_records_are_immutable_undrainable_enhanceable_and_reconstructable(
    tmp_path: Path,
) -> None:
    environment, calls = _environment(tmp_path)
    datasets_before = _tree_digest(ROOT / "datasets")
    request = _write_request(tmp_path / "request.json", _request_payload("prompt"))
    database = tmp_path / "plans.db"
    result = _wgp(
        "director", "plan", "--request", str(request), "--db", str(database),
        "--json", env=environment,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    plan = json.loads(result.stdout)
    assert plan["queue"]["executable_jobs"] == 0
    database_before = database.read_bytes()

    connection = sqlite3.connect(database)
    with pytest.raises(sqlite3.IntegrityError, match="immutable"):
        connection.execute("UPDATE director_plan_records SET record='changed'")
    with pytest.raises(sqlite3.IntegrityError, match="immutable"):
        connection.execute("DELETE FROM director_plan_records")
    connection.close()

    queue_result = _wgp(
        "director", "queue", "--db", str(database), "--json", env=environment
    )
    assert queue_result.returncode == 0, queue_result.stdout + queue_result.stderr
    inspection = json.loads(queue_result.stdout)
    assert inspection["record_count"] == 2
    assert inspection["selected_job"] is None
    assert inspection["drainable"] is False
    assert inspection["mutation_performed"] is False
    assert database.read_bytes() == database_before

    admission_copy = tmp_path / "admission-copy.db"
    shutil.copy2(database, admission_copy)
    admission = JobQueue(admission_copy)
    try:
        assert admission.list_state("pending") == []
        assert admission.next_admissible() is None
    finally:
        admission.close()
    genuine = JobQueue(tmp_path / "genuine.db")
    try:
        job_id = genuine.submit(
            plan_ref="genuine-render",
            clips=[
                {
                    "clip_index": 1,
                    "status": "pending",
                    "kind": "ref2va_render",
                    "prompt": "genuine",
                    "seed": 1,
                    "video_length": 56,
                }
            ],
        )
        assert genuine.next_admissible() == job_id
    finally:
        genuine.close()

    enhancement = tmp_path / "enhancement.json"
    enhancement.write_text(
        json.dumps(
            {
                "schema_version": "wangp-dspy.director-enhancement-request/v1",
                "source_db": str(database),
                "changes": {"prompt": "A narrower projection flickers across the dome."},
                "provenance_reason": "operator requested a narrower establishing idea",
            }
        ),
        encoding="utf-8",
    )
    enhanced_db = tmp_path / "enhanced.db"
    enhanced = _wgp(
        "director", "enhance", "--request", str(enhancement),
        "--output-db", str(enhanced_db), "--json", env=environment,
    )
    assert enhanced.returncode == 0, enhanced.stdout + enhanced.stderr
    enhanced_payload = json.loads(enhanced.stdout)
    assert enhanced_payload["changed_fields"] == ["prompt"]
    assert enhanced_payload["source_mutated"] is False
    assert enhanced_payload["original_request_sha256"] == plan["request_sha256"]
    assert enhanced_payload["enhanced_request_sha256"] != plan["request_sha256"]
    assert database.read_bytes() == database_before

    for source in (database, enhanced_db):
        review = _wgp(
            "director", "review", "--db", str(source), "--json", env=environment
        )
        assert review.returncode == 0, review.stdout + review.stderr
        evidence = json.loads(review.stdout)
        assert evidence["all_match"] is True
        assert evidence["hidden_mutation"] is False
        assert all(
            item["recorded_clip_sha256"] == item["reconstructed_clip_sha256"]
            for item in evidence["records"]
        )
    assert _tree_digest(ROOT / "datasets") == datasets_before
    assert _hash(AUDIO) == AUDIO_SHA256
    assert calls.read_text(encoding="utf-8") == ""


def _failure_setup(tmp_path: Path, case: str) -> tuple[list[str], dict[str, str]]:
    environment, _calls = _environment(tmp_path)
    mode = "screenplay" if case == "unknown-character" else (
        "music_video" if case.startswith("beat") else "prompt"
    )
    if case in {"audio-file-missing", "audio-hash", "audio-duration"}:
        mode = "audio"
    payload = _request_payload(mode)
    request = _write_request(tmp_path / "request.json", payload)
    database = tmp_path / "plans.db"
    command = [
        "director", "plan", "--request", str(request),
        "--db", str(database), "--json",
    ]
    if case == "request-missing":
        request.unlink()
    elif case == "request-invalid":
        request.write_text("{", encoding="utf-8")
    elif case == "prompt-missing":
        payload.pop("prompt")
        _write_request(request, payload)
    elif case == "audio-source-missing":
        payload.update(
            {
                "mode": "audio",
                "prompt": None,
                "audio": None,
                "pacing": {"strategy": "even", "target_duration_s": AUDIO_DURATION},
            }
        )
        _write_request(request, payload)
    elif case == "screenplay-missing":
        payload.update({"mode": "screenplay", "prompt": None, "screenplay": None})
        _write_request(request, payload)
    elif case == "mode-conflict":
        payload["audio"] = _audio_payload()
        _write_request(request, payload)
    elif case == "unknown-character":
        payload["screenplay"]["scenes"][0]["characters"].append("Ghost")
        _write_request(request, payload)
    elif case == "pacing-unsupported":
        payload["pacing"]["strategy"] = "liquid"
        _write_request(request, payload)
    elif case == "pacing-invalid":
        payload["pacing"].update({"clip_count": 1, "max_clip_s": 0.5})
        _write_request(request, payload)
    elif case == "pacing-conflict":
        payload["pacing"] = {
            "strategy": "exact_timecode",
            "target_duration_s": 4.0,
            "exact_start_s": 0.5,
            "exact_end_s": 4.0,
        }
        _write_request(request, payload)
    elif case == "audio-file-missing":
        payload["audio"]["path"] = str(tmp_path / "absent.wav")
        _write_request(request, payload)
    elif case == "audio-hash":
        payload["audio"]["sha256"] = "d" * 64
        _write_request(request, payload)
    elif case == "audio-duration":
        payload["pacing"]["target_duration_s"] = 4.0
        _write_request(request, payload)
    elif case == "beats-missing":
        payload["audio"]["beats"] = []
        _write_request(request, payload)
    elif case == "beats-invalid":
        payload["audio"]["beats"][0]["measurement"] = "claimed:vendor"
        _write_request(request, payload)
    elif case == "review-conflict":
        payload["review"].update({"mode": "auto", "manual_checkpoint_required": True})
        _write_request(request, payload)
    elif case == "enhancement-unsupported":
        payload["queue_enhancement"]["intent"] = "rename_everything"
        payload["queue_enhancement"]["allowed_fields"] = ["prompt", "title"]
        _write_request(request, payload)
    elif case == "queue-exists":
        database.write_bytes(b"exists")
    elif case in {
        "enhancement-request-missing",
        "enhancement-request-invalid",
        "queue-output-exists",
        "queue-enhancement-invalid",
    }:
        source_mode = "prompt" if case != "queue-enhancement-invalid" else "audio"
        source_request = _write_request(
            tmp_path / "source-request.json", _request_payload(source_mode)
        )
        source_db = tmp_path / "source.db"
        planned = _wgp(
            "director", "plan", "--request", str(source_request),
            "--db", str(source_db), "--json", env=environment,
        )
        assert planned.returncode == 0, planned.stdout + planned.stderr
        enhancement = tmp_path / "enhancement.json"
        document = {
            "schema_version": "wangp-dspy.director-enhancement-request/v1",
            "source_db": str(source_db),
            "changes": {"prompt": "A revised authorized prompt."},
            "provenance_reason": "operator revision",
        }
        enhancement.write_text(
            "{" if case == "enhancement-request-invalid" else json.dumps(document),
            encoding="utf-8",
        )
        output = tmp_path / "enhanced.db"
        if case == "queue-output-exists":
            output.write_bytes(b"exists")
        command = [
            "director", "enhance", "--request", str(enhancement),
            "--output-db", str(output), "--json",
        ]
        if case == "enhancement-request-missing":
            enhancement.unlink()
    elif case == "reconstruction-database-missing":
        command = ["director", "review", "--db", str(tmp_path / "missing.db"), "--json"]
    elif case == "reconstruction-records-missing":
        JobQueue(database).close()
        command = ["director", "review", "--db", str(database), "--json"]
    elif case == "reconstruction-database-invalid":
        database.write_bytes(b"not sqlite")
        command = ["director", "review", "--db", str(database), "--json"]
    elif case == "reconstruction-record-invalid":
        connection = sqlite3.connect(database)
        connection.execute(
            "CREATE TABLE director_plan_records (record_id TEXT PRIMARY KEY, "
            "request_sha256 TEXT NOT NULL, clip_index INTEGER NOT NULL, "
            "record TEXT NOT NULL, created_at REAL NOT NULL)"
        )
        connection.execute(
            "INSERT INTO director_plan_records VALUES ('bad', 'x', 1, '{}', 0)"
        )
        connection.commit()
        connection.close()
        command = ["director", "review", "--db", str(database), "--json"]
    return command, environment


@pytest.mark.parametrize(
    ("case", "code"),
    (
        ("request-missing", "DIRECTOR_REQUEST_MISSING"),
        ("request-invalid", "DIRECTOR_REQUEST_INVALID"),
        ("prompt-missing", "DIRECTOR_PROMPT_MISSING"),
        ("audio-source-missing", "DIRECTOR_AUDIO_MISSING"),
        ("screenplay-missing", "DIRECTOR_SCREENPLAY_MISSING"),
        ("mode-conflict", "DIRECTOR_MODE_CONFLICT"),
        ("unknown-character", "DIRECTOR_CHARACTER_REFERENCE_UNKNOWN"),
        ("pacing-unsupported", "DIRECTOR_PACING_UNSUPPORTED"),
        ("pacing-invalid", "DIRECTOR_PACING_INVALID"),
        ("pacing-conflict", "DIRECTOR_PACING_CONFLICT"),
        ("audio-file-missing", "DIRECTOR_AUDIO_MISSING"),
        ("audio-hash", "DIRECTOR_AUDIO_HASH_MISMATCH"),
        ("audio-duration", "DIRECTOR_AUDIO_DURATION_MISMATCH"),
        ("beats-missing", "DIRECTOR_AUDIO_BEATS_MISSING"),
        ("beats-invalid", "DIRECTOR_AUDIO_BEATS_INVALID"),
        ("review-conflict", "DIRECTOR_REVIEW_MODE_CONFLICT"),
        ("enhancement-unsupported", "DIRECTOR_QUEUE_ENHANCEMENT_UNSUPPORTED"),
        ("queue-exists", "DIRECTOR_QUEUE_EXISTS"),
        ("enhancement-request-missing", "DIRECTOR_ENHANCEMENT_REQUEST_MISSING"),
        ("enhancement-request-invalid", "DIRECTOR_ENHANCEMENT_REQUEST_INVALID"),
        ("queue-output-exists", "DIRECTOR_QUEUE_OUTPUT_EXISTS"),
        ("queue-enhancement-invalid", "DIRECTOR_QUEUE_ENHANCEMENT_INVALID"),
        ("reconstruction-database-missing", "DIRECTOR_RECONSTRUCTION_DATABASE_MISSING"),
        ("reconstruction-records-missing", "DIRECTOR_RECONSTRUCTION_RECORDS_MISSING"),
        ("reconstruction-database-invalid", "DIRECTOR_RECONSTRUCTION_DATABASE_INVALID"),
        ("reconstruction-record-invalid", "DIRECTOR_RECONSTRUCTION_RECORD_INVALID"),
    ),
)
def test_every_typed_failure_class_has_human_json_remediation_and_live_next_command(
    tmp_path: Path, case: str, code: str
) -> None:
    command, environment = _failure_setup(tmp_path, case)
    human = _wgp(*command[:-1], env=environment)
    machine = _wgp(*command, env=environment)
    assert human.returncode == machine.returncode == 2, (
        human.stdout + human.stderr + machine.stdout + machine.stderr
    )
    human_text = human.stdout + human.stderr
    assert f"diagnostic code={code}" in human_text
    assert "next: wgp director" in human_text
    diagnostic = json.loads(machine.stdout)["diagnostics"][0]
    assert diagnostic["code"] == code
    assert diagnostic["severity"] == "error"
    assert diagnostic["remediation"]
    _assert_next_command_resolves(diagnostic["next_command"])
