"""Real-process tests for the content front door and capability report."""

from __future__ import annotations

import hashlib
import json
import os
import shlex
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
BRIEF = ROOT / "datasets/content_briefs/lf004-operator-dogfood-56f/brief.json"
PLATES = ROOT / "datasets/content_briefs/lf004-operator-dogfood/plates"
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
    assert payload["governed_queue_command"] == shlex.join([
        "uv", "run", "--frozen", "--extra", "dev", "python",
        "-m", "scripts.run_jobs", "--db", "<run-dir>/jobs.db",
    ])
    assert payload["host_requirement"]["contacted"] is False
    assert "/Users/" not in machine.stdout
    assert "configured-host" not in machine.stdout
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
    expected = shlex.join([
        "uv", "run", "--frozen", "--extra", "dev", "python",
        "-m", "scripts.run_jobs", "--db", str(run_database),
    ])
    assert f"governed_queue_command={expected}" in configured.stdout
    assert "queue_submitted=false" in configured.stdout
    assert "submission=preview_only" in configured.stdout
    assert not run_database.exists()
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


def test_capability_report_verifies_each_manifest_entry(
    tmp_path: Path,
) -> None:
    environment, calls, _ = _environment(tmp_path)
    model = tmp_path / "model.bin"
    model.write_bytes(b"exact model bytes")
    missing = tmp_path / "missing.bin"
    manifest = tmp_path / "models.json"
    manifest.write_text(json.dumps([
        {"local_path": str(model), "sha256": hashlib.sha256(model.read_bytes()).hexdigest()},
        {"local_path": str(missing), "sha256": "0" * 64},
        {"remote_path": "remote/model.bin", "sha256": "1" * 64},
    ]), encoding="utf-8")
    result = _wgp(
        "doctor", "--capabilities", "--models", str(manifest),
        "--json", cwd=ROOT, env=environment,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert [(item["status"], item["download_required"])
            for item in payload["model_manifest"]["entries"]] == [
        ("verified", False), ("missing", True), ("remote_declared", True),
    ]
    assert all(item["wangp_downloads"] is False for item in payload["model_manifest"]["entries"])
    assert calls.read_text(encoding="utf-8") == ""
