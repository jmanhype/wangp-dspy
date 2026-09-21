import json
import hashlib
from pathlib import Path
from types import SimpleNamespace

import pytest

from qc.audio_critic.av_sync_gate import (
    AVSyncGateError, RemoteSyncNetAVSyncJudge, run_av_sync_gate,
)
from qc.audio_critic.syncnet_runner import (
    CropResult, SYNCNET_METHOD, SYNCNET_MODEL_SHA256, aggregate_results,
)


@pytest.fixture(autouse=True)
def complete_render_host_config(monkeypatch, tmp_path):
    """Resolve the SyncNet interpreter from an explicit test host."""

    monkeypatch.setenv("WANGP_CONFIG", str(tmp_path / "absent-config.toml"))
    monkeypatch.setenv("WANGP_SSH_TARGET", "configured-alias")
    monkeypatch.setenv("WANGP_WGP_ROOT", "/configured/Wan2GP")
    monkeypatch.setenv("WANGP_PULL_ROOT", str(tmp_path / "pull"))


def _evidence(**overrides):
    payload = {
        "method": SYNCNET_METHOD,
        "model_sha256": SYNCNET_MODEL_SHA256,
        "offset_frames_25fps": 0,
        "offset_seconds": 0.0,
        "confidence": 2.0,
        "passed": True,
        "phonetic_sync_verified": False,
        "crop_results": [],
    }
    payload.update(overrides)
    return payload


def test_run_av_sync_gate_requires_passed_syncnet_evidence():
    evidence = run_av_sync_gate(
        "cut.mp4", speaker_mouth_bbox=[.2, .3, .1, .1],
        judge=lambda **_: _evidence())
    assert evidence["passed"] is True
    assert evidence["speaker_mouth_bbox"] == [.2, .3, .1, .1]


def test_run_av_sync_gate_preserves_rejection_evidence():
    rejected = _evidence(passed=False, confidence=.2)
    with pytest.raises(AVSyncGateError, match="SyncNet gate failed") as caught:
        run_av_sync_gate(
            "cut.mp4", speaker_mouth_bbox=[.2, .3, .1, .1],
            judge=lambda **_: rejected)
    assert caught.value.evidence["confidence"] == .2


@pytest.mark.parametrize("bbox", [
    [.2, .3, 0, .1], [.2, .3, .9, .1], [.2, .3, .1], [-.1, .3, .1, .1],
])
def test_run_av_sync_gate_rejects_invalid_bbox(bbox):
    with pytest.raises(AVSyncGateError, match="speaker_mouth_bbox"):
        run_av_sync_gate(
            "cut.mp4", speaker_mouth_bbox=bbox,
            judge=lambda **_: _evidence())


def test_syncnet_aggregate_uses_median_multicrop_result():
    evidence = aggregate_results([
        CropResult(4, -9, .9, 8), CropResult(8, -3, 1.3, 8),
        CropResult(12, -3, 1.4, 8),
    ])
    assert evidence["offset_frames_25fps"] == -3
    assert evidence["confidence"] == 1.3
    assert evidence["passed"] is True
    assert evidence["phonetic_sync_verified"] is False


def test_syncnet_aggregate_rejects_low_confidence():
    evidence = aggregate_results([
        CropResult(4, 3, .2, 10), CropResult(8, 8, .5, 10),
        CropResult(12, 10, .3, 10),
    ])
    assert evidence["passed"] is False


class _Host:
    def __init__(self, result=None):
        self.result = result or SimpleNamespace(
            returncode=0, stdout=json.dumps(_evidence(status="complete")),
            stderr="")
        self.calls = []
        self.pushed = []

    def map_path(self, path):
        return "/host/" + str(path).replace("\\", "/").lstrip("/")

    def makedirs(self, path):
        self.calls.append((["mkdir", "-p", path], None))

    def push_file(self, local, remote):
        self.pushed.append((local, remote))
        self.calls.append((["rsync", local, remote], None))
        return remote

    def run_argv(self, argv, *, cwd, timeout):
        self.calls.append((argv, cwd, timeout))
        return self.result


