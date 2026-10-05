#!/usr/bin/env python3
"""One-attempt isolated mmgp 3.7.14 runtime repair for WD-28ac."""
from __future__ import annotations

import argparse
import ast
import base64
import hashlib
import importlib.metadata
import json
import os
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence


PACKAGE = "mmgp"
VERSION = "3.7.14"
WHEEL_FILENAME = "mmgp-3.7.14-py3-none-any.whl"
METADATA_WHEEL_SIZE = 68_211
METADATA_WHEEL_SHA256 = (
    "6b544fa77a0256586bd9223c8f85c83a318c5d2f184b6adbdc655b7f22b5d208"
)
WHEEL_SIZE = 68_211
WHEEL_SHA256 = (
    "6b544fa77a0256586bd9223c8f85c83a318c5d2f184b6adbdc655b7f22b5d208"
)
GATE10_SNAPSHOT_SHA256 = (
    "38780b034bc9d862491a8ec846e2ae3d736647cb65720a3f3dc426ccddb3bb4f"
)
GATE10_TRACE_SHA256 = (
    "7415a00a2e25eb468b3afee919fd5515ab5be6903cf04559f2cf8fece99804cd"
)
GATE11_SNAPSHOT_SHA256 = (
    "a4b77d969d5b675e6e076175aa6bc62caa7d927a3548a03b8b93e1ca3d3a720e"
)
GATE11_TRACE_SHA256 = (
    "080d570ea8cc90df011d834d663d50bce562ff67961b32686957284f191c6f92"
)
DEPENDENCIES = ("torch", "optimum.quanto", "accelerate", "safetensors", "psutil")
DEFAULT_DESTINATION = (
    "/home/straughter/wd-28ac-final-gate7-20261003/runtime/mmgp-3.7.14"
)
EXPECTED_OPERATOR_WHEEL_LAYOUT_AUTHORIZATION = {
    "recorded_at": "2026-10-03T22:32:06Z",
    "decision": "Authorized",
    "verbatim_approval": (
        "Yes you are authorized. Scope: the immediately pending Gate 11 "
        "boundary only—accept the known root __init__.py member in the "
        "already downloaded, exact hash-verified mmgp-3.7.14 wheel if "
        "inspection confirms it is inert; extract the preserved wheel "
        "into /home/straughter/wd-28ac-final-gate7-20261003/runtime/"
        "mmgp-3.7.14; and verify isolated mmgp imports. No new network "
        "GET, dependency install, deletion, overwrite, native retry, QC "
        "start, queue admission, render, model/reference mutation, "
        "system-runtime mutation, or protected-file change."
    ),
    "prior_boundary": "WHEEL_MEMBER_OUTSIDE_DECLARED_PACKAGE",
    "wheel_filename": WHEEL_FILENAME,
    "wheel_size_bytes": WHEEL_SIZE,
    "wheel_sha256": WHEEL_SHA256,
    "root_member": "__init__.py",
    "inert_requirement": "empty_or_whitespace_or_module_docstring_only",
    "resume_scope": "preserved_wheel_extraction_import_once",
    "network_get_limit": 0,
    "destination": DEFAULT_DESTINATION,
    "dependency_installs": 0,
    "deletion_authorized": False,
    "overwrite_authorized": False,
    "native_retry_authorized": False,
    "qc_start_authorized": False,
    "queue_admission_authorized": False,
    "render_authorized": False,
    "model_or_reference_mutation_authorized": False,
    "system_or_live_runtime_mutation_authorized": False,
    "protected_file_change_authorized": False,
}


class RuntimeRepairError(ValueError):
    """Typed terminal boundary for the isolated runtime repair."""

    def __init__(self, code: str, observed: str, remediation: str) -> None:
        super().__init__(observed)
        self.code = code
        self.observed = observed
        self.remediation = remediation


@dataclass(frozen=True)
class FetchResult:
    path: Path
    status: int
    final_url: str
    content_length: str
    declared_request_count: int = 1
    undeclared_request_count: int = 0


@dataclass(frozen=True)
class WheelLayout:
    members: list[zipfile.ZipInfo]
    root_member: str | None = None
    root_classification: dict[str, Any] | None = None


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

