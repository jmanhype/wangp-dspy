"""Real-process local preparation and fail-closed authorization coverage."""
from __future__ import annotations

import copy
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

import pytest

import scripts.run_editor_host_export as runner
from scripts.verify_maestro_parity import verify_bundle
from services.editor.assembly_exporter import enqueue_export
from services.editor.project_store import ProjectStore
from services.jobs.queue import JobQueue


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "datasets/runs/maestro-parity/editor-host-export/operator-authorization.template.json"
VIDEO = ROOT / "datasets/runs/provenance/lf002-vibevoice-film-20260917/cut1.mp4"
AUDIO = ROOT / "datasets/runs/provenance/lf002-vibevoice-audition-20260916/audio/orin.wav"
SCRIPT = ROOT / "scripts/run_editor_host_export.py"


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _temporary_repository(tmp_path: Path) -> Path:
    root = tmp_path / "repository"
    video = root / "datasets/runs/provenance/lf002-vibevoice-film-20260917"
    audio = root / "datasets/runs/provenance/lf002-vibevoice-audition-20260916/audio"
    video.mkdir(parents=True)
    audio.mkdir(parents=True)
    shutil.copyfile(VIDEO, video / "cut1.mp4")
    shutil.copyfile(AUDIO, audio / "orin.wav")
    return root


def _boundary_environment(tmp_path: Path) -> tuple[dict[str, str], Path]:
    """Instrument external boundaries without mocking any core Wangp behavior."""
    forbidden = tmp_path / "forbidden-bin"
    forbidden.mkdir(exist_ok=True)
    calls = tmp_path / "external-calls.log"
    calls.write_text("", encoding="utf-8")
    for name in ("ssh", "scp", "rsync", "curl", "wget", "nvidia-smi"):
        command = forbidden / name
        command.write_text(
            f'#!/bin/sh\nprintf "%s\\n" "{name} $*" >> {calls}\nexit 99\n',
            encoding="utf-8",
        )
        command.chmod(0o755)
    environment = os.environ.copy()
    environment["PATH"] = f"{forbidden}:{environment['PATH']}"
    environment.pop("WANGP_SSH_TARGET", None)
    return environment, calls


def _authorization() -> dict[str, Any]:
    record = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    record["status"] = "authorized"
    record["authorization"]["record"] = {
        "operator": "operator",
        "recorded_utc": "2026-09-29T23:17:30Z",
        "verbatim": "Authorize",
    }
    return record


def _rejection(record: Mapping[str, object]) -> runner.EditorHostExportError:
    with pytest.raises(runner.EditorHostExportError) as raised:
        runner.verify_authorization(record)
    return raised.value


def test_prepare_reproduces_exact_reference_and_preserves_sources(tmp_path: Path) -> None:
    root = _temporary_repository(tmp_path)
    original_hashes = {path: _hash(path) for path in (VIDEO, AUDIO)}
    project_path = runner.prepare_reference(root)
    export_path = root / "datasets/runs/maestro-parity/editor-host-export/export.json"
    copied_video = project_path.parent / "sources/video-cut.mp4"
    copied_audio = project_path.parent / "sources/voice.wav"

    assert _hash(project_path) == runner.PROJECT_FILE_SHA256
    assert _hash(export_path) == runner.EXPORT_SHA256
    assert {path: _hash(path) for path in (VIDEO, AUDIO, copied_video, copied_audio)} == {
        **original_hashes,
        copied_video: runner.VIDEO_SHA256,
        copied_audio: runner.AUDIO_SHA256,
    }

    store = ProjectStore(project_path)
    project = store.load().project
    assert store.verify_sources(project) == list(project.sources)
    payload = json.loads(export_path.read_text(encoding="utf-8"))
    assert payload["project_sha256"] == runner.PROJECT_IDENTITY_SHA256
    assert payload["director"]["plan"]["request_sha256"] == runner.DIRECTOR_REQUEST_SHA256
    assert payload["assembly"]["continuity_digest"] == runner.CONTINUITY_DIGEST
    assert runner.verify_reference(root) == project_path


