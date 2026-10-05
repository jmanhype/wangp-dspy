from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

import scripts.prepare_ltx_operations as planner
import scripts.run_ltx_final_operations as runner


ROOT = Path(__file__).resolve().parents[1]
RUN_DIR = ROOT / "datasets/runs/maestro-parity/ltx-dependency-terminalization"
PLAN_PATH = RUN_DIR / "phase-b-preparation/final-operation-plan.json"
AUTH_PATH = RUN_DIR / "operator-authorization.json"
RUNTIME_STATE = RUN_DIR / "phase-b-preparation/isolated-runtime-state-2026-10-03.json"
PLAN_SCRIPT = ROOT / "scripts/prepare_ltx_operations.py"


def _contract() -> tuple[dict[str, Any], dict[str, Any]]:
    return (
        json.loads(PLAN_PATH.read_text(encoding="utf-8")),
        json.loads(AUTH_PATH.read_text(encoding="utf-8")),
    )


def test_prior_gate7_plan_is_preserved_but_not_corrected_executable() -> None:
    plan, authorization = _contract()

    assert plan["schema_version"] == "wangp-dspy.wd-28ac.phase-b-operation-plan/v1"
    assert plan["mode"] == "final_native_operations_authorized"
    assert plan["host_execution_authorized"] is True
    assert plan["preflight_ready"] is True
    assert plan["native_python"] == "/usr/bin/python3"
    assert len(plan["operations"]) == 7
    for operation in plan["operations"]:
        argv = operation["native"]["argv"]
        assert argv[0] == "/usr/bin/python3"
        assert argv[1] == f"{operation['source_root']}/wgp.py"
        assert argv[2:3] == ["--process"]
        assert argv[3] == operation["native"]["settings_stage_path"]
        if operation["operation_id"] != "ltx23-upscale":
            assert argv[4:8] == ["--profile", "3", "--attention", "sdpa"]
        assert argv[-2:] == [
            "--output-dir", str(Path(argv[-1]))
        ]
        assert operation["source_root"].endswith(
            "WD-m7xw" if operation["row"] == "LTX-2.5" else "WD-osfm"
        )
    with pytest.raises(runner.FinalOperationError) as raised:
        runner.validate_contract(plan, authorization)
    assert raised.value.code == "PLAN_SCHEMA_INVALID"


def test_final_runner_dry_run_and_host_guard(tmp_path: Path) -> None:
    plan = tmp_path / "corrected-plan.json"
    generated = subprocess.run([
        sys.executable, str(PLAN_SCRIPT),
        "--repository-root", str(ROOT),
        "--final",
        "--runtime-state", str(RUNTIME_STATE),
        "--output", str(plan),
    ], text=True, capture_output=True, timeout=60)
    assert generated.returncode == 0, generated.stdout + generated.stderr
    code = runner.main([
        "--plan", str(plan), "--authorization", str(AUTH_PATH),
        "--queue-db", "/tmp/wd28ac-final-dry-run.db",
    ])
    assert code == 0
    guarded = runner.main([
        "--plan", str(plan), "--authorization", str(AUTH_PATH),
        "--queue-db", "/tmp/should-not-exist.db", "--execute",
    ])
    assert guarded == 2


def _temporary_plan(tmp_path: Path) -> dict[str, Any]:
    plan, _ = _contract()
    plan = json.loads(json.dumps(plan))
    for operation in plan["operations"]:
        operation["source_root"] = str(tmp_path / operation["operation_id"])
        native_root = tmp_path / operation["operation_id"]
        operation["native"]["settings_stage_path"] = str(native_root / "settings.json")
        operation["native"]["log_path"] = str(native_root / "native.log")
        argv = operation["native"]["argv"]
        argv[1] = f"{operation['source_root']}/wgp.py"
        argv[3] = operation["native"]["settings_stage_path"]
        argv[-1] = str(native_root / "native-output")
    return plan


def test_prior_plan_cannot_enter_queue_batch() -> None:
    plan, authorization = _contract()
    with pytest.raises(runner.FinalOperationError) as raised:
        runner.run_batch(plan, authorization, ROOT, Path("/tmp/should-not-exist.db"))
    assert raised.value.code == "PLAN_SCHEMA_INVALID"
