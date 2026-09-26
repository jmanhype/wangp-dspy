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
    FinishingCapabilityError,
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


def _face_refinement(track_ids: tuple[str, ...] = ("face-1",), selected: str | None = "face-1") -> dict[str, Any]:
    tracks = []
    for offset, track_id in enumerate(track_ids):
        tracks.append({
            "track_id": track_id,
            "identity_label": "Orin Vale",
            "confidence": 0.94,
            "start_s": 0.0,
            "end_s": 2.0,
            "x": 0.1 + offset * 0.01,
            "y": 0.1,
            "width": 0.3,
            "height": 0.3,
            "source": "operator-tracked",
            "license": "operator-recorded",
            "consent_ref": "orin-consent",
        })
    return {"tracks": tracks, "selected_track": selected, "strength": 0.3}


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


@pytest.mark.parametrize("factor", ("x2", "x3", "x4"))
def test_each_interpolation_factor_compiles_to_a_deterministic_graph(
    tmp_path: Path, factor: str
) -> None:
    target_fps = {"x2": 48.0, "x3": 72.0, "x4": 96.0}[factor]
    payload = _real_request(
        tmp_path,
        film_grain=None,
        interpolation={"factor": factor, "target_fps": target_fps, "scene_detection": True},
    )
    record = compile_finishing_request(FinishingRequest.model_validate(payload)).mapping()["records"][0]
    stage = next(item for item in record["command_graph"] if item["stage_id"] == "interpolation")
    assert f"fps={target_fps:g}" in stage["command"][6]
    assert record["backend_settings"]["interpolation"]["factor"] == factor


