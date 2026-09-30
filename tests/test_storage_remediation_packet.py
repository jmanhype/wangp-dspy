from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import Any, Callable

import pytest

from scripts import build_storage_remediation_packet as builder


ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = ROOT / builder.DEFAULT_INPUT.relative_to(ROOT)
PACKET_PATH = ROOT / "datasets/runs/maestro-parity/storage-remediation-prep/local-plan.json"
REQUEST_PATH = ROOT / "datasets/runs/maestro-parity/storage-remediation-prep/operator-authorization-request.md"
COMMAND_RE = re.compile(r"(?im)^\s*(?:ssh|scp|rsync|curl|wget|mv|rm|mkdir)\b")


def _committed_input() -> dict[str, Any]:
    return json.loads(INPUT_PATH.read_text(encoding="utf-8"))


def _mutations(data: dict[str, Any]) -> dict[str, Callable[[], None]]:
    h3 = data["model_manifests"]["WD-bw0h"]["assets"]
    ltx = data["model_manifests"]["WD-28ac"]["assets"]
    return {
        "missing-schema-field": lambda: data.pop("schema_version"),
        "missing-nested-field": lambda: data["boundaries"]["wd_bw0h_failure"]["diagnostic"].pop("detail"),
        "wrong-h3-total": lambda: h3[0].update(size_bytes=h3[0]["size_bytes"] + 1),
        "wrong-ltx-total": lambda: ltx[0].update(size_bytes=ltx[0]["size_bytes"] + 1),
        "duplicate-destination": lambda: ltx[1].update(destination=ltx[0]["destination"]),
        "malformed-model-hash": lambda: h3[0].update(sha256=h3[0]["sha256"].upper()),
        "negative-size": lambda: ltx[0].update(size_bytes=-1),
        "zero-size": lambda: h3[2].update(size_bytes=0),
        "candidate-size-drift": lambda: data["superseded_h3_candidates"][0].update(
            size_bytes=data["superseded_h3_candidates"][0]["size_bytes"] + 1),
        "source-hash-mismatch": lambda: data["source_evidence"][0].update(sha256="0" * 64),
        "ambiguous-extra-field": lambda: h3[0].update(unexpected=True),
    }


def test_real_builder_success_is_deterministic_and_rewrites_only_two_outputs(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    assert builder.main(["--input", str(INPUT_PATH), "--output-dir", str(first)]) == 0
    assert builder.main(["--input", str(INPUT_PATH), "--output-dir", str(second)]) == 0
    assert sorted(item.name for item in first.iterdir()) == [
        "local-plan.json", "operator-authorization-request.md"
    ]
    assert (first / "local-plan.json").read_bytes() == (second / "local-plan.json").read_bytes() == PACKET_PATH.read_bytes()
    assert (first / "operator-authorization-request.md").read_bytes() == (
        second / "operator-authorization-request.md"
    ).read_bytes() == REQUEST_PATH.read_bytes()


def test_committed_plan_preserves_facts_labels_and_unknown_hashes() -> None:
    packet_text = PACKET_PATH.read_text(encoding="utf-8")
    plan = json.loads(packet_text)
    assert (plan["schema_version"], plan["snapshot_only"]) == (builder.PLAN_SCHEMA, True)
    assert (plan["wd_bw0h"]["asset_count"], plan["wd_bw0h"]["total_size_bytes"]) == (4, 53_594_702_510)
    assert (plan["wd_28ac"]["asset_count"], plan["wd_28ac"]["total_size_bytes"]) == (5, 23_701_298_279)
    assert [item["sha256"] for item in plan["superseded_h3_candidates"]] == [None, None]
    assert all(item["sha256_status"] == "unknown_requires_live_verification" for item in plan["superseded_h3_candidates"])
    disk = plan["recorded_disk_facts"]
    assert (disk["snapshot_only"], disk["stale"], disk["live_verified"]) == (True, True, False)
    projected = plan["projected_destination_free_bytes"]
    assert (projected["projected_free_bytes"], projected["live_prediction"]) == (62_153_920_217, False)
    readiness = plan["snapshot_readiness"]
    assert (readiness["snapshot_only"], readiness["stale"], readiness["live_prediction"], readiness["meets_doctor_minimum"], readiness["fits_exact_ltx_manifest"]) == (True, True, False, True, True)
    assert "/Users/" not in packet_text and "/private/tmp/" not in packet_text


def test_operator_request_separates_approvals_and_forbids_deletion() -> None:
    request = REQUEST_PATH.read_text(encoding="utf-8")
    packet = PACKET_PATH.read_text(encoding="utf-8")
    required = ("Decision A: reversible H3 offload, then a possible WD-bw0h retry",
                "Decision B: exact WD-28ac LTX batch", "exactly five LTX assets totaling",
                "23701298279 bytes", "Measure and record each identity and size before any relocation",
                "Fresh live verification must confirm candidate identity, size, destination",
                "verify every asset identity and hash, every destination", "Deletion is forbidden",
                "No host command is included")
    assert all(part in request for part in required)
    assert request.count("own approval") + request.count("separate") >= 2
    for text in (packet, request):
        assert not COMMAND_RE.search(text)
        assert "```" not in text


def test_builder_import_surface_has_no_network_or_process_modules() -> None:
    source = ROOT / "scripts/build_storage_remediation_packet.py"
    tree = ast.parse(source.read_text(encoding="utf-8"), filename=source.name)
    modules = {alias.name.split(".")[0] for node in ast.walk(tree)
               if isinstance(node, ast.Import) for alias in node.names}
    modules |= {node.module.split(".")[0] for node in ast.walk(tree)
                if isinstance(node, ast.ImportFrom) and node.module}
    assert modules <= {"__future__", "argparse", "json", "re", "sys", "pathlib", "typing"}


@pytest.mark.parametrize("case", sorted(_mutations(_committed_input())))
def test_invalid_input_fails_closed_before_replacing_output(tmp_path: Path, case: str) -> None:
    data = _committed_input()
    _mutations(data)[case]()
    input_path = tmp_path / "input.json"
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    sentinel = output_dir / "local-plan.json"
    sentinel.write_bytes(b"unchanged-sentinel")
    input_path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(builder.StorageRemediationInputError) as raised:
        builder.build_packet(input_path, output_dir)
    assert raised.value.diagnostic()["code"] == "STORAGE_REMEDIATION_INPUT_INVALID"
    assert sentinel.read_bytes() == b"unchanged-sentinel"
    assert sorted(item.name for item in output_dir.iterdir()) == ["local-plan.json"]


def test_typed_render_and_missing_input_failures_preserve_outputs(tmp_path: Path) -> None:
    output_dir = tmp_path / "output"
    with pytest.raises(builder.StorageRemediationInputError) as raised:
        builder.build_packet(tmp_path / "absent.json", output_dir)
    assert raised.value.diagnostic()["code"] == "STORAGE_REMEDIATION_INPUT_INVALID"
    assert not output_dir.exists()
    packet = builder.build_packet(INPUT_PATH, tmp_path)
    request = tmp_path / "operator-authorization-request.md"
    builder.write_operator_request(packet, request)
    request.write_bytes(b"unchanged-request")
    packet["schema_version"] = "invalid/schema"
    with pytest.raises(builder.StorageRemediationInputError):
        builder.write_operator_request(packet, request)
    assert request.read_bytes() == b"unchanged-request"
