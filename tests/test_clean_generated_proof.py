from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/record_clean_generated_proof.py"
BUNDLE = ROOT / "datasets/runs/maestro-parity/clean-generated"


def _load_recorder() -> Any:
    spec = importlib.util.spec_from_file_location("record_clean_generated_proof", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run_script(tmp_path: Path, authorization: Path, manifest: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--proof-dir", str(tmp_path / "proof"), "--checkout", str(ROOT),
         "--installer", str(ROOT / "install.sh"), "--authorization", str(authorization),
         "--model-manifest", str(manifest)], capture_output=True, text=True, check=False,
    )


def test_clean_generated_manifest_is_the_exact_four_h3_assets() -> None:
    payload = json.loads((BUNDLE / "model-assets.json").read_text(encoding="utf-8"))
    accepted = json.loads((ROOT / "datasets/runs/maestro-parity/WD-isg9/model-assets.json").read_text(encoding="utf-8"))
    assert payload == accepted and len(payload["assets"]) == 4


@pytest.mark.parametrize("authorization,manifest,phrase", [
    (Path("absent.json"), BUNDLE / "model-assets.json", "CLEAN_GENERATED_INPUT_INVALID"),
    (BUNDLE / "operator-authorization.json", Path("models.json"), "model manifest must equal"),
])
def test_generated_mode_fails_closed_before_workspace(tmp_path: Path, authorization: Path, manifest: Path, phrase: str) -> None:
    if not authorization.is_absolute(): authorization = tmp_path / authorization
    if not manifest.is_absolute():
        payload = json.loads((BUNDLE / "model-assets.json").read_text()); payload["assets"][0]["sha256"] = "0" * 64
        manifest = tmp_path / manifest; manifest.write_text(json.dumps(payload))
    result = _run_script(tmp_path, authorization, manifest)
    assert result.returncode == 4 and phrase in result.stderr
    assert "GENERATED_PROOF_FAILED code=CLEAN_GENERATED_INPUT_INVALID" in result.stderr
    assert not (tmp_path / "proof").exists()


def test_generated_install_mode_requires_all_explicit_inputs() -> None:
    result = subprocess.run(["sh", str(ROOT / "install.sh"), "--clean-generated-proof", "/tmp/absent-bw0h"], capture_output=True, text=True, check=False)
    assert result.returncode == 11 and "all three explicit input paths are required" in result.stderr


def test_workspace_record_serializes_paths_without_permissive_json_values(tmp_path: Path) -> None:
    recorder = _load_recorder()
    workspace = tmp_path / "proof"
    output = workspace / "workspace.json"

    recorder.record(output, {"workspace": tmp_path, "checkout": tmp_path / "checkout"})

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload == {"workspace": str(tmp_path), "checkout": str(tmp_path / "checkout")}
    assert not output.with_name(output.name + ".tmp").exists()

    rejected = workspace / "failure.json"
    with pytest.raises(TypeError, match="Object of type object is not JSON serializable"):
        recorder.record(rejected, {"unexpected": object()})
    assert not rejected.exists()


def test_generated_install_dry_run_preserves_isolated_checkout_and_inputs() -> None:
    workspace = "/tmp/absent-bw0h-workspace"
    result = subprocess.run(
        ["sh", str(ROOT / "install.sh"), "--dry-run", "--source", str(ROOT), "--clean-generated-proof", workspace,
         "--generated-authorization", "datasets/runs/maestro-parity/clean-generated/operator-authorization.json",
         "--generated-manifest", "datasets/runs/maestro-parity/clean-generated/model-assets.json"],
        capture_output=True, text=True, check=False,
    )
    combined = result.stdout + result.stderr
    assert result.returncode == 0, combined
    assert f"git clone {ROOT} {workspace}/checkout" in combined
    assert f"--proof-dir {workspace}/proof" in combined
