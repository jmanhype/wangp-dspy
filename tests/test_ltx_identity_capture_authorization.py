from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pytest

import scripts.run_ltx_final_operations as runner

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "datasets/runs/maestro-parity/ltx-dependency-terminalization"
PROPOSAL = BASE / "operator-proposal.identity-capture.20261009.json"
AUTHORIZATION = BASE / "operator-authorization.identity-capture.20261009.json"


def direct_contract():
    plan = json.loads((BASE / "phase-b-preparation/corrected-retry-plan.json").read_text())
    authorization = json.loads(AUTHORIZATION.read_text())
    plan["identity_capture_authorization_binding"] = runner.identity_capture_authorization_binding(authorization)
    plan.pop("host_authorization_binding", None)
    plan.pop("execution_preconditions", None)
    return plan, authorization


def test_direct_authorization_valid_without_legacy_gates():
    plan, authorization = direct_contract()
    runner.validate_contract(plan, authorization)


@pytest.mark.parametrize("field", [
    "schema_version", "base_commit", "proposal_sha256", "authorization_canonical_sha256", "missing",
])
def test_direct_authorization_requires_exact_plan_binding(field):
    plan, authorization = direct_contract()
    if field == "missing":
        del plan["identity_capture_authorization_binding"]
    else:
        plan["identity_capture_authorization_binding"][field] = "wrong"
    with pytest.raises(runner.FinalOperationError) as error:
        runner.validate_contract(plan, authorization)
    assert error.value.code == "IDENTITY_CAPTURE_PLAN_BINDING_INVALID"


@pytest.mark.parametrize("field,value", [
    ("status", "consumed"), ("approved_by", "agent"), ("text", "approved"),
    ("timestamp", "2026-10-10T00:00:00Z"), ("base_commit", "wrong"),
    ("operation_count", 8), ("max_attempts_per_operation", 2), ("retry", "always"),
    ("stop_on_first_terminal_failure", False), ("model_downloads", 1),
    ("package_downloads", 1), ("dependency_installs", 1), ("provider_spend", True),
    ("training", True), ("deletions", 1), ("protected_engine_changes", 1),
    ("threshold_changes", 1), ("required_execution_identity", {}),
    ("operations", []), ("operator_approval", {}),
])
def test_direct_authorization_rejects_any_approval_change(field, value):
    plan, authorization = direct_contract()
    authorization[field] = value
    plan["identity_capture_authorization_binding"] = runner.identity_capture_authorization_binding(authorization)
    with pytest.raises(runner.FinalOperationError) as error:
        runner.validate_contract(plan, authorization)
    assert error.value.code == "IDENTITY_CAPTURE_AUTHORIZATION_INVALID"


def test_direct_binding_detects_other_content_changes_and_matches_external_digest():
    plan, authorization = direct_contract()
    assert plan["identity_capture_authorization_binding"]["authorization_canonical_sha256"] == (
        "a249dd96423bc035a2807f6ee4d3e493dd48ad11ab6a01ef39846f23c52cbb4c"
    )
    authorization["scope"] = "altered"
    with pytest.raises(runner.FinalOperationError) as error:
        runner.validate_contract(plan, authorization)
    assert error.value.code == "IDENTITY_CAPTURE_PLAN_BINDING_INVALID"


@pytest.mark.parametrize("field", ["base_commit", "proposal_sha256"])
def test_direct_binding_rejects_valid_but_different_hashes(field):
    plan, authorization = direct_contract()
    if field == "base_commit":
        authorization[field] = "0" * 40
    else:
        authorization["operator_approval"][field] = "0" * 64
    with pytest.raises(runner.FinalOperationError) as error:
        runner.validate_contract(plan, authorization)
    assert error.value.code == "IDENTITY_CAPTURE_PLAN_BINDING_INVALID"


