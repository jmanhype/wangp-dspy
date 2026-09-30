#!/usr/bin/env python3
"""Build the local-only WD-1s5s storage-remediation authorization packet."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

INPUT_SCHEMA, PLAN_SCHEMA = "wangp-dspy.storage-remediation-input/v1", "wangp-dspy.storage-remediation-plan/v1"
INVALID_CODE, WRITE_CODE = "STORAGE_REMEDIATION_INPUT_INVALID", "STORAGE_REMEDIATION_OUTPUT_WRITE_FAILED"
OFFLOAD_ROOT = "/mnt/bulk-hdd/straughter/model-offload/wangp-3090/"
H3_TOTAL, LTX_TOTAL, CANDIDATE_TOTAL = 53_594_702_510, 23_701_298_279, 44_288_216_793
DESTINATION_FREE, BULK_HDD_FREE = 17_865_703_424, 317_216_575_488
PROJECTED_FREE, DOCTOR_FLOOR = 62_153_920_217, 53_687_091_200
HASH_RE = re.compile(r"^[0-9a-f]{64}$")
REPO = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = REPO / "datasets/runs/maestro-parity/storage-remediation-prep/inputs.json"
DEFAULT_OUTPUT_DIR = REPO / "datasets/runs/maestro-parity/storage-remediation-prep"

_SOURCE_ROWS = (
    ("WD-bw0h", "story/WD-bw0h", "2dfe36863e29eef02af0ea330d13d331bafdc00e", "datasets/runs/maestro-parity/clean-generated/model-assets.json", "25078447afda2306e86a424a7c554fba5ae40f3838fcfcdddced6e9391b90fa0"),
    ("WD-bw0h", "story/WD-bw0h", "2dfe36863e29eef02af0ea330d13d331bafdc00e", "datasets/runs/maestro-parity/clean-generated/failed-retry/failure.json", "7d8320174c0d621cd32b4013acaddb81e92fc72a9d2af3eeabed76f5d987a6d5"),
    ("WD-bw0h", "story/WD-bw0h", "2dfe36863e29eef02af0ea330d13d331bafdc00e", "datasets/runs/maestro-parity/clean-generated/failed-retry/boundary.md", "b78f5936a227782e4c3b7866e041cd9bbcc3d60d7ed4b9ebe5418e14e3d78d5f"),
    ("WD-28ac", "story/WD-28ac", "fced67e1293dc2dbbdf3f29c8b615f6357012ab6", "datasets/runs/maestro-parity/ltx-dependency-terminalization/model-assets.json", "89f3b52bab6ff7f0ac028d5225798dd612ecdcdd10a1087f6e299474fb1b34a4"),
    ("WD-28ac", "story/WD-28ac", "fced67e1293dc2dbbdf3f29c8b615f6357012ab6", "datasets/runs/maestro-parity/ltx-dependency-terminalization/preflight-boundary.json", "6c881c9df3cd2a5d4ce85ee8fe5327e6631ac77cf2a2ca88c3b4579be4f05d53"),
    ("WD-28ac", "story/WD-28ac", "fced67e1293dc2dbbdf3f29c8b615f6357012ab6", "datasets/runs/maestro-parity/ltx-dependency-terminalization/host-storage-diagnosis/remote/filesystems.txt", "fe48f4f09634a511ae43a20211ca78bef83d415b38817303926aeac623817e9e"),
)
_SOURCE_KEYS = ("story", "branch", "head", "path", "sha256")
EXPECTED_SOURCES = tuple(dict(zip(_SOURCE_KEYS, row)) for row in _SOURCE_ROWS)

class StorageRemediationInputError(ValueError):
    """A typed, fail-closed error raised before packet output mutation."""

    def __init__(self, field: str, detail: str) -> None:
        super().__init__(f"{field}: {detail}")
        self.field = field
        self.detail = detail

    def diagnostic(self) -> dict[str, str]:
        return {"code": INVALID_CODE, "field": self.field, "detail": self.detail,
                "remediation": "Correct the committed typed snapshot; do not bypass validation."}

def _fail(field: str, detail: str) -> None:
    raise StorageRemediationInputError(field, detail)

def _exact_keys(value: Any, expected: set[str], field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        _fail(field, "expected an object")
    missing = sorted(expected - set(value))
    unknown = sorted(set(value) - expected)
    if missing or unknown:
        _fail(field, f"missing={missing}; unknown={unknown}")
    return value

def _string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        _fail(field, "expected a nonempty string")
    return value

def _integer(value: Any, field: str) -> int:
    if type(value) is not int:
        _fail(field, "expected an integer")
    return value

def _shape(value: Any, expected: Any) -> bool:
    if isinstance(expected, (bool, int, float)) or isinstance(value, (bool, int, float)):
        return type(value) is type(expected) and value == expected
    if isinstance(expected, dict):
        return isinstance(value, dict) and set(value) == set(expected) and all(
            _shape(value[key], item) for key, item in expected.items()
        )
    if isinstance(expected, list):
        return isinstance(value, list) and len(value) == len(expected) and all(
            _shape(item, example) for item, example in zip(value, expected)
        )
    return isinstance(value, type(expected)) and value == expected

def _expect(value: Any, expected: Any, field: str) -> Any:
    if not _shape(value, expected):
        _fail(field, f"expected {expected!r}")
    return value

def _load_input(input_path: Path) -> dict[str, Any]:
    try:
        value = json.loads(input_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        _fail("input", f"cannot read typed JSON: {exc}")
    if not isinstance(value, dict):
        _fail("input", "top-level value must be an object")
    return value


def _reject_local_checkout_paths(value: Any) -> None:
    if isinstance(value, str):
        if value.startswith("/Users/") or value.startswith("/private/tmp/"):
            _fail("input", "local checkout path is forbidden in portable packet data")
    elif isinstance(value, Mapping):
        for item in value.values():
            _reject_local_checkout_paths(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _reject_local_checkout_paths(item)


def _validate_sources(value: Any) -> list[dict[str, str]]:
    if not isinstance(value, list) or len(value) != len(EXPECTED_SOURCES):
        _fail("source_evidence", f"expected exactly {len(EXPECTED_SOURCES)} entries")
    for index, item in enumerate(value):
        _exact_keys(item, {"story", "branch", "head", "path", "sha256"}, f"source_evidence[{index}]")
        if item != EXPECTED_SOURCES[index]:
            _fail(f"source_evidence[{index}]", "does not match the immutable source")
        if not HASH_RE.fullmatch(item["sha256"]):
            _fail(f"source_evidence[{index}].sha256", "must be lowercase hexadecimal")
    return [dict(item) for item in value]


def _validate_manifest(value: Any, field: str, count: int, total: int) -> dict[str, Any]:
    manifest = _exact_keys(value, {"schema_version", "assets"}, field)
    if manifest["schema_version"] != "wangp-dspy.model-assets/v1":
        _fail(f"{field}.schema_version", "unexpected model manifest schema")
    assets = manifest["assets"]
    if not isinstance(assets, list) or len(assets) != count:
        _fail(f"{field}.assets", f"expected exactly {count} assets")
    ids: set[str] = set()
    destinations: set[str] = set()
    normalized: list[dict[str, Any]] = []
    asset_keys = {"id", "destination", "size_bytes", "sha256", "license"}
    for index, asset in enumerate(assets):
        asset_field = f"{field}.assets[{index}]"
        item = _exact_keys(asset, asset_keys, asset_field)
        asset_id = _string(item["id"], f"{asset_field}.id")
        destination = _string(item["destination"], f"{asset_field}.destination")
        size = _integer(item["size_bytes"], f"{asset_field}.size_bytes")
        digest = _string(item["sha256"], f"{asset_field}.sha256")
        _string(item["license"], f"{asset_field}.license")
        if size <= 0:
            _fail(f"{asset_field}.size_bytes", "must be positive")
        if not HASH_RE.fullmatch(digest):
            _fail(f"{asset_field}.sha256", "must be 64 lowercase hexadecimal characters")
        if asset_id in ids:
            _fail(f"{asset_field}.id", "duplicate asset id")
        if destination in destinations:
            _fail(f"{asset_field}.destination", "duplicate destination")
        ids.add(asset_id)
        destinations.add(destination)
        normalized.append(dict(item))
    if sum(item["size_bytes"] for item in normalized) != total:
        _fail(f"{field}.assets", f"manifest total must be exactly {total}")
    return {"schema_version": manifest["schema_version"], "assets": normalized}


def _validate_input(value: dict[str, Any]) -> dict[str, Any]:
    _reject_local_checkout_paths(value)
    root_keys = {"schema_version", "snapshot_only", "source_evidence", "model_manifests",
                 "boundaries", "superseded_h3_candidates", "recorded_disk", "offload_root", "doctor_minimum_free"}
    root = _exact_keys(value, root_keys, "input")
    _expect(root["schema_version"], INPUT_SCHEMA, "schema_version")
    _expect(root["snapshot_only"], True, "snapshot_only")
    _validate_sources(root["source_evidence"])
    raw_manifests = _exact_keys(root["model_manifests"], {"WD-bw0h", "WD-28ac"}, "model_manifests")
    manifests = {
        "WD-bw0h": _validate_manifest(raw_manifests["WD-bw0h"], "model_manifests.WD-bw0h", 4, H3_TOTAL),
        "WD-28ac": _validate_manifest(raw_manifests["WD-28ac"], "model_manifests.WD-28ac", 5, LTX_TOTAL),
    }
    boundaries = _exact_keys(root["boundaries"], {"wd_bw0h_failure", "wd_28ac_preflight",
                                                  "wd_28ac_filesystems"}, "boundaries")
    failure = _expect(boundaries.get("wd_bw0h_failure"), {
        "schema_version": "wangp-dspy.clean-generated-proof-failure/v1",
        "diagnostic": {"code": "STORAGE_PREPARATION_FAILED", "detail": "cannot create offload root"},
        "generated_artifact": False, "substitution_attempted": False,
    }, "boundaries.wd_bw0h_failure")
    preflight = _expect(boundaries.get("wd_28ac_preflight"), {
        "schema": "wangp-dspy.maestro-parity-preflight-boundary/v1",
        "queue_admission": "blocked_before_admission", "model_download_bytes_actual": 0,
        "destination_free_bytes": DESTINATION_FREE, "not_a_hardware_verdict": True,
    }, "boundaries.wd_28ac_preflight")
    _expect(boundaries.get("wd_28ac_filesystems"), {
        "destination_free_bytes": DESTINATION_FREE, "bulk_hdd_free_bytes": BULK_HDD_FREE,
    }, "boundaries.wd_28ac_filesystems")
    disk = _expect(root["recorded_disk"], {
        "destination_free_bytes": DESTINATION_FREE, "bulk_hdd_free_bytes": BULK_HDD_FREE,
        "snapshot_only": True, "stale": True, "live_verified": False,
    }, "recorded_disk")
    _expect(root["offload_root"], OFFLOAD_ROOT, "offload_root")
    _expect(root["doctor_minimum_free"], {
        "source_constant": "wangp/doctor.py:REMOTE_MINIMUM_FREE_GB",
        "minimum_gb": 50.0, "minimum_bytes": DOCTOR_FLOOR,
    }, "doctor_minimum_free")
    candidate = {"sha256": None, "sha256_status": "unknown_requires_live_verification"}
    candidates = _expect(root["superseded_h3_candidates"], [
        {"id": "superseded-h3-checkpoint-1", "size_bytes": 22_144_108_396, **candidate},
        {"id": "superseded-h3-checkpoint-2", "size_bytes": 22_144_108_397, **candidate},
    ], "superseded_h3_candidates")
    if DESTINATION_FREE + CANDIDATE_TOTAL != PROJECTED_FREE:
        _fail("recorded_disk", "projected free-space arithmetic is inconsistent")

    return {
        "source_evidence": root["source_evidence"],
        "model_manifests": manifests,
        "boundaries": {"wd_bw0h_failure": failure, "wd_28ac_preflight": preflight},
        "candidates": candidates,
        "disk": disk,
    }


def _make_packet(validated: Mapping[str, Any]) -> dict[str, Any]:
    h3 = validated["model_manifests"]["WD-bw0h"]
    ltx = validated["model_manifests"]["WD-28ac"]
    candidates = validated["candidates"]
    disk = validated["disk"]
    return {
        "schema_version": PLAN_SCHEMA,
        "story": "WD-1s5s",
        "snapshot_only": True,
        "source_evidence": validated["source_evidence"],
        "wd_bw0h": {
            "reusable_assets": h3["assets"],
            "asset_count": 4,
            "total_size_bytes": H3_TOTAL,
            "prior_failure": validated["boundaries"]["wd_bw0h_failure"],
            "future_action": {"id": "reversible_h3_offload_then_possible_retry",
                              "authorization_required": True,
                              "requires_live_candidate_size_and_hash_verification": True,
                              "deletion_permitted": False},
        },
        "superseded_h3_candidates": candidates,
        "wd_28ac": {
            "required_assets": ltx["assets"],
            "asset_count": 5,
            "total_size_bytes": LTX_TOTAL,
            "prior_boundary": validated["boundaries"]["wd_28ac_preflight"],
            "future_action": {"id": "exact_five_asset_ltx_batch",
                              "authorization_required": True,
                              "requires_live_size_hash_and_disk_verification": True,
                              "substitution_permitted": False},
        },
        "recorded_disk_facts": {**disk, "offload_root": OFFLOAD_ROOT,
                                "bulk_hdd_free_bytes": BULK_HDD_FREE},
        "projected_destination_free_bytes": {"snapshot_only": True, "stale": True,
            "live_prediction": False, "recorded_free_bytes": DESTINATION_FREE,
            "candidate_recovery_bytes": CANDIDATE_TOTAL, "projected_free_bytes": PROJECTED_FREE,
            "conditional_on": "recorded_snapshot_still_matches_live_host"},
        "snapshot_readiness": {"snapshot_only": True, "stale": True, "live_prediction": False,
            "meets_doctor_minimum": PROJECTED_FREE >= DOCTOR_FLOOR, "doctor_minimum_bytes": DOCTOR_FLOOR,
            "fits_exact_ltx_manifest": PROJECTED_FREE >= LTX_TOTAL, "ltx_manifest_bytes": LTX_TOTAL,
            "interpretation": "recorded arithmetic only; live host verification is still required"},
        "authorization_boundary": {"local_preparation_only": True,
            "future_actions_require_separate_operator_approval": True,
            "wd_bw0h_and_wd_28ac_approvals_are_distinct": True,
            "fresh_live_size_hash_and_disk_verification_required": True,
            "deletion_permitted": False},
        "execution_boundary": {"host_contact_performed": False, "network_access_performed": False,
            "model_bytes_read_or_moved": 0, "queue_jobs_admitted": 0, "commands_emitted": []},
    }


def _validate_packet_for_render(packet: Mapping[str, Any]) -> None:
    if packet.get("schema_version") != PLAN_SCHEMA:
        _fail("packet.schema_version", f"expected {PLAN_SCHEMA}")
    actions = packet.get("authorization_boundary", {})
    required = ("future_actions_require_separate_operator_approval",
                "wd_bw0h_and_wd_28ac_approvals_are_distinct")
    if not all(actions.get(key) for key in required):
        _fail("packet.authorization_boundary", "future approvals must be required and distinct")


def _atomic_write_bytes(path: Path, payload: bytes) -> None:
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_bytes(payload)
    temporary.replace(path)


def build_packet(input_path: Path, output_dir: Path) -> dict[str, Any]:
    """Validate the committed snapshot and atomically emit ``local-plan.json``."""
    value = _validate_input(_load_input(Path(input_path)))
    packet = _make_packet(value)
    output_dir.mkdir(parents=True, exist_ok=True)
    serialized = (json.dumps(packet, separators=(",", ":"), sort_keys=True) + "\n").encode("utf-8")
    _atomic_write_bytes(Path(output_dir) / "local-plan.json", serialized)
    return packet


def write_operator_request(packet: dict[str, Any], output_path: Path) -> None:
    """Render the non-executable authorization request from a validated packet."""
    _validate_packet_for_render(packet)
    candidates = packet["superseded_h3_candidates"]
    text = f"""# Operator authorization request: local storage remediation packet

