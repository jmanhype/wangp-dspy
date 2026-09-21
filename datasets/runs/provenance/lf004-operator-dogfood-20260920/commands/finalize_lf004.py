#!/usr/bin/env python3
from __future__ import annotations
import hashlib
import importlib.util
import json
import sqlite3
import subprocess
from pathlib import Path
from services.director.wiring import assemble_media
from services.director.run_ledger import repository_identity, write_run_ledger

ROOT = Path("/Users/Shared/HermesWorkspace/wangp-dspy/.claude/worktrees/dev-WD-42no")
DB = ROOT / "datasets/lf004-operator-dogfood-20260920.jobs.db"
RUN = ROOT / "datasets/runs/pull/lf004-operator-dogfood-20260920"
PROV = ROOT / "datasets/runs/provenance/lf004-operator-dogfood-20260920"
BRIEF = ROOT / "datasets/content_briefs/lf004-operator-dogfood"
PLAN_SHA = "70280fdcd6fb7f54bc4f7027e03de54e4897178dd41adcf92ef31bd347d7bd86"

def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()

def run_json(argv: list[str]) -> dict:
    result = subprocess.run(argv, check=True, capture_output=True, text=True)
    return json.loads(result.stdout)

def probe(path: Path) -> dict:
    raw = run_json(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)])
    video = next(stream for stream in raw["streams"] if stream["codec_type"] == "video")
    audio = next(stream for stream in raw["streams"] if stream["codec_type"] == "audio")
    return {
        "path": str(path), "sha256": sha(path), "format": raw["format"]["format_name"],
        "duration_s": float(raw["format"]["duration"]), "video_codec": video["codec_name"],
        "width": int(video["width"]), "height": int(video["height"]), "frame_count": int(video["nb_frames"]),
        "fps": video["avg_frame_rate"], "audio_codec": audio["codec_name"],
        "audio_channels": int(audio["channels"]), "audio_sample_rate": int(audio["sample_rate"]),
    }

def contact_sheet(source: Path, output: Path, tiles: int) -> dict:
    output.parent.mkdir(parents=True, exist_ok=True)
    interval = max(1.0, float(run_json(["ffprobe", "-v", "error", "-show_format", "-of", "json", str(source)])["format"]["duration"]) / tiles)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(source), "-vf", f"fps=1/{interval:.6f},scale=240:-1,tile={tiles}x1", "-frames:v", "1", str(output)], check=True)
    return {"path": str(output), "sha256": sha(output)}

con = sqlite3.connect(DB)
verify_spec = importlib.util.spec_from_file_location("lf004_verify", BRIEF / "run/verify.py")
verify = importlib.util.module_from_spec(verify_spec); verify_spec.loader.exec_module(verify)
if verify.canonical_sha(json.loads((BRIEF / "plan.json").read_text())) != PLAN_SHA:
    raise SystemExit("current LF004 plan does not match the operator-approved canonical hash")
con.row_factory = sqlite3.Row
jobs = [dict(row) for row in con.execute("select * from jobs order by created_at")]
attempts = [dict(row) for row in con.execute("select * from job_attempts order by attempt_id")]
failures = [dict(row) for row in con.execute("select * from job_attempt_failures order by failure_id")]
if len(jobs) != 4 or any(job["state"] != "done" for job in jobs):
    raise SystemExit(f"LF004 is not fully done: {[(j['job_id'], j['state']) for j in jobs]}")
