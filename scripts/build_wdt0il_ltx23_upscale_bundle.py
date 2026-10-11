#!/usr/bin/env python3
"""Build and checker-validate the final WD-t0il LTX-2.3 upscale bundle.

The builder is offline and read-only with respect to host ``3090``.  It
consumes the already-merged f654 identity-capture run, fails closed on
record/hash drift, and emits the canonical Maestro-parity evidence record.
It never renders, downloads, admits a queue job, retries, or alters media.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.build_wd28ac_parity_bundles import (
    BundleBuildError,
    _canonical_sha256,
    _load_json,
    _media_metadata,
    _observed_model_paths,
    _single_output,
    _validate_record,
    _write_json_atomic,
)
from scripts.verify_maestro_parity import verify_bundle

EVIDENCE_SCHEMA = "wangp-dspy.maestro-parity-evidence/v1"
REVIEW_SCHEMA = "wangp-dspy.wd-t0il.final-ltx-bundle-review/v1"
SUMMARY_SCHEMA = "wangp-dspy.wd-t0il.final-ltx-bundle-summary/v1"
RUN_COMMIT = "f6548f03528b058476367349a5f481614cfa35be"
OPERATION = "ltx23-upscale"
RAW_RUN = (
    "datasets/runs/maestro-parity/ltx-dependency-terminalization/"
    "identity-capture-f654-20261011"
)
RAW_OPERATION = f"{RAW_RUN}/{OPERATION}"
BUNDLE_RELATIVE = "datasets/runs/maestro-parity/WD-t0il/ltx23-upscale"
REFERENCE_SOURCE = (
    "datasets/runs/maestro-parity/WD-osfm/outputs/create/wd_osfm_create.mp4"
)
REFERENCE_ROLE = "spatial_upscale_source_video"
REFERENCE_LICENSE = (
    "Operator-owned generated evaluation asset; operator-authorized "
    "research/evaluation use; no redistribution"
)
AUTHORIZED_LOCAL_LICENSE = (
    "Operator-authorized existing local asset; hash-bound operator "
    "research/evaluation use; no redistribution"
)
EXPECTED_OUTPUT_SHA256 = (
    "126144d844e08ca70398f818daeb598761a1670c970c5849213d2d02e2e6a8b9"
)
EXPECTED_NATIVE_LOG_SHA256 = (
    "50fa2d01710ce78713e5c9746594fde8b5598b932ff539f9d1a5930b5c35623a"
)
EXPECTED_PROPOSAL_SHA256 = (
    "146b41ca4b204e73d0a51de4fc33937cc6cca3096ef50c7d5eea608ad13564c8"
)
EXPECTED_AUTHORIZATION_SHA256 = (
    "2e32b060cfa6c2f529e3aa2c0f73ff7862a8103dcf043c66790e0db161bab3b8"
)
GATE_THRESHOLDS = {
    "valid_media": 1.0,
    "nonempty_output": 1.0,
    "distinct_hash": 1.0,
    "width_multiplier": 2.0,
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _manifest_entry(manifest: dict[str, Any], relative: str) -> dict[str, Any]:
    entry = manifest.get(relative)
    if not isinstance(entry, dict):
        raise BundleBuildError(f"raw manifest lacks preserved entry: {relative}")
    return entry


def _verify_preserved(
    raw_root: Path,
    manifest: dict[str, Any],
    relative: str,
) -> dict[str, Any]:
    path = raw_root / relative
    entry = _manifest_entry(manifest, relative)
    if not path.is_file() or path.is_symlink():
        raise BundleBuildError(f"preserved raw file is absent or unsafe: {relative}")
    if path.stat().st_size != entry.get("size_bytes"):
        raise BundleBuildError(f"preserved raw file size drift: {relative}")
    if _sha256(path) != entry.get("sha256"):
        raise BundleBuildError(f"preserved raw file hash drift: {relative}")
    return entry


def _copy_preserved(
    source: Path,
    destination: Path,
    expected_hash: str,
    allowed_root: Path,
) -> None:
    allowed = allowed_root.resolve(strict=True)
    destination.parent.mkdir(parents=True, exist_ok=True)

    try:
        destination.relative_to(allowed)
    except ValueError as exc:
        raise BundleBuildError(
            f"destination escapes allowed root: {destination} -> {allowed}"
        ) from exc

    component = destination
    while component != allowed:
        if component.is_symlink():
            raise BundleBuildError(
                f"preserved-copy path traverses a symlink: {component}"
            )
        component = component.parent
        if component == component.parent:
            raise BundleBuildError(f"destination has no allowed ancestor: {destination}")

    if not source.is_file() or source.is_symlink():
        raise BundleBuildError(f"preserved source is not a regular file: {source}")

    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.",
        suffix=".copy",
        dir=str(destination.parent),
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as target, source.open("rb") as origin:
            shutil.copyfileobj(origin, target)
            target.flush()
            os.fsync(target.fileno())
        if temporary.is_symlink() or not temporary.is_file():
            raise BundleBuildError(f"exclusive preserved copy became unsafe: {temporary}")
        if _sha256(temporary) != expected_hash:
            raise BundleBuildError(f"copy changed source bytes: {source}")
        os.replace(temporary, destination)
        if destination.is_symlink() or not destination.is_file():
            raise BundleBuildError(f"preserved destination is unsafe: {destination}")
        destination_resolved = destination.resolve(strict=True)
        if not destination_resolved.is_relative_to(allowed):
            raise BundleBuildError(f"preserved destination escapes allowed root: {destination}")
        if _sha256(destination) != expected_hash:
            raise BundleBuildError(f"installed copy changed source bytes: {source}")
    finally:
        if temporary.exists():
            temporary.unlink()


def _summary_operation(summary: dict[str, Any]) -> dict[str, Any]:
    operations = summary.get("operations", [])
    rows = [
        row
        for row in operations
        if isinstance(row, dict) and row.get("operation_id") == OPERATION
    ]
    if len(rows) != 1:
        raise BundleBuildError("run summary must contain exactly one ltx23-upscale row")
    return rows[0]


def _validate_run(
    repo_root: Path,
) -> tuple[
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
]:
    raw_root = repo_root / RAW_RUN
    manifest = _load_json(raw_root / "sha256-manifest.json")
    summary = _load_json(raw_root / "run-summary.json")
    authorization = _load_json(raw_root / "operator-authorization.json")
    proposal = _load_json(raw_root / "operator-proposal.json")
    preflight = _load_json(raw_root / "preflight.json")
    stage = _load_json(raw_root / "stage-inventory.json")

    operation_relative = f"{OPERATION}/operation-record.json"
    settings_relative = f"{OPERATION}/settings.json"
    log_relative = f"{OPERATION}/native.log"
    output_relative = (
        f"{OPERATION}/native-output/wd_osfm_create_post.mp4"
    )
    _verify_preserved(raw_root, manifest, operation_relative)
    _verify_preserved(raw_root, manifest, settings_relative)
    _verify_preserved(raw_root, manifest, log_relative)
    _verify_preserved(raw_root, manifest, output_relative)

    row = _summary_operation(summary)
    expected_row = {
        "attempt": 1,
        "audio_codec": "aac",
        "duration_s": 1.375,
        "height": 1664,
        "native_exit": 0,
        "native_log_sha256": EXPECTED_NATIVE_LOG_SHA256,
        "operation_id": OPERATION,
        "operation_record_sha256": _sha256(raw_root / operation_relative),
        "output_sha256": EXPECTED_OUTPUT_SHA256,
        "output_size_bytes": 3729463,
        "settings_sha256": _sha256(raw_root / settings_relative),
        "source_commit": "4c93b64a47b5b0a915f2abec2ce754be98227150",
        "status": "rendered_pending_qc",
        "width": 896,
    }
    if any(row.get(key) != value for key, value in expected_row.items()):
        raise BundleBuildError(f"run-summary operation row drift: {row}")
    if not isinstance(row.get("output"), str) or not isinstance(row.get("source_status"), str):
        raise BundleBuildError("run-summary operation row lacks text provenance")
    if summary.get("status") != "all_native_renders_complete":
        raise BundleBuildError("identity-capture run is not complete")
    if (
        summary.get("operation_count") != 7
        or summary.get("rendered_pending_qc_count") != 7
        or summary.get("failed_count") != 0
        or summary.get("retry_attempted") is not False
        or summary.get("matrix_promotion") is not False
        or summary.get("repository_commit") != RUN_COMMIT
        or summary.get("repository_status") != ""
    ):
        raise BundleBuildError("identity-capture run-boundary drift")
    if summary.get("model_downloads") != 0 or summary.get("package_downloads") != 0:
        raise BundleBuildError("identity capture unexpectedly downloaded bytes")
    if summary.get("proposal_sha256") != EXPECTED_PROPOSAL_SHA256:
        raise BundleBuildError("identity-capture proposal binding drift")
    if summary.get("authorization_canonical_sha256") != EXPECTED_AUTHORIZATION_SHA256:
        raise BundleBuildError("identity-capture authorization binding drift")
    if _sha256(raw_root / "operator-proposal.json") != EXPECTED_PROPOSAL_SHA256:
        raise BundleBuildError("raw operator proposal hash drift")
    if _canonical_sha256(authorization) != EXPECTED_AUTHORIZATION_SHA256:
        raise BundleBuildError("raw operator authorization canonical hash drift")
    if authorization.get("status") != "approved" or authorization.get("base_commit") != RUN_COMMIT:
        raise BundleBuildError("operator authorization is not approved at f654")
    if authorization.get("retry") != "never" or authorization.get("max_attempts_per_operation") != 1:
        raise BundleBuildError("operator authorization is not the recorded one-shot boundary")
    if authorization.get("model_downloads") != 0 or authorization.get("package_downloads") != 0:
        raise BundleBuildError("operator authorization permits unexpected downloads")
    operations = [
        (item.get("row"), item.get("operation"), item.get("operation_id"))
        for item in authorization.get("operations", [])
    ]
    if ("LTX-2.3", "upscale", OPERATION) not in operations or len(operations) != 7:
        raise BundleBuildError("operator authorization does not name the final cell in the seven-operation batch")
    if proposal.get("existing_assets") != authorization.get("existing_assets"):
        raise BundleBuildError("proposal and authorization local-asset sets diverge")
    if preflight.get("assets_all_match") is not True or preflight.get("stage_inventory_valid") is not True:
        raise BundleBuildError("identity-capture preflight did not verify assets and stage")
    repository = stage.get("repository", {})
    if (
        stage.get("file_count") != 13
        or repository.get("commit_sha") != RUN_COMMIT
        or repository.get("status_porcelain_v1") != ""
        or repository.get("clean_tree") is not True
    ):
        raise BundleBuildError("identity-capture Wangp execution identity drift")
    for item in stage.get("files", []):
        relative = item.get("path")
        manifest_relative = f"repository/{relative}"
        preserved = _verify_preserved(raw_root, manifest, manifest_relative)
        if preserved.get("sha256") != item.get("sha256"):
            raise BundleBuildError(f"stage inventory hash drift: {relative}")

    return manifest, summary, authorization, preflight, stage, row


def _destination_for_observed(relative_model: str) -> str:
    return str(Path("/home/straughter/Wan2GP") / Path(relative_model))


def _model_provenance(
    repo_root: Path,
    authorization: dict[str, Any],
    native_log: Path,
) -> list[dict[str, Any]]:
    raw_root = repo_root / RAW_RUN
    observed = _observed_model_paths(native_log)
    expected = {
        "ltx-2.3-22b-dev_diffusion_model_quanto_int8.safetensors",
        "gemma-3-12b-it-qat-q4_0-unquantized_quanto_bf16_int8.safetensors",
        "ltx-2.3-22b-distilled-lora-384-1.1.safetensors",
        "ltx-2.3-22b-ic-lora-pixel-spatial-upscaler-x2-0.9.safetensors",
    }
    if set(observed) != expected:
        raise BundleBuildError(f"unexpected native model-load set: {sorted(observed)}")

    authorized = authorization.get("existing_assets", {})
    proposal_hash = authorization.get("operator_approval", {}).get("proposal_sha256", "")
    approved_at = authorization.get("operator_approval", {}).get("approved_at", "")
    verbatim = authorization.get("operator_approval", {}).get("verbatim", "")
    assets = {
        item["id"]: item
        for item in _load_json(
            repo_root
            / "datasets/runs/maestro-parity/ltx-dependency-terminalization/model-assets.json"
        )["assets"]
    }
    prior_rows = _load_json(
        repo_root / "datasets/runs/maestro-parity/WD-osfm/evidence.json"
    )["model_provenance"]
    prior_by_filename = {
        Path(str(item.get("destination", ""))).name: item for item in prior_rows
    }

    provenance: list[dict[str, Any]] = []
    observed_model_text = native_log.read_text(encoding="utf-8")
    for filename in observed:
        if filename in authorized:
            asset = assets.get(filename)
            source = (
                asset["source_url"]
                if asset is not None
                else (
                    "operator-recorded existing local LTX asset; "
                    "no upstream URL is claimed by this bundle"
                )
            )
            license_text = (
                asset["license"]
                if asset is not None
                else AUTHORIZED_LOCAL_LICENSE
            )
            provenance.append(
                {
                    "identity": filename,
                    "source": source,
                    "license": license_text,
                    "sha256": authorized[filename]["sha256"],
                    "destination": _destination_for_observed(
                        next(
                            line
                            for line in observed_model_text.splitlines()
                            if filename in line
                        ).split("'", 2)[1]
                    ),
                    "download_approved": True,
                    "preflight_hash_verified": True,
                    "downloaded_this_story": False,
                    "authorization_trace": {
                        "basis": "operator_authorized_existing_asset",
                        "path": f"{RAW_RUN}/operator-authorization.json",
                        "pointer": f"existing_assets[{filename}]",
                        "proposal_sha256": proposal_hash,
                        "approved_at": approved_at,
                        "verbatim": verbatim,
                    },
                }
            )
            continue
        prior = prior_by_filename.get(filename)
        if prior is None or prior.get("download_approved") is not True or prior.get("preflight_hash_verified") is not True:
            raise BundleBuildError(f"untraceable observed model: {filename}")
        provenance.append(
            {
                "identity": filename,
                "source": prior["source"],
                "license": prior["license"],
                "sha256": prior["sha256"],
                "destination": prior["destination"],
                "download_approved": True,
                "preflight_hash_verified": True,
                "downloaded_this_story": False,
                "prior_story": "WD-osfm",
                "authorization_trace": {
                    "basis": "pre_existing_host_asset",
                    "path": "datasets/runs/maestro-parity/WD-osfm/evidence.json",
                    "pointer": f"model_provenance[destination ends with /{filename}]",
                    "preflight_hash_verified": True,
                },
            }
        )
    return provenance


def _write_media_probe(repo_root: Path, bundle: Path, output: Path) -> dict[str, Any]:
    relative = output.relative_to(repo_root).as_posix()
    completed = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            relative,
        ],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    try:
        probe = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise BundleBuildError(f"invalid ffprobe output for {relative}: {exc}") from exc
    if probe.get("format", {}).get("filename") != relative:
        raise BundleBuildError("ffprobe did not describe the bundle output path")
    _write_json_atomic(bundle / "media.ffprobe.json", probe)
    return probe


def _objective_gates(
    output_relative: str,
    reference_relative: str,
    record: dict[str, Any],
) -> list[dict[str, Any]]:
    measurements = record["evidence"]["objective_measurements"]
    gates: list[dict[str, Any]] = []
    for name, threshold in GATE_THRESHOLDS.items():
        if name not in measurements:
            raise BundleBuildError(f"missing objective measurement: {name}")
        measured = float(measurements[name])
        if measured < threshold:
            raise BundleBuildError(f"objective gate {name} failed: {measured}")
        gates.append(
            {
                "name": f"wd_t0il_{OPERATION}_{name}",
                "inputs": [output_relative]
                + ([reference_relative] if name == "width_multiplier" else []),
                "threshold": threshold,
                "measured": measured,
                "verdict": "pass",
            }
        )
    return gates


def _repository_state(
    record: dict[str, Any], stage: dict[str, Any]
) -> dict[str, Any]:
    repository = stage["repository"]
    basis = {
        "wangp_commit": repository["commit_sha"],
        "wangp_status_porcelain_v1": repository["status_porcelain_v1"],
        "stage_file_count": stage["file_count"],
        "wan2gp_commit": record["native"]["before"]["source_commit"],
        "wan2gp_status": record["native"]["before"]["source_status"],
    }
    return {
        "commit": RUN_COMMIT,
        "dirty_state": {
            "dirty": False,
            "identity_sha256": _canonical_sha256(basis),
            "identity_basis": (
                "clean Wangp f654 execution inventory plus the exact native "
                "Wan2GP source identity"
            ),
            "wangp_commit": repository["commit_sha"],
            "wangp_status_porcelain_v1": repository["status_porcelain_v1"],
            "stage_file_count": stage["file_count"],
            "wan2gp_commit": record["native"]["before"]["source_commit"],
            "wan2gp_status": record["native"]["before"]["source_status"],
        },
    }


def build_bundle(repo_root: Path) -> dict[str, Any]:
    root = repo_root.resolve()
    raw_root = root / RAW_RUN
    raw_operation = root / RAW_OPERATION
    bundle = root / BUNDLE_RELATIVE
    (
        manifest,
        summary,
        authorization,
        preflight,
        stage,
        summary_row,
    ) = _validate_run(root)

    record = _validate_record(raw_operation, OPERATION)
    if record.get("attempt") != 1 or record.get("queue_state", {}).get("failure_count") != 0:
        raise BundleBuildError("final-cell record is not the recorded single attempt")
    raw_output = _single_output(raw_operation)
    output_hash = _sha256(raw_output)
    if output_hash != EXPECTED_OUTPUT_SHA256:
        raise BundleBuildError("final-cell output hash drift")

    _copy_preserved(
        raw_operation / "operation-record.json",
        bundle / "operation-record.json",
        _sha256(raw_operation / "operation-record.json"),
        bundle,
    )
    _copy_preserved(
        raw_operation / "settings.json",
        bundle / "settings.json",
        _sha256(raw_operation / "settings.json"),
        bundle,
    )
    _copy_preserved(
        raw_operation / "native.log",
        bundle / "native.log",
        EXPECTED_NATIVE_LOG_SHA256,
        bundle,
    )
    _copy_preserved(
        raw_output,
        bundle / "native-output" / raw_output.name,
        output_hash,
        bundle,
    )
    reference_source = root / REFERENCE_SOURCE
    if not reference_source.is_file():
        raise BundleBuildError(f"missing WD-osfm reference source: {reference_source}")
    reference_hash = _sha256(reference_source)
    _copy_preserved(
        reference_source,
        bundle / "inputs" / reference_source.name,
        reference_hash,
        bundle,
    )

    output = _single_output(bundle)
    output_relative = output.relative_to(bundle).as_posix()
    reference_relative = f"inputs/{reference_source.name}"
    _write_media_probe(root, bundle, output)
    media = _media_metadata(bundle, output, record)
    native_log = bundle / "native.log"
    approval = authorization["operator_approval"]

    payload: dict[str, Any] = {
        "schema": EVIDENCE_SCHEMA,
        "operator_authorization": {
            "status": "approved",
            "text": approval["verbatim"],
            "scope": (
                "WD-t0il final LTX-2.3 upscale packaging from the authorized "
                "seven-operation, one-attempt identity-capture batch at Wangp "
                "f654, using existing local assets only with zero downloads, "
                "installs, spend, training, deletion, threshold, or protected-"
                "engine changes"
            ),
            "timestamp": approval["approved_at"],
            "approved_by": authorization["approved_by"],
        },
        "command": record["argv"],
        "repository": _repository_state(record, stage),
        "model_provenance": _model_provenance(root, authorization, native_log),
        "reference_provenance": [
            {
                "path": reference_relative,
                "role": REFERENCE_ROLE,
                "sha256": reference_hash,
                "license": REFERENCE_LICENSE,
            }
        ],
        "queue_attempt": {
            "queue_id": record["queue_id"],
            "job_id": record["durable_job_id"],
            "retry_id": record["planned_job_id"],
            "admission_state": record["admission_state"],
            "exit_status": "succeeded",
            "native_logs": ["native.log"],
            "native_log_sha256": {"native.log": _sha256(native_log)},
        },
        "output": [{"path": output_relative, "sha256": output_hash}],
        "media_metadata": [media],
        "objective_gate_results": _objective_gates(
            output_relative, reference_relative, record
        ),
        "reviewer_verdict": {
            "decision": "approved",
            "evidence_links": [
                "reviewer-verdict.json",
                "operation-record.json",
                "settings.json",
                "media.ffprobe.json",
                "native.log",
            ],
            "reviewer": "WD-t0il deterministic final-cell bundle review",
            "review_scope": (
                "Read-only hash, authorization, settings, native-exit, media-"
                "probe, model-load, and objective-record review; this is not "
                "Paivot story acceptance or merge approval"
            ),
        },
        "runtime_notes": {
            "identity_capture_run": RAW_RUN,
            "identity_capture_run_sha256": _sha256(raw_root / "run-summary.json"),
            "operation_count": 7,
            "operation_attempt": 1,
            "retry_attempted": False,
            "matrix_promotion_in_host_batch": False,
            "model_downloads": 0,
            "package_downloads": 0,
            "dependency_installs": 0,
            "launcher_boundary": summary["launcher_setup_note"],
            "wan2gp_commit": record["native"]["before"]["source_commit"],
            "wan2gp_status": record["native"]["before"]["source_status"],
            "isolated_mmgp_version": record["runtime_preflight"]["mmgp_version"],
            "isolated_runtime_payload_sha256": record["runtime_preflight"][
                "payload_sha256"
            ],
            "system_mmgp_present": record["runtime_preflight"]["system_mmgp_present"],
            "stage_inventory_sha256": _sha256(raw_root / "stage-inventory.json"),
        },
    }
    _write_json_atomic(bundle / "evidence.json", payload)
    evidence_hash = _sha256(bundle / "evidence.json")
    review = {
        "schema_version": REVIEW_SCHEMA,
        "decision": "approved",
        "reviewer": "WD-t0il deterministic final-cell bundle review",
        "scope": (
            "Read-only deterministic packaging review only; no host action, "
            "retry, PM acceptance, capability transition, or merge authorization"
        ),
        "checks": {
            "authorization_canonical_sha256": EXPECTED_AUTHORIZATION_SHA256,
            "operation_record_sha256": _sha256(bundle / "operation-record.json"),
            "settings_sha256": _sha256(bundle / "settings.json"),
            "native_returncode": record["native"]["returncode"],
            "native_log_sha256": _sha256(native_log),
            "output_sha256": output_hash,
            "output_bytes": output.stat().st_size,
            "reference_sha256": reference_hash,
            "media_dimensions": [media["width"], media["height"]],
            "objective_measurements": record["evidence"][
                "objective_measurements"
            ],
        },
        "evidence_sha256": evidence_hash,
        "boundary": (
            "Approved for canonical evidence-bundle verification and independent "
            "PM review; not a Paivot acceptance or capability-matrix transition"
        ),
    }
    _write_json_atomic(bundle / "reviewer-verdict.json", review)
    report = verify_bundle(bundle)
    if not report.passed:
        diagnostics = "\n".join(
            f"FAIL {item.field}: {item.message}" for item in report.diagnostics
        )
        raise BundleBuildError(f"canonical checker rejected {bundle}:\n{diagnostics}")

    result = {
        "schema_version": SUMMARY_SCHEMA,
        "story": "WD-t0il",
        "operation": OPERATION,
        "bundle": BUNDLE_RELATIVE,
        "repository_commit": RUN_COMMIT,
        "evidence_sha256": evidence_hash,
        "output_sha256": output_hash,
        "native_log_sha256": _sha256(native_log),
        "reference_sha256": reference_hash,
        "owned_warnings": len(report.warnings),
        "diagnostics": len(report.diagnostics),
    }
    _write_json_atomic(bundle.parent / "build-summary.json", result)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    arguments = parser.parse_args(argv)
    try:
        summary = build_bundle(arguments.repo_root.resolve())
    except (BundleBuildError, OSError, subprocess.CalledProcessError) as exc:
        print(f"BUILD FAIL: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
