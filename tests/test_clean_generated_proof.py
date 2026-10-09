from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from services.jobs.queue import JobQueue


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/record_clean_generated_proof.py"
BUNDLE = ROOT / "datasets/runs/maestro-parity/clean-generated"
RETRY3 = BUNDLE / "failed-isolated-retry3-20261008"
RETRY3_HISTORICAL_SOURCE = RETRY3 / "historical-source"
RETRY3_HISTORICAL_SOURCE_FILES = (
    "install.sh",
    "scripts/record_clean_generated_proof.py",
    "scripts/verify_maestro_parity.py",
    "datasets/runs/maestro-parity/clean-generated/model-assets.json",
)


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


def _copy_retry3_historical_source(checkout: Path) -> None:
    for relative in RETRY3_HISTORICAL_SOURCE_FILES:
        destination = checkout / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(RETRY3_HISTORICAL_SOURCE / relative, destination)


def test_retry3_historical_source_evidence_is_exact_and_authorized() -> None:
    recorder = _load_recorder()
    authorization = json.loads((RETRY3 / "inputs/operator-authorization.json").read_text(encoding="utf-8"))
    authorized_files = authorization["authorized_source"]["files"]
    evidence_files = {
        path.relative_to(RETRY3_HISTORICAL_SOURCE).as_posix()
        for path in RETRY3_HISTORICAL_SOURCE.rglob("*")
        if path.is_file()
    }

    assert evidence_files == set(RETRY3_HISTORICAL_SOURCE_FILES)
    assert set(authorized_files) == evidence_files
    for relative in RETRY3_HISTORICAL_SOURCE_FILES:
        assert recorder.sha(RETRY3_HISTORICAL_SOURCE / relative) == authorized_files[relative]


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


def test_retry4_operator_authorization_is_approved_and_source_bound() -> None:
    recorder = _load_recorder()
    proposal = BUNDLE / "operator-proposal.isolated-runtime.retry4-20261009.json"
    authorization = json.loads(
        (
            BUNDLE
            / "operator-authorization.isolated-runtime.retry4-20261009.json"
        ).read_text(encoding="utf-8")
    )
    manifest = json.loads((BUNDLE / "model-assets.json").read_text(encoding="utf-8"))

    assert recorder.sha(proposal) == (
        "ac708a0886d2b6c18c58cc74139b37211244abbc54dc4960fe64698db1d8063b"
    )
    assert authorization["operator_approval"] == {
        "proposal": (
            "datasets/runs/maestro-parity/clean-generated/"
            "operator-proposal.isolated-runtime.retry4-20261009.json"
        ),
        "proposal_sha256": (
            "ac708a0886d2b6c18c58cc74139b37211244abbc54dc4960fe64698db1d8063b"
        ),
        "verbatim": "Continue authorized approved",
        "approved_at": "2026-10-09T00:21:12Z",
    }
    # Consumed retry4 authorizes the historical recorder, not this new preflight.
    with pytest.raises(recorder.ProofError, match="authorized source bytes differ"):
        recorder.validate_authorized_source(ROOT, authorization)

    assert authorization["status"] == "approved"
    assert authorization["text"] == "Continue authorized approved"
    assert authorization["allowed_host"]["remote_work_root"] == (
        "/home/straughter/Wan2GP/wd-bw0h-clean-generated-retry4-20261008"
    )
    assert len(manifest["assets"]) == 4


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

    with pytest.raises(recorder.ProofError, match="authorized source bytes differ"):
        recorder.validate_authorized_source(ROOT, authorization)


@pytest.mark.parametrize("relative", ["install.sh", "host/wangp_adapter.py", "host/render_host.py"])
def test_future_authorization_rejects_changed_source_bytes(tmp_path: Path, relative: str) -> None:
    recorder = _load_recorder()
    authorization = _future_isolated_runtime_authorization()
    checkout = tmp_path / "checkout"

    for source in recorder.V3_AUTHORIZED_SOURCE_FILES:
        destination = checkout / source
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / source, destination)
    (checkout / relative).write_text("# changed\n", encoding="utf-8")

    with pytest.raises(recorder.ProofError, match="authorized source bytes differ"):
        recorder.validate_authorized_source(checkout, authorization)