cuts = []
for job in jobs:
    clips = json.loads(job["clips"])
    if len(clips) != 1 or clips[0].get("status") != "done" or not clips[0].get("mp4"):
        raise SystemExit(f"invalid completed clip payload for {job['job_id']}: {clips}")
    clip = clips[0]
    media = Path(clip["mp4"])
    evidence_path = media.with_name("qc-evidence.json")
    evidence = json.loads(evidence_path.read_text())
    gates = {
        "whisper_pre": evidence["whisper_gates"]["pre"]["passed"],
        "whisper_post": evidence["whisper_gates"]["post"]["passed"],
        "vision": evidence["vision_judge"]["passed"],
        "av_sync": evidence["av_sync_gate"]["passed"],
    }
    if not all(gates.values()):
        raise SystemExit(f"gate failure for {job['job_id']}: {gates}")
    cuts.append({
        "job_id": job["job_id"], "clip_index": clip["clip_index"], "speaker": clip["speaker"],
        "dialogue": clip["dialogue_text"], "render_fingerprint": clip["render_fingerprint"],
        "media": probe(media), "qc_evidence_path": str(evidence_path), "qc_evidence_sha256": sha(evidence_path),
        "gates": gates, "whisper": evidence["whisper_gates"], "av_sync": evidence["av_sync_gate"],
    })
RUN.mkdir(parents=True, exist_ok=True)
assembly = assemble_media([cut["media"]["path"] for cut in cuts], str(RUN / "assembled.mp4"))
final = probe(RUN / "assembled.mp4")
if final["duration_s"] < 17.5 or final["width"] != 480 or final["height"] != 832:
    raise SystemExit(f"unexpected final media properties: {final}")
review = RUN / "review"
review.mkdir(parents=True, exist_ok=True)
visuals = {"cuts": [contact_sheet(Path(cut["media"]["path"]), review / f"cut{cut['clip_index']}.contact_sheet.jpg", 4) for cut in cuts], "film": contact_sheet(RUN / "assembled.mp4", review / "film.contact_sheet.jpg", 8)}
inputs = {str(path.relative_to(ROOT)): sha(path) for path in [BRIEF / "brief.json", BRIEF / "plan.json", BRIEF / "run/script.txt", *sorted((BRIEF / "plates").glob("*.png")), *sorted((BRIEF / "run").glob("*.json"))]}
repository = repository_identity(ROOT)
provenance = {
    "schema_version": 1, "run_id": "lf004-operator-dogfood-20260920", "status": "operator_review_pending",
    "operator_approval": {"approved_at_utc": "2026-09-20T20:47:21Z", "canonical_plan_sha256": PLAN_SHA, "scope": "exactly one governed LF004 production execution"},
    "inputs": inputs, "jobs": [{key: job[key] for key in ("job_id", "state", "failure_count", "failure_class")} for job in jobs],
    "attempts": attempts, "attempt_failures": failures, "cuts": cuts, "assembly": {**assembly, "output_sha256": final["sha256"]}, "final_media": final, "review_visuals": visuals,
    "repository": repository, "all_declared_gates_passed": True,
}
(RUN / "final-provenance.json").write_text(json.dumps(provenance, indent=2, sort_keys=True) + "\n")
(RUN / "operator_review_pending.json").write_text(json.dumps({"status": "operator_review_pending", "final_sha256": final["sha256"], "review_visuals": visuals}, indent=2) + "\n")
(RUN / "review.md").write_text("# LF004 Borrowed Sunrise — operator review\n\n**Status:** `operator_review_pending`; all mechanical gates passed.\n\n- Final film: `assembled.mp4`\n- SHA-256: `" + final["sha256"] + "`\n- Duration/resolution: " + f"{final['duration_s']:.3f}s, {final['width']}x{final['height']}" + "\n- Contact sheet: `review/film.contact_sheet.jpg`\n\nPer-cut contact sheets are in `review/`; full gate evidence and provenance are in `final-provenance.json`.\n")
write_run_ledger(str(ROOT / "datasets/run_ledger.json"), run_id=provenance["run_id"], identity=repository, status="operator_review_pending", extra={"canonical_plan_sha256": PLAN_SHA, "final_path": str(RUN / "assembled.mp4"), "final_sha256": final["sha256"], "review_path": str(review), "all_declared_gates_passed": True})
print(json.dumps({"status": "operator_review_pending", "jobs": len(jobs), "cuts": [cut["media"]["sha256"] for cut in cuts], "final": final, "review": str(review)}, indent=2))