def test_remote_syncnet_dispatches_repo_module_through_host(tmp_path):
    host = _Host()
    video = tmp_path / "syncnet-video.mp4"
    video.write_bytes(b"exact-final-artifact")
    judge = RemoteSyncNetAVSyncJudge(
        host=host, model_path="/models/syncnet.model",
        host_python="/host/python", host_repo="/host/repo")
    evidence = judge(
        video_path=str(video),
        speaker_mouth_bbox=[.2, .3, .1, .1])
    argv, cwd, timeout = next(
        call for call in host.calls if call[0][:1] == ["/host/python"])
    assert argv[:3] == ["/host/python", "-m", "qc.audio_critic.syncnet_runner"]
    expected_remote = "/host" + str(video)
    assert argv[argv.index("--video") + 1] == expected_remote
    assert argv[argv.index("--model") + 1] == "/models/syncnet.model"
    assert len(argv[argv.index("--video-sha256") + 1]) == 64
    assert cwd == "/host/repo"
    assert timeout == judge.timeout_s
    assert evidence["method"] == SYNCNET_METHOD
    assert evidence["remote_video_path"] == expected_remote
    assert host.pushed == [(str(video), expected_remote)]


def test_remote_syncnet_failure_includes_bounded_process_output():
    host = _Host(SimpleNamespace(
        returncode=2, stdout="", stderr="torch unavailable"))
    video = Path("/tmp/wangp-syncnet-test-missing-final.mp4")
    video.write_bytes(b"exact-final-artifact")
    judge = RemoteSyncNetAVSyncJudge(host=host)
    with pytest.raises(AVSyncGateError, match="torch unavailable"):
        judge(video_path=str(video),
              speaker_mouth_bbox=[.2, .3, .1, .1])


def test_remote_syncnet_requires_exact_local_final_artifact(tmp_path):
    host = _Host()
    judge = RemoteSyncNetAVSyncJudge(host=host)
    with pytest.raises(AVSyncGateError, match="local SyncNet video"):
        judge(video_path=str(tmp_path / "missing.mp4"),
              speaker_mouth_bbox=[.2, .3, .1, .1])
    assert not host.pushed


def test_live_calibration_evidence_matches_preserved_artifacts(
        lf003_fixtures):
    root = Path(__file__).resolve().parents[1]
    payload = json.loads((root / (
        "datasets/runs/provenance/syncnet-calibration-20260918/"
        "evidence.json")).read_text())
    paths = {
        "v3-original-cut1": (
            "datasets/runs/provenance/v3-original/v3_c1.mp4"),
        "v3-original-cut2": (
            "datasets/runs/provenance/v3-original/v3_c2.mp4"),
        "lf002-nell": (
            "datasets/runs/pull/acceptance/worker-a08dc195c192/"
            "render-0001/remux.mp4"),
        "lf002-orin": (
            "datasets/runs/pull/acceptance/worker-0646f3fdb158/"
            "render-0004/remux.mp4"),
        "lf003-tess": (
            "datasets/runs/pull/acceptance/worker-94129b34bdd8/"
            "render-0000/remux.mp4"),
        "lf003-rho": (
            "datasets/runs/pull/acceptance/worker-4e52f8dc1fc7/"
            "render-0000/remux.mp4"),
    }
    for cut in payload["cuts"]:
        path = root / paths[cut["label"]]
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        assert digest == cut["artifact_sha256"]
    accepted = [cut for cut in payload["cuts"]
                if cut["operator_verdict"].casefold() == "perfect"]
    assert accepted and all(cut["passed"] for cut in accepted)
    assert next(
        cut for cut in payload["cuts"]
        if cut["label"] == "lf003-rho")["passed"] is False
