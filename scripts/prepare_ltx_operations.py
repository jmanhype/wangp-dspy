#!/usr/bin/env python3
"""Fail-closed local WD-28ac Phase B operation planner."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence


RUN_DIR = Path(
    "datasets/runs/maestro-parity/ltx-dependency-terminalization"
)
GATE4_SNAPSHOT_SHA256 = (
    "38e9b171448464138e18ba6b4987d43c48a1f65df9f3bfc3da628418b2c58500"
)
GATE4_TRACE_SHA256 = (
    "1636e28fb5dbc9945c9fbe98df51500b560c5e9b06792d9798bad4823d283b9d"
)
GATE7_SNAPSHOT_SHA256 = (
    "ed82d6d2fbb2cf7f9745a55625ec8850d2cb1ff9c70514634ce9698b85f9091c"
)
GATE7_TRACE_SHA256 = (
    "21709889328392ed0e33a76ccadd16eeb284fd45278ea36b94a6161b4a9bf7b7"
)
EXPECTED_TREES = {
    "m7xw": ("faea82d15bf10b3479c42c0ea430892aae975870", "?? ckpts"),
    "osfm": ("4c93b64a47b5b0a915f2abec2ce754be98227150", "?? ckpts"),
}
REFERENCES = {
    "m7xw_create": {
        "path": "outputs/create/wd_m7xw_create.mp4",
        "sha256": "f05bc6e13ce6e25d753c9282d931a27ae73ebca3ededd409400f28181bf6441f",
        "story": "WD-m7xw",
    },
    "m7xw_first_frame": {
        "path": "outputs/create/first-frame.png",
        "sha256": "36e3f0a105931e9148697b446980923ce078352741d1213761c8215d38e8a19f",
        "story": "WD-m7xw",
    },
    "m7xw_repaint_mask": {
        "path": "inputs/repaint-mask.mp4",
        "sha256": "a8e569befaef39c5784fdec783da7a0153e2908c3be6e4ceed6d6a658eb13386",
        "story": "WD-m7xw",
    },
    "osfm_control": {
        "path": "inputs/control.mp4",
        "sha256": "1fb5689ac1647dda8ddd0806981eb0ee93a2ca641956ea3848fce65aad817a2a",
        "story": "WD-osfm",
    },
    "osfm_alternate_reference": {
        "path": "inputs/alternate-reference.png",
        "sha256": "f3a757b4225770edeaa0088063b4f3b383f971a124d07894f2d1e2dacec5199f",
        "story": "WD-osfm",
    },
    "osfm_create": {
        "path": "outputs/create/wd_osfm_create.mp4",
        "sha256": "d489d46173a3fe54e21577353ed98c76cf351610eafa0f44e279e8241a932957",
        "story": "WD-osfm",
    },
}
OPERATIONS: tuple[dict[str, Any], ...] = (
    {
        "operation_id": "ltx25-outpaint",
        "row": "LTX-2.5", "operation": "outpaint",
        "asset_id": "ltx-2.3-22b-ic-lora-outpaint.safetensors",
        "references": ["m7xw_create"],
        "template": "WD-m7xw/native-settings/outpaint.json",
        "command_pattern": "wd-m7xw-single-operation",
    },
    {
        "operation_id": "ltx25-repaint",
        "row": "LTX-2.5", "operation": "repaint",
        "asset_id": "ltx-2.3-22b-ic-lora-in-outpainting-0.9.safetensors",
        "references": ["m7xw_create", "m7xw_repaint_mask"],
        "template": "WD-m7xw/native-settings/repaint.json",
        "command_pattern": "wd-m7xw-single-operation",
    },
    {
        "operation_id": "ltx25-recast",
        "row": "LTX-2.5", "operation": "recast",
        "asset_id": "ltx-2.3-22b-ic-lora-ingredients-0.9.safetensors",
        "references": ["m7xw_first_frame"],
        "template": "WD-m7xw/native-settings/recast.json",
        "command_pattern": "wd-m7xw-single-operation",
    },
    {
        "operation_id": "ltx25-upscale",
        "row": "LTX-2.5", "operation": "upscale",
        "asset_id": "ltx-2.5-22b-ic-lora-pixel-spatial-upscaler-x2-1.0.safetensors",
        "references": ["m7xw_create"],
        "template": "WD-m7xw/native-settings/upscale.json",
        "command_pattern": "wd-m7xw-single-operation",
    },
    {
        "operation_id": "ltx23-outpaint",
        "row": "LTX-2.3", "operation": "outpaint",
        "asset_id": "ltx-2.3-22b-ic-lora-outpaint.safetensors",
        "references": ["osfm_control"],
        "template": "WD-osfm/native-settings/outpaint-probe.json",
        "command_pattern": "wd-osfm-separated-probe",
    },
    {
        "operation_id": "ltx23-recast",
        "row": "LTX-2.3", "operation": "recast",
        "asset_id": "ltx-2.3-22b-ic-lora-ingredients-0.9.safetensors",
        "references": ["osfm_alternate_reference"],
        "template": "WD-osfm/native-settings/recast-probe.json",
        "command_pattern": "wd-osfm-separated-probe",
    },
    {
        "operation_id": "ltx23-upscale",
        "row": "LTX-2.3", "operation": "upscale",
        "asset_id": "ltx-2.3-22b-dev_diffusion_model_quanto_int8.safetensors",
        "references": ["osfm_create"],
        "template": "WD-osfm/native-settings/upscale.json",
        "command_pattern": "wd-osfm-upscale",
    },
)
EXPECTED_CELLS = frozenset(
    (item["row"], item["operation"]) for item in OPERATIONS
)
ALLOWED_NEW_MATRIX_STATUSES = frozenset({
    "host_run_verified", "operator_approved_terminal_boundary"
})


class PhaseBPlanningError(ValueError):
    """Typed local Phase B planning boundary."""

    def __init__(self, code: str, observed: str, remediation: str) -> None:
        super().__init__(observed)
        self.code = code
        self.observed = observed
        self.remediation = remediation


class HostExecutionDisabledError(PhaseBPlanningError):
    """Raised when local-only Phase B is asked to execute host work."""


@dataclass(frozen=True)
class PreflightCheck:
    name: str
    passed: bool
    observed: str


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))

def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def _check(
    name: str, passed: bool, observed: str
) -> PreflightCheck:
    return PreflightCheck(name, bool(passed), observed)

def validate_gate4_authorization(
    authorization: Mapping[str, Any], gate_evidence: Mapping[str, Any]
) -> list[PreflightCheck]:
    gate = authorization.get("jev_phase_b_preparation_authorization", {})
    evidence_gate = gate_evidence.get("gates", {}).get("4", {})
    exact = gate == {
        "gate": 4,
        "mode": "live",
        "model": "jev-latest",
        "decision": "CONTINUE",
        "confidence": 0.78,
        "snapshot_sha256": GATE4_SNAPSHOT_SHA256,
        "trace_sha256": GATE4_TRACE_SHA256,
        "scope": "local_phase_b_preparation_only",
        "host_execution_authorized": False,
        "evidence": "jev-gates/2026-10-03/gate-3-4-evidence.json",
    }
    evidence_match = (
        evidence_gate.get("declared_snapshot_sha256") == GATE4_SNAPSHOT_SHA256
        and evidence_gate.get("declared_trace_sha256") == GATE4_TRACE_SHA256
        and evidence_gate.get("decision") == "CONTINUE"
    )
    return [
        _check("authorization_gate4_record", exact, json.dumps(gate, sort_keys=True)),
        _check("authorization_gate4_evidence", evidence_match, "gate-3-4 evidence binding"),
        _check(
            "host_execution_disabled",
            authorization.get("jev_phase_b_preparation_authorization", {}).get(
                "host_execution_authorized"
            ) is False,
            "Phase B host execution must remain disabled",
        ),
    ]

def validate_gate7_authorization(
    authorization: Mapping[str, Any], gate_evidence: Mapping[str, Any]
) -> list[PreflightCheck]:
    gate = authorization.get("jev_final_operations_authorization", {})
    expected = {
        "gate": 7,
        "mode": "live",
        "model": "jev-latest",
        "decision": "CONTINUE",
        "confidence": 0.80,
        "snapshot_sha256": GATE7_SNAPSHOT_SHA256,
        "trace_sha256": GATE7_TRACE_SHA256,
        "scope": "final_native_operations",
        "max_attempts_per_operation": 1,
        "retry": "never",
        "stop_on_first_terminal_failure": True,
        "operations_authorized": True,
        "matrix_cells_authorized": 7,
        "evidence": "jev-gates/2026-10-03/gate-7-evidence.json",
    }
    evidence = gate_evidence.get("gates", {}).get("7", gate_evidence)
    evidence_ok = (
        evidence.get("declared_snapshot_sha256") == GATE7_SNAPSHOT_SHA256
        and evidence.get("declared_trace_sha256") == GATE7_TRACE_SHA256
        and evidence.get("decision") == "CONTINUE"
    )
    return [
        _check("authorization_gate7_record", gate == expected, json.dumps(gate, sort_keys=True)),
        _check("authorization_gate7_evidence", evidence_ok, "gate-7 evidence binding"),
    ]

def evaluate_preflight(
    manifest: Mapping[str, Any],
    authorization: Mapping[str, Any],
    gate_evidence: Mapping[str, Any],
    postflight: Mapping[str, Any],
) -> list[PreflightCheck]:
    checks: list[PreflightCheck] = []
    if postflight.get("final_operations") and "jev_final_operations_authorization" in authorization:
        checks += validate_gate7_authorization(authorization, gate_evidence)
    else:
        checks += validate_gate4_authorization(authorization, gate_evidence)
    qc = postflight.get("phase_bounds", {}).get("qc_contacted")
    # A future host gate must provide a healthy, locally reachable QC fact.
    # Phase A deliberately supplies no such fact.
    checks.append(_check("qc_healthy", postflight.get("qc", {}).get("healthy") is True, f"qc_contacted={qc!r}"))
    free_bytes = int(postflight.get("disk_free_bytes", postflight.get("disk", {}).get("free_bytes", 0)))
    checks.append(_check("disk_headroom", free_bytes >= 1024**3, f"free_bytes={free_bytes}"))
    gpu = postflight.get("gpu", {})
    gpu_free = int(gpu.get("memory_free_mib", gpu.get("free_mib", 0)))
    checks.append(_check("gpu_idle", gpu.get("compute_apps") == [] and gpu_free > 0, f"free_mib={gpu_free},apps={gpu.get('compute_apps')!r}"))
    for tree_name, (commit, status) in EXPECTED_TREES.items():
        observed = postflight.get("trees", {}).get(tree_name, {})
        checks.append(_check(
            f"tree_{tree_name}",
            observed.get("commit") == commit and observed.get("status") == status,
            f"commit={observed.get('commit')!r},status={observed.get('status')!r}",
        ))
    assets = postflight.get("models", {})
    for asset in manifest["assets"]:
        observed = assets.get(asset["id"], {})
        checks.append(_check(
            f"model_{asset['id']}",
            observed.get("sha256") == asset["sha256"]
            and observed.get("size_bytes") == asset["size_bytes"],
            f"size={observed.get('size_bytes')!r},sha256={observed.get('sha256')!r}",
        ))
    observed_refs = postflight.get("references", {})
    for name, expected in REFERENCES.items():
        observed = observed_refs.get(name, {})
        checks.append(_check(
            f"reference_{name}",
            observed.get("sha256") == expected["sha256"],
            f"path={observed.get('path')!r},sha256={observed.get('sha256')!r}",
        ))
    return checks

def _command_for(
    item: Mapping[str, Any], native_python: str, source_root: str, run_root: str
) -> list[str]:
    settings = f"{run_root}/{item['operation_id']}/settings.json"
    output = f"{run_root}/{item['operation_id']}/native-output"
    command = [native_python, f"{source_root}/wgp.py", "--process", settings]
    if item["command_pattern"] != "wd-osfm-upscale":
        command += ["--profile", "3", "--attention", "sdpa"]
    return command + ["--output-dir", output]

def _objective_gates(item: Mapping[str, Any]) -> list[dict[str, Any]]:
    gates = [
        {"name": "valid_media", "threshold": 1.0, "measurement": "ffprobe valid video"},
        {"name": "nonempty_output", "threshold": 1.0, "measurement": "output bytes"},
        {"name": "distinct_hash", "threshold": 1.0, "measurement": "unique SHA-256 count"},
    ]
    if item["operation"] == "upscale":
        gates.append({
            "name": "width_multiplier", "threshold": 2.0,
            "measurement": "output_width / reference_width",
        })
    return gates

def build_plan(
    repository_root: Path,
    preflight_path: Path,
    postflight_path: Path,
    authorization_path: Path,
    gate_evidence_path: Path,
    native_python: str = "/usr/bin/python3",
    final_operations: bool = False,
) -> dict[str, Any]:
    run_root = repository_root / RUN_DIR
    manifest = _read_json(run_root / "model-assets.json")
    authorization = _read_json(authorization_path)
    gate_evidence = _read_json(gate_evidence_path)
    raw_postflight = _read_json(postflight_path)
    raw_preflight = _read_json(preflight_path)
    facts = _local_facts_from_snapshots(
        repository_root, raw_preflight, raw_postflight
    )
    facts["final_operations"] = final_operations
    checks = evaluate_preflight(manifest, authorization, gate_evidence, facts)
    wgp_root = str(Path(manifest["assets"][0]["destination"]).parent.parent)
    run_root_remote = str(Path(wgp_root).parent / "wd-28ac-run" / "phase-b-gate5")
    operations = []
    for item in OPERATIONS:
        template = repository_root / "datasets/runs/maestro-parity" / item["template"]
        if not template.is_file():
            raise PhaseBPlanningError(
                "NATIVE_TEMPLATE_ABSENT", str(template), "Restore accepted evidence without substitution."
            )
        output_name = f"wd_28ac_{item['operation_id']}.mp4"
        evidence_dir = f"phase-b-run/{item['operation_id']}"
        source_root = str(Path(wgp_root).parent / (
            "Wan2GP-story-WD-m7xw" if item["row"] == "LTX-2.5"
            else "Wan2GP-story-WD-osfm"
        ))
        operations.append({
            **item,
            "status": "planned_not_executed",
            "source_root": source_root,
            "queue": {
                "queue_id": f"wd-28ac-phase-b-{item['operation_id']}",
                "job_id": f"wd-28ac-{item['operation_id']}-attempt-1",
                "retry_id": "attempt-1",
                "admission_state": "planned_not_admitted",
            },
            "native": {
                "template_path": f"datasets/runs/maestro-parity/{item['template']}",
                "template_sha256": _sha256(template),
                "settings_stage_path": f"{run_root_remote}/{item['operation_id']}/settings.json",
                "argv": _command_for(item, native_python, source_root, run_root_remote),
                "log_path": f"{run_root_remote}/{item['operation_id']}/native.log",
                "timeout_seconds": 5400,
            },
            "references": {
                name: {
                    **REFERENCES[name],
                    "host_path": str(
                        Path(source_root).parent / (
                            "wd-m7xw-run" if REFERENCES[name]["story"] == "WD-m7xw"
                            else "wd-osfm-run"
                        ) / REFERENCES[name]["path"]
                    ),
                    "resolved_path": str(
                        repository_root / "datasets/runs/maestro-parity"
                        / REFERENCES[name]["story"] / REFERENCES[name]["path"]
                    ),
                }
                for name in item["references"]
            },
            "evidence_expectations": {
                "output": f"{evidence_dir}/{output_name}",
                "sha256": f"{evidence_dir}/{output_name}.sha256",
                "ffprobe": f"{evidence_dir}/{output_name}.ffprobe.json",
                "visual": [f"{evidence_dir}/contact-sheet.jpg", f"{evidence_dir}/first-frame.png"],
                "objective_gates": _objective_gates(item),
                "checker": {
                    "argv": [".venv/bin/python", "scripts/verify_maestro_parity.py", evidence_dir],
                    "required_result": "PASS",
                },
                "reviewer": {"decision": "approved", "independent": True},
            },
            "attempt_policy": {
                "max_attempts": 1,
                "retry": "never",
                "terminal_success": "verified_output",
                "terminal_failure": "typed_native_boundary",
                "inherit_evidence": False,
            },
        })
    ready = all(check.passed for check in checks)
    return {
        "schema_version": "wangp-dspy.wd-28ac.phase-b-operation-plan/v1",
        "story": "WD-28ac",
        "mode": (
            "final_native_operations_authorized"
            if final_operations and "jev_final_operations_authorization" in authorization
            else "local_preparation_only"
        ),
        "host_execution_authorized": (
            final_operations and "jev_final_operations_authorization" in authorization
        ),
        "native_python": native_python,
        "preflight_ready": ready,
        "preflight_checks": [check.__dict__ for check in checks],
        "scheduling": {
            "operation_count": len(operations),
            "order": [item["operation_id"] for item in operations],
            "stop_policy": "stop_queue_on_first_terminal_failure",
            "matrix_transition": "not_applied",
        },
        "operations": operations,
    }

def _local_facts_from_snapshots(
    repository_root: Path,
    preflight: Mapping[str, Any],
    postflight: Mapping[str, Any],
) -> dict[str, Any]:
    host_home = Path(next(iter(preflight["trees"]))).parent
    gpu_query = preflight.get("gpu", {}).get("query", {}).get("stdout", "")
    values = [value.strip() for value in gpu_query.split(",")]
    memory_free = int(values[3]) if len(values) >= 4 else 0
    compute = preflight.get("gpu_apps", {}).get("stdout", "").strip()
    raw_trees = preflight.get("trees", {})
    trees = {}
    for tree_name in EXPECTED_TREES:
        path = next(
            (path for path in raw_trees if path.endswith(f"WD-{tree_name}")), ""
        )
        observed = raw_trees.get(path, {})
        trees[tree_name] = {
            "commit": observed.get("observed_commit"),
            "status": observed.get("observed_status"),
        }
    return {
        "qc": {"healthy": postflight.get("qc_healthy") is True},
        "disk_free_bytes": int(next(
            line.split()[3]
            for line in postflight.get("disk", {}).get("stdout", "").splitlines()
            if line.strip() and not line.lstrip().startswith("Filesystem")
        )),
        "gpu": {"memory_free_mib": memory_free, "compute_apps": [] if not compute else [compute]},
        "trees": trees,
        "models": {
            name: item["final"] for name, item in postflight.get("assets", {}).items()
        },
            "references": {
                name: {
                    "host_path": str(
                        host_home / (
                            "wd-m7xw-run" if expected["story"] == "WD-m7xw"
                            else "wd-osfm-run"
                        ) / expected["path"]
                    ),
                    "path": str(
                    repository_root / "datasets/runs/maestro-parity"
                    / expected["story"] / expected["path"]
                ),
                "sha256": _sha256(
                    repository_root / "datasets/runs/maestro-parity"
                    / expected["story"] / expected["path"]
                ),
            }
            for name, expected in REFERENCES.items()
        },
    }

def validate_matrix_transition(
    before: Mapping[str, str], after: Mapping[str, str]
) -> list[dict[str, str]]:
    if set(before) != set(after):
        raise PhaseBPlanningError(
            "MATRIX_KEY_SET_DRIFT", "before/after key sets differ", "Do not add or remove matrix cells."
        )
    changes = []
    for key in sorted(before):
        if before[key] == after[key]:
            continue
        cell = key if isinstance(key, tuple) else tuple(key.rsplit("/", 1))
        if cell not in EXPECTED_CELLS:
            raise PhaseBPlanningError(
                "UNOWNED_MATRIX_TRANSITION", f"unowned cell changed: {key}", "Only the seven WD-28ac cells may change."
            )
        if before[key] != "dependency_blocked":
            raise PhaseBPlanningError(
                "INVALID_OLD_MATRIX_STATUS", f"{key} old status is {before[key]!r}", "Expected dependency_blocked."
            )
        if after[key] not in ALLOWED_NEW_MATRIX_STATUSES:
            raise PhaseBPlanningError(
                "INVALID_NEW_MATRIX_STATUS", f"{key} new status is {after[key]!r}", "Use a terminal verifier-approved status."
            )
        changes.append({"cell": key, "from": before[key], "to": after[key]})
    if len(changes) != 7:
        raise PhaseBPlanningError(
            "MATRIX_COUNT_INVALID", f"changed_cells={len(changes)}", "Exactly seven owned cells must transition."
        )
    return changes

def execute_operation(plan: Mapping[str, Any], operation_id: str) -> None:
    if not plan.get("host_execution_authorized") or not plan.get("preflight_ready"):
        raise HostExecutionDisabledError(
            "HOST_EXECUTION_NOT_AUTHORIZED",
            f"operation={operation_id}, local_phase_b_only=true",
            "Persist a separate live Jev host-execution gate and healthy preflight first.",
        )
    raise HostExecutionDisabledError(
        "HOST_EXECUTOR_NOT_ENABLED_IN_PHASE_B",
        "host executor wiring is intentionally absent from local preparation",
        "A separate gate must provide the governed queue/adapter executor.",
    )

def _write_atomic(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository-root", default=".")
    parser.add_argument("--preflight", default=str(RUN_DIR / "host-preflight-phase-a/host-state.json"))
    parser.add_argument("--postflight", default=str(RUN_DIR / "host-preflight-phase-a/phase-a-postflight.json"))
    parser.add_argument("--authorization", default=str(RUN_DIR / "operator-authorization.json"))
    parser.add_argument("--gate-evidence", default=str(RUN_DIR / "jev-gates/2026-10-03/gate-3-4-evidence.json"))
    parser.add_argument("--final", action="store_true", help="emit the Gate 7 final-operation plan")
    parser.add_argument("--gate7-evidence", default=str(RUN_DIR / "jev-gates/2026-10-03/gate-7-evidence.json"))
    parser.add_argument("--output")
    parser.add_argument("--execute-operation")
    return parser

def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.repository_root).resolve()
    try:
        plan = build_plan(
            root,
            (root / args.preflight).resolve(),
            (root / args.postflight).resolve(),
            (root / args.authorization).resolve(),
            (root / (args.gate7_evidence if args.final else args.gate_evidence)).resolve(),
            final_operations=args.final,
        )
        if args.execute_operation:
            execute_operation(plan, args.execute_operation)
        if args.output:
            _write_atomic((root / args.output).resolve(), plan)
        else:
            print(json.dumps(plan, indent=2, sort_keys=True))
    except PhaseBPlanningError as exc:
        print(json.dumps({
            "status": "failed_closed", "code": exc.code,
            "observed": exc.observed, "remediation": exc.remediation,
        }, sort_keys=True))
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