def _run(argv: Sequence[str], timeout: int = 90) -> dict[str, Any]:
    try:
        result = subprocess.run(
            list(argv), text=True, capture_output=True, timeout=timeout,
            check=False,
        )
        return {
            "argv": list(argv), "returncode": result.returncode,
            "stdout": result.stdout, "stderr": result.stderr,
        }
    except Exception as exc:
        return {
            "argv": list(argv), "returncode": 124, "stdout": "",
            "stderr": f"{type(exc).__name__}: {exc}",
        }

def validate_metadata(metadata: Mapping[str, Any]) -> dict[str, Any]:
    info = metadata.get("info", {})
    if info.get("name") != PACKAGE or info.get("version") != VERSION:
        raise RuntimeRepairError(
            "METADATA_IDENTITY_MISMATCH",
            f"name={info.get('name')!r},version={info.get('version')!r}",
            "Use exactly the Gate 9 mmgp 3.7.14 metadata artifact.",
        )
    try:
        wheel = next(
            item for item in metadata["urls"]
            if item.get("filename") == WHEEL_FILENAME
        )
    except (KeyError, StopIteration, TypeError) as exc:
        raise RuntimeRepairError(
            "WHEEL_METADATA_ABSENT", "declared wheel URL entry is absent",
            "Use the exact PyPI metadata artifact without substitution.",
        ) from exc
    expected = {
        "filename": WHEEL_FILENAME,
        "size": METADATA_WHEEL_SIZE,
        "digests": {"sha256": METADATA_WHEEL_SHA256},
        "packagetype": "bdist_wheel",
    }
    observed = {
        "filename": wheel.get("filename"),
        "size": wheel.get("size"),
        "digests": {"sha256": wheel.get("digests", {}).get("sha256")},
        "packagetype": wheel.get("packagetype"),
    }
    if observed != expected:
        raise RuntimeRepairError(
            "WHEEL_METADATA_MISMATCH", json.dumps(observed, sort_keys=True),
            "Require exactly 68211 bytes and the Gate 10 SHA-256.",
        )
    return {
        "package": PACKAGE,
        "version": VERSION,
        "wheel_filename": WHEEL_FILENAME,
        "requires_python": info.get("requires_python"),
        "requires_dist": info.get("requires_dist"),
        "wheel_url": wheel["url"],
        "wheel_size": METADATA_WHEEL_SIZE,
        "wheel_sha256": METADATA_WHEEL_SHA256,
        "last_serial": metadata.get("last_serial"),
        "vulnerabilities": metadata.get("vulnerabilities"),
    }

def validate_gate10(
    gate_summary: Mapping[str, Any], authorization: Mapping[str, Any]
) -> None:
    gate = gate_summary.get("gates", {}).get("10", {})
    auth = authorization.get("jev_runtime_repair_authorization", {})
    expected_gate = {
        "gate": 10, "mode": "live", "model": "jev-latest",
        "decision": "CONTINUE", "confidence": 0.81,
        "constraint_risk": 0.29, "missing_evidence_score": 1.28,
        "scope": "ISOLATED_RUNTIME_REPAIR_ONLY",
        "declared_snapshot_sha256": GATE10_SNAPSHOT_SHA256,
        "declared_trace_sha256": GATE10_TRACE_SHA256,
    }
    for key, value in expected_gate.items():
        if gate.get(key) != value:
            raise RuntimeRepairError(
                "GATE10_EVIDENCE_INVALID",
                f"{key}={gate.get(key)!r}, expected={value!r}",
                "Bind the exact supplied live Gate 10 evidence.",
            )
    expected_auth = {
        "gate": 10, "mode": "live", "model": "jev-latest",
        "decision": "CONTINUE", "confidence": 0.81,
        "snapshot_sha256": GATE10_SNAPSHOT_SHA256,
        "trace_sha256": GATE10_TRACE_SHA256,
        "scope": "isolated_runtime_repair_only",
        "wheel_filename": WHEEL_FILENAME,
        "wheel_size_bytes": METADATA_WHEEL_SIZE,
        "wheel_sha256": METADATA_WHEEL_SHA256, "wheel_get_limit": 1,
        "dependency_installs": 0,
        "extract_destination": DEFAULT_DESTINATION,
        "isolated_python": "/usr/bin/python3", "import_isolated": True,
        "native_retry_authorized": False, "qc_start_authorized": False,
        "queue_admission_authorized": False, "render_authorized": False,
        "deletion_authorized": False,
        "model_or_reference_mutation_authorized": False,
        "evidence": "runtime-repair/2026-10-03/gate-summary.json",
    }
    if auth != expected_auth:
        raise RuntimeRepairError(
            "GATE10_AUTHORIZATION_INVALID", json.dumps(auth, sort_keys=True),
            "Bind the exact one-GET isolated runtime authorization.",
        )

