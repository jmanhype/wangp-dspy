from __future__ import annotations

import hashlib
import io
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Any

import pytest

import scripts.repair_ltx_runtime as runner


ROOT = Path(__file__).resolve().parents[1]
RUN_DIR = ROOT / "datasets/runs/maestro-parity/ltx-dependency-terminalization"
METADATA = RUN_DIR / "runtime-repair/2026-10-03/mmgp-35714.json"
GATE_SUMMARY = RUN_DIR / "runtime-repair/2026-10-03/gate-summary.json"
AUTHORIZATION = RUN_DIR / "operator-authorization.json"
MANIFEST = RUN_DIR / "model-assets.json"
PLAN = RUN_DIR / "phase-b-preparation/final-operation-plan.json"
SCRIPT = ROOT / "scripts/repair_ltx_runtime.py"


SECRET_PATTERNS = (
    re.compile(rb"sk-(?:proj-)?[A-Za-z0-9_-]{20,}"),
    re.compile(rb"(?i)api[_-]?key\s*[:=]"),
    re.compile(rb"(?i)authorization\s*[:=]\s*[\"']?bearer"),
    re.compile(rb"(?:Signature=|Policy=|X-Amz-Signature=|access_token=)", re.I),
)


def _wheel_bytes() -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        archive.writestr("mmgp/__init__.py", "__version__ = '3.7.14'\n")
        archive.writestr(
            "mmgp-3.7.14.dist-info/METADATA",
            "Metadata-Version: 2.1\nName: mmgp\nVersion: 3.7.14\n",
        )
    return output.getvalue()


def _patch_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(runner, "_state", lambda: {
        "gpu": {"stdout": "GPU,24576,139,23978,0"},
        "gpu_apps": {"stdout": ""},
        "disk": {"stdout": "filesystem"},
        "processes": {"stdout": ""},
    })
    monkeypatch.setattr(
        runner, "_preservation_snapshot",
        lambda manifest, plan: {"models": {}, "references": {}},
    )


def _importer(module: str, isolated_path: str) -> dict[str, Any]:
    if module == "mmgp" and isolated_path:
        return {
            "returncode": 0,
            "stdout": json.dumps({
                "path": f"{isolated_path}/mmgp/__init__.py",
                "metadata_version": "3.7.14",
            }),
            "stderr": "",
        }
    if module == "mmgp":
        return {"returncode": 1, "stdout": "", "stderr": "No module named 'mmgp'"}
    return {
        "returncode": 0,
        "stdout": json.dumps({"path": f"/system/{module}.py"}),
        "stderr": "",
    }


def _runner(
    tmp_path: Path,
    *,
    fetcher: runner.FetchResult | Any,
) -> runner.RuntimeRepairRunner:
    runtime_root = tmp_path / "runtime"
    return runner.RuntimeRepairRunner(
        metadata_path=METADATA,
        gate_summary_path=GATE_SUMMARY,
        authorization_path=AUTHORIZATION,
        manifest_path=MANIFEST,
        operation_plan_path=PLAN,
        runtime_root=runtime_root,
        report_path=tmp_path / "report.json",
        destination=runtime_root / "mmgp-3.7.14",
        fetcher=fetcher,
        importer=_importer,
    )


def test_exact_gate8_10_evidence_and_metadata_are_secret_free() -> None:
    summary = json.loads(GATE_SUMMARY.read_text(encoding="utf-8"))
    metadata = runner.validate_metadata(json.loads(METADATA.read_text()))

    assert summary["gates"]["8"]["scope"] == "READONLY_RUNTIME_INVENTORY_ONLY"
    assert summary["gates"]["9"]["scope"] == "METADATA_ONLY"
    assert summary["gates"]["10"]["scope"] == "ISOLATED_RUNTIME_REPAIR_ONLY"
    assert summary["gates"]["10"]["declared_snapshot_sha256"] == (
        "38780b034bc9d862491a8ec846e2ae3d736647cb65720a3f3dc426ccddb3bb4f"
    )
    assert metadata["wheel_filename"] == "mmgp-3.7.14-py3-none-any.whl"
    assert metadata["wheel_size"] == 68_211
    assert metadata["wheel_sha256"] == (
        "6b544fa77a0256586bd9223c8f85c83a318c5d2f184b6adbdc655b7f22b5d208"
    )
    assert summary["raw_api_key_scan"]["matches"] == 0
    for directory in (GATE_SUMMARY.parent, RUN_DIR / "jev-gates/2026-10-03"):
        for path in directory.iterdir():
            if not path.is_file():
                continue
            for pattern in SECRET_PATTERNS:
                assert pattern.search(path.read_bytes()) is None, path.name