def test_committed_reference_is_verified_without_regeneration() -> None:
    assert runner.prepare_reference(ROOT) == ROOT / runner.PROJECT_RELATIVE
    assert runner.verify_reference(ROOT) == ROOT / runner.PROJECT_RELATIVE


def test_real_queue_admits_exactly_one_pending_editor_export(tmp_path: Path) -> None:
    root = _temporary_repository(tmp_path)
    runner.prepare_reference(root)
    export_path = root / "datasets/runs/maestro-parity/editor-host-export/export.json"
    payload = json.loads(export_path.read_text(encoding="utf-8"))
    database = tmp_path / "queue/jobs.db"
    job_id = enqueue_export(payload, export_path, database)

    queue = JobQueue(database)
    try:
        pending = queue.list_state("pending")
        record = queue.get(job_id)
    finally:
        queue.close()
    assert pending == [job_id]
    assert record.plan_ref == str(export_path)
    assert len(record.clips) == 1
    assert record.clips[0]["kind"] == "editor_export"
    assert record.clips[0]["status"] == "planned"
    assert record.clips[0]["gpu_work"] is False
    assert record.clips[0]["host_contact"] is False
    assert record.clips[0]["media_generated"] is False


def test_input_transfer_uses_valid_scp_options(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _temporary_repository(tmp_path)
    runner.prepare_reference(root)
    bundle = tmp_path / "host-run"
    bundle.mkdir()
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    calls = tmp_path / "scp-calls.log"
    (fake_bin / "scp").write_text(
        '#!/bin/sh\nprintf "%s\\n" "$*" >> ' + str(calls) + '\n',
        encoding="utf-8",
    )
    (fake_bin / "scp").chmod(0o755)
    monkeypatch.setenv("PATH", f"{fake_bin}:{os.environ['PATH']}")

    runner._transfer_inputs(root, bundle, runner.REMOTE_ROOT / "workspace")

    transfer_logs = sorted(bundle.glob("transfer-*.log"))
    commands = [
        json.loads(log.read_text(encoding="utf-8").splitlines()[0].removeprefix("command="))
        for log in transfer_logs
    ]
    assert len(calls.read_text(encoding="utf-8").splitlines()) == 4
    assert len(commands) == 4
    assert {command[0] for command in commands} == {"scp"}
    assert all(command[1:4] == ["-o", "BatchMode=yes", "-o"] for command in commands)


def test_authorization_rejects_template_partial_tampered_and_mismatches() -> None:
    template = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    template["status"] = "not_authorized"
    template["authorization"]["record"] = None
    assert template["host"] == "3090"
    assert template["jobs"] == [{"kind": "editor_export", "count": 1}]
    assert template["execution"] == {"gpu_work": False, "model_downloads": 0}

    absent = _rejection({})
    assert absent.code == "EDITOR_HOST_AUTHORIZATION_ABSENT"
    not_authorized = _rejection(template)
    assert not_authorized.code == "EDITOR_HOST_AUTHORIZATION_NOT_AUTHORIZED"

    partial = copy.deepcopy(template)
    partial["status"] = "authorized"
    assert _rejection(partial).code == "EDITOR_HOST_AUTHORIZATION_PARTIAL"

    tampered = _authorization()
    tampered["extra"] = True
    assert _rejection(tampered).code == "EDITOR_HOST_AUTHORIZATION_TAMPERED"

    host = _authorization()
    host["host"] = "other-host"
    assert _rejection(host).code == "EDITOR_HOST_AUTHORIZATION_HOST_MISMATCH"

    source = _authorization()
    source["sources"]["video-cut"]["sha256"] = "0" * 64
    assert _rejection(source).code == "EDITOR_HOST_AUTHORIZATION_SOURCE_MISMATCH"

    project = _authorization()
    project["project"]["identity_sha256"] = "0" * 64
    assert _rejection(project).code == "EDITOR_HOST_AUTHORIZATION_PROJECT_MISMATCH"
    assert runner.verify_authorization(_authorization()) is None


def test_workspace_source_mismatch_is_typed_before_editor_load(tmp_path: Path) -> None:
    root = _temporary_repository(tmp_path)
    project_path = runner.prepare_reference(root)
    copied = project_path.parent / "sources/voice.wav"
    copied.write_bytes(copied.read_bytes() + b"tamper")
    with pytest.raises(runner.EditorHostExportError) as raised:
        runner.verify_reference(root)
    assert raised.value.code == "EDITOR_HOST_SOURCE_MISMATCH"


def test_cli_has_no_external_boundary_contact_without_or_with_representation(tmp_path: Path) -> None:
    root = _temporary_repository(tmp_path)
    runner.prepare_reference(root)
    environment, calls = _boundary_environment(tmp_path)
    no_authorization = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root)],
        cwd=ROOT,
        env=environment,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )
    assert no_authorization.returncode == 3
    rejection = json.loads(no_authorization.stdout)
    assert rejection["diagnostics"][0]["code"] == "EDITOR_HOST_AUTHORIZATION_ABSENT"
    assert rejection["ssh_contact"] is False
    assert rejection["workspace_transfer"] is False
    assert calls.read_text(encoding="utf-8") == ""

    authorization_path = tmp_path / "authorized.json"
    authorization_path.write_text(json.dumps(_authorization()), encoding="utf-8")
    represented = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--root",
            str(root),
            "--authorization",
            str(authorization_path),
            "--show-authorized-command",
        ],
        cwd=ROOT,
        env=environment,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )
    assert represented.returncode == 0
    command = json.loads(represented.stdout)
    assert command["argv"][0] == "ssh"
    assert "-n" not in command["argv"]
    assert command["argv"][5] == "3090"
    assert command["argv"][6] == "/bin/sh"
    assert command["argv"][7] == "/tmp/wd-qthq-editor-export-contract-ffmpeg.sh"
    assert command["ffmpeg_argv"][0] == "ffmpeg"
    assert command["ffmpeg_argv"][1:3] == ["-nostdin", "-y"]
    assert command["executed"] is False
    assert command["gpu_work"] is False
    assert command["model_downloads"] == 0
    assert calls.read_text(encoding="utf-8") == ""


