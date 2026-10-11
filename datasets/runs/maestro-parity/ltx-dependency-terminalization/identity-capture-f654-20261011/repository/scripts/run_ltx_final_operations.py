#!/usr/bin/env python3
"""Governed one-attempt WD-28ac native-operation runner."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import time
import tomllib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from services.jobs.queue import JobQueue
from services.director.run_ledger import RepositoryIdentityError, repository_identity


ISOLATED_RUNTIME_DIRECTORY = (
    "/home/straughter/wd-28ac-final-gate7-20261003/runtime/mmgp-3.7.14"
)
ISOLATED_REMBG_DIRECTORY = (
    "/home/straughter/wd-28ac-final-gate7-20261003/runtime/rembg-2.0.65"
)
COMFYUI_SITE_PACKAGES = (
    "/home/straughter/ComfyUI/venv/lib/python3.12/site-packages"
)
CORRECTED_NATIVE_PYTHONPATH = ":".join((
    ISOLATED_REMBG_DIRECTORY,
    ISOLATED_RUNTIME_DIRECTORY,
    COMFYUI_SITE_PACKAGES,
))
ISOLATED_MMGP_IMPORT_PATH = (
    "/home/straughter/wd-28ac-final-gate7-20261003/runtime/mmgp-3.7.14/mmgp/__init__.py"
)
ISOLATED_RUNTIME_PAYLOAD_SHA256 = (
    "d39fa7a56869387410d299ab139eb724e3be3f04055fd5d0da69d32dec9f309b"
)
ISOLATED_RUNTIME_FILE_COUNT = 12
ISOLATED_RUNTIME_UNCOMPRESSED_BYTES = 291005
CORRECTED_NATIVE_ENVIRONMENT = {
    "PYTHONUNBUFFERED": "1",
    "PYTHONDONTWRITEBYTECODE": "1",
    "PYTORCH_ALLOC_CONF": "expandable_segments:True",
    "HF_HUB_OFFLINE": "1",
    "TRANSFORMERS_OFFLINE": "1",
    "PYTHONPATH": CORRECTED_NATIVE_PYTHONPATH,
}
PRIOR_NATIVE_RUN_ROOT = "/home/straughter/wd-28ac-run/phase-b-gate5"
CORRECTED_NATIVE_RUN_ROOT = (
    "/home/straughter/wd-28ac-run/phase-b-gate22-corrected-retry"
)
IDENTITY_CAPTURE_AUTHORIZATION_SCHEMA = "wangp-dspy.ltx-identity-capture-authorization/v1"
IDENTITY_CAPTURE_OPERATIONS = [
    {"row": row, "operation": operation, "operation_id": f"{prefix}-{operation}"}
    for row, prefix, operations in (
        ("LTX-2.5", "ltx25", ("outpaint", "repaint", "recast", "upscale")),
        ("LTX-2.3", "ltx23", ("outpaint", "recast", "upscale")),
    )
    for operation in operations
]
IDENTITY_CAPTURE_REQUIRED_IDENTITY = {
    key: True for key in (
        "clean_wangp_repository", "record_commit", "record_staged_file_path_size_sha256",
        "record_status_porcelain_v1", "staged_bytes_must_match_tracked_head",
        "wan2gp_commit_is_not_wangp_identity",
    )
}
GATE15_SNAPSHOT_SHA256 = (
    "2d80ae6623256e56223a47c359b3e754a9cecffc8c768063a37c155cf88b2b89"
)
GATE15_TRACE_SHA256 = (
    "60a03fdb467c77fe512619777628b2c40832598f4fe3ab7c1955f1ba5461b8cd"
)
GATE15_PREFLIGHT_SHA256 = (
    "26b1f0c232fdec66f09eb28b45f3beed55e8f3006b166f7c118d0a73d0ae5ca3"
)
EXPECTED_GATE15_HOST_AUTHORIZATION = {
    "gate": 15,
    "mode": "live",
    "model": "jev-latest",
    "decision": "CONTINUE",
    "confidence": 0.80,
    "snapshot_sha256": GATE15_SNAPSHOT_SHA256,
    "trace_sha256": GATE15_TRACE_SHA256,
    "scope": "corrected_native_operations_after_immediate_preflight",
    "fresh_preflight_path": (
        "jev-gates/2026-10-04/gate-15-fresh-host-preflight.json"
    ),
    "fresh_preflight_sha256": GATE15_PREFLIGHT_SHA256,
    "fresh_host_recheck": True,
    "separate_fresh_host_gate_required": False,
    "immediate_preflight_before_execution_required": True,
    "local_binding_host_contact_authorized": False,
    "host_execution_authorized": True,
    "operations_authorized": True,
    "operations": [
        {"row": "LTX-2.5", "operation": "outpaint"},
        {"row": "LTX-2.5", "operation": "repaint"},
        {"row": "LTX-2.5", "operation": "recast"},
        {"row": "LTX-2.5", "operation": "upscale"},
        {"row": "LTX-2.3", "operation": "outpaint"},
        {"row": "LTX-2.3", "operation": "recast"},
        {"row": "LTX-2.3", "operation": "upscale"},
    ],
    "matrix_cells_authorized": 7,
    "max_attempts_per_operation": 1,
    "retry": "never",
    "stop_on_first_terminal_failure": True,
    "judge_start_policy": "governed_judge_ctl_only_if_required",
    "judge_control_path": "/home/straughter/marathon/bin/judge_ctl.sh",
    "unauthorized_judge_control_authorized": False,
    "download_authorized": False,
    "network_or_model_get_authorized": False,
    "dependency_install_authorized": False,
    "deletion_authorized": False,
    "substitution_authorized": False,
    "model_or_reference_mutation_authorized": False,
    "runtime_mutation_authorized": False,
    "protected_file_change_authorized": False,
    "threshold_change_authorized": False,
    "protected_engine_change_authorized": False,
    "unrelated_operations_authorized": False,
    "wd_bw0h_h3_retry_authorized": False,
    "provider_spend_authorized": False,
    "training_authorized": False,
    "capability_or_matrix_claim_authorized": False,
}
EXPECTED_GATE15_PLAN_BINDING = {
    "gate": 15,
    "snapshot_sha256": GATE15_SNAPSHOT_SHA256,
    "trace_sha256": GATE15_TRACE_SHA256,
    "fresh_preflight_sha256": GATE15_PREFLIGHT_SHA256,
}
EXPECTED_GATE15_EXECUTION_PRECONDITIONS = {
    "gate15_preflight_sha256": GATE15_PREFLIGHT_SHA256,
    "fresh_host_recheck": True,
    "separate_fresh_host_gate_required": False,
    "immediate_preflight_before_execution_required": True,
    "queue_collision_check_required": True,
    "judge_start_policy": "governed_judge_ctl_only_if_required",
    "judge_control_path": "/home/straughter/marathon/bin/judge_ctl.sh",
}


class FinalOperationError(ValueError):
    """Typed terminal WD-28ac native-operation boundary."""

    def __init__(self, code: str, observed: str, remediation: str) -> None:
        super().__init__(observed)
        self.code = code
        self.observed = observed
        self.remediation = remediation


STAGE_INVENTORY_SCHEMA = "wangp-dspy.ltx-stage-inventory/v2"


def _stage_error(code: str, observed: str) -> FinalOperationError:
    return FinalOperationError(code, observed,
                               "Restage from a clean Wangp checkout and rebuild the inventory.")


def _stage_git(root: Path, *args: str) -> bytes:
    try:
        result = subprocess.run(["git", "-C", str(root), *args],
                                capture_output=True, check=False, timeout=60)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise _stage_error("STAGE_INVENTORY_GIT_FAILED", str(exc)) from exc
    if result.returncode:
        raise _stage_error("STAGE_INVENTORY_GIT_FAILED",
                           result.stderr.decode("utf-8", "replace"))
    return result.stdout


def _stage_repository(root: Path) -> dict[str, Any]:
    try:
        identity = repository_identity(root)
    except (RepositoryIdentityError, OSError) as exc:
        raise _stage_error("EXECUTION_REPOSITORY_IDENTITY_UNPROVEN", str(exc)) from exc
    if identity["repo_root"] != str(root.resolve()):
        raise _stage_error("STAGE_INVENTORY_REPOSITORY_INVALID", str(root))
    status = _stage_git(root, "status", "--porcelain=v1").decode("utf-8", "replace")
    if status or not identity["clean_tree"] or identity["dirty_tree"]:
        raise _stage_error("STAGE_INVENTORY_DIRTY_REPOSITORY", repr(status))
    try:
        project = tomllib.loads(_stage_git(root, "show", "HEAD:pyproject.toml").decode())
        for marker in ("scripts/run_ltx_final_operations.py", "services/director/run_ledger.py"):
            _stage_git(root, "cat-file", "-e", f"HEAD:{marker}")
    except (ValueError, UnicodeError) as exc:
        raise _stage_error("STAGE_INVENTORY_REPOSITORY_INVALID", str(exc)) from exc
    metadata = project.get("project")
    if not isinstance(metadata, dict) or metadata.get("name") != "wangp-dspy":
        raise _stage_error("STAGE_INVENTORY_REPOSITORY_INVALID", str(root))
    return {"repo_root": identity["repo_root"], "commit_sha": identity["commit_sha"],
            "status_porcelain_v1": status, "clean_tree": True, "dirty_tree": False,
            "status_sha256": hashlib.sha256(status.encode()).hexdigest()}


def _stage_files(root: Path) -> list[dict[str, Any]]:
    files = []
    def fingerprint(value: os.stat_result) -> tuple[int, ...]:
        return (value.st_dev, value.st_ino, value.st_mode, value.st_size,
                value.st_mtime_ns, value.st_ctime_ns)
    try:
        if root.is_symlink() or not root.is_dir():
            raise _stage_error("STAGE_INVENTORY_PATH_INVALID", str(root))
        def walk(directory: Path) -> None:
            for path in sorted(directory.iterdir()):
                if "\\" in path.name:
                    raise _stage_error("STAGE_INVENTORY_PATH_INVALID", str(path))
                mode = path.lstat().st_mode
                if stat.S_ISDIR(mode):
                    walk(path)
                elif stat.S_ISREG(mode):
                    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
                    with os.fdopen(descriptor, "rb") as source:
                        before = os.fstat(source.fileno())
                        if not stat.S_ISREG(before.st_mode):
                            raise _stage_error("STAGE_INVENTORY_PATH_INVALID", str(path))
                        payload = source.read()
                        after = os.fstat(source.fileno())
                    if fingerprint(before) != fingerprint(after) or fingerprint(path.lstat()) != fingerprint(after):
                        raise _stage_error("STAGE_INVENTORY_FILE_CHANGED", str(path))
                    files.append({"path": path.relative_to(root).as_posix(),
                                  "size_bytes": len(payload),
                                  "sha256": hashlib.sha256(payload).hexdigest()})
                else:
                    raise _stage_error("STAGE_INVENTORY_PATH_INVALID", str(path))
        walk(root)
    except OSError as exc:
        raise _stage_error("STAGE_INVENTORY_FILE_UNREADABLE", str(exc)) from exc
    return sorted(files, key=lambda item: item["path"])


def build_stage_inventory(repository_root: Path, staged_root: Path) -> dict[str, Any]:
    """Bind every staged runner byte to a clean Wangp HEAD (never Wan2GP)."""
    repository = _stage_repository(repository_root)
    files = _stage_files(staged_root)
    if not files:
        raise _stage_error("STAGE_INVENTORY_FILES_MISSING", str(staged_root))
    for entry in files:
        payload = _stage_git(repository_root, "show",
                             f"{repository['commit_sha']}:{entry['path']}")
        expected = hashlib.sha256(payload).hexdigest()
        if entry["sha256"] != expected:
            raise _stage_error("STAGE_INVENTORY_SOURCE_MISMATCH",
                               f"{entry['path']}: expected={expected}, observed={entry['sha256']}")
    if _stage_repository(repository_root) != repository:
        raise _stage_error("STAGE_INVENTORY_REPOSITORY_CHANGED", str(repository_root))
    return {"schema_version": STAGE_INVENTORY_SCHEMA, "repository": repository,
            "staged_root": str(staged_root.resolve()), "file_count": len(files), "files": files}


def validate_stage_inventory(inventory: Mapping[str, Any], repository_root: Path,
                             staged_root: Path) -> None:
    """Reject incomplete identity and any staged path, size, or content drift."""
    if not isinstance(inventory, Mapping) or not isinstance(inventory.get("repository"), Mapping):
        raise _stage_error("EXECUTION_REPOSITORY_IDENTITY_UNPROVEN", "repository is absent")
    if (set(inventory) != {"schema_version", "repository", "staged_root", "file_count", "files"}
            or inventory["schema_version"] != STAGE_INVENTORY_SCHEMA):
        raise _stage_error("STAGE_INVENTORY_SCHEMA_INVALID", repr(inventory))
    repository = _stage_repository(repository_root)
    recorded = inventory["repository"]
    if set(recorded) != set(repository):
        raise _stage_error("STAGE_INVENTORY_REPOSITORY_INVALID", repr(recorded))
    for key, expected in repository.items():
        if type(recorded[key]) is not type(expected) or recorded[key] != expected:
            raise _stage_error("STAGE_INVENTORY_REPOSITORY_MISMATCH",
                               f"{key}: expected={expected!r}, observed={recorded[key]!r}")
    if inventory["staged_root"] != str(staged_root.resolve()):
        raise _stage_error("STAGE_INVENTORY_ROOT_MISMATCH", str(inventory["staged_root"]))
    entries = inventory["files"]
    if (not isinstance(entries, list) or type(inventory["file_count"]) is not int
            or inventory["file_count"] != len(entries) or not entries):
        raise _stage_error("STAGE_INVENTORY_FILES_INVALID", repr(entries))
    paths = []
    for entry in entries:
        if (not isinstance(entry, dict) or set(entry) != {"path", "size_bytes", "sha256"}
                or type(entry["size_bytes"]) is not int or entry["size_bytes"] < 0
                or not isinstance(entry["sha256"], str)
                or not re.fullmatch("[0-9a-f]{64}", entry["sha256"])):
            raise _stage_error("STAGE_INVENTORY_FILES_INVALID", repr(entry))
        path = entry["path"]
        if (not isinstance(path, str) or not path or path.startswith("/")
                or "\\" in path or any(part in {"", ".", ".."} for part in path.split("/"))):
            raise _stage_error("STAGE_INVENTORY_PATH_INVALID", repr(path))
        paths.append(path)
    if paths != sorted(set(paths)):
        raise _stage_error("STAGE_INVENTORY_PATH_ORDER_INVALID", repr(paths))
    actual = {entry["path"]: entry for entry in _stage_files(staged_root)}
    missing, extra = set(paths) - actual.keys(), actual.keys() - set(paths)
    if missing or extra:
        raise _stage_error("STAGE_INVENTORY_FILE_SET_MISMATCH",
                           f"missing={sorted(missing)}, extra={sorted(extra)}")
    for entry in entries:
        for key in ("size_bytes", "sha256"):
            if entry[key] != actual[entry["path"]][key]:
                raise _stage_error("STAGE_INVENTORY_SIZE_MISMATCH" if key == "size_bytes"
                                   else "STAGE_INVENTORY_HASH_MISMATCH",
                                   f"{entry['path']}: expected={entry[key]}, observed={actual[entry['path']][key]}")
    if build_stage_inventory(repository_root, staged_root) != inventory:
        raise _stage_error("STAGE_INVENTORY_CHANGED", "inventory changed during validation")


@dataclass(frozen=True)
class NativeResult:
    returncode: int
    log_path: str
    output_path: str
    started_at: float
    finished_at: float
    before: dict[str, Any]
    after: dict[str, Any]


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))

def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    os.replace(temporary, path)

def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def _run(argv: Sequence[str], timeout: int = 60) -> dict[str, Any]:
    result = subprocess.run(
        list(argv), text=True, capture_output=True, timeout=timeout, check=False
    )
    return {
        "argv": list(argv),
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }

def _snapshot(operation: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source_commit": _run([
            "git", "-C", str(operation["source_root"]), "rev-parse", "HEAD"
        ])["stdout"].strip(),
        "source_status": _run([
            "git", "-C", str(operation["source_root"]), "status", "--porcelain=v1"
        ])["stdout"].strip(),
        "gpu": _run([
            "nvidia-smi", "--query-gpu=name,memory.total,memory.used,memory.free,utilization.gpu",
            "--format=csv,noheader,nounits",
        ]),
        "gpu_apps": _run([
            "nvidia-smi", "--query-compute-apps=pid,process_name,used_memory",
            "--format=csv,noheader",
        ]),
        "disk": _run(["df", "-B1", str(operation["source_root"])]),
    }

def identity_capture_authorization_binding(authorization: Mapping[str, Any]) -> dict[str, Any]:
    """Compute a content binding, not proof of operator provenance (recorded externally)."""
    canonical = json.dumps(authorization, sort_keys=True, separators=(",", ":"))
    return {
        "schema_version": authorization.get("schema_version"),
        "base_commit": authorization.get("base_commit"),
        "proposal_sha256": authorization.get("operator_approval", {}).get("proposal_sha256"),
        "authorization_canonical_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
    }


def _validate_identity_capture_authorization(
    plan: Mapping[str, Any], authorization: Mapping[str, Any]
) -> bool:
    """Validate the direct approval contract and binding, never infer it from legacy gates."""
    if authorization.get("schema_version") != IDENTITY_CAPTURE_AUTHORIZATION_SCHEMA:
        if "identity_capture_authorization_binding" in plan:
            raise FinalOperationError(
                "IDENTITY_CAPTURE_AUTHORIZATION_INVALID", "direct authorization schema absent",
                "Use the exact approved identity-capture authorization, not a consumed legacy gate.",
            )
        return False
    approval = authorization.get("operator_approval")
    approval = approval if isinstance(approval, Mapping) else {}
    timestamp = authorization.get("timestamp")
    try:
        valid_timestamp = (isinstance(timestamp, str) and "T" in timestamp
                           and datetime.fromisoformat(timestamp).tzinfo is not None)
    except ValueError:
        valid_timestamp = False
    exact_fields = {
        "status": "approved", "approved_by": "operator", "operation_count": 7,
        "max_attempts_per_operation": 1, "retry": "never",
        "stop_on_first_terminal_failure": True,
        "model_downloads": 0, "package_downloads": 0, "dependency_installs": 0,
        "provider_spend": False, "training": False, "deletions": 0,
        "protected_engine_changes": 0, "threshold_changes": 0,
    }
    identity = authorization.get("required_execution_identity")
    if (
        any(type(authorization.get(key)) is not type(value) or authorization.get(key) != value
            for key, value in exact_fields.items())
        or not isinstance(authorization.get("base_commit"), str)
        or re.fullmatch(r"[0-9a-f]{40}", authorization.get("base_commit", "")) is None
        or not isinstance(approval.get("proposal_sha256"), str)
        or re.fullmatch(r"[0-9a-f]{64}", approval.get("proposal_sha256", "")) is None
        or not isinstance(approval.get("proposal"), str) or not approval["proposal"].strip()
        or not isinstance(authorization.get("text"), str) or not authorization["text"].strip()
        or authorization["text"] != approval.get("verbatim")
        or not valid_timestamp or timestamp != approval.get("approved_at")
        or authorization.get("operations") != IDENTITY_CAPTURE_OPERATIONS
        or not isinstance(identity, Mapping) or set(identity) != set(IDENTITY_CAPTURE_REQUIRED_IDENTITY)
        or any(value is not True for value in identity.values())
    ):
        raise FinalOperationError(
            "IDENTITY_CAPTURE_AUTHORIZATION_INVALID", "direct approval constraints invalid",
            "Require an operator approval with seven one-shot operations and all safety limits.",
        )
    # Keep the approval digest outside source bytes: embedding it creates a circular
    # dependency when the approval base_commit identifies this runner's final commit.
    # External operator evidence establishes provenance; this verifies agreement.
    if plan.get("identity_capture_authorization_binding") != identity_capture_authorization_binding(authorization):
        raise FinalOperationError(
            "IDENTITY_CAPTURE_PLAN_BINDING_INVALID", "identity-capture binding mismatch",
            "Bind the exact schema, base commit, proposal and canonical authorization hashes.",
        )
    if (plan.get("mode") != "corrected_native_operations_authorized"
            or plan.get("host_execution_authorized") is not True
            or plan.get("preflight_ready") is not True):
        raise FinalOperationError(
            "PLAN_PREFLIGHT_NOT_READY", "direct authorization requires an authorized, ready plan",
            "Collect healthy QC and fresh host facts first.",
        )
    identities = [
        {key: item.get(key) for key in ("row", "operation", "operation_id")}
        for item in plan.get("operations", [])
    ]
    if identities != authorization["operations"]:
        raise FinalOperationError(
            "IDENTITY_CAPTURE_OPERATIONS_INVALID", "operation identities or order differ",
            "Use exactly the seven named operations in the approved order.",
        )
    return True


def validate_contract(
    plan: Mapping[str, Any], authorization: Mapping[str, Any]
) -> None:
    operations = plan.get("operations", [])
    if plan.get("schema_version") != (
        "wangp-dspy.wd-28ac.corrected-native-retry-plan/v1"
    ):
        raise FinalOperationError(
            "PLAN_SCHEMA_INVALID", str(plan.get("schema_version")),
            "Use the CI-green Gate 12 corrected-retry plan.",
        )
    if plan.get("mode") not in {
        "corrected_native_runtime_integration_local_only",
        "corrected_native_operations_authorized",
    }:
        raise FinalOperationError("PLAN_NOT_CORRECTED_FINAL", plan.get("mode", ""),
                                  "Regenerate the plan with Gate 12 integration.")
    if plan.get("mode") == "corrected_native_operations_authorized" and (
        not plan.get("host_execution_authorized") or not plan.get("preflight_ready")
    ):
        raise FinalOperationError(
            "PLAN_PREFLIGHT_NOT_READY",
            "host_execution_authorized or preflight_ready is false",
            "Collect healthy QC and fresh host facts first.",
        )
    if len(operations) != 7:
        raise FinalOperationError("OPERATION_COUNT_INVALID", str(len(operations)),
                                  "Exactly seven planned operations are required.")
    direct_authorization = _validate_identity_capture_authorization(plan, authorization)
    gate = authorization.get("jev_final_operations_authorization", {})
    if not direct_authorization and (
        gate.get("operations_authorized") is not True or gate.get("retry") != "never"
    ):
        raise FinalOperationError("GATE7_AUTHORIZATION_INVALID",
                                  json.dumps(gate, sort_keys=True),
                                  "Bind the exact live Gate 7 CONTINUE record.")
    corrected = authorization.get("operator_corrected_native_retry_authorization", {})
    if not direct_authorization and (corrected.get("decision") != "Authorized" or corrected.get(
        "separate_host_retry_gate_required"
    ) is not True):
        raise FinalOperationError(
            "CORRECTED_NATIVE_RETRY_AUTHORIZATION_INVALID",
            json.dumps(corrected, sort_keys=True),
            "Bind the operator corrected native-retry record.",
        )
    if not direct_authorization and plan.get("mode") == "corrected_native_operations_authorized":
        host_gate = authorization.get(
            "jev_corrected_native_retry_host_authorization", {}
        )
        if host_gate != EXPECTED_GATE15_HOST_AUTHORIZATION:
            raise FinalOperationError(
                "HOST_GATE_AUTHORIZATION_INVALID",
                json.dumps(host_gate, sort_keys=True)[:1000],
                "Bind the exact live Gate 15 corrected-host authorization.",
            )
        if plan.get("host_authorization_binding") != EXPECTED_GATE15_PLAN_BINDING:
            raise FinalOperationError(
                "HOST_GATE_PLAN_BINDING_INVALID",
                json.dumps(plan.get("host_authorization_binding"), sort_keys=True),
                "Bind the plan to the exact Gate 15 hashes.",
            )
        if (
            plan.get("execution_preconditions")
            != EXPECTED_GATE15_EXECUTION_PRECONDITIONS
        ):
            raise FinalOperationError(
                "EXECUTION_PRECONDITIONS_INVALID",
                json.dumps(plan.get("execution_preconditions"), sort_keys=True),
                "Require an immediate fresh preflight before corrected execution.",
            )
    runtime = plan.get("isolated_runtime")
    payload = runtime.get("expected_payload", {}) if isinstance(runtime, dict) else {}
    inventory = payload.get("inventory")
    inventory_is_valid = isinstance(inventory, list) and all(
        isinstance(item, Mapping)
        and isinstance(item.get("path"), str)
        and isinstance(item.get("sha256"), str)
        and isinstance(item.get("size_bytes"), int)
        for item in inventory
    )
    inventory_bytes = (
        sum(item["size_bytes"] for item in inventory)
        if inventory_is_valid else -1
    )
    if (
        not isinstance(runtime, dict)
        or runtime.get("directory") != ISOLATED_RUNTIME_DIRECTORY
        or payload.get("canonical_sha256") != ISOLATED_RUNTIME_PAYLOAD_SHA256
        or payload.get("file_count") != ISOLATED_RUNTIME_FILE_COUNT
        or payload.get("uncompressed_bytes") != ISOLATED_RUNTIME_UNCOMPRESSED_BYTES
        or not inventory_is_valid
        or len(inventory) != ISOLATED_RUNTIME_FILE_COUNT
        or inventory_bytes != ISOLATED_RUNTIME_UNCOMPRESSED_BYTES
        or _canonical_payload_hash(inventory) != ISOLATED_RUNTIME_PAYLOAD_SHA256
    ):
        raise FinalOperationError(
            "RUNTIME_BINDING_ABSENT", json.dumps(runtime, sort_keys=True)[:1000],
            "Bind the proven isolated mmgp 3.7.14 payload identity.",
        )
    identities = [(item["row"], item["operation"]) for item in operations]
    if len(set(identities)) != 7:
        raise FinalOperationError("OPERATION_IDENTITY_DUPLICATE", json.dumps(identities),
                                  "Each owned cell must occur exactly once.")
    for item in operations:
        native = item.get("native", {})
        if native.get("environment") != CORRECTED_NATIVE_ENVIRONMENT:
            raise FinalOperationError(
                "NATIVE_ENVIRONMENT_INVALID",
                json.dumps(native.get("environment"), sort_keys=True),
                "Bind PYTHONPATH and all offline/CUDA environment settings.",
            )
        paths = (
            native.get("settings_stage_path", ""), native.get("log_path", ""),
            *(native.get("argv", [])),
        )
        if any(PRIOR_NATIVE_RUN_ROOT in str(value) for value in paths):
            raise FinalOperationError(
                "PRIOR_NATIVE_BOUNDARY_OVERLAP", json.dumps(paths),
                "Use the corrected retry namespace; never overwrite Gate 7 evidence.",
            )
        if not all(
            CORRECTED_NATIVE_RUN_ROOT in str(value)
            for value in (native.get("settings_stage_path", ""), native.get("log_path", ""))
        ):
            raise FinalOperationError(
                "CORRECTED_RUN_NAMESPACE_INVALID", json.dumps(paths),
                "Stage corrected attempts under the Gate 20 run root.",
            )

def build_native_environment(operation: Mapping[str, Any]) -> dict[str, str]:
    environment = operation.get("native", {}).get("environment")
    if environment != CORRECTED_NATIVE_ENVIRONMENT:
        raise FinalOperationError(
            "NATIVE_ENVIRONMENT_INVALID", json.dumps(environment, sort_keys=True),
            "Plan must bind the isolated runtime and existing offline/CUDA settings.",
        )
    return dict(CORRECTED_NATIVE_ENVIRONMENT)

def _canonical_payload_hash(inventory: Any) -> str | None:
    if not isinstance(inventory, list):
        return None
    try:
        path_sorted_inventory = sorted(
            inventory, key=lambda item: item["path"]
        )
    except (KeyError, TypeError):
        return None
    canonical = json.dumps(
        path_sorted_inventory, sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

def validate_runtime_state(
    state: Mapping[str, Any], *, require_fresh: bool = True
) -> dict[str, Any]:
    if state.get("directory") != ISOLATED_RUNTIME_DIRECTORY:
        raise FinalOperationError(
            "RUNTIME_PATH_INVALID", str(state.get("directory")),
            "Use the proven isolated mmgp 3.7.14 directory.",
        )
    if (
        state.get("exists") is not True
        or state.get("regular_directory") is not True
        or state.get("symlink") is not False
    ):
        raise FinalOperationError(
            "RUNTIME_PATH_INVALID", json.dumps({
                "exists": state.get("exists"),
                "regular_directory": state.get("regular_directory"),
                "symlink": state.get("symlink"),
            }, sort_keys=True), "Require the exact non-symlink runtime directory.",
        )
    if require_fresh and (
        state.get("fresh_host_recheck") is not True
        or state.get("separate_fresh_host_gate_required") is not False
    ):
        raise FinalOperationError(
            "RUNTIME_PREFLIGHT_STALE", json.dumps({
                "fresh_host_recheck": state.get("fresh_host_recheck"),
                "separate_fresh_host_gate_required": state.get(
                    "separate_fresh_host_gate_required"
                ),
            }, sort_keys=True),
            "A separate fresh host gate must recheck the isolated runtime.",
        )
    imported = state.get("isolated_import", {})
    if imported.get("returncode") != 0 or imported.get("python") != "/usr/bin/python3":
        raise FinalOperationError(
            "RUNTIME_IMPORT_FAILED", json.dumps(imported, sort_keys=True),
            "Require /usr/bin/python3 to import the isolated runtime.",
        )
    if imported.get("path") != ISOLATED_MMGP_IMPORT_PATH:
        raise FinalOperationError(
            "RUNTIME_IMPORT_PATH_INVALID", str(imported.get("path")),
            "mmgp must resolve inside the proven isolated directory.",
        )
    if imported.get("metadata_version") != "3.7.14":
        raise FinalOperationError(
            "RUNTIME_IMPORT_VERSION_INVALID", str(imported.get("metadata_version")),
            "Require mmgp 3.7.14.",
        )
    payload = state.get("payload", {})
    inventory = payload.get("inventory")
    if (
        payload.get("file_count") != ISOLATED_RUNTIME_FILE_COUNT
        or payload.get("uncompressed_bytes") != ISOLATED_RUNTIME_UNCOMPRESSED_BYTES
        or payload.get("canonical_sha256") != ISOLATED_RUNTIME_PAYLOAD_SHA256
        or _canonical_payload_hash(inventory) != ISOLATED_RUNTIME_PAYLOAD_SHA256
    ):
        raise FinalOperationError(
            "RUNTIME_PAYLOAD_DRIFT", json.dumps({
                "canonical_sha256": payload.get("canonical_sha256"),
                "computed_sha256": _canonical_payload_hash(inventory),
                "file_count": payload.get("file_count"),
                "uncompressed_bytes": payload.get("uncompressed_bytes"),
            }, sort_keys=True), "Preserve the proven 12-file mmgp payload exactly.",
        )
    if state.get("system_mmgp_present") is not False:
        raise FinalOperationError(
            "SYSTEM_MMGP_PRESENT", str(state.get("system_mmgp_present")),
            "System mmgp must remain absent; only PYTHONPATH binding is authorized.",
        )
    return {
        "status": "passed",
        "directory": ISOLATED_RUNTIME_DIRECTORY,
        "payload_sha256": ISOLATED_RUNTIME_PAYLOAD_SHA256,
        "mmgp_version": "3.7.14",
        "system_mmgp_present": False,
    }

def stage_settings(
    operation: Mapping[str, Any], template_root: Path
) -> dict[str, Any]:
    template = template_root / operation["native"]["template_path"]
    destination = Path(operation["native"]["settings_stage_path"])
    if not template.is_file():
        raise FinalOperationError("NATIVE_TEMPLATE_ABSENT", str(template),
                                  "Deploy the exact accepted settings template.")
    digest = _sha256(template)
    if digest != operation["native"]["template_sha256"]:
        raise FinalOperationError("NATIVE_TEMPLATE_HASH_MISMATCH", digest,
                                  "Redeploy the exact CI-green template bytes.")
    if destination.exists():
        raise FinalOperationError("SETTINGS_STAGE_COLLISION", str(destination),
                                  "Use a new dated run root; do not overwrite evidence.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(template, destination)
    if _sha256(destination) != digest:
        raise FinalOperationError("SETTINGS_STAGE_WRITE_MISMATCH", str(destination),
                                  "Verify staged settings bytes before queue admission.")
    return {
        "template": str(template),
        "template_sha256": digest,
        "destination": str(destination),
        "destination_sha256": _sha256(destination),
    }

def execute_native(
    operation: Mapping[str, Any],
    *,
    executor: Callable[[Sequence[str], str, int, str], int] | None = None,
) -> NativeResult:
    argv = [str(value) for value in operation["native"]["argv"]]
    log_path = Path(operation["native"]["log_path"])
    output_root = Path(argv[argv.index("--output-dir") + 1])
    log_path.parent.mkdir(parents=True, exist_ok=True)
    output_root.mkdir(parents=True, exist_ok=True)
    if log_path.exists() or any(output_root.iterdir()):
        raise FinalOperationError("NATIVE_RUN_COLLISION", str(output_root),
                                  "Each operation may be attempted at most once.")
    before = _snapshot(operation)
    started = time.time()

    def default_executor(command: Sequence[str], cwd: str, timeout: int, log: str) -> int:
        environment = os.environ.copy()
        environment.update(operation["native"]["environment"])
        with open(log, "w", encoding="utf-8") as native_log:
            process = subprocess.Popen(
                list(command), cwd=cwd, env=environment, stdout=native_log,
                stderr=subprocess.STDOUT, text=True,
            )
            try:
                return process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
                return 124

    runner = executor or default_executor
    returncode = runner(
        argv, str(operation["source_root"]),
        int(operation["native"]["timeout_seconds"]), str(log_path)
    )
    finished = time.time()
    after = _snapshot(operation)
    candidates = [
        path for path in output_root.glob("*.mp4")
        if path.is_file() and path.stat().st_mtime >= started - 1
    ]
    if not candidates:
        raise FinalOperationError(
            "NATIVE_NO_OUTPUT", f"exit={returncode}, output_root={output_root}",
            "Preserve the native log and stop without retry or substitution.",
        )
    output = max(candidates, key=lambda path: path.stat().st_mtime)
    return NativeResult(returncode, str(log_path), str(output), started, finished, before, after)

def _collect_evidence(
    operation: Mapping[str, Any], native: NativeResult
) -> dict[str, Any]:
    evidence_root = Path("datasets/runs/maestro-parity/ltx-dependency-terminalization/phase-b-run")
    operation_root = evidence_root / operation["operation_id"]
    operation_root.mkdir(parents=True, exist_ok=True)
    output = operation_root / f"wd_28ac_{operation['operation_id']}.mp4"
    if output.exists():
        raise FinalOperationError("EVIDENCE_OUTPUT_COLLISION", str(output),
                                  "Do not overwrite prior operation evidence.")
    shutil.copyfile(native.output_path, output)
    digest = _sha256(output)
    (operation_root / f"{output.name}.sha256").write_text(
        f"{digest}  {output.name}\n", encoding="utf-8"
    )
    ffprobe = operation_root / f"{output.name}.ffprobe.json"
    ffprobe_result = _run([
        "ffprobe", "-v", "error", "-show_streams", "-show_format",
        "-of", "json", str(output),
    ], timeout=120)
    if ffprobe_result["returncode"] != 0:
        raise FinalOperationError("FFPROBE_FAILED", ffprobe_result["stderr"],
                                  "Preserve output and native log; stop without retry.")
    ffprobe.write_text(ffprobe_result["stdout"], encoding="utf-8")
    first_frame = operation_root / "first-frame.png"
    contact_sheet = operation_root / "contact-sheet.jpg"
    for destination, video_filter in (
        (first_frame, "select=eq(n\\,0)"),
        (contact_sheet, "fps=6,scale=240:-1,tile=4x2"),
    ):
        result = _run([
            "ffmpeg", "-nostdin", "-v", "error", "-y", "-i", str(output),
            "-vf", video_filter, "-frames:v", "1", str(destination),
        ], timeout=300)
        if result["returncode"] != 0 or not destination.is_file():
            raise FinalOperationError("VISUAL_EVIDENCE_FAILED", result["stderr"],
                                      "Preserve all artifacts and stop without retry.")
    metadata = _read_json(ffprobe)
    video_stream = next(
        stream for stream in metadata["streams"] if stream.get("codec_type") == "video"
    )
    measured = {
        "valid_media": 1.0,
        "nonempty_output": float(output.stat().st_size > 0),
        "distinct_hash": 1.0,
    }
    if operation["operation"] == "upscale":
        reference = next(iter(operation["references"].values()))
        ref_probe = _run([
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=width", "-of", "csv=p=0", reference["host_path"],
        ], timeout=120)
        reference_width = int(ref_probe["stdout"].strip())
        measured["width_multiplier"] = float(video_stream["width"]) / reference_width
    return {
        "output": str(output),
        "output_size_bytes": output.stat().st_size,
        "output_sha256": digest,
        "ffprobe": str(ffprobe),
        "width": int(video_stream["width"]),
        "height": int(video_stream["height"]),
        "duration_s": float(metadata["format"]["duration"]),
        "visual": [str(contact_sheet), str(first_frame)],
        "objective_measurements": measured,
        "native_source_output": native.output_path,
    }

def run_batch(
    plan: Mapping[str, Any],
    authorization: Mapping[str, Any],
    template_root: Path,
    queue_db: Path,
    *,
    executor: Callable[[Sequence[str], str, int, str], int] | None = None,
    runtime_state: Mapping[str, Any] | None = None,
)-> dict[str, Any]:
    validate_contract(plan, authorization)
    if plan.get("mode") != "corrected_native_operations_authorized":
        raise FinalOperationError(
            "CORRECTED_HOST_RETRY_NOT_AUTHORIZED",
            f"mode={plan.get('mode')!r}",
            "Wait for the separate Jev corrected-host-retry gate.",
        )
    host_gate = authorization.get("jev_corrected_native_retry_host_authorization", {})
    if (authorization.get("schema_version") != IDENTITY_CAPTURE_AUTHORIZATION_SCHEMA
            and host_gate.get("host_execution_authorized") is not True):
        raise FinalOperationError(
            "CORRECTED_HOST_RETRY_NOT_AUTHORIZED",
            json.dumps(host_gate, sort_keys=True),
            "Bind the separate live corrected-host-retry gate.",
        )
    if runtime_state is None:
        raise FinalOperationError(
            "RUNTIME_STATE_REQUIRED", "runtime_state is absent",
            "Provide a fresh isolated-runtime preflight state.",
        )
    repository_root = plan.get("runner_repository_root")
    if not isinstance(repository_root, str) or not Path(repository_root).is_absolute():
        raise _stage_error("EXECUTION_REPOSITORY_IDENTITY_UNPROVEN",
                           "runner_repository_root must explicitly identify the Wangp checkout")
    validate_stage_inventory(plan.get("stage_inventory"), Path(repository_root), template_root)
    if (authorization.get("schema_version") == IDENTITY_CAPTURE_AUTHORIZATION_SCHEMA
            and plan["stage_inventory"]["repository"]["commit_sha"]
            != authorization["base_commit"]):
        raise _stage_error(
            "IDENTITY_CAPTURE_EXECUTION_COMMIT_MISMATCH",
            "Validated Wangp execution commit differs from the approved base_commit",
        )
    runtime_preflight = validate_runtime_state(runtime_state, require_fresh=True)
    if queue_db.exists():
        raise FinalOperationError(
            "QUEUE_DB_COLLISION", str(queue_db),
            "Use a new queue database; prior queue evidence is immutable.",
        )
    queue = JobQueue(str(queue_db))
    records = []
    try:
        for operation in plan["operations"]:
            staged = stage_settings(operation, template_root)
            clip = {
                "clip_index": 0,
                "kind": "wd_28ac_native_operation",
                "operation_id": operation["operation_id"],
                "row": operation["row"],
                "operation": operation["operation"],
                "status": "pending",
            }
            actual_job_id = queue.submit(
                plan_ref=operation["queue"]["queue_id"], clips=[clip]
            )
            queue.set_state(actual_job_id, "preflight")
            queue.claim_active(actual_job_id, owner_pid=os.getpid())
            record: dict[str, Any] = {
                "operation_id": operation["operation_id"],
                "planned_job_id": operation["queue"]["job_id"],
                "durable_job_id": actual_job_id,
                "queue_id": operation["queue"]["queue_id"],
                "settings": staged,
                "argv": operation["native"]["argv"],
                "environment": dict(operation["native"]["environment"]),
                "runtime_preflight": runtime_preflight,
                "admission_state": "admitted",
                "attempt": 1,
            }
            try:
                queue.set_state(actual_job_id, "rendering")
                native = execute_native(operation, executor=executor)
                if native.returncode != 0:
                    raise FinalOperationError(
                        "NATIVE_EXIT_FAILURE",
                        f"exit={native.returncode}, log={native.log_path}",
                        "Preserve log/output state and stop without retry.",
                    )
                evidence = _collect_evidence(operation, native)
                queue.update_clip(
                    actual_job_id, 0, status="rendered",
                    log=native.log_path, mp4=evidence["output"], qc_verdict=None,
                    lane="wd-28ac-native",
                )
                queue.set_state(actual_job_id, "rendered_pending_qc")
                record.update({
                    "status": "rendered_pending_qc",
                    "native": native.__dict__,
                    "evidence": evidence,
                    "queue_state": queue.get(actual_job_id).to_json(),
                })
                records.append(record)
                _write_json(Path(operation["native"]["log_path"]).parent / "operation-record.json", record)
            except FinalOperationError as exc:
                queue.record_failure(actual_job_id, failure_class=exc.code)
                queue.set_failure_detail(actual_job_id, exc.observed)
                queue.set_state(actual_job_id, "failed")
                record.update({
                    "status": "failed",
                    "boundary": {
                        "code": exc.code, "observed": exc.observed,
                        "remediation": exc.remediation,
                    },
                    "queue_state": queue.get(actual_job_id).to_json(),
                })
                records.append(record)
                _write_json(Path(operation["native"]["log_path"]).parent / "operation-record.json", record)
                return {
                    "status": "failed_closed",
                    "terminal_operation": operation["operation_id"],
                    "boundary": record["boundary"],
                    "operations": records,
                }
        return {
            "status": "all_native_renders_complete",
            "attempted": len(records),
            "operations": records,
        }
    finally:
        _write_json(queue_db.parent / "queue-summary.json", {
            "states": {state: queue.list_state(state) for state in (
                "pending", "preflight", "rendering", "rendered_pending_qc",
                "qc", "done", "failed", "dead_letter",
            )},
            "jobs": {record["durable_job_id"]: record for record in records},
        })
        queue.close()

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", required=True)
    parser.add_argument("--authorization", required=True)
    parser.add_argument("--template-root", default=".")
    parser.add_argument("--queue-db", required=True)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--allow-host", action="store_true")
    parser.add_argument("--runtime-state")
    return parser

def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    plan = _read_json(Path(args.plan))
    authorization = _read_json(Path(args.authorization))
    try:
        validate_contract(plan, authorization)
        if not args.execute:
            print(json.dumps({
                "status": "dry_run_validated", "operation_count": len(plan["operations"]),
                "queue_admissions": 0, "native_attempts": 0,
            }, sort_keys=True))
            return 0
        if not args.allow_host:
            raise FinalOperationError(
                "HOST_GUARD_REQUIRED", "--execute requires --allow-host",
                "Pass the explicit host guard only after Gate 7 CI."
            )
        if args.runtime_state is None:
            raise FinalOperationError(
                "RUNTIME_STATE_REQUIRED", "--runtime-state is absent",
                "Provide fresh isolated mmgp runtime preflight evidence.",
            )
        result = run_batch(
            plan, authorization, Path(args.template_root), Path(args.queue_db),
            runtime_state=_read_json(Path(args.runtime_state)),
        )
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["status"] == "all_native_renders_complete" else 2
    except FinalOperationError as exc:
        print(json.dumps({
            "status": "failed_closed", "code": exc.code,
            "observed": exc.observed, "remediation": exc.remediation,
        }, sort_keys=True))
        return 2


if __name__ == "__main__":
    sys.exit(main())
