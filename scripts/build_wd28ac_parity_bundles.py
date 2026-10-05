#!/usr/bin/env python3
"""Build and checker-validate the six successful WD-28ac Gate 22 bundles.

The builder is offline and read-only with respect to host ``3090``.  It consumes
artifacts already copied into this repository, fails closed on record/hash
drift, and emits compact ``wangp-dspy.maestro-parity-evidence/v1`` records.
It never renders, downloads, admits a queue job, accepts a story, or merges.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from fractions import Fraction
from pathlib import Path
from typing import Any

from scripts.verify_maestro_parity import verify_bundle

REPO_ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_SCHEMA = "wangp-dspy.maestro-parity-evidence/v1"
REVIEW_SCHEMA = "wangp-dspy.wd-28ac.bundle-review/v1"
SUMMARY_SCHEMA = "wangp-dspy.wd-28ac.gate22-bundle-summary/v1"
RUN_COMMIT = "83ce535585e6edac59365b57941bb5d0107f461a"
RUN_REVIEWED_AT = "2026-10-04T16:20:49Z"
OPERATIONS = (
    "ltx25-outpaint",
    "ltx25-repaint",
    "ltx25-recast",
    "ltx25-upscale",
    "ltx23-outpaint",
    "ltx23-recast",
)
TERMINAL_EXCLUDED_OPERATION = "ltx23-upscale"
BASE_STORY = {
    "ltx25-outpaint": "WD-m7xw",
    "ltx25-repaint": "WD-m7xw",
    "ltx25-recast": "WD-m7xw",
    "ltx25-upscale": "WD-m7xw",
    "ltx23-outpaint": "WD-osfm",
    "ltx23-recast": "WD-osfm",
}
OPERATION_ASSET = {
    "ltx25-outpaint": "ltx-2.3-22b-ic-lora-outpaint.safetensors",
    "ltx25-repaint": "ltx-2.3-22b-ic-lora-in-outpainting-0.9.safetensors",
    "ltx25-recast": "ltx-2.3-22b-ic-lora-ingredients-0.9.safetensors",
    "ltx25-upscale": "ltx-2.5-22b-ic-lora-pixel-spatial-upscaler-x2-1.0.safetensors",
    "ltx23-outpaint": "ltx-2.3-22b-ic-lora-outpaint.safetensors",
    "ltx23-recast": "ltx-2.3-22b-ic-lora-ingredients-0.9.safetensors",
}
REFERENCES: dict[str, tuple[tuple[str, str], ...]] = {
    "ltx25-outpaint": (("inputs/wd_m7xw_create.mp4", "ltx25_generated_source_video"),),
    "ltx25-repaint": (
        ("inputs/wd_m7xw_create.mp4", "ltx25_generated_source_video"),
        ("inputs/repaint-mask.mp4", "repaint_editable_region_mask"),
    ),
    "ltx25-recast": (("inputs/first-frame.png", "recast_reference_frame"),),
    "ltx25-upscale": (("inputs/wd_m7xw_create.mp4", "spatial_upscale_source_video"),),
    "ltx23-outpaint": (("inputs/control.mp4", "person_bearing_control_video"),),
    "ltx23-recast": (("inputs/alternate-reference.png", "recast_reference_frame"),),
}
REFERENCE_LICENSE = (
    "Operator-owned generated evaluation asset; operator-authorized "
    "research/evaluation use; no redistribution"
)
GATE_THRESHOLDS = {
    "valid_media": 1.0,
    "nonempty_output": 1.0,
    "distinct_hash": 1.0,
    "width_multiplier": 2.0,
}
MODEL_FILE_SUFFIXES = (".safetensors", ".gguf")
MODEL_LOG_PATTERNS = (
    re.compile(r"Loading Model '([^']+)'"),
    re.compile(r"Loading Text Encoder '([^']+)'"),
    re.compile(r"Lora '([^']+)' was loaded"),
)


class BundleBuildError(RuntimeError):
    """Raised before an evidence record can truthfully be emitted."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise BundleBuildError(f"cannot read valid JSON {path}: {exc}") from exc


