"""Real-process, no-GPU coverage for the WD-4d90 first-run platform."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
HOST_KEYS = (
    "WANGP_SSH_TARGET",
    "WANGP_WGP_ROOT",
    "WANGP_PULL_ROOT",
    "WANGP_WGP_PYTHON",
)
NETWORK_COMMANDS = ("ssh", "curl", "wget")


def _repository_digest() -> str:
    files = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=False,
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


def _environment(
    tmp_path: Path,
    *,
    accelerator_tool: str = "absent",
) -> tuple[dict[str, str], Path]:
    forbidden = tmp_path / "forbidden-bin"
    forbidden.mkdir()
    calls = tmp_path / "forbidden-calls"
    calls.write_text("", encoding="utf-8")
    for name in NETWORK_COMMANDS:
        command = forbidden / name
        command.write_text(
            f'#!/bin/sh\nprintf "%s\\n" "{name} $*" >> {calls}\nexit 99\n',
            encoding="utf-8",
        )
        command.chmod(0o755)
    nvidia_bin = tmp_path / "nvidia-bin"
    nvidia_bin.mkdir()
    if accelerator_tool != "absent":
        nvidia = nvidia_bin / "nvidia-smi"
        if accelerator_tool == "valid":
            nvidia.write_text(
                "#!/bin/sh\n"
                f"printf '%s\\n' 'nvidia-smi $*' >> {calls}\n"
                "printf '0, \"Synthetic CUDA GPU\", 24576 MiB\\n'\n",
                encoding="utf-8",
            )
        else:
            nvidia.write_text(
                "#!/bin/sh\n"
                f"printf '%s\\n' 'nvidia-smi $*' >> {calls}\n"
                "printf 'synthetic tool made no device claim\\n'\n"
                "exit 99\n",
                encoding="utf-8",
            )
        nvidia.chmod(0o755)
    environment = os.environ.copy()
    prefixes = [str(forbidden)]
    if accelerator_tool != "absent":
        prefixes.append(str(nvidia_bin))
    prefixes.append(str(Path(shutil.which("uv")).parent))
    environment["PATH"] = ":".join(prefixes)
    environment["WANGP_CONFIG"] = str(tmp_path / "absent-wangp.toml")
    for key in HOST_KEYS:
        environment.pop(key, None)
    environment.pop("WANGP_LLM_API_KEY", None)
    return environment, calls


def _assert_no_network_calls(calls: Path) -> None:
    recorded = calls.read_text(encoding="utf-8").splitlines()
    assert not [
        line for line in recorded
        if line.startswith(("ssh ", "curl ", "wget "))
    ]


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


def _inventory(
    path: Path,
    *,
    accelerators: list[dict[str, object]],
) -> Path:
    payload = {
        "schema_version": "wangp-dspy.platform-inventory/v1",
        "platform": {
            "system": "Darwin",
            "release": "24.0.0",
            "machine": "arm64",
            "processor": None,
        },
        "cpu": {"logical_cores": 10, "physical_cores": 10, "name": None},
        "memory": {"total_bytes": 68_719_476_736, "available_bytes": None},
        "disk": {
            "root": "/",
            "total_bytes": 994_662_589_440,
            "free_bytes": 107_374_182_400,
        },
        "accelerators": accelerators,
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_profile_reports_no_accelerator_and_real_local_collection(
    tmp_path: Path,
) -> None:
    environment, calls = _environment(
        tmp_path, accelerator_tool="unparseable"
    )
    inventory = _inventory(tmp_path / "inventory.json", accelerators=[])

    human = _wgp(
        "first-run", "profile", "--inventory", str(inventory),
        cwd=ROOT, env=environment,
    )
    assert human.returncode == 0, human.stdout + human.stderr
    assert "platform=Darwin arm64" in human.stdout
    assert "accelerators=0" in human.stdout
    assert "vram_bytes=unknown" in human.stdout
    assert "profile=planning-only-external-render" in human.stdout
    assert "profile_status=advisory-unverified" in human.stdout
    assert "gpu_work=false host_contact=false verified_generation=false" in human.stdout

    machine = _wgp(
        "first-run", "profile", "--inventory", str(inventory), "--json",
        cwd=ROOT, env=environment,
    )
    assert machine.returncode == 0, machine.stdout + machine.stderr
    payload = json.loads(machine.stdout)
    assert payload["accelerators"] == []
    assert payload["recommendation"]["profile"] == (
        "planning-only-external-render"
    )
    assert payload["recommendation"]["reasons"] == [
        "no local accelerator was reported"
    ]
    assert payload["unknowns"] == [
        "cpu name unavailable from the local standard library",
        "memory availability was not inferred",
        "accelerator VRAM unavailable without executing hardware tools",
    ]
    assert payload["collection"] == {
        "read_only": True,
        "network_access": False,
        "host_contact": False,
        "gpu_work": False,
        "verified_generation": False,
    }

    actual = _wgp(
        "first-run", "profile", "--json", cwd=ROOT, env=environment
    )
    assert actual.returncode == 0, actual.stdout + actual.stderr
    local = json.loads(actual.stdout)
    assert local["schema_version"] == "wangp-dspy.platform-profile/v1"
    assert local["accelerators"] == []
    assert local["accelerator_absence_reasons"] == [
        "nvidia-smi probe failed with exit 99; no accelerator inferred"
    ]
    assert local["disk"]["free_bytes"] > 0
    assert local["collection"]["read_only"] is True
    _assert_no_network_calls(calls)


def test_accelerator_is_absent_when_probe_tool_is_absent(
    tmp_path: Path,
) -> None:
    environment, calls = _environment(tmp_path, accelerator_tool="absent")
    result = _wgp(
        "first-run", "profile", "--json", cwd=ROOT, env=environment
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["accelerators"] == []
    assert payload["accelerator_absence_reasons"] == [
        "nvidia-smi absent from PATH; no probe attempted"
    ]
    assert calls.read_text(encoding="utf-8") == ""


def test_shadowed_accelerator_tool_without_device_output_is_absent(
    tmp_path: Path,
) -> None:
    environment, calls = _environment(
        tmp_path, accelerator_tool="unparseable"
    )
    result = _wgp(
        "first-run", "profile", "--json", cwd=ROOT, env=environment
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["accelerators"] == []
    assert payload["accelerator_absence_reasons"] == [
        "nvidia-smi probe failed with exit 99; no accelerator inferred"
    ]
    recorded = calls.read_text(encoding="utf-8").splitlines()
    assert len(recorded) == 1
    assert recorded[0].startswith("nvidia-smi ")
    assert not [
        line for line in recorded
        if line.startswith(("ssh ", "curl ", "wget "))
    ]


def test_parsed_device_output_reports_one_tool_attributed_accelerator(
    tmp_path: Path,
) -> None:
    environment, calls = _environment(tmp_path, accelerator_tool="valid")
    result = _wgp(
        "first-run", "profile", "--json", cwd=ROOT, env=environment
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["accelerators"] == [{
        "kind": "cuda",
        "name": "Synthetic CUDA GPU",
        "vram_bytes": 25_769_803_776,
        "detection": "reported by nvidia-smi",
    }]
    assert payload["accelerator_absence_reasons"] == []
    recorded = calls.read_text(encoding="utf-8").splitlines()
    assert len(recorded) == 1
    assert recorded[0].startswith("nvidia-smi ")


def test_profile_recommendation_is_advisory_when_vram_is_visible(
    tmp_path: Path,
) -> None:
    environment, calls = _environment(tmp_path)
    inventory = _inventory(
        tmp_path / "inventory.json",
        accelerators=[{
            "kind": "cuda",
            "name": "recorded accelerator",
            "vram_bytes": 25_769_803_776,
            "detection": "operator-recorded inventory",
        }],
    )
    result = _wgp(
        "first-run", "profile", "--inventory", str(inventory), "--json",
        cwd=ROOT, env=environment,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["recommendation"]["profile"] == "local-candidate-24gb"
    assert payload["recommendation"]["reasons"] == [
        "24 GiB or more accelerator memory was reported",
        "at least 100 GiB disk headroom was reported",
    ]
    assert payload["recommendation"]["status"] == "advisory-unverified"
    assert calls.read_text(encoding="utf-8") == ""


def _asset(
    path: Path,
    payload: bytes | None,
    *,
    digest: str | None = None,
    size: int | None = None,
) -> dict[str, object]:
    destination = path.resolve()
    if payload is not None:
        destination.write_bytes(payload)
    expected = digest or (
        hashlib.sha256(payload or b"").hexdigest()
        if payload is not None
        else "0" * 64
    )
    return {
        "id": path.name,
        "source_url": f"https://example.invalid/{path.name}",
        "sha256": expected,
        "size_bytes": size if size is not None else len(payload or b""),
        "license": "operator-recorded upstream license",
        "destination": str(destination),
    }


def test_download_states_are_durable_and_never_fetch(
    tmp_path: Path,
) -> None:
    environment, calls = _environment(tmp_path)
    complete = _asset(tmp_path / "complete.bin", b"complete")
    mismatched = _asset(
        tmp_path / "mismatch.bin", b"12345678", digest="a" * 64
    )
    partial = _asset(tmp_path / "partial.bin", b"part")
    partial["size_bytes"] = 8
    absent = _asset(tmp_path / "absent.bin", None, size=8)
    manifest = tmp_path / "assets.json"
    manifest.write_text(
        json.dumps({"schema_version": "wangp-dspy.model-assets/v1", "assets": [
            complete, mismatched, partial, absent,
        ]}),
        encoding="utf-8",
    )
    state = tmp_path / "download-state.json"

    result = _wgp(
        "first-run", "download", "--manifest", str(manifest),
        "--state", str(state), "--json", cwd=ROOT, env=environment,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    by_id = {item["id"]: item for item in payload["assets"]}
    assert [(key, value["status"]) for key, value in sorted(by_id.items())] == [
        ("absent.bin", "absent"),
        ("complete.bin", "complete"),
        ("mismatch.bin", "checksum_mismatch"),
        ("partial.bin", "partial"),
    ]
    assert payload["download_plan"]["total_size_bytes"] == 24
    assert payload["download_plan"]["wangp_downloads"] is False

    paused = _wgp(
        "first-run", "download", "--manifest", str(manifest),
        "--state", str(state), "--pause", "partial.bin", "--json",
        cwd=ROOT, env=environment,
    )
    assert paused.returncode == 0, paused.stdout + paused.stderr
    assert next(
        item for item in json.loads(paused.stdout)["assets"]
        if item["id"] == "partial.bin"
    )["status"] == "paused"

    resumed = _wgp(
        "first-run", "download", "--manifest", str(manifest),
        "--state", str(state), "--resume", "partial.bin", "--json",
        cwd=ROOT, env=environment,
    )
    assert resumed.returncode == 2, resumed.stdout + resumed.stderr
    machine = json.loads(resumed.stdout)
    assert machine["diagnostics"][0]["code"] == "DOWNLOAD_REQUIRES_OPERATOR"
    assert machine["diagnostics"][0]["next_command"].startswith("curl ")
    assert machine["assets"][2]["status"] == "partial"
    assert machine["assets"][2]["resume_requested"] is True
    assert calls.read_text(encoding="utf-8") == ""


def test_download_manifest_rejects_incomplete_provenance(
    tmp_path: Path,
) -> None:
    environment, calls = _environment(tmp_path)
    manifest = tmp_path / "invalid.json"
    manifest.write_text(json.dumps({
        "schema_version": "wangp-dspy.model-assets/v1",
        "assets": [{
            "id": "unsafe",
            "source_url": "https://example.invalid/unsafe.bin",
            "sha256": "not-a-hash",
            "size_bytes": -1,
            "license": "",
            "destination": str(tmp_path / "unsafe.bin"),
        }],
    }), encoding="utf-8")
    result = _wgp(
        "first-run", "download", "--manifest", str(manifest),
        "--state", str(tmp_path / "state.json"), cwd=ROOT, env=environment,
    )
    assert result.returncode == 2
    assert "diagnostic code=PLATFORM_INPUT_INVALID" in result.stderr
    assert calls.read_text(encoding="utf-8") == ""


def _runtime_config(
    path: Path,
    *,
    local_payload: bytes | None,
) -> Path:
    local_path = path.parent / "local-model.bin"
    if local_payload is not None:
        local_path.write_bytes(local_payload)
    payload = {
        "schema_version": "wangp-dspy.llm-runtime/v1",
        "selection": "local-then-external",
        "local": {
            "model_path": str(local_path),
            "sha256": hashlib.sha256(local_payload or b"").hexdigest(),
            "runtime_command": [
                "ollama", "run", "operator-recorded-model"
            ],
        },
        "external": {
            "provider": "operator-recorded-openai-compatible",
            "base_url": "https://example.invalid/v1",
            "model": "operator-recorded-model",
            "api_key_env": "WANGP_LLM_API_KEY",
        },
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_llm_runtime_prefers_local_and_fails_closed_for_credentials(
    tmp_path: Path,
) -> None:
    environment, calls = _environment(tmp_path)
    complete = _runtime_config(
        tmp_path / "runtime.json", local_payload=b"local weights"
    )
    local = _wgp(
        "first-run", "runtime", "--config", str(complete), "--json",
        cwd=ROOT, env=environment,
    )
    assert local.returncode == 0, local.stdout + local.stderr
    payload = json.loads(local.stdout)
    assert payload["selected_runtime"] == "bundled-local"
    assert payload["ready"] is True
    assert payload["provider_contact"] is False

    missing = _runtime_config(
        tmp_path / "runtime-missing.json", local_payload=None
    )
    fallback = _wgp(
        "first-run", "runtime", "--config", str(missing), "--json",
        cwd=ROOT, env={**environment, "WANGP_LLM_API_KEY": "secret-value"},
    )
    assert fallback.returncode == 0, fallback.stdout + fallback.stderr
    payload = json.loads(fallback.stdout)
    assert payload["selected_runtime"] == "external-provider"
    assert payload["ready"] is True
    assert "secret-value" not in fallback.stdout

    denied = _wgp(
        "first-run", "runtime", "--config", str(missing), "--json",
        cwd=ROOT, env=environment,
    )
    assert denied.returncode == 2, denied.stdout + denied.stderr
    diagnostic = json.loads(denied.stdout)["diagnostics"][0]
    assert diagnostic["code"] == "LLM_CREDENTIAL_MISSING"
    assert "secret" not in json.dumps(diagnostic).lower()
    assert calls.read_text(encoding="utf-8") == ""


def test_recovery_maps_recorded_oom_without_gate_or_style_changes(
    tmp_path: Path,
) -> None:
    environment, calls = _environment(tmp_path)
    command = [
        "wgp-render", "--model", "h3", "--style", "lf004",
        "--settings", "settings.json",
    ]
    record = tmp_path / "oom.json"
    record.write_text(json.dumps({
        "schema_version": "wangp-dspy.oom-recovery/v1",
        "evidence": {
            "message": "torch.cuda.OutOfMemoryError: CUDA out of memory",
            "run_id": "run-123",
            "source": "attempt-2/stderr.json",
        },
        "render": {
            "model": "h3",
            "style_id": "lf004",
            "resolution": "768p",
            "frames": 107,
            "calibration": None,
        },
        "command": command,
    }), encoding="utf-8")

    human = _wgp(
        "first-run", "recovery", "--record", str(record),
        cwd=ROOT, env=environment,
    )
    assert human.returncode == 0, human.stdout + human.stderr
    assert "oom_detected=true" in human.stdout
    assert "strategy=bounded-calibration" in human.stdout
    assert "preserves_model=true preserves_style=true" in human.stdout
    assert "gate_mutation=false automatic_change=false" in human.stdout
    assert "next command: " + subprocess.list2cmdline(command) in human.stdout

    machine = _wgp(
        "first-run", "recovery", "--record", str(record), "--json",
        cwd=ROOT, env=environment,
    )
    assert machine.returncode == 0, machine.stdout + machine.stderr
    payload = json.loads(machine.stdout)
    assert payload["calibration"]["resolution"] == "512p"
    assert payload["calibration"]["frames"] is None
    assert payload["authorization_required"] is True

    ordinary = tmp_path / "ordinary.json"
    payload = json.loads(record.read_text(encoding="utf-8"))
    payload["evidence"]["message"] = "disk full"
    ordinary.write_text(json.dumps(payload), encoding="utf-8")
    rejected = _wgp(
        "first-run", "recovery", "--record", str(ordinary),
        cwd=ROOT, env=environment,
    )
    assert rejected.returncode == 2
    assert "diagnostic code=OOM_NOT_DETECTED" in rejected.stderr
    assert calls.read_text(encoding="utf-8") == ""


def test_remote_access_previews_but_never_contacts_ssh(
    tmp_path: Path,
) -> None:
    environment, calls = _environment(tmp_path)
    incomplete = _wgp(
        "first-run", "remote", "--json", cwd=ROOT, env=environment
    )
    assert incomplete.returncode == 3, incomplete.stdout + incomplete.stderr
    payload = json.loads(incomplete.stdout)
    assert payload["ready"] is False
    assert payload["diagnostics"][0]["code"] == "HOST_CONFIGURATION_INCOMPLETE"
    assert payload["command_preview"].startswith("ssh -o BatchMode=yes")
    assert payload["host_contact"] is False

    configured = _wgp(
        "first-run", "remote", "--json", cwd=ROOT, env={
            **environment,
            "WANGP_SSH_TARGET": "operator-host",
            "WANGP_WGP_ROOT": "/opt/wangp",
            "WANGP_PULL_ROOT": str(tmp_path / "pull"),
        }
    )
    assert configured.returncode == 0, configured.stdout + configured.stderr
    payload = json.loads(configured.stdout)
    assert payload["ready"] is True
    assert payload["command_preview"] == (
        "ssh -o BatchMode=yes operator-host true"
    )
    assert payload["host_contact"] is False
    assert calls.read_text(encoding="utf-8") == ""


def test_first_run_help_is_registered_without_replacing_doctor(
    tmp_path: Path,
) -> None:
    environment, calls = _environment(tmp_path)
    result = _wgp("--help", cwd=ROOT, env=environment)
    assert result.returncode == 0
    assert "first-run" in result.stdout
    assert "doctor" in result.stdout
    assert calls.read_text(encoding="utf-8") == ""
