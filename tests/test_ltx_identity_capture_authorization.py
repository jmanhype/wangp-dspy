from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "datasets/runs/maestro-parity/ltx-dependency-terminalization"
PROPOSAL = BASE / "operator-proposal.identity-capture.20261009.json"
AUTHORIZATION = BASE / "operator-authorization.identity-capture.20261009.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_identity_capture_proposal_and_authorization_are_exact() -> None:
    proposal = json.loads(PROPOSAL.read_text(encoding="utf-8"))
    authorization = json.loads(AUTHORIZATION.read_text(encoding="utf-8"))

    assert digest(PROPOSAL) == (
        "e77f11fba5b4cce93bcdc1ff342b58e98146df942fe24e0afbdc09fa7f39deef"
    )
    assert authorization["operator_approval"] == {
        "proposal": (
            "datasets/runs/maestro-parity/ltx-dependency-terminalization/"
            "operator-proposal.identity-capture.20261009.json"
        ),
        "proposal_sha256": (
            "e77f11fba5b4cce93bcdc1ff342b58e98146df942fe24e0afbdc09fa7f39deef"
        ),
        "verbatim": "Continue authorized approved",
        "approved_at": "2026-10-09T00:21:12Z",
    }
    assert authorization["status"] == "approved"
    assert authorization["text"] == "Continue authorized approved"
    assert authorization["base_commit"] == (
        "9a47698d718e53f69ad49716aa44953bb07851d6"
    )


def test_identity_capture_authorization_is_one_shot_and_uses_existing_assets() -> None:
    authorization = json.loads(AUTHORIZATION.read_text(encoding="utf-8"))
    operations = [
        (item["row"], item["operation"], item["operation_id"])
        for item in authorization["operations"]
    ]

    assert operations == [
        ("LTX-2.5", "outpaint", "ltx25-outpaint"),
        ("LTX-2.5", "repaint", "ltx25-repaint"),
        ("LTX-2.5", "recast", "ltx25-recast"),
        ("LTX-2.5", "upscale", "ltx25-upscale"),
        ("LTX-2.3", "outpaint", "ltx23-outpaint"),
        ("LTX-2.3", "recast", "ltx23-recast"),
        ("LTX-2.3", "upscale", "ltx23-upscale"),
    ]
    assert authorization["operation_count"] == 7
    assert authorization["max_attempts_per_operation"] == 1
    assert authorization["retry"] == "never"
    assert authorization["stop_on_first_terminal_failure"] is True
    assert authorization["model_downloads"] == 0
    assert authorization["package_downloads"] == 0
    assert authorization["dependency_installs"] == 0
    assert authorization["provider_spend"] is False
    assert authorization["training"] is False
    assert authorization["deletions"] == 0
    assert set(authorization["existing_assets"]) == {
        "ltx-2.3-22b-ic-lora-ingredients-0.9.safetensors",
        "ltx-2.3-22b-ic-lora-outpaint.safetensors",
        "ltx-2.3-22b-ic-lora-in-outpainting-0.9.safetensors",
        "ltx-2.5-22b-ic-lora-pixel-spatial-upscaler-x2-1.0.safetensors",
        "ltx-2.3-22b-dev_diffusion_model_quanto_int8.safetensors",
        "ltx-2.3-22b-distilled-lora-384-1.1.safetensors",
        "ltx-2.3-22b-ic-lora-pixel-spatial-upscaler-x2-0.9.safetensors",
    }
    assert all(
        re.fullmatch("[0-9a-f]{64}", item["sha256"]) is not None
        for item in authorization["existing_assets"].values()
    )


def test_identity_capture_authorization_corrects_proposal_hash_typos_from_authority() -> None:
    authorization = json.loads(AUTHORIZATION.read_text(encoding="utf-8"))
    model_assets = {
        item["id"]: item
        for item in json.loads(
            (BASE / "model-assets.json").read_text(encoding="utf-8")
        )["assets"]
    }
    retry3_preflight = json.loads(
        (
            BASE
            / "final-cell-retry3-20261008/preflight.json"
        ).read_text(encoding="utf-8")
    )
    corrections = authorization["proposal_asset_hash_corrections"]

    assert set(corrections) == {
        "ltx-2.3-22b-ic-lora-ingredients-0.9.safetensors",
        "ltx-2.3-22b-distilled-lora-384-1.1.safetensors",
        "ltx-2.5-22b-ic-lora-pixel-spatial-upscaler-x2-1.0.safetensors",
    }
    assert corrections[
        "ltx-2.3-22b-ic-lora-ingredients-0.9.safetensors"
    ]["canonical_sha256"] == (
        model_assets["ltx-2.3-22b-ic-lora-ingredients-0.9.safetensors"]["sha256"]
    )
    assert corrections[
        "ltx-2.3-22b-distilled-lora-384-1.1.safetensors"
    ]["canonical_sha256"] == (
        retry3_preflight["existing_distilled_lora"]["sha256"]
    )
    assert corrections[
        "ltx-2.5-22b-ic-lora-pixel-spatial-upscaler-x2-1.0.safetensors"
    ]["canonical_sha256"] == (
        model_assets[
            "ltx-2.5-22b-ic-lora-pixel-spatial-upscaler-x2-1.0.safetensors"
        ]["sha256"]
    )
    for name, correction in corrections.items():
        assert authorization["existing_assets"][name]["sha256"] == (
            correction["canonical_sha256"]
        )
