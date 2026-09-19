import hashlib
import json
from pathlib import Path

from scripts.run_acceptance import _load_bundle, _normalize_inputs, _premise
from services.director.run import DirectorRun


ROOT = Path(__file__).resolve().parents[1]
BUNDLE_PATH = ROOT / (
    "assets/acceptance/lf003-v3/"
    "staging-two-cut-vibevoice-rhostrong-20260918.json")


def test_rhostrong_bundle_uses_strong_fresh_vibevoice_guide():
    bundle = _load_bundle(BUNDLE_PATH)
    assert "completed_prefix" not in bundle
    rho = bundle["vibevoice_provenance"]["reports"][1]
    report = json.loads((ROOT / rho["report"]).read_text())
    turn = report["turns"][0]
    audio = ROOT / turn["prepared_path"]
    digest = hashlib.sha256(audio.read_bytes()).hexdigest()

    assert rho["generation_seed"] == 44
    assert rho["whisper_pass_bar"] == 0.8
    assert turn["whisper_gate"]["pass_bar"] == 0.8
    assert turn["whisper_gate"]["score"] == 0.833
    assert turn["prepared_sha256"] == digest == rho["prepared_sha256"]
    assert bundle["audio_paths"][1].endswith(
        "lf003-vibevoice-rho-strong-20260918/audio/rho.prepared.wav")


def test_rhostrong_bundle_plans_two_fresh_gated_cuts(tmp_path):
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

    assert plan.run_id == "lf003-two-cut-vibevoice-rhostrong-20260918"
    assert [clip["seed"] for clip in plan.clips] == [906, 906]
    assert plan.clips[1]["image_refs"][0] == "chain://clip0001/last_frame"
    assert all(clip["video_length"] == 56 for clip in plan.clips)
