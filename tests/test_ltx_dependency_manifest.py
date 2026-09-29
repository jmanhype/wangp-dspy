from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from predict.model_assets import load_asset_manifest


ROOT = Path(__file__).resolve().parents[1]
RUN_DIR = ROOT / "datasets/runs/maestro-parity/ltx-dependency-terminalization"
MANIFEST_PATH = RUN_DIR / "model-assets.json"
AUTHORIZATION_PATH = RUN_DIR / "operator-authorization.template.json"
TOTAL_BYTES = 23_701_298_279
ASSET_FIELDS = {
    "id", "source_url", "sha256", "size_bytes", "license", "destination",
}

EXPECTED_ASSETS: dict[str, dict[str, Any]] = {
    "ltx-2.3-22b-ic-lora-ingredients-0.9.safetensors": {
        "id": "ltx-2.3-22b-ic-lora-ingredients-0.9.safetensors",
        "source_url": "https://huggingface.co/DeepBeepMeep/LTX-2/resolve/main/ltx-2.3-22b-ic-lora-ingredients-0.9.safetensors",
        "sha256": "4647f4f18c87208f949b6f473d49af679ddd87532b40718480e5153852f1f1ba",
        "size_bytes": 1_308_778_338,
        "license": "Upstream distribution license; operator research/evaluation only",
        "destination": "/home/straughter/Wan2GP/ckpts/ltx-2.3-22b-ic-lora-ingredients-0.9.safetensors",
    },
    "ltx-2.3-22b-ic-lora-outpaint.safetensors": {
        "id": "ltx-2.3-22b-ic-lora-outpaint.safetensors",
        "source_url": "https://huggingface.co/DeepBeepMeep/LTX-2/resolve/main/ltx-2.3-22b-ic-lora-outpaint.safetensors",
        "sha256": "76df7c1ccbe8d657e38f38e8defbc0755a8d57b1a2b34fcad1f6376f4ce289f0",
        "size_bytes": 1_308_756_416,
        "license": "Upstream distribution license; operator research/evaluation only",
        "destination": "/home/straughter/Wan2GP/ckpts/ltx-2.3-22b-ic-lora-outpaint.safetensors",
    },
    "ltx-2.3-22b-ic-lora-in-outpainting-0.9.safetensors": {
        "id": "ltx-2.3-22b-ic-lora-in-outpainting-0.9.safetensors",
        "source_url": "https://huggingface.co/DeepBeepMeep/LTX-2/resolve/main/ltx-2.3-22b-ic-lora-in-outpainting-0.9.safetensors",
        "sha256": "748bca2d539cf2776abe801da96f06d6f31eec64f2354dea0f4b336292d3b837",
        "size_bytes": 1_308_778_338,
        "license": "Upstream distribution license; operator research/evaluation only",
        "destination": "/home/straughter/Wan2GP/ckpts/ltx-2.3-22b-ic-lora-in-outpainting-0.9.safetensors",
    },
    "ltx-2.5-22b-ic-lora-pixel-spatial-upscaler-x2-1.0.safetensors": {
        "id": "ltx-2.5-22b-ic-lora-pixel-spatial-upscaler-x2-1.0.safetensors",
        "source_url": "https://huggingface.co/DeepBeepMeep/LTX-2/resolve/main/ltx-2.5-22b-ic-lora-pixel-spatial-upscaler-x2-1.0.safetensors",
        "sha256": "229e549af18993e1670ad5dac7d2d8d03bb558ae446ac4ee23f8ba1263783996",
        "size_bytes": 327_322_640,
        "license": "Upstream distribution license; operator research/evaluation only",
        "destination": "/home/straughter/Wan2GP/ckpts/ltx-2.5-22b-ic-lora-pixel-spatial-upscaler-x2-1.0.safetensors",
    },
    "ltx-2.3-22b-dev_diffusion_model_quanto_int8.safetensors": {
        "id": "ltx-2.3-22b-dev_diffusion_model_quanto_int8.safetensors",
        "source_url": "https://huggingface.co/DeepBeepMeep/LTX-2/resolve/main/ltx-2.3-22b-dev_diffusion_model_quanto_int8.safetensors",
        "sha256": "f27d0effb85903172d976f1929dc0b3a204944ff014574eaab51cdc5e54f0f22",
        "size_bytes": 19_447_662_547,
        "license": "Upstream distribution license; operator research/evaluation only",
        "destination": "/home/straughter/Wan2GP/ckpts/ltx-2.3-22b-dev_diffusion_model_quanto_int8.safetensors",
    },
}

EXPECTED_OWNERSHIP: dict[str, frozenset[tuple[str, str]]] = {
    "ltx-2.3-22b-ic-lora-ingredients-0.9.safetensors": frozenset({
        ("LTX-2.5", "recast"),
        ("LTX-2.3", "recast"),
    }),
    "ltx-2.3-22b-ic-lora-outpaint.safetensors": frozenset({
        ("LTX-2.5", "outpaint"),
        ("LTX-2.3", "outpaint"),
    }),
    "ltx-2.3-22b-ic-lora-in-outpainting-0.9.safetensors": frozenset({
        ("LTX-2.5", "repaint"),
    }),
    "ltx-2.5-22b-ic-lora-pixel-spatial-upscaler-x2-1.0.safetensors": frozenset({
        ("LTX-2.5", "upscale"),
    }),
    "ltx-2.3-22b-dev_diffusion_model_quanto_int8.safetensors": frozenset({
        ("LTX-2.3", "upscale"),
    }),
}

