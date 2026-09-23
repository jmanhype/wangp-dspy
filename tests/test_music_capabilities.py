"""Real-process no-GPU coverage for governed music planning."""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import subprocess
from pathlib import Path

import pytest

from services.jobs.queue import JobQueue

ROOT = Path(__file__).resolve().parents[1]
HOST_KEYS = (
    "WANGP_SSH_TARGET", "WANGP_WGP_ROOT", "WANGP_PULL_ROOT",
    "WANGP_WGP_PYTHON",
)


def _models(path: Path) -> None:
    entries = []
    for family, preset, digest, vram in (
        ("ace_step", "song", "a" * 64, "24gb"),
        ("ace_step", "instrumental", "c" * 64, "24gb"),
        ("stable_audio", "instrumental", "b" * 64, "16gb"),
        ("stable_audio", "song", "d" * 64, "16gb"),
    ):
        entries.append({
            "family": family, "preset": preset, "sha256": digest,
            "license": "operator-recorded license", "license_accepted": True,
            "source": "operator inventory", "usage_constraint": "recorded constraint",
            "vram_profile": vram,
        })
    path.write_text(json.dumps({"models": entries}), encoding="utf-8")


def _request(
    path: Path,
    *,
    family: str = "ace_step",
    preset: str = "song",
    mode: str = "generate",
    sections: int = 2,
    style: bool = False,
) -> Path:
    section_list = [
        {
            "name": name, "duration_s": 4.0,
            "melody_abc": "| C4 E4 G4 C4 | D4 F4 A4 B4 |",
            "chords": ["C", "Dm"],
        }
        for name in ("intro", "chorus")[:sections]
    ]
    request = {
        "schema_version": "wangp-dspy.music-capability-request/v1",
        "model": {"family": family, "preset": preset}, "mode": mode,
        "title": "Deterministic Test Song", "style": "bright analog chamber pop",
        "lyrics": None if preset == "instrumental" else "one two three",
        "tempo_bpm": 120, "meter": "4/4", "key": "C",
        "sections": section_list, "duration_s": 4.0 * sections,
        "output_format": {"sample_rate_hz": 48000, "channels": 2},
        "recipe_seed": 904,
    }
    if style:
        reference = path.parent / "reference.wav"
        before = path.parent / "before.wav"
        reference.write_bytes(b"authorized-reference")
        before.write_bytes(b"authorized-before")
        request["style_adaptation"] = {
            "references": [{
                "path": str(reference),
                "sha256": hashlib.sha256(reference.read_bytes()).hexdigest(),
                "source": "operator-owned reference", "rights": "internal evaluation only",
            }],
            "comparison": {
                "mode": "audible_ab",
                "before": {
                    "path": str(before),
                    "sha256": hashlib.sha256(before.read_bytes()).hexdigest(),
                },
                "after_path_planned": str(path.parent / "after.wav"),
            },
            "command_planned": "authorized-host-only adapter command",
        }
    path.write_text(json.dumps(request), encoding="utf-8")
    return path


def _environment(tmp_path: Path) -> tuple[dict[str, str], Path]:
    forbidden = tmp_path / "forbidden-bin"
    forbidden.mkdir()
    calls = tmp_path / "host-calls"
    calls.write_text("", encoding="utf-8")
    for name in ("ssh", "nvidia-smi", "curl"):
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
    ("family", "preset", "model_type"),
    [("ace_step", "song", "planned/ace_step"), ("stable_audio", "instrumental", "planned/stable_audio")],
)
def test_generation_normalization_is_deterministic_and_makes_no_audio(
    tmp_path: Path, family: str, preset: str, model_type: str
) -> None:
    environment, calls = _environment(tmp_path)
    models, request, score = tmp_path / "models.json", tmp_path / "request.json", tmp_path / "song.abc"
    _models(models)
    _request(request, family=family, preset=preset)
    args = ("music", "plan", "--request", str(request), "--models", str(models))
    first = _wgp(*args, "--score-out", str(score), "--json", cwd=ROOT, env=environment)
    second = _wgp(*args, "--json", cwd=ROOT, env=environment)
    assert first.returncode == second.returncode == 0, first.stdout + first.stderr
    assert second.stdout == first.stdout
    payload = json.loads(first.stdout)
    assert payload["capability_status"] == "planned"
    assert payload["operation"] == "generate"
    assert payload["summary"] == {
        "gpu_work": False, "training_executed": False, "audio_created": False,
        "queue_submitted": False, "host_contact": False,
    }
    assert payload["model"]["family"] == family
    assert payload["tracks"][0]["backend_settings"]["model_type"] == model_type
    assert payload["tracks"][0]["format"] == {
        "sample_rate_hz": 48000, "channels": 2,
        "measurement_status": "not verified - requires authorized host run",
    }
    assert score.read_text(encoding="utf-8").startswith("X:1\nT:Deterministic Test Song")
    assert list(tmp_path.glob("*.wav")) == []
    assert calls.read_text(encoding="utf-8") == ""


