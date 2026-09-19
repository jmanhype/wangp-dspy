import hashlib
import json
from pathlib import Path

from scripts.run_acceptance import (
    _load_bundle,
    _normalize_inputs,
    _premise,
)
from services.director.run import DirectorRun


ROOT = Path(__file__).resolve().parents[1]
BUNDLE_PATH = ROOT / (
    "assets/acceptance/lf003-v3/"
    "staging-two-cut-vibevoice-20260917.json")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_lf003_vibevoice_bundle_plans_two_grid_aligned_cuts(
        tmp_path, lf003_fixtures):
    bundle = _load_bundle(BUNDLE_PATH)
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
        durations_s=bundle["durations_s"],
        seed_override=bundle["seed"], emit_record=False)

    assert plan.run_id == "lf003-two-cut-vibevoice-20260917"
    assert [clip["audio_guide"] for clip in plan.clips] == inputs["audio"]
    assert all(clip["video_length"] == 56 for clip in plan.clips)
    assert all(clip["seed"] == 905 for clip in plan.clips)
    assert "golden_canary" not in bundle


def test_lf003_bundle_matches_vibevoice_report_and_style_anchor(
        lf003_fixtures):
    bundle = _load_bundle(BUNDLE_PATH)
    report_path = ROOT / bundle["vibevoice_provenance"]["report"]
    report = json.loads(report_path.read_text())

    assert report["status"] == "complete"
    assert report["completed_turn_count"] == 2
    for bundle_entry, report_turn in zip(
            bundle["media_manifest"]["audio"], report["turns"]):
        audio_path = ROOT / bundle_entry["path"]
        assert bundle_entry["speaker"] == report_turn["speaker"]
        assert _sha256(audio_path) == report_turn["prepared_sha256"]
        assert report_turn["whisper_gate"]["passed"] is True

    anchor = ROOT / bundle["media_manifest"]["plates"]["anchor"]
    assert _sha256(anchor) == bundle["premise"]["style_ref"]
