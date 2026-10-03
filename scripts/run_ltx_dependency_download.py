#!/usr/bin/env python3
"""Fail-closed one-request-per-asset downloader control for WD-28ac."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from predict.model_assets import load_asset_manifest


RUN_DIR = Path(
    "datasets/runs/maestro-parity/ltx-dependency-terminalization"
)
WRITE_OUT = (
    "%{http_code}\t%{url_effective}\t%{size_download}\t"
    "%{num_redirects}\t%{num_connects}\n"
)
CORRECTED_RETRY_VERBATIM = "Yes"
CORRECTED_RETRY_TIMESTAMP = "2026-10-03T13:11:01Z"
PRESERVED_FIRST_ASSET = "ltx-2.3-22b-ic-lora-ingredients-0.9.safetensors"
REMAINING_ASSETS = frozenset({
    "ltx-2.3-22b-ic-lora-outpaint.safetensors",
    "ltx-2.3-22b-ic-lora-in-outpainting-0.9.safetensors",
    "ltx-2.5-22b-ic-lora-pixel-spatial-upscaler-x2-1.0.safetensors",
    "ltx-2.3-22b-dev_diffusion_model_quanto_int8.safetensors",
})
PHASE_A_ASSETS = frozenset({
    "ltx-2.3-22b-ic-lora-in-outpainting-0.9.safetensors",
    "ltx-2.5-22b-ic-lora-pixel-spatial-upscaler-x2-1.0.safetensors",
    "ltx-2.3-22b-dev_diffusion_model_quanto_int8.safetensors",
})
GATE2_SNAPSHOT_SHA256 = (
    "1e7d3349996543e8cf1ae9d3f66711be26ab73fa1d8b49d866fafb2ec13cbdf2"
)
GATE2_TRACE_SHA256 = (
    "2f15b2d5bc2746d9354810b3ad5302635cad66ba97ae4c1af472b4336dc835dd"
)
AUTHORIZED_OPERATION_CELLS = frozenset({
    ("LTX-2.5", "outpaint"),
    ("LTX-2.5", "repaint"),
    ("LTX-2.5", "recast"),
    ("LTX-2.5", "upscale"),
    ("LTX-2.3", "outpaint"),
    ("LTX-2.3", "recast"),
    ("LTX-2.3", "upscale"),
})


class LTXDownloadControlError(ValueError):
    """Typed WD-28ac download-control boundary."""

    def __init__(self, code: str, observed: str, remediation: str) -> None:
        super().__init__(observed)
        self.code = code
        self.observed = observed
        self.remediation = remediation


@dataclass(frozen=True)
class CurlOutcome:
    returncode: int
    stdout: str
    stderr: str


class DownloadController:
    """Bound each asset to exactly one declared curl invocation."""

    def __init__(
        self,
        manifest: Any,
        authorization: Mapping[str, Any],
        *,
        retry_authorized: bool,
    ) -> None:
        self.manifest = manifest
        self.authorization = authorization
        self.retry_authorized = retry_authorized
        phase_a = authorization.get("jev_phase_a_authorization", {})
        self.allowed_download_ids = set(phase_a.get("assets", []))
        self._curl_invocations: dict[str, int] = {}

    def _asset(self, asset_id: str):
        for asset in self.manifest.assets:
            if asset.id == asset_id:
                return asset
        raise LTXDownloadControlError(
            "ASSET_NOT_DECLARED",
            f"asset {asset_id!r} is absent from the exact five-asset manifest",
            "Select one of the five declared WD-28ac asset ids.",
        )

    def curl_argv(self, asset_id: str, partial: str | Path) -> list[str]:
        asset = self._asset(asset_id)
        if asset.id not in self.allowed_download_ids:
            raise LTXDownloadControlError(
                "ASSET_OUTSIDE_CORRECTED_RETRY_SCOPE",
                f"asset {asset.id!r} is not one of the four remaining downloads",
                "The preserved first partial must be verified and promoted without a network request.",
            )
        return [
            "curl",
            "--fail",
            "--location",
            "--retry",
            "0",
            "--connect-timeout",
            "30",
            "--max-time",
            "14400",
            "--output",
            str(partial),
            "--write-out",
            WRITE_OUT,
            asset.source_url,
        ]

    def plan(self, asset_id: str) -> dict[str, Any]:
        asset = self._asset(asset_id)
        partial = Path(f"{asset.destination}.WD-28ac.partial")
        return {
            "schema_version": "wangp-dspy.wd-28ac.download-plan/v1",
            "asset_id": asset.id,
            "mode": "dry_run",
            "retry_authorized": self.retry_authorized,
            "source_url": asset.source_url,
            "destination": asset.destination,
            "partial": partial.as_posix(),
            "curl_argv": self.curl_argv(asset.id, partial),
            "request_accounting": {
                "curl_invocations": 0,
                "declared_request_count": 0,
                "undeclared_request_count": 0,
                "url_effective_probe_request_count": 0,
                "redirect_count": None,
                "network_request_count": 0,
            },
            "url_effective_source": None,
        }

    def execute(
        self,
        asset_id: str,
        *,
        runner: Callable[[Sequence[str]], CurlOutcome] | None = None,
    ) -> dict[str, Any]:
        if not self.retry_authorized:
            raise LTXDownloadControlError(
                "RETRY_NOT_AUTHORIZED",
                "WD-28ac metadata correction explicitly does not authorize retry",
                "Record a distinct operator retry decision before any network execution.",
            )
        asset = self._asset(asset_id)
        if self._curl_invocations.get(asset.id, 0) >= 1:
            raise LTXDownloadControlError(
                "DECLARED_REQUEST_BUDGET_EXHAUSTED",
                f"asset {asset.id!r} already consumed its one curl invocation",
                "Never repeat a declared asset GET; preserve evidence and stop.",
            )
        destination = Path(asset.destination)
        partial = Path(f"{asset.destination}.WD-28ac.partial")
        if destination.exists() or partial.exists():
            raise LTXDownloadControlError(
                "DESTINATION_OR_PARTIAL_COLLISION",
                f"destination or partial already exists for {asset.id!r}",
                "Stop without moving, replacing, or deleting existing evidence.",
            )
        if not destination.parent.is_dir():
            raise LTXDownloadControlError(
                "DESTINATION_PARENT_ABSENT",
                f"destination parent is absent: {destination.parent}",
                "Create only an operator-approved destination directory before retry.",
            )

        argv = self.curl_argv(asset.id, partial)
        self._curl_invocations[asset.id] = 1
        if runner is None:
            def default_runner(command: Sequence[str]) -> CurlOutcome:
                proc = subprocess.run(
                    list(command), text=True, capture_output=True, check=False
                )
                return CurlOutcome(proc.returncode, proc.stdout, proc.stderr)
            runner = default_runner
        result = runner(argv)

        fields = result.stdout.strip().split("\t")
        if len(fields) != 5:
            raise LTXDownloadControlError(
                "CURL_ACCOUNTING_OUTPUT_INVALID",
                f"expected five same-response fields, got {len(fields)}",
                "Keep url_effective in the declared curl --write-out; never issue another GET.",
            )
        http_code, url_effective, size_download, redirect_count, connects = fields
        try:
            size_download_value = int(size_download)
            redirect_count_value = int(redirect_count)
            connects_value = int(connects)
        except ValueError as exc:
            raise LTXDownloadControlError(
                "CURL_ACCOUNTING_OUTPUT_INVALID",
                "curl returned a non-integer size, redirect, or connection count",
                "Preserve the partial; use curl num_redirects and do not repeat the GET.",
            ) from exc
        observed_size = partial.stat().st_size if partial.exists() else 0
        observed_sha256 = _sha256(partial) if partial.exists() else ""
        size_match = observed_size == asset.size_bytes
        sha_match = observed_sha256 == asset.sha256
        promoted = result.returncode == 0 and size_match and sha_match
        if promoted:
            os.replace(partial, destination)

        return {
            "schema_version": "wangp-dspy.wd-28ac.download-attempt/v2",
            "asset_id": asset.id,
            "curl_exit": result.returncode,
            "curl_stderr": result.stderr,
            "http_code": http_code,
            "url_effective": url_effective,
            "url_effective_source": "declared_curl_write_out",
            "reported_size_download_bytes": size_download_value,
            "redirect_count": redirect_count_value,
            "connection_count": connects_value,
            "observed_size_bytes": observed_size,
            "expected_size_bytes": asset.size_bytes,
            "size_match": size_match,
            "observed_sha256": observed_sha256,
            "expected_sha256": asset.sha256,
            "expected_xet_hash": asset.xet_hash,
            "file_sha256_match": sha_match,
            "promoted": promoted,
            "request_accounting": {
                "curl_invocations": 1,
                "declared_request_count": 1,
                "undeclared_request_count": 0,
                "url_effective_probe_request_count": 0,
                "redirect_count": redirect_count_value,
                "network_request_count": 1 + redirect_count_value,
            },
            "curl_argv": argv,
        }


def _canonical_digest(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_controller(
    manifest_path: str | Path, authorization_path: str | Path
) -> DownloadController:
    manifest_payload = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    manifest = load_asset_manifest(manifest_path)
    authorization = json.loads(
        Path(authorization_path).read_text(encoding="utf-8")
    )
    if manifest_payload.get("schema_version") != "wangp-dspy.model-assets/v1":
        raise LTXDownloadControlError(
            "MANIFEST_SCHEMA_INVALID",
            f"unsupported schema {manifest_payload.get('schema_version')!r}",
            "Use wangp-dspy.model-assets/v1 with separated sha256 and xet_hash.",
        )
    if any(asset.xet_hash is None for asset in manifest.assets):
        raise LTXDownloadControlError(
            "XET_IDENTITY_ABSENT",
            "every WD-28ac asset must carry a separate xet_hash",
            "Bind both LFS-OID file SHA-256 and XET identity from metadata.",
        )
    if any(asset.sha256 == asset.xet_hash for asset in manifest.assets):
        raise LTXDownloadControlError(
            "HASH_SEMANTICS_CONFLATED",
            "one or more assets label xet_hash as sha256",
            "Use metadata lfs.oid for sha256 and xetHash for xet_hash.",
        )
    if authorization.get("status") != "authorized":
        raise LTXDownloadControlError(
            "OPERATOR_AUTHORIZATION_INVALID",
            f"authorization status is {authorization.get('status')!r}",
            "Record the exact operator authorization before planning execution.",
        )
    reference = authorization.get("manifest", {})
    if reference.get("sha256") != _canonical_digest(manifest_payload):
        raise LTXDownloadControlError(
            "AUTHORIZATION_MANIFEST_DIGEST_MISMATCH",
            "authorization is not bound to the canonical corrected manifest",
            "Rebind authorization after a deliberate, reviewed manifest change.",
        )
    correction = authorization.get("metadata_correction", {})
    expected_correction = {
        "repository_revision": manifest.source_revision,
        "model_json_sha256": "33fb1cde721375e7b391aa2189b711965364ac0dfa403a48407ab0e8d1604505",
        "tree_json_sha256": "079d472c84a9fa68e29fab9a17896a079ea209f6c6bc8d3313a7601ee5e91baa",
    }
    if any(correction.get(key) != value for key, value in expected_correction.items()):
        raise LTXDownloadControlError(
            "METADATA_AUDIT_BINDING_INVALID",
            "authorization metadata correction does not match preserved evidence",
            "Bind the exact repository revision and both metadata response hashes.",
        )
    retry = bool(authorization.get("retry_authorized"))
    phase_a = authorization.get("jev_phase_a_authorization")
    if not isinstance(phase_a, dict):
        raise LTXDownloadControlError(
            "PHASE_A_AUTHORIZATION_ABSENT",
            "active WD-28ac download control requires Jev Gate #2",
            "Persist and bind live Jev Gate #2 before any Phase A execution.",
        )
    if phase_a != {
        "gate": 2,
        "mode": "live",
        "model": "jev-latest",
        "decision": "CONTINUE",
        "confidence": 0.96,
        "snapshot_sha256": GATE2_SNAPSHOT_SHA256,
        "trace_sha256": GATE2_TRACE_SHA256,
        "phase": "downloads_only",
        "expected_existing_finals": [
            "ltx-2.3-22b-ic-lora-ingredients-0.9.safetensors",
            "ltx-2.3-22b-ic-lora-outpaint.safetensors",
        ],
        "assets": [
            "ltx-2.3-22b-ic-lora-in-outpainting-0.9.safetensors",
            "ltx-2.5-22b-ic-lora-pixel-spatial-upscaler-x2-1.0.safetensors",
            "ltx-2.3-22b-dev_diffusion_model_quanto_int8.safetensors",
        ],
        "max_curl_invocations_per_asset": 1,
        "prohibited_actions": {
            "qc_start_or_stop": True,
            "queue_admission": True,
            "render": True,
            "matrix_transition": True,
            "deletion_move_or_overwrite": True,
            "undeclared_model_or_url_effective_request": True,
        },
        "stop_before": "Jev Gate #3",
        "evidence": "jev-gates/2026-10-03/gate-evidence.json",
    }:
        raise LTXDownloadControlError(
            "PHASE_A_AUTHORIZATION_INVALID",
            "Jev Gate #2 identity, scope, or prohibitions differ from the exact record",
            "Bind the live CONTINUE decision, exact hashes, three assets, and Phase A limits.",
        )
    if set(phase_a["assets"]) != PHASE_A_ASSETS:
        raise LTXDownloadControlError(
            "PHASE_A_ASSET_SCOPE_INVALID",
            "Phase A assets are not exactly the three remaining downloads",
            "Exclude the two verified finals and name only the three absent assets.",
        )
    corrected = authorization.get("corrected_retry_approval")
    if retry:
        if not isinstance(corrected, dict):
            raise LTXDownloadControlError(
                "CORRECTED_RETRY_AUTHORIZATION_INVALID",
                "retry_authorized=true without a corrected retry approval object",
                "Record the verbatim operator corrected-retry approval.",
            )
        static_expectations = {
            "verbatim": CORRECTED_RETRY_VERBATIM,
            "approved_by": "operator",
            "timestamp": CORRECTED_RETRY_TIMESTAMP,
            "corrected_manifest_sha256": _canonical_digest(manifest_payload),
            "max_curl_invocations_per_remaining_asset": 1,
        }
        if any(corrected.get(key) != value for key, value in static_expectations.items()):
            raise LTXDownloadControlError(
                "CORRECTED_RETRY_AUTHORIZATION_INVALID",
                "corrected retry approval identity, timestamp, digest, or invocation bound drifts",
                "Bind the exact live tracker approval and corrected manifest.",
            )
        if set(corrected.get("remaining_download_assets", [])) != REMAINING_ASSETS:
            raise LTXDownloadControlError(
                "CORRECTED_RETRY_ASSET_SCOPE_INVALID",
                "remaining download assets are not exactly the four authorized assets",
                "Exclude the preserved first partial and include only the four named assets.",
            )
        preserved_asset = next(
            asset for asset in manifest.assets if asset.id == PRESERVED_FIRST_ASSET
        )
        preserved_path = f"{preserved_asset.destination}.WD-28ac.partial"
        preserved = corrected.get("preserved_first_partial", {})
        if preserved != {
            "asset_id": PRESERVED_FIRST_ASSET,
            "path": preserved_path,
            "size_bytes": 1_308_778_338,
            "sha256": "515e4e139001ac6282357a5b35372e42e98b3affd5fcc886a52242abeed19559",
            "network_requests_authorized": 0,
            "promotion_required_before_remaining_downloads": True,
        }:
            raise LTXDownloadControlError(
                "CORRECTED_RETRY_PRESERVED_PARTIAL_INVALID",
                "preserved first-partial identity or zero-network promotion boundary drifts",
                "Verify exact size/LFS SHA and promote only the declared preserved partial.",
            )
        if corrected.get("prior_undeclared_url_effective_get") != {
            "reported_payload_bytes": 172_109,
            "retained_as_boundary": True,
            "repeat_allowed": False,
        }:
            raise LTXDownloadControlError(
                "CORRECTED_RETRY_PRIOR_BOUNDARY_INVALID",
                "prior 172109-byte undeclared GET boundary is not retained exactly",
                "Preserve the boundary and prohibit any repeat URL-effectiveness GET.",
            )
        observed_cells = frozenset(
            (item.get("row"), item.get("operation"))
            for item in corrected.get("operation_scope", [])
        )
        if observed_cells != AUTHORIZED_OPERATION_CELLS:
            raise LTXDownloadControlError(
                "CORRECTED_RETRY_OPERATION_SCOPE_INVALID",
                "operation scope is not exactly the seven named cells",
                "Use only the seven authorized LTX operations.",
            )
    authorized_assets = {
        item.get("id"): item for item in authorization.get("assets", [])
    }
    for asset in manifest.assets:
        item = authorized_assets.get(asset.id, {})
        if item.get("sha256") != asset.sha256 or item.get("xet_hash") != asset.xet_hash:
            raise LTXDownloadControlError(
                "AUTHORIZATION_INTEGRITY_MISMATCH",
                f"authorization integrity drift for {asset.id!r}",
                "Keep authorization sha256/xet_hash mappings exactly equal to manifest.",
            )
    return DownloadController(
        manifest,
        authorization,
        retry_authorized=retry,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default=str(RUN_DIR / "model-assets.json"))
    parser.add_argument(
        "--authorization", default=str(RUN_DIR / "operator-authorization.json")
    )
    parser.add_argument("--asset", required=True)
    parser.add_argument("--report")
    parser.add_argument(
        "--execute",
        action="store_true",
        help="execute one declared network GET (requires retry authorization)",
    )
    parser.add_argument(
        "--allow-network",
        action="store_true",
        help="additional execution guard; dry-run never needs this flag",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        controller = load_controller(args.manifest, args.authorization)
        if args.execute and not args.allow_network:
            raise LTXDownloadControlError(
                "NETWORK_GUARD_REQUIRED",
                "--execute requires --allow-network",
                "Pass both guards only after a distinct retry authorization.",
            )
        payload = (
            controller.execute(args.asset)
            if args.execute
            else controller.plan(args.asset)
        )
    except LTXDownloadControlError as exc:
        print(
            json.dumps(
                {
                    "status": "failed_closed",
                    "code": exc.code,
                    "observed": exc.observed,
                    "remediation": exc.remediation,
                },
                sort_keys=True,
            )
        )
        return 2
    output = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.report:
        Path(args.report).write_text(output, encoding="utf-8")
    else:
        print(output, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