def test_authorized_runner_represents_argv_but_never_executes() -> None:
    command = runner.authorized_command(_authorization())
    assert isinstance(command.argv, tuple)
    assert command.argv[0] == "ssh"
    assert "-n" not in command.argv
    assert command.argv[5] == "3090"
    assert command.argv[6] == "/bin/sh"
    assert command.argv[7] == "/tmp/wd-qthq-editor-export-contract-ffmpeg.sh"
    assert command.ffmpeg_argv[0] == "ffmpeg"
    assert "-filter_complex" in command.ffmpeg_argv
    assert "-c:v" in command.ffmpeg_argv
    assert command.ffmpeg_argv[command.ffmpeg_argv.index("-c:v") + 1] == "libx264"
    assert command.gpu_work is False
    assert command.model_downloads == 0
    with pytest.raises(runner.EditorHostExportError) as raised:
        runner.run_authorized_host_export(_authorization())
    assert raised.value.code == "EDITOR_HOST_EXECUTION_NOT_IMPLEMENTED"


def test_execution_guard_fails_closed_before_host_contact(tmp_path: Path) -> None:
    root = _temporary_repository(tmp_path)
    runner.prepare_reference(root)
    bundle = root / runner.REFERENCE_RELATIVE / "host-run"
    bundle.mkdir(parents=True)
    (bundle / "prior-attempt").write_text("fail closed", encoding="utf-8")
    environment, calls = _boundary_environment(tmp_path)
    with pytest.raises(runner.EditorHostExportError) as raised:
        runner.execute_authorized_host_export(root, _authorization())
    assert raised.value.code == "EDITOR_HOST_RUN_ALREADY_PRESENT"
    assert calls.read_text(encoding="utf-8") == ""