def _write_json_atomic(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", dir=str(path.parent)
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, sort_keys=True, separators=(",", ":"))
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _canonical_sha256(payload: Any) -> str:
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _observed_model_paths(native_log: Path) -> list[str]:
    """Return only model files explicitly reported as loaded by Wan2GP."""
    try:
        text = native_log.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise BundleBuildError(f"cannot read native log {native_log}: {exc}") from exc
    observed: list[str] = []
    for pattern in MODEL_LOG_PATTERNS:
        matches = pattern.findall(text)
        if not matches:
            raise BundleBuildError(
                "MODEL_PROVENANCE_NATIVE_LOAD_ABSENT: "
                f"{native_log} has no match for {pattern.pattern}"
            )
        observed.extend(matches)
    for relative in observed:
        name = Path(relative).name
        if not name.lower().endswith(MODEL_FILE_SUFFIXES):
            raise BundleBuildError(
                "MODEL_PROVENANCE_NON_MODEL_FILE: "
                f"native log reports non-model file as a model: {name}"
            )
    return [Path(relative).name for relative in observed]


def _single_output(bundle: Path) -> Path:
    outputs = sorted((bundle / "native-output").glob("*.mp4"))
    if len(outputs) != 1 or not outputs[0].is_file():
        raise BundleBuildError(
            f"{bundle / 'native-output'} must contain exactly one regular MP4"
        )
    return outputs[0]


def _validate_record(bundle: Path, operation: str) -> dict[str, Any]:
    record_path = bundle / "operation-record.json"
    record = _load_json(record_path)
    if record.get("operation_id") != operation:
        raise BundleBuildError(f"{record_path}: operation_id drift")
    if record.get("admission_state") != "admitted":
        raise BundleBuildError(f"{record_path}: operation was not admitted")
    if record.get("native", {}).get("returncode") != 0:
        raise BundleBuildError(f"{record_path}: native process did not succeed")
    if record.get("status") != "rendered_pending_qc":
        raise BundleBuildError(f"{record_path}: terminal status is not rendered")
    settings = bundle / "settings.json"
    expected_settings_hash = record.get("settings", {}).get("destination_sha256")
    if not isinstance(expected_settings_hash, str) or _sha256(settings) != expected_settings_hash:
        raise BundleBuildError(f"{settings}: staged settings hash drift")
    output = _single_output(bundle)
    evidence = record.get("evidence", {})
    if _sha256(output) != evidence.get("output_sha256"):
        raise BundleBuildError(f"{output}: output SHA-256 drift")
    if output.stat().st_size != evidence.get("output_size_bytes"):
        raise BundleBuildError(f"{output}: output byte-size drift")
    native_name = Path(record["native"]["output_path"]).name
    if output.name != native_name:
        raise BundleBuildError(
            f"{output}: native output filename drift; expected {native_name}"
        )
    return record


def _media_metadata(bundle: Path, output: Path, record: dict[str, Any]) -> dict[str, Any]:
    probe_path = bundle / "media.ffprobe.json"
    probe = _load_json(probe_path)
    streams = probe.get("streams", [])
    videos = [stream for stream in streams if stream.get("codec_type") == "video"]
    audios = [stream for stream in streams if stream.get("codec_type") == "audio"]
    if len(videos) != 1 or len(audios) != 1:
        raise BundleBuildError(f"{probe_path}: expected one video and one audio stream")
    video = videos[0]
    audio = audios[0]
    try:
        width = int(video["width"])
        height = int(video["height"])
        duration = float(probe["format"]["duration"])
        fps = float(Fraction(video["avg_frame_rate"]))
        sample_rate = int(audio["sample_rate"])
        channels = int(audio["channels"])
        codec = str(audio["codec_name"])
    except (KeyError, TypeError, ValueError, ZeroDivisionError) as exc:
        raise BundleBuildError(f"{probe_path}: invalid media metadata: {exc}") from exc
    expected = record["evidence"]
    if (width, height) != (expected["width"], expected["height"]):
        raise BundleBuildError(f"{probe_path}: dimensions drift from operation record")
    relative = output.relative_to(bundle).as_posix()
    return {
        "path": relative,
        "kind": "video",
        "width": width,
        "height": height,
        "duration_s": duration,
        "fps": fps,
        "alpha_mode": "none",
        "audio": {
            "present": True,
            "codec": codec,
            "sample_rate_hz": sample_rate,
            "channels": channels,
        },
    }


