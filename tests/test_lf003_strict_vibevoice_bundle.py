import hashlib
import json
from pathlib import Path

from qc.audio_critic.whisper_gate import DEFAULT_WHISPER_PASS_BAR
from scripts.run_acceptance import (
    _load_bundle, _normalize_inputs, _premise, _prepare_completed_prefix,
)
from services.director.run import DirectorRun
from tests.lf003_fixtures import stage_lf003_jobs_db


ROOT = Path(__file__).resolve().parents[1]
BUNDLE_PATH = ROOT / (
    "assets/acceptance/lf003-v3/"
    "staging-two-cut-vibevoice-strict-20260917.json")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_strict_bundle_audio_meets_production_whisper_bar():
    bundle = _load_bundle(BUNDLE_PATH)
    entries = bundle["vibevoice_provenance"]["reports"]
    assert [entry["speaker"] for entry in entries] == ["Tess", "Rho"]

    for entry in entries:
        report = json.loads((ROOT / entry["report"]).read_text())
        turn = next(
            item for item in report["turns"]
            if item["speaker"] == entry["speaker"])
        audio = ROOT / turn["prepared_path"]
        assert _sha256(audio) == entry["prepared_sha256"]
        assert _sha256(audio) == turn["prepared_sha256"]
        assert turn["whisper_gate"]["passed"] is True
        assert turn["whisper_gate"]["score"] >= DEFAULT_WHISPER_PASS_BAR

    rho_entry = entries[1]
    assert rho_entry["whisper_pass_bar"] == DEFAULT_WHISPER_PASS_BAR
    assert rho_entry["whisper_score"] >= DEFAULT_WHISPER_PASS_BAR


def test_strict_bundle_plans_and_adopts_completed_tess_prefix(
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
    staged_prefix = stage_lf003_jobs_db(
        tmp_path / "lf003-two-cut-vibevoice-20260917.jobs.db",
        fixtures=lf003_fixtures)
    prefix = {**bundle["completed_prefix"], **staged_prefix}
    completed = _prepare_completed_prefix(plan, prefix, root=ROOT)

    assert plan.run_id == "lf003-two-cut-vibevoice-strict-20260917"
    assert [clip["seed"] for clip in plan.clips] == [906, 906]
    assert all(clip["video_length"] == 56 for clip in plan.clips)
    assert plan.clips[0]["audio_guide"].endswith("tess.prepared.wav")
    assert plan.clips[1]["audio_guide"].endswith("rho.prepared.wav")
    assert completed["status"] == "done"
    assert completed["completed_prefix_source"]["sha256"] == (
        bundle["completed_prefix"]["expected_sha256"])