def validate_gate11(
    gate_summary: Mapping[str, Any], authorization: Mapping[str, Any]
) -> None:
    expected_summary = {
        "gate": 11, "mode": "live", "model": "jev-latest",
        "decision": "CONTINUE", "confidence": 0.82,
        "constraint_risk": 0.28, "missing_evidence_score": 1.35,
        "scope": "CORRECTED_ISOLATED_RUNTIME_REPAIR_ONCE",
        "declared_snapshot_sha256": GATE11_SNAPSHOT_SHA256,
        "declared_trace_sha256": GATE11_TRACE_SHA256,
    }
    for key, value in expected_summary.items():
        if gate_summary.get(key) != value:
            raise RuntimeRepairError(
                "GATE11_EVIDENCE_INVALID",
                f"{key}={gate_summary.get(key)!r}, expected={value!r}",
                "Bind the exact supplied live Gate 11 evidence.",
            )
    expected_auth = {
        "gate": 11, "mode": "live", "model": "jev-latest",
        "decision": "CONTINUE", "confidence": 0.82,
        "snapshot_sha256": GATE11_SNAPSHOT_SHA256,
        "trace_sha256": GATE11_TRACE_SHA256,
        "scope": "corrected_isolated_runtime_repair_once",
        "dependency_probe": "exact_module_import",
        "wheel_filename": WHEEL_FILENAME,
        "wheel_size_bytes": METADATA_WHEEL_SIZE,
        "wheel_sha256": METADATA_WHEEL_SHA256,
        "wheel_get_limit": 1,
        "dependency_installs": 0,
        "extract_destination": DEFAULT_DESTINATION,
        "isolated_python": "/usr/bin/python3",
        "import_isolated": True,
        "native_retry_authorized": False,
        "qc_start_authorized": False,
        "queue_admission_authorized": False,
        "render_authorized": False,
        "deletion_authorized": False,
        "model_or_reference_mutation_authorized": False,
        "system_or_live_runtime_mutation_authorized": False,
        "protected_file_change_authorized": False,
        "prior_gate10_zero_request_boundary_preserved": True,
        "evidence": "runtime-repair/2026-10-03/gate-11-evidence.json",
    }
    auth = authorization.get("jev_corrected_runtime_repair_authorization", {})
    if auth != expected_auth:
        raise RuntimeRepairError(
            "GATE11_AUTHORIZATION_INVALID",
            json.dumps(auth, sort_keys=True),
            "Bind the exact corrected one-attempt authorization.",
        )

def validate_wheel_layout_authorization(
    authorization: Mapping[str, Any],
) -> None:
    record = authorization.get("operator_wheel_layout_authorization", {})
    if record != EXPECTED_OPERATOR_WHEEL_LAYOUT_AUTHORIZATION:
        raise RuntimeRepairError(
            "WHEEL_LAYOUT_AUTHORIZATION_INVALID",
            json.dumps(record, sort_keys=True),
            "Bind the exact operator preserved-wheel resume authorization.",
        )