def test_interpolation_scene_detection_is_explicit_deterministic_and_plan_only(
    tmp_path: Path,
) -> None:
    payload = _real_request(tmp_path, film_grain=None)
    enabled = _mutate(payload, "interpolation.scene_detection", True)
    disabled = _mutate(payload, "interpolation.scene_detection", False)
    enabled_record = compile_finishing_request(
        FinishingRequest.model_validate(enabled)
    ).mapping()["records"][0]
    disabled_record = compile_finishing_request(
        FinishingRequest.model_validate(disabled)
    ).mapping()["records"][0]

    def interpolation_graph(record: dict[str, Any]) -> str:
        stage = next(
            item for item in record["command_graph"]
            if item["stage_id"] == "interpolation"
        )
        return stage["command"][6]

    enabled_graph = interpolation_graph(enabled_record)
    disabled_graph = interpolation_graph(disabled_record)
    assert enabled_graph.endswith(":scd=1")
    assert disabled_graph.endswith(":scd=0")
    assert enabled_graph != disabled_graph
    assert enabled_record["backend_settings"]["interpolation"]["scene_detection"] is True
    assert disabled_record["backend_settings"]["interpolation"]["scene_detection"] is False

    repeated_record = compile_finishing_request(
        FinishingRequest.model_validate(enabled)
    ).mapping()["records"][0]
    record_bytes = json.dumps(
        enabled_record, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    repeated_bytes = json.dumps(
        repeated_record, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    assert record_bytes == repeated_bytes
    assert enabled_record["backend_settings_sha256"] == repeated_record["backend_settings_sha256"]
    assert enabled_record["command_graph_sha256"] == repeated_record["command_graph_sha256"]
    for record in (enabled_record, disabled_record):
        assert record["plan_only"] is True
        assert all(
            record[key] is False for key in (
                "executable", "queue_submitted", "host_contact", "media_generated",
            )
        )
    assert all(
        record["measurement_status"] == "unverified"
        for record in (enabled_record, disabled_record)
    )
    assert all(
        stage["executed"] is False
        for record in (enabled_record, disabled_record)
        for stage in record["command_graph"]
    )


@pytest.mark.parametrize("scale", ("x2", "x3", "x4"))
def test_each_spatial_upscale_factor_compiles_to_a_deterministic_graph(
    tmp_path: Path, scale: str
) -> None:
    multiplier = {"x2": 2, "x3": 3, "x4": 4}[scale]
    payload = _real_request(
        tmp_path,
        interpolation=None,
        film_grain=None,
        spatial_upscale={"scale": scale, "model_sha256": None},
    )
    record = compile_finishing_request(FinishingRequest.model_validate(payload)).mapping()["records"][0]
    stage = next(item for item in record["command_graph"] if item["stage_id"] == "spatial_upscale")
    assert f"scale=iw*{multiplier}:ih*{multiplier}" in stage["command"][6]
    assert record["backend_settings"]["spatial_upscale"]["scale"] == scale


@pytest.mark.parametrize(
    "grain",
    (
        {"strength": 0.0, "size": 4, "temporal_persistence": 0.0},
        {"strength": 12.5, "size": 16, "temporal_persistence": 0.5},
        {"strength": 64.0, "size": 64, "temporal_persistence": 1.0},
    ),
)
def test_each_film_grain_control_setting_compiles_unexecuted(
    tmp_path: Path, grain: dict[str, float | int]
) -> None:
    payload = _real_request(tmp_path, interpolation=None, film_grain=grain)
    record = compile_finishing_request(FinishingRequest.model_validate(payload)).mapping()["records"][0]
    stage = next(item for item in record["command_graph"] if item["stage_id"] == "film_grain")
    graph = stage["command"][6]
    size = int(grain["size"])
    strength = format(float(grain["strength"]), ".17g")
    persistence = format(float(grain["temporal_persistence"]), ".17g")
    assert f"scale=ceil(iw/{size}):ceil(ih/{size})" in graph
    assert f"scale=iw*{size}:ih*{size}" in graph
    assert f"noise=alls={strength}" in graph
    assert f"all_opacity={persistence}" in graph
    assert "all_seed=8107" in graph
    assert stage["executed"] is False


def test_film_grain_size_and_temporal_persistence_each_change_the_graph(
    tmp_path: Path,
) -> None:
    def graph_for(grain: dict[str, float | int]) -> str:
        payload = _real_request(tmp_path, interpolation=None, film_grain=grain)
        record = compile_finishing_request(FinishingRequest.model_validate(payload)).mapping()["records"][0]
        return next(
            item["command"][6] for item in record["command_graph"]
            if item["stage_id"] == "film_grain"
        )

    size_4 = graph_for({"strength": 12.0, "size": 4, "temporal_persistence": 0.5})
    size_64 = graph_for({"strength": 12.0, "size": 64, "temporal_persistence": 0.5})
    assert size_4 != size_64
    assert "ceil(iw/4):ceil(ih/4)" in size_4 and "iw*4:ih*4" in size_4
    assert "ceil(iw/64):ceil(ih/64)" in size_64 and "iw*64:ih*64" in size_64

    reseeded = graph_for({"strength": 12.0, "size": 16, "temporal_persistence": 0.0})
    held = graph_for({"strength": 12.0, "size": 16, "temporal_persistence": 1.0})
    assert reseeded != held
    assert "all_opacity=0" in reseeded and "all_opacity=1" in held
    assert "allf=t+u" in reseeded and held


def test_film_grain_plan_is_deterministic_for_the_same_request_and_seed(
    tmp_path: Path,
) -> None:
    payload = _real_request(
        tmp_path,
        interpolation=None,
        film_grain={"strength": 12.0, "size": 16, "temporal_persistence": 0.5},
    )
    request = FinishingRequest.model_validate(payload)
    first = compile_finishing_request(request).mapping()
    second = compile_finishing_request(FinishingRequest.model_validate(payload)).mapping()
    assert first == second
    first_record, second_record = first["records"][0], second["records"][0]
    assert first_record["backend_settings_sha256"] == second_record["backend_settings_sha256"]
    assert first_record["command_graph_sha256"] == second_record["command_graph_sha256"]


def test_non_ffmpeg_film_grain_controls_fail_closed_without_backend_fallback(
    tmp_path: Path,
) -> None:
    payload = _real_request(
        tmp_path,
        backend="film",
        interpolation=None,
        film_grain={"strength": 12.0, "size": 17, "temporal_persistence": 0.75},
    )
    with pytest.raises(FinishingCapabilityError, match="film_grain.size") as raised:
        compile_finishing_request(FinishingRequest.model_validate(payload))
    assert raised.value.code == "FINISH_GRAIN_CONTROL_UNSUPPORTED"
    assert raised.value.metadata["unsupported_controls"] == [
        "film_grain.size", "film_grain.temporal_persistence"
    ]


@pytest.mark.parametrize(
    ("container", "codec", "encoder"),
    (
        ("mp4", "h264", "libx264"),
        ("mp4", "hevc", "libx265"),
        ("mp4", "av1", "libsvtav1"),
        ("mov", "h264", "libx264"),
        ("mov", "prores", "prores_ks"),
        ("mkv", "h264", "libx264"),
        ("mkv", "hevc", "libx265"),
        ("mkv", "vp9", "libvpx-vp9"),
        ("mkv", "av1", "libsvtav1"),
        ("webm", "vp9", "libvpx-vp9"),
    ),
)
def test_each_supported_codec_target_compiles_unmeasured(
    tmp_path: Path, container: str, codec: str, encoder: str
) -> None:
    payload = _real_request(tmp_path, interpolation=None)
    payload["output"].update({"container": container, "codec": codec})
    request = FinishingRequest.model_validate(payload)
    record = compile_finishing_request(request).mapping()["records"][0]
    stage = record["command_graph"][-1]
    assert encoder in stage["command"]
    assert record["output"]["codec"] == codec
    assert record["measurement_status"] == "unverified"


@pytest.mark.parametrize("tracks", (("face-1",), ("face-1", "face-2")))
def test_face_refinement_compiles_only_an_explicit_selected_track(
    tmp_path: Path, tracks: tuple[str, ...]
) -> None:
    selected = tracks[0]
    payload = _real_request(
        tmp_path,
        interpolation=None,
        film_grain=None,
        face_refinement=_face_refinement(tracks, selected=selected),
    )
    record = compile_finishing_request(FinishingRequest.model_validate(payload)).mapping()["records"][0]
    stage = next(item for item in record["command_graph"] if item["stage_id"] == "face_refinement")
    assert record["selected_face_track"]["track_id"] == selected
    assert "crop=" in stage["command"][6]
    assert "overlay=" in stage["command"][6]


@pytest.mark.parametrize("vram", (4, 16, 256))
def test_each_declared_neural_profile_remains_typed_unavailable(
    tmp_path: Path, vram: int
) -> None:
    payload = _real_request(
        tmp_path,
        backend="neural_frame_gen",
        film_grain=None,
        neural_path={
            "model_sha256": "b" * 64,
            "backend_profile": "authorized-host-only",
            "minimum_vram_gb": vram,
            "authorized_host": None,
            "support_status": "unavailable_without_authorized_host",
        },
    )
    with pytest.raises(FinishingCapabilityError, match="authorized host"):
        compile_finishing_request(FinishingRequest.model_validate(payload))


@pytest.mark.parametrize(
    ("case", "code"),
    (
        ("request-missing", "FINISH_REQUEST_MISSING"),
        ("request-invalid", "FINISH_REQUEST_INVALID"),
        ("operation-missing", "FINISH_OPERATION_MISSING"),
        ("operation-unsupported", "FINISH_OPERATION_UNSUPPORTED"),
        ("interpolation-invalid", "FINISH_INTERPOLATION_INVALID"),
        ("spatial-invalid", "FINISH_SPATIAL_UPSCALE_INVALID"),
        ("grain-control-unsupported", "FINISH_GRAIN_CONTROL_UNSUPPORTED"),
        ("codec-unsupported", "FINISH_CODEC_UNSUPPORTED"),
        ("face-invalid", "FINISH_FACE_TRACK_INVALID"),
        ("face-ambiguous", "FINISH_FACE_TRACK_AMBIGUOUS"),
        ("face-mismatch", "FINISH_FACE_TRACK_MISMATCH"),
        ("face-time", "FINISH_FACE_TRACK_OUT_OF_BOUNDS"),
        ("source-missing", "FINISH_SOURCE_MISSING"),
        ("source-hash", "FINISH_SOURCE_HASH_MISMATCH"),
        ("output-invalid", "FINISH_OUTPUT_INVALID"),
        ("output-exists", "FINISH_OUTPUT_EXISTS"),
        ("neural-unavailable", "FINISH_NEURAL_PATH_UNAVAILABLE"),
        ("queue-path", "FINISH_QUEUE_PATH_MISSING"),
        ("queue-exists", "FINISH_QUEUE_EXISTS"),
        ("run-unauthorized", "FINISH_EXECUTION_UNAUTHORIZED"),
        ("reconstruct-missing", "FINISH_RECONSTRUCTION_DATABASE_MISSING"),
        ("reconstruct-empty", "FINISH_RECONSTRUCTION_RECORDS_MISSING"),
        ("reconstruct-record", "FINISH_RECONSTRUCTION_RECORD_INVALID"),
    ),
)
def test_every_typed_failure_class_is_exit_2_and_next_command_resolves_live(
    tmp_path: Path,
    case: str,
    code: str,
) -> None:
    environment, calls = _environment(tmp_path)
    request_path = tmp_path / "request.json"
    database = tmp_path / "partial.db"
    payload = _real_request(tmp_path)
    command = ["finish", "plan", "--request", str(request_path), "--db", str(database), "--json"]

    if case == "request-missing":
        request_path = tmp_path / "absent.json"
        command[3] = str(request_path)
    elif case == "request-invalid":
        request_path.write_text("{", encoding="utf-8")
    elif case == "operation-missing":
        payload["interpolation"] = None
        payload["film_grain"] = None
    elif case == "operation-unsupported":
        payload["backend"] = "rife"
    elif case == "interpolation-invalid":
        payload["interpolation"]["target_fps"] = 72.0
    elif case == "spatial-invalid":
        payload.update({
            "backend": "real_esrgan",
            "interpolation": None,
            "film_grain": None,
            "spatial_upscale": {"scale": "x2", "model_sha256": None},
        })
    elif case == "grain-control-unsupported":
        payload["backend"] = "film"
        payload["interpolation"] = None
        payload["film_grain"].update({"size": 17, "temporal_persistence": 0.75})
    elif case == "codec-unsupported":
        payload["output"].update({"container": "webm", "codec": "h264"})
    elif case == "face-invalid":
        payload["film_grain"] = None
        face = _face_refinement(("face-1",))
        face["tracks"][0]["width"] = 0.9
        face["tracks"][0]["x"] = 0.8
        payload["face_refinement"] = face
    elif case == "face-ambiguous":
        payload["film_grain"] = None
        payload["face_refinement"] = _face_refinement(("face-1", "face-2"), selected=None)
    elif case == "face-mismatch":
        payload["film_grain"] = None
        payload["face_refinement"] = _face_refinement(("face-1",), selected="face-2")
    elif case == "face-time":
        payload["film_grain"] = None
        face = _face_refinement(("face-1",))
        face["tracks"][0]["end_s"] = 9.0
        payload["face_refinement"] = face
    elif case == "source-missing":
        payload["source"]["path"] = str(tmp_path / "absent-source.mp4")
    elif case == "source-hash":
        payload["source"]["sha256"] = "b" * 64
    elif case == "output-invalid":
        payload["output"]["path"] = payload["source"]["path"]
    elif case == "output-exists":
        output = tmp_path / "existing.mp4"
        output.write_bytes(b"exists")
        payload["output"]["path"] = str(output)
    elif case == "neural-unavailable":
        payload.update({
            "backend": "neural_frame_gen",
            "film_grain": None,
            "neural_path": {
                "model_sha256": "b" * 64,
                "backend_profile": "authorized-host-only",
                "minimum_vram_gb": 16,
                "authorized_host": None,
                "support_status": "unavailable_without_authorized_host",
            },
        })
    elif case == "queue-path":
        command = ["finish", "plan", "--request", str(request_path), "--json"]
    elif case == "queue-exists":
        database.write_bytes(b"exists")
    elif case == "run-unauthorized":
        command = ["finish", "run", "--request", str(request_path), "--json"]
    elif case == "reconstruct-missing":
        command = ["finish", "plan", "--db", str(tmp_path / "absent.db"), "--reconstruct", "--json"]
    elif case == "reconstruct-empty":
        connection = sqlite3.connect(database)
        connection.execute(
            "CREATE TABLE finishing_plan_records("
            "record_id TEXT PRIMARY KEY, plan_ref TEXT NOT NULL, record_index INTEGER NOT NULL, "
            "record TEXT NOT NULL, created_at REAL NOT NULL)"
        )
        connection.close()
        command = ["finish", "plan", "--db", str(database), "--reconstruct", "--json"]
    elif case == "reconstruct-record":
        request_path.write_text(json.dumps(payload), encoding="utf-8")
        valid = _wgp(
            "finish", "plan", "--request", str(request_path),
            "--db", str(tmp_path / "valid.db"), "--json", env=environment,
        )
        assert valid.returncode == 0, valid.stdout + valid.stderr
        connection = sqlite3.connect(tmp_path / "valid.db")
        connection.execute("DROP TRIGGER finishing_plan_records_immutable_update")
        record_id, raw = connection.execute(
            "SELECT record_id, record FROM finishing_plan_records"
        ).fetchone()
        damaged = json.loads(raw)
        damaged.pop("recipe")
        connection.execute(
            "UPDATE finishing_plan_records SET record=? WHERE record_id=?",
            (json.dumps(damaged), record_id),
        )
        connection.commit()
        connection.close()
        command = ["finish", "plan", "--db", str(tmp_path / "valid.db"), "--reconstruct", "--json"]

    if not request_path.exists() and case not in {
        "request-missing", "request-invalid",
        "queue-path", "run-unauthorized", "reconstruct-missing",
        "reconstruct-empty", "reconstruct-record",
    }:
        request_path.write_text(json.dumps(payload), encoding="utf-8")

    human_command = [item for item in command if item != "--json"]
    human = _wgp(*human_command, env=environment)
    machine = _wgp(*command, env=environment)
    assert human.returncode == machine.returncode == 2, (
        f"{case}: {human.returncode}/{machine.returncode} "
        f"{human.stdout}{human.stderr}{machine.stdout}{machine.stderr}"
    )
    assert "Traceback" not in human.stdout + human.stderr + machine.stdout + machine.stderr
    diagnostic = json.loads(machine.stdout)["diagnostics"][0]
    assert diagnostic["code"] == code, f"{case}: {diagnostic}"
    assert diagnostic["remediation"]
    _assert_next_command_resolves_against_live_cli(diagnostic["next_command"])
    if command[1] == "plan" and case not in {
        "queue-exists", "reconstruct-missing", "reconstruct-empty", "reconstruct-record"
    }:
        assert not database.exists()
    assert calls.read_text(encoding="utf-8") == ""
