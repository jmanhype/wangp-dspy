#!/usr/bin/env python3
"""Queue reconciliation and evidence finalization for the one LF004 recovery."""

from __future__ import annotations

import hashlib, json, sqlite3, subprocess, sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from host.wangp_adapter import DEFAULT_MAX_ATTEMPTS  # noqa: E402
from services.director.run_ledger import repository_identity, write_run_ledger  # noqa: E402
from services.director.wiring import assemble_media  # noqa: E402
from services.jobs.queue import JobQueue  # noqa: E402

BASE = ROOT / "datasets/content_briefs/lf004-operator-dogfood-56f"
RUN_ID = "lf004-operator-dogfood-56f-recovery-20260921"
DB = ROOT / f"datasets/{RUN_ID}.jobs.db"
PULL = ROOT / "datasets/runs/pull" / RUN_ID
PROVENANCE = ROOT / "datasets/runs/provenance" / RUN_ID
LEDGER = ROOT / f"datasets/{RUN_ID}.run_ledger.json"
PLAN_SHA = "620f2ba44beb7d0bc920772c136aa0ce6f76df89acd286647c23e5a7c8015eb8"
SPEAKERS = {
    1: "Tess (S1), the woman on the LEFT; not Rho (S2) on the RIGHT",
    2: "Rho (S2), the man on the RIGHT; not Tess (S1) on the LEFT",
    3: "Tess (S1), the woman on the LEFT; not Rho (S2) on the RIGHT",
    4: "Rho (S2), the man on the RIGHT; not Tess (S1) on the LEFT",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def reconcile() -> None:
    plan = json.loads((BASE / "plan.json").read_text(encoding="utf-8"))
    queue = JobQueue(str(DB))
    records: list[dict[str, Any]] = []
    reopened: int | None = None
    try:
        states = ("failed", "dead_letter", "pending", "rendered_pending_qc", "qc")
        ids = [job_id for state in states for job_id in queue.list_state(state)]
        jobs = sorted((queue.get(job_id) for job_id in ids), key=lambda job: job.clips[0]["clip_index"])
        assert [job.clips[0]["clip_index"] for job in jobs] == [1, 2, 3, 4]
        for job, dialogue in zip(jobs, plan["dialogue"], strict=True):
            clips = list(job.clips)
            clip = clips[0]
            missing = [name for name in ("audio_policy", "audio_carrier", "speaker_manifest", "dialogue_text") if name not in clip]
            clip.update({"audio_policy": {"discard_rendered_audio": False, "remux_source": "source_master", "remux_window": clip["audio_provenance"]["keeper_window_s"]}, "audio_carrier": "native_h3", "speaker_manifest": {"schema": "wangp-dspy.speaker-manifest/v1", "turns": [{"turn_index": 1, "speaker_id": clip["speaker_sn"], "picture_n": 1, "audio_path": clip["audio_guide"], "intended_text": dialogue["text"]}]}, "dialogue_text": dialogue["text"], "profile": 3, "recipe_name": "production", "model_type": "minimax_h3_ref2va_pruned", "audio_prompt_type": "A", "video_prompt_type": "I", "image_prompt_type": "S" if clip["chain"]["re_anchor"] else "I", "image_start": clip["image_refs"][0] if clip["chain"]["re_anchor"] else None, "action": "subtle natural listening and speaking motion", "speaker_description": SPEAKERS[int(clip["clip_index"])], "premise_id": "lf004-operator-dogfood", "resolution": [480, 832], "requested_frames": 56, "video_length": 56, "force_fps": 24, "steps": 20, "audio": {"path": clip["audio_guide"], "apad": True, "start_s": 0.0, "padded_duration_s": 56 / 24}})
            clip["audio_provenance"] = {**clip["audio_provenance"], "whisper_map": clip["audio_guide"]}
            queue.update_clips(job.job_id, clips)
            records.append({"job_id": job.job_id, "clip_index": clip["clip_index"], "state_before": job.state, "missing_before_reconcile": missing})
        terminal = queue.list_state("failed") + queue.list_state("dead_letter")
        assert len(terminal) <= 1, terminal
        if terminal:
            if queue.get(terminal[0]).state != "dead_letter":
                queue.set_state(terminal[0], "dead_letter")
            reopened = queue.reopen_dead_letter(terminal[0], reason="reapply recorded LF004 content-brief queue reconciliation before QC")
    finally:
        queue.close()
    write_json(PROVENANCE / "recovery-reconciliation.json", {
        "schema_version": 1, "canonical_plan_sha256": PLAN_SHA, "reopened_attempt_id": reopened,
        "reason": "content-brief queue envelope omitted accepted Ref2VA audio/QC/runtime fields",
        "discovered_bug": any(record["missing_before_reconcile"] for record in records), "jobs": records,
    })


def rows(db: sqlite3.Connection, query: str) -> list[dict[str, Any]]:
    db.row_factory = sqlite3.Row
    return [dict(row) for row in db.execute(query)]


def probe(path: Path) -> dict[str, Any]:
    argv = ["ffprobe", "-v", "error", "-show_entries", "format=duration,size:stream=index,codec_type,codec_name,width,height,avg_frame_rate,nb_frames,channels,sample_rate", "-of", "json", str(path)]
    result = subprocess.run(argv, check=True, capture_output=True, text=True)
    return {"path": str(path), "sha256": sha(path), "ffprobe": json.loads(result.stdout)}


def contact_sheet(source: Path, output: Path, tiles: int) -> dict[str, Any]:
    duration = float(probe(source)["ffprobe"]["format"]["duration"])
    interval = max(1.0, duration / tiles)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(source), "-vf", f"fps=1/{interval:.6f},scale=240:-1,tile={tiles}x1", "-frames:v", "1", str(output)], check=True)
    return {"path": str(output), "sha256": sha(output)}


