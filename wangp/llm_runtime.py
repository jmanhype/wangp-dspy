"""Typed local-or-external LLM runtime selection without provider calls."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Mapping

from pydantic import BaseModel, ConfigDict, Field, field_validator


RUNTIME_SCHEMA = "wangp-dspy.llm-runtime/v1"


class LlmRuntimeError(ValueError):
    """A typed fail-closed runtime preflight rejection."""

    def __init__(self, code: str, observed: str, remediation: str) -> None:
        super().__init__(observed)
        self.code = code
        self.observed = observed
        self.remediation = remediation


class LocalRuntime(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    model_path: str = Field(min_length=1)
    sha256: str = Field(min_length=64, max_length=64)
    runtime_command: tuple[str, ...] = Field(min_length=1)

    @field_validator("sha256")
    @classmethod
    def _digest(cls, value: str) -> str:
        normalized = value.lower()
        if any(character not in "0123456789abcdef" for character in normalized):
            raise ValueError("local model sha256 must be hexadecimal")
        return normalized


class ExternalRuntime(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    provider: str = Field(min_length=1)
    base_url: str = Field(min_length=1)
    model: str = Field(min_length=1)
    api_key_env: str = Field(min_length=1)


class LlmRuntimeConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = RUNTIME_SCHEMA
    selection: str = Field(pattern="^(local-only|external-only|local-then-external)$")
    local: LocalRuntime | None = None
    external: ExternalRuntime | None = None

    @field_validator("schema_version")
    @classmethod
    def _version(cls, value: str) -> str:
        if value != RUNTIME_SCHEMA:
            raise ValueError(f"unsupported runtime schema {value!r}; expected {RUNTIME_SCHEMA}")
        return value


def load_runtime_config(path: str | Path) -> LlmRuntimeConfig:
    source = Path(path).expanduser()
    import json

    payload = json.loads(source.read_text(encoding="utf-8"))
    return LlmRuntimeConfig.model_validate(payload)


def _digest(path: Path) -> str | None:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError:
        return None
    return digest.hexdigest()


def _local_status(
    runtime: LocalRuntime,
) -> tuple[str, str | None, int | None]:
    path = Path(runtime.model_path).expanduser()
    if not path.is_file():
        return "missing", None, None
    actual = _digest(path)
    if actual is None:
        return "unreadable", None, None
    if actual != runtime.sha256:
        return "hash_mismatch", actual, path.stat().st_size
    return "complete", actual, path.stat().st_size


def resolve_runtime(
    config: LlmRuntimeConfig,
    *,
    environ: Mapping[str, str],
) -> dict[str, Any]:
    """Resolve configuration only; no model or external provider is contacted."""

    local: dict[str, Any] | None = None
    if config.local is not None:
        status, actual, size = _local_status(config.local)
        local = {
            "status": status,
            "model_path": config.local.model_path,
            "sha256": config.local.sha256,
            "observed_sha256": actual,
            "size_bytes": size,
            "runtime_command": list(config.local.runtime_command),
            "executed": False,
        }
    if config.selection in {"local-only", "local-then-external"}:
        if local is not None and local["status"] == "complete":
            return {
                "schema_version": RUNTIME_SCHEMA,
                "selected_runtime": "bundled-local",
                "ready": True,
                "local": local,
                "external": None,
                "provider_contact": False,
            }
        if config.selection == "local-only":
            raise LlmRuntimeError(
                "LOCAL_RUNTIME_ASSET_INVALID",
                f"local model status={local and local['status']}",
                "Restore the configured local model bytes or change runtime selection explicitly.",
            )
    if config.external is None:
        raise LlmRuntimeError(
            "LLM_RUNTIME_INCOMPLETE",
            "external fallback is not configured",
            "Record provider, base URL, model, and API-key environment variable.",
        )
    credential = environ.get(config.external.api_key_env, "").strip()
    if not credential:
        raise LlmRuntimeError(
            "LLM_CREDENTIAL_MISSING",
            f"environment variable {config.external.api_key_env} is empty",
            "Set the credential in the named environment variable; never record its value.",
        )
    return {
        "schema_version": RUNTIME_SCHEMA,
        "selected_runtime": "external-provider",
        "ready": True,
        "local": local,
        "external": {
            "provider": config.external.provider,
            "base_url": config.external.base_url,
            "model": config.external.model,
            "api_key_env": config.external.api_key_env,
            "credential_present": True,
        },
        "provider_contact": False,
    }


def render_runtime(payload: Mapping[str, Any]) -> str:
    value = dict(payload)
    selected = value["selected_runtime"]
    ready = str(value["ready"]).lower()
    provider_contact = str(value["provider_contact"]).lower()
    lines = [
        f"runtime={selected}",
        f"ready={ready}",
        f"provider_contact={provider_contact}",
    ]
    if value.get("local") is not None:
        local = dict(value["local"])
        lines.append(
            f"local_status={local['status']} executed=false"
        )
    if value.get("external") is not None:
        external = dict(value["external"])
        lines.append(
            f"external_provider={external['provider']} credential=present_not_read"
        )
    return "\n".join(lines)


__all__ = [
    "LlmRuntimeConfig",
    "LlmRuntimeError",
    "load_runtime_config",
    "render_runtime",
    "resolve_runtime",
]
