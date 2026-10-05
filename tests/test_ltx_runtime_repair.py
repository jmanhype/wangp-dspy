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
GATE11_SUMMARY = RUN_DIR / "runtime-repair/2026-10-03/gate-11-evidence.json"
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


def _rooted_wheel_bytes(root_content: bytes) -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        archive.writestr("__init__.py", root_content)
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
    gate_summary: Path = GATE_SUMMARY,
) -> runner.RuntimeRepairRunner:
    runtime_root = tmp_path / "runtime"
    return runner.RuntimeRepairRunner(
        metadata_path=METADATA,
        gate_summary_path=gate_summary,
        authorization_path=AUTHORIZATION,
        manifest_path=MANIFEST,
        operation_plan_path=PLAN,
        runtime_root=runtime_root,
        report_path=tmp_path / "report.json",
        destination=runtime_root / "mmgp-3.7.14",
        fetcher=fetcher,
        importer=_importer,
    )


def _resume_runner(
    tmp_path: Path,
    *,
    payload: bytes,
) -> runner.RuntimeRepairRunner:
    runtime_root = tmp_path / "runtime"
    runtime_root.mkdir()
    (runtime_root / runner.WHEEL_FILENAME).write_bytes(payload)
    (runtime_root / ".mmgp-3.7.14.extraction-staging").mkdir()
    return runner.RuntimeRepairRunner(
        metadata_path=METADATA,
        gate_summary_path=GATE11_SUMMARY,
        authorization_path=AUTHORIZATION,
        manifest_path=MANIFEST,
        operation_plan_path=PLAN,
        runtime_root=runtime_root,
        report_path=tmp_path / "resume-report.json",
        destination=runtime_root / "mmgp-3.7.14",
        fetcher=lambda *_: pytest.fail("network attempted during resume"),
        importer=_importer,
    )


def _patch_resume_constants(
    monkeypatch: pytest.MonkeyPatch, payload: bytes
) -> None:
    monkeypatch.setattr(runner, "WHEEL_SIZE", len(payload))
    monkeypatch.setattr(
        runner, "WHEEL_SHA256", hashlib.sha256(payload).hexdigest()
    )


