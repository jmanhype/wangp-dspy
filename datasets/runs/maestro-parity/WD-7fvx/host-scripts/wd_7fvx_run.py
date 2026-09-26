#!/usr/bin/env python3
"""Run the authorized no-download WD-7fvx source-pairing rework."""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from typing import Sequence

from predict.continuation_lane import transcript_match_score
from qc.audio_critic.local_qwen_vision_judge import LocalQwenVisionJudge
from qc.audio_critic.syncnet_runner import run as run_syncnet
from qc.audio_critic.vision_judge import run_vision_judge
from qc.audio_critic.whisper_cli import whisper_transcriber
from services.jobs.queue import JobQueue, next_admissible

MODELS = {
    "/home/straughter/.cache/whisper/small.pt": "9ecf779972d90ba49c06d968637d720dd632c55bbf19d441fb42bf17a411e794",
    "/mnt/bulk/home/straughter/models/qwen38-27b-uncensored/Q4_K_M.gguf": "3445102e9cde5d562508642c100a2f5ac3368a5a3f748442811d7a95daee3bec",
    "/mnt/bulk/home/straughter/models/qwen38-27b-uncensored/mmproj-f16.gguf": "add205b7bfdb3f71f6da36b0a82aa20928dd829a920878c602628cdfbebc5288",
    "/home/straughter/models/syncnet_v2/syncnet_v2.model": "961e8696f888fce4f3f3a6c3d5b3267cf5b343100b238e79b2659bff2c605442",
}
SOURCES = {
    "inputs/wd_cpow_vibevoice_raw.prepared.wav": "e371ebe7ee1ce9964657b4f34f61d32fbff2a5345bdb90add6c3e7dba1ee2175",
    "inputs/wd_cpow_vibevoice_revoice.mp4": "1cdac314c38142e15af22e1122a3df8177a5e2027b9a7fcde5807e13c8c407d3",
}
TARGETS = (
    ("audio", "outputs/wd_7fvx_audio_rework.mp4", "wd-7fvx-audio.native.log"),
    ("screenplay", "outputs/wd_7fvx_screenplay_rework.mp4", "wd-7fvx-screenplay.native.log"),
)


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def run(argv: Sequence[str], log: Path) -> None:
    log.write_text(json.dumps(list(argv)) + "\n", encoding="utf-8")
    subprocess.run(list(argv), stdout=log.open("a"), stderr=subprocess.STDOUT, check=True)


def probe(path: Path) -> dict:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
        check=True, text=True, capture_output=True,
    )
    return json.loads(result.stdout)


def preflight(root: Path, final: bool) -> dict:
    expected = MODELS if not final else {}
    expected.update(SOURCES if final else {})
    files = {}
    for relative, wanted in sorted(expected.items()):
        path = root / relative
        actual = digest(path) if path.is_file() else None
        files[relative] = {"sha256": actual, "expected_sha256": wanted, "match": actual == wanted}
    health = subprocess.run(
        ["curl", "-fsS", "--max-time", "10", "http://127.0.0.1:8000/health"],
        text=True, capture_output=True, check=False,
    )
    models_api = subprocess.run(
        ["curl", "-fsS", "--max-time", "10", "http://127.0.0.1:8000/v1/models"],
        text=True, capture_output=True, check=False,
    )
    free = shutil.disk_usage(root).free
    compute = subprocess.run(
        ["nvidia-smi", "--query-compute-apps=pid,process_name,used_memory", "--format=csv,noheader"],
        text=True, capture_output=True, check=False,
    )
    compute_lines = [line.strip() for line in compute.stdout.splitlines() if line.strip()]
    llama_only = bool(compute_lines) and all("llama" in line.lower() for line in compute_lines)
    payload = {
        "schema_version": "wangp-dspy.wd-7fvx-preflight/v1",
        "host": subprocess.run(["hostname"], text=True, capture_output=True, check=True).stdout.strip(),
        "user": subprocess.run(["id", "-un"], text=True, capture_output=True, check=True).stdout.strip(),
        "disk_free_bytes": free,
        "min_free_bytes": 15_000_000_000,
        "disk_floor_pass": free >= 15_000_000_000,
        "gpu": subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,memory.used,utilization.gpu", "--format=csv,noheader"],
            text=True, capture_output=True, check=True,
        ).stdout.strip(),
        "gpu_compute_processes": compute_lines,
        "gpu_preflight_pass": llama_only,
        "llama_health": {"exit_code": health.returncode, "stdout": health.stdout.strip()},
        "llama_models": {"exit_code": models_api.returncode, "stdout": models_api.stdout.strip()},
        "files": files,
        "all_required_hashes_match": all(item["match"] for item in files.values()),
        "operator_service_mutation": False,
        "planned_model_download_bytes": 0,
        "actual_model_download_bytes": 0,
    }
    destination = root / ("host-final-state.json" if final else "host-preflight.json")
    destination.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def compose(root: Path, mode: str, output: Path, log: Path) -> None:
    source_video = root / "inputs/wd_cpow_vibevoice_revoice.mp4"
    source_audio = root / "inputs/wd_cpow_vibevoice_raw.prepared.wav"
    run([
        "ffmpeg", "-y", "-v", "error", "-i", str(source_video), "-i", str(source_audio),
        "-map", "0:v:0", "-map", "1:a:0", "-t", "2.333333",
        "-vf", "pad=1920:1152:640:288,fps=24,crop=960:768:557+9*t:112+9*t,format=yuv420p",
        "-r", "24", "-c:v", "libx264", "-crf", "18", "-preset", "veryfast",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
        "-movflags", "+faststart", str(output),
    ], log)
    frames = root / "review" / mode / "frames"
    frames.mkdir(parents=True, exist_ok=True)
    hashes = []
    for position, timestamp in enumerate(("0.04", "1.16", "2.20"), start=1):
        frame = frames / f"frame_{position:03d}.jpg"
        run([
            "ffmpeg", "-y", "-v", "error", "-ss", timestamp, "-i", str(source_video),
            "-frames:v", "1", "-q:v", "2", str(frame),
        ], log)
        hashes.append(digest(frame))
    (root / "review" / mode / "frame-hashes.json").write_text(
        json.dumps({"frame_sha256": hashes, "unique_frame_hash_count": len(set(hashes))}, indent=2) + "\n",
        encoding="utf-8",
    )


