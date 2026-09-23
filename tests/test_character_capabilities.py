"""Real-process no-GPU coverage for portable character continuity."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import zipfile
from pathlib import Path

import pytest

from predict.character_packages import (
    PACKAGE_SCHEMA_VERSION,
    AppearanceInput,
    AppearanceRole,
    CharacterDefinition,
    ContinuityConstraint,
    ContinuityContract,
    ContinuityMode,
    IdentityMetric,
)
from services.jobs.executor import JobExecutor
from services.jobs.queue import JobQueue


ROOT = Path(__file__).resolve().parents[1]
HOST_KEYS = (
    "WANGP_SSH_TARGET",
    "WANGP_WGP_ROOT",
    "WANGP_PULL_ROOT",
    "WANGP_WGP_PYTHON",
)


def test_character_definition_format_is_typed() -> None:
    definition = CharacterDefinition.model_validate(
        {
            "schema_version": PACKAGE_SCHEMA_VERSION,
            "character_id": "Orin Vale",
            "speaker_label": "Orin",
            "version": 1,
            "description": "Operator-created fictional scientist",
            "appearance": [
                {
                    "path": "appearance/native.png",
                    "sha256": "a" * 64,
                    "role": "native",
                    "width": 2048,
                    "height": 2048,
                    "source_path": "/authorized/originals/orin-native.png",
                    "license": "operator-recorded licence",
                    "consent_ref": "orin-appearance-consent",
                }
            ],
            "continuity": {
                "modes": ["image", "video"],
                "constraints": [
                    {"metric": "face_embedding_cosine", "threshold": 0.75},
                    {"metric": "cross_mode_binding", "threshold": 1.0},
                ],
            },
            "recipe_seed": 907,
            "voice": {
                "path": "voice/orin.wgpvoice",
                "voice_binding_id": "orin-v1-primary",
            },
        }
    )
    assert definition.appearance[0].role is AppearanceRole.native
    assert definition.continuity.modes == (
        ContinuityMode.image,
        ContinuityMode.video,
    )
    assert IdentityMetric.cross_mode_binding in {
        constraint.metric for constraint in definition.continuity.constraints
    }


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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
        ["uv", "run", "--frozen", "--extra", "dev", "wgp", "character", *args],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )


def _voice_package(
    path: Path,
    *,
    character_id: str = "Orin Vale",
    speaker_label: str = "Orin",
    binding: str = "orin-v1-primary",
) -> Path:
    appearance = b"native-appearance-bytes"
    reference = b"authorized-voice-reference-bytes"
    manifest = {
        "schema_version": "wangp-dspy.character-voice-package/v1",
        "character": {
            "character_id": character_id,
            "speaker_label": speaker_label,
            "voice_binding_id": binding,
            "appearance": {
                "member": "appearance.png",
                "sha256": hashlib.sha256(appearance).hexdigest(),
                "role": "character_appearance",
                "visual_binding": "character_appearance",
            },
        },
        "voice": {
            "engine_compatibility": ["vibevoice", "vibe_7b"],
            "references": [
                {
                    "member": "references/primary.wav",
                    "sha256": hashlib.sha256(reference).hexdigest(),
                    "role": "primary",
                    "duration_s": 3.0,
                    "source": "operator recording",
                    "license": "operator-recorded license",
                    "consent_ref": "orin-voice-consent",
                }
            ],
            "language": "en-US",
            "style": "warm analytical",
        },
        "audio_claimed": False,
        "host_contact": False,
        "execution_status": "planned",
    }
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for member, data in (
            ("appearance.png", appearance),
            ("references/primary.wav", reference),
            ("voice-package.json", json.dumps(manifest, sort_keys=True, indent=2).encode() + b"\n"),
        ):
            info = zipfile.ZipInfo(member, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)
    return path


def _definition_payload(
    tmp_path: Path,
    *,
    character_id: str = "Orin Vale",
    speaker_label: str = "Orin",
    binding: str = "orin-v1-primary",
) -> tuple[dict[str, object], Path, Path]:
    native = tmp_path / "authorized-originals" / "orin-native.png"
    native.parent.mkdir(parents=True, exist_ok=True)
    native.write_bytes(b"native-appearance-bytes")
    voice = _voice_package(
        tmp_path / "orin.wgpvoice",
        character_id=character_id,
        speaker_label=speaker_label,
        binding=binding,
    )
    payload = {
        "schema_version": PACKAGE_SCHEMA_VERSION,
        "character_id": character_id,
        "speaker_label": speaker_label,
        "version": 1,
        "description": "Operator-created fictional scientist",
        "appearance": [
            {
                "path": str(native),
                "sha256": _digest(native),
                "role": "native",
                "width": 2,
                "height": 1,
                "source_path": str(native),
                "license": "operator-recorded licence",
                "consent_ref": "orin-appearance-consent",
            }
        ],
        "voice": {"path": str(voice), "voice_binding_id": binding},
        "continuity": {
            "modes": ["image", "video"],
            "constraints": [
                {"metric": "face_embedding_cosine", "threshold": 0.75},
                {"metric": "cross_mode_binding", "threshold": 1.0},
            ],
        },
        "recipe_seed": 907,
    }
    return payload, native, voice


def _write_json(path: Path, payload: dict[str, object]) -> Path:
    path.write_text(json.dumps(payload, sort_keys=True, indent=2), encoding="utf-8")
    return path


def _export_package(
    tmp_path: Path,
    env: dict[str, str],
    *,
    character_id: str = "Orin Vale",
    speaker_label: str = "Orin",
    binding: str = "orin-v1-primary",
) -> tuple[Path, dict[str, object], Path, Path]:
    payload, native, voice = _definition_payload(
        tmp_path,
        character_id=character_id,
        speaker_label=speaker_label,
        binding=binding,
    )
    definition = _write_json(tmp_path / "definition.json", payload)
    package = tmp_path / f"{character_id.lower().replace(' ', '-')}.wgpcharacter"
    result = _wgp(
        "export", "--definition", str(definition), "--package", str(package), "--json", env=env
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return package, json.loads(result.stdout), native, voice


def _request_payload(package: Path, *, mode: str = "image") -> dict[str, object]:
    result = _wgp("show", "--package", str(package), "--json", env=os.environ.copy())
    assert result.returncode == 0, result.stdout + result.stderr
    manifest = json.loads(result.stdout)["manifest"]
    appearance = manifest["appearance"][0]
    return {
        "schema_version": "wangp-dspy.character-continuity-request/v1",
        "mode": mode,
        "operation": "identity_edit" if mode == "image" else "create",
        "prompt": "preserve the bound character identity",
        "character": {
            "package_path": str(package),
            "package_sha256": json.loads(result.stdout)["package_sha256"],
            "character_id": manifest["character_id"],
            "speaker_label": manifest["speaker_label"],
            "appearance_member": appearance["member"],
            "appearance_sha256": appearance["sha256"],
            "voice_member": manifest["voice"]["member"],
            "voice_binding_id": manifest["voice"]["voice_binding_id"],
            "voice_sha256": manifest["voice"]["sha256"],
            "modes": manifest["continuity"]["modes"],
        },
        "recipe_seed": 907,
    }


def _tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        digest.update(str(path.relative_to(root)).encode() + b"\0")
        digest.update(path.read_bytes())
    return digest.hexdigest()


def test_real_character_round_trip_registry_and_native_recovery_are_hash_stable(
    tmp_path: Path,
) -> None:
    environment, calls = _environment(tmp_path)
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    source.mkdir()
    destination.mkdir()
    package, exported, native, _voice = _export_package(source, environment)
    second = source / "orin-second.wgpcharacter"
    definition = _write_json(source / "repeat.json", _definition_payload(source)[0])
    repeat = _wgp(
        "export", "--definition", str(definition), "--package", str(second), "--json", env=environment
    )
    assert repeat.returncode == 0, repeat.stdout + repeat.stderr
    assert _digest(second) == _digest(package)
    assert exported["package_sha256"] == _digest(package)
    assert exported["manifest"]["voice"]["voice_binding_id"] == "orin-v1-primary"
    assert exported["generation_claimed"] is False and exported["host_contact"] is False

    imported = destination / "orin"
    human = _wgp("import", "--package", str(package), "--destination", str(imported), env=environment)
    machine = _wgp(
        "import", "--package", str(package), "--destination", str(destination / "second"), "--json", env=environment
    )
    assert human.returncode == machine.returncode == 0, human.stdout + human.stderr
    assert "generation_claimed=false host_contact=false" in human.stdout
    imported_manifest = json.loads(machine.stdout)
    assert imported_manifest["package_sha256"] == _digest(package)
    assert imported_manifest["member_sha256"] == exported["member_sha256"]
    assert all(_digest(item) for item in imported.rglob("*") if item.is_file())
    registry = destination / "registry"
    registry.mkdir()
    shutil.copy2(package, registry / package.name)
    resolved = _wgp(
        "resolve", "--registry", str(registry), "--identity", "Orin Vale", "--json", env=environment
    )
    assert resolved.returncode == 0, resolved.stdout + resolved.stderr
    assert json.loads(resolved.stdout)["speaker_label"] == "Orin"
    alias = _wgp(
        "resolve", "--registry", str(registry), "--identity", "orin", env=environment
    )
    assert alias.returncode == 0, alias.stdout + alias.stderr

    recovered = destination / "recovered-native.png"
    recovery = _wgp(
        "recover", "--package", str(package), "--destination", str(recovered), "--json", env=environment
    )
    assert recovery.returncode == 0, recovery.stdout + recovery.stderr
    recovery_payload = json.loads(recovery.stdout)
    assert recovery_payload["sha256"] == _digest(native) == _digest(recovered)
    assert recovery_payload["transcoded"] == "false"
    assert calls.read_text(encoding="utf-8") == ""


def test_image_and_video_plans_bind_identity_hashes_and_are_deterministic(
    tmp_path: Path,
) -> None:
    environment, calls = _environment(tmp_path)
    package, inspected, _native, _voice = _export_package(tmp_path, environment)
    outputs: list[str] = []
    for mode in ("image", "video"):
        request = _write_json(tmp_path / f"{mode}.json", _request_payload(package, mode=mode))
        args = ("plan", "--request", str(request), "--dry-run")
        human = _wgp(*args, env=environment)
        first = _wgp(*args, "--json", env=environment)
        second = _wgp(*args, "--json", env=environment)
        assert human.returncode == first.returncode == second.returncode == 0
        assert first.stdout == second.stdout
        assert f"mode={mode}" in human.stdout
        assert "gpu_work=false media_generated=false" in human.stdout
        payload = json.loads(first.stdout)
        record = payload["records"][0]
        assert payload["capability_status"] == "planned"
        assert record["package_sha256"] == inspected["package_sha256"]
        assert record["identity_sha256"] == inspected["identity_sha256"]
        assert record["appearance_sha256"] == inspected["manifest"]["appearance"][0]["sha256"]
        assert record["voice_sha256"] == inspected["manifest"]["voice"]["sha256"]
        assert record["voice_binding_id"] == "orin-v1-primary"
        assert record["executable"] is False and record["plan_only"] is True
        outputs.append(first.stdout)
    assert json.loads(outputs[0])["request_sha256"] != json.loads(outputs[1])["request_sha256"]
    assert calls.read_text(encoding="utf-8") == ""


def test_plan_store_is_immutable_undrainable_reconstructable_and_read_only(
    tmp_path: Path,
) -> None:
    environment, calls = _environment(tmp_path)
    before = _tree_digest(ROOT / "datasets")
    package, _inspected, _native, _voice = _export_package(tmp_path, environment)
    request = _write_json(tmp_path / "request.json", _request_payload(package))
    database = tmp_path / "run" / "character-plan.db"
    result = _wgp(
        "plan", "--request", str(request), "--db", str(database), "--json", env=environment
    )
    assert result.returncode == 0, result.stdout + result.stderr
    plan = json.loads(result.stdout)
    assert plan["queue"]["executable_jobs"] == 0
    database_before = database.read_bytes()
    package_before = package.read_bytes()
    connection = sqlite3.connect(database)
    record_id, raw = connection.execute(
        "SELECT record_id, record FROM character_plan_records"
    ).fetchone()
    record = json.loads(raw)
    assert record["kind"] == "character_plan_record"
    assert record["plan_only"] is True and record["executable"] is False
    with pytest.raises(sqlite3.IntegrityError, match="immutable"):
        connection.execute("UPDATE character_plan_records SET record='changed'")
    with pytest.raises(sqlite3.IntegrityError, match="immutable"):
        connection.execute("DELETE FROM character_plan_records")
    connection.close()

    admission_copy = tmp_path / "admission-copy.db"
    shutil.copy2(database, admission_copy)
    admission = JobQueue(admission_copy)
    try:
        assert admission.list_state("pending") == []
        assert admission.next_admissible() is None
        executor = JobExecutor(
            queue=admission,
            preflight=lambda _job: pytest.fail("character plan admitted"),
            render=lambda _clip: pytest.fail("character plan rendered"),
            qc=lambda _clip: pytest.fail("character plan reached QC"),
        )
        assert executor.run_once() is None
    finally:
        admission.close()
    genuine = JobQueue(tmp_path / "genuine.db")
    try:
        job_id = genuine.submit(
            plan_ref="genuine-render",
            clips=[{"clip_index": 1, "status": "pending", "kind": "ref2va_render"}],
        )
        assert genuine.next_admissible() == job_id
    finally:
        genuine.close()

    reconstructed = _wgp(
        "plan", "--reconstruct", "--db", str(database), "--json", env=environment
    )
    assert reconstructed.returncode == 0, reconstructed.stdout + reconstructed.stderr
    evidence = json.loads(reconstructed.stdout)
    assert evidence["all_match"] is True and evidence["hidden_mutation"] is False
    item = evidence["records"][0]
    assert item["recorded_binding_sha256"] == item["reconstructed_binding_sha256"]
    assert item["recorded_seed_sha256"] == item["reconstructed_seed_sha256"]
    assert database.read_bytes() == database_before
    assert package.read_bytes() == package_before
    assert _tree_digest(ROOT / "datasets") == before
    assert calls.read_text(encoding="utf-8") == ""


@pytest.mark.parametrize(
    ("case", "code"),
    (
        ("definition-missing", "CHARACTER_DEFINITION_MISSING"),
        ("definition-invalid", "CHARACTER_DEFINITION_INVALID"),
        ("output-exists", "CHARACTER_OUTPUT_EXISTS"),
        ("voice-invalid", "CHARACTER_VOICE_PACKAGE_INVALID"),
        ("voice-mismatch", "CHARACTER_VOICE_BINDING_MISMATCH"),
        ("appearance-missing", "CHARACTER_APPEARANCE_UNUSABLE"),
        ("appearance-hash", "CHARACTER_APPEARANCE_UNUSABLE"),
        ("export-output", "CHARACTER_PACKAGE_OUTPUT_INVALID"),
        ("package-invalid", "CHARACTER_PACKAGE_INVALID"),
        ("import-destination", "CHARACTER_IMPORT_DESTINATION_EXISTS"),
        ("native-missing", "CHARACTER_NATIVE_SOURCE_MISSING"),
        ("native-hash", "CHARACTER_APPEARANCE_MISMATCH"),
        ("registry-missing", "CHARACTER_REGISTRY_MISSING"),
        ("registry-duplicate", "CHARACTER_IDENTITY_DUPLICATE"),
        ("registry-ambiguous", "CHARACTER_IDENTITY_AMBIGUOUS"),
        ("identity-unresolved", "CHARACTER_IDENTITY_UNRESOLVED"),
        ("request-missing", "CHARACTER_REQUEST_MISSING"),
        ("request-invalid", "CHARACTER_REQUEST_INVALID"),
        ("package-hash", "CHARACTER_PACKAGE_MISMATCH"),
        ("identity-mismatch", "CHARACTER_IDENTITY_MISMATCH"),
        ("appearance-binding", "CHARACTER_APPEARANCE_MISMATCH"),
        ("voice-binding", "CHARACTER_VOICE_BINDING_MISMATCH"),
        ("mode-unsupported", "CHARACTER_MODE_UNSUPPORTED"),
        ("queue-path", "CHARACTER_QUEUE_PATH_MISSING"),
        ("queue-exists", "CHARACTER_QUEUE_EXISTS"),
        ("reconstruct-missing", "CHARACTER_RECONSTRUCTION_DATABASE_MISSING"),
        ("reconstruct-empty", "CHARACTER_RECONSTRUCTION_RECORDS_MISSING"),
        ("reconstruct-invalid", "CHARACTER_RECONSTRUCTION_RECORD_INVALID"),
    ),
)
def test_every_typed_failure_class_is_exit_2_without_partial_state(
    tmp_path: Path, case: str, code: str
) -> None:
    environment, calls = _environment(tmp_path)
    package, _inspected, native, voice = _export_package(tmp_path, environment)
    request_payload = _request_payload(package, mode="video")
    request = _write_json(tmp_path / "request.json", request_payload)
    database = tmp_path / "partial.db"
    definition = tmp_path / "definition.json"
    command = ["plan", "--request", str(request), "--db", str(database), "--json"]

    if case == "definition-missing":
        command = ["create", "--definition", str(tmp_path / "absent.json"), "--out", str(tmp_path / "out.json"), "--json"]
    elif case == "definition-invalid":
        definition.write_text("{", encoding="utf-8")
        command = ["create", "--definition", str(definition), "--out", str(tmp_path / "out.json"), "--json"]
    elif case == "output-exists":
        output = tmp_path / "out.json"
        output.write_text("exists", encoding="utf-8")
        command = ["create", "--definition", str(definition), "--out", str(output), "--json"]
    elif case == "voice-invalid":
        invalid_voice = tmp_path / "invalid.wgpvoice"
        invalid_voice.write_bytes(b"not a zip")
        command = ["bind-voice", "--definition", str(definition), "--voice", str(invalid_voice), "--out", str(tmp_path / "bound.json"), "--json"]
    elif case == "voice-mismatch":
        other_voice = _voice_package(tmp_path / "other.wgpvoice", character_id="Other Character")
        command = ["bind-voice", "--definition", str(definition), "--voice", str(other_voice), "--out", str(tmp_path / "bound.json"), "--json"]
    elif case == "appearance-missing":
        native.unlink()
        command = ["export", "--definition", str(definition), "--package", str(tmp_path / "new.wgpcharacter"), "--json"]
    elif case == "appearance-hash":
        native.write_bytes(b"changed-native")
        command = ["export", "--definition", str(definition), "--package", str(tmp_path / "new.wgpcharacter"), "--json"]
    elif case == "export-output":
        command = ["export", "--definition", str(definition), "--package", str(package), "--json"]
    elif case == "package-invalid":
        package.write_bytes(b"not a zip")
        command = ["show", "--package", str(package), "--json"]
    elif case == "import-destination":
        destination = tmp_path / "existing"
        destination.mkdir()
        command = ["import", "--package", str(package), "--destination", str(destination), "--json"]
    elif case == "native-missing":
        native.unlink()
        command = ["recover", "--package", str(package), "--destination", str(tmp_path / "native.png"), "--json"]
    elif case == "native-hash":
        native.write_bytes(b"changed-native")
        command = ["recover", "--package", str(package), "--destination", str(tmp_path / "native.png"), "--json"]
    elif case == "registry-missing":
        command = ["resolve", "--registry", str(tmp_path / "absent-registry"), "--identity", "Orin Vale", "--json"]
    elif case in {"registry-duplicate", "registry-ambiguous"}:
        registry = tmp_path / "registry"
        registry.mkdir()
        shutil.copy2(package, registry / "one.wgpcharacter")
        other_dir = tmp_path / "other"
        other_dir.mkdir()
        if case == "registry-duplicate":
            other, _payload, _native, _voice = _export_package(other_dir, environment)
        else:
            other, _payload, _native, _voice = _export_package(
                other_dir, environment, character_id="Other Character", speaker_label="Orin"
            )
        shutil.copy2(other, registry / "two.wgpcharacter")
        command = ["resolve", "--registry", str(registry), "--identity", "Orin Vale", "--json"]
    elif case == "identity-unresolved":
        registry = tmp_path / "registry"
        registry.mkdir()
        shutil.copy2(package, registry / "orin.wgpcharacter")
        command = ["resolve", "--registry", str(registry), "--identity", "Unknown", "--json"]
    elif case == "request-missing":
        command[2] = str(tmp_path / "absent-request.json")
    elif case == "request-invalid":
        request.write_text("{", encoding="utf-8")
    elif case == "package-hash":
        payload = json.loads(request.read_text())
        payload["character"]["package_sha256"] = "b" * 64
        _write_json(request, payload)
    elif case == "identity-mismatch":
        payload = json.loads(request.read_text())
        payload["character"]["character_id"] = "Other Character"
        _write_json(request, payload)
    elif case == "appearance-binding":
        payload = json.loads(request.read_text())
        payload["character"]["appearance_sha256"] = "b" * 64
        _write_json(request, payload)
    elif case == "voice-binding":
        payload = json.loads(request.read_text())
        payload["character"]["voice_binding_id"] = "other-binding-v1"
        _write_json(request, payload)
    elif case == "mode-unsupported":
        image_only = dict(_definition_payload(tmp_path / "image-only")[0])
        image_only["continuity"]["modes"] = ["image"]
        image_definition = _write_json(tmp_path / "image-only.json", image_only)
        image_package = tmp_path / "image-only.wgpcharacter"
        export = _wgp(
            "export", "--definition", str(image_definition), "--package", str(image_package), "--json", env=environment
        )
        assert export.returncode == 0, export.stdout + export.stderr
        payload = _request_payload(image_package, mode="video")
        payload["character"]["modes"] = ["image", "video"]
        _write_json(request, payload)
    elif case == "queue-path":
        command = ["plan", "--request", str(request), "--json"]
    elif case == "queue-exists":
        database.write_bytes(b"exists")
    elif case == "reconstruct-missing":
        command = ["plan", "--reconstruct", "--db", str(tmp_path / "absent.db"), "--json"]
    elif case == "reconstruct-empty":
        connection = sqlite3.connect(database)
        connection.execute(
            "CREATE TABLE character_plan_records(record_id TEXT PRIMARY KEY, plan_ref TEXT, "
            "record_index INTEGER, record TEXT, created_at REAL)"
        )
        connection.close()
        command = ["plan", "--reconstruct", "--db", str(database), "--json"]
    elif case == "reconstruct-invalid":
        valid = _wgp(
            "plan", "--request", str(request), "--db", str(tmp_path / "valid.db"), "--json", env=environment
        )
        assert valid.returncode == 0, valid.stdout + valid.stderr
        connection = sqlite3.connect(tmp_path / "valid.db")
        connection.execute("DROP TRIGGER character_plan_records_immutable_update")
        record_id, raw = connection.execute(
            "SELECT record_id, record FROM character_plan_records"
        ).fetchone()
        damaged = json.loads(raw)
        damaged.pop("recipe")
        connection.execute(
            "UPDATE character_plan_records SET record=? WHERE record_id=?",
            (json.dumps(damaged), record_id),
        )
        connection.commit()
        connection.close()
        command = ["plan", "--reconstruct", "--db", str(tmp_path / "valid.db"), "--json"]

    result = _wgp(*command, env=environment)
    assert result.returncode == 2, f"{case}: {result.returncode} {result.stdout} {result.stderr}"
    assert "Traceback" not in result.stdout + result.stderr
    if command[0] == "plan" and case not in {"queue-exists", "reconstruct-missing", "reconstruct-empty", "reconstruct-invalid"}:
        assert not database.exists()
    if case not in {"reconstruct-missing", "reconstruct-empty", "reconstruct-invalid"}:
        diagnostic = json.loads(result.stdout)["diagnostics"][0]
        assert diagnostic["code"] == code, f"{case}: {diagnostic}"
        assert diagnostic["remediation"] and diagnostic["next_command"]
    assert calls.read_text(encoding="utf-8") == ""
