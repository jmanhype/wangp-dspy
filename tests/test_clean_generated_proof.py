from __future__ import annotations

import importlib.util
import json
import shutil
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


def test_clean_generated_authorization_is_the_exact_retry_approval() -> None:
    payload = json.loads((BUNDLE / "operator-authorization.json").read_text(encoding="utf-8"))

    assert payload["text"] == "Authorize"
    assert payload["timestamp"] == "2026-09-29T23:17:30Z"
    assert payload["scope"] == (
        "WD-bw0h clean-machine H3 retry at head "
        "6900884acd6baa3d978d30dd4aae92401b8f75e8, using the existing four-model "
        "no-download manifest and only the governed one-attempt boundary."
    )


@pytest.mark.parametrize("authorization,manifest,phrase", [
    (Path("absent.json"), BUNDLE / "model-assets.json", "CLEAN_GENERATED_INPUT_INVALID"),
    (BUNDLE / "operator-authorization.json", Path("models.json"), "AUTHORIZATION_ALREADY_CONSUMED"),
])
def test_generated_mode_fails_closed_before_workspace(tmp_path: Path, authorization: Path, manifest: Path, phrase: str) -> None:
    if not authorization.is_absolute(): authorization = tmp_path / authorization
    if not manifest.is_absolute():
        payload = json.loads((BUNDLE / "model-assets.json").read_text()); payload["assets"][0]["sha256"] = "0" * 64
        manifest = tmp_path / manifest; manifest.write_text(json.dumps(payload))
    result = _run_script(tmp_path, authorization, manifest)
    assert result.returncode == 4 and f"GENERATED_PROOF_FAILED code={phrase}" in result.stderr
    assert not (tmp_path / "proof").exists()


def test_generated_mode_rejects_tampered_host_before_workspace(tmp_path: Path) -> None:
    payload = json.loads((BUNDLE / "operator-authorization.json").read_text(encoding="utf-8"))
    payload["allowed_host"]["target"] = "unauthorized-host"
    authorization = tmp_path / "operator-authorization.json"
    authorization.write_text(json.dumps(payload), encoding="utf-8")

    result = _run_script(tmp_path, authorization, BUNDLE / "model-assets.json")

    assert result.returncode == 4
    assert "GENERATED_PROOF_FAILED code=CLEAN_GENERATED_INPUT_INVALID" in result.stderr
    assert not (tmp_path / "proof").exists()


def test_consumed_authorization_cannot_be_replayed(tmp_path: Path) -> None:
    result = _run_script(
        tmp_path,
        BUNDLE / "operator-authorization.json",
        BUNDLE / "model-assets.json",
    )

    assert result.returncode == 4
    assert "GENERATED_PROOF_FAILED code=AUTHORIZATION_ALREADY_CONSUMED" in result.stderr
    assert not (tmp_path / "proof").exists()


def test_install_docs_disclose_consumed_authorization() -> None:
    text = (ROOT / "docs/install.md").read_text(encoding="utf-8")

    assert "committed authorization for that retry has been consumed" in text
    assert "historical command shape" in text
    assert "not permission to" in text and "rerun it" in text
    assert "AUTHORIZATION_ALREADY_CONSUMED" in text
    assert "without rebuilding" in text
    assert "absent legacy Wan2GP" in text and "virtual environment" in text
    assert "exact remote work root must be absent" in text


def _future_isolated_runtime_authorization() -> dict[str, Any]:
    authorization = json.loads(
        (
            BUNDLE
            / "isolated-runtime-authorization.template.json"
        ).read_text(encoding="utf-8")
    )
    authorization.update(
        status="approved",
        text="Authorize the exact WD-bw0h isolated-runtime retry",
        timestamp="2026-10-07T16:00:00Z",
        scope="one no-download H3 create through the isolated runtime",
    )
    return authorization


def test_future_isolated_runtime_authorization_shape_is_accepted() -> None:
    recorder = _load_recorder()
    authorization = _future_isolated_runtime_authorization()
    manifest = json.loads((BUNDLE / "model-assets.json").read_text(encoding="utf-8"))

    validated, assets = recorder.inputs(authorization, manifest)

    assert validated is authorization
    assert len(assets) == 4