def test_execution_can_continue_only_the_exact_successful_preflight_boundary(tmp_path: Path) -> None:
    bundle = tmp_path / "host-run"
    script = bundle / "staged-scripts/preflight.sh"
    script.parent.mkdir(parents=True)
    script.write_text("set -eu\n", encoding="utf-8")
    workspace = runner.REMOTE_ROOT / "20260929T195201Z" / "cc0280f0"
    identity = {
        "name": "preflight",
        "local_path": "staged-scripts/preflight.sh",
        "remote_path": "/tmp/wd-qthq-editor-export-20260929T195201Z-3c1a4bfd-preflight.sh",
        "sha256": _hash(script),
        "byte_size": script.stat().st_size,
    }
    (bundle / "staged-scripts/preflight.json").write_text(
        json.dumps(identity), encoding="utf-8"
    )
    (bundle / "stage-preflight.log").write_text("exit=0\n", encoding="utf-8")
    (bundle / "execute-preflight.log").write_text(
        "command=[]\n"
        "stdout:\n"
        "host=straughter-Z690-Steel-Legend\n"
        "user=straughter\n"
        f"workspace={workspace}\n"
        "ffmpeg=/usr/bin/ffmpeg\n"
        "ffprobe=/usr/bin/ffprobe\n"
        f"free_bytes={runner.MINIMUM_FREE_BYTES}\n"
        "stderr:\n"
        "exit=0\n",
        encoding="utf-8",
    )

    resumed = runner._resume_successful_preflight(bundle)
    assert resumed is not None
    resumed_workspace, host, token, staged_scripts = resumed
    assert resumed_workspace == workspace
    assert host["free_bytes"] == runner.MINIMUM_FREE_BYTES
    assert token == "20260929T195201Z-3c1a4bfd"
    assert staged_scripts == [identity]

    (bundle / "unexpected-file").write_text("partial evidence", encoding="utf-8")
    assert runner._resume_successful_preflight(bundle) is None


def test_recorded_real_host_replay_passes_canonical_checker() -> None:
    bundle = ROOT / "datasets/runs/maestro-parity/editor-host-export/host-run"
    summary = json.loads((bundle / "run-summary.json").read_text(encoding="utf-8"))
    evidence = json.loads((bundle / "evidence.json").read_text(encoding="utf-8"))
    output = bundle / "outputs/editor-export.mp4"

    assert summary["repository_commit"] == "4f854dd1b938f145dcbd5eef907f6348ee12657a"
    assert summary["host"]["host"] == "straughter-Z690-Steel-Legend"
    assert summary["gpu_work"] is False and summary["model_downloads"] == 0
    assert summary["before_hashes"] == summary["after_hashes"]
    assert summary["queue"]["final_state"] == "done"
    assert summary["queue"]["retry_id"] == "attempt-1"
    assert summary["queue"]["clips"][0]["kind"] == "editor_export"
    assert summary["queue"]["clips"][0]["render_attempted"] is True
    assert summary["command"][0] == "ssh" and "-n" not in summary["command"]
    assert summary["command"][6] == "/bin/sh"
    assert Path(summary["command"][7]).is_absolute()
    assert output.stat().st_size == summary["output"]["byte_size"]
    assert _hash(output) == summary["output"]["sha256"] == evidence["output"][0]["sha256"]
    for staged in summary["staged_scripts"]:
        assert staged["sha256"] == _hash(bundle / str(staged["local_path"]))

    queue = JobQueue(bundle / "queue/jobs.db")
    try:
        record = queue.get(summary["queue"]["job_id"])
    finally:
        queue.close()
    assert record.state == "done"
    assert record.clips == summary["queue"]["clips"]

    gates = {gate["name"]: gate for gate in evidence["objective_gate_results"]}
    assert gates["duration_seconds"]["measured"] == 4.0
    assert gates["first_half_source_order_ssim"]["measured"] >= 0.98
    assert gates["second_half_clone_order_ssim"]["measured"] >= 0.98
    assert gates["declared_audio_head_correlation"]["measured"] >= 0.99
    assert gates["audio_padding_tail_rmse"]["measured"] <= 0.01

    report = verify_bundle(bundle)
    assert report.passed
    assert not report.diagnostics
    assert not report.warnings