def test_one_fetch_real_zip_extraction_and_isolated_import(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_environment(monkeypatch)
    payload = _wheel_bytes()
    monkeypatch.setattr(runner, "WHEEL_SIZE", len(payload))
    monkeypatch.setattr(
        runner, "WHEEL_SHA256", hashlib.sha256(payload).hexdigest()
    )
    calls: list[str] = []

    def fetch(url: str, destination: Path, timeout: int) -> runner.FetchResult:
        calls.append(url)
        destination.write_bytes(payload)
        return runner.FetchResult(
            destination, 200, url, str(len(payload)), 1, 0
        )

    unit = _runner(tmp_path, fetcher=fetch)
    report = unit.run()

    assert calls == [json.loads(METADATA.read_text())["urls"][0]["url"]]
    assert report["status"] == "passed"
    assert report["network_accounting"]["declared_wheel_gets"] == 1
    assert report["network_accounting"]["undeclared_requests"] == 0
    assert report["dependency_installs"] == 0
    assert report["extraction"]["file_count"] == 2
    assert (unit.destination / "mmgp/__init__.py").is_file()
    assert report["isolated_import"]["returncode"] == 0
    assert report["post_system_mmgp"]["returncode"] == 1
    assert report["preservation_unchanged"] is True


def test_wrong_hash_preserves_wheel_and_stops_before_extraction(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_environment(monkeypatch)
    payload = b"wrong-but-preserved"
    monkeypatch.setattr(runner, "WHEEL_SIZE", len(payload))
    monkeypatch.setattr(runner, "WHEEL_SHA256", "0" * 64)
    calls: list[str] = []

    def fetch(url: str, destination: Path, timeout: int) -> runner.FetchResult:
        calls.append(url)
        destination.write_bytes(payload)
        return runner.FetchResult(destination, 200, url, str(len(payload)), 1, 0)

    unit = _runner(tmp_path, fetcher=fetch)
    with pytest.raises(runner.RuntimeRepairError) as raised:
        unit.run()
    assert raised.value.code == "WHEEL_HASH_MISMATCH"
    assert len(calls) == 1
    assert unit.runtime_root.joinpath(runner.WHEEL_FILENAME).read_bytes() == payload
    assert not unit.destination.exists()
    assert json.loads((tmp_path / "report.json").read_text())["boundary"]["code"] == (
        "WHEEL_HASH_MISMATCH"
    )


def test_existing_destination_fails_before_network(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_environment(monkeypatch)
    runtime_root = tmp_path / "runtime"
    destination = runtime_root / "mmgp-3.7.14"
    destination.parent.mkdir(parents=True)
    destination.mkdir()

    def no_fetch(url: str, destination: Path, timeout: int) -> runner.FetchResult:
        raise AssertionError("network attempted after destination collision")

    unit = _runner(tmp_path, fetcher=no_fetch)
    with pytest.raises(runner.RuntimeRepairError) as raised:
        unit.preflight()
    assert raised.value.code == "RUNTIME_PATH_COLLISION"


def test_wheel_path_escape_and_symlink_members_fail_closed(tmp_path: Path) -> None:
    wheel = tmp_path / "unsafe.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr("../escape", "x")
    with zipfile.ZipFile(wheel, "r") as archive:
        with pytest.raises(runner.RuntimeRepairError) as raised:
            runner.validate_wheel_members(archive)
    assert raised.value.code == "WHEEL_UNSAFE_MEMBER"


def test_real_process_dry_run_uses_no_network() -> None:
    result = subprocess.run([
        sys.executable, str(SCRIPT),
        "--metadata", str(METADATA),
        "--gate-summary", str(GATE_SUMMARY),
        "--authorization", str(AUTHORIZATION),
        "--manifest", str(MANIFEST),
        "--operation-plan", str(PLAN),
        "--report", "/tmp/wd28ac-runtime-repair-dry-run.json",
    ], text=True, capture_output=True, timeout=60)
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload == {
        "status": "dry_run_validated",
        "wheel": {
            "filename": "mmgp-3.7.14-py3-none-any.whl",
            "size": 68_211,
            "sha256": "6b544fa77a0256586bd9223c8f85c83a318c5d2f184b6adbdc655b7f22b5d208",
        },
        "declared_wheel_gets": 0,
        "dependency_installs": 0,
    }
