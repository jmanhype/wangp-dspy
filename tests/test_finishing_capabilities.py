"""Real-process no-GPU tests for typed finishing capabilities."""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import sqlite3
import subprocess
from functools import lru_cache
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from predict.finishing import (
    BACKEND_OPERATIONS,
    SCHEMA_VERSION,
    FinishingBackend,
    FinishingRequest,
    backend_settings,
    request_digest,
)
from services.finishing.pipeline import (
    compile_finishing_request,
    enqueue_plan,
    reconstruct_plan_database,
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
    choice_line = next(
        line for line in result.stdout.splitlines()
        if line.strip().startswith("{") and line.strip().endswith("}")
    )
    return frozenset(choice_line.strip().strip("{}").split(","))


@lru_cache(maxsize=1)
def _live_finish_verbs() -> frozenset[str]:
    result = _wgp("finish", "--help", env=os.environ.copy())
    assert result.returncode == 0, result.stdout + result.stderr
    choice_line = next(
        line for line in result.stdout.splitlines()
        if line.strip().startswith("{") and line.strip().endswith("}")
    )
    return frozenset(choice_line.strip().strip("{}").split(","))


def _assert_next_command_resolves_against_live_cli(command: str) -> None:
    tokens = command.split()
    assert tokens[0] == "wgp" and len(tokens) >= 3, command
    assert tokens[1] in _live_cli_verbs(), command
    assert tokens[1] == "finish", command
    assert tokens[2] in _live_finish_verbs(), command


def _request(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "backend": "ffmpeg",
        "source": {
            "path": "datasets/runs/provenance/v3-original/v3_c1.mp4",
            "sha256": "a" * 64,
            "immutable": True,
            "measurement": "declared_ffprobe_unverified",
            "stream": {
                "index": 0,
                "codec_name": "h264",
                "codec_type": "video",
                "width": 512,
                "height": 768,
                "duration_s": 4.0,
                "avg_frame_rate": "24/1",
            },
        },
        "interpolation": {
            "factor": "x2",
            "target_fps": 48.0,
            "scene_detection": True,
        },
        "film_grain": {"strength": 12.0, "size": 16, "temporal_persistence": 0.5},
        "output": {
            "path": "outputs/finished.mp4",
            "container": "mp4",
            "codec": "h264",
            "overwrite": False,
            "measurement": "planned_ffprobe_unverified",
        },
        "recipe_seed": 8107,
    }
    for key, value in overrides.items():
        if value is None:
            payload.pop(key, None)
        else:
            payload[key] = value
    return payload


def _mutate(payload: dict[str, Any], path: str, value: Any) -> dict[str, Any]:
    document = json.loads(json.dumps(payload))
    cursor: Any = document
    keys = path.split(".")
    for key in keys[:-1]:
        cursor = cursor[key]
    if value is None:
        cursor.pop(keys[-1], None)
    else:
        cursor[keys[-1]] = value
    return document


def _real_request(tmp_path: Path, **overrides: Any) -> dict[str, Any]:
    source = ROOT / "datasets/runs/provenance/v3-original/v3_c1.mp4"
    payload = _request(**overrides)
    payload["source"] = {
        "path": str(source),
        "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "immutable": True,
        "measurement": "declared_ffprobe_unverified",
        "stream": {
            "index": 0,
            "codec_name": "h264",
            "codec_type": "video",
            "width": 704,
            "height": 576,
            "duration_s": 2.333333,
            "avg_frame_rate": "24/1",
        },
    }
    payload["output"] = {
        "path": str(tmp_path / "finished.mp4"),
        "container": "mp4",
        "codec": "h264",
        "overwrite": False,
        "measurement": "planned_ffprobe_unverified",
    }
    return payload


def _tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        digest.update(str(path.relative_to(root)).encode("utf-8") + b"\0")
        digest.update(path.read_bytes())
    return digest.hexdigest()


def test_typed_finishing_request_normalizes_all_no_gpu_operations() -> None:
    request = FinishingRequest.model_validate(_request())
    assert request.backend is FinishingBackend.ffmpeg
    assert request.interpolation is not None
    assert request.film_grain is not None
    assert request.source.measurement == "declared_ffprobe_unverified"
    assert request.output.measurement == "planned_ffprobe_unverified"
    assert backend_settings(request)["operations"] == [
        "interpolation", "film_grain", "codec"
    ]
    assert backend_settings(request)["codec_arguments"][:2] == ["-c:v", "libx264"]
    assert request_digest(request) == request_digest(FinishingRequest.model_validate(_request()))


def test_typed_request_rejects_invalid_factor_backend_codec_and_face_geometry() -> None:
    cases = (
        (_mutate(_request(), "interpolation.factor", "x5"), "x5"),
        (_mutate(_request(), "backend", "rife"), "does not plan operations: film_grain"),
        (_mutate(_request(), "output.codec", "vp9"), "does not support codec vp9"),
        (_mutate(_request(), "interpolation.target_fps", 72.0), "must equal source fps"),
        (_request(film_grain=None, interpolation=None), "at least one refinement operation"),
    )
    for payload, expected in cases:
        try:
            FinishingRequest.model_validate(payload)
        except ValidationError as exc:
            assert expected in str(exc), f"{expected}: {exc}"
        else:
            raise AssertionError(f"accepted invalid request: {expected}")

    face_payload = _request(
        film_grain=None,
        face_refinement={
            "tracks": [{
                "track_id": "face-1",
                "identity_label": "Orin",
                "confidence": 0.94,
                "start_s": 0.0,
                "end_s": 2.0,
                "x": 0.8,
                "y": 0.1,
                "width": 0.4,
                "height": 0.2,
                "source": "operator-tracked",
                "license": "operator-recorded",
                "consent_ref": "orin-consent",
            }],
            "selected_track": "face-1",
            "strength": 0.3,
        },
    )
    try:
        FinishingRequest.model_validate(face_payload)
    except ValidationError as exc:
        assert "normalized bounds" in str(exc)
    else:
        raise AssertionError("accepted an out-of-bounds face region")


def test_neural_path_is_declared_unavailable_and_requires_neural_backend() -> None:
    neural = {
        "model_sha256": "b" * 64,
        "backend_profile": "authorized-host-only",
        "minimum_vram_gb": 16,
        "authorized_host": None,
        "support_status": "unavailable_without_authorized_host",
    }
    payload = _request(
        backend="neural_frame_gen",
        film_grain=None,
        neural_path=neural,
    )
    request = FinishingRequest.model_validate(payload)
    settings = backend_settings(request)
    assert settings["neural_execution"] == "unavailable"
    assert settings["neural_path"]["authorized_host"] is None

    unauthorized = _mutate(payload, "neural_path.authorized_host", "gpu-host")
    with_gpu_backend = _mutate(_request(), "neural_path", neural)
    for document, expected in (
        (unauthorized, "cannot authorize a neural host"),
        (with_gpu_backend, "requires backend neural_frame_gen"),
    ):
        try:
            FinishingRequest.model_validate(document)
        except ValidationError as exc:
            assert expected in str(exc)
        else:
            raise AssertionError(f"accepted invalid neural declaration: {expected}")


def test_backend_operation_matrix_and_manifest_hashes_are_explicit() -> None:
    assert "face_refinement" in BACKEND_OPERATIONS[FinishingBackend.ffmpeg]
    assert "film_grain" not in BACKEND_OPERATIONS[FinishingBackend.neural_frame_gen]
    assert all(re.fullmatch(r"[0-9a-f]{64}", digest) for digest in ("a" * 64, "b" * 64))
    assert hashlib.sha256(b"source").hexdigest() != "a" * 64


def test_finishing_plan_is_immutable_undrainable_and_reconstructable(
    tmp_path: Path,
) -> None:
    datasets_before = _tree_digest(ROOT / "datasets")
    source = ROOT / "datasets/runs/provenance/v3-original/v3_c1.mp4"
    source_before = source.read_bytes()
    request = FinishingRequest.model_validate(_real_request(tmp_path))
    plan = compile_finishing_request(request).mapping()
    record = plan["records"][0]
    assert plan["capability_status"] == "planned"
    assert record["kind"] == "finishing_plan_record"
    assert record["executable"] is False and record["plan_only"] is True
    assert record["queue_submitted"] is False and record["host_contact"] is False
    assert record["measurement_status"] == "unverified"
    assert [stage["stage_id"] for stage in record["command_graph"]] == [
        "probe", "interpolation", "film_grain", "codec"
    ]
    assert all(stage["executed"] is False for stage in record["command_graph"])

    database = tmp_path / "plans" / "finishing.db"
    record_ids = enqueue_plan(plan, database)
    assert len(record_ids) == 1
    database_before = database.read_bytes()
    connection = sqlite3.connect(database)
    tables = {row[0] for row in connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    )}
    assert "jobs" not in tables
    with pytest.raises(sqlite3.IntegrityError, match="immutable"):
        connection.execute("UPDATE finishing_plan_records SET record='changed'")
    with pytest.raises(sqlite3.IntegrityError, match="immutable"):
        connection.execute("DELETE FROM finishing_plan_records")
    connection.close()

    admission_copy = tmp_path / "admission-copy.db"
    shutil.copy2(database, admission_copy)
    admission = JobQueue(admission_copy)
    try:
        assert admission.list_state("pending") == []
        assert admission.next_admissible() is None
        executor = JobExecutor(
            queue=admission,
            preflight=lambda _job: pytest.fail("finishing plan admitted"),
            render=lambda _clip: pytest.fail("finishing plan rendered"),
            qc=lambda _clip: pytest.fail("finishing plan reached QC"),
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

    evidence = reconstruct_plan_database(database)
    assert len(evidence) == 1
    assert evidence[0]["match"] is True
    assert evidence[0]["hidden_mutation"] is False
    assert evidence[0]["recorded_command_graph_sha256"] == evidence[0]["reconstructed_command_graph_sha256"]
    assert database.read_bytes() == database_before
    assert source.read_bytes() == source_before
    assert _tree_digest(ROOT / "datasets") == datasets_before


def test_finish_plan_probe_and_run_cli_modes_are_real_processes(
    tmp_path: Path,
) -> None:
    environment, calls = _environment(tmp_path)
    request = tmp_path / "finishing.json"
    request.write_text(json.dumps(_real_request(tmp_path)), encoding="utf-8")
    plan_args = ("finish", "plan", "--request", str(request), "--dry-run")
    human = _wgp(*plan_args, env=environment)
    first = _wgp(*plan_args, "--json", env=environment)
    second = _wgp(*plan_args, "--json", env=environment)
    assert human.returncode == first.returncode == second.returncode == 0, (
        human.stdout + human.stderr + first.stdout + first.stderr
    )
    assert first.stdout == second.stdout
    assert "measurement_status=unverified" not in human.stdout
    assert "gpu_work=false media_generated=false" in human.stdout
    plan = json.loads(first.stdout)
    assert plan["capability_status"] == "planned"
    assert "queue" not in plan

    probe_args = ("finish", "probe", "--request", str(request))
    probe_human = _wgp(*probe_args, env=environment)
    probe_json = _wgp(*probe_args, "--json", env=environment)
    assert probe_human.returncode == probe_json.returncode == 0, (
        probe_human.stdout + probe_human.stderr + probe_json.stdout + probe_json.stderr
    )
    assert "measurement_status=unverified executed=false host_contact=false" in probe_human.stdout
    probe = json.loads(probe_json.stdout)
    assert probe["command_graph"][0]["stage_id"] == "probe"
    assert probe["executed"] is False and probe["host_contact"] is False

    run_human = _wgp("finish", "run", "--request", str(request), env=environment)
    run_json = _wgp("finish", "run", "--request", str(request), "--json", env=environment)
    assert run_human.returncode == run_json.returncode == 2, (
        run_human.stdout + run_human.stderr + run_json.stdout + run_json.stderr
    )
    diagnostic = json.loads(run_json.stdout)["diagnostics"][0]
    assert diagnostic["code"] == "FINISH_EXECUTION_UNAUTHORIZED"
    assert diagnostic["next_command"]
    _assert_next_command_resolves_against_live_cli(diagnostic["next_command"])
    assert calls.read_text(encoding="utf-8") == ""
