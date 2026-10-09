from __future__ import annotations

import json
import copy
import hashlib
import os
import shutil
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


def stage_identity_fixture(tmp_path: Path) -> tuple[Path, Path, dict[str, Any]]:
    """Real committed Wangp-shaped source and the preserved 13-path stage shape."""
    repository, staged = tmp_path / "wangp", tmp_path / "staged"
    repository.mkdir()
    paths = json.loads((RUN_DIR / "final-cell-retry3-20261008/stage-inventory.json").read_text())["files"]
    for relative in paths + ["pyproject.toml", "services/director/run_ledger.py"]:
        target = repository / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)
        if relative in paths:
            destination = staged / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(target, destination)
    for args in (["init", "-q"], ["add", "."],
                 ["-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                  "-c", "core.hooksPath=/dev/null", "commit", "-qm", "fixture"]):
        subprocess.run(["git", "-C", str(repository), *args], check=True, capture_output=True)
    return repository, staged, runner.build_stage_inventory(repository, staged)


def test_stage_inventory_clean_retry3_shape(tmp_path: Path) -> None:
    repository, staged, inventory = stage_identity_fixture(tmp_path)
    assert runner.validate_stage_inventory(inventory, repository, staged) is None
    identity = inventory["repository"]
    assert identity["commit_sha"] == subprocess.check_output(
        ["git", "-C", str(repository), "rev-parse", "HEAD"], text=True).strip()
    assert identity["status_porcelain_v1"] == ""
    assert identity["clean_tree"] is True and identity["dirty_tree"] is False
    assert identity["status_sha256"] == hashlib.sha256(b"").hexdigest()
    assert inventory["schema_version"] == "wangp-dspy.ltx-stage-inventory/v2"
    assert inventory["file_count"] == 13
    paths = [entry["path"] for entry in inventory["files"]]
    assert paths == sorted(paths) and len(set(paths)) == 13
    for entry in inventory["files"]:
        payload = (staged / entry["path"]).read_bytes()
        assert entry["size_bytes"] == len(payload)
        assert entry["sha256"] == hashlib.sha256(payload).hexdigest()


def test_direct_authorization_rejects_newer_clean_execution_commit(tmp_path: Path) -> None:
    repository, staged, old_inventory = stage_identity_fixture(tmp_path)
    # Advance a real clean checkout without changing the staged bytes. A valid
    # inventory alone must not authorize a different execution revision.
    subprocess.run([
        "git", "-C", str(repository), "-c", "user.name=Fixture",
        "-c", "user.email=fixture@example.invalid", "-c", "core.hooksPath=/dev/null",
        "commit", "--allow-empty", "-qm", "newer execution revision",
    ], check=True, capture_output=True)
    inventory = runner.build_stage_inventory(repository, staged)
    assert inventory["repository"]["commit_sha"] != old_inventory["repository"]["commit_sha"]
    assert runner.validate_stage_inventory(inventory, repository, staged) is None
    plan = json.loads((RUN_DIR / "phase-b-preparation/corrected-retry-plan.json").read_text())
    authorization = json.loads(
        (RUN_DIR / "operator-authorization.identity-capture.20261009.json").read_text()
    )
    assert inventory["repository"]["commit_sha"] != authorization["base_commit"]
    plan["identity_capture_authorization_binding"] = runner.identity_capture_authorization_binding(authorization)
    plan["runner_repository_root"] = str(repository)
    plan["stage_inventory"] = inventory
    queue = tmp_path / "must-not-exist.db"
    with pytest.raises(runner.FinalOperationError) as raised:
        runner.run_batch(plan, authorization, staged, queue, runtime_state={})
    assert raised.value.code == "IDENTITY_CAPTURE_EXECUTION_COMMIT_MISMATCH"
    assert not queue.exists()
    # A fresh external approval may bind this exact final commit without embedding
    # its own digest in runner source. This fixture is structural, not real approval.
    authorization["base_commit"] = inventory["repository"]["commit_sha"]
    plan["identity_capture_authorization_binding"] = runner.identity_capture_authorization_binding(authorization)
    with pytest.raises(runner.FinalOperationError) as raised:
        runner.run_batch(plan, authorization, staged, queue, runtime_state={})
    assert raised.value.code == "RUNTIME_PATH_INVALID"
    assert not queue.exists()


@pytest.mark.parametrize("change,code", [
    ("dirty", "STAGE_INVENTORY_DIRTY_REPOSITORY"),
    ("missing", "STAGE_INVENTORY_FILE_SET_MISMATCH"),
    ("extra", "STAGE_INVENTORY_FILE_SET_MISMATCH"),
    ("hash", "STAGE_INVENTORY_HASH_MISMATCH"),
    ("size", "STAGE_INVENTORY_SIZE_MISMATCH"),
    ("symlink", "STAGE_INVENTORY_PATH_INVALID"),
    ("directory", "STAGE_INVENTORY_FILE_SET_MISMATCH"),
    ("fifo", "STAGE_INVENTORY_PATH_INVALID"),
])
def test_stage_inventory_real_file_rejections(tmp_path: Path, change: str, code: str) -> None:
    repository, staged, inventory = stage_identity_fixture(tmp_path)
    relative = inventory["files"][0]["path"]
    path = staged / relative
    expected_hash = inventory["files"][0]["sha256"]
    if change == "dirty":
        (repository / relative).write_bytes(b"dirty")
    elif change == "missing":
        path.unlink()
    elif change == "extra":
        (staged / "extra.py").write_bytes(b"extra")
    elif change == "hash":
        data = path.read_bytes()
        path.write_bytes(bytes([data[0] ^ 1]) + data[1:])
    elif change == "size":
        path.write_bytes(b"different size")
    else:
        path.unlink()
        if change == "symlink":
            path.symlink_to(repository / relative)
        elif change == "directory":
            path.mkdir()
        else:
            os.mkfifo(path)
    with pytest.raises(runner.FinalOperationError) as raised:
        runner.validate_stage_inventory(inventory, repository, staged)
    assert raised.value.code == code
    assert relative in raised.value.observed or change == "extra"
    if change == "hash":
        assert expected_hash in raised.value.observed
        assert hashlib.sha256(path.read_bytes()).hexdigest() in raised.value.observed
    if change == "dirty":
        assert " M " in raised.value.observed
        with pytest.raises(runner.FinalOperationError, match=" M "):
            runner.build_stage_inventory(repository, staged)


@pytest.mark.parametrize("change,code", [
    ("absent", "EXECUTION_REPOSITORY_IDENTITY_UNPROVEN"),
    ("repo_absent", "EXECUTION_REPOSITORY_IDENTITY_UNPROVEN"),
    ("repo_extra", "STAGE_INVENTORY_REPOSITORY_INVALID"),
    ("wan2gp", "STAGE_INVENTORY_REPOSITORY_MISMATCH"),
    ("status", "STAGE_INVENTORY_REPOSITORY_MISMATCH"),
    ("boolean", "STAGE_INVENTORY_REPOSITORY_MISMATCH"),
    ("schema", "STAGE_INVENTORY_SCHEMA_INVALID"),
    ("duplicate", "STAGE_INVENTORY_PATH_ORDER_INVALID"),
    ("unsafe", "STAGE_INVENTORY_PATH_INVALID"),
    ("size_type", "STAGE_INVENTORY_FILES_INVALID"),
    ("hash_format", "STAGE_INVENTORY_FILES_INVALID"),
])
def test_stage_inventory_record_rejections(tmp_path: Path, change: str, code: str) -> None:
    repository, staged, inventory = stage_identity_fixture(tmp_path)
    invalid = copy.deepcopy(inventory)
    if change == "absent":
        invalid = None
    elif change == "repo_absent":
        del invalid["repository"]
    elif change == "repo_extra":
        invalid["repository"]["source_root"] = "/Wan2GP"
    elif change == "wan2gp":
        invalid["repository"]["commit_sha"] = "4c93b64a47b5b0a915f2abec2ce754be98227150"
    elif change == "status":
        invalid["repository"]["status_porcelain_v1"] = " M pyproject.toml\n"
    elif change == "boolean":
        invalid["repository"]["clean_tree"] = 1
    elif change == "schema":
        invalid["schema_version"] = "v1"
    elif change == "duplicate":
        invalid["files"][1] = invalid["files"][0]
    elif change == "unsafe":
        invalid["files"][0]["path"] = "../escape"
    elif change == "size_type":
        invalid["files"][0]["size_bytes"] = True
    else:
        invalid["files"][0]["sha256"] = "bad"
    with pytest.raises(runner.FinalOperationError) as raised:
        runner.validate_stage_inventory(invalid, repository, staged)
    assert raised.value.code == code


def test_stage_inventory_rejects_non_wangp_and_unversioned_bytes(tmp_path: Path) -> None:
    repository, staged, _ = stage_identity_fixture(tmp_path)
    (staged / "unversioned.py").write_bytes(b"new")
    with pytest.raises(runner.FinalOperationError) as raised:
        runner.build_stage_inventory(repository, staged)
    assert raised.value.code == "STAGE_INVENTORY_GIT_FAILED"
    with pytest.raises(runner.FinalOperationError) as raised:
        runner.build_stage_inventory(tmp_path / "absent", staged)
    assert raised.value.code == "EXECUTION_REPOSITORY_IDENTITY_UNPROVEN"
    (repository / "pyproject.toml").write_text('[project]\nname = "Wan2GP"\n')
    subprocess.run(["git", "-C", str(repository), "-c", "user.name=Fixture",
                    "-c", "user.email=fixture@example.invalid", "-c", "core.hooksPath=/dev/null",
                    "commit", "-qam", "not Wangp"], check=True, capture_output=True)
    with pytest.raises(runner.FinalOperationError) as raised:
        runner.build_stage_inventory(repository, staged)
    assert raised.value.code == "STAGE_INVENTORY_REPOSITORY_INVALID"


def test_stage_inventory_cannot_bless_bytes_from_another_revision(tmp_path: Path) -> None:
    repository, staged, inventory = stage_identity_fixture(tmp_path)
    entry = inventory["files"][0]
    altered = b"not committed runner bytes"
    (staged / entry["path"]).write_bytes(altered)
    entry.update(size_bytes=len(altered), sha256=hashlib.sha256(altered).hexdigest())
    with pytest.raises(runner.FinalOperationError) as raised:
        runner.validate_stage_inventory(inventory, repository, staged)
    assert raised.value.code == "STAGE_INVENTORY_SOURCE_MISMATCH"
    assert entry["path"] in raised.value.observed


def test_missing_inventory_stops_before_queue_and_staging(tmp_path: Path) -> None:
    plan = json.loads((RUN_DIR / "phase-b-preparation/corrected-retry-plan.json").read_text())
    authorization = json.loads(AUTH_PATH.read_text())
    queue_db = tmp_path / "must-not-be-created.db"
    with pytest.raises(runner.FinalOperationError) as raised:
        runner.run_batch(plan, authorization, tmp_path, queue_db, runtime_state={})
    assert raised.value.code == "EXECUTION_REPOSITORY_IDENTITY_UNPROVEN"
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("with_inventory", [False, True])
def test_invalid_inventory_blocks_authorized_batch(tmp_path: Path, with_inventory: bool) -> None:
    repository, staged, inventory = stage_identity_fixture(tmp_path)
    plan = json.loads((RUN_DIR / "phase-b-preparation/corrected-retry-plan.json").read_text())
    plan["runner_repository_root"] = str(repository)
    if with_inventory:
        plan["stage_inventory"] = inventory
        (staged / inventory["files"][0]["path"]).unlink()
    before = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*"))
    with pytest.raises(runner.FinalOperationError) as raised:
        runner.run_batch(plan, json.loads(AUTH_PATH.read_text()), staged,
                         tmp_path / "queue.db", runtime_state={})
    assert raised.value.code == ("STAGE_INVENTORY_FILE_SET_MISMATCH" if with_inventory
                                 else "EXECUTION_REPOSITORY_IDENTITY_UNPROVEN")
    assert sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*")) == before
