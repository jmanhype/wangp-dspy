"""Real-repository coverage for the final WD-t0il LTX-2.3 upscale bundle."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from scripts.build_wdt0il_ltx23_upscale_bundle import _copy_preserved, build_bundle
from scripts.verify_maestro_parity import verify_bundle


ROOT = Path(__file__).resolve().parents[1]
RAW = (
    ROOT
    / "datasets/runs/maestro-parity/ltx-dependency-terminalization"
    / "identity-capture-f654-20261011/ltx23-upscale"
)
BUNDLE = ROOT / "datasets/runs/maestro-parity/WD-t0il/ltx23-upscale"
RAW_FILES = (
    "operation-record.json",
    "settings.json",
    "native.log",
    "native-output/wd_osfm_create_post.mp4",
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_copy_preserved_rejects_symlink_redirects_and_exclusive_temp_names(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.bin"
    source.write_bytes(b"preserved-bytes")
    expected = digest(source)

    external_directory = tmp_path / "external-directory"
    external_directory.mkdir()
    parent_alias = tmp_path / "parent-alias"
    parent_alias.symlink_to(external_directory)
    redirected_destination = parent_alias / "nested.bin"
    try:
        _copy_preserved(source, redirected_destination, expected, tmp_path)
    except Exception as exc:
        assert "symlink" in str(exc)
    else:
        raise AssertionError("symlinked parent was accepted")
    assert not redirected_destination.exists()

    allowed = tmp_path / "allowed"
    allowed.mkdir()
    external_file = external_directory / "external-file.bin"
    external_file.write_bytes(b"original-external")
    destination = allowed / "target.bin"
    destination.symlink_to(external_file)
    try:
        _copy_preserved(source, destination, expected, allowed)
    except Exception as exc:
        assert "symlink" in str(exc)
    else:
        raise AssertionError("symlinked destination was accepted")
    assert external_file.read_bytes() == b"original-external"

    destination.unlink()
    stale_alias = allowed / ".target.bin.copy"
    stale_alias.symlink_to(external_file)
    _copy_preserved(source, destination, expected, allowed)
    assert destination.is_file() and not destination.is_symlink()
    assert destination.read_bytes() == b"preserved-bytes"
    assert external_file.read_bytes() == b"original-external"
    stale_alias.unlink()


def snapshot(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def test_final_bundle_rebuild_is_deterministic_and_checker_passes() -> None:
    summary = build_bundle(ROOT)
    once = snapshot(BUNDLE)
    rebuilt = build_bundle(ROOT)
    after = snapshot(BUNDLE)

    assert once == after
    assert rebuilt == summary
    assert summary["repository_commit"] == (
        "f6548f03528b058476367349a5f481614cfa35be"
    )
    assert summary["output_sha256"] == (
        "126144d844e08ca70398f818daeb598761a1670c970c5849213d2d02e2e6a8b9"
    )
    assert summary["native_log_sha256"] == (
        "50fa2d01710ce78713e5c9746594fde8b5598b932ff539f9d1a5930b5c35623a"
    )
    report = verify_bundle(BUNDLE)
    assert report.passed
    assert report.diagnostics == ()
    assert report.warnings == ()


def test_final_bundle_preserves_exact_f654_operation_bytes() -> None:
    evidence = json.loads((BUNDLE / "evidence.json").read_text(encoding="utf-8"))
    manifest = json.loads(
        (
            RAW.parent / "sha256-manifest.json"
        ).read_text(encoding="utf-8")
    )

    for relative in RAW_FILES:
        source = RAW / relative
        copied = BUNDLE / relative
        assert copied.read_bytes() == source.read_bytes()
        expected = manifest[f"ltx23-upscale/{relative}"]
        assert digest(copied) == expected["sha256"]
        assert copied.stat().st_size == expected["size_bytes"]

    assert evidence["command"] == json.loads(
        (RAW / "operation-record.json").read_text(encoding="utf-8")
    )["argv"]
    assert evidence["queue_attempt"]["native_log_sha256"] == {
        "native.log": "50fa2d01710ce78713e5c9746594fde8b5598b932ff539f9d1a5930b5c35623a"
    }
    assert evidence["runtime_notes"]["operation_attempt"] == 1
    assert evidence["runtime_notes"]["retry_attempted"] is False
    assert evidence["runtime_notes"]["model_downloads"] == 0


def test_final_bundle_model_provenance_is_exact_and_local() -> None:
    evidence = json.loads((BUNDLE / "evidence.json").read_text(encoding="utf-8"))
    models = {
        item["identity"]: item for item in evidence["model_provenance"]
    }

    assert set(models) == {
        "ltx-2.3-22b-dev_diffusion_model_quanto_int8.safetensors",
        "gemma-3-12b-it-qat-q4_0-unquantized_quanto_bf16_int8.safetensors",
        "ltx-2.3-22b-distilled-lora-384-1.1.safetensors",
        "ltx-2.3-22b-ic-lora-pixel-spatial-upscaler-x2-0.9.safetensors",
    }
    assert all(item["download_approved"] is True for item in models.values())
    assert all(item["preflight_hash_verified"] is True for item in models.values())
    assert all(item["downloaded_this_story"] is False for item in models.values())
    assert models[
        "ltx-2.3-22b-dev_diffusion_model_quanto_int8.safetensors"
    ]["sha256"] == (
        "5fc8d83656cdabf93b79bfb8799ee1c84c8270c59a49caccd4f8d1a27c77f6ec"
    )
    assert models[
        "ltx-2.3-22b-distilled-lora-384-1.1.safetensors"
    ]["authorization_trace"]["basis"] == (
        "operator_authorized_existing_asset"
    )
    assert models[
        "ltx-2.3-22b-ic-lora-pixel-spatial-upscaler-x2-0.9.safetensors"
    ]["authorization_trace"]["pointer"] == (
        "existing_assets[ltx-2.3-22b-ic-lora-pixel-spatial-upscaler-x2-0.9.safetensors]"
    )