def test_v3_authorization_binds_committed_source_without_circular_commit(tmp_path: Path) -> None:
    recorder = _load_recorder()
    checkout = tmp_path / "checkout"
    checkout.mkdir()

    for relative in recorder.V3_AUTHORIZED_SOURCE_FILES:
        destination = checkout / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, destination)
    authorization = _future_isolated_runtime_authorization()
    authorization_path = checkout / "authorization.json"
    authorization_path.write_text(json.dumps(authorization, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    subprocess.run(("git", "init", str(checkout)), capture_output=True, text=True, check=True)
    subprocess.run(("git", "-C", str(checkout), "add", "."), capture_output=True, text=True, check=True)
    subprocess.run(
        ("git", "-C", str(checkout), "-c", "user.name=Test", "-c", "user.email=test@example.test", "commit", "-m", "v3 authorization"),
        capture_output=True,
        text=True,
        check=True,
    )

    validated, assets = recorder.inputs(authorization, json.loads((BUNDLE / "model-assets.json").read_text(encoding="utf-8")))
    # A future approval must bind the updated recorder; do not rewrite historical approval files.
    validated["authorized_source"]["files"] = recorder.source_manifest(checkout, recorder.V3_AUTHORIZED_SOURCE_FILES)
    validated["authorized_source"]["identity_sha256"] = recorder.source_identity(validated["authorized_source"]["files"])
    recorder.validate_authorized_source(checkout, validated)

    assert len(assets) == 4


def test_operator_v3_authorization_is_approved_and_exact_source_bound() -> None:
    recorder = _load_recorder()
    authorization = _future_isolated_runtime_authorization()

    assert authorization["status"] == "approved"
    assert authorization["text"]
    assert authorization["allowed_host"] == json.loads(
        (BUNDLE / "isolated-runtime-authorization.template.json").read_text(encoding="utf-8")
    )["allowed_host"]
    with pytest.raises(recorder.ProofError, match="authorized source bytes differ"):
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


def test_retry2_operator_authorization_cannot_be_replayed(tmp_path: Path) -> None:
    recorder = _load_recorder()
    result = _run_script(
        tmp_path,
        BUNDLE / "operator-authorization.isolated-runtime.retry2-20261008.json",
        BUNDLE / "model-assets.json",
    )

    assert result.returncode == 4
    assert "GENERATED_PROOF_FAILED code=AUTHORIZATION_ALREADY_CONSUMED" in result.stderr
    assert not (tmp_path / "proof").exists()


def test_retry3_operator_authorization_cannot_be_replayed_after_consumption(tmp_path: Path) -> None:
    recorder = _load_recorder()
    retry3 = BUNDLE / "failed-isolated-retry3-20261008"
    authorization = json.loads((retry3 / "inputs/operator-authorization.json").read_text(encoding="utf-8"))
    manifest = json.loads((retry3 / "inputs/model-assets.json").read_text(encoding="utf-8"))

    with pytest.raises(recorder.ProofError) as caught:
        recorder.inputs(authorization, manifest)

    assert caught.value.code == "AUTHORIZATION_ALREADY_CONSUMED"
    assert not (tmp_path / "proof").exists()

    records = json.loads((BUNDLE / "authorization-consumption.json").read_text(encoding="utf-8"))["records"]
    consumed = [record for record in records if record["authorization_canonical_sha256"] == (
        "521c1e07e6496a1fcb6be435fcb0dcaa358a5e1c236c022283776d385afa746a"
    )]
    assert len(consumed) == 1
    assert consumed[0]["status"] == "consumed"
    assert consumed[0]["evidence"]
    assert all((ROOT / path).is_file() for path in consumed[0]["evidence"])


def test_retry3_operator_authorization_is_approved_and_source_bound(tmp_path: Path) -> None:
    recorder = _load_recorder()
    authorization = json.loads(
        (
            BUNDLE
            / "operator-authorization.isolated-runtime.retry3-20261008.json"
        ).read_text(encoding="utf-8")
    )
    manifest = json.loads((BUNDLE / "model-assets.json").read_text(encoding="utf-8"))

    # Historical v2 hashes must validate against historical bytes, not the v3 recorder.
    _copy_retry3_historical_source(tmp_path)
    recorder.validate_authorized_source(tmp_path, authorization)
    assert len(authorization["authorized_source"]["files"]) == 4

    assert authorization["status"] == "approved"
    assert authorization["text"] == "Continue approved authorized"
    assert authorization["allowed_host"]["remote_work_root"] == (
        "/home/straughter/Wan2GP/wd-bw0h-clean-generated-retry3-20261008"
    )
    assert len(manifest["assets"]) == 4


def test_retry4_operator_authorization_cannot_be_replayed_after_consumption() -> None:
    recorder = _load_recorder()
    retry4 = BUNDLE / "failed-isolated-retry4-20261009"
    authorization = json.loads((retry4 / "inputs/operator-authorization.json").read_text(encoding="utf-8"))
    manifest = json.loads((retry4 / "inputs/model-assets.json").read_text(encoding="utf-8"))

    with pytest.raises(recorder.ProofError) as caught:
        recorder.inputs(authorization, manifest)

    assert caught.value.code == "AUTHORIZATION_ALREADY_CONSUMED"
    with pytest.raises(recorder.ProofError, match="authorized source bytes differ"):
        recorder.validate_authorized_source(ROOT, authorization)

    records = json.loads((BUNDLE / "authorization-consumption.json").read_text(encoding="utf-8"))["records"]
    consumed = [record for record in records if record["authorization_canonical_sha256"] == (
        "4957b87064d0e7a93b566f426ee352084af8c5ebb7d1af876ce11e22fa68f969"
    )]
    assert len(consumed) == 1
    assert consumed[0]["generated_artifact"] is False
    assert all((ROOT / path).is_file() for path in consumed[0]["evidence"])


def test_retry4_boundary_proves_media_write_failure_after_staging_repair() -> None:
    retry4 = BUNDLE / "failed-isolated-retry4-20261009"
    failure = json.loads((retry4 / "failure.json").read_text(encoding="utf-8"))
    queue = json.loads((retry4 / "queue/final.json").read_text(encoding="utf-8"))
    native_log = (retry4 / "host-logs/render.log").read_text(encoding="utf-8")
    settings_probe = (retry4 / "host-logs/remote-settings-probe.txt").read_text(encoding="utf-8")

    assert failure["diagnostic"] == {
        "code": "GENERATION_FAILED",
        "detail": "queue did not complete exactly one render: failed",
    }
    assert failure["generated_artifact"] is False
    assert queue["state"] == "failed"
    assert queue["clips"][0]["render_attempted"] is True
    assert queue["failures"][0]["failure_detail"] == (
        "[lane=fl2va] render failed for clip 1: WanGPError: WanGP queue completed "
        "with an unexpected task count 0/1; expected 1/1"
    )
    assert "H3 denoising: 100%|██████████| 20/20" in native_log
    assert 'TypeError: an integer is required' in native_log
    assert "Queue completed: 0/1 tasks" in native_log
    assert "settings_staging_boundary=CLEARED" in settings_probe


def test_v3_template_binds_exact_six_file_boundary() -> None:
    recorder = _load_recorder()
    authorization = _future_isolated_runtime_authorization()
    assert authorization["schema_version"] == "wangp-dspy.clean-generated-authorization/v3"
    files = authorization["authorized_source"]["files"]
    assert set(files) == {
        "install.sh", "scripts/record_clean_generated_proof.py", "scripts/verify_maestro_parity.py",
        "datasets/runs/maestro-parity/clean-generated/model-assets.json",
        "host/wangp_adapter.py", "host/render_host.py",
    }
    for relative in ("host/wangp_adapter.py", "host/render_host.py"):
        assert files[relative] == recorder.sha(ROOT / relative)
    with pytest.raises(recorder.ProofError, match="authorized source bytes differ"):
        recorder.validate_authorized_source(ROOT, authorization)


@pytest.mark.parametrize("relative", ["host/wangp_adapter.py", "host/render_host.py"])
@pytest.mark.parametrize("tamper", ["hash", "missing", "extra"])
def test_v3_rejects_transport_source_tampering(relative: str, tamper: str) -> None:
    recorder = _load_recorder()
    authorization = _future_isolated_runtime_authorization()
    files = authorization["authorized_source"]["files"]
    if tamper == "hash":
        files[relative] = "0" * 64
    elif tamper == "missing":
        del files[relative]
    else:
        files["unrelated.py"] = files[relative]
    # Even a self-consistent identity cannot authorize different bytes/file membership.
    authorization["authorized_source"]["identity_sha256"] = recorder.source_identity(files)
    with pytest.raises(recorder.ProofError) as caught:
        recorder.validate_authorized_source(ROOT, authorization)
    assert caught.value.code == "AUTHORIZED_SOURCE_INVALID"
    with pytest.raises(recorder.ProofError, match="authorization boundary mismatch"):
        recorder.inputs(authorization, recorder.load(BUNDLE / "model-assets.json"))


def test_v2_cannot_claim_v3_template_identity() -> None:
    recorder = _load_recorder()
    authorization = _future_isolated_runtime_authorization()
    authorization["schema_version"] = "wangp-dspy.clean-generated-authorization/v2"
    with pytest.raises(recorder.ProofError, match="v2 isolated authorization is retired") as caught:
        recorder.inputs(authorization, recorder.load(BUNDLE / "model-assets.json"))
    assert caught.value.code == "AUTHORIZATION_V2_RETIRED"
    with pytest.raises(recorder.ProofError, match="file set differs"):
        recorder.validate_authorized_source(ROOT, authorization)


def test_v2_mutated_consumed_authorization_is_retired(tmp_path: Path) -> None:
    recorder = _load_recorder()
    authorization = recorder.load(BUNDLE / "operator-authorization.isolated-runtime.retry3-20261008.json")
    # Changing the fingerprint must not bypass retirement of the consumed v2 boundary.
    authorization["text"] = "test-only historical v2 boundary"
    with pytest.raises(recorder.ProofError, match="v2 isolated authorization is retired") as caught:
        recorder.inputs(authorization, recorder.load(BUNDLE / "model-assets.json"))
    assert caught.value.code == "AUTHORIZATION_V2_RETIRED"
    # Historical source validation is separate from permission to run.
    _copy_retry3_historical_source(tmp_path)
    recorder.validate_authorized_source(tmp_path, authorization)


def test_queue_state_uses_actual_job_attempt_schema(tmp_path: Path) -> None:
    recorder = _load_recorder()
    database = tmp_path / "queue.db"
    queue = JobQueue(database)
    clip = {
        "clip_index": 0,
        "kind": "video_generation",
        "status": "pending",
        "prompt": "queue schema probe",
    }
    try:
        job_id = queue.submit(plan_ref="queue-schema-probe", clips=[clip])
        state = recorder.queue_state(database, job_id)
    finally:
        queue.close()

    assert state["attempts"] == []
    assert state["failures"] == []


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


@pytest.mark.parametrize("mode", ["success", "exception", "nonzero", "missing", "empty", "hash"])
def test_media_write_preflight_before_queue(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mode: str) -> None:
    recorder = _load_recorder()
    events: list[str] = []
    remote = tmp_path / "remote"
    remote.mkdir()
    proof = tmp_path / "proof"
    proof.mkdir()
    (proof / "argv.nul").write_bytes(b"install\0")
    config = {"remote_work_root": str(remote), "wgp_python": sys.executable,
              "pull_root": str(tmp_path), "target": "fake", "wgp_root": str(remote), "qc_url": "unused"}

    class Host:
        def push_file(self, source: str, target: str) -> str:
            events.append(Path(target).name)
            shutil.copyfile(source, target)
            return target

        def run_probe(self, argv: list[str], timeout: int = 120) -> tuple[int, str, str]:
            if argv[0] in {"mkdir", "chmod"}:
                process = subprocess.run(argv, capture_output=True, text=True, check=False)
                return process.returncode, process.stdout, process.stderr
            events.append("probe")
            assert argv == [str(remote / "media-write-python.sh"), str(remote / "media-write.py"), str(remote / "media-write.mp4")]
            assert (remote / "media-write-python.sh").read_text() == recorder.offline_wrapper_body(config)
            body = (remote / "media-write.py").read_text()
            assert "torchvision.io.write_video" in body and "torch.zeros((1, 8, 8, 3)" in body
            if mode == "exception":
                raise RuntimeError("transport failed")
            output = remote / "media-write.mp4"
            output.write_bytes(b"synthetic fixture bytes" if mode != "empty" else b"")
            versions = {key: "test-fixture" for key in ("python", "torch", "torchvision", "av")}
            out = json.dumps({"versions": versions}) + "\n" + json.dumps({
                "size_bytes": output.stat().st_size, "sha256": recorder.sha(output)}) + "\n"
            return (1 if mode == "nonzero" else 0), out, "TypeError: an integer is required" if mode == "nonzero" else ""

        def fetch_file(self, source: str, target: str) -> None:
            events.append("fetch")
            if mode != "missing":
                shutil.copyfile(source, target)
            if mode == "hash":
                Path(target).write_bytes(b"different fixture bytes")

    auth = tmp_path / "authorization.json"
    manifest = tmp_path / "manifest.json"
    recorder.record(auth, {"allowed_host": config})
    recorder.record(manifest, {})
    monkeypatch.setattr(recorder, "inputs", lambda auth, manifest: (auth, []))
    monkeypatch.setattr(recorder, "repository", lambda checkout: ("test", "", "test"))
    monkeypatch.setattr(recorder, "tools", lambda: {})
    monkeypatch.setattr(recorder, "validate_authorized_source", lambda *args: None)
    monkeypatch.setattr(recorder, "render_host", lambda config: Host())
    monkeypatch.setattr(recorder, "ensure_fresh_remote_root", lambda *args: None)
    monkeypatch.setattr(recorder, "relocate", lambda *args: events.append("storage"))
    monkeypatch.setattr(recorder, "models", lambda *args: events.append("models"))
    monkeypatch.setattr(recorder, "offline_wrapper", lambda *args: ("test", "test"))

    def submit(*args: Any, **kwargs: Any) -> None:
        events.append("queue-submit")
        raise RuntimeError("stop before any render")

    monkeypatch.setattr(JobQueue, "submit", submit)
    assert recorder.main(["--proof-dir", str(proof), "--checkout", str(tmp_path), "--installer", "unused",
                          "--authorization", str(auth), "--model-manifest", str(manifest)]) == 4
    result = recorder.load(proof / "preflight/media-write.json")
    assert result["log_sha256"] == recorder.sha(Path(result["log_path"]))
    assert events[:3] == ["media-write-python.sh", "media-write.py", "probe"]
    if mode == "success":
        assert result["passed"] and result["size_bytes"] > 0
        assert result["sha256"] == recorder.sha(Path(result["local_path"]))
        assert set(result["versions"]) == {"python", "torch", "torchvision", "av"}
        assert events[-3:] == ["storage", "models", "queue-submit"]
    else:
        assert not result["passed"]
        assert recorder.load(proof / "failure.json")["diagnostic"]["code"] == "MEDIA_WRITE_PREFLIGHT_FAILED"
        assert "queue-submit" not in events and "models" not in events
        assert not (proof / "queue.db").exists()


@pytest.mark.parametrize("fail_write", [False, True])
def test_media_write_script_executes_offline_with_fixture_runtime(tmp_path: Path, fail_write: bool) -> None:
    """Execute staged scripts locally; dependency fixtures are not real codec evidence."""
    recorder = _load_recorder()
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    (runtime / "torch.py").write_text('__version__ = "fixture-torch"\nuint8 = "uint8"\n'
                                       'def zeros(shape, dtype):\n    assert shape == (1, 8, 8, 3)\n    return shape\n')
    (runtime / "av.py").write_text('__version__ = "fixture-av"\n')
    action = 'raise TypeError("an integer is required")' if fail_write else 'Path(path).write_bytes(b"fixture-video")'
    (runtime / "torchvision.py").write_text(
        'import os\nfrom pathlib import Path\n__version__ = "fixture-torchvision"\nclass io:\n'
        '    @staticmethod\n    def write_video(path, frames, fps):\n'
        '        assert os.environ["HF_HUB_OFFLINE"] == os.environ["TRANSFORMERS_OFFLINE"] == "1"\n'
        '        assert fps == 24\n        ' + action + '\n')
    config = {"remote_work_root": str(tmp_path / "remote"), "wgp_python": sys.executable,
              "runtime": {"python": sys.executable, "pythonpath": [str(runtime)], "environment": {}}}
    recorder.record(tmp_path / "proof/inputs/resolved-host.json", config)

    class LocalHost:
        def push_file(self, source: str, target: str) -> str:
            shutil.copyfile(source, target)
            return target

        def fetch_file(self, source: str, target: str) -> None:
            shutil.copyfile(source, target)

        def run_probe(self, argv: list[str], timeout: int = 120) -> tuple[int, str, str]:
            process = subprocess.run(argv, capture_output=True, text=True, check=False, timeout=timeout)
            return process.returncode, process.stdout, process.stderr

    if fail_write:
        with pytest.raises(recorder.ProofError, match="TypeError: an integer is required"):
            recorder.media_write_preflight(LocalHost(), tmp_path / "proof", config)
    else:
        result = recorder.media_write_preflight(LocalHost(), tmp_path / "proof", config)
        assert result["passed"] and result["versions"]["av"] == "fixture-av"
