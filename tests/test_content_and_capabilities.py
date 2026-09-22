"""Real-process tests for the content front door and capability report."""

from __future__ import annotations

import hashlib
import json
import os
import shlex
import sqlite3
import subprocess
from pathlib import Path

from wangp.environment import describe_capabilities

import pytest


ROOT = Path(__file__).resolve().parents[1]
BRIEF = ROOT / "datasets/content_briefs/lf004-operator-dogfood-56f/brief.json"
PLATES = ROOT / "datasets/content_briefs/lf004-operator-dogfood/plates"
QUEUE = ROOT / "datasets/lf004-operator-dogfood-56f-recovery-20260921.jobs.db"
HOST_KEYS = (
    "WANGP_SSH_TARGET",
    "WANGP_WGP_ROOT",
    "WANGP_PULL_ROOT",
    "WANGP_WGP_PYTHON",
)


def _repository_digest() -> str:
    files = subprocess.run(
        ["git", "ls-files", "-z"], cwd=ROOT, check=True,
        capture_output=True, text=False,
    ).stdout.split(b"\0")
    digest = hashlib.sha256()
    for raw_name in sorted(name for name in files if name):
        name = raw_name.decode("utf-8")
        digest.update(raw_name + b"\0")
        digest.update((ROOT / name).read_bytes())
    return digest.hexdigest()


@pytest.fixture(autouse=True)
def repository_remains_byte_identical() -> None:
    before = _repository_digest()
    yield
    assert _repository_digest() == before


def _shadow_commands(
    directory: Path, calls: Path, names: tuple[str, ...]
) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for name in names:
        command = directory / name
        command.write_text(
            f'#!/bin/sh\nprintf "%s\\n" "{name} $*" >> {calls}\nexit 99\n',
            encoding="utf-8",
        )
        command.chmod(0o755)


def _environment(
    tmp_path: Path,
    *, include_nvidia_shadow: bool = True
) -> tuple[dict[str, str], Path, Path]:
    ssh_bin = tmp_path / "ssh-bin"
    nvidia_bin = tmp_path / "nvidia-bin"
    calls = tmp_path / "forbidden-calls"
    _shadow_commands(ssh_bin, calls, ("ssh",))
    _shadow_commands(nvidia_bin, calls, ("nvidia-smi",))
    calls.write_text("", encoding="utf-8")
    environment = os.environ.copy()
    prefixes = [str(ssh_bin)]
    if include_nvidia_shadow:
        prefixes.append(str(nvidia_bin))
    environment["PATH"] = ":".join([*prefixes, environment["PATH"]])
    environment["WANGP_CONFIG"] = str(tmp_path / "absent-config.toml")
    for key in HOST_KEYS:
        environment.pop(key, None)
    return environment, calls, nvidia_bin


def _wgp(
    *args: str, cwd: Path, env: dict[str, str]
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "uv", "run", "--frozen", "--extra", "dev", "wgp", *args
        ],
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        timeout=180,
        check=False,
    )


def test_content_prints_no_gpu_plan_human_and_stable_json(
    tmp_path: Path,
) -> None:
    environment, calls, _ = _environment(tmp_path)
    output = tmp_path / "plans" / "plan.json"
    human = _wgp(
        "content", "--brief", str(BRIEF), "--plates", str(PLATES),
        "--out", str(output), cwd=ROOT, env=environment,
    )
    assert human.returncode == 0, human.stdout + human.stderr
    assert "would_generate clip_count=4 speakers=Tess,Rho" in human.stdout
    assert "planned_duration_s=9.332" in human.stdout
    assert "host_requirement=unconfigured" in human.stdout
    assert "gpu_work=false" in human.stdout
    assert "queue_submitted=false" in human.stdout
    assert output.is_file()

    machine = _wgp(
        "content", "--brief", str(BRIEF), "--plates", str(PLATES),
        "--out", str(output), "--json", cwd=ROOT, env=environment,
    )
    assert machine.returncode == 0, machine.stdout + machine.stderr
    payload = json.loads(machine.stdout)
    assert payload["schema_version"] == "wangp-dspy.content-request/v1"
    assert payload["what_will_be_generated"] == {
        "clip_count": 4,
        "speakers": ["Tess", "Rho", "Tess", "Rho"],
        "planned_duration_s": 9.332,
    }
    assert payload["summary"]["gpu_work"] is False
    assert payload["summary"]["queue_submitted"] is False
    assert payload["governed_queue_command"] is None
    assert payload["host_requirement"]["contacted"] is False
    assert "/Users/" not in machine.stdout
    assert "configured-host" not in machine.stdout
    assert calls.read_text(encoding="utf-8") == ""


