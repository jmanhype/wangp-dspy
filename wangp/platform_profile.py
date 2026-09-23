"""Typed local hardware inventory and advisory profile recommendation."""

from __future__ import annotations

import os
import platform
import shutil
from pathlib import Path
from typing import Mapping

from pydantic import BaseModel, ConfigDict, Field, field_validator


INVENTORY_SCHEMA = "wangp-dspy.platform-inventory/v1"
PROFILE_SCHEMA = "wangp-dspy.platform-profile/v1"
MINIMUM_DISK_BYTES = 100 * 1024**3
MINIMUM_ACCELERATOR_VRAM_BYTES = 24 * 1024**3


class PlatformSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    system: str = Field(min_length=1)
    release: str = Field(min_length=1)
    machine: str = Field(min_length=1)
    processor: str | None = None


class CpuSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    logical_cores: int = Field(gt=0)
    physical_cores: int | None = Field(default=None, gt=0)
    name: str | None = None


class MemorySnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    total_bytes: int = Field(gt=0)
    available_bytes: int | None = Field(default=None, gt=0)


class DiskSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    root: str = Field(min_length=1)
    total_bytes: int = Field(gt=0)
    free_bytes: int = Field(gt=0)


class AcceleratorSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: str = Field(min_length=1)
    name: str | None = None
    vram_bytes: int | None = Field(default=None, gt=0)
    detection: str = Field(min_length=1)


class PlatformInventory(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = INVENTORY_SCHEMA
    platform: PlatformSnapshot
    cpu: CpuSnapshot
    memory: MemorySnapshot
    disk: DiskSnapshot
    accelerators: tuple[AcceleratorSnapshot, ...] = ()

    @field_validator("schema_version")
    @classmethod
    def _version(cls, value: str) -> str:
        if value != INVENTORY_SCHEMA:
            raise ValueError(
                f"unsupported inventory schema {value!r}; expected {INVENTORY_SCHEMA}"
            )
        return value


def collect_inventory(
    repository_root: str | Path = ".",
    *,
    environ: Mapping[str, str] | None = None,
) -> PlatformInventory:
    """Collect standard-library facts only; never run a hardware tool."""

    del environ  # Kept in the signature to make future env inputs explicit.
    root = Path(repository_root).expanduser().resolve()
    usage = shutil.disk_usage(root)
    try:
        memory_total = os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")
    except (AttributeError, OSError, ValueError):
        memory_total = 0
    if memory_total <= 0:
        raise ValueError("local physical memory size is unavailable")

    accelerators: tuple[AcceleratorSnapshot, ...] = ()
    if shutil.which("nvidia-smi") is not None:
        accelerators = (
            AcceleratorSnapshot(
                kind="cuda-presence-only",
                name=None,
                vram_bytes=None,
                detection="nvidia-smi found on PATH; executable not run",
            ),
        )
    return PlatformInventory(
        platform=PlatformSnapshot(
            system=platform.system(),
            release=platform.release(),
            machine=platform.machine(),
            processor=platform.processor() or None,
        ),
        cpu=CpuSnapshot(
            logical_cores=os.cpu_count() or 1,
            physical_cores=None,
            name=None,
        ),
        memory=MemorySnapshot(total_bytes=memory_total, available_bytes=None),
        disk=DiskSnapshot(
            root=str(root),
            total_bytes=usage.total,
            free_bytes=usage.free,
        ),
        accelerators=accelerators,
    )


def _recommendation(
    inventory: PlatformInventory,
) -> tuple[str, str, list[str], list[str]]:
    largest_vram = max(
        (
            accelerator.vram_bytes
            for accelerator in inventory.accelerators
            if accelerator.vram_bytes is not None
        ),
        default=None,
    )
    unknowns = [
        "cpu name unavailable from the local standard library",
        "memory availability was not inferred",
    ]
    if any(accelerator.vram_bytes is None for accelerator in inventory.accelerators):
        unknowns.append(
            "accelerator VRAM unavailable without executing hardware tools"
        )
    enough_disk = inventory.disk.free_bytes >= MINIMUM_DISK_BYTES
    if largest_vram is not None and largest_vram >= MINIMUM_ACCELERATOR_VRAM_BYTES:
        profile = "local-candidate-24gb"
        reasons = [
            "24 GiB or more accelerator memory was reported",
            "at least 100 GiB disk headroom was reported" if enough_disk
            else "less than 100 GiB disk headroom was reported",
        ]
        return profile, "advisory-unverified", reasons, unknowns
    if inventory.accelerators:
        profile = "planning-only-external-render"
        reasons = [
            "no accelerator reported at least 24 GiB VRAM",
            "at least 100 GiB disk headroom was reported" if enough_disk
            else "less than 100 GiB disk headroom was reported",
        ]
        return profile, "advisory-unverified", reasons, unknowns
    unknowns.append(
        "accelerator VRAM unavailable without executing hardware tools"
    )
    return (
        "planning-only-external-render",
        "advisory-unverified",
        ["no local accelerator was reported"],
        unknowns,
    )


def profile_mapping(inventory: PlatformInventory) -> dict[str, object]:
    """Return the stable machine view; the recommendation is not execution proof."""

    profile, status, reasons, unknowns = _recommendation(inventory)
    accelerators = [item.model_dump(exclude_none=True) for item in inventory.accelerators]
    return {
        "schema_version": PROFILE_SCHEMA,
        "platform": inventory.platform.model_dump(exclude_none=True),
        "cpu": inventory.cpu.model_dump(exclude_none=True),
        "memory": inventory.memory.model_dump(exclude_none=True),
        "disk": inventory.disk.model_dump(),
        "accelerators": accelerators,
        "recommendation": {
            "profile": profile,
            "status": status,
            "reasons": reasons,
        },
        "unknowns": unknowns,
        "collection": {
            "read_only": True,
            "network_access": False,
            "host_contact": False,
            "gpu_work": False,
            "verified_generation": False,
        },
    }


def render_profile(payload: Mapping[str, object]) -> str:
    value = dict(payload)
    platform_value = dict(value["platform"])
    recommendation = dict(value["recommendation"])
    accelerators = list(value["accelerators"])
    cpu = dict(value["cpu"])
    memory = dict(value["memory"])
    disk = dict(value["disk"])
    if not accelerators:
        accelerator_line = "accelerators=0 vram_bytes=unknown"
    else:
        vram_values = [
            item.get("vram_bytes") for item in accelerators
            if item.get("vram_bytes") is not None
        ]
        rendered_vram = str(max(vram_values)) if vram_values else "unknown"
        accelerator_line = (
            f"accelerators={len(accelerators)} vram_bytes={rendered_vram}"
        )
    return "\n".join([
        f"platform={platform_value['system']} {platform_value['machine']}",
        f"cpu_logical_cores={cpu['logical_cores']}",
        f"ram_total_bytes={memory['total_bytes']} ram_available_bytes={memory.get('available_bytes', 'unknown')}",
        f"disk_free_bytes={disk['free_bytes']} disk_total_bytes={disk['total_bytes']}",
        accelerator_line,
        f"profile={recommendation['profile']}",
        f"profile_status={recommendation['status']}",
        *(f"reason={reason}" for reason in recommendation["reasons"]),
        *(f"unknown={reason}" for reason in value["unknowns"]),
        "gpu_work=false host_contact=false verified_generation=false",
    ])


__all__ = [
    "PlatformInventory",
    "collect_inventory",
    "profile_mapping",
    "render_profile",
]
