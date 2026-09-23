"""Real-process no-GPU coverage for governed speech planning."""
from __future__ import annotations

import hashlib
import json
import math
import os
import sqlite3
import struct
import subprocess
import wave
from pathlib import Path

import pytest

from services.jobs.queue import JobQueue

ROOT = Path(__file__).resolve().parents[1]
HOST_KEYS = (
    "WANGP_SSH_TARGET", "WANGP_WGP_ROOT", "WANGP_PULL_ROOT",
    "WANGP_WGP_PYTHON",
)


def _models(path: Path) -> None:
    entries = [
        {
            "family": "vibevoice", "preset": "vibe_7b", "sha256": "a" * 64,
            "license": "operator-recorded license", "license_accepted": True,
            "source": "operator inventory", "usage_constraint": "recorded constraint",
            "vram_profile": "24gb",
        },
        {
            "family": "chatterbox", "preset": "chatterbox_multilingual", "sha256": "b" * 64,
            "license": "operator-recorded fallback license", "license_accepted": True,
            "source": "separate operator inventory", "usage_constraint": "recorded constraint",
            "vram_profile": "16gb",
        },
    ]
    path.write_text(json.dumps({"models": entries}), encoding="utf-8")


def _wav(path: Path, seconds: float = 2.0) -> Path:
    rate = 24_000
    frames = int(rate * seconds)
    with wave.open(str(path), "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(rate)
        audio.writeframes(b"".join(
            struct.pack("<h", int(12000 * math.sin(2 * math.pi * 220 * frame / rate)))
            for frame in range(frames)
        ))
    return path


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _request(
    path: Path,
    *,
    family: str = "vibevoice",
    mode: str = "speech",
    refs: int = 0,
    character: bool = False,
    max_chars: int = 60,
    text: str | None = None,
) -> Path:
    request = {
        "schema_version": "wangp-dspy.speech-capability-request/v1",
        "model": {"family": family, "preset": "chatterbox_multilingual" if family == "chatterbox" else "vibe_7b"},
        "mode": mode,
        "text": text or "First sentence is short. Second sentence follows in order. Third completes the plan.",
        "language": "en-US", "style": "calm narrator",
        "references": [],
        "segment_policy": {
            "max_segment_chars": max_chars,
            "max_segment_duration_s": 20.0,
            "silence_s": 0.25,
            "split_on_sentence": True,
        },
        "output_path_planned": str(path.parent / "assembled.wav"),
        "recipe_seed": 906,
    }
    for index in range(refs):
        reference = _wav(path.parent / f"voice-{index + 1}.wav")
        request["references"].append({
            "path": str(reference), "sha256": _hash(reference),
            "role": "primary" if index == 0 else "secondary", "duration_s": 2.0,
            "source": "operator-authorized reference", "license": "internal evaluation only",
            "consent_ref": f"consent-record-{index + 1}",
        })
    if character:
        appearance = path.parent / "appearance.png"
        appearance.write_bytes(b"operator-appearance")
        request["character"] = {
            "character_id": "Nell", "speaker_label": "Nell",
            "appearance": {"path": str(appearance), "sha256": _hash(appearance)},
            "voice_binding_id": "nell-v1-primary",
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


def _tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        digest.update(str(path.relative_to(root)).encode() + b"\0")
        digest.update(path.read_bytes())
    return digest.hexdigest()


@pytest.mark.parametrize(
    ("family", "mode", "refs"),
    [
        ("vibevoice", "speech", 0),
        ("vibevoice", "voice_clone", 1),
        ("vibevoice", "voice_clone", 2),
        ("chatterbox", "speech", 0),
    ],
)
def test_every_mode_normalizes_segments_deterministically_without_audio(
    tmp_path: Path, family: str, mode: str, refs: int
) -> None:
    environment, calls = _environment(tmp_path)
    models, request = tmp_path / "models.json", tmp_path / "request.json"
    _models(models)
    _request(request, family=family, mode=mode, refs=refs)
    verb = "clone" if mode == "voice_clone" else "generate"
    args = ("voice", verb, "--request", str(request), "--models", str(models))
    human = _wgp(*args, cwd=ROOT, env=environment)
    first = _wgp(*args, "--json", cwd=ROOT, env=environment)
    second = _wgp(*args, "--json", cwd=ROOT, env=environment)
    assert human.returncode == first.returncode == second.returncode == 0, first.stdout + first.stderr
    assert "audio_created=false" in human.stdout
    assert second.stdout == first.stdout
    plan = json.loads(first.stdout)
    assert plan["capability_status"] == "planned"
    assert plan["engine"]["family"] == family
    assert plan["segment_count"] == 2
    assert plan["assembly"]["order"] == [1, 2]
    assert plan["summary"] == {
        "gpu_work": False, "audio_created": False,
        "queue_submitted": False, "host_contact": False,
    }
    assert len(plan["records"][0]["voice_package"]["references"]) == refs
    assert plan["records"][0]["format"] == {
        "sample_rate_hz": 24000, "channels": 1,
        "measurement_status": "not verified - requires authorized host run",
    }
    assert not Path(plan["assembly"]["assembled_target"]).exists()
    assert calls.read_text(encoding="utf-8") == ""


def test_durable_plan_is_immutable_undrainable_reconstructable_and_real_job_admitted(
    tmp_path: Path,
) -> None:
    environment, calls = _environment(tmp_path)
    models, request = tmp_path / "models.json", tmp_path / "request.json"
    database = tmp_path / "run" / "plans.db"
    _models(models)
    _request(request)
    result = _wgp(
        "voice", "generate", "--request", str(request), "--models", str(models),
        "--db", str(database), "--json", cwd=ROOT, env=environment,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    plan = json.loads(result.stdout)
    assert plan["queue"]["executable_jobs"] == 0
    assert len(plan["queue"]["record_ids"]) == 2
    connection = sqlite3.connect(database)
    rows = connection.execute(
        "SELECT segment_index, record FROM speech_plan_records ORDER BY segment_index"
    ).fetchall()
    for expected_index, raw in rows:
        record = json.loads(raw)
        assert record["segment_index"] == expected_index
        assert record["kind"] == "speech_plan_record"
        assert record["plan_only"] is True and record["executable"] is False
        assert record["backend"]["family"] == "vibevoice"
        assert record["backend_settings"]["mode"] == "speech"
        assert record["text"]["text_sha256"]
        assert record["assembly"]["order"] == [1, 2]
    with pytest.raises(sqlite3.IntegrityError, match="immutable"):
        connection.execute("UPDATE speech_plan_records SET record='changed'")
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
    comparison = _wgp("voice", "plan", "--db", str(database), "--reconstruct", "--json", cwd=ROOT, env=environment)
    assert comparison.returncode == 0, comparison.stdout + comparison.stderr
    evidence = json.loads(comparison.stdout)
    assert evidence["all_match"] is True and evidence["hidden_mutation"] is False
    assert len(evidence["records"]) == 2
    assert not Path(plan["assembly"]["assembled_target"]).exists()
    assert calls.read_text(encoding="utf-8") == ""


def test_portable_character_package_round_trip_is_hash_verified_and_namespace_safe(
    tmp_path: Path,
) -> None:
    environment, calls = _environment(tmp_path)
    models, request, package = tmp_path / "models.json", tmp_path / "request.json", tmp_path / "nell.wgpvoice"
    imported = tmp_path / "imported" / "nell"
    _models(models)
    _request(request, mode="voice_clone", refs=2, character=True)
    export = _wgp(
        "voice", "export", "--request", str(request), "--models", str(models),
        "--package", str(package), "--json", cwd=ROOT, env=environment,
    )
    assert export.returncode == 0, export.stdout + export.stderr
    exported = json.loads(export.stdout)
    assert exported["manifest"]["character"]["character_id"] == "Nell"
    assert exported["manifest"]["character"]["appearance"]["visual_binding"] == "character_appearance"
    assert exported["audio_claimed"] is False
    human = _wgp(
        "voice", "import", "--package", str(package), "--destination", str(imported),
        cwd=ROOT, env=environment,
    )
    imported_json = _wgp(
        "voice", "import", "--package", str(package), "--destination", str(tmp_path / "imported" / "second"),
        "--json", cwd=ROOT, env=environment,
    )
    assert human.returncode == imported_json.returncode == 0, human.stdout + human.stderr
    payload = json.loads(imported_json.stdout)
    assert payload["package_sha256"] == exported["package_sha256"]
    assert (imported / "voice-package.json").is_file()
    assert (imported / "appearance.png").is_file()
    assert (imported / "references" / "primary.wav").is_file()
    assert _hash(imported / "references" / "primary.wav") == _hash(tmp_path / "voice-1.wav")
    assert calls.read_text(encoding="utf-8") == ""


def test_repository_datasets_are_read_only_across_real_cli_run(tmp_path: Path) -> None:
    environment, calls = _environment(tmp_path)
    before = _tree_digest(ROOT / "datasets")
    models, request = tmp_path / "models.json", tmp_path / "request.json"
    _models(models)
    _request(request)
    result = _wgp(
        "voice", "plan", "--request", str(request), "--models", str(models), "--json",
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
        ("backend-incomplete", "SPEECH_BACKEND_INCOMPLETE"),
        ("engine-mode", "SPEECH_ENGINE_MODE_UNSUPPORTED"),
        ("format", "SPEECH_FORMAT_UNSUPPORTED"),
        ("request-missing", "SPEECH_REQUEST_MISSING"),
        ("request-invalid", "SPEECH_REQUEST_INVALID"),
        ("reference-count", "SPEECH_REFERENCE_COUNT_INVALID"),
        ("reference-missing", "SPEECH_REFERENCE_MISSING"),
        ("reference-hash", "SPEECH_REFERENCE_UNUSABLE"),
        ("reference-format", "SPEECH_REFERENCE_UNUSABLE"),
        ("segment-duration", "SPEECH_SEGMENT_INVALID"),
        ("segment-token", "SPEECH_SEGMENT_INVALID"),
        ("character", "SPEECH_CHARACTER_BINDING_INVALID"),
        ("mode-mismatch", "SPEECH_MODE_MISMATCH"),
        ("output-exists", "SPEECH_OUTPUT_EXISTS"),
        ("queue-exists", "SPEECH_QUEUE_EXISTS"),
        ("package-unsupported", "VOICE_PACKAGE_UNSUPPORTED"),
        ("package-output-exists", "VOICE_PACKAGE_OUTPUT_EXISTS"),
        ("package-invalid", "VOICE_PACKAGE_INVALID"),
        ("package-destination-exists", "VOICE_PACKAGE_DESTINATION_EXISTS"),
        ("appearance-missing", "VOICE_APPEARANCE_MISSING"),
        ("reconstruct-missing", "SPEECH_RECONSTRUCTION_DATABASE_MISSING"),
        ("reconstruct-empty", "SPEECH_RECONSTRUCTION_RECORDS_MISSING"),
        ("reconstruct-record", "SPEECH_RECONSTRUCTION_RECORD_INVALID"),
        ("reconstruct-database", "SPEECH_RECONSTRUCTION_INVALID"),
    ],
)
def test_every_typed_failure_class_is_machine_readable(
    tmp_path: Path, case: str, code: str
) -> None:
    environment, calls = _environment(tmp_path)
    models, request, database = tmp_path / "models.json", tmp_path / "request.json", tmp_path / "plans.db"
    package = tmp_path / "character.wgpvoice"
    _models(models)
    _request(
        request,
        family="chatterbox" if case == "engine-mode" else "vibevoice",
        mode="voice_clone" if case in {
            "engine-mode", "reference-missing", "reference-hash", "reference-format",
            "package-unsupported", "package-output-exists", "appearance-missing", "mode-mismatch",
        } else "speech",
        refs=2 if case in {
            "engine-mode", "reference-missing", "reference-hash", "reference-format",
            "package-unsupported", "package-output-exists", "appearance-missing", "mode-mismatch",
        } else 0,
        character=case in {
            "package-unsupported", "package-output-exists", "appearance-missing",
        },
    )
    document = json.loads(request.read_text())
    command = ["voice", "plan", "--request", str(request), "--models", str(models), "--json"]
    if case in {"reference-missing", "reference-hash", "reference-format", "appearance-missing"}:
        path = (
            Path(document["character"]["appearance"]["path"])
            if case == "appearance-missing"
            else Path(document["references"][0]["path"])
        )
        if case == "reference-missing":
            path.unlink()
        elif case == "reference-hash":
            document["references"][0]["sha256"] = "c" * 64
        elif case == "reference-format":
            path.write_bytes(b"not riff wav")
        else:
            path.unlink()
    if case in {"package-unsupported", "package-output-exists", "appearance-missing"}:
        if case == "package-unsupported":
            document["character"] = None
        elif case == "package-output-exists":
            package.write_bytes(b"existing")
        command = ["voice", "export", "--request", str(request), "--models", str(models), "--package", str(package), "--json"]
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
    elif case == "format":
        document["output_format"] = {"sample_rate_hz": 44100, "channels": 1}
    elif case == "request-missing":
        command[3] = str(tmp_path / "absent.json")
    elif case == "request-invalid":
        request.write_text("{", encoding="utf-8")
    elif case == "reference-count":
        document["references"] = document.get("references", [])
        document["mode"] = "voice_clone"
    elif case == "segment-duration":
        document["segment_policy"]["max_segment_duration_s"] = 31.0
    elif case == "segment-token":
        document["segment_policy"]["max_segment_chars"] = 20
        document["text"] = "supercalifragilisticexpialidocious"
    elif case == "character":
        document["character"] = {
            "character_id": "Orin", "speaker_label": "Orin",
            "voice_binding_id": "orin-v1",
        }
    elif case == "mode-mismatch":
        document["mode"] = "voice_clone"
        command[1] = "generate"
    elif case == "output-exists":
        Path(document["output_path_planned"]).write_bytes(b"prior")
    elif case == "queue-exists":
        database.write_bytes(b"exists")
        command += ["--db", str(database)]
    elif case == "package-invalid":
        package.write_bytes(b"not a zip")
        command = ["voice", "import", "--package", str(package), "--destination", str(tmp_path / "import"), "--json"]
    elif case == "package-destination-exists":
        destination = tmp_path / "existing-import"
        destination.mkdir()
        package.write_bytes(b"not a zip")
        command = ["voice", "import", "--package", str(package), "--destination", str(destination), "--json"]
    elif case == "reconstruct-missing":
        command = ["voice", "plan", "--db", str(tmp_path / "absent.db"), "--reconstruct", "--json"]
    elif case == "reconstruct-empty":
        connection = sqlite3.connect(database)
        connection.execute(
            "CREATE TABLE speech_plan_records(record_id TEXT PRIMARY KEY, plan_ref TEXT, "
            "segment_index INTEGER, record TEXT, created_at REAL)"
        )
        connection.close()
        command = ["voice", "plan", "--db", str(database), "--reconstruct", "--json"]
    elif case == "reconstruct-record":
        _request(tmp_path / "valid.json")
        valid = _wgp(
            "voice", "generate", "--request", str(tmp_path / "valid.json"), "--models", str(models),
            "--db", str(database), "--json", cwd=ROOT, env=environment,
        )
        assert valid.returncode == 0, valid.stdout + valid.stderr
        connection = sqlite3.connect(database)
        connection.execute("DROP TRIGGER speech_plan_records_immutable_update")
        record_id, raw = connection.execute("SELECT record_id, record FROM speech_plan_records").fetchone()
        damaged = json.loads(raw)
        damaged.pop("recipe")
        connection.execute("UPDATE speech_plan_records SET record=? WHERE record_id=?", (json.dumps(damaged), record_id))
        connection.commit()
        connection.close()
        command = ["voice", "plan", "--db", str(database), "--reconstruct", "--json"]
    elif case == "reconstruct-database":
        database.write_bytes(b"not sqlite")
        command = ["voice", "plan", "--db", str(database), "--reconstruct", "--json"]
    if case not in {"request-missing", "request-invalid"}:
        request.write_text(json.dumps(document), encoding="utf-8")
    result = _wgp(*command, cwd=ROOT, env=environment)
    assert result.returncode == 2, f"{case}: {result.returncode} {result.stdout} {result.stderr}"
    diagnostic = json.loads(result.stdout)["diagnostics"][0]
    assert diagnostic["code"] == code, f"{case}: {diagnostic}"
    assert diagnostic["remediation"] and diagnostic["next_command"]
    assert "Traceback" not in result.stdout + result.stderr
    assert calls.read_text(encoding="utf-8") == ""