def test_future_authorization_rejects_runtime_tampering() -> None:
    recorder = _load_recorder()
    authorization = _future_isolated_runtime_authorization()
    authorization["allowed_host"]["runtime"]["python"] = "/usr/local/bin/python3"
    manifest = json.loads((BUNDLE / "model-assets.json").read_text(encoding="utf-8"))

    with pytest.raises(recorder.ProofError, match="authorization boundary mismatch"):
        recorder.inputs(authorization, manifest)


def test_future_authorization_binds_exact_authorized_source_bytes() -> None:
    recorder = _load_recorder()
    authorization = _future_isolated_runtime_authorization()

    recorder.validate_authorized_source(ROOT, authorization)


def test_future_authorization_rejects_changed_source_bytes(tmp_path: Path) -> None:
    recorder = _load_recorder()
    authorization = _future_isolated_runtime_authorization()
    checkout = tmp_path / "checkout"

    for relative in recorder.AUTHORIZED_SOURCE_FILES:
        destination = checkout / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, destination)
    (checkout / "install.sh").write_text("#!/bin/sh\n# changed\n", encoding="utf-8")

    with pytest.raises(recorder.ProofError, match="authorized source bytes differ"):
        recorder.validate_authorized_source(checkout, authorization)


def test_v2_authorization_binds_committed_source_without_circular_commit(tmp_path: Path) -> None:
    recorder = _load_recorder()
    checkout = tmp_path / "checkout"
    checkout.mkdir()

    for relative in recorder.AUTHORIZED_SOURCE_FILES:
        destination = checkout / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, destination)
    authorization = _future_isolated_runtime_authorization()
    authorization_path = checkout / "authorization.json"
    authorization_path.write_text(json.dumps(authorization, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    subprocess.run(("git", "init", str(checkout)), capture_output=True, text=True, check=True)
    subprocess.run(("git", "-C", str(checkout), "add", "."), capture_output=True, text=True, check=True)
    subprocess.run(
        ("git", "-C", str(checkout), "-c", "user.name=Test", "-c", "user.email=test@example.test", "commit", "-m", "v2 authorization"),
        capture_output=True,
        text=True,
        check=True,
    )

    validated, assets = recorder.inputs(authorization, json.loads((BUNDLE / "model-assets.json").read_text(encoding="utf-8")))
    recorder.validate_authorized_source(checkout, validated)

    assert len(assets) == 4


def test_operator_v2_authorization_is_approved_and_exact_source_bound() -> None:
    recorder = _load_recorder()
    authorization = _future_isolated_runtime_authorization()

    assert authorization["status"] == "approved"
    assert authorization["text"]
    assert authorization["allowed_host"] == json.loads(
        (BUNDLE / "isolated-runtime-authorization.template.json").read_text(encoding="utf-8")
    )["allowed_host"]
    recorder.validate_authorized_source(ROOT, authorization)


def test_consumed_v2_authorization_cannot_be_replayed(tmp_path: Path) -> None:
    result = _run_script(
        tmp_path,
        BUNDLE / "operator-authorization.isolated-runtime.v2.json",
        BUNDLE / "model-assets.json",
    )

    assert result.returncode == 4
    assert "GENERATED_PROOF_FAILED code=AUTHORIZATION_ALREADY_CONSUMED" in result.stderr
    assert not (tmp_path / "proof").exists()


def test_model_preflight_parses_literal_remote_tab_escapes() -> None:
    recorder = _load_recorder()
    row = (
        "/home/straughter/Wan2GP/ckpts/model.safetensors"
        "\\t21057674787\\t2026-09-01 17:21:46.441729800 -0500\\t\\t"
        "30ff400f974b11a1ef13d216c5d9f6439a9c10322a3988b0374a39672ce288f0"
    )

    path, size, mtime, digest = recorder.parse_model_row(row)

    assert path == "/home/straughter/Wan2GP/ckpts/model.safetensors"
    assert size == "21057674787"
    assert mtime == "2026-09-01 17:21:46.441729800 -0500"
    assert digest == "30ff400f974b11a1ef13d216c5d9f6439a9c10322a3988b0374a39672ce288f0"


def test_model_preflight_rejects_missing_model_field() -> None:
    recorder = _load_recorder()

    with pytest.raises(recorder.ProofError, match="expected path, size, mtime, and sha256"):
        recorder.parse_model_row("/model.safetensors\\t21057674787")


def test_generated_install_mode_requires_all_explicit_inputs() -> None:
    result = subprocess.run(["sh", str(ROOT / "install.sh"), "--clean-generated-proof", "/tmp/absent-bw0h"], capture_output=True, text=True, check=False)
    assert result.returncode == 11 and "all three explicit input paths are required" in result.stderr


def test_offline_wrapper_exports_exact_isolated_runtime() -> None:
    recorder = _load_recorder()
    config = {
        "wgp_python": "/usr/bin/python3",
        "runtime": {
            "python": "/usr/bin/python3",
            "pythonpath": [
                "/home/straughter/wd-28ac-final-gate7-20261003/runtime/rembg-2.0.65",
                "/home/straughter/wd-28ac-final-gate7-20261003/runtime/mmgp-3.7.14",
                "/home/straughter/ComfyUI/venv/lib/python3.12/site-packages",
            ],
            "environment": {
                "PYTHONUNBUFFERED": "1",
                "PYTORCH_ALLOC_CONF": "expandable_segments:True",
            },
        },
    }

    body = recorder.offline_wrapper_body(config)

    assert "export HF_HUB_OFFLINE=1" in body
    assert "export TRANSFORMERS_OFFLINE=1" in body
    assert "export PYTHONPATH=/home/straughter/wd-28ac-final-gate7-20261003/runtime/rembg-2.0.65:/home/straughter/wd-28ac-final-gate7-20261003/runtime/mmgp-3.7.14:/home/straughter/ComfyUI/venv/lib/python3.12/site-packages" in body
    assert 'exec /usr/bin/python3 "$@"' in body


def test_offline_wrapper_rejects_runtime_python_mismatch() -> None:
    recorder = _load_recorder()
    config = {
        "wgp_python": "/usr/bin/python3",
        "runtime": {
            "python": "/usr/local/bin/python3",
            "pythonpath": ["/opt/isolated-runtime"],
            "environment": {},
        },
    }

    with pytest.raises(
        recorder.ProofError,
        match="runtime python differs from authorized host python",
    ):
        recorder.offline_wrapper_body(config)


def test_remote_work_root_must_be_fresh(tmp_path: Path) -> None:
    class AbsentHost:
        def run_probe(self, argv: list[str], timeout: int = 120) -> tuple[int, str, str]:
            assert argv == ["test", "!", "-e", "/authorized/remote-root"]
            return 0, "", ""

    recorder = _load_recorder()
    proof = tmp_path / "proof"

    recorder.ensure_fresh_remote_root(AbsentHost(), proof, {"remote_work_root": "/authorized/remote-root"})

    payload = json.loads((proof / "preflight/remote-work-root.json").read_text(encoding="utf-8"))
    assert payload == {"path": "/authorized/remote-root", "absent": True, "probe_error": ""}


def test_existing_remote_work_root_fails_closed(tmp_path: Path) -> None:
    class ExistingHost:
        def run_probe(self, argv: list[str], timeout: int = 120) -> tuple[int, str, str]:
            return 1, "", "remote root exists"

    recorder = _load_recorder()

    with pytest.raises(recorder.ProofError, match="remote work root already exists"):
        recorder.ensure_fresh_remote_root(
            ExistingHost(),
            tmp_path / "proof",
            {"remote_work_root": "/authorized/remote-root"},
        )


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
         "--generated-authorization", "datasets/runs/maestro-parity/clean-generated/operator-authorization.isolated-runtime.v2.json",
         "--generated-manifest", "datasets/runs/maestro-parity/clean-generated/model-assets.json"],
        capture_output=True, text=True, check=False,
    )
    combined = result.stdout + result.stderr
    assert result.returncode == 0, combined
    assert f"git clone {ROOT} {workspace}/checkout" in combined
    assert f"--proof-dir {workspace}/proof" in combined
    assert "Checkout ready. Next commands:" not in combined
    assert "run_content_brief.py" not in combined