def _model_provenance(
    repo_root: Path,
    operation: str,
    record: dict[str, Any],
    native_log: Path,
) -> list[dict[str, Any]]:
    base_path = (
        repo_root
        / "datasets/runs/maestro-parity"
        / BASE_STORY[operation]
        / "evidence.json"
    )
    raw_base = _load_json(base_path).get("model_provenance")
    if not isinstance(raw_base, list) or not raw_base:
        raise BundleBuildError(f"{base_path}: base model provenance is absent")
    base_by_filename: dict[str, dict[str, Any]] = {}
    for item in raw_base:
        filename = Path(str(item.get("destination", ""))).name
        if not filename:
            continue
        existing = base_by_filename.get(filename)
        if existing is not None and existing != item:
            raise BundleBuildError(
                "MODEL_PROVENANCE_PRIOR_ASSET_AMBIGUOUS: "
                f"{BASE_STORY[operation]} records multiple entries for {filename}"
            )
        base_by_filename[filename] = item
    assets = {
        item["id"]: item
        for item in _load_json(
            repo_root
            / "datasets/runs/maestro-parity/ltx-dependency-terminalization/model-assets.json"
        )["assets"]
    }
    authorization_path = (
        repo_root
        / "datasets/runs/maestro-parity/ltx-dependency-terminalization"
        / "operator-authorization.json"
    )
    authorization = _load_json(authorization_path)
    authorized_assets = {
        str(item["id"]): item
        for item in authorization.get("assets", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    try:
        asset = assets[OPERATION_ASSET[operation]]
    except KeyError as exc:
        raise BundleBuildError(
            f"missing authorized WD-28ac asset {OPERATION_ASSET[operation]}"
        ) from exc
    runtime = record["runtime_preflight"]
    if runtime.get("payload_sha256") != (
        "d39fa7a56869387410d299ab139eb724e3be3f04055fd5d0da69d32dec9f309b"
    ):
        raise BundleBuildError("isolated runtime identity drift")

    observed = _observed_model_paths(native_log)
    if asset["id"] not in observed:
        raise BundleBuildError(
            "MODEL_PROVENANCE_OPERATION_ASSET_NOT_LOADED: "
            f"authorized asset {asset['id']} is absent from {native_log}"
        )

    provenance: list[dict[str, Any]] = []
    for filename in observed:
        authorized = authorized_assets.get(filename)
        if authorized is not None:
            manifest_asset = assets.get(filename)
            if manifest_asset is None:
                raise BundleBuildError(
                    "MODEL_PROVENANCE_MANIFEST_ABSENT: "
                    f"authorized asset {filename} is absent from model-assets.json"
                )
            if manifest_asset.get("sha256") != authorized.get("sha256"):
                raise BundleBuildError(
                    "MODEL_PROVENANCE_AUTHORIZATION_HASH_DRIFT: "
                    f"authorized asset {filename} disagrees with model-assets.json"
                )
            approval = authorization.get("operator_approval", {})
            provenance.append(
                {
                    "identity": manifest_asset["id"],
                    "source": manifest_asset["source_url"],
                    "license": manifest_asset["license"],
                    "sha256": manifest_asset["sha256"],
                    "destination": manifest_asset["destination"],
                    "download_approved": True,
                    "preflight_hash_verified": True,
                    "downloaded_this_story": True,
                    "authorization_trace": {
                        "basis": "operator_authorized_asset",
                        "path": authorization_path.relative_to(
                            repo_root
                        ).as_posix(),
                        "pointer": f"assets[id={filename}]",
                        "approved_at": approval.get("timestamp", ""),
                        "verbatim": approval.get("verbatim", ""),
                    },
                }
            )
            continue

        prior = base_by_filename.get(filename)
        if prior is None:
            raise BundleBuildError(
                "MODEL_PROVENANCE_AUTHORIZATION_ABSENT: "
                f"observed model {filename} is neither operator-authorized "
                "nor recorded as a pre-existing host asset"
            )
        if prior.get("download_approved") is not True:
            raise BundleBuildError(
                "MODEL_PROVENANCE_PREEXISTING_APPROVAL_ABSENT: "
                f"prior story {BASE_STORY[operation]} did not approve {filename}"
            )
        if prior.get("preflight_hash_verified") is not True:
            raise BundleBuildError(
                "MODEL_PROVENANCE_PREEXISTING_HASH_UNVERIFIED: "
                f"prior story {BASE_STORY[operation]} did not verify {filename}"
            )
        normalized = {
            "identity": filename,
            "source": prior["source"],
            "license": prior["license"],
            "sha256": prior["sha256"],
            "destination": prior["destination"],
            "download_approved": True,
            "preflight_hash_verified": True,
            "downloaded_this_story": False,
            "prior_story": BASE_STORY[operation],
            "authorization_trace": {
                "basis": "pre_existing_host_asset",
                "path": base_path.relative_to(repo_root).as_posix(),
                "pointer": f"model_provenance[destination ends with /{filename}]",
                "preflight_hash_verified": True,
            },
        }
        if prior.get("postflight_hash_verified") is not None:
            normalized["postflight_hash_verified"] = prior[
                "postflight_hash_verified"
            ]
        provenance.append(normalized)

    return provenance


def _reference_provenance(bundle: Path, operation: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for relative, role in REFERENCES[operation]:
        path = bundle / relative
        if not path.is_file():
            raise BundleBuildError(f"missing reference provenance file: {path}")
        rows.append(
            {
                "path": relative,
                "role": role,
                "sha256": _sha256(path),
                "license": REFERENCE_LICENSE,
            }
        )
    return rows


def _repository_state(record: dict[str, Any]) -> dict[str, Any]:
    native_before = record["native"]["before"]
    basis = {
        "wan2gp_commit": native_before["source_commit"],
        "wan2gp_status": native_before["source_status"],
        "wd28ac_runner_commit": RUN_COMMIT,
    }
    dirty = bool(native_before["source_status"].strip())
    return {
        "commit": RUN_COMMIT,
        "dirty_state": {
            "dirty": dirty,
            "identity_sha256": _canonical_sha256(basis),
            "identity_basis": "WD-28ac runner commit plus exact native source-tree status",
            "wan2gp_commit": native_before["source_commit"],
            "wan2gp_status": native_before["source_status"],
        },
    }


def _objective_gates(
    output_relative: str, record: dict[str, Any], operation: str
) -> list[dict[str, Any]]:
    measurements = record["evidence"]["objective_measurements"]
    required = ("valid_media", "nonempty_output", "distinct_hash")
    missing = [name for name in required if name not in measurements]
    if missing:
        raise BundleBuildError(f"missing objective measurements: {missing}")
    gates: list[dict[str, Any]] = []
    for name in (*required, "width_multiplier"):
        if name not in measurements:
            continue
        measured = float(measurements[name])
        threshold = GATE_THRESHOLDS[name]
        if measured < threshold:
            raise BundleBuildError(f"objective gate {name} failed: {measured}")
        inputs = [output_relative]
        if name == "width_multiplier":
            inputs.append(REFERENCES[operation][0][0])
        gates.append(
            {
                "name": f"wd_28ac_{operation}_{name}",
                "inputs": inputs,
                "threshold": threshold,
                "measured": measured,
                "verdict": "pass",
            }
        )
    return gates


def _build_one(repo_root: Path, evidence_root: Path, operation: str) -> dict[str, Any]:
    bundle = evidence_root / operation
    record = _validate_record(bundle, operation)
    output = _single_output(bundle)
    output_relative = output.relative_to(bundle).as_posix()
    output_hash = _sha256(output)
    native_log = bundle / "native.log"
    authorization = _load_json(
        repo_root
        / "datasets/runs/maestro-parity/ltx-dependency-terminalization/operator-authorization.json"
    )["corrected_retry_approval"]
    media = _media_metadata(bundle, output, record)
    payload: dict[str, Any] = {
        "schema": EVIDENCE_SCHEMA,
        "operator_authorization": {
            "status": "approved",
            "text": authorization["verbatim"],
            "scope": (
                "WD-28ac corrected native retry: the seven named governed LTX "
                "operations on host 3090 with no deletion, training, provider "
                "spend, unrelated mutation, threshold change, protected-engine "
                "change, or undeclared model/body request"
            ),
            "timestamp": authorization["timestamp"],
            "approved_by": authorization["approved_by"],
        },
        "command": record["argv"],
        "repository": _repository_state(record),
        "model_provenance": _model_provenance(
            repo_root, operation, record, native_log
        ),
        "reference_provenance": _reference_provenance(bundle, operation),
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
            output_relative, record, operation
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
            "reviewer": "WD-28ac developer bundle review",
            "review_scope": (
                "Deterministic hash, settings, native-exit, media-probe, and "
                "objective-record review for PM evidence packaging; this is not "
                "Paivot story acceptance or merge approval"
            ),
        },
        "runtime_notes": {
            "wan2gp_commit": record["native"]["before"]["source_commit"],
            "wan2gp_status": record["native"]["before"]["source_status"],
            "isolated_mmgp_version": record["runtime_preflight"]["mmgp_version"],
            "isolated_runtime_payload_sha256": record["runtime_preflight"][
                "payload_sha256"
            ],
            "system_mmgp_present": record["runtime_preflight"]["system_mmgp_present"],
        },
    }
    evidence_path = bundle / "evidence.json"
    _write_json_atomic(evidence_path, payload)
    evidence_hash = _sha256(evidence_path)
    review = {
        "schema_version": REVIEW_SCHEMA,
        "decision": "approved",
        "reviewed_at": RUN_REVIEWED_AT,
        "reviewer": "WD-28ac developer bundle review",
        "scope": (
            "Read-only deterministic packaging review only; no host action, "
            "PM acceptance, capability transition, or merge authorization"
        ),
        "checks": {
            "operation_record_sha256": _sha256(bundle / "operation-record.json"),
            "settings_sha256": _sha256(bundle / "settings.json"),
            "native_returncode": record["native"]["returncode"],
            "native_log_sha256": _sha256(native_log),
            "output_sha256": output_hash,
            "output_bytes": output.stat().st_size,
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
    return {
        "operation": operation,
        "bundle": bundle.relative_to(repo_root).as_posix(),
        "evidence_sha256": evidence_hash,
        "output_sha256": output_hash,
        "owned_warnings": len(report.warnings),
        "diagnostics": len(report.diagnostics),
    }


def build_all(repo_root: Path, evidence_root: Path | None = None) -> dict[str, Any]:
    root = evidence_root or (
        repo_root / "datasets/runs/maestro-parity/WD-28ac/gate22"
    )
    if TERMINAL_EXCLUDED_OPERATION in OPERATIONS:
        raise BundleBuildError("terminal operation must not be bundled")
    lanes = [_build_one(repo_root, root, operation) for operation in OPERATIONS]
    summary = {
        "schema_version": SUMMARY_SCHEMA,
        "story": "WD-28ac",
        "gate": "phase-b-gate22-corrected-retry",
        "repository_commit": RUN_COMMIT,
        "reviewed_at": RUN_REVIEWED_AT,
        "operation_count": len(lanes),
        "terminal_excluded_operation": TERMINAL_EXCLUDED_OPERATION,
        "lanes": lanes,
    }
    _write_json_atomic(root / "build-summary.json", summary)
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    arguments = parser.parse_args(argv)
    try:
        summary = build_all(arguments.repo_root.resolve())
    except (BundleBuildError, OSError) as exc:
        print(f"BUILD FAIL: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
