from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

import scripts.prepare_ltx_operations as planner


ROOT = Path(__file__).resolve().parents[1]
RUN_DIR = ROOT / "datasets/runs/maestro-parity/ltx-dependency-terminalization"
GATE_DIR = RUN_DIR / "jev-gates/2026-10-03"
SCRIPT = ROOT / "scripts/prepare_ltx_operations.py"
PYTHON = Path(sys.executable)

EXPECTED_OPERATIONS = {
    "ltx25-outpaint": {
        "row": "LTX-2.5", "operation": "outpaint",
        "asset": "ltx-2.3-22b-ic-lora-outpaint.safetensors",
        "references": {"m7xw_create"},
    },
    "ltx25-repaint": {
        "row": "LTX-2.5", "operation": "repaint",
        "asset": "ltx-2.3-22b-ic-lora-in-outpainting-0.9.safetensors",
        "references": {"m7xw_create", "m7xw_repaint_mask"},
    },
    "ltx25-recast": {
        "row": "LTX-2.5", "operation": "recast",
        "asset": "ltx-2.3-22b-ic-lora-ingredients-0.9.safetensors",
        "references": {"m7xw_first_frame"},
    },
    "ltx25-upscale": {
        "row": "LTX-2.5", "operation": "upscale",
        "asset": "ltx-2.5-22b-ic-lora-pixel-spatial-upscaler-x2-1.0.safetensors",
        "references": {"m7xw_create"},
    },
    "ltx23-outpaint": {
        "row": "LTX-2.3", "operation": "outpaint",
        "asset": "ltx-2.3-22b-ic-lora-outpaint.safetensors",
        "references": {"osfm_control"},
    },
    "ltx23-recast": {
        "row": "LTX-2.3", "operation": "recast",
        "asset": "ltx-2.3-22b-ic-lora-ingredients-0.9.safetensors",
        "references": {"osfm_alternate_reference"},
    },
    "ltx23-upscale": {
        "row": "LTX-2.3", "operation": "upscale",
        "asset": "ltx-2.3-22b-dev_diffusion_model_quanto_int8.safetensors",
        "references": {"osfm_create"},
    },
}

SECRET_PATTERNS = {
    "openai": re.compile(rb"sk-(?:proj-)?[A-Za-z0-9_-]{20,}"),
    "api_key": re.compile(rb"(?i)api[_-]?key\s*[:=]\s*[\"']?[A-Za-z0-9_-]{16,}"),
    "bearer": re.compile(rb"(?i)authorization\s*[:=]\s*[\"']?bearer\s+[A-Za-z0-9._-]{16,}"),
    "signed_url": re.compile(rb"(?:Signature=|Policy=|X-Amz-Signature=|access_token=)", re.I),
}


