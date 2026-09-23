"""Real-process no-GPU coverage for typed sound-effect planning."""
from __future__ import annotations

import hashlib
import json
import math
import os
import sqlite3
import struct
import subprocess
import wave
from functools import lru_cache
from pathlib import Path

import pytest

from services.audio_post.plan_compiler import compile_audio_post_request
from services.jobs.queue import JobQueue

from predict.audio_post import (
    AudioPostOperation,
    AudioPostRequest,
    attach_manifest_model,
    load_audio_post_model_manifest,
)


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "datasets/runs/provenance/lf002-vibevoice-film-20260917/cut1.mp4"
HOST_KEYS = (
    "WANGP_SSH_TARGET", "WANGP_WGP_ROOT", "WANGP_PULL_ROOT",
    "WANGP_WGP_PYTHON",
)


def _models(path: Path) -> None:
    entries = [
        {
            "family": family, "preset": preset, "sha256": digest * 64,
            "license": f"operator-recorded {family} license", "license_accepted": True,
            "source": f"operator {family} inventory", "usage_constraint": "recorded constraint",
            "vram_profile": vram,
        }
        for family, preset, digest, vram in (
            ("stable_audio", "sound_effect", "a", "16gb"),
            ("vibevoice", "revoice", "b", "24gb"),
            ("deepfilternet", "refinement", "c", "12gb"),
        )
    ]
    path.write_text(json.dumps({"models": entries}), encoding="utf-8")


