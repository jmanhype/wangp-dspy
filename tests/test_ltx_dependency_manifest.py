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
AUTHORIZED_AUTHORIZATION_PATH = RUN_DIR / "operator-authorization.json"
TOTAL_BYTES = 23_701_298_279
ASSET_FIELDS = {
    "id", "source_url", "sha256", "xet_hash", "size_bytes", "license",
    "destination",
}

EXPECTED_ASSETS: dict[str, dict[str, Any]] = {
    "ltx-2.3-22b-ic-lora-ingredients-0.9.safetensors": {
        "id": "ltx-2.3-22b-ic-lora-ingredients-0.9.safetensors",
        "source_url": "https://huggingface.co/DeepBeepMeep/LTX-2/resolve/main/ltx-2.3-22b-ic-lora-ingredients-0.9.safetensors",
        "sha256": "515e4e139001ac6282357a5b35372e42e98b3affd5fcc886a52242abeed19559",
        "xet_hash": "4647f4f18c87208f949b6f473d49af679ddd87532b40718480e5153852f1f1ba",
        "size_bytes": 1_308_778_338,
        "license": "Upstream distribution license; operator research/evaluation only",
        "destination": "/home/straughter/Wan2GP/ckpts/ltx-2.3-22b-ic-lora-ingredients-0.9.safetensors",
    },
    "ltx-2.3-22b-ic-lora-outpaint.safetensors": {
        "id": "ltx-2.3-22b-ic-lora-outpaint.safetensors",
        "source_url": "https://huggingface.co/DeepBeepMeep/LTX-2/resolve/main/ltx-2.3-22b-ic-lora-outpaint.safetensors",
        "sha256": "32c5d3e0649aa4e89b192319f3c79460dfd2319d2859ca11fa6f88e983a81665",
        "xet_hash": "76df7c1ccbe8d657e38f38e8defbc0755a8d57b1a2b34fcad1f6376f4ce289f0",
        "size_bytes": 1_308_756_416,
        "license": "Upstream distribution license; operator research/evaluation only",
        "destination": "/home/straughter/Wan2GP/ckpts/ltx-2.3-22b-ic-lora-outpaint.safetensors",
    },
    "ltx-2.3-22b-ic-lora-in-outpainting-0.9.safetensors": {
        "id": "ltx-2.3-22b-ic-lora-in-outpainting-0.9.safetensors",
        "source_url": "https://huggingface.co/DeepBeepMeep/LTX-2/resolve/main/ltx-2.3-22b-ic-lora-in-outpainting-0.9.safetensors",
        "sha256": "73dd0841c0d4f0eb26fb1f017781b841b2752021944ac5ecefe57917f6dae6b5",
        "xet_hash": "748bca2d539cf2776abe801da96f06d6f31eec64f2354dea0f4b336292d3b837",
        "size_bytes": 1_308_778_338,
        "license": "Upstream distribution license; operator research/evaluation only",
        "destination": "/home/straughter/Wan2GP/ckpts/ltx-2.3-22b-ic-lora-in-outpainting-0.9.safetensors",
    },
    "ltx-2.5-22b-ic-lora-pixel-spatial-upscaler-x2-1.0.safetensors": {
        "id": "ltx-2.5-22b-ic-lora-pixel-spatial-upscaler-x2-1.0.safetensors",
        "source_url": "https://huggingface.co/DeepBeepMeep/LTX-2/resolve/main/ltx-2.5-22b-ic-lora-pixel-spatial-upscaler-x2-1.0.safetensors",
        "sha256": "984851b769ea2bcb4c9e0a239a7676239e42c6a6001ddc69943b41ff0b283c1d",
        "xet_hash": "229e549af18993e1670ad5dac7d2d8d03bb558ae446ac4ee23f8ba1263783996",
        "size_bytes": 327_322_640,
        "license": "Upstream distribution license; operator research/evaluation only",
        "destination": "/home/straughter/Wan2GP/ckpts/ltx-2.5-22b-ic-lora-pixel-spatial-upscaler-x2-1.0.safetensors",
    },
    "ltx-2.3-22b-dev_diffusion_model_quanto_int8.safetensors": {
        "id": "ltx-2.3-22b-dev_diffusion_model_quanto_int8.safetensors",
        "source_url": "https://huggingface.co/DeepBeepMeep/LTX-2/resolve/main/ltx-2.3-22b-dev_diffusion_model_quanto_int8.safetensors",
        "sha256": "5fc8d83656cdabf93b79bfb8799ee1c84c8270c59a49caccd4f8d1a27c77f6ec",
        "xet_hash": "f27d0effb85903172d976f1929dc0b3a204944ff014574eaab51cdc5e54f0f22",
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
    assert set(payload) == {"schema_version", "source_revision", "assets"}
    assert payload["schema_version"] == "wangp-dspy.model-assets/v1"
    assert payload["source_revision"] == "6aa898aea1d968febdd834dc29e1dbef35340aeb"
    entries = payload["assets"]
    assert isinstance(entries, list)
    identities = {entry["id"] for entry in entries}
    assert identities == set(EXPECTED_ASSETS), "asset identity set drift"
    assert len(entries) == len(EXPECTED_ASSETS)
    assert len(identities) == len(entries), "duplicate asset identity"
    for entry in entries:
        assert set(entry) == ASSET_FIELDS
        expected = EXPECTED_ASSETS[entry["id"]]
        for field in (
            "source_url", "sha256", "xet_hash", "size_bytes", "license",
            "destination",
        ):
            assert entry[field] == expected[field], f"{field} drift for {entry['id']}"
        assert entry["sha256"] != entry["xet_hash"], (
            f"file SHA-256 and XET hash are conflated for {entry['id']}"
        )
    assert sum(entry["size_bytes"] for entry in entries) == TOTAL_BYTES


def _assert_authorization(
    authorization: dict[str, Any], manifest: dict[str, Any]
) -> None:
    assert authorization["status"] == "authorized", (
        "authorization status is not authorized"
    )
    approval = authorization["operator_approval"]
    assert isinstance(approval, dict)
    assert approval.get("verbatim")
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
    manifest_assets = {item["id"]: item for item in manifest["assets"]}
    assert {
        item["id"]: {key: item[key] for key in ("sha256", "xet_hash")}
        for item in assets
    } == {
        item["id"]: {key: item[key] for key in ("sha256", "xet_hash")}
        for item in manifest["assets"]
    }
    assert all(
        manifest_assets[item["id"]]["sha256"] != item["xet_hash"]
        for item in assets
    )

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
            "no undeclared network access or download bytes",
            "no substitution from unrelated assets",
            "no training or provider spend",
            "no unrelated mutation, threshold change, or protected-engine semantic change",
            "no deletion except explicitly reversible temporary artifacts allowed by WD-28ac",
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


def test_recorded_operator_authorization_is_exact_and_linked_to_manifest() -> None:
    manifest = _read(MANIFEST_PATH)
    authorization = _read(AUTHORIZED_AUTHORIZATION_PATH)

    assert set(authorization) == {
        "schema_version",
        "status",
        "retry_authorized",
        "manifest",
        "metadata_correction",
        "corrected_retry_approval",
        "jev_phase_a_authorization",
        "jev_phase_b_preparation_authorization",
        "jev_qc_readiness_authorization",
        "jev_final_operations_authorization",
        "jev_runtime_repair_authorization",
        "assets",
        "operator_approval",
        "authorized_scope",
        "required_approval",
    }
    assert authorization["schema_version"] == "wangp-dspy.ltx-dependency-authorization/v1"
    assert authorization["retry_authorized"] is True
    assert authorization["operator_approval"] == {
        "verbatim": "Authorized",
        "approved_by": "operator",
        "timestamp": "2026-10-03T06:57:55Z",
        "source": "WD-28ac live tracker comment",
    }
    assert authorization["authorized_scope"]["execution_path"] == "governed Wan2GP queue/adapter"
    assert authorization["metadata_correction"] == {
        "audit_recorded_utc": "2026-10-03T08:11:12Z",
        "repository_revision": "6aa898aea1d968febdd834dc29e1dbef35340aeb",
        "model_json_sha256": "33fb1cde721375e7b391aa2189b711965364ac0dfa403a48407ab0e8d1604505",
        "tree_json_sha256": "079d472c84a9fa68e29fab9a17896a079ea209f6c6bc8d3313a7601ee5e91baa",
        "finding": "The prior manifest sha256 fields contained xetHash values. Repaired sha256 fields are metadata lfs.oid exact-file digests, and xet_hash remains a separately named non-SHA identity.",
        "prior_manifest_canonical_sha256": "7f159b99bdd3a688763c5c3d4188f5672ecff9af8003d2c5f76ab783fa31ceb1",
        "prior_correction_alone_did_not_authorize_retry": True,
        "retry_authorization": "corrected_retry_approval",
    }
    assert authorization["corrected_retry_approval"] == {
        "verbatim": "Yes",
        "approved_by": "operator",
        "timestamp": "2026-10-03T13:11:01Z",
        "source": "WD-28ac OPERATOR CORRECTED-RETRY AUTHORIZATION live tracker comment",
        "corrected_manifest_sha256": "05c9e6ba1d69d4a75c20d83bcb41e381e64de2a310b8dcba05a84f66b62136d2",
        "preserved_first_partial": {
            "asset_id": "ltx-2.3-22b-ic-lora-ingredients-0.9.safetensors",
            "path": "/home/straughter/Wan2GP/ckpts/ltx-2.3-22b-ic-lora-ingredients-0.9.safetensors.WD-28ac.partial",
            "size_bytes": 1_308_778_338,
            "sha256": "515e4e139001ac6282357a5b35372e42e98b3affd5fcc886a52242abeed19559",
            "network_requests_authorized": 0,
            "promotion_required_before_remaining_downloads": True,
        },
        "remaining_download_assets": [
            "ltx-2.3-22b-ic-lora-outpaint.safetensors",
            "ltx-2.3-22b-ic-lora-in-outpainting-0.9.safetensors",
            "ltx-2.5-22b-ic-lora-pixel-spatial-upscaler-x2-1.0.safetensors",
            "ltx-2.3-22b-dev_diffusion_model_quanto_int8.safetensors",
        ],
        "max_curl_invocations_per_remaining_asset": 1,
        "prior_undeclared_url_effective_get": {
            "reported_payload_bytes": 172_109,
            "retained_as_boundary": True,
            "repeat_allowed": False,
        },
        "operation_scope": [
            {"row": "LTX-2.5", "operation": "outpaint"},
            {"row": "LTX-2.5", "operation": "repaint"},
            {"row": "LTX-2.5", "operation": "recast"},
            {"row": "LTX-2.5", "operation": "upscale"},
            {"row": "LTX-2.3", "operation": "outpaint"},
            {"row": "LTX-2.3", "operation": "recast"},
            {"row": "LTX-2.3", "operation": "upscale"},
        ],
        "prohibitions": [
            "no deletion",
            "no training",
            "no provider spend",
            "no unrelated mutation",
            "no threshold change",
            "no protected-engine change",
            "no undeclared model/body request",
            "no WD-bw0h H3 retry",
        ],
    }
    assert authorization["jev_phase_a_authorization"] == {
        "gate": 2,
        "mode": "live",
        "model": "jev-latest",
        "decision": "CONTINUE",
        "confidence": 0.96,
        "snapshot_sha256": "1e7d3349996543e8cf1ae9d3f66711be26ab73fa1d8b49d866fafb2ec13cbdf2",
        "trace_sha256": "2f15b2d5bc2746d9354810b3ad5302635cad66ba97ae4c1af472b4336dc835dd",
        "phase": "downloads_only",
        "expected_existing_finals": [
            "ltx-2.3-22b-ic-lora-ingredients-0.9.safetensors",
            "ltx-2.3-22b-ic-lora-outpaint.safetensors",
        ],
        "assets": [
            "ltx-2.3-22b-ic-lora-in-outpainting-0.9.safetensors",
            "ltx-2.5-22b-ic-lora-pixel-spatial-upscaler-x2-1.0.safetensors",
            "ltx-2.3-22b-dev_diffusion_model_quanto_int8.safetensors",
        ],
        "max_curl_invocations_per_asset": 1,
        "prohibited_actions": {
            "qc_start_or_stop": True,
            "queue_admission": True,
            "render": True,
            "matrix_transition": True,
            "deletion_move_or_overwrite": True,
            "undeclared_model_or_url_effective_request": True,
        },
        "stop_before": "Jev Gate #3",
        "evidence": "jev-gates/2026-10-03/gate-evidence.json",
    }
    assert authorization["jev_phase_b_preparation_authorization"] == {
        "gate": 4,
        "mode": "live",
        "model": "jev-latest",
        "decision": "CONTINUE",
        "confidence": 0.78,
        "snapshot_sha256": "38e9b171448464138e18ba6b4987d43c48a1f65df9f3bfc3da628418b2c58500",
        "trace_sha256": "1636e28fb5dbc9945c9fbe98df51500b560c5e9b06792d9798bad4823d283b9d",
        "scope": "local_phase_b_preparation_only",
        "host_execution_authorized": False,
        "evidence": "jev-gates/2026-10-03/gate-3-4-evidence.json",
    }
    assert authorization["jev_qc_readiness_authorization"] == {
        "gate": 6,
        "mode": "live",
        "model": "jev-latest",
        "decision": "CONTINUE",
        "confidence": 0.98,
        "snapshot_sha256": "f9509a57f4311c4a595e591551fe2f3fd4e55e25bf0862ee107fb263d9340aae",
        "trace_sha256": "f6ffafda422883b9f5cb5149bb3e9384c167b034ec5d4cae9e994659c6e10726",
        "scope": "qc_readiness_only",
        "judge_control_path": "/home/straughter/marathon/bin/judge_ctl.sh",
        "health_endpoint": "http://127.0.0.1:8000/health",
        "authorized_actions": [
            "record_prestart_state",
            "start_existing_judge_ctl",
            "verify_port_8000_health",
            "record_healthy_state",
            "stop_judge_cleanly",
            "verify_zero_processes_and_health_unreachable",
        ],
        "prohibited_actions": [
            "native_operation",
            "queue_admission",
            "render",
            "retrieval",
            "network_model_get",
            "model_or_file_mutation",
            "unrelated_process_action",
            "protected_file_edit",
            "matrix_transition",
        ],
        "operations_authorized": False,
        "evidence": "jev-gates/2026-10-03/gate-5-6-evidence.json",
    }
    assert authorization["jev_final_operations_authorization"] == {
        "gate": 7,
        "mode": "live",
        "model": "jev-latest",
        "decision": "CONTINUE",
        "confidence": 0.80,
        "snapshot_sha256": "ed82d6d2fbb2cf7f9745a55625ec8850d2cb1ff9c70514634ce9698b85f9091c",
        "trace_sha256": "21709889328392ed0e33a76ccadd16eeb284fd45278ea36b94a6161b4a9bf7b7",
        "scope": "final_native_operations",
        "max_attempts_per_operation": 1,
        "retry": "never",
        "stop_on_first_terminal_failure": True,
        "operations_authorized": True,
        "matrix_cells_authorized": 7,
        "evidence": "jev-gates/2026-10-03/gate-7-evidence.json",
    }
    assert authorization["jev_runtime_repair_authorization"] == {
        "gate": 10,
        "mode": "live",
        "model": "jev-latest",
        "decision": "CONTINUE",
        "confidence": 0.81,
        "snapshot_sha256": "38780b034bc9d862491a8ec846e2ae3d736647cb65720a3f3dc426ccddb3bb4f",
        "trace_sha256": "7415a00a2e25eb468b3afee919fd5515ab5be6903cf04559f2cf8fece99804cd",
        "scope": "isolated_runtime_repair_only",
        "wheel_filename": "mmgp-3.7.14-py3-none-any.whl",
        "wheel_size_bytes": 68_211,
        "wheel_sha256": "6b544fa77a0256586bd9223c8f85c83a318c5d2f184b6adbdc655b7f22b5d208",
        "wheel_get_limit": 1,
        "dependency_installs": 0,
        "extract_destination": "/home/straughter/wd-28ac-final-gate7-20261003/runtime/mmgp-3.7.14",
        "isolated_python": "/usr/bin/python3",
        "import_isolated": True,
        "native_retry_authorized": False,
        "qc_start_authorized": False,
        "queue_admission_authorized": False,
        "render_authorized": False,
        "deletion_authorized": False,
        "model_or_reference_mutation_authorized": False,
        "evidence": "runtime-repair/2026-10-03/gate-summary.json",
    }
    assert authorization["authorized_scope"]["boundaries"] == [
        "no training",
        "no provider spend",
        "no unrelated mutation",
        "no threshold change",
        "no protected-engine change",
        "reversible storage handling",
        "no deletion except explicitly reversible temporary artifacts allowed by WD-28ac",
    ]
    _assert_authorization(authorization, manifest)


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


def test_xet_hash_conflation_fails_closed() -> None:
    conflated = _read(MANIFEST_PATH)
    entry = conflated["assets"][0]
    entry["sha256"] = entry["xet_hash"]
    with pytest.raises(AssertionError, match="sha256 drift"):
        _assert_manifest(conflated)


def test_partial_authorization_fails_closed() -> None:
    manifest = _read(MANIFEST_PATH)
    partial = _read(AUTHORIZATION_PATH)
    partial["status"] = "authorized"
    partial["operator_approval"] = {
        "verbatim": "partial approval",
        "approved_by": "operator",
        "timestamp": "2026-09-29T00:00:00Z",
    }
    partial["assets"] = partial["assets"][:4]
    with pytest.raises(AssertionError, match="authorization asset set drift"):
        _assert_authorization(partial, manifest)
