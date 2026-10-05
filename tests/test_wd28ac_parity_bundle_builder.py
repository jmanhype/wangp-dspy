"""Real bundle tests for the six successful WD-28ac Gate 22 lanes."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from scripts.build_wd28ac_parity_bundles import (
    BundleBuildError,
    OPERATIONS,
    TERMINAL_EXCLUDED_OPERATION,
    _validate_record,
    build_all,
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
    before = _snapshot(EVIDENCE_ROOT)
    summary = build_all(ROOT)
    after = _snapshot(EVIDENCE_ROOT)
    assert before == after
    assert summary["operation_count"] == 6
    assert summary["terminal_excluded_operation"] == "ltx23-upscale"
    for operation in OPERATIONS:
        report = verify_bundle(EVIDENCE_ROOT / operation)
        assert report.passed
        assert report.diagnostics == ()


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