EXPECTED_CELLS = frozenset().union(*EXPECTED_OWNERSHIP.values())


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _assert_manifest(payload: dict[str, Any]) -> None:
    assert set(payload) == {"schema_version", "assets"}
    assert payload["schema_version"] == "wangp-dspy.model-assets/v1"
    entries = payload["assets"]
    assert isinstance(entries, list)
    identities = {entry["id"] for entry in entries}
    assert identities == set(EXPECTED_ASSETS), "asset identity set drift"
    assert len(entries) == len(EXPECTED_ASSETS)
    assert len(identities) == len(entries), "duplicate asset identity"
    for entry in entries:
        assert set(entry) == ASSET_FIELDS
        expected = EXPECTED_ASSETS[entry["id"]]
        for field in ("source_url", "sha256", "size_bytes", "license", "destination"):
            assert entry[field] == expected[field], f"{field} drift for {entry['id']}"
    assert sum(entry["size_bytes"] for entry in entries) == TOTAL_BYTES


def _assert_authorization(
    authorization: dict[str, Any], manifest: dict[str, Any]
) -> None:
    assert authorization["status"] == "approved", (
        "authorization status is not approved"
    )
    approval = authorization["operator_approval"]
    assert isinstance(approval, dict)
    assert approval.get("text")
    assert approval.get("approved_by")
    assert approval.get("timestamp")

    manifest_digest = hashlib.sha256(
        json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    reference = authorization["manifest"]
    assert reference["path"] == "model-assets.json"
    assert reference["sha256"] == manifest_digest
    assert reference["total_download_bytes"] == TOTAL_BYTES

    assets = authorization["assets"]
    assert {item["id"] for item in assets} == set(EXPECTED_ASSETS), (
        "authorization asset set drift"
    )
    observed_ownership = {
        item["id"]: frozenset(
            (cell["row"], cell["operation"]) for cell in item["cells"]
        )
        for item in assets
    }
    assert observed_ownership == EXPECTED_OWNERSHIP
    assert frozenset().union(*observed_ownership.values()) == EXPECTED_CELLS

    required = authorization["required_approval"]
    assert required == {
        "asset_ids": sorted(EXPECTED_ASSETS),
        "total_download_bytes": TOTAL_BYTES,
        "host": "3090",
        "cells": [
            {"row": row, "operation": operation}
            for row, operation in sorted(EXPECTED_CELLS)
        ],
        "prohibitions": [
            "no model-byte download or HEAD request",
            "no storage mutation",
            "no queue admission, render, or retrieval",
            "no protected-engine semantic change",
        ],
    }


def test_manifest_schema_and_exact_order_neutral_asset_identities() -> None:
    payload = _read(MANIFEST_PATH)
    _assert_manifest(payload)
    parsed = load_asset_manifest(MANIFEST_PATH)
    assert [asset.model_dump() for asset in parsed.assets] == payload["assets"]


def test_manifest_total_is_exactly_declared_download_volume() -> None:
    payload = _read(MANIFEST_PATH)
    assert len(payload["assets"]) == 5
    assert sum(item["size_bytes"] for item in payload["assets"]) == TOTAL_BYTES


def test_authorization_template_links_manifest_but_stays_not_authorized() -> None:
    manifest = _read(MANIFEST_PATH)
    authorization = _read(AUTHORIZATION_PATH)
    manifest_digest = hashlib.sha256(
        json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    assert authorization["status"] == "not_authorized"
    assert authorization["operator_approval"] is None
    assert authorization["manifest"]["path"] == "model-assets.json"
    assert authorization["manifest"]["sha256"] == manifest_digest
    assert authorization["manifest"]["total_download_bytes"] == TOTAL_BYTES
    with pytest.raises(AssertionError, match="authorization status"):
        _assert_authorization(authorization, manifest)


def test_authorization_template_owns_exactly_seven_affected_cells() -> None:
    authorization = _read(AUTHORIZATION_PATH)
    ownership = {
        item["id"]: frozenset(
            (cell["row"], cell["operation"]) for cell in item["cells"]
        )
        for item in authorization["assets"]
    }
    assert ownership == EXPECTED_OWNERSHIP
    assert frozenset().union(*ownership.values()) == EXPECTED_CELLS
    assert len(EXPECTED_CELLS) == 7


@pytest.mark.parametrize(
    "asset_id", sorted(EXPECTED_ASSETS), ids=sorted(EXPECTED_ASSETS)
)
def test_every_asset_identity_is_exact(asset_id: str) -> None:
    entries = {
        entry["id"]: entry for entry in _read(MANIFEST_PATH)["assets"]
    }
    assert entries[asset_id] == EXPECTED_ASSETS[asset_id]


def test_manifest_drift_fails_closed() -> None:
    wrong_hash = _read(MANIFEST_PATH)
    wrong_hash["assets"][0]["sha256"] = "0" * 64
    with pytest.raises(AssertionError, match="sha256 drift"):
        _assert_manifest(wrong_hash)

    partial_asset_set = _read(MANIFEST_PATH)
    partial_asset_set["assets"] = partial_asset_set["assets"][:4]
    with pytest.raises(AssertionError, match="asset identity set drift"):
        _assert_manifest(partial_asset_set)

    undeclared_extra_bytes = _read(MANIFEST_PATH)
    undeclared_extra_bytes["assets"][0]["size_bytes"] += 1
    with pytest.raises(AssertionError, match="size_bytes drift"):
        _assert_manifest(undeclared_extra_bytes)


def test_partial_authorization_fails_closed() -> None:
    manifest = _read(MANIFEST_PATH)
    partial = _read(AUTHORIZATION_PATH)
    partial["status"] = "approved"
    partial["operator_approval"] = {
        "text": "partial approval",
        "approved_by": "operator",
        "timestamp": "2026-09-29T00:00:00Z",
    }
    partial["assets"] = partial["assets"][:4]
    with pytest.raises(AssertionError, match="authorization asset set drift"):
        _assert_authorization(partial, manifest)