@pytest.mark.parametrize("field", list(runner.IDENTITY_CAPTURE_REQUIRED_IDENTITY))
def test_direct_identity_flags_cannot_be_disabled_even_with_matching_digest(field):
    plan, authorization = direct_contract()
    authorization["required_execution_identity"][field] = False
    plan["identity_capture_authorization_binding"] = runner.identity_capture_authorization_binding(authorization)
    with pytest.raises(runner.FinalOperationError) as error:
        runner.validate_contract(plan, authorization)
    assert error.value.code == "IDENTITY_CAPTURE_AUTHORIZATION_INVALID"


@pytest.mark.parametrize("field", ["proposal_sha256", "verbatim", "approved_at"])
def test_direct_authorization_rejects_changed_approval_binding(field):
    plan, authorization = direct_contract()
    authorization["operator_approval"][field] = "wrong"
    with pytest.raises(runner.FinalOperationError) as error:
        runner.validate_contract(plan, authorization)
    assert error.value.code == "IDENTITY_CAPTURE_AUTHORIZATION_INVALID"


def test_consumed_legacy_authorization_is_not_direct_authorization():
    plan, _ = direct_contract()
    authorization = json.loads((BASE / "operator-authorization.json").read_text())
    with pytest.raises(runner.FinalOperationError) as error:
        runner.validate_contract(plan, authorization)
    assert error.value.code == "IDENTITY_CAPTURE_AUTHORIZATION_INVALID"
    authorization["schema_version"] = runner.IDENTITY_CAPTURE_AUTHORIZATION_SCHEMA
    with pytest.raises(runner.FinalOperationError) as error:
        runner.validate_contract(plan, authorization)
    assert error.value.code == "IDENTITY_CAPTURE_AUTHORIZATION_INVALID"


@pytest.mark.parametrize("change,code", [
    ("count", "OPERATION_COUNT_INVALID"),
    ("operation_id", "IDENTITY_CAPTURE_OPERATIONS_INVALID"),
    ("row", "IDENTITY_CAPTURE_OPERATIONS_INVALID"),
    ("operation", "IDENTITY_CAPTURE_OPERATIONS_INVALID"),
    ("order", "IDENTITY_CAPTURE_OPERATIONS_INVALID"),
    ("host_execution_authorized", "PLAN_PREFLIGHT_NOT_READY"),
    ("preflight_ready", "PLAN_PREFLIGHT_NOT_READY"),
    ("mode", "PLAN_PREFLIGHT_NOT_READY"),
    ("environment", "NATIVE_ENVIRONMENT_INVALID"),
    ("isolated_runtime", "RUNTIME_BINDING_ABSENT"),
])
def test_direct_authorization_preserves_plan_invariants(change, code):
    plan, authorization = direct_contract()
    if change == "count":
        plan["operations"].pop()
    elif change == "order":
        plan["operations"].reverse()
    elif change in {"operation_id", "row", "operation"}:
        plan["operations"][0][change] = "wrong"
    elif change == "environment":
        plan["operations"][0]["native"]["environment"] = {}
    elif change == "mode":
        plan[change] = "corrected_native_runtime_integration_local_only"
    else:
        plan[change] = False
    with pytest.raises(runner.FinalOperationError) as error:
        runner.validate_contract(plan, authorization)
    assert error.value.code == code


def test_direct_batch_passes_host_authorization_but_requires_runtime_and_identity(tmp_path):
    plan, authorization = direct_contract()
    queue = tmp_path / "queue.db"
    with pytest.raises(runner.FinalOperationError) as error:
        runner.run_batch(plan, authorization, ROOT, queue)
    assert error.value.code == "RUNTIME_STATE_REQUIRED"
    plan.pop("runner_repository_root", None)
    with pytest.raises(runner.FinalOperationError) as error:
        runner.run_batch(plan, authorization, ROOT, queue, runtime_state={})
    assert error.value.code == "EXECUTION_REPOSITORY_IDENTITY_UNPROVEN"
    assert not queue.exists()


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
