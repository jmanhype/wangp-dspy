from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

import scripts.run_ltx_dependency_download as runner


ROOT = Path(__file__).resolve().parents[1]
RUN_DIR = ROOT / "datasets/runs/maestro-parity/ltx-dependency-terminalization"
MANIFEST = RUN_DIR / "model-assets.json"
AUTHORIZATION = RUN_DIR / "operator-authorization.json"
ASSET_ID = "ltx-2.3-22b-ic-lora-in-outpainting-0.9.safetensors"


class FakeCurl:
    def __init__(self, payload: bytes) -> None:
        self.payload = payload
        self.calls: list[list[str]] = []

    def __call__(self, argv: list[str]) -> runner.CurlOutcome:
        self.calls.append(list(argv))
        output = Path(argv[argv.index("--output") + 1])
        output.write_bytes(self.payload)
        return runner.CurlOutcome(
            returncode=0,
            stdout=(
                f"200\thttps://cdn.invalid/resolved\t{len(self.payload)}\t"
                "1\t2\n"
            ),
            stderr="",
        )


def _canonical(payload: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _temporary_pair(tmp_path: Path) -> tuple[Path, Path]:
    payload = b"exact payload"
    destination = tmp_path / "asset.bin"
    preserved_destination = tmp_path / "preserved.bin"
    manifest_payload = {
        "schema_version": "wangp-dspy.model-assets/v1",
        "source_revision": "6aa898aea1d968febdd834dc29e1dbef35340aeb",
        "assets": [
            {
                "id": "ltx-2.3-22b-ic-lora-ingredients-0.9.safetensors",
                "source_url": "https://example.invalid/preserved.bin",
                "sha256": "515e4e139001ac6282357a5b35372e42e98b3affd5fcc886a52242abeed19559",
                "xet_hash": "a" * 64,
                "size_bytes": 1_308_778_338,
                "license": "test license",
                "destination": str(preserved_destination),
            },
            {
                "id": ASSET_ID,
                "source_url": "https://example.invalid/asset.bin",
                "sha256": hashlib.sha256(payload).hexdigest(),
                "xet_hash": "b" * 64,
                "size_bytes": len(payload),
                "license": "test license",
                "destination": str(destination),
            },
        ],
    }
    authorization = {
        "status": "authorized",
        "retry_authorized": True,
        "manifest": {
            "path": "model-assets.json",
            "sha256": _canonical(manifest_payload),
            "total_download_bytes": len(payload),
        },
        "metadata_correction": {
            "repository_revision": "6aa898aea1d968febdd834dc29e1dbef35340aeb",
            "model_json_sha256": "33fb1cde721375e7b391aa2189b711965364ac0dfa403a48407ab0e8d1604505",
            "tree_json_sha256": "079d472c84a9fa68e29fab9a17896a079ea209f6c6bc8d3313a7601ee5e91baa",
        },
        "jev_phase_a_authorization": {
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
        },
        "corrected_retry_approval": {
            "verbatim": "Yes",
            "approved_by": "operator",
            "timestamp": "2026-10-03T13:11:01Z",
            "corrected_manifest_sha256": _canonical(manifest_payload),
            "preserved_first_partial": {
                "asset_id": "ltx-2.3-22b-ic-lora-ingredients-0.9.safetensors",
                "path": f"{preserved_destination}.WD-28ac.partial",
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
        },
        "assets": [{
            "id": "ltx-2.3-22b-ic-lora-ingredients-0.9.safetensors",
            "sha256": "515e4e139001ac6282357a5b35372e42e98b3affd5fcc886a52242abeed19559",
            "xet_hash": "a" * 64,
            "cells": [{"row": "LTX-2.3", "operation": "recast"}],
        }, {
            "id": ASSET_ID,
            "sha256": hashlib.sha256(payload).hexdigest(),
            "xet_hash": "b" * 64,
            "cells": [{"row": "LTX-2.3", "operation": "outpaint"}],
        }],
    }
    manifest = tmp_path / "assets.json"
    auth = tmp_path / "authorization.json"
    manifest.write_text(json.dumps(manifest_payload), encoding="utf-8")
    auth.write_text(json.dumps(authorization), encoding="utf-8")
    return manifest, auth


def test_current_repair_plans_one_curl_and_zero_network_requests() -> None:
    controller = runner.load_controller(MANIFEST, AUTHORIZATION)
    plan = controller.plan(ASSET_ID)

    assert plan["mode"] == "dry_run"
    assert plan["retry_authorized"] is True
    assert plan["request_accounting"] == {
        "curl_invocations": 0,
        "declared_request_count": 0,
        "undeclared_request_count": 0,
        "url_effective_probe_request_count": 0,
        "redirect_count": None,
        "network_request_count": 0,
    }
    source_urls = [
        value for index, value in enumerate(plan["curl_argv"])
        if index > 0 and plan["curl_argv"][index - 1] != "--write-out"
        and value.startswith("https://")
    ]
    assert source_urls == [plan["source_url"]]


def test_one_declared_curl_records_effective_url_without_second_get(
    tmp_path: Path,
) -> None:
    manifest, auth = _temporary_pair(tmp_path)
    controller = runner.load_controller(manifest, auth)
    fake = FakeCurl(b"exact payload")

    report = controller.execute(ASSET_ID, runner=fake)

    assert len(fake.calls) == 1
    assert report["url_effective"] == "https://cdn.invalid/resolved"
    assert report["url_effective_source"] == "declared_curl_write_out"
    assert report["file_sha256_match"] is True
    assert report["promoted"] is True
    assert report["request_accounting"] == {
        "curl_invocations": 1,
        "declared_request_count": 1,
        "undeclared_request_count": 0,
        "url_effective_probe_request_count": 0,
        "redirect_count": 1,
        "network_request_count": 2,
    }

    def no_call(_: list[str]) -> runner.CurlOutcome:
        raise AssertionError("second network invocation attempted")

    with pytest.raises(runner.LTXDownloadControlError) as raised:
        controller.execute(ASSET_ID, runner=no_call)
    assert raised.value.code == "DECLARED_REQUEST_BUDGET_EXHAUSTED"
    assert len(fake.calls) == 1


def test_curl_85_num_redirects_parse_and_accounting_are_same_invocation(
    tmp_path: Path,
) -> None:
    manifest, auth = _temporary_pair(tmp_path)
    controller = runner.load_controller(manifest, auth)
    fake = FakeCurl(b"exact payload")

    report = controller.execute(ASSET_ID, runner=fake)

    assert runner.WRITE_OUT == (
        "%{http_code}\t%{url_effective}\t%{size_download}\t"
        "%{num_redirects}\t%{num_connects}\n"
    )
    assert "%{redirect_count}" not in runner.WRITE_OUT
    assert len(fake.calls) == 1
    assert report["url_effective_source"] == "declared_curl_write_out"
    assert report["request_accounting"] == {
        "curl_invocations": 1,
        "declared_request_count": 1,
        "undeclared_request_count": 0,
        "url_effective_probe_request_count": 0,
        "redirect_count": 1,
        "network_request_count": 2,
    }
    source_urls = [
        value for index, value in enumerate(fake.calls[0])
        if index > 0 and fake.calls[0][index - 1] != "--write-out"
        and value.startswith("https://")
    ]
    assert source_urls == [json.loads(manifest.read_text())["assets"][1]["source_url"]]


def test_hash_mismatch_preserves_partial_without_promotion(
    tmp_path: Path,
) -> None:
    manifest, auth = _temporary_pair(tmp_path)
    controller = runner.load_controller(manifest, auth)
    fake = FakeCurl(b"wrong payload")

    report = controller.execute(ASSET_ID, runner=fake)

    assert report["size_match"] is True
    assert report["file_sha256_match"] is False
    assert report["promoted"] is False
    assert Path(report["curl_argv"][report["curl_argv"].index("--output") + 1]).is_file()
    destination = json.loads(manifest.read_text())["assets"][0]["destination"]
    assert not Path(destination).exists()


def test_invalid_curl_accounting_field_preserves_partial_before_promotion(
    tmp_path: Path,
) -> None:
    manifest, auth = _temporary_pair(tmp_path)
    controller = runner.load_controller(manifest, auth)

    class InvalidAccountingCurl:
        def __init__(self) -> None:
            self.calls = 0

        def __call__(self, argv: list[str]) -> runner.CurlOutcome:
            self.calls += 1
            Path(argv[argv.index("--output") + 1]).write_bytes(b"exact payload")
            return runner.CurlOutcome(
                returncode=0,
                stdout=f"200\thttps://cdn.invalid/resolved\t{len(b'exact payload')}\t\t2\n",
                stderr="",
            )

    fake = InvalidAccountingCurl()
    with pytest.raises(runner.LTXDownloadControlError) as raised:
        controller.execute(ASSET_ID, runner=fake)
    assert raised.value.code == "CURL_ACCOUNTING_OUTPUT_INVALID"
    assert fake.calls == 1
    assert "%{num_redirects}" in runner.WRITE_OUT
    assert "%{redirect_count}" not in runner.WRITE_OUT
    destination = json.loads(manifest.read_text())["assets"][1]["destination"]
    assert Path(f"{destination}.WD-28ac.partial").is_file()
    assert not Path(destination).exists()


def test_exact_verified_final_resume_fails_before_network_or_mutation() -> None:
    controller = runner.load_controller(MANIFEST, AUTHORIZATION)
    for asset_id in (
        "ltx-2.3-22b-ic-lora-ingredients-0.9.safetensors",
        "ltx-2.3-22b-ic-lora-outpaint.safetensors",
    ):
        with pytest.raises(runner.LTXDownloadControlError) as raised:
            controller.plan(asset_id)
        assert raised.value.code == "ASSET_OUTSIDE_CORRECTED_RETRY_SCOPE"


def test_loader_rejects_sha256_xet_conflation(tmp_path: Path) -> None:
    manifest, auth = _temporary_pair(tmp_path)
    payload = json.loads(manifest.read_text())
    payload["assets"][0]["sha256"] = payload["assets"][0]["xet_hash"]
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    authorization = json.loads(auth.read_text())
    authorization["manifest"]["sha256"] = _canonical(payload)
    authorization["assets"][0]["sha256"] = payload["assets"][0]["xet_hash"]
    auth.write_text(json.dumps(authorization), encoding="utf-8")

    with pytest.raises(runner.LTXDownloadControlError) as raised:
        runner.load_controller(manifest, auth)
    assert raised.value.code == "HASH_SEMANTICS_CONFLATED"
