"""Explicit render-host preview that always stops before transport."""

from __future__ import annotations

import shlex
from typing import Any

from wangp.config import (
    ENVIRONMENT_KEYS,
    HostConfig,
    missing_host_keys,
)


def _preview_target(config: HostConfig) -> str:
    return (
        config.target.value
        if config.target is not None
        else "<unconfigured-target>"
    )


def command_preview(config: HostConfig) -> str:
    target = _preview_target(config)
    return shlex.join(["ssh", "-o", "BatchMode=yes", target, "true"])


def remote_report(config: HostConfig) -> dict[str, Any]:
    missing = missing_host_keys(config)
    settings = []
    for key, setting in zip(
        ("host.target", "host.wgp_root", "host.pull_root"),
        config.required_settings(),
        strict=True,
    ):
        settings.append({
            "key": key,
            "configured": setting is not None,
            "source": setting.source if setting is not None else "unconfigured",
        })
    environment = [ENVIRONMENT_KEYS[key] for key in missing]
    diagnostic = None
    if missing:
        diagnostic = {
            "code": "HOST_CONFIGURATION_INCOMPLETE",
            "severity": "error",
            "title": "Explicit render host is incomplete",
            "observed": f"missing {', '.join(missing)}",
            "why": "Wangp will not infer or contact a renderer host.",
            "remediation": (
                "Set every explicit host value, then rerun this preview before authorization."
            ),
            "next_command": "wgp first-run remote --json",
            "evidence_refs": [str(config.repository_config), str(config.user_config)],
            "metadata": {"missing_keys": list(missing), "environment_keys": environment},
        }
    return {
        "ready": not missing,
        "missing_keys": list(missing),
        "settings": settings,
        "command_preview": command_preview(config),
        "host_contact": False,
        "authorization_required": True,
        "diagnostics": [] if diagnostic is None else [diagnostic],
    }


def render_remote(payload: dict[str, Any]) -> str:
    return "\n".join([
        f"ready={str(payload['ready']).lower()}",
        f"missing_keys={','.join(payload['missing_keys']) or 'none'}",
        f"command_preview={payload['command_preview']}",
        "host_contact=false",
        f"authorization_required={str(payload['authorization_required']).lower()}",
    ])


__all__ = ["command_preview", "remote_report", "render_remote"]