def classify_root_member(content: bytes) -> dict[str, Any]:
    result: dict[str, Any] = {
        "byte_count": len(content),
        "sha256": hashlib.sha256(content).hexdigest(),
        "content_base64": base64.b64encode(content).decode("ascii"),
        "is_inert": False,
        "classification": "non_inert_statements",
        "ast_body_node_types": None,
    }
    try:
        decoded = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        result["classification"] = "invalid_utf8"
        result["decode_error"] = str(exc)
        return result
    if not content:
        result.update(is_inert=True, classification="empty")
        return result
    if not decoded.strip():
        result.update(is_inert=True, classification="whitespace_only")
        return result
    try:
        parsed = ast.parse(decoded, filename="__init__.py")
    except SyntaxError as exc:
        result["classification"] = "invalid_python"
        result["parse_error"] = str(exc)
        return result
    node_types = [type(node).__name__ for node in parsed.body]
    result["ast_body_node_types"] = node_types
    docstrings_only = all(
        isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
        for node in parsed.body
    )
    if not docstrings_only:
        return result
    result.update(
        is_inert=True,
        classification=(
            "comments_only" if not parsed.body else "module_docstring_only"
        ),
    )
    return result

def _state() -> dict[str, Any]:
    return {
        "gpu": _run([
            "nvidia-smi", "--query-gpu=name,memory.total,memory.used,memory.free,utilization.gpu",
            "--format=csv,noheader,nounits",
        ]),
        "gpu_apps": _run([
            "nvidia-smi", "--query-compute-apps=pid,process_name,used_memory",
            "--format=csv,noheader",
        ]),
        "disk": _run(["df", "-B1", "/home"]),
        "processes": _run(["ps", "-eo", "pid,comm,args"]),
    }

def _python_import(python: str, module: str, *, isolated_path: str | None = None,
                   timeout: int = 120,
                   require_metadata: bool = False) -> dict[str, Any]:
    code = (
        "import json,sys\n"
        + (
            "import importlib.metadata\n"
            if require_metadata else ""
        )
        + f"module=__import__({module!r},fromlist=['__name__'])\n"
        "print(json.dumps({'path':getattr(module,'__file__',None),"
        + (
            "'metadata_version':importlib.metadata.version("
            + repr(module.partition('.')[0]) + "),"
            if require_metadata else "'metadata_version':None,"
        )
        + "'python':sys.executable}))\n"
    )
    environment = os.environ.copy()
    if isolated_path is None:
        environment.pop("PYTHONPATH", None)
    else:
        environment["PYTHONPATH"] = isolated_path
    result = subprocess.run(
        [python, "-c", code], text=True, capture_output=True,
        timeout=timeout, check=False, env=environment,
    )
    return {
        "module": module, "returncode": result.returncode,
        "stdout": result.stdout, "stderr": result.stderr,
        "isolated_path": isolated_path,
    }

def _preservation_snapshot(
    manifest: Mapping[str, Any], operation_plan: Mapping[str, Any]
) -> dict[str, Any]:
    models = {}
    for asset in manifest["assets"]:
        path = Path(asset["destination"])
        models[asset["id"]] = {
            "path": str(path), "size_bytes": path.stat().st_size,
            "sha256": _sha256(path),
        }
    references = {}
    for operation in operation_plan["operations"]:
        for name, reference in operation["references"].items():
            path = Path(reference["host_path"])
            references[name] = {
                "path": str(path), "size_bytes": path.stat().st_size,
                "sha256": _sha256(path),
            }
    return {"models": models, "references": references}

