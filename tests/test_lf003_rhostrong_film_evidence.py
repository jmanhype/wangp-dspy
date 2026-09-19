import hashlib
import json
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / (
    "datasets/runs/provenance/lf003-rhostrong-film-20260918/manifest.json")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_lf003_rhostrong_manifest_pins_assembly_and_both_cuts():
    payload = json.loads(MANIFEST.read_text())
    assert payload["execution_repository"]["commit_sha"] == (
        "8d865dc5aafce70c7162dda6e47d9f2686e2e09f")
    assert payload["execution_repository"]["clean_tree"] is True
    assert payload["status"] == "mechanically_eligible_final_candidate"
    assert payload["operator_verdict"] == "pending"

    for record in [payload["jobs_db"], payload["ledger"], *payload["cuts"],
                   payload["assembled"]]:
        path = ROOT / record.get("path", record.get("artifact"))
        assert path.is_file()
        assert _sha256(path) == record["sha256"]

    assert payload["assembled"]["frames"] == 112
    assert payload["assembled"]["duration_s"] == 4.666667
    assert [cut["whisper_pre"] for cut in payload["cuts"]] == [0.833, 0.833]
    assert [cut["whisper_post"] for cut in payload["cuts"]] == [0.833, 0.667]
    assert all(cut["syncnet_confidence"] >= 1.0 for cut in payload["cuts"])
    assert all(cut["syncnet_offset_frames_25fps"] == -1
               for cut in payload["cuts"])


def test_lf003_rhostrong_queue_and_qc_evidence_are_complete():
    payload = json.loads(MANIFEST.read_text())
    db = ROOT / payload["jobs_db"]["path"]
    connection = sqlite3.connect(db)
    try:
        rows = connection.execute(
            "select job_id,state,failure_count,clips from jobs "
            "order by created_at").fetchall()
    finally:
        connection.close()

    assert [row[1] for row in rows] == ["done", "done"]
    assert [row[2] for row in rows] == [0, 0]
    for row, expected in zip(rows, payload["cuts"]):
        assert row[0] == expected["job_id"]
        clip = json.loads(row[3])[0]
        assert clip["status"] == "done"
        evidence = json.loads(
            Path(clip["qc_verdict"]["path"].replace(
                "/private/tmp/wangp-dspy-rhostrong-8d865dc", str(ROOT)))
            .read_text())
        assert evidence["whisper_gates"]["pre"]["passed"] is True
        assert evidence["whisper_gates"]["post"]["passed"] is True
        assert evidence["vision_judge"]["passed"] is True
        assert evidence["av_sync_gate"]["passed"] is True
        assert evidence["av_sync_gate"]["phonetic_sync_verified"] is False