def _run_plan(tmp_path: Path) -> dict[str, Any]:
    output = tmp_path / "operation-plan.json"
    result = subprocess.run([
        str(PYTHON), str(SCRIPT),
        "--repository-root", str(ROOT),
        "--output", str(output),
    ], text=True, capture_output=True, timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr
    return json.loads(output.read_text(encoding="utf-8"))


def test_gate3_and_gate4_no_secret_evidence_is_exact() -> None:
    summary = json.loads((GATE_DIR / "gate-3-4-evidence.json").read_text())
    gate3 = summary["gates"]["3"]
    gate4 = summary["gates"]["4"]

    assert gate3["decision"] == "GATHER_EVIDENCE"
    assert gate3["declared_snapshot_sha256"] == (
        "d1d7b81948f1d7f8e5fa93e8a48782f7d76e04b2b633121d4d17a5dbd46658fa"
    )
    assert gate4["decision"] == "CONTINUE"
    assert gate4["confidence"] == 0.78
    assert gate4["declared_snapshot_sha256"] == (
        "38e9b171448464138e18ba6b4987d43c48a1f65df9f3bfc3da628418b2c58500"
    )
    assert gate4["scope"] == "LOCAL_PHASE_B_PREPARATION_ONLY"
    assert summary["raw_api_key_scan"]["matches"] == 0
    for path in GATE_DIR.iterdir():
        if not path.is_file():
            continue
        raw = path.read_bytes()
        assert all(pattern.search(raw) is None for pattern in SECRET_PATTERNS.values()), path.name


def test_real_process_plan_maps_exactly_seven_operations(tmp_path: Path) -> None:
    plan = _run_plan(tmp_path)
    operations = {item["operation_id"]: item for item in plan["operations"]}

    assert set(operations) == set(EXPECTED_OPERATIONS)
    assert plan["scheduling"]["operation_count"] == 7
    for operation_id, expected in EXPECTED_OPERATIONS.items():
        item = operations[operation_id]
        assert (item["row"], item["operation"]) == (
            expected["row"], expected["operation"]
        )
        assert item["asset_id"] == expected["asset"]
        assert set(item["references"]) == expected["references"]
        template = ROOT / "datasets/runs/maestro-parity" / item["template"]
        assert template.is_file()
        assert item["native"]["template_sha256"] == hashlib.sha256(
            template.read_bytes()
        ).hexdigest()
        argv = item["native"]["argv"]
        assert argv[0].endswith("/venv/bin/python")
        assert argv[1].endswith("/wgp.py")
        assert argv[2:3] == ["--process"]
        assert argv[3] == item["native"]["settings_stage_path"]
        if operation_id != "ltx23-upscale":
            assert argv[4:8] == ["--profile", "3", "--attention", "sdpa"]
        assert argv[-2:] == ["--output-dir", item["native"]["argv"][-1]]


def test_plan_is_local_only_and_fails_only_on_qc_preflight(tmp_path: Path) -> None:
    plan = _run_plan(tmp_path)
    checks = {item["name"]: item for item in plan["preflight_checks"]}

    assert plan["mode"] == "local_preparation_only"
    assert plan["host_execution_authorized"] is False
    assert plan["preflight_ready"] is False
    assert set(name for name, item in checks.items() if not item["passed"]) == {
        "qc_healthy"
    }
    for operation in plan["operations"]:
        assert operation["status"] == "planned_not_executed"
        assert operation["queue"]["admission_state"] == "planned_not_admitted"
        assert operation["attempt_policy"] == {
            "max_attempts": 1,
            "retry": "never",
            "terminal_success": "verified_output",
            "terminal_failure": "typed_native_boundary",
            "inherit_evidence": False,
        }
    assert plan["scheduling"]["stop_policy"] == "stop_queue_on_first_terminal_failure"
    assert plan["scheduling"]["matrix_transition"] == "not_applied"


def test_plan_has_hash_media_visual_gate_checker_and_reviewer_expectations(
    tmp_path: Path,
) -> None:
    plan = _run_plan(tmp_path)
    for operation in plan["operations"]:
        evidence = operation["evidence_expectations"]
        assert evidence["output"].endswith(".mp4")
        assert evidence["sha256"].endswith(".sha256")
        assert evidence["ffprobe"].endswith(".ffprobe.json")
        assert set(evidence["visual"]) == {
            "phase-b-run/contact-sheet.jpg".replace(
                "phase-b-run", f"phase-b-run/{operation['operation_id']}"
            ),
            "phase-b-run/first-frame.png".replace(
                "phase-b-run", f"phase-b-run/{operation['operation_id']}"
            ),
        }
        assert evidence["checker"]["required_result"] == "PASS"
        assert evidence["reviewer"] == {"decision": "approved", "independent": True}
        gate_names = {item["name"] for item in evidence["objective_gates"]}
        assert {"valid_media", "nonempty_output", "distinct_hash"} <= gate_names
        if operation["operation"] == "upscale":
            assert "width_multiplier" in gate_names


def test_execute_cli_refuses_host_work_before_execution(tmp_path: Path) -> None:
    result = subprocess.run([
        str(PYTHON), str(SCRIPT),
        "--repository-root", str(ROOT),
        "--execute-operation", "ltx25-outpaint",
    ], text=True, capture_output=True, timeout=60)
    assert result.returncode == 2
    payload = json.loads(result.stdout)
    assert payload["code"] == "HOST_EXECUTION_NOT_AUTHORIZED"
    assert "local_phase_b_only=true" in payload["observed"]


def _matrix_maps() -> tuple[dict[str, str], dict[str, str]]:
    before = {f"{row}/{op}": "dependency_blocked" for row, op in planner.EXPECTED_CELLS}
    before["other/operation"] = "unsupported_on_this_hardware"
    after = {
        key: "host_run_verified" if key != "other/operation" else value
        for key, value in before.items()
    }
    return before, after


def test_matrix_validator_accepts_exactly_seven_owned_cells() -> None:
    before, after = _matrix_maps()
    changes = planner.validate_matrix_transition(before, after)
    assert len(changes) == 7
    assert {item["cell"] for item in changes} == {
        f"{row}/{op}" for row, op in planner.EXPECTED_CELLS
    }


@pytest.mark.parametrize(
    "mutation,code",
    [
        (lambda before, after: after.__setitem__("other/operation", "host_run_verified"), "UNOWNED_MATRIX_TRANSITION"),
        (lambda before, after: after.__setitem__("LTX-2.5/outpaint", "dependency_blocked"), "MATRIX_COUNT_INVALID"),
        (lambda before, after: after.__setitem__("LTX-2.5/outpaint", "unsupported"), "INVALID_NEW_MATRIX_STATUS"),
    ],
)
def test_matrix_validator_rejects_drift(
    mutation: Any, code: str
) -> None:
    before, after = _matrix_maps()
    mutation(before, after)
    with pytest.raises(planner.PhaseBPlanningError) as raised:
        planner.validate_matrix_transition(before, after)
    assert raised.value.code == code


def test_negative_preflight_paths_are_typed(tmp_path: Path) -> None:
    plan = _run_plan(tmp_path)
    facts = {
        "qc": {"healthy": False},
        "disk_free_bytes": 1,
        "gpu": {"memory_free_mib": 23978, "compute_apps": ["pid=1"]},
        "trees": {
            name: {"commit": "wrong", "status": "wrong"}
            for name in planner.EXPECTED_TREES
        },
        "models": {
            asset["id"]: {"sha256": "0" * 64, "size_bytes": 0}
            for asset in json.loads((RUN_DIR / "model-assets.json").read_text())["assets"]
        },
        "references": {
            name: {"path": name, "sha256": "0" * 64} for name in planner.REFERENCES
        },
    }
    manifest = json.loads((RUN_DIR / "model-assets.json").read_text())
    authorization = json.loads((RUN_DIR / "operator-authorization.json").read_text())
    gate = json.loads((GATE_DIR / "gate-3-4-evidence.json").read_text())
    checks = planner.evaluate_preflight(manifest, authorization, gate, facts)
    failed = {item.name for item in checks if not item.passed}
    assert {"qc_healthy", "disk_headroom", "gpu_idle"} <= failed
    assert {f"tree_{name}" for name in planner.EXPECTED_TREES} <= failed
    assert {f"model_{asset['id']}" for asset in manifest["assets"]} <= failed
    assert {f"reference_{name}" for name in planner.REFERENCES} <= failed
