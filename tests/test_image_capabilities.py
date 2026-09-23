"""Real-process no-GPU coverage for Maestro image planning."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
from pathlib import Path

import pytest

from services.jobs.executor import JobExecutor
from services.jobs.queue import JobQueue


ROOT = Path(__file__).resolve().parents[1]
HOST_KEYS = ("WANGP_SSH_TARGET", "WANGP_WGP_ROOT", "WANGP_PULL_ROOT", "WANGP_WGP_PYTHON")


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_models(path: Path) -> None:
    entries = []
    for family, preset, vram in (
        ("qwen_image", "qwen-professional", "24gb"),
        ("qwen_image", "qwen-standard", "16gb"),
        ("flux_kontext", "flux-kontext", "24gb"),
    ):
        entries.append({
            "family": family,
            "preset": preset,
            "sha256": hashlib.sha256(f"{family}/{preset}".encode()).hexdigest(),
            "license": "operator-recorded upstream license",
            "license_accepted": True,
            "vram_profile": vram,
        })
    path.write_text(json.dumps({"models": entries}), encoding="utf-8")


def _write_request(
    path: Path,
    *,
    operation: str = "generate",
    references: int = 0,
    transparent: bool = False,
    enhancement: bool = False,
    **overrides: object,
) -> list[Path]:
    files: list[Path] = []
    refs = []
    for index in range(references):
        reference = path.parent / f"reference-{index + 1}.png"
        reference.write_bytes(f"reference-{index + 1}".encode())
        files.append(reference)
        refs.append({
            "path": str(reference),
            "sha256": _digest(reference),
            "role": "identity" if operation == "identity_edit" and index == 0 else "subject",
            "license": "operator-recorded input license",
        })
    request: dict[str, object] = {
        "schema_version": "wangp-dspy.image-capability-request/v1",
        "model": {"family": "qwen_image", "preset": "qwen-professional"},
        "operation": operation,
        "prompt": f"deterministic image {operation}",
        "license": "operator-recorded output license",
        "references": refs,
        "prompt_enhancement": (
            {"mode": "operator_authorized", "provider": "declared-provider", "authorization_ref": "run-record"}
            if enhancement else {"mode": "off"}
        ),
        "output": {"format": "png", "transparency": transparent, "width": 1024, "height": 1024},
        "recipe_seed": 904,
    }
    if operation in {"edit", "identity_edit", "outpaint"}:
        mask = path.parent / "edit-mask.png"
        mask.write_bytes(b"grayscale-mask")
        files.append(mask)
        request["mask"] = {"path": str(mask), "sha256": _digest(mask)}
    if operation == "upscale":
        request["upscale"] = {"source_width": 512, "source_height": 512, "factor": 2}
    if operation == "outpaint":
        request["outpaint"] = {"source_width": 512, "source_height": 512}
    if operation == "identity_edit":
        request["identity_gate"] = {"metric": "face_embedding_cosine", "threshold": 0.75}
    request.update(overrides)
    path.write_text(json.dumps(request), encoding="utf-8")
    return files


def _environment(tmp_path: Path) -> tuple[dict[str, str], Path]:
    forbidden = tmp_path / "forbidden-bin"
    forbidden.mkdir(exist_ok=True)
    calls = tmp_path / "host-calls"
    calls.write_text("", encoding="utf-8")
    for name in ("ssh", "nvidia-smi", "curl"):
        command = forbidden / name
        command.write_text(f'#!/bin/sh\nprintf "%s\\n" "{name} $*" >> {calls}\nexit 99\n', encoding="utf-8")
        command.chmod(0o755)
    environment = os.environ.copy()
    environment["PATH"] = f"{forbidden}:{environment['PATH']}"
    environment["WANGP_CONFIG"] = str(tmp_path / "absent-wangp.toml")
    for key in HOST_KEYS:
        environment.pop(key, None)
    return environment, calls


def _wgp(*args: str, cwd: Path = ROOT, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["uv", "run", "--frozen", "--extra", "dev", "wgp", *args],
        cwd=cwd, env=env, text=True, capture_output=True, timeout=120, check=False,
    )


@pytest.mark.parametrize(
    ("operation", "verb", "references"),
    (
        ("generate", "plan", 2),
        ("edit", "edit", 1),
        ("upscale", "upscale", 1),
        ("outpaint", "outpaint", 1),
        ("identity_edit", "edit", 2),
    ),
)
def test_real_cli_normalizes_every_operation(
    tmp_path: Path, operation: str, verb: str, references: int
) -> None:
    environment, calls = _environment(tmp_path)
    models = tmp_path / "models.json"
    request = tmp_path / "request.json"
    _write_models(models)
    _write_request(request, operation=operation, references=references, transparent=True, enhancement=True)
    result = _wgp(
        "image", verb, "--request", str(request), "--models", str(models),
        "--dry-run", "--json", env=environment,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    record = payload["records"][0]
    assert payload["capability_status"] == "planned"
    assert payload["operation"] == operation
    assert record["reference_count"] == references
    assert record["reference_limit"] == 10
    assert record["alpha_mode"] == "8_bit_alpha"
    assert record["output"]["format"] == "png"
    assert record["prompt_enhancement"]["mode"] == "operator_authorized"
    assert record["identity_gate"] is not None if operation == "identity_edit" else True
    assert record["identity_gate"] is None if operation != "identity_edit" else True
    assert record["output_image"] is None
    assert payload["summary"] == {"gpu_work": False, "queue_submitted": False, "host_contact": False}
    assert calls.read_text(encoding="utf-8") == ""


def test_ten_references_are_accepted_and_eleventh_fails_typed(tmp_path: Path) -> None:
    environment, calls = _environment(tmp_path)
    models = tmp_path / "models.json"
    request = tmp_path / "request.json"
    _write_models(models)
    _write_request(request, operation="generate", references=10)
    accepted = _wgp("image", "plan", "--request", str(request), "--models", str(models), "--dry-run", "--json", env=environment)
    assert accepted.returncode == 0, accepted.stdout + accepted.stderr
    assert json.loads(accepted.stdout)["records"][0]["reference_count"] == 10
    _write_request(request, operation="generate", references=11)
    rejected = _wgp("image", "plan", "--request", str(request), "--models", str(models), "--dry-run", "--json", env=environment)
    assert rejected.returncode == 2, rejected.stdout + rejected.stderr
    diagnostic = json.loads(rejected.stdout)["diagnostics"][0]
    assert diagnostic["code"] == "IMAGE_REFERENCE_LIMIT_EXCEEDED"
    assert "at most 10" in diagnostic["observed"]
    assert calls.read_text(encoding="utf-8") == ""


def test_human_and_json_surfaces_declare_planning_only(tmp_path: Path) -> None:
    environment, _calls = _environment(tmp_path)
    models = tmp_path / "models.json"
    request = tmp_path / "request.json"
    _write_models(models)
    _write_request(request, operation="generate", references=1, transparent=True)
    human = _wgp("image", "plan", "--request", str(request), "--models", str(models), "--dry-run", env=environment)
    machine = _wgp("image", "plan", "--request", str(request), "--models", str(models), "--dry-run", "--json", env=environment)
    assert human.returncode == machine.returncode == 0
    assert "capability_status=planned" in human.stdout
    assert "alpha_mode=8_bit_alpha" in human.stdout
    assert "gpu_work=false queue_submitted=false host_contact=false" in human.stdout
    assert json.loads(machine.stdout)["records"][0]["plan_only"] is True


def test_plan_store_is_immutable_undrainable_reconstructable_and_genuine_jobs_remain_admissible(
    tmp_path: Path,
) -> None:
    environment, calls = _environment(tmp_path)
    models = tmp_path / "models.json"
    request = tmp_path / "request.json"
    database = tmp_path / "run" / "image-plan.db"
    _write_models(models)
    _write_request(request, operation="identity_edit", references=2)
    result = _wgp("image", "edit", "--request", str(request), "--models", str(models), "--db", str(database), "--json", env=environment)
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout)["queue"]["executable_jobs"] == 0

    before = database.read_bytes()
    connection = sqlite3.connect(database)
    record_id, raw = connection.execute("SELECT record_id, record FROM image_plan_records").fetchone()
    record = json.loads(raw)
    connection.close()
    assert record["kind"] == "image_plan_record"
    assert record["plan_only"] is True and record["executable"] is False
    assert record["queue_submitted"] is False and record["host_contact"] is False
    assert record["reference_limit"] == 10 and record["reference_count"] == 2
    assert [item["index"] for item in record["references"]] == [1, 2]
    assert all(item["sha256"] == _digest(Path(item["path"])) for item in record["references"])
    assert record["mask"]["sha256"] == _digest(Path(record["mask"]["path"]))
    assert record["backend"]["sha256"] == hashlib.sha256(b"qwen_image/qwen-professional").hexdigest()

    admission_copy = tmp_path / "admission-copy.db"
    shutil.copy2(database, admission_copy)
    admission = JobQueue(admission_copy)
    try:
        assert admission.list_state("pending") == []
        assert admission.next_admissible() is None
        executor = JobExecutor(
            queue=admission,
            preflight=lambda _job: pytest.fail("image plan admitted"),
            render=lambda _clip: pytest.fail("image plan rendered"),
            qc=lambda _clip: pytest.fail("image plan reached QC"),
        )
        assert executor.run_once() is None
    finally:
        admission.close()
    assert database.read_bytes() == before

    genuine = JobQueue(tmp_path / "genuine.db")
    try:
        job_id = genuine.submit(plan_ref="genuine-render", clips=[{"clip_index": 1, "status": "pending", "kind": "ref2va_render"}])
        assert genuine.next_admissible() == job_id
    finally:
        genuine.close()

    reconstructed = _wgp("image", "plan", "--reconstruct", "--db", str(database), "--json", env=environment)
    assert reconstructed.returncode == 0, reconstructed.stdout + reconstructed.stderr
    evidence = json.loads(reconstructed.stdout)
    assert evidence["all_match"] is True and evidence["hidden_mutation"] is False
    assert evidence["records"][0]["recorded_settings_sha256"] == evidence["records"][0]["reconstructed_settings_sha256"]
    assert database.read_bytes() == before
    assert calls.read_text(encoding="utf-8") == ""


@pytest.mark.parametrize(
    "case",
    (
        "manifest-missing", "manifest-invalid", "hash-missing", "backend-incomplete",
        "operation-unsupported", "request-missing", "request-invalid", "reference-missing",
        "reference-hash", "mask-missing", "mask-hash", "mask-format", "output-size",
        "identity-gate", "enhancement", "queue-path", "queue-exists",
        "reconstruct-missing", "reconstruct-empty", "reconstruct-invalid",
    ),
)
def test_every_typed_failure_class_is_exit_2_without_partial_queue(
    tmp_path: Path, case: str
) -> None:
    environment, calls = _environment(tmp_path)
    models = tmp_path / "models.json"
    request = tmp_path / "request.json"
    database = tmp_path / "partial.db"
    _write_models(models)
    operation = "identity_edit"
    references = 1
    files = _write_request(request, operation=operation, references=references)
    expected = {
        "manifest-missing": "MODEL_MANIFEST_MISSING",
        "manifest-invalid": "MODEL_MANIFEST_INVALID",
        "hash-missing": "MODEL_HASH_MISSING",
        "backend-incomplete": "IMAGE_BACKEND_INCOMPLETE",
        "operation-unsupported": "IMAGE_OPERATION_UNSUPPORTED",
        "request-missing": "IMAGE_REQUEST_MISSING",
        "request-invalid": "IMAGE_REQUEST_INVALID",
        "reference-missing": "IMAGE_REFERENCE_MISSING",
        "reference-hash": "IMAGE_REFERENCE_UNUSABLE",
        "mask-missing": "IMAGE_MASK_MISSING",
        "mask-hash": "IMAGE_MASK_UNUSABLE",
        "mask-format": "IMAGE_MASK_INVALID",
        "output-size": "IMAGE_OUTPUT_UNSUPPORTED",
        "identity-gate": "IMAGE_IDENTITY_GATE_MISSING",
        "enhancement": "IMAGE_PROMPT_ENHANCEMENT_UNAUTHORIZED",
        "queue-path": "IMAGE_QUEUE_PATH_MISSING",
        "queue-exists": "IMAGE_QUEUE_EXISTS",
        "reconstruct-missing": "IMAGE_RECONSTRUCTION_DATABASE_MISSING",
        "reconstruct-empty": "IMAGE_RECONSTRUCTION_RECORDS_MISSING",
        "reconstruct-invalid": "IMAGE_RECONSTRUCTION_RECORD_INVALID",
    }[case]
    verb_args = ["image", "edit", "--request", str(request), "--models", str(models), "--db", str(database), "--json"]
    if case == "manifest-missing":
        models.unlink()
    elif case == "manifest-invalid":
        models.write_text("{", encoding="utf-8")
    elif case == "hash-missing":
        manifest = json.loads(models.read_text()); manifest["models"][0].pop("sha256"); models.write_text(json.dumps(manifest))
    elif case == "backend-incomplete":
        manifest = json.loads(models.read_text()); manifest["models"][0]["vram_profile"] = "8gb"; models.write_text(json.dumps(manifest))
    elif case == "operation-unsupported":
        _write_request(request, operation="upscale", references=1)
        document = json.loads(request.read_text()); document["model"] = {"family": "flux_kontext", "preset": "flux-kontext"}; request.write_text(json.dumps(document))
        verb_args = ["image", "upscale", "--request", str(request), "--models", str(models), "--db", str(database), "--json"]
    elif case == "request-missing":
        request.unlink()
    elif case == "request-invalid":
        verb_args = ["image", "upscale", "--request", str(request), "--models", str(models), "--db", str(database), "--json"]
    elif case == "reference-missing":
        files[0].unlink()
    elif case == "reference-hash":
        files[0].write_bytes(b"changed")
    elif case == "mask-missing":
        files[-1].unlink()
    elif case == "mask-hash":
        files[-1].write_bytes(b"changed-mask")
    elif case == "mask-format":
        document = json.loads(request.read_text()); document["mask"]["path"] = str(files[-1].with_suffix(".jpg")); request.write_text(json.dumps(document))
    elif case == "output-size":
        document = json.loads(request.read_text()); document["output"]["width"] = 1001; request.write_text(json.dumps(document))
    elif case == "identity-gate":
        document = json.loads(request.read_text()); document.pop("identity_gate"); request.write_text(json.dumps(document))
    elif case == "enhancement":
        document = json.loads(request.read_text()); document["prompt_enhancement"] = {"mode": "operator_authorized", "provider": "declared-provider"}; request.write_text(json.dumps(document))
    elif case == "queue-path":
        verb_args.remove("--db"); verb_args.remove(str(database))
    elif case == "queue-exists":
        database.parent.mkdir(parents=True, exist_ok=True); database.write_bytes(b"existing")
    elif case == "reconstruct-missing":
        verb_args = ["image", "plan", "--reconstruct", "--db", str(tmp_path / "missing.db"), "--json"]
    elif case == "reconstruct-empty":
        empty = tmp_path / "empty.db"; JobQueue(empty).close()
        verb_args = ["image", "plan", "--reconstruct", "--db", str(empty), "--json"]
    elif case == "reconstruct-invalid":
        valid = tmp_path / "valid.db"
        assert _wgp("image", "edit", "--request", str(request), "--models", str(models), "--db", str(valid), "--json", env=environment).returncode == 0
        connection = sqlite3.connect(valid)
        damaged = json.loads(connection.execute("SELECT record FROM image_plan_records").fetchone()[0]); damaged.pop("recipe")
        connection.execute("UPDATE image_plan_records SET record=?", (json.dumps(damaged),)); connection.commit(); connection.close()
        verb_args = ["image", "plan", "--reconstruct", "--db", str(valid), "--json"]

    result = _wgp(*verb_args, env=environment)
    assert result.returncode == 2, result.stdout + result.stderr
    diagnostic = json.loads(result.stdout)["diagnostics"][0]
    assert diagnostic["code"] == expected, result.stdout
    assert diagnostic["remediation"] and diagnostic["next_command"]
    assert "Traceback" not in result.stdout + result.stderr
    if case not in {"queue-exists", "reconstruct-missing", "reconstruct-empty", "reconstruct-invalid"}:
        assert not database.exists()
    assert calls.read_text(encoding="utf-8") == ""