def test_style_plan_declares_audible_ab_without_execution(tmp_path: Path) -> None:
    environment, calls = _environment(tmp_path)
    models, request = tmp_path / "models.json", tmp_path / "request.json"
    _models(models)
    _request(request, preset="instrumental", mode="style_adaptation", style=True)
    args = ("music", "style", "--request", str(request), "--models", str(models))
    human = _wgp(*args, cwd=ROOT, env=environment)
    payload = json.loads(_wgp(*args, "--json", cwd=ROOT, env=environment).stdout)
    assert human.returncode == 0, human.stdout + human.stderr
    assert "training_executed=false audio_created=false" in human.stdout
    assert "comparison=audible_ab" in human.stdout
    assert "after_status=planned aesthetic_verdict=none" in human.stdout
    record = payload["tracks"][0]
    comparison = record["style_adaptation"]["comparison"]
    assert record["backend_settings"]["style_adaptation"]["mode"] == "structural_plan_only"
    assert comparison["before"]["sha256"] == hashlib.sha256(b"authorized-before").hexdigest()
    assert comparison["after_planned"]["audio_claimed"] is False
    assert not Path(comparison["after_planned"]["path"]).exists()
    assert payload["summary"]["training_executed"] is False
    assert calls.read_text(encoding="utf-8") == ""


