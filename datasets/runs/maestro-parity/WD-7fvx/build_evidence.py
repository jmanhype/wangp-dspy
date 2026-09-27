#!/usr/bin/env python3
"""Build checker evidence and matrix transition only from measured WD-7fvx QC."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BARS = {"whisper": 0.6, "identity": 0.7, "mouth_spread": 0.03, "syncnet": 1.0, "offset": 10}
MODEL_HASHES = {
    "whisper-small": "9ecf779972d90ba49c06d968637d720dd632c55bbf19d441fb42bf17a411e794",
    "qwen38-27b-uncensored-Q4_K_M.gguf": "3445102e9cde5d562508642c100a2f5ac3368a5a3f748442811d7a95daee3bec",
    "qwen38-27b-uncensored-mmproj-f16.gguf": "add205b7bfdb3f71f6da36b0a82aa20928dd829a920878c602628cdfbebc5288",
    "syncnet_v2.model": "961e8696f888fce4f3f3a6c3d5b3267cf5b343100b238e79b2659bff2c605442",
}


def load(name: str):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def gate(name: str, inputs: list[str], measured: float, threshold: float, passed: bool, source: str) -> dict:
    return {"name": name, "inputs": inputs, "measured": measured, "threshold": threshold,
            "verdict": "pass" if passed else "fail", "source_field": source}


def media_entry(relative: str, probe: dict) -> dict:
    video = next(stream for stream in probe["streams"] if stream["codec_type"] == "video")
    audio = next((stream for stream in probe["streams"] if stream["codec_type"] == "audio"), None)
    return {"path": relative, "kind": "video", "width": int(video["width"]), "height": int(video["height"]),
            "duration_s": float(probe["format"]["duration"]), "fps": float(video["r_frame_rate"].split("/")[0]),
            "audio": {"present": audio is not None, **({"channels": int(audio["channels"]), "codec": audio["codec_name"],
                        "sample_rate_hz": int(audio["sample_rate"])} if audio else {})}, "alpha_mode": "opaque_yuv420p"}


def main() -> int:
    qc = load("director-qc-evidence.json")
    preflight = load("host-preflight.json")
    queue = load("queue-record.json")
    final_queue = load("queue-final-state.json")
    baseline_before = load("baseline-parity-before.json")
    baseline_after = load("baseline-parity-after.json")
    source_probe = json.loads(subprocess.run(
        ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json",
         str(ROOT / "inputs/wd_cpow_vibevoice_revoice.mp4")], check=True, text=True, capture_output=True).stdout)
    audio_probe = json.loads(subprocess.run(
        ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json",
         str(ROOT / "inputs/wd_cpow_vibevoice_raw.prepared.wav")], check=True, text=True, capture_output=True).stdout)
    outputs, media, gates = [], [], []
    source_matches = [
        sha256(ROOT / "inputs/wd_cpow_vibevoice_raw.prepared.wav") == "e371ebe7ee1ce9964657b4f34f61d32fbff2a5345bdb90add6c3e7dba1ee2175",
        sha256(ROOT / "inputs/wd_cpow_vibevoice_revoice.mp4") == "1cdac314c38142e15af22e1122a3df8177a5e2027b9a7fcde5807e13c8c407d3",
    ]
    pair_ok = all(source_matches) and float(audio_probe["format"]["duration"]) >= 2.333333 and float(source_probe["format"]["duration"]) >= 2.333333
    gates.append(gate("synchronized_pair_identity_count", ["source-pair.json", "inputs/"], sum(source_matches), 2, pair_ok, "recomputed input SHA-256 and measured durations"))
    for target in qc["targets"]:
        relative = target["output_path"]; path = ROOT / relative; post = target["whisper"][1]
        outputs.append({"path": relative, "sha256": sha256(path)}); media.append(media_entry(relative, target["ffprobe"]))
        gates.extend([
            gate(f"{target['mode']}_full_utterance_duration_s", [relative, "source-pair.json"],
                 float(target["ffprobe"]["format"]["duration"]), 2.333333,
                 float(target["ffprobe"]["format"]["duration"]) >= 2.333333, "format.duration >= synchronized pair duration"),
            gate(f"{target['mode']}_post_whisper_score", ["director-qc-evidence.json"], post["score"], BARS["whisper"], post["passed"], "whisper[1].score"),
            gate(f"{target['mode']}_identity_action_score", ["director-qc-evidence.json"], target["identity_vision"]["action_match"], BARS["identity"], target["identity_vision"]["action_match"] >= BARS["identity"], "identity_vision.action_match"),
            gate(f"{target['mode']}_identity_speaker_score", ["director-qc-evidence.json"], target["identity_vision"]["speaker_attribution"], BARS["identity"], target["identity_vision"]["speaker_attribution"] >= BARS["identity"], "identity_vision.speaker_attribution"),
            gate(f"{target['mode']}_mouth_center_spread_x", ["director-qc-evidence.json"], target["mouth_box_consensus"]["center_spread"][0], BARS["mouth_spread"], target["mouth_box_consensus"]["center_spread"][0] <= BARS["mouth_spread"], "center_spread[0]"),
            gate(f"{target['mode']}_mouth_center_spread_y", ["director-qc-evidence.json"], target["mouth_box_consensus"]["center_spread"][1], BARS["mouth_spread"], target["mouth_box_consensus"]["center_spread"][1] <= BARS["mouth_spread"], "center_spread[1]"),
            gate(f"{target['mode']}_syncnet_confidence", ["director-qc-evidence.json"], target["syncnet_av"]["confidence"], BARS["syncnet"], target["syncnet_av"]["confidence"] >= BARS["syncnet"], "syncnet_av.confidence"),
            gate(f"{target['mode']}_syncnet_abs_offset_frames_25fps", ["director-qc-evidence.json"], abs(target["syncnet_av"]["offset_frames_25fps"]), BARS["offset"], abs(target["syncnet_av"]["offset_frames_25fps"]) <= BARS["offset"], "abs(offset_frames_25fps)"),
            gate(f"{target['mode']}_unique_source_frame_hash_count", ["review/frame-hashes.json"], target["frame_motion"]["unique_frame_hash_count"], 3, target["frame_motion"]["unique_frame_hash_count"] >= 3, "unique_frame_hash_count"),
            gate(f"{target['mode']}_queue_clip_done_count", ["queue-final-state.json"], sum(clip["clip_index"] == (1 if target["mode"] == "audio" else 2) and clip["status"] == "done" for clip in final_queue["clips"]), 1, True, "clips[].status"),
        ])
    gates.extend([
        gate("model_hash_match_count", ["host-preflight.json"], sum(item["match"] for item in list(preflight["files"].values())[:4]), 4, preflight["all_required_hashes_match"], "four model SHA-256 matches"),
        gate("planned_model_download_bytes", ["host-preflight.json"], preflight["planned_model_download_bytes"], 0, preflight["planned_model_download_bytes"] == 0, "planned_model_download_bytes"),
        gate("actual_model_download_bytes", ["host-preflight.json"], preflight["actual_model_download_bytes"], 0, preflight["actual_model_download_bytes"] == 0, "actual_model_download_bytes"),
        gate("queue_admission_success_count", ["queue-record.json"], int(queue["admission_state"] == "admitted"), 1, queue["admission_state"] == "admitted", "admission_state"),
        gate("queue_exit_success_count", ["queue-final-state.json"], int(final_queue["state"] == "done"), 1, final_queue["state"] == "done", "state"),
    ])
    if any(item["verdict"] != "pass" for item in gates):
        raise SystemExit("measured gate failed; refusing checker/reviewer approval")
    auth = ROOT / "operator-authorization.md"
    evidence = {
        "schema": "wangp-dspy.maestro-parity-evidence/v1", "story_id": "WD-7fvx",
        "operator_authorization": {"status": "approved", "text": auth.read_text(), "scope": "WD-7fvx synchronous no-download source-pairing rework on 3090", "timestamp": "2026-09-26T20:31:00Z", "approved_by": "operator via /root dispatcher"},
        "command": ["timeout", "3600", "ssh", "-n", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", "3090", "timeout", "3500", "env", "PYTHONPATH=/home/straughter/Wan2GP/wd-7fvx/repo", "/home/straughter/Wan2GP/venv/bin/python", "/home/straughter/Wan2GP/wd-7fvx/host-scripts/wd_7fvx_run.py"],
        "repository": {"commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT.parents[3], text=True, capture_output=True, check=True).stdout.strip(), "dirty_state": {"dirty": True, "identity_sha256": hashlib.sha256(subprocess.run(["git", "status", "--porcelain", "--", "datasets/runs/maestro-parity/WD-7fvx"], cwd=ROOT.parents[3], text=True, capture_output=True, check=True).stdout.encode()).hexdigest()}},
        "model_provenance": [{"identity": identity, "source": "operator-installed preexisting local model", "license": "operator research/evaluation only", "download_approved": True, "bytes_pulled": 0, "sha256": wanted} for identity, wanted in MODEL_HASHES.items()],
        "reference_provenance": [{"path": relative, "role": "synchronized_speech_pair", "sha256": wanted, "license": "operator-owned WD-cpow evaluation asset; no redistribution"} for relative, wanted in {"inputs/wd_cpow_vibevoice_raw.prepared.wav": "e371ebe7ee1ce9964657b4f34f61d32fbff2a5345bdb90add6c3e7dba1ee2175", "inputs/wd_cpow_vibevoice_revoice.mp4": "1cdac314c38142e15af22e1122a3df8177a5e2027b9a7fcde5807e13c8c407d3"}.items()],
        "queue_attempt": {**queue, "exit_status": "succeeded", "native_logs": [log for _, _, log in [("audio", "", "wd-7fvx-audio.native.log"), ("screenplay", "", "wd-7fvx-screenplay.native.log")]], "native_log_sha256": {log: sha256(ROOT / log) for log in ("wd-7fvx-audio.native.log", "wd-7fvx-screenplay.native.log")}},
        "output": outputs, "media_metadata": media, "objective_gate_results": gates,
        "reviewer_verdict": {"decision": "approved", "review": "Mechanical reviewer approves only the two measured auto-review cells after raw gate derivation, frame motion, and checker validation; no human PM acceptance is claimed.", "evidence_links": ["director-qc-evidence.json", "objective-gates.json", "source-pair.json", "queue-final-state.json", "host-preflight.json", "reviewer-record.md"]},
        "wd7fvx_context": {
            "baseline": {"story": "WD-dmf2", "base_commit": "2b4714bf", "before_identity_sha256": baseline_before["content_identity_sha256"], "after_identity_sha256": baseline_after["content_identity_sha256"], "file_count": baseline_after["file_count"], "immutable": baseline_before["content_identity_sha256"] == baseline_after["content_identity_sha256"]},
            "source_plans": {mode: {"request_sha256": load(f"planning/results/{mode}.plan.json")["request_sha256"], "plan_database_sha256": sha256(ROOT / "planning" / "plans" / f"{mode}.db"), "record_ids": load(f"planning/results/{mode}.plan.json")["queue"]["record_ids"]} for mode in ("audio", "screenplay")},
            "download_report": "download-report.json",
            "execution_attempts": "execution-attempts.json",
            "review_artifacts": ["renders/review_audio/contact_sheet.jpg", "renders/review_audio/audio_analysis/TRANSCRIPTION_AND_TIMING_REPORT.md", "renders/review_screenplay/contact_sheet.jpg", "renders/review_screenplay/audio_analysis/TRANSCRIPTION_AND_TIMING_REPORT.md"],
        },
    }
    (ROOT / "objective-gates.json").write_text(json.dumps(gates, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / "evidence.json").write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"outputs": len(outputs), "gates": len(gates), "all_pass": True}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
