import hashlib
import json

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


def test_report_cannot_overwrite_input(artifacts):
    with pytest.raises(lf002_canary.LF002CanaryError, match="overwrite"):
        lf002_canary.verify_lf002_canary(
            **artifacts, report_path=artifacts["pair"])