def test_durable_plan_is_immutable_undrainable_reconstructable_and_real_job_admitted(
    tmp_path: Path,
) -> None:
    environment, calls = _environment(tmp_path)
    models, request = tmp_path / "models.json", tmp_path / "request.json"
    database, score = tmp_path / "run" / "plans.db", tmp_path / "song.abc"
    _models(models)
    _request(request)
    result = _wgp(
        "music", "compile", "--request", str(request), "--models", str(models),
        "--db", str(database), "--score-out", str(score), "--json",
        cwd=ROOT, env=environment,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    plan = json.loads(result.stdout)
    assert plan["queue"]["executable_jobs"] == 0
    assert len(plan["queue"]["record_ids"]) == 2
    connection = sqlite3.connect(database)
    rows = connection.execute(
        "SELECT track_index, record FROM music_plan_records ORDER BY track_index"
    ).fetchall()
    for track_index, (expected_index, raw) in enumerate(rows, start=1):
        record = json.loads(raw)
        assert record["track_index"] == expected_index
        assert record["kind"] == "music_plan_record"
        assert record["plan_only"] is True and record["executable"] is False
        assert record["backend"]["sha256"] == "a" * 64
        assert record["score"]["sha256"] == plan["score_sha256"]
        assert record["section"]["name"] == ("intro" if track_index == 1 else "chorus")
        assert record["format"]["sample_rate_hz"] == 48000 and record["format"]["channels"] == 2
    with pytest.raises(sqlite3.IntegrityError, match="immutable"):
        connection.execute("UPDATE music_plan_records SET record='changed'")
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

    comparison = _wgp("music", "compare", "--db", str(database), "--json", cwd=ROOT, env=environment)
    assert comparison.returncode == 0, comparison.stdout + comparison.stderr
    evidence = json.loads(comparison.stdout)
    assert evidence["all_match"] is True and evidence["hidden_mutation"] is False
    assert len(evidence["records"]) == 2
    assert all(item["match"] for item in evidence["records"])
    assert list(tmp_path.rglob("*.wav")) == []
    assert calls.read_text(encoding="utf-8") == ""


def test_repository_datasets_are_read_only_across_real_cli_run(tmp_path: Path) -> None:
    environment, calls = _environment(tmp_path)
    before = _tree_digest(ROOT / "datasets")
    models, request = tmp_path / "models.json", tmp_path / "request.json"
    _models(models)
    _request(request)
    result = _wgp(
        "music", "plan", "--request", str(request), "--models", str(models), "--json",
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
        ("backend-incomplete", "MUSIC_BACKEND_INCOMPLETE"),
        ("operation-unsupported", "MUSIC_OPERATION_UNSUPPORTED"),
        ("format-unsupported", "MUSIC_FORMAT_UNSUPPORTED"),
        ("request-missing", "MUSIC_REQUEST_MISSING"),
        ("request-invalid", "MUSIC_REQUEST_INVALID"),
        ("score-invalid", "MUSIC_SCORE_INVALID"),
        ("section-invalid", "MUSIC_SECTION_INVALID"),
        ("style-input-invalid", "MUSIC_STYLE_INPUT_INVALID"),
        ("reference-missing", "MUSIC_STYLE_REFERENCE_MISSING"),
        ("reference-hash", "MUSIC_STYLE_REFERENCE_UNUSABLE"),
        ("baseline-missing", "MUSIC_STYLE_BASELINE_MISSING"),
        ("after-exists", "MUSIC_STYLE_OUTPUT_ALREADY_PRESENT"),
        ("mode-mismatch", "MUSIC_MODE_MISMATCH"),
        ("queue-path", "MUSIC_QUEUE_PATH_MISSING"),
        ("queue-exists", "MUSIC_QUEUE_EXISTS"),
        ("score-exists", "MUSIC_SCORE_OUTPUT_EXISTS"),
        ("reconstruct-missing", "MUSIC_RECONSTRUCTION_DATABASE_MISSING"),
        ("reconstruct-empty", "MUSIC_RECONSTRUCTION_RECORDS_MISSING"),
        ("reconstruct-record", "MUSIC_RECONSTRUCTION_RECORD_INVALID"),
        ("reconstruct-database", "MUSIC_RECONSTRUCTION_INVALID"),
    ],
)
def test_every_typed_failure_class_is_machine_readable(
    tmp_path: Path, case: str, code: str
) -> None:
    environment, calls = _environment(tmp_path)
    models, request = tmp_path / "models.json", tmp_path / "request.json"
    database, score = tmp_path / "plans.db", tmp_path / "song.abc"
    is_style = case in {
        "operation-unsupported", "style-input-invalid", "reference-missing", "mode-mismatch",
        "reference-hash", "baseline-missing", "after-exists",
    }
    _models(models)
    _request(
        request, family="stable_audio" if case == "operation-unsupported" else "ace_step",
        preset="instrumental" if is_style else "song",
        mode="style_adaptation" if is_style else "generate",
        style=is_style and case != "style-input-invalid",
    )
    document = json.loads(request.read_text())
    command = ["music", "plan", "--request", str(request), "--models", str(models), "--json"]
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
    elif case == "format-unsupported":
        document["output_format"] = {"sample_rate_hz": 44100, "channels": 2}
    elif case == "request-missing":
        command[3] = str(tmp_path / "absent.json")
    elif case == "request-invalid":
        request.write_text("{", encoding="utf-8")
    elif case == "score-invalid":
        document["sections"][0]["melody_abc"] = "this is not ABC"
    elif case == "section-invalid":
        document["sections"][0]["duration_s"] = 3.0
    elif case == "style-input-invalid":
        document["style_adaptation"] = None
    elif case == "reference-missing":
        Path(document["style_adaptation"]["references"][0]["path"]).unlink()
    elif case == "reference-hash":
        document["style_adaptation"]["references"][0]["sha256"] = "c" * 64
    elif case == "baseline-missing":
        Path(document["style_adaptation"]["comparison"]["before"]["path"]).unlink()
    elif case == "after-exists":
        Path(document["style_adaptation"]["comparison"]["after_path_planned"]).write_bytes(b"prior")
    elif case == "mode-mismatch":
        command = ["music", "plan", "--request", str(request), "--models", str(models), "--json"]
    elif case == "queue-path":
        command = ["music", "compile", "--request", str(request), "--models", str(models), "--json"]
    elif case == "queue-exists":
        database.write_bytes(b"exists")
        command += ["--db", str(database)]
    elif case == "score-exists":
        score.write_text("existing", encoding="utf-8")
        command += ["--score-out", str(score)]
    elif case == "reconstruct-missing":
        command = ["music", "compare", "--db", str(tmp_path / "absent.db"), "--json"]
    elif case == "reconstruct-empty":
        connection = sqlite3.connect(database)
        connection.execute(
            "CREATE TABLE music_plan_records("
            "record_id TEXT PRIMARY KEY, plan_ref TEXT, track_index INTEGER, "
            "record TEXT, created_at REAL)"
        )
        connection.close()
        command = ["music", "compare", "--db", str(database), "--json"]
    elif case == "reconstruct-record":
        _request(tmp_path / "valid.json")
        valid = _wgp("music", "compile", "--request", str(tmp_path / "valid.json"),
                     "--models", str(models), "--db", str(database), "--json",
                     cwd=ROOT, env=environment)
        assert valid.returncode == 0, valid.stdout + valid.stderr
        connection = sqlite3.connect(database)
        connection.execute("DROP TRIGGER music_plan_records_immutable_update")
        record_id, raw = connection.execute("SELECT record_id, record FROM music_plan_records").fetchone()
        damaged = json.loads(raw)
        damaged.pop("recipe")
        connection.execute("UPDATE music_plan_records SET record=? WHERE record_id=?",
                           (json.dumps(damaged), record_id))
        connection.commit()
        connection.close()
        command = ["music", "compare", "--db", str(database), "--json"]
    elif case == "reconstruct-database":
        database.write_bytes(b"not sqlite")
        command = ["music", "compare", "--db", str(database), "--json"]
    if case not in {"request-missing", "request-invalid"}:
        request.write_text(json.dumps(document), encoding="utf-8")
    if is_style and case != "mode-mismatch":
        command[1] = "style"
    result = _wgp(*command, cwd=ROOT, env=environment)
    assert result.returncode == 2, f"{case}: {result.returncode} {result.stdout} {result.stderr}"
    diagnostic = json.loads(result.stdout)["diagnostics"][0]
    assert diagnostic["code"] == code, f"{case}: {diagnostic}"
    assert diagnostic["remediation"] and diagnostic["next_command"]
    assert "Traceback" not in result.stdout + result.stderr
    assert calls.read_text(encoding="utf-8") == ""