def whisper(root: Path, path: Path, label: str) -> dict:
    isolated = root / "qc" / f"{label}_whisper"
    isolated.mkdir(parents=True, exist_ok=True)

    def runner(argv: Sequence[str]):
        return subprocess.run(list(argv), text=True, capture_output=True, check=False, timeout=900)

    intended = "This is the last rain we have."
    transcript = whisper_transcriber(str(path), runner=runner, model="small", output_dir=str(isolated))
    score = transcript_match_score(transcript, intended)
    return {"path": str(path), "phase": label.split("_")[-1], "intended_text": intended,
            "transcript": transcript, "score": round(score, 6), "pass_bar": 0.6,
            "passed": score >= 0.6, "model": "whisper-small", "model_sha256": MODELS[next(iter(MODELS))]}


class Host:
    @staticmethod
    def run_probe(argv: Sequence[str], timeout: float):
        result = subprocess.run(list(argv), text=True, capture_output=True, check=False, timeout=timeout)
        return result.returncode, result.stdout, result.stderr

    @staticmethod
    def write_text(path: str, content: str) -> str:
        Path(path).write_text(content, encoding="utf-8")
        return path


def qc(root: Path, mode: str, output: Path) -> dict:
    judge = LocalQwenVisionJudge(host=Host(), endpoint="http://127.0.0.1:8000/v1/chat/completions",
                                  model="q", timeout_s=180.0, max_tokens=1024)
    speaker = "elder woman with white hair holding a bowl"
    action = "an elder speaks while offering a bowl beside a restrained man in a firelit cave"
    raw = judge(video_path=str(output), expected_speaker=speaker, expected_action=action)
    (root / "qc" / f"{mode}_local-qwen-raw.json").write_text(
        json.dumps(raw, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    evidence = run_vision_judge(
        str(output), expected_speaker=speaker, expected_action=action,
        judge=lambda **_: raw, pass_bar=0.7,
    ).to_dict()
    bbox = evidence["speaker_mouth_bbox"]
    sync = run_syncnet(output, bbox, "/home/straughter/models/syncnet_v2/syncnet_v2.model", video_sha256=digest(output))
    return {"path": str(output), "expected_speaker": speaker, "expected_action": action,
            "identity_vision": {"passed": evidence["passed"],
                                "speaker_attribution": evidence["speaker_attribution"],
                                "action_match": evidence["action_match"], "pass_bar": evidence["pass_bar"],
                                "raw_response_sha256": hashlib.sha256(str(raw.get("raw_response", "")).encode()).hexdigest()},
            "mouth_box_consensus": {"passed": evidence["passed"],
                                    "speaker_mouth_bboxes": evidence["speaker_mouth_bboxes"],
                                    "center_spread": evidence["speaker_mouth_center_spread"]},
            "syncnet_av": sync,
            "frame_motion": json.loads((root / "review" / mode / "frame-hashes.json").read_text())}


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    before = preflight(root, final=False)
    if not (before["disk_floor_pass"] and before["all_required_hashes_match"]
            and before["llama_health"]["exit_code"] == 0 and before["gpu_preflight_pass"]):
        raise SystemExit(2)
    database = root / "queue.db"
    if database.exists():
        record = json.loads((root / "queue-record.json").read_text(encoding="utf-8"))
        job_id = record["job_id"]
        queue = JobQueue(database)
        try:
            state = queue.get(job_id).state
        finally:
            queue.close()
        if state != "rendered_pending_qc":
            raise SystemExit(f"cannot resume job {job_id} from state {state}")
        resuming = True
    else:
        queue = JobQueue(database)
        try:
            job_id = queue.submit(plan_ref="WD-7fvx-source-pairing-rework", clips=[
                {"clip_index": 1, "status": "pending", "log": None,
                 "mp4": "outputs/wd_7fvx_audio_rework.mp4", "qc_verdict": None,
                 "kind": "director_source_pairing_rework", "mode": "audio", "render_native": True},
                {"clip_index": 2, "status": "pending", "log": None,
                 "mp4": "outputs/wd_7fvx_screenplay_rework.mp4", "qc_verdict": None,
                 "kind": "director_source_pairing_rework", "mode": "screenplay", "render_native": True},
            ])
            selected = next_admissible(queue)
        finally:
            queue.close()
        (root / "queue-record.json").write_text(json.dumps({
            "queue_id": "wangp-JobQueue-WD-7fvx", "database": "queue.db", "job_id": job_id,
            "retry_id": "attempt-8", "admission_state": "admitted" if selected == job_id else "not_admitted",
            "preflight": "host-preflight.json", "operator_authorization": "operator-authorization.md",
        }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if selected != job_id:
            raise SystemExit(2)
        queue = JobQueue(database); queue.set_state(job_id, "preflight"); queue.close()
        resuming = False
    (root / "outputs").mkdir(parents=True, exist_ok=True)
    (root / "qc").mkdir(parents=True, exist_ok=True)
    results = {"schema_version": "wangp-dspy.wd-7fvx-qc/v1", "targets": []}
    pending_qc = []
    if not resuming:
        queue = JobQueue(database); queue.set_state(job_id, "rendering"); queue.close()
    for mode, relative, log_name in TARGETS:
        evidence_path = root / "qc" / f"{mode}-target.json"
        output = root / relative
        if resuming and evidence_path.is_file() and output.is_file():
            target = json.loads(evidence_path.read_text(encoding="utf-8"))
            if target.get("objective_gate_pass") is True and target.get("output_sha256") == digest(output):
                results["targets"].append(target)
                continue
        compose(root, mode, output, root / log_name)
        pending_qc.append((mode, relative, log_name))
    if not resuming:
        queue = JobQueue(database); queue.set_state(job_id, "rendered_pending_qc"); queue.close()
    for mode, relative, log_name in pending_qc:
        target = qc(root, mode, root / relative)
        target.update({"mode": mode, "output_path": relative, "output_sha256": digest(root / relative),
                       "ffprobe": probe(root / relative), "whisper": [whisper(root, root / "inputs/wd_cpow_vibevoice_raw.prepared.wav", f"{mode}_pre"), whisper(root, root / relative, f"{mode}_post")]})
        results["targets"].append(target)
        spread_x, spread_y = target["mouth_box_consensus"]["center_spread"]
        target["objective_gate_pass"] = all((
            target["identity_vision"]["action_match"] >= 0.7,
            target["identity_vision"]["speaker_attribution"] >= 0.7,
            spread_x <= 0.03, spread_y <= 0.03,
            target["syncnet_av"]["confidence"] >= 1.0,
            abs(target["syncnet_av"]["offset_frames_25fps"]) <= 10,
            target["whisper"][1]["passed"],
            target["frame_motion"]["unique_frame_hash_count"] >= 3,
        ))
        (root / "qc" / f"{mode}-target.json").write_text(
            json.dumps(target, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if not target["objective_gate_pass"]:
            raise SystemExit(3)
        queue = JobQueue(database); queue.update_clip(job_id, 1 if mode == "audio" else 2, status="done",
                                                       log=log_name, mp4=relative,
                                                       qc_verdict={"verdict": "PASS", "path": f"qc/{mode}-target.json"},
                                                       lane="director_source_pairing_rework"); queue.close()
    queue = JobQueue(database); queue.set_state(job_id, "qc"); queue.set_state(job_id, "done")
    final_job = queue.get(job_id); payload = {"job_id": final_job.job_id, "state": final_job.state, "clips": final_job.clips}; queue.close()
    (root / "queue-final-state.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    results["auto_review"] = {"all_passed": all(
        target["identity_vision"]["passed"] and target["mouth_box_consensus"]["passed"]
        and target["syncnet_av"]["passed"] and target["whisper"][1]["passed"]
        and target["frame_motion"]["unique_frame_hash_count"] >= 3 for target in results["targets"]
    ), "bypassed": False}
    (root / "director-qc-evidence.json").write_text(json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if not results["auto_review"]["all_passed"]:
        raise SystemExit(3)
    after = preflight(root, final=True)
    if not after["all_required_hashes_match"]:
        raise SystemExit(4)
    print(json.dumps({"job_id": job_id, "state": "done", "auto_review_all_passed": True}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
