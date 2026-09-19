import hashlib
import json
import sqlite3
from pathlib import Path

from scripts.run_acceptance import _load_bundle, _normalize_inputs, _premise
from services.director.run import DirectorRun


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / (
    "datasets/runs/provenance/lf003-four-cut-fullgate-20260919/manifest.json")
RUN_ID = "lf003-four-cut-fullgate-20260919"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _content_records(value):
    if isinstance(value, dict):
        if isinstance(value.get("path"), str) and isinstance(
                value.get("sha256"), str):
            yield value
        for child in value.values():
            yield from _content_records(child)
    elif isinstance(value, list):
        for child in value:
            yield from _content_records(child)


def test_fourcut_bundle_plans_fresh_chained_cuts(tmp_path):
    bundle_path = ROOT / (
        "assets/acceptance/lf003-v3/"
        "staging-four-cut-vibevoice-fullgate-20260919.json")
    bundle = _load_bundle(bundle_path)
    assert "completed_prefix" not in bundle
    assert bundle["run_id"] == RUN_ID
    assert bundle["expected_cuts"] == 4
    assert bundle["seed"] == 906
    assert bundle["durations_s"] == [2.3333333333333335] * 4

    premise = _premise(bundle)
    inputs = _normalize_inputs(bundle, premise, root=ROOT)
    run = DirectorRun(
        run_id=bundle["run_id"], premise=premise,
        dataset_run_path=str(tmp_path / "runs.jsonl"))
    plan = run.plan(
        inputs["script"], audio_paths=inputs["audio"],
        plate_paths=inputs["plates"], media_manifest=inputs["media"],
        recipe_name=bundle["recipe_name"],
        expected_cuts=bundle["expected_cuts"],
        durations_s=bundle["durations_s"], seed_override=bundle["seed"],
        emit_record=False)

    assert [clip["speaker"] for clip in plan.clips] == [
        "Tess", "Rho", "Tess", "Rho"]
    assert [clip["seed"] for clip in plan.clips] == [906] * 4
    assert [clip["video_length"] for clip in plan.clips] == [56] * 4
    assert [clip["image_refs"][0] for clip in plan.clips] == [
        str(ROOT / "assets/acceptance/lf003-v3/anchor.png"),
        "chain://clip0001/last_frame",
        "chain://clip0002/last_frame",
        "chain://clip0003/last_frame",
    ]
def test_fourcut_manifest_records_clean_entry_and_terminal_cut3_failure():
    payload = json.loads(MANIFEST.read_text())
    assert payload["run_id"] == RUN_ID
    assert payload["status"] == "gate_failed_cut3"
    assert payload["operator_verdict"] == "not_requested"
    assert payload["no_completed_prefix"] is True
    assert payload["assembly"] is None
    identity = payload["execution_repository"]
    assert identity["commit_sha"] == (
        "35201a11bb1839fd5ba83739eed690227aabe199")
    assert identity["clean_tree"] is True
    assert identity["dirty_tree"] is False
    assert identity["changed_path_count"] == 0
    assert identity["untracked_path_count"] == 0
    assert payload["entry_acceptance"]["verbatim_operator_message"] == (
        "i agree to everything you may continue on all fronts")
    assert payload["entry_acceptance"]["accepted_assembled_sha256"] == (
        "1c1184fbcf504ffbc4657926e13d20c6dd039e41dc6c54bfe6e61919032b21ad")
    acceptance = json.loads((ROOT / (
        "datasets/runs/provenance/lf003-four-cut-fullgate-20260919/"
        "operator-acceptance.json")).read_text())
    prior = acceptance["prior_run"]
    assert prior["planned_record_line_sha256"] == (
        "4c08dfe429499fc38bd20d0e9796b4d4d9ae06c4cd417bc1748b3b8c3969e502")
    assert prior["needs_review_record_line_sha256"] == (
        "92180c776a820a58a3f725aa9e92308aba84f67c4dd1c1585853ba2537cbe996")
    assert len(prior["story_embedded_assembled_hash_text"]) == 63
    assert prior["story_embedded_hash_valid"] is False


def test_fourcut_manifest_artifacts_are_content_addressed():
    payload = json.loads(MANIFEST.read_text())
    records = list(_content_records(payload))
    assert len(records) >= 50
    for record in records:
        path = ROOT / record["path"]
        assert path.is_file(), record["path"]
        assert path.stat().st_size == record["bytes"], record["path"]
        assert _sha256(path) == record["sha256"], record["path"]


def test_fourcut_queue_ledger_and_cut_gates_fail_closed():
    payload = json.loads(MANIFEST.read_text())
    db = ROOT / payload["jobs_db"]["path"]
    connection = sqlite3.connect(db)
    try:
        rows = connection.execute(
            "select job_id,state,failure_count,failure_class,failure_detail "
            "from jobs order by created_at").fetchall()
    finally:
        connection.close()

    assert [row[1] for row in rows] == ["done", "done", "failed", "pending"]
    assert rows[2][3:] == (
        "qc_gate",
        "vision result must include three speaker_mouth_bboxes [x,y,w,h]")

    ledger_path = ROOT / payload["ledger"]["path"]
    lines = ledger_path.read_bytes().splitlines()
    records = [json.loads(line) for line in lines]
    assert [record["status"] for record in records] == [
        "planned", "gate_failed"]
    assert payload["ledger"]["line_sha256"] == [
        hashlib.sha256(line).hexdigest() for line in lines]

    cuts = payload["cuts"]
    assert cuts[0]["state"] == "done"
    assert cuts[0]["identity_vision_passed"] is True
    assert cuts[0]["syncnet_confidence"] >= 1.0
    assert cuts[1]["state"] == "done"
    assert cuts[1]["identity_vision_passed"] is True
    assert cuts[1]["syncnet_confidence"] >= 1.0
    assert cuts[2]["state"] == "failed"
    assert cuts[2]["whisper_pre"] == 1.0
    assert cuts[2]["whisper_post"] == 1.0
    assert cuts[2]["identity_vision_passed"] is None
    assert cuts[2]["mouth_boxes"] is None
    assert cuts[2]["syncnet_confidence"] is None
    assert cuts[3]["state"] == "pending"
    assert cuts[3]["artifacts"] == {}
