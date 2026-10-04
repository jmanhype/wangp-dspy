from __future__ import annotations

import copy
import hashlib
import json
import re
import subprocess
import sys
from os import pathsep
from pathlib import Path
from typing import Any

import pytest

import scripts.prepare_ltx_operations as planner
import scripts.run_ltx_final_operations as runner


ROOT = Path(__file__).resolve().parents[1]
RUN_DIR = ROOT / "datasets/runs/maestro-parity/ltx-dependency-terminalization"
GATE_DIR = RUN_DIR / "jev-gates/2026-10-03"
GATE14_PREFLIGHT_PATH = (
    RUN_DIR / "jev-gates/2026-10-04/gate-14-fresh-host-preflight.json"
)
GATE15_DIR = RUN_DIR / "jev-gates/2026-10-04"
GATE15_PREFLIGHT_PATH = GATE15_DIR / "gate-15-fresh-host-preflight.json"
GATE15_STATE_PATH = (
    RUN_DIR / "phase-b-preparation/isolated-runtime-state-2026-10-04-gate15.json"
)
AUTH_PATH = RUN_DIR / "operator-authorization.json"
CONTRACT_PATH = RUN_DIR / "phase-b-preparation/isolated-runtime-contract.json"
STATE_PATH = RUN_DIR / "phase-b-preparation/isolated-runtime-state-2026-10-03.json"
CORRECTED_PLAN_PATH = RUN_DIR / "phase-b-preparation/corrected-retry-plan.json"
OLD_PLAN_PATH = RUN_DIR / "phase-b-preparation/final-operation-plan.json"
OLD_BOUNDARY_PATH = RUN_DIR / "final-native-operations/terminal-boundary/boundary.json"
PLAN_SCRIPT = ROOT / "scripts/prepare_ltx_operations.py"
EXPECTED_NATIVE_PYTHONPATH = pathsep.join((
    runner.ISOLATED_REMBG_DIRECTORY,
    runner.ISOLATED_RUNTIME_DIRECTORY,
    runner.COMFYUI_SITE_PACKAGES,
))

SECRET_PATTERNS = (
    re.compile(rb"sk-(?:proj-)?[A-Za-z0-9_-]{20,}"),
    re.compile(rb"(?i)api[_-]?key\s*[:=]"),
    re.compile(rb"(?i)authorization\s*[:=]\s*[\"']?bearer"),
    re.compile(rb"(?:Signature=|Policy=|X-Amz-Signature=|access_token=)", re.I),
)


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _runtime_state(*, fresh: bool = False) -> dict[str, Any]:
    value = _read(STATE_PATH)
    value["fresh_host_recheck"] = fresh
    value["separate_fresh_host_gate_required"] = not fresh
    return value