This WD-1s5s packet is preparation only. It records stale snapshots, performs no host contact, and grants no authority. Two future actions require separate, explicit operator approvals.

## Decision A: reversible H3 offload, then a possible WD-bw0h retry

- Reversibly offload exactly the two superseded H3 checkpoints listed below; no other model asset is in this scope.
- Candidate SHA-256 values are unknown. Measure and record each identity and size before any relocation, then preserve a reversible recovery path.
- Fresh live verification must confirm candidate identity, size, destination free space, and bulk-HDD free space. Deletion is forbidden.
- A possible WD-bw0h retry requires its own approval after the storage precondition is verified; this section does not authorize that retry.

| Candidate | Recorded bytes | SHA-256 |
| --- | ---: | --- |
| {candidates[0]['id']} | {candidates[0]['size_bytes']} | unknown; live verification required |
| {candidates[1]['id']} | {candidates[1]['size_bytes']} | unknown; live verification required |

## Decision B: exact WD-28ac LTX batch

- Approve or reject the separate batch of exactly five LTX assets totaling {LTX_TOTAL} bytes.
- Before any transfer, verify every asset identity and hash, every destination, and current destination disk headroom. Substitution is forbidden.

## Recorded arithmetic, not live state

The stale destination snapshot records {DESTINATION_FREE} bytes free. Reversible offload of both candidates would recover {CANDIDATE_TOTAL} bytes and project {PROJECTED_FREE} bytes free only if that snapshot still matches. That number is above the {DOCTOR_FLOOR}-byte doctor floor and above the exact LTX manifest, but it is not a live observation or outcome prediction.

No host command is included. This request authorizes neither action and forbids deletion, model substitution, queue admission, and any unapproved host contact.
"""
    _atomic_write_bytes(Path(output_path), text.encode("utf-8"))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    arguments = parser.parse_args(argv)
    try:
        packet = build_packet(arguments.input, arguments.output_dir)
        write_operator_request(packet, arguments.output_dir / "operator-authorization-request.md")
    except StorageRemediationInputError as exc:
        print(json.dumps({"diagnostic": exc.diagnostic()}, sort_keys=True), file=sys.stderr)
        return 2
    except OSError as exc:
        diagnostic = {"code": WRITE_CODE, "detail": str(exc)}
        print(json.dumps({"diagnostic": diagnostic}, sort_keys=True), file=sys.stderr)
        return 3
    print("STORAGE_REMEDIATION_PACKET_READY outputs=2 authorization_required=true commands_emitted=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
