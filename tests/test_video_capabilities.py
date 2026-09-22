"""Real-process no-GPU coverage for Maestro video breadth planning."""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import subprocess
from pathlib import Path

import pytest

from services.jobs.executor import JobExecutor
from services.jobs.queue import JobQueue


ROOT = Path(__file__).resolve().parents[1]
HOST_KEYS = (
    "WANGP_SSH_TARGET",
    "WANGP_WGP_ROOT",
    "WANGP_PULL_ROOT",
    "WANGP_WGP_PYTHON",
)

MODEL_CASES = (
    ("minimax_h3", "standard", "create"),
    ("minimax_h3", "h3_vdn_hybrid_attention", "extend"),
    ("minimax_h3", "taomate_three_step", "edit"),
    ("minimax_h3", "kfi_frames_injection", "retake"),
    ("minimax_h3", "h3_outpaint", "outpaint"),
    ("minimax_h3", "h3_audio_refinement", "edit"),
    ("ltx", "2.5", "recast"),
    ("ltx", "2.3", "upscale"),
    ("scail", "2", "repaint"),
    ("wan", "2gp", "blend"),
    ("hunyuan", "standard", "create"),
)


def _write_models(path: Path, *, drop_hash: bool = False) -> None:
    entries = []
    for family, preset, _operation in MODEL_CASES:
        digest = hashlib.sha256(f"{family}/{preset}".encode()).hexdigest()
        entry = {
            "family": family,
            "preset": preset,
            "sha256": digest,
            "license": "operator-recorded upstream license",
            "license_accepted": True,
            "vram_profile": "24gb" if family in {"minimax_h3", "scail", "hunyuan"} else "16gb",
        }
        if drop_hash and family == "minimax_h3" and preset == "standard":
            entry.pop("sha256")
        entries.append(entry)
    path.write_text(json.dumps({"models": entries}), encoding="utf-8")


def _write_request(
    path: Path,
    *,
    family: str = "minimax_h3",
    preset: str = "standard",
    operation: str = "create",
    clips: int = 1,
    overlap_frames: int = 0,
    mode: str = "one_window",
    reference: str | None = None,
    lora: str | None = None,
    **overrides: object,
) -> None:
    prompts = []
    for index in range(clips):
        clip = {
            "prompt": f"deterministic clip {index + 1}",
            "duration_s": 4.0,
        }
        if operation != "create":
            clip["reference"] = str(Path(reference or "").resolve())
        prompts.append(clip)
    control = {"mode": mode}
    if mode == "one_window":
        control["one_window"] = True
    elif mode == "exact_timecode":
        control["exact_timecode"] = {
            "start": "00:00:00:00",
            "end": "00:00:07:20" if clips == 2 else "00:00:04:00",
        }
    else:
        control["window_count"] = clips
    request = {
        "schema_version": "wangp-dspy.video-capability-request/v1",
        "model": {"family": family, "preset": preset},
        "operation": operation,
        "clips": prompts,
        "overlap": {
            "strategy": "sliding_window" if overlap_frames else "none",
            "frames": overlap_frames,
        },
        "long_form": control,
        "loras": [],
        "render": {
            "width": 480,
            "height": 832,
            "num_inference_steps": 20,
            "guidance_scale": 1.0,
            "embedded_guidance_scale": 6.0,
            "force_fps": "24",
            "profile": "profile3",
        },
        "recipe_seed": 904,
    }
    if lora is not None:
        request["loras"] = [{
            "path": str(Path(lora).resolve()),
            "sha256": (
                hashlib.sha256(Path(lora).read_bytes()).hexdigest()
                if Path(lora).is_file() else "a" * 64
            ),
            "weight": 0.5,
        }]
    request.update(overrides)
    path.write_text(json.dumps(request), encoding="utf-8")


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


def _wgp(
    *args: str, cwd: Path, env: dict[str, str]
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["uv", "run", "--frozen", "--extra", "dev", "wgp", *args],
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )


@pytest.mark.parametrize(
    ("family", "preset", "operation"), MODEL_CASES
)
def test_real_cli_normalizes_every_named_family_preset_and_operation(
    tmp_path: Path, family: str, preset: str, operation: str
) -> None:
    environment, calls = _environment(tmp_path)
    models = tmp_path / "models.json"
    request = tmp_path / "request.json"
    reference = tmp_path / "reference.mp4"
    reference.write_bytes(b"reference")
    _write_models(models)
    _write_request(
        request,
        family=family,
        preset=preset,
        operation=operation,
        reference=str(reference),
    )
    result = _wgp(
        "video", "--request", str(request), "--models", str(models),
        "--dry-run", "--json", cwd=ROOT, env=environment,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["capability_status"] == "planned"
    assert payload["operation"] == operation
    assert payload["clips"][0]["backend"]["preset"] == preset
    assert payload["summary"] == {
        "gpu_work": False,
        "queue_submitted": False,
        "host_contact": False,
    }
    assert payload["clips"][0]["backend_settings"]["force_fps"] == "24"
    assert calls.read_text(encoding="utf-8") == ""


def test_long_form_controls_overlap_lora_and_deterministic_json(
    tmp_path: Path,
) -> None:
    environment, calls = _environment(tmp_path)
    models = tmp_path / "models.json"
    lora = tmp_path / "style-lora.safetensors"
    lora.write_bytes(b"style-lora-bytes")
    _write_models(models)
    for mode, overlap in (
        ("one_window", 0), ("exact_timecode", 4), ("window_count", 4)
    ):
        request = tmp_path / f"{mode}.json"
        count = 1 if mode == "one_window" else 2
        if mode == "exact_timecode":
            count = 2
        _write_request(
            request,
            family="wan",
            preset="2gp",
            operation="create",
            clips=count,
            overlap_frames=overlap,
            mode=mode,
            lora=str(lora),
        )
        first = _wgp(
            "video", "--request", str(request), "--models", str(models),
            "--dry-run", "--json", cwd=ROOT, env=environment,
        )
        assert first.returncode == 0, first.stdout + first.stderr
        second = _wgp(
            "video", "--request", str(request), "--models", str(models),
            "--dry-run", "--json", cwd=ROOT, env=environment,
        )
        assert second.stdout == first.stdout
        payload = json.loads(first.stdout)
        assert payload["long_form_mode"] == mode
        assert payload["clips"][0]["loras"][0]["weight"] == "0.5"
        if overlap:
            assert payload["clips"][0]["window"]["overlap_frames"] == overlap
            assert payload["accounted_duration_s"] == pytest.approx(7.833333)
    assert calls.read_text(encoding="utf-8") == ""


def test_real_temporary_plan_store_is_immutable_unsubmitted_undrainable_and_reconstructable(
    tmp_path: Path,
) -> None:
    environment, calls = _environment(tmp_path)
    models = tmp_path / "models.json"
    request = tmp_path / "request.json"
    lora = tmp_path / "style-lora.safetensors"
    lora.write_bytes(b"style-lora-bytes")
    database = tmp_path / "run" / "jobs.db"
    _write_models(models)
    _write_request(
        request,
        family="minimax_h3",
        preset="h3_vdn_hybrid_attention",
        operation="create",
        clips=3,
        overlap_frames=6,
        mode="window_count",
        lora=str(lora),
    )
    result = _wgp(
        "video", "--request", str(request), "--models", str(models),
        "--db", str(database), "--json", cwd=ROOT, env=environment,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "queue_submitted=false" not in result.stdout  # machine payload is JSON
    payload = json.loads(result.stdout)
    assert payload["summary"]["queue_submitted"] is False
    assert len(payload["queue"]["record_ids"]) == 3
    assert payload["queue"]["executable_jobs"] == 0

    connection = sqlite3.connect(database)
    rows = connection.execute(
        "SELECT record_id, record FROM video_plan_records "
        "ORDER BY clip_index, created_at, record_id"
    ).fetchall()
    connection.close()
    assert len(rows) == 3
    for index, (_record_id, raw_record) in enumerate(rows, start=1):
        clip = json.loads(raw_record)
        assert clip["clip_index"] == index
        assert clip["kind"] == "video_plan_record"
        assert clip["plan_only"] is True
        assert clip["executable"] is False
        assert clip["queue_submitted"] is False
        assert clip["host_contact"] is False
        assert clip["backend_settings"]["prompt"] == "multishot"
        assert clip["backend_settings"]["profile"] == 3
        assert clip["operation"] == "create"
        assert clip["backend"]["sha256"] == hashlib.sha256(
            b"minimax_h3/h3_vdn_hybrid_attention"
        ).hexdigest()
        assert clip["loras"][0]["sha256"] == hashlib.sha256(
            b"style-lora-bytes"
        ).hexdigest()
        assert clip["window"]["overlap_frames"] == (6 if index < 3 else 0)
        assert clip["overlap"] == {"strategy": "sliding_window", "frames": 6}
    assert clip["recipe_seed"] == 904
    assert calls.read_text(encoding="utf-8") == ""

    admission_queue = JobQueue(database)
    try:
        assert admission_queue.list_state("pending") == []
        assert admission_queue.next_admissible() is None
        executor = JobExecutor(
            queue=admission_queue,
            preflight=lambda _job: pytest.fail("plan-only artifact admitted"),
            render=lambda _clip: pytest.fail("plan-only clip rendered"),
            qc=lambda _clip: pytest.fail("plan-only clip reached QC"),
        )
        assert executor.run_once() is None
    finally:
        admission_queue.close()

    reconstructed = _wgp(
        "video", "--reconstruct", "--db", str(database), "--json",
        cwd=ROOT, env=environment,
    )
    assert reconstructed.returncode == 0, reconstructed.stdout + reconstructed.stderr
    evidence = json.loads(reconstructed.stdout)
    assert evidence["all_match"] is True
    assert evidence["hidden_mutation"] is False
    assert len(evidence["records"]) == 3
    assert all(item["match"] for item in evidence["records"])
    assert calls.read_text(encoding="utf-8") == ""


@pytest.mark.parametrize(("frame", "valid"), [(23, True), (24, False), (99, False)])
def test_timecode_frame_boundary_is_enforced_at_24fps(
    frame: int, valid: bool
) -> None:
    from predict.video_capabilities import VideoCapabilityError, parse_timecode

    value = f"00:00:00:{frame:02d}"
    if valid:
        assert parse_timecode(value) == pytest.approx(frame / 24)
        return
    with pytest.raises(VideoCapabilityError) as raised:
        parse_timecode(value)
    assert raised.value.code == "VIDEO_TIMECODE_INVALID"
    assert f"frame field {frame} is outside 0..23" in raised.value.observed


def test_non_24fps_request_gets_structured_rejection(tmp_path: Path) -> None:
    environment, calls = _environment(tmp_path)
    models = tmp_path / "models.json"
    request = tmp_path / "request.json"
    _write_models(models)
    _write_request(request)
    document = json.loads(request.read_text())
    document["render"]["force_fps"] = "30"
    request.write_text(json.dumps(document), encoding="utf-8")
    result = _wgp(
        "video", "--request", str(request), "--models", str(models),
        "--dry-run", "--json", cwd=ROOT, env=environment,
    )
    assert result.returncode == 2
    diagnostic = json.loads(result.stdout)["diagnostics"][0]
    assert diagnostic["code"] == "VIDEO_FRAME_RATE_UNSUPPORTED"
    assert "30" in diagnostic["observed"]
    assert calls.read_text(encoding="utf-8") == ""


@pytest.mark.parametrize(
    ("mutation_name", "expected_code"),
    [
        ("wrong_family_preset", "MODEL_MANIFEST_MISSING"),
        ("clip_below_job_floor", "VIDEO_FRAME_COUNT_BELOW_FLOOR"),
    ],
)
def test_expected_validation_failures_stay_machine_readable(
    tmp_path: Path, mutation_name: str, expected_code: str
) -> None:
    environment, calls = _environment(tmp_path)
    models = tmp_path / "models.json"
    request = tmp_path / "request.json"
    _write_models(models)
    _write_request(request)
    document = json.loads(request.read_text())
    if mutation_name == "wrong_family_preset":
        document["model"]["preset"] = "2.5"
    else:
        document["clips"][0]["duration_s"] = 1.0
    request.write_text(json.dumps(document), encoding="utf-8")
    result = _wgp(
        "video", "--request", str(request), "--models", str(models),
        "--dry-run", "--json", cwd=ROOT, env=environment,
    )
    assert result.returncode == 2, result.stdout + result.stderr
    diagnostic = json.loads(result.stdout)["diagnostics"][0]
    assert diagnostic["code"] == expected_code
    assert diagnostic["next_command"]
    assert calls.read_text(encoding="utf-8") == ""


def test_absent_create_reference_is_ignored_consistently(tmp_path: Path) -> None:
    environment, calls = _environment(tmp_path)
    models = tmp_path / "models.json"
    request = tmp_path / "request.json"
    _write_models(models)
    _write_request(request, operation="create")
    document = json.loads(request.read_text())
    document["clips"][0]["reference"] = str(tmp_path / "not-needed.mp4")
    request.write_text(json.dumps(document), encoding="utf-8")
    result = _wgp(
        "video", "--request", str(request), "--models", str(models),
        "--dry-run", "--json", cwd=ROOT, env=environment,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["clips"][0]["reference"] is None
    assert calls.read_text(encoding="utf-8") == ""


def test_reconstruction_fails_closed_for_missing_empty_nonpending_or_corrupt_records(
    tmp_path: Path,
) -> None:
    environment, _calls = _environment(tmp_path)
    missing = tmp_path / "missing.db"
    missing_result = _wgp(
        "video", "--reconstruct", "--db", str(missing), "--json",
        cwd=ROOT, env=environment,
    )
    assert missing_result.returncode == 2
    assert json.loads(missing_result.stdout)["diagnostics"][0]["code"] == (
        "VIDEO_RECONSTRUCTION_DATABASE_MISSING"
    )

    empty = tmp_path / "empty.db"
    JobQueue(empty).close()
    empty_result = _wgp(
        "video", "--reconstruct", "--db", str(empty), "--json",
        cwd=ROOT, env=environment,
    )
    assert empty_result.returncode == 2
    empty_diagnostic = json.loads(empty_result.stdout)["diagnostics"][0]
    assert empty_diagnostic["code"] == "VIDEO_RECONSTRUCTION_RECORDS_MISSING"
    assert empty_diagnostic["metadata"]["state_counts"]["pending"] == 0

    nonpending = tmp_path / "nonpending.db"
    queue = JobQueue(nonpending)
    job_id = queue.submit(
        plan_ref="legacy", clips=[{"clip_index": 1, "status": "pending"}]
    )
    queue.set_state(job_id, "preflight")
    queue.set_state(job_id, "rendering")
    queue.set_state(job_id, "failed")
    queue.close()
    nonpending_result = _wgp(
        "video", "--reconstruct", "--db", str(nonpending), "--json",
        cwd=ROOT, env=environment,
    )
    assert nonpending_result.returncode == 2
    nonpending_diagnostic = json.loads(nonpending_result.stdout)["diagnostics"][0]
    assert nonpending_diagnostic["code"] == "VIDEO_RECONSTRUCTION_RECORDS_MISSING"
    assert nonpending_diagnostic["metadata"]["state_counts"]["failed"] == 1

    models = tmp_path / "models.json"
    request = tmp_path / "request.json"
    corrupt = tmp_path / "corrupt.db"
    _write_models(models)
    _write_request(request)
    assert _wgp(
        "video", "--request", str(request), "--models", str(models),
        "--db", str(corrupt), "--json", cwd=ROOT, env=environment,
    ).returncode == 0
    connection = sqlite3.connect(corrupt)
    record_id, raw = connection.execute(
        "SELECT record_id, record FROM video_plan_records"
    ).fetchone()
    damaged = json.loads(raw)
    damaged.pop("recipe")
    connection.execute(
        "UPDATE video_plan_records SET record=? WHERE record_id=?",
        (json.dumps(damaged), record_id),
    )
    connection.commit()
    connection.close()
    corrupt_result = _wgp(
        "video", "--reconstruct", "--db", str(corrupt), "--json",
        cwd=ROOT, env=environment,
    )
    assert corrupt_result.returncode == 2
    corrupt_diagnostic = json.loads(corrupt_result.stdout)["diagnostics"][0]
    assert corrupt_diagnostic["code"] == "VIDEO_RECONSTRUCTION_RECORD_INVALID"
    assert corrupt_diagnostic["metadata"]["record_id"] == record_id


@pytest.mark.parametrize(
    (
        "case",
        "code",
        "family",
        "preset",
        "operation",
        "overlap_frames",
        "mode",
        "drop_hash",
        "write_reference",
        "write_lora",
    ),
    [
        ("manifest-missing", "MODEL_MANIFEST_MISSING", "minimax_h3", "standard", "create", 0, "one_window", False, True, True),
        ("hash-missing", "MODEL_HASH_MISSING", "minimax_h3", "standard", "create", 0, "one_window", True, True, True),
        ("operation-unsupported", "VIDEO_OPERATION_UNSUPPORTED", "hunyuan", "standard", "outpaint", 0, "one_window", False, True, True),
        ("overlap-invalid", "VIDEO_OVERLAP_INVALID", "minimax_h3", "standard", "create", 0, "exact_timecode", False, True, True),
        ("timecode-invalid", "VIDEO_TIMECODE_INVALID", "minimax_h3", "standard", "create", 0, "exact_timecode", False, True, True),
        ("window-invalid", "VIDEO_WINDOW_COUNT_INVALID", "minimax_h3", "standard", "create", 0, "window_count", False, True, True),
        ("reference-missing", "VIDEO_REFERENCE_MISSING", "minimax_h3", "standard", "edit", 0, "one_window", False, False, True),
        ("lora-missing", "VIDEO_LORA_UNUSABLE", "minimax_h3", "standard", "create", 0, "one_window", False, True, False),
        ("lora-hash-mismatch", "VIDEO_LORA_UNUSABLE", "minimax_h3", "standard", "create", 0, "one_window", False, True, True),
        ("vram-invalid", "VIDEO_BACKEND_INCOMPLETE", "minimax_h3", "standard", "create", 0, "one_window", False, True, True),
        ("license-missing", "VIDEO_BACKEND_INCOMPLETE", "minimax_h3", "standard", "create", 0, "one_window", False, True, True),
    ],
)
def test_every_incomplete_or_unsupported_request_fails_typed_without_partial_queue(
    tmp_path: Path,
    case: str,
    code: str,
    family: str,
    preset: str,
    operation: str,
    overlap_frames: int,
    mode: str,
    drop_hash: bool,
    write_reference: bool,
    write_lora: bool,
) -> None:
    environment, calls = _environment(tmp_path)
    models = tmp_path / "models.json"
    request = tmp_path / "request.json"
    database = tmp_path / "partial.db"
    reference = tmp_path / "reference.mp4"
    if write_reference:
        reference.write_bytes(b"reference")
    lora = tmp_path / "lora.safetensors"
    if write_lora:
        lora.write_bytes(b"lora")
    _write_models(models, drop_hash=drop_hash)
    if case == "manifest-missing":
        models.unlink()
    _write_request(
        request,
        family=family,
        preset=preset,
        operation=operation,
        clips=1 if mode != "window_count" else 2,
        overlap_frames=overlap_frames,
        mode=mode,
        reference=str(reference),
        lora=str(lora),
    )
    if case == "overlap-invalid":
        document = json.loads(request.read_text())
        document["overlap"] = {"strategy": "sliding_window", "frames": 0}
        request.write_text(json.dumps(document), encoding="utf-8")
    elif case == "timecode-invalid":
        document = json.loads(request.read_text())
        document["long_form"]["exact_timecode"]["end"] = "00:00:99:00"
        request.write_text(json.dumps(document), encoding="utf-8")
    elif case == "window-invalid":
        document = json.loads(request.read_text())
        document["long_form"]["window_count"] = 3
        request.write_text(json.dumps(document), encoding="utf-8")
    elif case == "vram-invalid":
        manifest = json.loads(models.read_text())
        for entry in manifest["models"]:
            if entry["family"] == "minimax_h3" and entry["preset"] == "standard":
                entry["vram_profile"] = "8gb"
        models.write_text(json.dumps(manifest), encoding="utf-8")
    elif case == "license-missing":
        manifest = json.loads(models.read_text())
        for entry in manifest["models"]:
            if entry["family"] == "minimax_h3" and entry["preset"] == "standard":
                entry.pop("license", None)
        models.write_text(json.dumps(manifest), encoding="utf-8")
    if case == "lora-hash-mismatch":
        document = json.loads(request.read_text())
        document["loras"][0]["sha256"] = "b" * 64
        request.write_text(json.dumps(document), encoding="utf-8")

    result = _wgp(
        "video", "--request", str(request), "--models", str(models),
        "--db", str(database), "--json", cwd=ROOT, env=environment,
    )
    assert result.returncode == 2, result.stdout + result.stderr
    diagnostic = json.loads(result.stdout)["diagnostics"][0]
    assert diagnostic["code"] == code
    assert diagnostic["remediation"]
    assert diagnostic["next_command"]
    assert "Traceback" not in result.stdout + result.stderr
    assert not database.exists()
    assert list(tmp_path.glob(".partial.db.*")) == []
    assert calls.read_text(encoding="utf-8") == ""