def _voice(path: Path) -> Path:
    rate, frames = 24_000, 48_000
    with wave.open(str(path), "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(rate)
        audio.writeframes(b"".join(
            struct.pack("<h", int(12000 * math.sin(2 * math.pi * 180 * frame / rate)))
            for frame in range(frames)
        ))
    return path


def _request(path: Path, operation: str = "sfx") -> Path:
    family = {"sfx": "stable_audio", "revoice": "vibevoice", "refine": "deepfilternet"}[operation]
    preset = {"sfx": "sound_effect", "revoice": "revoice", "refine": "refinement"}[operation]
    request = {
        "schema_version": "wangp-dspy.audio-post-request/v1",
        "model": {"family": family, "preset": preset},
        "operation": operation,
        "source": {
            "path": str(SOURCE), "sha256": _hash(SOURCE), "immutable": True,
            "video": {"index": 0, "codec_type": "video", "duration_s": 2.333333},
            "audio": {"index": 1, "codec_type": "audio", "duration_s": 2.304},
        },
        "output": {
            "container": "mp4" if operation in {"revoice", "refine"} else "wav",
            "codec": "aac" if operation in {"revoice", "refine"} else "pcm_s16le",
            "sample_rate_hz": 48000, "channels": 2,
        },
        "output_path_planned": str(path.parent / f"{operation}-planned.{'mp4' if operation != 'sfx' else 'wav'}"),
        "recipe_seed": 907,
    }
    if operation == "sfx":
        request["prompt"] = "distant metal gate latch with dry room tail"
        request["duration_s"] = 2.3
    elif operation == "revoice":
        voice = _voice(path.parent / "target-voice.wav")
        request["voice"] = {
            "path": str(voice), "sha256": _hash(voice), "role": "primary",
            "duration_s": 2.0, "source": "operator-authorized reference",
            "license": "internal evaluation only", "consent_ref": "consent-record-1",
        }
    else:
        request["refinement"] = {
            "mode": "denoise_and_loudness", "noise_reduction_db": 6.0, "target_lufs": -18.0,
        }
    path.write_text(json.dumps(request), encoding="utf-8")
    return path


def _environment(tmp_path: Path) -> tuple[dict[str, str], Path]:
    forbidden = tmp_path / "forbidden-bin"
    forbidden.mkdir()
    calls = tmp_path / "host-calls"
    calls.write_text("", encoding="utf-8")
    for name in ("ssh", "nvidia-smi", "curl", "wget"):
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


def _wgp(*args: str, cwd: Path, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["uv", "run", "--frozen", "--extra", "dev", "wgp", *args],
        cwd=cwd, env=env, text=True, capture_output=True, timeout=120, check=False,
    )


@lru_cache(maxsize=1)
def _live_cli_verbs() -> frozenset[str]:
    help_text = _wgp("--help", cwd=ROOT, env=os.environ.copy())
    assert help_text.returncode == 0, help_text.stdout + help_text.stderr
    choice_line = next(
        line for line in help_text.stdout.splitlines()
        if line.strip().startswith("{") and line.strip().endswith("}")
    )
    return frozenset(choice_line.strip().strip("{}").split(","))


@lru_cache(maxsize=1)
def _live_sfx_verbs() -> frozenset[str]:
    help_text = _wgp("sfx", "--help", cwd=ROOT, env=os.environ.copy())
    assert help_text.returncode == 0, help_text.stdout + help_text.stderr
    choice_line = next(
        line for line in help_text.stdout.splitlines()
        if line.strip().startswith("{") and line.strip().endswith("}")
    )
    return frozenset(choice_line.strip().strip("{}").split(","))


def _assert_next_command_resolves_against_live_cli(command: str) -> None:
    tokens = command.split()
    assert tokens[0] == "wgp"
    assert len(tokens) >= 2
    assert tokens[1] in _live_cli_verbs(), command
    if tokens[1] == "sfx":
        assert len(tokens) >= 3
        assert tokens[2] in _live_sfx_verbs(), command
    assert not command.startswith("wgp audio "), command


def _tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        digest.update(str(path.relative_to(root)).encode() + b"\0")
        digest.update(path.read_bytes())
    return digest.hexdigest()


@pytest.mark.parametrize("operation", ("sfx", "revoice", "refine"))
def test_every_mode_plans_deterministically_without_output_or_host_calls(
    tmp_path: Path, operation: str
) -> None:
    environment, calls = _environment(tmp_path)
    models, request = tmp_path / "models.json", tmp_path / "request.json"
    _models(models)
    _request(request, operation)
    verb = {"sfx": "effect", "revoice": "revoice", "refine": "refine"}[operation]
    args = ("sfx", verb, "--request", str(request), "--models", str(models))
    human = _wgp(*args, cwd=ROOT, env=environment)
    first = _wgp(*args, "--json", cwd=ROOT, env=environment)
    second = _wgp(*args, "--json", cwd=ROOT, env=environment)
    assert human.returncode == first.returncode == second.returncode == 0, first.stdout + first.stderr
    assert "audio_created=false video_changed=false" in human.stdout
    assert second.stdout == first.stdout
    plan = json.loads(first.stdout)
    record = plan["records"][0]
    assert plan["capability_status"] == "planned"
    assert record["video_fixed"] == {
        "immutable": True, "source_video_sha256": _hash(SOURCE),
        "transformations": [], "video_bytes_changed": False,
        "measurement_status": "not verified - requires authorized host run",
    }
    assert record["plan_only"] is True and record["executable"] is False
    assert record["command_planned"]["graph"][1]["stage"] == "hold_video_fixed"
    assert plan["summary"] == {
        "gpu_work": False, "audio_created": False, "video_changed": False,
        "queue_submitted": False, "host_contact": False,
    }
    assert not Path(plan["records"][0]["output"]["path"]).exists()
    assert calls.read_text(encoding="utf-8") == ""


def test_committed_ffprobe_streams_match_the_typed_request(tmp_path: Path) -> None:
    models, request = tmp_path / "models.json", tmp_path / "request.json"
    _models(models)
    _request(request, "refine")
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "stream=index,codec_type,duration", "-of", "json", str(SOURCE)],
        text=True, capture_output=True, check=True,
    )
    streams = {int(item["index"]): item for item in json.loads(probe.stdout)["streams"]}
    payload = json.loads(request.read_text(encoding="utf-8"))
    for name in ("video", "audio"):
        declared = payload["source"][name]
        observed = streams[declared["index"]]
        assert observed["codec_type"] == declared["codec_type"]
        assert float(observed["duration"]) == declared["duration_s"]
    compiled = compile_audio_post_request(
        attach_manifest_model(payload, load_audio_post_model_manifest(models))
    ).mapping()
    assert compiled["records"][0]["source"]["sha256"] == _hash(SOURCE)


