import hashlib
import json
from pathlib import Path

import pytest

from predict import lf002_canary


@pytest.fixture
def artifacts(tmp_path):
    paths = {}
    for key in ("cut1", "cut2", "pair", "chain"):
        paths[key] = tmp_path / key
        paths[key].write_bytes(key.encode())
    return paths


def test_production_hashes_are_operator_accepted_lf002_artifacts():
    assert lf002_canary.LF002_GOLDEN_SHA256 == {
        "cut1": "64916cd42d40e0f81a51dd750d2134d194dd59c8318bf3d6f75fbc8649d97770",
        "cut2": "c3131c041a2b586e15ab19280a0ede64aa294b2e6bdc9f26fde0e353fbc29ceb",
        "pair": "ef4c3944ef728862119b065838ac1ec5f1e1452d1f8b4fdbb0d683f06272a527",
        "chain": "1c1d86b0108c31a8318d428fcf626d3af6ffd0c0ba6269a8a69859eca6fb53de",
    }


def test_wrong_hash_fails_without_probe(monkeypatch, artifacts, tmp_path):
    monkeypatch.setattr(
        lf002_canary, "_probe",
        lambda _path: pytest.fail("wrong bytes must not be probed"))
    report = tmp_path / "report.json"
    with pytest.raises(lf002_canary.LF002CanaryError, match="SHA256 mismatch"):
        lf002_canary.verify_lf002_canary(**artifacts, report_path=report)
    evidence = json.loads(report.read_text())
    assert evidence["passed"] is False
    assert len(evidence["errors"]) == 4


def test_matching_artifacts_and_streams_pass(monkeypatch, artifacts, tmp_path):
    monkeypatch.setattr(
        lf002_canary, "LF002_GOLDEN_SHA256",
        {key: hashlib.sha256(path.read_bytes()).hexdigest()
         for key, path in artifacts.items()})

    def streams(path):
        return [
            {"codec_type": "video", "nb_read_frames":
                "112" if path.name == "pair" else "56",
             "r_frame_rate": "24/1", "start_time": "0.000000"},
            {"codec_type": "audio", "start_time": "0.000000"},
        ]

    monkeypatch.setattr(lf002_canary, "_probe", streams)
    report = tmp_path / "report.json"
    result = lf002_canary.verify_lf002_canary(
        **artifacts, report_path=report)
    assert result["passed"] is True
    assert result["operator_verdict"] == "perfect"
    assert all(result["artifacts"][key]["path"] == str(path)
               for key, path in artifacts.items())


def test_report_cannot_overwrite_input(artifacts):
    with pytest.raises(lf002_canary.LF002CanaryError, match="overwrite"):
        lf002_canary.verify_lf002_canary(
            **artifacts, report_path=artifacts["pair"])


def test_report_filesystem_failure_is_typed(tmp_path):
    blocker = tmp_path / "blocker"
    blocker.write_text("not a directory")
    report = blocker / "nested" / "report.json"
    with pytest.raises(
            lf002_canary.LF002CanaryError, match="write LF002 canary report"):
        lf002_canary.verify_lf002_canary(
            cut1="cut1.mp4", cut2="cut2.mp4", pair="pair.mp4",
            chain="chain.png", report_path=report)


def test_published_lf002_provenance_is_reproducible_and_complete():
    root = Path(__file__).resolve().parents[1]
    asset_dir = root / "assets" / "lf002-two-cut-20260913"
    provenance = (
        root / "datasets" / "runs" / "provenance" /
        "lf002-golden-20260916")
    scene = json.loads((asset_dir / "scene-preparation.json").read_text())
    bundle_name = scene["staging_bundle"]
    assert (asset_dir / bundle_name).is_file()
    bundle = json.loads((asset_dir / bundle_name).read_text())
    assert bundle["golden_canary"]["recipe_version"] == (
        lf002_canary.LF002_RECIPE_VERSION)
    canary = json.loads((provenance / "canary.json").read_text())
    assert canary["passed"] is True
    assert all(not Path(value["path"]).is_absolute()
               for value in canary["artifacts"].values())
