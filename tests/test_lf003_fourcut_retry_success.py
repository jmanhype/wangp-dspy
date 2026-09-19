import hashlib
import json
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUN_ID = "lf003-four-cut-fullgate-retry-20260919"
MANIFEST = ROOT / f"datasets/runs/provenance/{RUN_ID}/manifest.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _content_records(value):
    if isinstance(value, dict):
        if isinstance(value.get("path"), str) and isinstance(value.get("sha256"), str):
            yield value
        for child in value.values():
            yield from _content_records(child)
    elif isinstance(value, list):
        for child in value:
            yield from _content_records(child)


def test_retry_manifest_declares_full_gate_success_and_pending_operator_review():
    payload = json.loads(MANIFEST.read_text())
    assert payload["run_id"] == RUN_ID
    assert payload["status"] == "mechanically_eligible_operator_review_pending"
    assert payload["operator_verdict"] == "not_requested"
    assert payload["no_completed_prefix"] is True
    assert payload["threshold_changes"] == []
    identity = payload["execution_repository"]
    assert identity["commit_sha"] == "52654ff6bda49a931863f27bc9396be9b3e4d39e"
    assert identity["clean_tree"] is True and identity["untracked_path_count"] == 0
    assert payload["bundle"]["sha256"] == (
        "2ecf63deae1da43d9d865996946b082b3a6968d1fbf0ba30ab6bbdf3a122ce28"
    )


def test_retry_manifest_artifacts_are_content_addressed():
    payload = json.loads(MANIFEST.read_text())
    records = list(_content_records(payload))
    assert len(records) >= 85
    for artifact in records:
        path = ROOT / artifact["path"]
        assert path.is_file(), artifact["path"]
        assert path.stat().st_size == artifact["bytes"], artifact["path"]
        assert _sha256(path) == artifact["sha256"], artifact["path"]


def test_retry_queue_ledger_and_every_cut_passed_all_gates():
    payload = json.loads(MANIFEST.read_text())
    connection = sqlite3.connect(ROOT / payload["jobs_db"]["path"])
    try:
        rows = connection.execute(
            "select state,failure_count,failure_class,clips from jobs order by created_at"
        ).fetchall()
    finally:
        connection.close()

    assert [row[0] for row in rows] == ["done"] * 4
    assert [row[1] for row in rows] == [0, 1, 0, 1]
    assert [row[2] for row in rows] == [None, "qc_gate", None, "qc_gate"]
    assert [json.loads(row[3])[0]["seed"] for row in rows] == [906, 907, 906, 907]

    lines = (ROOT / payload["ledger"]["path"]).read_bytes().splitlines()
    assert [json.loads(line)["status"] for line in lines] == [
        "planned", "needs_review"]
    assert payload["ledger"]["line_sha256"] == [
        hashlib.sha256(line).hexdigest() for line in lines]

    expected = [
        (1, 0.833, 0.833, 0.9, 0.95, 3.199512),
        (2, 0.833, 0.833, 0.9, 0.95, 1.885130),
        (3, 1.0, 1.0, 0.95, 0.95, 3.395669),
        (4, 0.833, 0.667, 0.9, 0.95, 4.623250),
    ]
    for cut, whisper_pre, whisper_post, action, speaker, syncnet in expected:
        item = payload["cuts"][cut - 1]
        assert item["state"] == "done" and item["identity_vision_passed"] is True
        assert item["whisper_pre"] == whisper_pre and item["whisper_post"] == whisper_post
        assert item["vision_action"] == action and item["vision_speaker"] == speaker
        assert len(item["mouth_boxes"]) == 3 and item["syncnet_passed"] is True
        assert item["syncnet_confidence"] == syncnet


def test_both_governed_rejections_are_preserved():
    payload = json.loads(MANIFEST.read_text())
    rejections = payload["rejected_attempts"]
    assert set(rejections) == {
        "datasets/runs/pull/acceptance/worker-56d7f6cd7b8a/render-0001/remux.mp4",
        "datasets/runs/pull/acceptance/worker-743819fad2a8/render-0004/remux.mp4",
    }
    assert rejections[
        "datasets/runs/pull/acceptance/worker-56d7f6cd7b8a/render-0001/remux.mp4"
    ]["gate"] == "SyncNet"
    assert rejections[
        "datasets/runs/pull/acceptance/worker-743819fad2a8/render-0004/remux.mp4"
    ]["gate"] == "post-Whisper"
    assert len(payload["rejected_attempt_artifacts"]) == 20


def test_retry_assembly_and_review_metadata():
    payload = json.loads(MANIFEST.read_text())
    assembled = payload["assembled"]
    assert assembled["sha256"] == (
        "5a8676922d16c954d579c096c5eb9891ce33758ef1ebda27e98f03c632422063"
    )
    assert assembled["duration_s"] == 9.333333
    assert assembled["frames"] == 224
    assert assembled["resolution"] == [704, 576]
    assert assembled["fps"] == "24/1"
    assert assembled["audio_codec"] == "aac"
