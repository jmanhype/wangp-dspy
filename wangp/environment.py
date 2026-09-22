"""Honest, read-only first-run capability reporting."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

from wangp.config import ALL_HOST_KEYS, load_host_config, missing_host_keys
from wangp.diagnostics import redact_sensitive


NOT_IMPLEMENTED_CAPABILITIES = (
    "image generation",
    "music generation",
    "speech/voice cloning",
    "sound effects",
    "upscaling",
    "face refinement",
    "video editing",
    "GUI",
)
IMPLEMENTED_CAPABILITIES = (
    "no-GPU content planning",
    "host-backed rendering through the governed queue when explicitly configured",
)
_MODEL_MANIFESTS = ("models.json", "models/manifest.json")


@dataclass(frozen=True)
class CapabilityReport:
    """A stable snapshot of local facts; collection performs no host call."""

    payload: Mapping[str, Any] = field(default_factory=dict)

    def mapping(self) -> dict[str, Any]:
        return redact_sensitive(dict(self.payload))

    def render(self) -> str:
        value = self.mapping()
        tools = " ".join(
            f"{name}={'available' if item['available'] else 'missing'}"
            for name, item in sorted(value["tools"].items())
        )
        host = value["host_configuration"]
        missing_host = ", ".join(host["missing_keys"])
        host_state = (
            "complete (not contacted)" if host["complete"]
            else f"incomplete (missing {missing_host or 'none'})"
        )
        models = value["model_manifest"]
        model_states = ", ".join(
            f"{item['id']}:{item['status']}" for item in models["entries"]
        ) or "none"
        capabilities = value["generation_capabilities"]
        return "\n".join([
            f"platform={value['platform']['system']} {value['platform']['machine']}",
            f"python={value['python']['implementation']} {value['python']['version']}",
            tools,
            f"local_accelerator={value['local_accelerator']['detail']}",
            f"ram_available_bytes={value['resources']['ram_available_bytes']}",
            f"disk_free_bytes={value['resources']['disk_free_bytes']}",
            f"host_configuration={host_state}",
            (
                f"model_manifest={models['status']} "
                f"entries={model_states}"
            ),
            "implemented=" + "; ".join(capabilities["implemented"]),
            "not_implemented=" + "; ".join(capabilities["not_implemented"]),
            "collection=read_only network_access=false host_contact=false",
        ])


def _tool(name: str) -> dict[str, object]:
    return {"available": shutil.which(name) is not None}


def _accelerator() -> dict[str, object]:
    visible = shutil.which("nvidia-smi") is not None
    detail = (
        "nvidia-smi visible on PATH; presence check only, GPU was not called"
        if visible
        else "no local accelerator (nvidia-smi not found on PATH)"
    )
    return {"visible": visible, "detail": detail}


def _resources(repository_root: Path) -> dict[str, object]:
    total: int | None = None
    available: int | None = None
    try:
        total = os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")
    except (AttributeError, OSError, ValueError):
        total = None
    if platform.system() == "Linux":
        try:
            values = {
                line.split(":", 1)[0]: int(line.split(":", 1)[1].strip()[:-3])
                * 1024
                for line in Path("/proc/meminfo").read_text().splitlines()
                if line.startswith(("MemTotal:", "MemAvailable:"))
            }
            total, available = values["MemTotal:"], values["MemAvailable:"]
        except (OSError, ValueError, KeyError, IndexError):
            pass
    elif platform.system() == "Darwin" and total is not None:
        try:
            completed = subprocess.run(
                ["vm_stat"], capture_output=True, text=True, timeout=3, check=False
            )
            page_size = os.sysconf("SC_PAGE_SIZE")
            pages = 0
            wanted = ("Pages free", "Pages inactive", "Pages purgeable")
            for line in completed.stdout.splitlines():
                key = line.split(":", 1)[0]
                if key in wanted:
                    pages += int(line.rsplit(" ", 1)[-1].rstrip("."))
            available = pages * page_size
        except (OSError, subprocess.SubprocessError, ValueError):
            available = None
    usage = shutil.disk_usage(repository_root)
    return {
        "ram_total_bytes": total,
        "ram_available_bytes": available,
        "disk_total_bytes": usage.total,
        "disk_free_bytes": usage.free,
    }


def _host_state(repository_root: Path, environ: Mapping[str, str]) -> dict[str, object]:
    config = load_host_config(
        repository_root=repository_root, environ=environ
    )
    resolved = []
    for key, setting in zip(ALL_HOST_KEYS, config.settings(), strict=True):
        resolved.append({
            "key": key,
            "configured": setting is not None,
            "source": setting.source if setting is not None else "unconfigured",
        })
    missing = missing_host_keys(config)
    if config.wgp_python is None and "host.wgp_python" not in missing:
        missing += ("host.wgp_python",)
    return {
        "complete": not missing,
        "missing_keys": list(missing),
        "resolved": resolved,
        "contacted": False,
    }


def _hash_file(path: Path) -> str | None:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as payload:
            for chunk in iter(lambda: payload.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError:
        return None
    return digest.hexdigest()


def _normalized_models(
    payload: object, context: str
) -> list[dict[str, str]]:
    if isinstance(payload, dict) and isinstance(payload.get("models"), list):
        payload = payload["models"]
    if not isinstance(payload, list) or not payload:
        raise ValueError(f"{context}: manifest must contain at least one model")
    models: list[dict[str, str]] = []
    for item in payload:
        if not isinstance(item, dict):
            raise ValueError(f"{context}: each model must be an object")
        digest = item.get("sha256")
        if (
            not isinstance(digest, str)
            or len(digest) != 64
            or any(
                character not in "0123456789abcdef"
                for character in digest.lower()
            )
        ):
            raise ValueError(
                f"{context}: each model needs a valid 64-character sha256"
            )
        local = item.get("local_path", item.get("path"))
        remote = item.get("remote_path")
        if not isinstance(local, str) and not isinstance(remote, str):
            raise ValueError(
                f"{context}: each model needs local_path/path or remote_path"
            )
        model = {"sha256": digest.lower()}
        if isinstance(local, str):
            model["local_path"] = local
        if isinstance(remote, str):
            model["remote_path"] = remote
        models.append(model)
    return models


def _manifest_from_root(
    repository_root: Path,
) -> tuple[str, Sequence[Mapping[str, str]] | None, str | None]:
    for relative in _MODEL_MANIFESTS:
        path = repository_root / relative
        if not path.is_file():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            models = _normalized_models(payload, "model manifest")
            return "present", models, None
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
            return "invalid", None, (
                "fix or remove the discovered manifest: it must be nonempty "
                "and every entry needs a valid sha256 plus local_path/path "
                "or remote_path"
            )
    return "absent", None, None


def _models(
    repository_root: Path,
    supplied: Sequence[Mapping[str, str]] | None,
) -> dict[str, object]:
    if supplied is not None:
        try:
            status, models, problem = (
                "present",
                _normalized_models(list(supplied), "model manifest"),
                None,
            )
        except ValueError:
            status, models, problem = (
                "invalid", None,
                "manifest must be nonempty and each entry needs a valid "
                "sha256 plus local_path/path or remote_path",
            )
    else:
        status, models, problem = _manifest_from_root(repository_root)
    entries: list[dict[str, object]] = []
    if status == "absent":
        return {
            "status": "absent",
            "entries": entries,
            "remediation": (
                "supply a manifest with sha256 plus local_path or remote_path "
                "for every required model; Wangp will not download models"
            ),
        }
    if models is None:
        return {
            "status": status,
            "entries": entries,
            "remediation": problem or "fix the model manifest",
        }
    for index, model in enumerate(models, start=1):
        local = model.get("local_path")
        state = "remote_declared"
        if local is not None:
            path = Path(local).expanduser()
            if not path.is_file():
                state = "missing"
            else:
                actual = _hash_file(path)
                expected = str(model.get("sha256", "")).lower()
                state = (
                    "verified" if actual == expected
                    else "unreadable" if actual is None
                    else "hash_mismatch"
                )
        download_required = state != "verified"
        entries.append({
            "id": f"entry-{index}",
            "status": state,
            "download_required": download_required,
            "wangp_downloads": False,
        })
    return {"status": status, "entries": entries, "remediation": ""}


def describe_capabilities(
    repository_root: str | Path,
    *,
    environ: Mapping[str, str],
    models: Sequence[Mapping[str, str]] | None = None,
) -> CapabilityReport:
    """Collect only local facts; never execute SSH, nvidia-smi, or network I/O."""

    root = Path(repository_root).expanduser().resolve()
    return CapabilityReport({
        "schema_version": "wangp-dspy.capabilities/v1",
        "platform": {"system": platform.system(), "machine": platform.machine()},
        "python": {
            "implementation": platform.python_implementation(),
            "version": platform.python_version(),
            "executable_name": Path(sys.executable).name,
        },
        "tools": {"ffmpeg": _tool("ffmpeg"), "ffprobe": _tool("ffprobe")},
        "local_accelerator": _accelerator(),
        "resources": _resources(root),
        "host_configuration": _host_state(root, environ),
        "model_manifest": _models(root, models),
        "generation_capabilities": {
            "implemented": IMPLEMENTED_CAPABILITIES,
            "not_implemented": NOT_IMPLEMENTED_CAPABILITIES,
        },
        "collection": {"read_only": True, "network_access": False, "host_contact": False},
    })


__all__ = [
    "CapabilityReport",
    "NOT_IMPLEMENTED_CAPABILITIES",
    "describe_capabilities",
]
