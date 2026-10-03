from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

import pytest

import scripts.prepare_ltx_operations as planner
import scripts.run_ltx_final_operations as runner


ROOT = Path(__file__).resolve().parents[1]
RUN_DIR = ROOT / "datasets/runs/maestro-parity/ltx-dependency-terminalization"
PLAN_PATH = RUN_DIR / "phase-b-preparation/final-operation-plan.json"
AUTH_PATH = RUN_DIR / "operator-authorization.json"


def _contract() -> tuple[dict[str, Any], dict[str, Any]]:
    return (
        json.loads(PLAN_PATH.read_text(encoding="utf-8")),
        json.loads(AUTH_PATH.read_text(encoding="utf-8")),
    )


def test_gate7_contract_and_exact_command_mapping() -> None:
    plan, authorization = _contract()
    runner.validate_contract(plan, authorization)

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


def test_final_runner_dry_run_and_host_guard() -> None:
    code = runner.main([
        "--plan", str(PLAN_PATH), "--authorization", str(AUTH_PATH),
        "--queue-db", "/tmp/wd28ac-final-dry-run.db",
    ])
    assert code == 0
    guarded = runner.main([
        "--plan", str(PLAN_PATH), "--authorization", str(AUTH_PATH),
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


def test_real_job_queue_runs_each_once_and_stops_on_first_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan = _temporary_plan(tmp_path)
    authorization = json.loads(AUTH_PATH.read_text())
    template_root = ROOT
    calls: list[str] = []

    def executor(argv: list[str], cwd: str, timeout: int, log: str) -> int:
        operation_id = Path(cwd).name
        calls.append(operation_id)
        Path(log).write_text("native log\n", encoding="utf-8")
        output_dir = Path(argv[argv.index("--output-dir") + 1])
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "output.mp4").write_bytes(b"output")
        return 1 if operation_id == "ltx25-repaint" else 0

    monkeypatch.setattr(runner, "_snapshot", lambda operation: {"snapshot": True})
    monkeypatch.setattr(
        runner, "_collect_evidence",
        lambda operation, native: {"output": native.output_path, "objective": True},
    )
    result = runner.run_batch(
        plan, authorization, template_root, tmp_path / "queue.db", executor=executor
    )

    assert result["status"] == "failed_closed"
    assert result["terminal_operation"] == "ltx25-repaint"
    assert calls == ["ltx25-outpaint", "ltx25-repaint"]
    summary = json.loads((tmp_path / "queue-summary.json").read_text())
    assert summary["states"]["rendered_pending_qc"] == [
        result["operations"][0]["durable_job_id"]
    ]
    assert summary["states"]["failed"] == [
        result["operations"][1]["durable_job_id"]
    ]
    assert summary["states"]["pending"] == []
    assert len(calls) == 2