def test_content_submit_without_out_keeps_every_printed_path(
    tmp_path: Path,
) -> None:
    environment, calls, _ = _environment(tmp_path)
    environment.update({
        "WANGP_SSH_TARGET": "configured-host",
        "WANGP_WGP_ROOT": "/remote/Wan2GP",
        "WANGP_PULL_ROOT": "/local/pull",
        "WANGP_WGP_PYTHON": "/remote/python",
    })
    result = _wgp(
        "content", "--brief", str(BRIEF), "--plates", str(PLATES),
        "--submit", cwd=ROOT, env=environment,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    command = next(
        line.removeprefix("governed_queue_command=")
        for line in result.stdout.splitlines()
        if line.startswith("governed_queue_command=")
    )
    tail = command.split("--db ", 1)[1]
    database = Path(shlex.split(tail)[0])
    assert database.is_file()
    connection = sqlite3.connect(database)
    rows = connection.execute(
        "SELECT job_id, state, clips FROM jobs ORDER BY rowid"
    ).fetchall()
    connection.close()
    assert [row[1] for row in rows] == ["pending"] * 4
    needs = [json.loads(row[2])[0]["needs"] for row in rows]
    assert needs[0] is None
    assert needs[1:] == [row[0] for row in rows[:-1]]
    assert calls.read_text(encoding="utf-8") == ""


def test_content_submit_fails_closed_then_prints_only_with_host(
    tmp_path: Path,
) -> None:
    environment, calls, _ = _environment(tmp_path)
    output = tmp_path / "plan.json"
    unconfigured = _wgp(
        "content", "--brief", str(BRIEF), "--plates", str(PLATES),
        "--out", str(output), "--submit", cwd=ROOT, env=environment,
    )
    combined = unconfigured.stdout + unconfigured.stderr
    assert unconfigured.returncode == 3
    assert unconfigured.stdout == ""
    assert combined.count("diagnostic code=") == 1
    assert "missing host keys: host.target, host.wgp_root, host.wgp_python" in combined
    assert "WANGP_SSH_TARGET, WANGP_WGP_ROOT, WANGP_WGP_PYTHON" in combined
    assert "next: wgp doctor --capabilities" in combined
    assert not output.exists()
    assert calls.read_text(encoding="utf-8") == ""

    environment.update({
        "WANGP_SSH_TARGET": "configured-host",
        "WANGP_WGP_ROOT": "/remote/Wan2GP",
        "WANGP_PULL_ROOT": "/local/pull",
        "WANGP_WGP_PYTHON": "/remote/python",
    })
    configured = _wgp(
        "content", "--brief", str(BRIEF), "--plates", str(PLATES),
        "--out", str(output), "--submit", cwd=ROOT, env=environment,
    )
    assert configured.returncode == 0, configured.stdout + configured.stderr
    run_database = output.parent / "run" / "jobs.db"
    assert run_database.is_file()
    expected = shlex.join([
        "uv", "run", "--frozen", "--extra", "dev", "python",
        "-m", "scripts.run_jobs", "--db", str(run_database),
    ])
    assert f"governed_queue_command={expected}" in configured.stdout
    assert "queue_submitted=true" in configured.stdout
    assert "submission=queued; queue worker not executed" in configured.stdout
    connection = sqlite3.connect(run_database)
    assert connection.execute("SELECT count(*) FROM jobs").fetchone()[0] == 4
    connection.close()
    assert calls.read_text(encoding="utf-8") == ""


def test_invalid_brief_and_plates_are_typed_and_write_no_plan(
    tmp_path: Path,
) -> None:
    environment, calls, _ = _environment(tmp_path)
    payload = json.loads(BRIEF.read_text(encoding="utf-8"))
    payload["dialogue"][0]["speaker"] = "NotInRoster"
    invalid = tmp_path / "invalid-brief.json"
    invalid.write_text(json.dumps(payload), encoding="utf-8")
    output = tmp_path / "plan.json"
    result = _wgp(
        "content", "--brief", str(invalid), "--plates", str(PLATES),
        "--out", str(output), cwd=ROOT, env=environment,
    )
    assert result.returncode == 2
    assert result.stdout == ""
    assert "diagnostic code=INPUT_INVALID" in result.stderr
    assert "dialogue[0].speaker" in result.stderr
    assert "remediation:" in result.stderr
    assert "next: wgp content --brief <brief>" in result.stderr
    assert not output.exists()
    assert not (tmp_path / "run").exists()
    assert calls.read_text(encoding="utf-8") == ""

    machine = _wgp(
        "content", "--brief", str(invalid), "--plates", str(PLATES),
        "--out", str(output), "--json", cwd=ROOT, env=environment,
    )
    assert machine.returncode == 2
    diagnostic = json.loads(machine.stdout)["diagnostics"][0]
    assert diagnostic["code"] == "INPUT_INVALID"
    assert "/Users/" not in machine.stdout
    assert str(tmp_path) not in machine.stdout

    rejected = _wgp(
        "content", "--brief", str(BRIEF), "--plates",
        str(tmp_path / "missing-plates"), "--out", str(output),
        cwd=ROOT, env=environment,
    )
    assert rejected.returncode == 2
    assert "plates directory does not exist: <plates>" in rejected.stderr
    assert not output.exists()
    assert calls.read_text(encoding="utf-8") == ""


@pytest.mark.parametrize(
    "forged_text", ["Two\nRho: forged turn", "Two\nunlabelled continuation"]
)
def test_embedded_dialogue_newline_is_rejected_before_artifacts(
    tmp_path: Path, forged_text: str
) -> None:
    environment, calls, _ = _environment(tmp_path)
    payload = json.loads(BRIEF.read_text(encoding="utf-8"))
    payload["dialogue"][0]["text"] = forged_text
    brief = tmp_path / "multiline-brief.json"
    brief.write_text(json.dumps(payload), encoding="utf-8")
    output = tmp_path / "plan.json"
    run_dir = tmp_path / "run"
    result = _wgp(
        "content", "--brief", str(brief), "--plates", str(PLATES),
        "--out", str(output), "--run-dir", str(run_dir),
        cwd=ROOT, env=environment,
    )
    assert result.returncode == 2
    assert "dialogue[0].text contains a control character" in result.stderr
    assert "remediation:" in result.stderr
    assert not output.exists()
    assert not run_dir.exists()
    assert calls.read_text(encoding="utf-8") == ""


def test_capability_report_is_read_only_and_honest(tmp_path: Path) -> None:
    environment, calls, nvidia_bin = _environment(
        tmp_path, include_nvidia_shadow=False
    )
    environment["PATH"] = environment["PATH"].replace(
        f":{nvidia_bin}", "", 1
    )
    human = _wgp("doctor", "--capabilities", cwd=ROOT, env=environment)
    assert human.returncode == 0, human.stdout + human.stderr
    assert "local_accelerator=no local accelerator" in human.stdout
    assert "model_manifest=absent" in human.stdout
    assert "not_implemented=image generation; music generation; speech/voice cloning; sound effects; upscaling; face refinement; video editing; GUI" in human.stdout
    assert "host_contact=false" in human.stdout

    machine = _wgp(
        "doctor", "--capabilities", "--json", cwd=ROOT, env=environment
    )
    assert machine.returncode == 0, machine.stdout + machine.stderr
    payload = json.loads(machine.stdout)
    assert payload["local_accelerator"]["visible"] is False
    assert payload["local_accelerator"]["detail"] == (
        "no local accelerator (nvidia-smi not found on PATH)"
    )
    assert payload["model_manifest"]["status"] == "absent"
    assert payload["generation_capabilities"]["not_implemented"] == [
        "image generation", "music generation", "speech/voice cloning",
        "sound effects", "upscaling", "face refinement", "video editing",
        "GUI",
    ]
    assert payload["collection"] == {
        "read_only": True,
        "network_access": False,
        "host_contact": False,
    }
    assert "/Users/" not in machine.stdout
    assert calls.read_text(encoding="utf-8") == ""


def test_capabilities_cannot_silently_skip_requested_doctor_work(
    tmp_path: Path,
) -> None:
    environment, calls, _ = _environment(tmp_path)
    combined = _wgp(
        "doctor", "--capabilities", "--db", str(QUEUE),
        "--json", cwd=ROOT, env=environment,
    )
    assert combined.returncode == 2
    payload = json.loads(combined.stdout)
    assert payload["diagnostics"][0]["code"] == "INPUT_INVALID"
    assert "--capabilities is a standalone local report" in combined.stdout

    probe = _wgp(
        "doctor", "--capabilities", "--probe-host",
        cwd=ROOT, env=environment,
    )
    assert probe.returncode == 2
    assert "--capabilities is a standalone local report" in probe.stderr
    assert "ssh_reachable" not in probe.stdout + probe.stderr
    assert calls.read_text(encoding="utf-8") == ""


def test_capability_report_verifies_each_manifest_entry(
    tmp_path: Path,
) -> None:
    environment, calls, _ = _environment(tmp_path)
    model = tmp_path / "model.bin"
    model.write_bytes(b"exact model bytes")
    missing = tmp_path / "missing.bin"
    mismatched = tmp_path / "mismatched.bin"
    mismatched.write_bytes(b"wrong model bytes")
    unreadable = tmp_path / "unreadable.bin"
    unreadable.write_bytes(b"cannot read these bytes")
    unreadable.chmod(0)
    manifest = tmp_path / "models.json"
    manifest.write_text(json.dumps([
        {"local_path": str(model), "sha256": hashlib.sha256(model.read_bytes()).hexdigest()},
        {"local_path": str(missing), "sha256": "0" * 64},
        {"local_path": str(mismatched), "sha256": "2" * 64},
        {"local_path": str(unreadable), "sha256": "3" * 64},
        {"remote_path": "remote/model.bin", "sha256": "1" * 64},
    ]), encoding="utf-8")
    try:
        result = _wgp(
            "doctor", "--capabilities", "--models", str(manifest),
            "--json", cwd=ROOT, env=environment,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        payload = json.loads(result.stdout)
        assert [(item["status"], item["download_required"])
                for item in payload["model_manifest"]["entries"]] == [
            ("verified", False), ("missing", True),
            ("hash_mismatch", True), ("unreadable", True),
            ("remote_declared", True),
        ]
        assert all(
            item["wangp_downloads"] is False
            for item in payload["model_manifest"]["entries"]
        )
    finally:
        unreadable.chmod(0o644)
    assert calls.read_text(encoding="utf-8") == ""


@pytest.mark.parametrize("payload", [[], [{}]])
def test_invalid_or_empty_manifests_are_configuration_failures(
    tmp_path: Path, payload: list[object]
) -> None:
    environment, calls, _ = _environment(tmp_path)
    manifest = tmp_path / "models.json"
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    result = _wgp(
        "doctor", "--capabilities", "--models", str(manifest),
        "--json", cwd=ROOT, env=environment,
    )
    assert result.returncode == 2
    diagnostic = json.loads(result.stdout)["diagnostics"][0]
    assert diagnostic["code"] == "INPUT_INVALID"
    assert "sha256" in diagnostic["observed"] or "manifest" in diagnostic["observed"]

    discovered_root = tmp_path / "discovered"
    discovered_root.mkdir()
    (discovered_root / "models.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )
    report = describe_capabilities(
        discovered_root,
        environ={"WANGP_CONFIG": str(tmp_path / "absent.toml")},
    ).mapping()
    assert report["model_manifest"]["status"] == "invalid"
    assert report["model_manifest"]["entries"] == []
    assert calls.read_text(encoding="utf-8") == ""


def test_discovery_supports_legacy_local_path_alias(
    tmp_path: Path,
) -> None:
    model = tmp_path / "legacy-model.bin"
    model.write_bytes(b"legacy local bytes")
    root = tmp_path / "repository"
    root.mkdir()
    (root / "models.json").write_text(json.dumps([{
        "path": str(model),
        "sha256": hashlib.sha256(model.read_bytes()).hexdigest(),
    }]), encoding="utf-8")
    report = describe_capabilities(
        root, environ={"WANGP_CONFIG": str(tmp_path / "absent.toml")}
    ).mapping()
    assert report["model_manifest"]["status"] == "present"
    assert report["model_manifest"]["entries"] == [{
        "id": "entry-1",
        "status": "verified",
        "download_required": False,
        "wangp_downloads": False,
    }]