def test_plan_records_are_immutable_undrainable_reconstructable_and_real_job_admitted(
    tmp_path: Path,
) -> None:
    environment, calls = _environment(tmp_path)
    models, request, database = tmp_path / "models.json", tmp_path / "request.json", tmp_path / "plans.db"
    _models(models)
    _request(request, "revoice")
    result = _wgp(
        "sfx", "revoice", "--request", str(request), "--models", str(models),
        "--db", str(database), "--json", cwd=ROOT, env=environment,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    plan = json.loads(result.stdout)
    assert plan["queue"] == {"database": str(database), "record_ids": plan["queue"]["record_ids"], "executable_jobs": 0}
    connection = sqlite3.connect(database)
    with pytest.raises(sqlite3.IntegrityError, match="immutable"):
        connection.execute("UPDATE audio_post_plan_records SET record='changed'")
    with pytest.raises(sqlite3.IntegrityError, match="immutable"):
        connection.execute("DELETE FROM audio_post_plan_records")
    connection.close()
    queue = JobQueue(database)
    try:
        assert queue.list_state("pending") == []
        assert queue.next_admissible() is None
        genuine = queue.submit(plan_ref="genuine-render", clips=[{
            "clip_index": 1, "status": "pending", "log": None, "mp4": None,
            "qc_verdict": None, "kind": "ref2va_render", "prompt": "genuine",
            "seed": 1, "video_length": 56,
        }])
        assert queue.next_admissible() == genuine
    finally:
        queue.close()
    comparison = _wgp("sfx", "plan", "--db", str(database), "--reconstruct", "--json", cwd=ROOT, env=environment)
    assert comparison.returncode == 0, comparison.stdout + comparison.stderr
    evidence = json.loads(comparison.stdout)
    assert evidence["all_match"] is True and evidence["hidden_mutation"] is False
    assert evidence["records"][0]["recorded_settings_sha256"] == evidence["records"][0]["reconstructed_settings_sha256"]
    assert calls.read_text(encoding="utf-8") == ""


def test_repository_datasets_are_read_only_across_real_cli_run(tmp_path: Path) -> None:
    environment, calls = _environment(tmp_path)
    before = _tree_digest(ROOT / "datasets")
    models, request = tmp_path / "models.json", tmp_path / "request.json"
    _models(models)
    _request(request, "sfx")
    result = _wgp(
        "sfx", "effect", "--request", str(request), "--models", str(models), "--json",
        cwd=ROOT, env=environment,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert _tree_digest(ROOT / "datasets") == before
    assert calls.read_text(encoding="utf-8") == ""


@pytest.mark.parametrize(
    ("case", "code"),
    [
        ("manifest-missing", "MODEL_MANIFEST_MISSING"),
        ("manifest-invalid", "MODEL_MANIFEST_INVALID"),
        ("hash-missing", "MODEL_HASH_MISSING"),
        ("backend-incomplete", "AUDIO_POST_BACKEND_INCOMPLETE"),
        ("operation-unsupported", "AUDIO_POST_OPERATION_UNSUPPORTED"),
        ("layout-unsupported", "AUDIO_POST_TARGET_LAYOUT_UNSUPPORTED"),
        ("duration-mismatch", "AUDIO_POST_DURATION_MISMATCH"),
        ("voice-missing", "AUDIO_POST_VOICE_MISSING"),
        ("voice-hash", "AUDIO_POST_VOICE_UNUSABLE"),
        ("stream-invalid", "AUDIO_POST_SOURCE_STREAM_INVALID"),
        ("video-mutation", "AUDIO_POST_VIDEO_MUTATION_REFUSED"),
        ("source-missing", "AUDIO_POST_SOURCE_MISSING"),
        ("source-hash", "AUDIO_POST_SOURCE_HASH_MISMATCH"),
        ("mode-mismatch", "AUDIO_POST_MODE_MISMATCH"),
        ("output-exists", "AUDIO_POST_OUTPUT_EXISTS"),
        ("queue-exists", "AUDIO_POST_QUEUE_EXISTS"),
        ("request-missing", "AUDIO_POST_REQUEST_MISSING"),
        ("request-invalid", "AUDIO_POST_REQUEST_INVALID"),
        ("reconstruct-missing", "AUDIO_POST_RECONSTRUCTION_DATABASE_MISSING"),
        ("reconstruct-empty", "AUDIO_POST_RECONSTRUCTION_RECORDS_MISSING"),
        ("reconstruct-record", "AUDIO_POST_RECONSTRUCTION_RECORD_INVALID"),
        ("reconstruct-database", "AUDIO_POST_RECONSTRUCTION_INVALID"),
    ],
)
def test_every_typed_failure_class_is_machine_readable_and_next_command_resolves_live(
    tmp_path: Path, case: str, code: str
) -> None:
    environment, calls = _environment(tmp_path)
    models, request, database = tmp_path / "models.json", tmp_path / "request.json", tmp_path / "plans.db"
    operation = "revoice" if case in {
        "voice-missing", "voice-hash", "mode-mismatch",
    } else "sfx"
    _models(models)
    _request(request, operation)
    document = json.loads(request.read_text(encoding="utf-8"))
    verb = {"sfx": "effect", "revoice": "revoice", "refine": "refine"}[operation]
    command = ["sfx", verb, "--request", str(request), "--models", str(models), "--json"]
    if case == "manifest-missing":
        models.unlink()
    elif case == "manifest-invalid":
        models.write_text("{", encoding="utf-8")
    elif case == "hash-missing":
        manifest = json.loads(models.read_text())
        manifest["models"][0].pop("sha256")
        models.write_text(json.dumps(manifest), encoding="utf-8")
    elif case == "backend-incomplete":
        manifest = json.loads(models.read_text())
        manifest["models"][0].pop("license")
        models.write_text(json.dumps(manifest), encoding="utf-8")
    elif case == "operation-unsupported":
        document["operation"] = "refine"
        document.pop("prompt")
        document.pop("duration_s")
        document["refinement"] = {"mode": "denoise_and_loudness", "noise_reduction_db": 6.0, "target_lufs": -18.0}
        document["output"] = {"container": "mp4", "codec": "aac", "sample_rate_hz": 48000, "channels": 2}
        document["output_path_planned"] = str(tmp_path / "unsupported.mp4")
    elif case == "layout-unsupported":
        document["output"]["sample_rate_hz"] = 44100
    elif case == "duration-mismatch":
        document["duration_s"] = 2.31
    elif case == "voice-missing":
        document.pop("voice")
    elif case == "voice-hash":
        document["voice"]["sha256"] = "d" * 64
    elif case == "stream-invalid":
        document["source"]["video"]["index"] = document["source"]["audio"]["index"]
    elif case == "video-mutation":
        document["video"] = {
            "immutable": True,
            "transformations": [{"operation": "crop", "value": "1:1"}],
        }
    elif case == "source-missing":
        document["source"]["path"] = str(tmp_path / "absent.mp4")
    elif case == "source-hash":
        document["source"]["sha256"] = "e" * 64
    elif case == "mode-mismatch":
        verb = "effect"
        command[1] = verb
    elif case == "output-exists":
        Path(document["output_path_planned"]).write_bytes(b"prior")
    elif case == "queue-exists":
        database.write_bytes(b"exists")
        command += ["--db", str(database)]
    elif case == "request-missing":
        command[3] = str(tmp_path / "absent.json")
    elif case == "request-invalid":
        request.write_text("{", encoding="utf-8")
    elif case == "reconstruct-missing":
        command = ["sfx", "plan", "--db", str(tmp_path / "absent.db"), "--reconstruct", "--json"]
    elif case == "reconstruct-empty":
        connection = sqlite3.connect(database)
        connection.execute(
            "CREATE TABLE audio_post_plan_records(record_id TEXT PRIMARY KEY, plan_ref TEXT, "
            "record_index INTEGER, record TEXT, created_at REAL)"
        )
        connection.close()
        command = ["sfx", "plan", "--db", str(database), "--reconstruct", "--json"]
    elif case == "reconstruct-record":
        _request(tmp_path / "valid.json", "refine")
        valid = _wgp(
            "sfx", "refine", "--request", str(tmp_path / "valid.json"), "--models", str(models),
            "--db", str(database), "--json", cwd=ROOT, env=environment,
        )
        assert valid.returncode == 0, valid.stdout + valid.stderr
        connection = sqlite3.connect(database)
        connection.execute("DROP TRIGGER audio_post_plan_records_immutable_update")
        record_id, raw = connection.execute("SELECT record_id, record FROM audio_post_plan_records").fetchone()
        damaged = json.loads(raw)
        damaged.pop("recipe")
        connection.execute("UPDATE audio_post_plan_records SET record=? WHERE record_id=?", (json.dumps(damaged), record_id))
        connection.commit()
        connection.close()
        command = ["sfx", "plan", "--db", str(database), "--reconstruct", "--json"]
    elif case == "reconstruct-database":
        database.write_bytes(b"not sqlite")
        command = ["sfx", "plan", "--db", str(database), "--reconstruct", "--json"]
    if case not in {"request-missing", "request-invalid"} and not case.startswith("reconstruct"):
        request.write_text(json.dumps(document), encoding="utf-8")
    result = _wgp(*command, cwd=ROOT, env=environment)
    assert result.returncode == 2, f"{case}: {result.returncode} {result.stdout} {result.stderr}"
    diagnostic = json.loads(result.stdout)["diagnostics"][0]
    assert diagnostic["code"] == code, f"{case}: {diagnostic}"
    assert diagnostic["remediation"] and diagnostic["next_command"]
    _assert_next_command_resolves_against_live_cli(diagnostic["next_command"])
    assert "Traceback" not in result.stdout + result.stderr
    assert calls.read_text(encoding="utf-8") == ""


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_sound_effect_request_normalizes_typed_duration_and_format() -> None:
    root = Path(__file__).resolve().parents[1]
    source = root / "datasets/runs/provenance/lf002-vibevoice-film-20260917/cut1.mp4"
    models = Path(__file__).resolve().parent / "sfx-models.fixture.json"
    request = Path(__file__).resolve().parent / "sfx-request.fixture.json"
    models.write_text(json.dumps({"models": [{
        "family": "stable_audio", "preset": "sound_effect", "sha256": "a" * 64,
        "license": "operator-recorded license", "license_accepted": True,
        "source": "operator inventory", "usage_constraint": "recorded constraint",
        "vram_profile": "16gb",
    }]}), encoding="utf-8")
    request.write_text(json.dumps({
        "schema_version": "wangp-dspy.audio-post-request/v1",
        "model": {"family": "stable_audio", "preset": "sound_effect"},
        "operation": "sfx",
        "prompt": "distant metal gate latch with dry room tail",
        "duration_s": 2.3,
        "source": {
            "path": str(source), "sha256": _hash(source), "immutable": True,
            "video": {"index": 0, "codec_type": "video", "duration_s": 2.333333},
            "audio": {"index": 1, "codec_type": "audio", "duration_s": 2.304},
        },
        "output": {"container": "wav", "codec": "pcm_s16le", "sample_rate_hz": 48000, "channels": 2},
        "output_path_planned": str(Path(__file__).resolve().parent / "planned-effect.wav"),
        "recipe_seed": 907,
    }), encoding="utf-8")
    payload = json.loads(request.read_text(encoding="utf-8"))
    normalized = attach_manifest_model(payload, load_audio_post_model_manifest(models))
    assert isinstance(normalized, AudioPostRequest)
    assert normalized.operation is AudioPostOperation.sfx
    assert normalized.duration_s == 2.3
    assert normalized.source.immutable is True
    models.unlink()
    request.unlink()
