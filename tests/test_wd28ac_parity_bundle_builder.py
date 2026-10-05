"""Real bundle tests for the six successful WD-28ac Gate 22 lanes."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pytest

from scripts.build_wd28ac_parity_bundles import (
    BundleBuildError,
    OPERATIONS,
    TERMINAL_EXCLUDED_OPERATION,
    _validate_record,
    build_all,
    _model_provenance,
)
from scripts.verify_maestro_parity import verify_bundle


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_ROOT = ROOT / "datasets/runs/maestro-parity/WD-28ac/gate22"


def _snapshot(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def test_gate22_scope_is_exactly_six_successes_and_excludes_terminal_upscale() -> None:
    assert OPERATIONS == (
        "ltx25-outpaint",
        "ltx25-repaint",
        "ltx25-recast",
        "ltx25-upscale",
        "ltx23-outpaint",
        "ltx23-recast",
    )
    assert TERMINAL_EXCLUDED_OPERATION == "ltx23-upscale"
    assert TERMINAL_EXCLUDED_OPERATION not in OPERATIONS


def test_rebuild_is_deterministic_and_every_real_bundle_passes_checker() -> None:
    summary = build_all(ROOT)
    once = _snapshot(EVIDENCE_ROOT)
    build_all(ROOT)
    after = _snapshot(EVIDENCE_ROOT)
    assert once == after
    assert summary["operation_count"] == 6
    assert summary["terminal_excluded_operation"] == "ltx23-upscale"
    for operation in OPERATIONS:
        report = verify_bundle(EVIDENCE_ROOT / operation)
        assert report.passed
        assert report.diagnostics == ()


def test_model_provenance_contains_only_observed_traceable_models() -> None:
    for operation in OPERATIONS:
        evidence = json.loads(
            (EVIDENCE_ROOT / operation / "evidence.json").read_text(encoding="utf-8")
        )
        native_log = (EVIDENCE_ROOT / operation / "native.log").read_text(
            encoding="utf-8", errors="replace"
        )
        observed = [
            Path(match.group(1)).name
            for match in (
                re.search(r"Loading Model '([^']+)'", native_log),
                re.search(r"Loading Text Encoder '([^']+)'", native_log),
                re.search(r"Lora '([^']+)' was loaded", native_log),
            )
            if match is not None
        ]
        provenance = evidence["model_provenance"]
        assert len(provenance) == 3, (operation, provenance)
        assert {item["identity"].removesuffix(".safetensors").removesuffix(".gguf") for item in provenance} == {
            name.removesuffix(".safetensors").removesuffix(".gguf") for name in observed
        }
        assert all(
            item["identity"].endswith((".safetensors", ".gguf"))
            for item in provenance
        )
        assert all(item["download_approved"] is True for item in provenance)
        assert all("authorization_trace" in item for item in provenance)
        assert {
            item["authorization_trace"]["basis"] for item in provenance
        } == {"pre_existing_host_asset", "operator_authorized_asset"}


def test_model_provenance_fails_closed_for_untraceable_observed_model(
    tmp_path: Path,
) -> None:
    repo = tmp_path
    parity = repo / "datasets/runs/maestro-parity"
    base = parity / "WD-m7xw"
    terminalization = parity / "ltx-dependency-terminalization"
    base.mkdir(parents=True)
    terminalization.mkdir(parents=True)
    (base / "evidence.json").write_text(
        json.dumps(
            {
                "model_provenance": [
                    {
                        "identity": "gemma4.safetensors",
                        "source": "https://example.invalid/gemma4.safetensors",
                        "license": "test license",
                        "sha256": "1" * 64,
                        "destination": "/host/gemma4.safetensors",
                        "preflight_hash_verified": True,
                        "postflight_hash_verified": True,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    (terminalization / "model-assets.json").write_text(
        json.dumps(
            {
                "assets": [
                    {
                        "id": "ltx-2.3-22b-ic-lora-outpaint.safetensors",
                        "source_url": "https://example.invalid/lora.safetensors",
                        "license": "test license",
                        "sha256": "2" * 64,
                        "destination": "/host/lora.safetensors",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    (terminalization / "operator-authorization.json").write_text(
        json.dumps(
            {
                "operator_approval": {
                    "timestamp": "2026-10-03T06:57:55Z",
                    "verbatim": "Authorized",
                },
                "assets": [
                    {
                        "id": "ltx-2.3-22b-ic-lora-outpaint.safetensors",
                        "sha256": "2" * 64,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    native_log = tmp_path / "native.log"
    native_log.write_text(
        "Loading Model 'ckpts/untraceable.safetensors' ...\n"
        "Loading Text Encoder 'ckpts/gemma4.safetensors' ...\n"
        "Lora 'loras/ltx2/ltx-2.3-22b-ic-lora-outpaint.safetensors' was loaded in model 'x'\n",
        encoding="utf-8",
    )
    record = {
        "runtime_preflight": {
            "payload_sha256": "d39fa7a56869387410d299ab139eb724e3be3f04055fd5d0da69d32dec9f309b"
        }
    }

    with pytest.raises(BundleBuildError, match="MODEL_PROVENANCE_AUTHORIZATION_ABSENT"):
        _model_provenance(repo, "ltx25-outpaint", record, native_log)


def test_model_provenance_fails_closed_for_non_model_observed_file(
    tmp_path: Path,
) -> None:
    repo = tmp_path
    parity = repo / "datasets/runs/maestro-parity"
    base = parity / "WD-m7xw"
    terminalization = parity / "ltx-dependency-terminalization"
    base.mkdir(parents=True)
    terminalization.mkdir(parents=True)
    (base / "evidence.json").write_text(
        json.dumps(
            {
                "model_provenance": [
                    {
                        "identity": "base.safetensors",
                        "source": "https://example.invalid/base.safetensors",
                        "license": "test license",
                        "sha256": "1" * 64,
                        "destination": "/host/base.safetensors",
                        "preflight_hash_verified": True,
                        "postflight_hash_verified": True,
                    },
                    {
                        "identity": "tokenizer.json",
                        "source": "https://example.invalid/tokenizer.json",
                        "license": "test license",
                        "sha256": "3" * 64,
                        "destination": "/host/tokenizer.json",
                        "preflight_hash_verified": True,
                        "postflight_hash_verified": True,
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    (terminalization / "model-assets.json").write_text(
        json.dumps(
            {
                "assets": [
                    {
                        "id": "ltx-2.3-22b-ic-lora-outpaint.safetensors",
                        "source_url": "https://example.invalid/lora.safetensors",
                        "license": "test license",
                        "sha256": "2" * 64,
                        "destination": "/host/lora.safetensors",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    (terminalization / "operator-authorization.json").write_text(
        json.dumps(
            {
                "operator_approval": {
                    "timestamp": "2026-10-03T06:57:55Z",
                    "verbatim": "Authorized",
                },
                "assets": [
                    {
                        "id": "ltx-2.3-22b-ic-lora-outpaint.safetensors",
                        "sha256": "2" * 64,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    native_log = tmp_path / "native.log"
    native_log.write_text(
        "Loading Model 'ckpts/base.safetensors' ...\n"
        "Loading Text Encoder 'ckpts/tokenizer.json' ...\n"
        "Lora 'loras/ltx2/ltx-2.3-22b-ic-lora-outpaint.safetensors' was loaded in model 'x'\n",
        encoding="utf-8",
    )
    record = {
        "runtime_preflight": {
            "payload_sha256": "d39fa7a56869387410d299ab139eb724e3be3f04055fd5d0da69d32dec9f309b"
        }
    }

    with pytest.raises(BundleBuildError, match="MODEL_PROVENANCE_NON_MODEL_FILE"):
        _model_provenance(repo, "ltx25-outpaint", record, native_log)


def test_builder_fails_closed_when_output_hash_differs_from_native_record(
    tmp_path: Path,
) -> None:
    bundle = tmp_path / "ltx25-outpaint"
    output_dir = bundle / "native-output"
    output_dir.mkdir(parents=True)
    output = output_dir / "wd_m7xw_outpaint.mp4"
    output.write_bytes(b"changed output bytes")
    (bundle / "settings.json").write_text("{}", encoding="utf-8")
    record = {
        "operation_id": "ltx25-outpaint",
        "admission_state": "admitted",
        "native": {"returncode": 0, "output_path": "/host/wd_m7xw_outpaint.mp4"},
        "status": "rendered_pending_qc",
        "settings": {
            "destination_sha256": hashlib.sha256(b"{}").hexdigest()
        },
        "evidence": {
            "output_sha256": "0" * 64,
            "output_size_bytes": output.stat().st_size,
        },
    }
    (bundle / "operation-record.json").write_text(
        json.dumps(record), encoding="utf-8"
    )
    with pytest.raises(BundleBuildError, match="output SHA-256 drift"):
        _validate_record(bundle, "ltx25-outpaint")
