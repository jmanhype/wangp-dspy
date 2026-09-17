import hashlib
import json
from pathlib import Path

from scripts.run_acceptance import (
    _load_bundle,
    _normalize_inputs,
    _premise,
)
from services.director.run import DirectorRun
from predict.audio_dataplane import AudioGuideProvenance
from predict.ref2va_settings import ref2va_wire_settings
from predict.render_profiles import Ref2VAProfile


ROOT = Path(__file__).resolve().parents[1]
BUNDLE_PATH = ROOT / (
    "assets/lf002-two-cut-20260913/"
    "staging-two-cut-vibevoice-20260917.json")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_vibevoice_bundle_plans_with_preserved_turn_audio(tmp_path):
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

    assert plan.run_id == "lf002-two-cut-vibevoice-20260917"
    assert [clip["audio_guide"] for clip in plan.clips] == inputs["audio"]
    assert [clip["seed"] for clip in plan.clips] == [905, 905]
    assert all(clip["video_length"] == 56 for clip in plan.clips)
    assert "golden_canary" not in bundle


def test_vibevoice_bundle_matches_verified_ref2va_backend_contract(tmp_path):
    from predict.prompt_director import RenderBrief
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
    first = plan.clips[0]
    raw_provenance = dict(first["audio_provenance"])
    raw_provenance["keeper_window_s"] = tuple(
        raw_provenance["keeper_window_s"])
    provenance = AudioGuideProvenance(**raw_provenance)
    settings = Ref2VAProfile().build_settings(
        [RenderBrief(
            subject=first["speaker"], motion="speaks in sync with audio",
            camera="static medium shot", style="cinematic")],
        None,
        image_refs=first["image_refs"], image_start=first["image_start"],
        audio_guide=first["audio_guide"], audio_prompt_type="A",
        guide_duration_s=56 / 24, shot_duration_s=56 / 24,
        audio_provenance=provenance, continuation=True, profile=2,
        recipe_name="golden_v3", legacy_prompt=first["prompt"], seed=905)
    wire = ref2va_wire_settings(settings)
    assert wire["image_prompt_type"] == "S"
    assert wire["image_start"] == first["image_start"] == first["image_refs"][0]
    assert wire["video_length"] == 56

    # Both cuts of the operator-accepted LF002 control already completed with
    # this exact backend contract: materialized image_start, 56 frames, and a
    # probed guide duration above the profile's two-second floor.
    golden_settings = sorted((
        ROOT / "datasets/runs/provenance/lf002-golden-20260916/"
        "single-ledger-20260916").glob("render-*/settings.json"))
    assert len(golden_settings) == 2
    for settings_path in golden_settings:
        verified = json.loads(settings_path.read_text())
        wire = ref2va_wire_settings(verified)
        assert wire["image_start"] == wire["image_refs"][0]
        assert wire["video_length"] == 56
        assert verified["guide_duration_s"] >= 2.0


def test_vibevoice_bundle_matches_hashed_complete_report():
    bundle = _load_bundle(BUNDLE_PATH)
    evidence_path = ROOT / bundle["vibevoice_provenance"]["evidence"]
    report_path = ROOT / bundle["vibevoice_provenance"]["report"]
    evidence = json.loads(evidence_path.read_text())
    report = json.loads(report_path.read_text())

    assert evidence["status"] == "complete"
    assert report["status"] == "complete"
    assert report["completed_turn_count"] == 2
    for bundle_entry, evidence_turn, report_turn in zip(
            bundle["media_manifest"]["audio"], evidence["turns"],
            report["turns"]):
        audio_path = ROOT / bundle_entry["path"]
        assert bundle_entry["speaker"] == evidence_turn["speaker"]
        assert bundle_entry["speaker"] == report_turn["speaker"]
        assert _sha256(audio_path) == evidence_turn["prepared_sha256"]
        assert _sha256(audio_path) == report_turn["prepared_sha256"]
        assert report_turn["whisper_gate"]["passed"] is True