def _corrected_plan(tmp_path: Path) -> dict[str, Any]:
    output = tmp_path / "corrected-retry-plan.json"
    result = subprocess.run([
        sys.executable, str(PLAN_SCRIPT),
        "--repository-root", str(ROOT),
        "--final",
        "--runtime-state", str(STATE_PATH),
        "--output", str(output),
    ], text=True, capture_output=True, timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr
    return _read(output)


def _portable_operation(operation: dict[str, Any]) -> dict[str, Any]:
    """Remove only the checkout-dependent absolute reference prefix."""
    portable = json.loads(json.dumps(operation))
    for reference in portable["references"].values():
        reference["resolved_path"] = str(
            Path("datasets/runs/maestro-parity")
            / reference["story"]
            / reference["path"]
        )
    return portable


def test_gate15_host_authorization_and_fresh_state_are_exact() -> None:
    decision = _read(GATE15_DIR / "wd28ac-jev-decision-15.json")
    snapshot = _read(GATE15_DIR / "wd28ac-jev-snapshot-15.json")
    authorization = _read(AUTH_PATH)
    plan = _read(CORRECTED_PLAN_PATH)
    state = _read(GATE15_STATE_PATH)
    preflight = _read(GATE15_PREFLIGHT_PATH)

    assert decision["decision"].upper() == "CONTINUE"
    assert decision["snapshot_sha256"] == (
        "2d80ae6623256e56223a47c359b3e754a9cecffc8c768063a37c155cf88b2b89"
    )
    assert decision["trace_sha256"] == (
        "60a03fdb467c77fe512619777628b2c40832598f4fe3ab7c1955f1ba5461b8cd"
    )
    assert snapshot["metadata"]["fresh_preflight_sha256"] == (
        "26b1f0c232fdec66f09eb28b45f3beed55e8f3006b166f7c118d0a73d0ae5ca3"
    )

    gate = authorization["jev_corrected_native_retry_host_authorization"]
    assert gate == runner.EXPECTED_GATE15_HOST_AUTHORIZATION
    assert gate["gate"] == 15
    assert gate["snapshot_sha256"] == decision["snapshot_sha256"]
    assert gate["trace_sha256"] == decision["trace_sha256"]
    assert gate["fresh_preflight_sha256"] == (
        snapshot["metadata"]["fresh_preflight_sha256"]
    )
    assert [(item["row"], item["operation"]) for item in gate["operations"]] == [
        ("LTX-2.5", "outpaint"),
        ("LTX-2.5", "repaint"),
        ("LTX-2.5", "recast"),
        ("LTX-2.5", "upscale"),
        ("LTX-2.3", "outpaint"),
        ("LTX-2.3", "recast"),
        ("LTX-2.3", "upscale"),
    ]
    assert gate["max_attempts_per_operation"] == 1
    assert gate["stop_on_first_terminal_failure"] is True
    assert gate["judge_start_policy"] == "governed_judge_ctl_only_if_required"
    assert gate["judge_control_path"] == (
        "/home/straughter/marathon/bin/judge_ctl.sh"
    )

    assert state["evidence_source"]["path"] == (
        "jev-gates/2026-10-04/gate-15-fresh-host-preflight.json"
    )
    assert state["evidence_source"]["sha256"] == (
        "26b1f0c232fdec66f09eb28b45f3beed55e8f3006b166f7c118d0a73d0ae5ca3"
    )
    assert state["fresh_host_recheck"] is True
    assert state["separate_fresh_host_gate_required"] is False
    for key in (
        "directory", "exists", "regular_directory", "symlink", "payload",
        "system_mmgp_present",
    ):
        assert state[key] == preflight["isolated_runtime"][key]
    fresh_import = preflight["isolated_runtime"]["isolated_import"]
    assert state["isolated_import"] == {
        **fresh_import,
        "python": fresh_import["argv"][0],
        **fresh_import["payload"],
    }
    assert runner.validate_runtime_state(state)["status"] == "passed"

    assert plan["mode"] == "corrected_native_operations_authorized"
    assert plan["host_execution_authorized"] is True
    assert plan["preflight_ready"] is True
    assert plan["host_authorization_binding"] == {
        "gate": 15,
        "snapshot_sha256": decision["snapshot_sha256"],
        "trace_sha256": decision["trace_sha256"],
        "fresh_preflight_sha256": snapshot["metadata"]["fresh_preflight_sha256"],
    }
    runner.validate_contract(plan, authorization)

    for key, bad in (
        ("gate", 14),
        ("snapshot_sha256", "0" * 64),
        ("trace_sha256", "0" * 64),
        ("fresh_preflight_sha256", "0" * 64),
        ("host_execution_authorized", False),
        ("max_attempts_per_operation", 2),
        ("stop_on_first_terminal_failure", False),
    ):
        tampered = json.loads(json.dumps(authorization))
        tampered["jev_corrected_native_retry_host_authorization"][key] = bad
        with pytest.raises(runner.FinalOperationError) as raised:
            runner.validate_contract(plan, tampered)
        assert raised.value.code == "HOST_GATE_AUTHORIZATION_INVALID"

    missing = json.loads(json.dumps(authorization))
    del missing["jev_corrected_native_retry_host_authorization"]
    with pytest.raises(runner.FinalOperationError) as raised:
        runner.validate_contract(plan, missing)
    assert raised.value.code == "HOST_GATE_AUTHORIZATION_INVALID"

    for path in (
        GATE15_DIR / "wd28ac-jev-snapshot-15.json",
        GATE15_DIR / "wd28ac-jev-decision-15.json",
        GATE15_DIR / "wd28ac-jev-trace-15.jsonl",
        GATE15_PREFLIGHT_PATH,
        GATE15_STATE_PATH,
        AUTH_PATH,
    ):
        for pattern in SECRET_PATTERNS:
            assert pattern.search(path.read_bytes()) is None, path


def test_gate12_and_corrected_native_retry_authorizations_are_exact() -> None:
    gate = _read(GATE_DIR / "gate-12-evidence.json")
    authorization = _read(AUTH_PATH)

    assert gate["gate"] == 12
    assert gate["decision"] == "CONTINUE"
    assert gate["scope"] == "LOCAL_NATIVE_RUNTIME_INTEGRATION_ONLY"
    assert gate["confidence"] == 0.85
    assert gate["constraint_risk"] == 0.37
    assert gate["missing_evidence_score"] == 1.45
    assert gate["declared_snapshot_sha256"] == (
        "09edc9f0a470777a3871dcf8336e5862b219b92c670e2bf7291f2e65d74b8ddc"
    )
    assert gate["declared_trace_sha256"] == (
        "0a79c7f332add517cb079f60fb12594b7f8184939680c35b004aaccc7c462341"
    )
    assert gate["stop_before"] == "separate_jev_corrected_host_retry_gate"
    operator = authorization["operator_corrected_native_retry_authorization"]
    local = authorization["jev_local_native_runtime_integration_authorization"]
    assert operator["decision"] == "Authorized"
    assert operator["separate_host_retry_gate_required"] is True
    assert local["host_contact_authorized"] is False
    assert local["native_retry_authorized"] is False
    for path in (
        GATE_DIR / "wd28ac-jev-snapshot-12.json",
        GATE_DIR / "wd28ac-jev-decision-12.json",
        GATE_DIR / "wd28ac-jev-trace-12.jsonl",
        GATE_DIR / "gate-12-evidence.json",
        AUTH_PATH,
    ):
        for pattern in SECRET_PATTERNS:
            assert pattern.search(path.read_bytes()) is None, path


def test_corrected_plan_binds_runtime_environment_and_new_namespace(
    tmp_path: Path,
) -> None:
    plan = _corrected_plan(tmp_path)
    committed = _read(CORRECTED_PLAN_PATH)
    runtime = plan["isolated_runtime"]
    checks = {item["name"]: item for item in plan["preflight_checks"]}

    runner.validate_contract(committed, _read(AUTH_PATH))
    assert committed["schema_version"] == plan["schema_version"]
    assert committed["mode"] == "corrected_native_operations_authorized"
    assert committed["host_execution_authorized"] is True
    assert committed["preflight_ready"] is True
    assert committed["runtime_identity_ready"] == plan["runtime_identity_ready"]
    assert committed["isolated_runtime"] == plan["isolated_runtime"]
    assert committed["prior_boundary"] == plan["prior_boundary"]
    assert committed["scheduling"] == plan["scheduling"]
    assert all(item["passed"] for item in committed["preflight_checks"])
    for committed_operation, generated_operation in zip(
        committed["operations"], plan["operations"]
    ):
        assert _portable_operation(committed_operation) == _portable_operation(
            generated_operation
        )
        for reference in generated_operation["references"].values():
            assert Path(reference["resolved_path"]).is_file()

    assert plan["schema_version"] == (
        "wangp-dspy.wd-28ac.corrected-native-retry-plan/v1"
    )
    assert plan["mode"] == "corrected_native_runtime_integration_local_only"
    assert plan["host_execution_authorized"] is False
    assert plan["runtime_identity_ready"] is True
    assert plan["preflight_ready"] is False
    assert checks["isolated_mmgp_runtime_path"]["passed"] is True
    assert checks["isolated_mmgp_import_path_version"]["passed"] is True
    assert checks["isolated_mmgp_payload_identity"]["passed"] is True
    assert checks["system_mmgp_absent"]["passed"] is True
    assert checks["corrected_host_retry_gate"]["passed"] is False
    assert runtime["directory"] == (
        "/home/straughter/wd-28ac-final-gate7-20261003/runtime/mmgp-3.7.14"
    )
    assert runtime["payload"]["file_count"] == 12
    assert runtime["payload"]["canonical_sha256"] == (
        "d39fa7a56869387410d299ab139eb724e3be3f04055fd5d0da69d32dec9f309b"
    )
    for operation in plan["operations"]:
        native = operation["native"]
        assert native["environment"] == {
            "PYTHONUNBUFFERED": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTORCH_ALLOC_CONF": "expandable_segments:True",
            "HF_HUB_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1",
            "PYTHONPATH": EXPECTED_NATIVE_PYTHONPATH,
        }
        assert "phase-b-gate5" not in native["settings_stage_path"]
        assert "phase-b-gate5" not in native["log_path"]
        assert "phase-b-gate20-corrected-retry" in native["settings_stage_path"]
        assert operation["queue"]["retry_id"] == "corrected-retry-attempt-3"
        assert operation["queue"]["job_id"].endswith(
            "-corrected-retry-attempt-3"
        )
        assert operation["status"] == "planned_not_executed"
        assert operation["queue"]["admission_state"] == "planned_not_admitted"
    assert plan["prior_boundary"]["path"] == (
        "final-native-operations/terminal-boundary/boundary.json"
    )
    assert plan["prior_boundary"]["overwritable"] is False


def test_runtime_preflight_rejects_stale_path_import_payload_or_system_drift(
) -> None:
    valid = _runtime_state(fresh=True)
    assert runner.validate_runtime_state(valid)["status"] == "passed"

    stale = _runtime_state(fresh=False)
    with pytest.raises(runner.FinalOperationError) as raised:
        runner.validate_runtime_state(stale, require_fresh=True)
    assert raised.value.code == "RUNTIME_PREFLIGHT_STALE"

    wrong_path = _runtime_state(fresh=True)
    wrong_path["directory"] = "/tmp/wrong-mmgp"
    wrong_import = _runtime_state(fresh=True)
    wrong_import["isolated_import"]["path"] = "/tmp/wrong/mmgp/__init__.py"
    wrong_version = _runtime_state(fresh=True)
    wrong_version["isolated_import"]["metadata_version"] = "3.7.15"
    payload_drift = _runtime_state(fresh=True)
    payload_drift["payload"]["inventory"] = payload_drift["payload"]["inventory"][:-1]
    system = _runtime_state(fresh=True)
    system["system_mmgp_present"] = True
    missing = _runtime_state(fresh=True)
    missing["exists"] = False

    cases = (
        (wrong_path, "RUNTIME_PATH_INVALID"),
        (wrong_import, "RUNTIME_IMPORT_PATH_INVALID"),
        (wrong_version, "RUNTIME_IMPORT_VERSION_INVALID"),
        (payload_drift, "RUNTIME_PAYLOAD_DRIFT"),
        (system, "SYSTEM_MMGP_PRESENT"),
        (missing, "RUNTIME_PATH_INVALID"),
    )
    for state, code in cases:
        with pytest.raises(runner.FinalOperationError) as raised:
            runner.validate_runtime_state(state, require_fresh=True)
        assert raised.value.code == code


def test_gate14_runtime_contract_derives_canonical_from_inventory(
    tmp_path: Path,
) -> None:
    preflight = _read(GATE14_PREFLIGHT_PATH)
    fresh_payload = preflight["isolated_runtime"]["payload"]
    fresh_inventory = fresh_payload["inventory"]
    assert [item["path"] for item in fresh_inventory] == sorted(
        item["path"] for item in fresh_inventory
    )
    assert runner._canonical_payload_hash(fresh_inventory) == (
        fresh_payload["canonical_sha256"]
    )

    contract = _read(CONTRACT_PATH)
    contract_payload = contract["expected_payload"]
    contract_inventory = contract_payload["inventory"]
    derived = runner._canonical_payload_hash(contract_inventory)
    assert derived == fresh_payload["canonical_sha256"]
    assert contract_payload["canonical_sha256"] == derived
    assert contract_inventory == fresh_inventory
    assert runner.ISOLATED_RUNTIME_PAYLOAD_SHA256 == derived

    plan = _corrected_plan(tmp_path)
    expected_payload = plan["isolated_runtime"]["expected_payload"]
    top_level = next(
        item for item in expected_payload["inventory"]
        if item["path"] == "mmgp-3.7.14.dist-info/top_level.txt"
    )
    top_level["sha256"] = "0" * 64
    assert expected_payload["canonical_sha256"] == derived
    with pytest.raises(runner.FinalOperationError) as raised:
        runner.validate_contract(plan, _read(AUTH_PATH))
    assert raised.value.code == "RUNTIME_BINDING_ABSENT"


def test_runner_contract_requires_v2_runtime_and_records_environment(
    tmp_path: Path,
) -> None:
    plan = _corrected_plan(tmp_path)
    authorization = _read(AUTH_PATH)
    runner.validate_contract(plan, authorization)

    environment = runner.build_native_environment(plan["operations"][0])
    assert environment["PYTHONPATH"] == EXPECTED_NATIVE_PYTHONPATH
    assert environment["HF_HUB_OFFLINE"] == "1"
    assert environment["TRANSFORMERS_OFFLINE"] == "1"
    assert environment["PYTORCH_ALLOC_CONF"] == "expandable_segments:True"
    assert environment["PYTHONDONTWRITEBYTECODE"] == "1"

    stale = _read(OLD_PLAN_PATH)
    with pytest.raises(runner.FinalOperationError) as raised:
        runner.validate_contract(stale, authorization)
    assert raised.value.code in {"PLAN_SCHEMA_INVALID", "RUNTIME_BINDING_ABSENT"}


def test_corrected_run_namespace_rejects_paths_outside_gate20_root() -> None:
    plan = _read(CORRECTED_PLAN_PATH)
    authorization = _read(AUTH_PATH)

    for field in ("settings_stage_path", "log_path"):
        old_filename = "settings.json" if field == "settings_stage_path" else "native.log"
        invalid = copy.deepcopy(plan)
        invalid["operations"][0]["native"][field] = (
            "/home/straughter/wd-28ac-run/phase-b-gate12-corrected-retry/"
            "ltx25-outpaint/" + old_filename
        )
        with pytest.raises(runner.FinalOperationError) as raised:
            runner.validate_contract(invalid, authorization)
        assert raised.value.code == "CORRECTED_RUN_NAMESPACE_INVALID"


def test_corrected_retry_cannot_run_or_touch_prior_boundary_before_gate13(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan = _corrected_plan(tmp_path)
    authorization = _read(AUTH_PATH)
    queue_db = tmp_path / "new-native-queue.db"
    prior_hash = hashlib.sha256(OLD_BOUNDARY_PATH.read_bytes()).hexdigest()
    monkeypatch.setattr(
        runner, "validate_runtime_state",
        lambda *args, **kwargs: _runtime_state(fresh=True),
    )

    with pytest.raises(runner.FinalOperationError) as raised:
        runner.run_batch(
            plan, authorization, ROOT, queue_db,
            runtime_state=_runtime_state(fresh=True),
        )
    assert raised.value.code == "CORRECTED_HOST_RETRY_NOT_AUTHORIZED"
    assert not queue_db.exists()
    assert hashlib.sha256(OLD_BOUNDARY_PATH.read_bytes()).hexdigest() == prior_hash
    assert hashlib.sha256(OLD_PLAN_PATH.read_bytes()).hexdigest() == (
        "01a3a3195144d0d46585fe07e76860d5059dbbbcaf8377ec95c35f52936a5ab4"
    )


def test_fresh_runtime_and_environment_capture_stop_on_first_terminal_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan = _read(CORRECTED_PLAN_PATH)
    authorization = _read(AUTH_PATH)
    runtime_state = _read(GATE15_STATE_PATH)
    monkeypatch.setattr(
        runner, "CORRECTED_NATIVE_RUN_ROOT", str(tmp_path / "native")
    )
    for operation in plan["operations"]:
        source = tmp_path / operation["operation_id"]
        source.mkdir()
        operation["source_root"] = str(source)
        native_root = tmp_path / "native" / operation["operation_id"]
        operation["native"]["settings_stage_path"] = str(native_root / "settings.json")
        operation["native"]["log_path"] = str(native_root / "native.log")
        operation["native"]["argv"][1] = f"{source}/wgp.py"
        operation["native"]["argv"][3] = operation["native"]["settings_stage_path"]
        operation["native"]["argv"][-1] = str(native_root / "native-output")
    calls: list[dict[str, Any]] = []

    def executor(argv: list[str], cwd: str, timeout: int, log: str) -> int:
        operation_id = Path(cwd).name
        calls.append({
            "operation_id": operation_id,
            "argv": list(argv),
            "cwd": cwd,
            "log": log,
        })
        Path(log).write_text("native log\n", encoding="utf-8")
        output = Path(argv[argv.index("--output-dir") + 1])
        output.mkdir(parents=True, exist_ok=True)
        (output / "output.mp4").write_bytes(b"output")
        return 1 if operation_id == "ltx25-repaint" else 0

    monkeypatch.setattr(runner, "_snapshot", lambda operation: {"snapshot": True})
    monkeypatch.setattr(
        runner, "_collect_evidence",
        lambda operation, native: {"output": native.output_path, "objective": True},
    )
    result = runner.run_batch(
        plan, authorization, ROOT, tmp_path / "queue.db",
        runtime_state=runtime_state, executor=executor,
    )

    assert result["status"] == "failed_closed"
    assert result["terminal_operation"] == "ltx25-repaint"
    assert [item["operation_id"] for item in calls] == [
        "ltx25-outpaint", "ltx25-repaint"
    ]
    assert all(
        item["environment"]["PYTHONPATH"] == EXPECTED_NATIVE_PYTHONPATH
        for item in result["operations"]
    )
    summary = _read(tmp_path / "queue-summary.json")
    assert summary["states"]["pending"] == []
    assert summary["states"]["failed"] == [
        result["operations"][1]["durable_job_id"]
    ]


def test_contract_rejects_native_environment_drift_or_missing_pythonpath(
    tmp_path: Path,
) -> None:
    plan = _corrected_plan(tmp_path)
    drifted = json.loads(json.dumps(plan))
    drifted["operations"][0]["native"]["environment"]["PYTHONPATH"] = (
        runner.ISOLATED_RUNTIME_DIRECTORY
    )
    with pytest.raises(runner.FinalOperationError) as raised:
        runner.validate_contract(drifted, _read(AUTH_PATH))
    assert raised.value.code == "NATIVE_ENVIRONMENT_INVALID"

    missing = json.loads(json.dumps(plan))
    del missing["operations"][0]["native"]["environment"]["PYTHONPATH"]
    with pytest.raises(runner.FinalOperationError) as raised:
        runner.validate_contract(missing, _read(AUTH_PATH))
    assert raised.value.code == "NATIVE_ENVIRONMENT_INVALID"
