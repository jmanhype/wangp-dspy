from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from predict.model_assets import load_asset_manifest


ROOT = Path(__file__).resolve().parents[1]
RUN_DIR = ROOT / "datasets/runs/maestro-parity/ltx-dependency-terminalization"
AUDIT_DIR = RUN_DIR / "metadata-audit"
MODEL = AUDIT_DIR / "model.json"
TREE = AUDIT_DIR / "tree.json"
SUMMARY = AUDIT_DIR / "summary.json"
MANIFEST = RUN_DIR / "model-assets.json"


def _read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _assert_audit_consistency(
    summary: dict[str, Any], model: dict[str, Any], tree: list[dict[str, Any]]
) -> None:
    assert model["sha"] == summary["repository"]["revision"] == (
        "6aa898aea1d968febdd834dc29e1dbef35340aeb"
    )
    expected_paths = {item["path"] for item in summary["assets"]}
    tree_assets = {
        item["path"]: item for item in tree if item.get("path") in expected_paths
    }
    assert set(tree_assets) == expected_paths
    siblings = {item["rfilename"] for item in model["siblings"]}
    for audited in summary["assets"]:
        assert audited["path"] in siblings
        metadata = tree_assets[audited["path"]]
        assert audited["size_bytes"] == metadata["size"] == metadata["lfs"]["size"]
        assert audited["lfs_oid_actual_file_sha256"] == metadata["lfs"]["oid"]
        assert audited["xet_hash_not_file_sha256"] == metadata["xetHash"]
        assert audited["lfs_oid_actual_file_sha256"] != (
            audited["xet_hash_not_file_sha256"]
        )


def test_metadata_response_and_summary_hashes_are_exact() -> None:
    summary = _read(SUMMARY)
    assert _digest(MODEL) == summary["source_evidence"]["model_json"]["sha256"] == (
        "33fb1cde721375e7b391aa2189b711965364ac0dfa403a48407ab0e8d1604505"
    )
    assert _digest(TREE) == summary["source_evidence"]["tree_json"]["sha256"] == (
        "079d472c84a9fa68e29fab9a17896a079ea209f6c6bc8d3313a7601ee5e91baa"
    )
    assert MODEL.stat().st_size == summary["source_evidence"]["model_json"]["size_bytes"]
    assert TREE.stat().st_size == summary["source_evidence"]["tree_json"]["size_bytes"]
    _assert_audit_consistency(summary, _read(MODEL), _read(TREE))


def test_manifest_uses_lfs_oid_as_sha_and_xet_hash_separately() -> None:
    summary = _read(SUMMARY)
    audited = {item["id"]: item for item in summary["assets"]}
    manifest = _read(MANIFEST)

    assert manifest["source_revision"] == summary["repository"]["revision"]
    assert len(manifest["assets"]) == len(audited) == 5
    for asset in manifest["assets"]:
        metadata = audited[asset["id"]]
        assert asset["sha256"] == metadata["lfs_oid_actual_file_sha256"]
        assert asset["xet_hash"] == metadata["xet_hash_not_file_sha256"]
        assert asset["sha256"] != asset["xet_hash"]
    assert sum(item["size_bytes"] for item in manifest["assets"]) == 23_701_298_279
    parsed = load_asset_manifest(MANIFEST)
    assert parsed.source_revision == summary["repository"]["revision"]
    assert all(
        asset.sha256 != asset.xet_hash
        for asset in parsed.assets
    )


def test_ingredients_partial_is_reconciled_without_calling_xet_a_sha() -> None:
    summary = _read(SUMMARY)
    finding = summary["finding"]
    partial = finding["ingredients_partial"]

    assert finding["prior_manifest_values_were"] == "xetHash"
    assert finding["actual_file_sha256_field"] == "lfs.oid"
    assert finding["xet_hash_is_file_sha256"] is False
    assert partial["observed_sha256"] == (
        "515e4e139001ac6282357a5b35372e42e98b3affd5fcc886a52242abeed19559"
    )
    assert partial["observed_sha256_equals_lfs_oid"] is True
    assert summary["prior_download_boundary"] == {
        "declared_get_count": 1,
        "undeclared_url_effective_get_count": 1,
        "undeclared_reported_payload_bytes": 172_109,
        "source_hash_discrepancy_resolved_by_metadata": True,
        "undeclared_request_boundary_remains": True,
    }
    assert summary["retry_authorized"] is False


def test_metadata_summary_drift_fails_closed() -> None:
    summary = _read(SUMMARY)
    model = _read(MODEL)
    tree = _read(TREE)

    wrong_file_sha = deepcopy(summary)
    item = wrong_file_sha["assets"][0]
    item["lfs_oid_actual_file_sha256"] = item["xet_hash_not_file_sha256"]
    with pytest.raises(AssertionError):
        _assert_audit_consistency(wrong_file_sha, model, tree)

    wrong_size = deepcopy(summary)
    wrong_size["assets"][0]["size_bytes"] += 1
    with pytest.raises(AssertionError):
        _assert_audit_consistency(wrong_size, model, tree)