def test_wheel_layout_authorization_is_exact_and_secret_free() -> None:
    authorization = json.loads(AUTHORIZATION.read_text(encoding="utf-8"))
    record = authorization["operator_wheel_layout_authorization"]

    assert record == {
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
        "wheel_filename": "mmgp-3.7.14-py3-none-any.whl",
        "wheel_size_bytes": 68_211,
        "wheel_sha256": (
            "6b544fa77a0256586bd9223c8f85c83a318c5d2f184b6adbdc655b7f22b5d208"
        ),
        "root_member": "__init__.py",
        "inert_requirement": "empty_or_whitespace_or_module_docstring_only",
        "resume_scope": "preserved_wheel_extraction_import_once",
        "network_get_limit": 0,
        "destination": "/home/straughter/wd-28ac-final-gate7-20261003/runtime/mmgp-3.7.14",
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
    for pattern in SECRET_PATTERNS:
        assert pattern.search(AUTHORIZATION.read_bytes()) is None


def test_inert_root_classifier_accepts_only_inert_python() -> None:
    accepted = {
        b"": "empty",
        b"\n \t\n": "whitespace_only",
        b"\"Module docstring only.\"\n": "module_docstring_only",
        b"# comment only\n": "comments_only",
    }
    for content, classification in accepted.items():
        result = runner.classify_root_member(content)
        assert result["is_inert"] is True, content
        assert result["classification"] == classification
        assert result["byte_count"] == len(content)
        assert result["sha256"] == hashlib.sha256(content).hexdigest()

    rejected = (
        b"VALUE = 1\n",
        b"import os\n",
        b"print('call')\n",
        b"\"doc\"\nVALUE = 1\n",
        b"\x00\xff\n",
        b"def broken(:\n",
    )
    for content in rejected:
        result = runner.classify_root_member(content)
        assert result["is_inert"] is False, content
        assert result["ast_body_node_types"] is not None or (
            result["classification"] in {
                "invalid_utf8", "invalid_python", "non_inert_statements"
            }
        )


def test_resume_preserved_wheel_extracts_and_imports_with_zero_network(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_environment(monkeypatch)
    payload = _rooted_wheel_bytes(b"")
    _patch_resume_constants(monkeypatch, payload)
    unit = _resume_runner(tmp_path, payload=payload)

    report = unit.run(resume=True)

    assert report["status"] == "passed"
    assert report["mode"] == "resume_preserved_wheel"
    assert report["network_accounting"] == {
        "declared_wheel_gets": 0,
        "undeclared_requests": 0,
        "wheel_get_limit": 0,
    }
    assert report["root_member"]["member"] == "__init__.py"
    assert report["root_member"]["classification"]["is_inert"] is True
    assert report["extraction"]["file_count"] == 3
    assert (unit.destination / "__init__.py").read_bytes() == b""
    assert (unit.destination / "mmgp/__init__.py").is_file()
    assert not (
        unit.destination.parent / ".mmgp-3.7.14.extraction-staging"
    ).exists()
    assert report["isolated_import"]["returncode"] == 0
    assert report["post_system_mmgp"]["returncode"] == 1
    assert report["preservation_unchanged"] is True


def test_resume_rejects_non_inert_root_without_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_environment(monkeypatch)
    payload = _rooted_wheel_bytes(b"VALUE = 1\n")
    _patch_resume_constants(monkeypatch, payload)
    unit = _resume_runner(tmp_path, payload=payload)
    staging = unit.destination.parent / ".mmgp-3.7.14.extraction-staging"

    with pytest.raises(runner.RuntimeRepairError) as raised:
        unit.run(resume=True)

    assert raised.value.code == "ROOT_MEMBER_NOT_INERT"
    assert unit.runtime_root.joinpath(runner.WHEEL_FILENAME).read_bytes() == payload
    assert list(staging.iterdir()) == []
    assert not unit.destination.exists()
    assert json.loads((tmp_path / "resume-report.json").read_text())[
        "boundary"
    ]["code"] == "ROOT_MEMBER_NOT_INERT"


def test_resume_rejects_hash_mismatch_before_extraction(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_environment(monkeypatch)
    payload = _rooted_wheel_bytes(b"")
    monkeypatch.setattr(runner, "WHEEL_SIZE", len(payload))
    monkeypatch.setattr(runner, "WHEEL_SHA256", "0" * 64)
    unit = _resume_runner(tmp_path, payload=payload)

    with pytest.raises(runner.RuntimeRepairError) as raised:
        unit.run(resume=True)

    assert raised.value.code == "WHEEL_HASH_MISMATCH"
    assert unit.runtime_root.joinpath(runner.WHEEL_FILENAME).read_bytes() == payload
    assert list((unit.destination.parent / ".mmgp-3.7.14.extraction-staging").iterdir()) == []
    assert not unit.destination.exists()


def test_resume_refuses_collisions_and_never_overwrites_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_environment(monkeypatch)
    payload = _rooted_wheel_bytes(b"")
    _patch_resume_constants(monkeypatch, payload)

    cases = ("report", "staging", "destination")
    for case in cases:
        workspace = tmp_path / case
        workspace.mkdir()
        unit = _resume_runner(workspace, payload=payload)
        staging = unit.destination.parent / ".mmgp-3.7.14.extraction-staging"
        preserved = {
            "report": unit.report_path,
            "staging": staging / "preserved",
            "destination": unit.destination / "preserved",
        }[case]
        preserved.parent.mkdir(parents=True, exist_ok=True)
        preserved.write_bytes(b"preserved")

        with pytest.raises(runner.RuntimeRepairError) as raised:
            unit.run(resume=True)

        assert raised.value.code == "RESUME_STATE_COLLISION"
        assert preserved.read_bytes() == b"preserved"
        assert not unit.destination.exists() or case == "destination"
        assert unit.runtime_root.joinpath(runner.WHEEL_FILENAME).read_bytes() == payload


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


def test_gate11_binds_corrected_exact_module_import_scope() -> None:
    gate = json.loads(GATE11_SUMMARY.read_text(encoding="utf-8"))
    authorization = json.loads(AUTHORIZATION.read_text(encoding="utf-8"))
    runner.validate_gate11(gate, authorization)

    assert gate["gate"] == 11
    assert gate["decision"] == "CONTINUE"
    assert gate["confidence"] == 0.82
    assert gate["constraint_risk"] == 0.28
    assert gate["missing_evidence_score"] == 1.35
    assert gate["scope"] == "CORRECTED_ISOLATED_RUNTIME_REPAIR_ONCE"
    assert gate["declared_snapshot_sha256"] == (
        "a4b77d969d5b675e6e076175aa6bc62caa7d927a3548a03b8b93e1ca3d3a720e"
    )
    assert gate["declared_trace_sha256"] == (
        "080d570ea8cc90df011d834d663d50bce562ff67961b32686957284f191c6f92"
    )
    assert gate["prior_gate10_boundary"] == {
        "declared_wheel_gets": 0,
        "undeclared_requests": 0,
        "must_remain_unchanged": True,
    }
    assert authorization["jev_corrected_runtime_repair_authorization"][
        "dependency_probe"
    ] == "exact_module_import"


def test_dependency_probe_imports_exact_module_without_top_level_metadata(
    tmp_path: Path,
) -> None:
    namespace = tmp_path / "optimum" / "quanto"
    namespace.mkdir(parents=True)
    (namespace / "__init__.py").write_text("VALUE = 1\n", encoding="utf-8")

    module_only = runner._python_import(
        sys.executable, "optimum.quanto",
        isolated_path=str(tmp_path), require_metadata=False,
    )
    metadata_probe = runner._python_import(
        sys.executable, "optimum.quanto",
        isolated_path=str(tmp_path), require_metadata=True,
    )

    assert module_only["returncode"] == 0
    payload = json.loads(module_only["stdout"])
    assert payload["path"] == str(namespace / "__init__.py")
    assert payload["metadata_version"] is None
    assert metadata_probe["returncode"] != 0
    assert "No package metadata was found for optimum" in metadata_probe["stderr"]


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


def test_resume_real_process_dry_run_binds_zero_network_guard() -> None:
    report = Path("/tmp/wd28ac-runtime-repair-resume-dry-run.json")
    argv = [
        sys.executable, str(SCRIPT),
        "--metadata", str(METADATA),
        "--gate-summary", str(GATE11_SUMMARY),
        "--authorization", str(AUTHORIZATION),
        "--manifest", str(MANIFEST),
        "--operation-plan", str(PLAN),
        "--report", str(report),
        "--resume-preserved-wheel",
    ]
    result = subprocess.run(
        argv, text=True, capture_output=True, timeout=60
    )
    assert result.returncode == 0
    assert json.loads(result.stdout) == {
        "status": "dry_run_validated",
        "wheel": {
            "filename": "mmgp-3.7.14-py3-none-any.whl",
            "size": 68_211,
            "sha256": (
                "6b544fa77a0256586bd9223c8f85c83a318c5d2f184b6adbdc655b7f22b5d208"
            ),
        },
        "declared_wheel_gets": 0,
        "dependency_installs": 0,
        "mode": "resume_preserved_wheel",
        "network_get_limit": 0,
    }
    assert not report.exists()

    guarded = subprocess.run(
        [*argv, "--execute", "--allow-network"],
        text=True, capture_output=True, timeout=60,
    )
    assert guarded.returncode == 2
    assert json.loads(guarded.stdout)["code"] == (
        "NETWORK_FORBIDDEN_IN_RESUME_MODE"
    )
