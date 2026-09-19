from pathlib import Path

from scripts.run_acceptance import _load_bundle, _normalize_inputs, _premise
from services.director.run import DirectorRun


ROOT = Path(__file__).resolve().parents[1]
BUNDLE_PATH = ROOT / (
    "assets/acceptance/lf003-v3/"
    "staging-two-cut-vibevoice-fullgate-20260918.json")


def test_fullgate_bundle_plans_two_fresh_chained_cuts(
        tmp_path, lf003_fixtures):
    bundle = _load_bundle(BUNDLE_PATH)
    assert "completed_prefix" not in bundle
    calibration = Path(
        bundle["vibevoice_provenance"]["syncnet_calibration"])
    assert calibration.is_relative_to(Path("datasets/runs/provenance"))
    assert (ROOT / calibration).is_file()

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

    assert plan.run_id == "lf003-two-cut-vibevoice-fullgate-20260918"
    assert [clip["seed"] for clip in plan.clips] == [906, 906]
    assert all(clip["video_length"] == 56 for clip in plan.clips)
    assert plan.clips[1]["image_refs"][0] == "chain://clip0001/last_frame"
    assert plan.clips[0]["audio_guide"].endswith("tess.prepared.wav")
    assert plan.clips[1]["audio_guide"].endswith("rho.prepared.wav")
