"""Typed, durable model-asset status without implicit downloads."""

from __future__ import annotations

import hashlib
import json
import re
import shlex
from pathlib import Path
from typing import Mapping

from pydantic import BaseModel, ConfigDict, Field, field_validator


ASSET_SCHEMA = "wangp-dspy.model-assets/v1"
STATE_SCHEMA = "wangp-dspy.download-state/v1"
_SHA256 = re.compile(r"[0-9a-f]{64}")


class ModelAsset(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(min_length=1)
    source_url: str = Field(min_length=1)
    sha256: str = Field(min_length=64, max_length=64)
    size_bytes: int = Field(gt=0)
    license: str = Field(min_length=1)
    destination: str = Field(min_length=1)

    @field_validator("sha256")
    @classmethod
    def _digest(cls, value: str) -> str:
        normalized = value.lower()
        if _SHA256.fullmatch(normalized) is None:
            raise ValueError("sha256 must be 64 lowercase hexadecimal characters")
        return normalized

    @field_validator("source_url")
    @classmethod
    def _url(cls, value: str) -> str:
        if not (value.startswith("https://") or value.startswith("http://")):
            raise ValueError("source_url must be an explicit http(s) URL")
        return value

    @field_validator("destination")
    @classmethod
    def _absolute(cls, value: str) -> str:
        if not Path(value).is_absolute():
            raise ValueError("destination must be an absolute local path")
        return value


class AssetManifest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = ASSET_SCHEMA
    assets: tuple[ModelAsset, ...] = Field(min_length=1)

    @field_validator("schema_version")
    @classmethod
    def _version(cls, value: str) -> str:
        if value != ASSET_SCHEMA:
            raise ValueError(f"unsupported asset schema {value!r}; expected {ASSET_SCHEMA}")
        return value


class AssetState(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    paused: bool = False
    resume_requested: bool = False


class DownloadState(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = STATE_SCHEMA
    assets: dict[str, AssetState] = Field(default_factory=dict)

    @field_validator("schema_version")
    @classmethod
    def _version(cls, value: str) -> str:
        if value != STATE_SCHEMA:
            raise ValueError(f"unsupported state schema {value!r}; expected {STATE_SCHEMA}")
        return value


def load_asset_manifest(path: str | Path) -> AssetManifest:
    source = Path(path).expanduser()
    payload = json.loads(source.read_text(encoding="utf-8"))
    return AssetManifest.model_validate(payload)


def load_download_state(path: str | Path) -> DownloadState:
    source = Path(path).expanduser()
    if not source.is_file():
        return DownloadState()
    payload = json.loads(source.read_text(encoding="utf-8"))
    return DownloadState.model_validate(payload)


def write_download_state(path: str | Path, state: DownloadState) -> None:
    target = Path(path).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.tmp")
    temporary.write_text(
        json.dumps(state.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(target)


def _file_digest(path: Path) -> str | None:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError:
        return None
    return digest.hexdigest()


def asset_status(
    asset: ModelAsset, state: AssetState
) -> dict[str, object]:
    destination = Path(asset.destination).expanduser()
    observed_bytes: int | None = None
    observed_digest: str | None = None
    if destination.is_file():
        try:
            observed_bytes = destination.stat().st_size
            observed_digest = _file_digest(destination)
        except OSError:
            observed_bytes = None
            observed_digest = None
    if observed_bytes == asset.size_bytes and observed_digest == asset.sha256:
        status = "complete"
    elif state.paused:
        status = "paused"
    elif observed_bytes is None:
        status = "absent" if not destination.exists() else "unreadable"
    elif observed_bytes == asset.size_bytes:
        status = "checksum_mismatch"
    elif observed_bytes < asset.size_bytes:
        status = "partial"
    else:
        status = "checksum_mismatch"
    return {
        "id": asset.id,
        "status": status,
        "size_bytes": asset.size_bytes,
        "bytes_present": observed_bytes,
        "observed_sha256": observed_digest,
        "paused": state.paused,
        "resume_requested": state.resume_requested,
        "source_url": asset.source_url,
        "license": asset.license,
        "destination": asset.destination,
    }


def asset_report(
    manifest: AssetManifest, state: DownloadState
) -> dict[str, object]:
    entries = [
        asset_status(asset, state.assets.get(asset.id, AssetState()))
        for asset in manifest.assets
    ]
    pending = [entry for entry in entries if entry["status"] != "complete"]
    return {
        "schema_version": ASSET_SCHEMA,
        "assets": entries,
        "download_plan": {
            "asset_count": len(pending),
            "total_size_bytes": sum(
                int(entry["size_bytes"]) for entry in pending
            ),
            "wangp_downloads": False,
            "authorization_required": True,
        },
    }


def pause_asset(
    manifest: AssetManifest, state: DownloadState, asset_id: str
) -> DownloadState:
    if asset_id not in {asset.id for asset in manifest.assets}:
        raise KeyError(f"unknown asset id: {asset_id}")
    values = dict(state.assets)
    previous = values.get(asset_id, AssetState())
    values[asset_id] = AssetState(
        paused=True, resume_requested=previous.resume_requested
    )
    return DownloadState(assets=values)


def resume_asset(
    manifest: AssetManifest, state: DownloadState, asset_id: str
) -> tuple[DownloadState, ModelAsset]:
    if asset_id not in {asset.id for asset in manifest.assets}:
        raise KeyError(f"unknown asset id: {asset_id}")
    values = dict(state.assets)
    previous = values.get(asset_id, AssetState())
    values[asset_id] = AssetState(
        paused=False, resume_requested=True
    )
    asset = next(item for item in manifest.assets if item.id == asset_id)
    return DownloadState(assets=values), asset


def operator_download_command(asset: ModelAsset) -> str:
    return shlex.join([
        "curl",
        "--fail",
        "--location",
        "--continue-at",
        "-",
        "--output",
        asset.destination,
        asset.source_url,
    ])


__all__ = [
    "AssetManifest",
    "DownloadState",
    "asset_report",
    "load_asset_manifest",
    "load_download_state",
    "operator_download_command",
    "pause_asset",
    "resume_asset",
    "write_download_state",
]