def _default_fetch(url: str, destination: Path, timeout: int) -> FetchResult:
    request = urllib.request.Request(url, headers={"User-Agent": "wd-28ac-runtime-repair"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        status = response.status
        final_url = response.url
        content_length = response.headers.get("Content-Length", "")
        with destination.open("wb") as output:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                output.write(chunk)
    return FetchResult(
        destination, status, final_url, content_length,
        declared_request_count=1, undeclared_request_count=0,
    )

def validate_wheel(path: Path) -> None:
    size = path.stat().st_size
    digest = _sha256(path)
    if size != WHEEL_SIZE:
        raise RuntimeRepairError(
            "WHEEL_SIZE_MISMATCH", f"observed={size},expected={WHEEL_SIZE}",
            "Preserve the fetched bytes; do not retry or substitute.",
        )
    if digest != WHEEL_SHA256:
        raise RuntimeRepairError(
            "WHEEL_HASH_MISMATCH", f"observed={digest},expected={WHEEL_SHA256}",
            "Preserve the fetched bytes; do not retry or substitute.",
        )

def validate_wheel_members(
    archive: zipfile.ZipFile, *, allow_inert_root_init: bool = False
) -> WheelLayout:
    members = archive.infolist()
    seen: set[str] = set()
    allowed_roots = (f"{PACKAGE}/", f"{PACKAGE}-{VERSION}.dist-info/")
    outside_members: list[zipfile.ZipInfo] = []
    for member in members:
        name = member.filename
        normalized = os.path.normpath(name)
        if name in seen:
            raise RuntimeRepairError("WHEEL_DUPLICATE_MEMBER", name, "Reject ambiguous wheel members.")
        seen.add(name)
        if normalized.startswith(("/", "..")) or ".." in Path(normalized).parts:
            raise RuntimeRepairError("WHEEL_UNSAFE_MEMBER", name, "Refuse path escape before extraction.")
        mode = (member.external_attr >> 16) & 0o170000
        if mode == 0o120000:
            raise RuntimeRepairError("WHEEL_SYMLINK_MEMBER", name, "Refuse symlink extraction.")
        if not any(normalized.startswith(root) for root in allowed_roots):
            outside_members.append(member)
    root_member: zipfile.ZipInfo | None = None
    root_classification: dict[str, Any] | None = None
    if outside_members:
        names = [member.filename for member in outside_members]
        if (
            not allow_inert_root_init
            or len(outside_members) != 1
            or names != ["__init__.py"]
        ):
            raise RuntimeRepairError(
                "WHEEL_MEMBER_OUTSIDE_DECLARED_PACKAGE",
                ",".join(names),
                "Refuse extraction outside the mmgp/dist-info payload.",
            )
        root_member = outside_members[0]
        root_classification = classify_root_member(archive.read(root_member))
        if not root_classification["is_inert"]:
            raise RuntimeRepairError(
                "ROOT_MEMBER_NOT_INERT",
                json.dumps(root_classification, sort_keys=True),
                "Preserve the wheel/staging state; no retry is authorized.",
            )
    if archive.testzip() is not None:
        raise RuntimeRepairError("WHEEL_CRC_INVALID", "zip testzip reported a corrupt member", "Preserve wheel and stop.")
    return WheelLayout(
        members=members, root_member=root_member.filename if root_member else None,
        root_classification=root_classification,
    )

def extract_wheel(
    wheel: Path, destination: Path, *, resume: bool = False
) -> dict[str, Any]:
    staging = destination.parent / f".{destination.name}.extraction-staging"
    if destination.exists() or (not resume and staging.exists()):
        raise RuntimeRepairError(
            "EXTRACTION_DESTINATION_COLLISION",
            f"destination={destination},staging={staging}",
            "Stop without overwrite or deletion.",
        )
    if resume:
        if not staging.is_dir() or staging.is_symlink() or any(staging.iterdir()):
            raise RuntimeRepairError(
                "RESUME_STAGING_NOT_EMPTY_OR_ABSENT",
                f"staging={staging}",
                "Stop without overwrite or deletion.",
            )
    else:
        staging.mkdir(parents=True, exist_ok=False)
    with zipfile.ZipFile(wheel, "r") as archive:
        layout = validate_wheel_members(
            archive, allow_inert_root_init=resume
        )
        archive.extractall(staging)
    inventory = []
    root = staging.resolve()
    for path in sorted(item for item in staging.rglob("*") if item.is_file()):
        resolved = path.resolve()
        if not str(resolved).startswith(str(root) + os.sep):
            raise RuntimeRepairError("EXTRACTED_PATH_ESCAPE", str(path), "Stop without deletion.")
        inventory.append({
            "path": str(path.relative_to(staging)), "size_bytes": path.stat().st_size,
            "sha256": _sha256(path),
        })
    os.rename(staging, destination)
    return {
        "destination": str(destination),
        "file_count": len(inventory),
        "uncompressed_bytes": sum(item["size_bytes"] for item in inventory),
        "inventory": inventory,
        "root_member": layout.root_member,
        "root_classification": layout.root_classification,
    }

class RuntimeRepairRunner:
    def __init__(
        self,
        *,
        metadata_path: Path,
        gate_summary_path: Path,
        authorization_path: Path,
        manifest_path: Path,
        operation_plan_path: Path,
        runtime_root: Path,
        report_path: Path,
        destination: Path = Path(DEFAULT_DESTINATION),
        fetcher: Callable[[str, Path, int], FetchResult] | None = None,
        importer: Callable[[str, str], Mapping[str, Any]] | None = None,
    ) -> None:
        self.metadata_path = metadata_path
        self.gate_summary_path = gate_summary_path
        self.authorization_path = authorization_path
        self.manifest_path = manifest_path
        self.operation_plan_path = operation_plan_path
        self.runtime_root = runtime_root
        self.report_path = report_path
        self.destination = destination
        self.fetcher = fetcher or _default_fetch
        self.importer = importer or (lambda module, path: _python_import(
            "/usr/bin/python3", module, isolated_path=path,
            require_metadata=module == PACKAGE,
        ))
        self.report: dict[str, Any] = {
            "schema_version": "wangp-dspy.wd-28ac.isolated-runtime-repair/v1",
            "story": "WD-28ac", "gate": 10,
            "status": "in_progress", "dependency_installs": 0,
            "network_accounting": {
                "declared_wheel_gets": 0, "undeclared_requests": 0,
                "wheel_get_limit": 1,
            },
            "boundary_counters": {
                "native_retries": 0, "qc_starts": 0, "queue_admissions": 0,
                "renders": 0, "deletions": 0, "model_mutations": 0,
                "reference_mutations": 0, "protected_file_changes": 0,
            },
        }

    def _fail(self, code: str, observed: str, remediation: str) -> None:
        self.report["status"] = "failed_closed"
        self.report["boundary"] = {
            "code": code, "observed": observed, "remediation": remediation,
        }
        if not os.path.lexists(self.report_path):
            _write_json(self.report_path, self.report)

    def validate_documents(self, *, resume: bool = False) -> dict[str, Any]:
        metadata = validate_metadata(_read_json(self.metadata_path))
        gate_summary = _read_json(self.gate_summary_path)
        authorization = _read_json(self.authorization_path)
        if gate_summary.get("gate") == 11:
            validate_gate11(gate_summary, authorization)
            if resume:
                validate_wheel_layout_authorization(authorization)
        else:
            validate_gate10(gate_summary, authorization)
        self.report["gate"] = int(gate_summary.get("gate", 10))
        return metadata

    def preflight(self, *, resume: bool = False) -> dict[str, Any]:
        state = _state()
        if state["gpu_apps"]["stdout"].strip():
            raise RuntimeRepairError(
                "GPU_NOT_IDLE", state["gpu_apps"]["stdout"].strip(),
                "Stop before network; no process action is authorized.",
            )
        dependencies = {}
        for module in DEPENDENCIES:
            probe = self.importer(module, "")
            dependencies[module] = probe
            if probe.get("returncode") != 0:
                raise RuntimeRepairError(
                    "DECLARED_DEPENDENCY_IMPORT_FAILED",
                    f"module={module},stderr={probe.get('stderr','')[-300:]}",
                    "No dependency install is authorized.",
                )
        system_mmgp = self.importer(PACKAGE, "")
        if system_mmgp_ok(system_mmgp):
            raise RuntimeRepairError(
                "SYSTEM_MMGP_ALREADY_PRESENT",
                json.dumps(system_mmgp, sort_keys=True),
                "No system/live runtime mutation is authorized.",
            )
        wheel = self.runtime_root / WHEEL_FILENAME
        destination = self.destination
        staging = destination.parent / f".{destination.name}.extraction-staging"
        if resume:
            if os.path.lexists(self.report_path):
                raise RuntimeRepairError(
                    "RESUME_STATE_COLLISION", f"report={self.report_path}",
                    "Stop without overwriting preserved evidence.",
                )
            if (
                not self.runtime_root.is_dir()
                or self.runtime_root.is_symlink()
                or not wheel.is_file()
                or wheel.is_symlink()
                or not staging.is_dir()
                or staging.is_symlink()
                or any(staging.iterdir())
                or os.path.lexists(destination)
            ):
                raise RuntimeRepairError(
                    "RESUME_STATE_COLLISION",
                    (
                        f"runtime_root={self.runtime_root},wheel={wheel},"
                        f"destination={destination},staging={staging},"
                        f"report={self.report_path}"
                    ),
                    "Stop without overwrite or deletion.",
                )
            children = sorted(path.name for path in self.runtime_root.iterdir())
            if children != sorted((WHEEL_FILENAME, staging.name)):
                raise RuntimeRepairError(
                    "RESUME_STATE_COLLISION",
                    f"runtime_children={children}",
                    "Only the preserved wheel and empty staging are allowed.",
                )
            validate_wheel(wheel)
            with zipfile.ZipFile(wheel, "r") as archive:
                layout = validate_wheel_members(
                    archive, allow_inert_root_init=True
                )
            return {
                "state": state, "dependencies": dependencies,
                "system_mmgp": system_mmgp, "wheel_path": str(wheel),
                "destination": str(destination), "staging": str(staging),
                "runtime_children": children,
                "root_member": {
                    "member": layout.root_member,
                    "classification": layout.root_classification,
                },
            }
        if self.runtime_root.exists() or wheel.exists() or destination.exists() or staging.exists():
            raise RuntimeRepairError(
                "RUNTIME_PATH_COLLISION",
                f"runtime_root={self.runtime_root},wheel={wheel},destination={destination},staging={staging}",
                "Stop without overwrite or deletion.",
            )
        return {
            "state": state, "dependencies": dependencies,
            "system_mmgp": system_mmgp, "wheel_path": str(wheel),
            "destination": str(destination), "staging": str(staging),
        }

    def run(self, *, resume: bool = False) -> Mapping[str, Any]:
        try:
            metadata = self.validate_documents(resume=resume)
            self.report["metadata"] = metadata
            preflight = self.preflight(resume=resume)
            self.report["preflight"] = preflight
            self.report["preservation_before"] = _preservation_snapshot(
                _read_json(self.manifest_path),
                _read_json(self.operation_plan_path),
            )
            wheel_path = Path(preflight["wheel_path"])
            if resume:
                self.report["mode"] = "resume_preserved_wheel"
                self.report["network_accounting"] = {
                    "declared_wheel_gets": 0,
                    "undeclared_requests": 0,
                    "wheel_get_limit": 0,
                }
                validate_wheel(wheel_path)
                self.report["wheel"] = {
                    "path": str(wheel_path),
                    "size_bytes": wheel_path.stat().st_size,
                    "sha256": _sha256(wheel_path),
                }
                self.report["root_member"] = preflight["root_member"]
                _write_json(self.report_path, self.report)

                extraction = extract_wheel(
                    wheel_path, Path(preflight["destination"]), resume=True
                )
                self.report["extraction"] = extraction
            else:
                self.runtime_root.mkdir(parents=True, exist_ok=False)
                wheel = Path(preflight["wheel_path"])
                fetched = self.fetcher(metadata["wheel_url"], wheel, 300)
                self.report["network_accounting"] = {
                    "declared_wheel_gets": 1,
                    "undeclared_requests": int(fetched.undeclared_request_count),
                    "wheel_get_limit": 1,
                    "http_status": fetched.status,
                    "final_url": fetched.final_url,
                    "content_length": fetched.content_length,
                }
                validate_wheel(wheel)
                self.report["wheel"] = {
                    "path": str(wheel), "size_bytes": wheel.stat().st_size,
                    "sha256": _sha256(wheel),
                }
                _write_json(self.report_path, self.report)

                extraction = extract_wheel(wheel, Path(preflight["destination"]))
                self.report["extraction"] = extraction
            imported = self.importer(PACKAGE, preflight["destination"])
            self.report["isolated_import"] = imported
            if imported.get("returncode") != 0:
                raise RuntimeRepairError(
                    "ISOLATED_IMPORT_FAILED", imported.get("stderr", ""),
                    "Preserve extraction; do not install dependencies or retry.",
                )
            try:
                imported_payload = json.loads(imported.get("stdout", "{}"))
            except json.JSONDecodeError as exc:
                raise RuntimeRepairError(
                    "ISOLATED_IMPORT_OUTPUT_INVALID",
                    imported.get("stdout", ""),
                    "Require the structured path/version import probe.",
                ) from exc
            path = str(imported_payload.get("path", ""))
            if not path or not path.startswith(preflight["destination"]):
                raise RuntimeRepairError(
                    "ISOLATED_IMPORT_PATH_INVALID", path,
                    "Import must resolve inside the declared extraction destination.",
                )
            if imported_payload.get("metadata_version") != VERSION:
                raise RuntimeRepairError(
                    "ISOLATED_IMPORT_VERSION_INVALID",
                    str(imported_payload.get("metadata_version")),
                    f"Require mmgp {VERSION}.",
                )
            post_system = self.importer(PACKAGE, "")
            if system_mmgp_ok(post_system):
                raise RuntimeRepairError(
                    "SYSTEM_RUNTIME_MUTATED", json.dumps(post_system, sort_keys=True),
                    "Only PYTHONPATH-isolated import was authorized.",
                )
            self.report["post_system_mmgp"] = post_system
            self.report["state_after"] = _state()
            self.report["preservation_after"] = _preservation_snapshot(
                _read_json(self.manifest_path),
                _read_json(self.operation_plan_path),
            )
            preservation_ok = (
                self.report["preservation_before"] == self.report["preservation_after"]
            )
            if not preservation_ok:
                raise RuntimeRepairError(
                    "PROTECTED_ASSET_CHANGED", "before/after preservation snapshot differs",
                    "Preserve all evidence and stop.",
                )
            self.report["preservation_unchanged"] = True
            self.report["status"] = "passed"
            _write_json(self.report_path, self.report)
            return self.report
        except RuntimeRepairError as exc:
            self._fail(exc.code, exc.observed, exc.remediation)
            raise
        except Exception as exc:
            self._fail(
                "UNEXPECTED_RUNTIME_REPAIR_FAILURE",
                f"{type(exc).__name__}: {exc}",
                "Preserve wheel/destination/report and stop without retry.",
            )
            raise


def system_mmgp_ok(probe: Mapping[str, Any]) -> bool:
    """The import probe uses subprocess and may be injected in tests."""
    return probe.get("returncode") == 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--metadata", required=True)
    parser.add_argument("--gate-summary", required=True)
    parser.add_argument("--authorization", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--operation-plan", required=True)
    parser.add_argument("--runtime-root", default="/home/straughter/wd-28ac-final-gate7-20261003/runtime")
    parser.add_argument("--report", required=True)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--allow-network", action="store_true")
    parser.add_argument("--resume-preserved-wheel", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    runner = RuntimeRepairRunner(
        metadata_path=Path(args.metadata),
        gate_summary_path=Path(args.gate_summary),
        authorization_path=Path(args.authorization),
        manifest_path=Path(args.manifest),
        operation_plan_path=Path(args.operation_plan),
        runtime_root=Path(args.runtime_root),
        report_path=Path(args.report),
    )
    try:
        metadata = runner.validate_documents(
            resume=args.resume_preserved_wheel
        )
        if not args.execute:
            payload = {
                "status": "dry_run_validated", "wheel": {
                    "filename": metadata["wheel_filename"],
                    "size": metadata["wheel_size"],
                    "sha256": metadata["wheel_sha256"],
                },
                "declared_wheel_gets": 0, "dependency_installs": 0,
            }
            if args.resume_preserved_wheel:
                payload["mode"] = "resume_preserved_wheel"
                payload["network_get_limit"] = 0
            print(json.dumps(payload, sort_keys=True))
            return 0
        if args.resume_preserved_wheel:
            if args.allow_network:
                raise RuntimeRepairError(
                    "NETWORK_FORBIDDEN_IN_RESUME_MODE",
                    "--allow-network was supplied",
                    "Preserved-wheel resume must issue zero GETs.",
                )
            runner.run(resume=True)
            return 0
        if not args.allow_network:
            raise RuntimeRepairError(
                "NETWORK_GUARD_REQUIRED", "--execute requires --allow-network",
                "Pass the guard only after Gate 10 exact-head CI.",
            )
        runner.run()
        return 0
    except RuntimeRepairError as exc:
        print(json.dumps({
            "status": "failed_closed", "code": exc.code,
            "observed": exc.observed, "remediation": exc.remediation,
        }, sort_keys=True))
        return 2


if __name__ == "__main__":
    sys.exit(main())