def terminal_failure(connection: sqlite3.Connection) -> None:
    jobs = rows(connection, "select * from jobs order by created_at")
    attempts = rows(connection, "select * from job_attempts order by attempt_id")
    failures = rows(connection, "select * from job_attempt_failures order by failure_id")
    payload = {"schema_version": 1, "run_id": RUN_ID, "status": "fail_closed", "canonical_plan_sha256": PLAN_SHA, "jobs": jobs, "attempts": attempts, "failures": failures, "repository": repository_identity(ROOT)}
    write_json(PULL / "terminal-gate-failure.json", payload)
    write_run_ledger(LEDGER, run_id=RUN_ID, identity=repository_identity(ROOT), status="fail_closed", extra={"canonical_plan_sha256": PLAN_SHA, "evidence": str(PULL / "terminal-gate-failure.json")})


def finalize() -> None:
    connection = sqlite3.connect(DB)
    jobs = rows(connection, "select * from jobs order by created_at")
    if len(jobs) != 4 or any(job["state"] != "done" for job in jobs):
        terminal_failure(connection)
        raise SystemExit(f"fail-closed queue: {[(job['job_id'], job['state']) for job in jobs]}")
    cuts: list[dict[str, Any]] = []
    for job in jobs:
        clips = json.loads(job["clips"])
        assert len(clips) == 1 and clips[0].get("status") == "done" and clips[0].get("mp4")
        clip = clips[0]
        evidence_path = Path(clip.get("qc_evidence_path") or Path(clip["mp4"]).with_name("qc-evidence.json"))
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        vision = evidence["vision_judge"]
        mouth_boxes = vision.get("speaker_mouth_bboxes")
        gates = {"whisper_pre": evidence["whisper_gates"]["pre"]["passed"], "whisper_post": evidence["whisper_gates"]["post"]["passed"], "vision_identity_composition": vision["passed"], "mouth_box_three_frame_localization": isinstance(mouth_boxes, list) and len(mouth_boxes) == 3, "syncnet_av": evidence["av_sync_gate"]["passed"]}
        if not all(gates.values()):
            terminal_failure(connection)
            raise SystemExit(f"fail-closed gates for {job['job_id']}: {gates}")
        media = probe(Path(clip["mp4"]))
        cuts.append({"job_id": job["job_id"], "clip_index": clip["clip_index"], "speaker": clip["speaker"], "dialogue": clip["dialogue_text"], "seed": clip.get("seed"), "render_fingerprint": clip.get("render_fingerprint"), "media": media, "gates": gates, "whisper": evidence["whisper_gates"], "vision": vision, "av_sync": evidence["av_sync_gate"], "qc_evidence_path": str(evidence_path), "qc_evidence_sha256": sha(evidence_path)})
    connection.close()
    PULL.mkdir(parents=True, exist_ok=True)
    assembly = assemble_media([cut["media"]["path"] for cut in cuts], str(PULL / "assembled.mp4"))
    final = probe(PULL / "assembled.mp4")
    write_json(PULL / "probe.json", final)
    review = PULL / "review"
    visuals = {"film": contact_sheet(PULL / "assembled.mp4", review / "film.contact_sheet.jpg", 8), "cuts": [contact_sheet(Path(cut["media"]["path"]), review / f"cut{cut['clip_index']}.contact_sheet.jpg", 4) for cut in cuts]}
    video = next(stream for stream in final["ffprobe"]["streams"] if stream["codec_type"] == "video")
    expected_duration = 224 / 24
    assert int(video["nb_frames"]) == 224 and video["avg_frame_rate"] == "24/1" and abs(float(final["ffprobe"]["format"]["duration"]) - expected_duration) <= 1 / 48
    settings = {path.name: sha(path) for path in sorted(PROVENANCE.glob("*.json"))}
    identity = repository_identity(ROOT)
    payload = {"schema_version": 1, "run_id": RUN_ID, "status": "operator_review_pending", "operator_approval": {"approved_at_utc": "2026-09-21T00:54:03Z", "canonical_plan_sha256": PLAN_SHA, "brief_hash": "sha256:67202d3597affeab4e5edcf15a1acef2f5e88ed00950ce17ff3012f5bb0472cd", "raw_brief_sha256": sha(BASE / "brief.json")}, "inputs": {"brief_sha256": sha(BASE / "brief.json"), "plan_sha256": sha(BASE / "plan.json"), "planning_ledger_sha256": sha(BASE / "run/run_ledger.json"), "launcher_sha256": sha(BASE / "run/run_recovery_once.sh"), "verifier_sha256": sha(BASE / "run/verify.py")}, "retry_policy": {"DEFAULT_MAX_ATTEMPTS": DEFAULT_MAX_ATTEMPTS, "per_cut_max_attempts": 3}, "reconciliation": json.loads((PROVENANCE / "recovery-reconciliation.json").read_text()), "settings_hashes": settings, "jobs": [{key: job.get(key) for key in ("job_id", "state", "failure_count", "failure_class")} for job in jobs], "cuts": cuts, "assembly": {**assembly, "output_sha256": final["sha256"]}, "final_media": final, "review_visuals": visuals, "repository": identity, "all_declared_gates_passed": True, "creative_acceptance": "none"}
    guides = json.loads((BASE.parent / "lf004-operator-dogfood/run/audio-guides.json").read_text(encoding="utf-8"))
    payload["inputs"]["guides"] = [sha(ROOT / turn["audio"]) for turn in guides["turns"]]
    payload["inputs"]["plates"] = {name: sha(BASE.parent / "lf004-operator-dogfood/plates" / item["staged"]) for name, item in guides["plates"].items()}
    write_json(PULL / "final-provenance.json", payload)
    write_json(PULL / "operator_review_pending.json", {"status": "operator_review_pending", "final_sha256": final["sha256"], "review_visuals": visuals})
    (PULL / "review.md").write_text("# LF004 56-frame recovery — operator review\n\nStatus: `operator_review_pending`; all mechanical gates passed. Final film: `assembled.mp4` SHA-256 `" + final["sha256"] + "`.\n\nFilm contact sheet: `review/film.contact_sheet.jpg`; per-cut sheets and full evidence are in this directory.\n", encoding="utf-8")
    write_run_ledger(LEDGER, run_id=RUN_ID, identity=identity, status="operator_review_pending", extra={"canonical_plan_sha256": PLAN_SHA, "final_path": str(PULL / "assembled.mp4"), "final_sha256": final["sha256"], "all_declared_gates_passed": True})
    print(json.dumps({"status": payload["status"], "cuts": [cut["media"]["sha256"] for cut in cuts], "final_sha256": final["sha256"]}, sort_keys=True))


def main(argv: list[str]) -> int:
    if argv == ["reconcile"]:
        reconcile()
    elif argv == ["finalize"]:
        finalize()
    else:
        raise SystemExit("usage: recover_once.py reconcile|finalize")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
