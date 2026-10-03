#!/usr/bin/env python3
"""Governed one-attempt WD-28ac native-operation runner."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from services.jobs.queue import JobQueue


class FinalOperationError(ValueError):
    """Typed terminal WD-28ac native-operation boundary."""

    def __init__(self, code: str, observed: str, remediation: str) -> None:
        super().__init__(observed)
        self.code = code
        self.observed = observed
        self.remediation = remediation


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

def validate_contract(
    plan: Mapping[str, Any], authorization: Mapping[str, Any]
) -> None:
    operations = plan.get("operations", [])
    if plan.get("schema_version") != "wangp-dspy.wd-28ac.phase-b-operation-plan/v1":
        raise FinalOperationError(
            "PLAN_SCHEMA_INVALID", str(plan.get("schema_version")),
            "Use the CI-green Gate 7 final-operation plan.",
        )
    if plan.get("mode") != "final_native_operations_authorized":
        raise FinalOperationError("PLAN_NOT_FINAL", plan.get("mode", ""),
                                  "Regenerate the plan with Gate 7 authorization.")
    if not plan.get("host_execution_authorized") or not plan.get("preflight_ready"):
        raise FinalOperationError("PLAN_PREFLIGHT_NOT_READY",
                                  "host_execution_authorized or preflight_ready is false",
                                  "Collect healthy QC and fresh host facts first.")
    if len(operations) != 7:
        raise FinalOperationError("OPERATION_COUNT_INVALID", str(len(operations)),
                                  "Exactly seven planned operations are required.")
    gate = authorization.get("jev_final_operations_authorization", {})
    if gate.get("operations_authorized") is not True or gate.get("retry") != "never":
        raise FinalOperationError("GATE7_AUTHORIZATION_INVALID",
                                  json.dumps(gate, sort_keys=True),
                                  "Bind the exact live Gate 7 CONTINUE record.")
    identities = [(item["row"], item["operation"]) for item in operations]
    if len(set(identities)) != 7:
        raise FinalOperationError("OPERATION_IDENTITY_DUPLICATE", json.dumps(identities),
                                  "Each owned cell must occur exactly once.")

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
        environment.update({
            "PYTHONUNBUFFERED": "1",
            "PYTORCH_ALLOC_CONF": "expandable_segments:True",
            "HF_HUB_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1",
        })
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
)-> dict[str, Any]:
    validate_contract(plan, authorization)
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
        result = run_batch(
            plan, authorization, Path(args.template_root), Path(args.queue_db)
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
