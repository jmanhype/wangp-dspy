#!/usr/bin/env python3
"""Queue reconciliation and evidence finalization for the one LF004 recovery."""

from __future__ import annotations

import hashlib, importlib.util, json, os, sqlite3, subprocess, sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from host.wangp_adapter import DEFAULT_MAX_ATTEMPTS  # noqa: E402
from predict.content_brief import load_content_brief  # noqa: E402
from services.director.run_ledger import repository_identity, write_run_ledger  # noqa: E402
from services.director.wiring import assemble_media  # noqa: E402
from services.jobs.queue import JobQueue, effective_render_fingerprint  # noqa: E402

BASE = ROOT / "datasets/content_briefs/lf004-operator-dogfood-56f"
RUN_ID = "lf004-operator-dogfood-56f-recovery-20260921"
DB = ROOT / f"datasets/{RUN_ID}.jobs.db"
PULL = ROOT / "datasets/runs/pull" / RUN_ID
PROVENANCE = ROOT / "datasets/runs/provenance" / RUN_ID
LEDGER = ROOT / f"datasets/{RUN_ID}.run_ledger.json"
PLAN_SHA = "620f2ba44beb7d0bc920772c136aa0ce6f76df89acd286647c23e5a7c8015eb8"
CANONICAL_ACCEPTANCE_REPO_PATH = (PROVENANCE / "operator-acceptance.json").relative_to(ROOT).as_posix()
FINAL_MEDIA_SHA256 = "2659ded7f48cef046741026cc476e316594689046b4a51ba6e58b7264a96e0d7"
OPERATOR_ACCEPTANCE_SHA256 = "e10e3e2180c9570a4ed731f428bab6a2e036b94b4988bd092f943c7b2dd1c76d"
OPERATOR_VERDICT_SOURCE = 'operator message: "i approve"'
EXECUTED_LAUNCHER_SHA256 = "419ba28c8f9ce5ce5028a66de424d7e67bbdf231724c3f586940f9f1b4720cc7"
RAW_BRIEF_SHA = "bc213a4a524390f2afcb913e120f8cf87276db1dc04f3f1934b9c69871cec767"
SEMANTIC_BRIEF_HASH = "sha256:67202d3597affeab4e5edcf15a1acef2f5e88ed00950ce17ff3012f5bb0472cd"
RAW_PLAN_SHA = "d0650b2e6b9d6fdbb1807ef82622c9c9a17888a0d4896e0c245feab146013943"
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


def _git_blob(path: Path) -> str:
    relative = path.relative_to(ROOT).as_posix()
    result = subprocess.run(["git", "-C", str(ROOT), "rev-parse", f"HEAD:{relative}"], check=True, capture_output=True, text=True)
    return result.stdout.strip()


def canonical_sha(plan: dict[str, Any]) -> str:
    spec = importlib.util.spec_from_file_location("lf004_verify", BASE / "run/verify.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module.canonical_sha(plan)


def verify_recovery_inputs(brief_path: Path | None = None, plan_path: Path | None = None) -> dict[str, str]:
    brief_path = brief_path or BASE / "brief.json"
    plan_path = plan_path or BASE / "plan.json"
    raw_brief = sha(brief_path)
    brief = load_content_brief(brief_path)
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    actual = {"raw_brief_sha256": raw_brief, "semantic_brief_hash": brief.brief_hash, "raw_plan_sha256": sha(plan_path), "canonical_plan_sha256": canonical_sha(plan)}
    expected = {"raw_brief_sha256": RAW_BRIEF_SHA, "semantic_brief_hash": SEMANTIC_BRIEF_HASH, "raw_plan_sha256": RAW_PLAN_SHA, "canonical_plan_sha256": PLAN_SHA}
    if actual != expected:
        raise ValueError(f"approved LF004 input hash mismatch: {actual}")
    return actual


def staging_plan(root: Path) -> list[dict[str, str]]:
    source = root / "datasets/content_briefs/lf004-operator-dogfood"
    remote = "/home/straughter/Wan2GP/lf004-operator-dogfood-56f-recovery-20260921"
    guides = [
        "lf003-vibevoice-audition-20260917/audio/tess.prepared.wav",
        "lf003-vibevoice-rho-strong-20260918/audio/rho.prepared.wav",
        "lf003-four-cut-fullgate-20260919/audio/tess-cut3.prepared.wav",
        "lf003-four-cut-fullgate-20260919/audio/rho-cut4.prepared.wav",
    ]
    paths = [*sorted((source / "plates").glob("*.png")), *(root / "datasets/runs/provenance" / item for item in guides)]
    destinations = [f"{remote}/plates/{path.name}" if path.parent == source / "plates" else f"{remote}/datasets/runs/provenance/{path.relative_to(root / 'datasets/runs/provenance')}" for path in paths]
    return [{"local": str(path), "remote": remote_path} for path, remote_path in zip(paths, destinations, strict=True)]


def stage_assets(root: Path, *, dry_run: bool, output: Path | None = None) -> list[dict[str, str]]:
    from pathlib import PurePosixPath
    from host.render_host import SshHost

    plan = staging_plan(root)
    if dry_run:
        if output is not None:
            write_json(output, {"schema_version": 1, "root": str(root), "assets": plan})
        return plan
    source = root / "datasets/content_briefs/lf004-operator-dogfood"
    remote = "/home/straughter/Wan2GP/lf004-operator-dogfood-56f-recovery-20260921"
    host = SshHost(target="3090", wgp_root="/home/straughter/Wan2GP", pull_root=str(root / "datasets/runs/pull"), asset_map={str(source / "plates"): f"{remote}/plates", str(root / "datasets/runs/provenance"): f"{remote}/datasets/runs/provenance"})
    staged = []
    for item in plan:
        local = Path(item["local"])
        destination = host.map_asset(str(local))
        host.makedirs(str(PurePosixPath(destination).parent))
        assert host.push_asset(str(local)) == destination
        staged.append({"local": str(local), "remote": destination})
    if output is not None:
        write_json(output, {"schema_version": 1, "root": str(root), "assets": staged})
    return staged


def run_film_once() -> list[dict[str, Any]]:
    from scripts.run_film import run_film

    verify_recovery_inputs()
    plan = json.loads((BASE / "plan.json").read_text(encoding="utf-8"))
    return run_film(
        BASE / "run/script.txt", BASE.parent / "lf004-operator-dogfood/plates",
        characters=plan["characters"], durations=[56.0 / 24.0] * 4,
        audio_paths=[clip["audio_guide"] for clip in plan["clips"]],
        db_path=DB, run_ledger_path=LEDGER,
        premise_id="LF004 Operator Dogfood: Borrowed Sunrise")


def correct_fingerprints() -> None:
    before_sha = sha(DB)
    queue = JobQueue(str(DB))
    records: list[dict[str, Any]] = []
    try:
        jobs = sorted((queue.get(job_id) for job_id in queue.list_state("done")), key=lambda job: job.clips[0]["clip_index"])
        assert [job.clips[0]["clip_index"] for job in jobs] == [1, 2, 3, 4]
        for job in jobs:
            clips = [dict(clip) for clip in job.clips]
            old = clips[0].get("render_fingerprint")
            effective = effective_render_fingerprint(clips[0])
            queue.update_render_inputs(job.job_id, clips)
            corrected = queue.get(job.job_id).clips[0]
            assert corrected["render_fingerprint"] == effective_render_fingerprint(corrected)
            records.append({"job_id": job.job_id, "clip_index": corrected["clip_index"], "stored_before": old, "effective": effective, "stored_after": corrected["render_fingerprint"]})
    finally:
        queue.close()
    payload = {"schema_version": 1, "correction": "post_render_effective_input_fingerprint", "render_rerun": False, "production_run_rerun": False, "method": "JobQueue.update_render_inputs", "pre_correction_db_sha256": before_sha, "post_correction_db_sha256": sha(DB), "jobs": records}
    write_json(PROVENANCE / "fingerprint-correction.json", payload)


def reconcile(db_path: Path = DB, provenance: Path = PROVENANCE, brief_path: Path | None = None, plan_path: Path | None = None) -> None:
    verify_recovery_inputs(brief_path, plan_path)
    plan = json.loads((plan_path or BASE / "plan.json").read_text(encoding="utf-8"))
    queue = JobQueue(str(db_path))
    records: list[dict[str, Any]] = []
    reopened: int | None = None
    try:
        states = ("done", "failed", "dead_letter", "pending", "rendered_pending_qc", "qc")
        ids = [job_id for state in states for job_id in queue.list_state(state)]
        jobs = sorted((queue.get(job_id) for job_id in ids), key=lambda job: job.clips[0]["clip_index"])
        assert [job.clips[0]["clip_index"] for job in jobs] == [1, 2, 3, 4]
        for job, dialogue in zip(jobs, plan["dialogue"], strict=True):
            clips = list(job.clips)
            clip = clips[0]
            missing = [name for name in ("audio_policy", "audio_carrier", "speaker_manifest", "dialogue_text") if name not in clip]
            clip.update({"audio_policy": {"discard_rendered_audio": False, "remux_source": "source_master", "remux_window": clip["audio_provenance"]["keeper_window_s"]}, "audio_carrier": "native_h3", "speaker_manifest": {"schema": "wangp-dspy.speaker-manifest/v1", "turns": [{"turn_index": 1, "speaker_id": clip["speaker_sn"], "picture_n": 1, "audio_path": clip["audio_guide"], "intended_text": dialogue["text"]}]}, "dialogue_text": dialogue["text"], "profile": 3, "recipe_name": "production", "model_type": "minimax_h3_ref2va_pruned", "audio_prompt_type": "A", "video_prompt_type": "I", "image_prompt_type": "S" if clip["chain"]["re_anchor"] else "I", "image_start": clip["image_refs"][0] if clip["chain"]["re_anchor"] else None, "action": "subtle natural listening and speaking motion", "speaker_description": SPEAKERS[int(clip["clip_index"])], "premise_id": "lf004-operator-dogfood", "resolution": [480, 832], "requested_frames": 56, "video_length": 56, "force_fps": 24, "steps": 20, "audio": {"path": clip["audio_guide"], "apad": True, "start_s": 0.0, "padded_duration_s": 56 / 24}})
            clip["audio_provenance"] = {**clip["audio_provenance"], "whisper_map": clip["audio_guide"]}
            queue.update_render_inputs(job.job_id, clips)
            records.append({"job_id": job.job_id, "clip_index": clip["clip_index"], "state_before": job.state, "missing_before_reconcile": missing})
        terminal = queue.list_state("failed") + queue.list_state("dead_letter")
        assert len(terminal) <= 1, terminal
        if terminal:
            if queue.get(terminal[0]).state != "dead_letter":
                queue.set_state(terminal[0], "dead_letter")
            reopened = queue.reopen_dead_letter(terminal[0], reason="reapply recorded LF004 content-brief queue reconciliation before QC")
    finally:
        queue.close()
    write_json(provenance / "recovery-reconciliation.json", {
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
    output.parent.mkdir(parents=True, exist_ok=True)
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


def _validate_operator_acceptance(payload: dict[str, Any]) -> None:
    expected = {
        "schema_version": "wangp-dspy.operator-acceptance/v1",
        "status": "operator_accepted",
        "creative_acceptance": "accepted",
        "verdict": "keep",
        "verdict_source": OPERATOR_VERDICT_SOURCE,
    }
    actual = {key: payload.get(key) for key in expected}
    if actual != expected:
        raise ValueError(f"unsupported LF004 operator acceptance: {actual}")
    artifact = payload.get("artifact")
    if not isinstance(artifact, dict) or artifact.get("sha256") != FINAL_MEDIA_SHA256:
        raise ValueError("LF004 acceptance artifact hash mismatch")
    if artifact.get("path") != "datasets/runs/pull/lf004-operator-dogfood-56f-recovery-20260921/assembled.mp4":
        raise ValueError("LF004 acceptance artifact path mismatch")


def _launcher_identity() -> dict[str, Any]:
    launcher = BASE / "run/run_recovery_once.sh"
    run_film = ROOT / "scripts/run_film.py"
    return {
        "repository": repository_identity(ROOT),
        "launcher_path": launcher.relative_to(ROOT).as_posix(),
        "launcher_sha256": sha(launcher),
        "scripts_run_film_path": run_film.relative_to(ROOT).as_posix(),
        "scripts_run_film_sha256": sha(run_film),
        "scripts_run_film_git_blob": _git_blob(run_film),
    }


def _validate_reconciled(final: dict[str, Any], ledger: dict[str, Any], postprocess: dict[str, Any], sidecar: dict[str, Any], review: str, canonical_sha: str) -> None:
    verdict = final.get("operator_verdict", {})
    if not all((final.get("status") == "operator_accepted", final.get("creative_acceptance") == "accepted", verdict.get("verdict") == "keep", verdict.get("verdict_source") == OPERATOR_VERDICT_SOURCE, verdict.get("acceptance_record_sha256") == canonical_sha, ledger.get("status") == "operator_accepted", postprocess.get("final_status") == "operator_accepted", final.get("post_execution_recovery", {}).get("final_status") == "operator_accepted", sidecar.get("status") == "operator_accepted", sidecar.get("record_class") == "historical_pre_verdict_snapshot", "Pre-verdict history" in review)):
        raise ValueError("LF004 evidence is accepted but incomplete or corrupted")


def _scoped_file(path: Path, root: Path, label: str) -> Path:
    """Return a readable path without following a link outside the root."""
    try:
        resolved = path.resolve(strict=True)
    except FileNotFoundError as error:
        raise FileNotFoundError(f"LF004 scoped {label} not found in output root: {path}") from error
    if not resolved.is_relative_to(root.resolve()):
        raise ValueError(f"LF004 scoped {label} path escapes output root: {path}")
    return path


def _resolve_operator_acceptance(acceptance_path: Path | None, pull: Path, provenance: Path, *, scoped: bool) -> Path:
    """Resolve the acceptance record without crossing an explicit output root."""
    if acceptance_path is not None:
        if scoped and not acceptance_path.resolve().is_relative_to(pull.resolve()):
            raise ValueError(f"LF004 acceptance path escapes output root: {acceptance_path}")
        return acceptance_path

    canonical = provenance / "operator-acceptance.json"
    if scoped:
        return _scoped_file(canonical, pull, "acceptance record")

    local = pull / "operator-acceptance.json"
    if not canonical.exists():
        raise FileNotFoundError(f"LF004 canonical operator acceptance record not found: {canonical}")
    candidates = [canonical, local] if local.exists() else [canonical]
    candidate_bytes = [candidate.read_bytes() for candidate in candidates]
    candidate_shas = [hashlib.sha256(item).hexdigest() for item in candidate_bytes]
    if len(set(candidate_shas)) != 1 or len(set(candidate_bytes)) != 1:
        disagreement = dict(zip((str(path) for path in candidates), candidate_shas, strict=True))
        raise ValueError(f"LF004 acceptance candidate records disagree: {disagreement}")
    return canonical


def record_operator_verdict(acceptance_path: Path | None = None, output_root: Path | None = None) -> dict[str, Any]:
    """Reconcile durable LF004 evidence from the one recorded operator verdict."""
    pull = PULL if output_root is None else output_root
    provenance = PROVENANCE if output_root is None else output_root / "provenance"
    ledger_path = LEDGER if output_root is None else output_root / "run-ledger.json"
    canonical = provenance / "operator-acceptance.json"
    source = _resolve_operator_acceptance(acceptance_path, pull, provenance, scoped=output_root is not None)
    acceptance_bytes = source.read_bytes()
    acceptance_sha = sha(source)
    if acceptance_sha != OPERATOR_ACCEPTANCE_SHA256:
        raise ValueError(f"LF004 acceptance record hash mismatch: {acceptance_sha}")
    acceptance = json.loads(acceptance_bytes)
    _validate_operator_acceptance(acceptance)

    final_path = pull / "final-provenance.json"
    sidecar_path = pull / "operator_review_pending.json"
    postprocess_path = pull / "postprocess-recovery.json"
    review_path = pull / "review.md"
    required = [final_path, sidecar_path, postprocess_path, review_path, ledger_path]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(f"authoritative LF004 evidence missing: {missing}")
    if output_root is not None:
        for path, label in ((final_path, "final provenance"), (sidecar_path, "operator sidecar"), (postprocess_path, "postprocess recovery"), (review_path, "review"), (ledger_path, "run ledger")):
            _scoped_file(path, output_root, label)
    final = json.loads(final_path.read_text(encoding="utf-8"))
    sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
    postprocess = json.loads(postprocess_path.read_text(encoding="utf-8"))
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    review = review_path.read_text(encoding="utf-8")
    historical_status = "operator_review_pending"
    recorded_hashes = (acceptance["artifact"]["sha256"], final.get("final_media", {}).get("sha256"), final.get("assembly", {}).get("output_sha256"), sidecar.get("final_sha256"), ledger.get("final_sha256"))
    if any(value != FINAL_MEDIA_SHA256 for value in recorded_hashes):
        raise ValueError(f"LF004 final-media identity mismatch: {recorded_hashes}")
    media = Path(final["final_media"]["path"])
    if not media.is_absolute():
        media = ROOT / media
    if sha(media) != FINAL_MEDIA_SHA256:
        raise ValueError(f"LF004 final media bytes mismatch: {media}")

    if final.get("status") == "operator_accepted":
        _validate_reconciled(final, ledger, postprocess, sidecar, review, acceptance_sha)
        if not canonical.exists() or sha(canonical) != acceptance_sha:
            raise ValueError("LF004 canonical acceptance record mismatch")
        return {"action": "no_change", "status": "operator_accepted", "changed_paths": [], "acceptance_record_sha256": acceptance_sha, "final_sha256": FINAL_MEDIA_SHA256}
    if final.get("status") != "operator_review_pending" or sidecar.get("status") != "operator_review_pending":
        raise ValueError(f"LF004 cannot reconcile status pair: {final.get('status')}, {sidecar.get('status')}")
    if final.get("creative_acceptance") != "none" or postprocess.get("final_status") != "operator_review_pending" or ledger.get("status") != "operator_review_pending":
        raise ValueError("LF004 pre-verdict evidence has unexpected state")
    if final.get("inputs", {}).get("launcher_sha256") != EXECUTED_LAUNCHER_SHA256:
        raise ValueError("LF004 executed launcher hash mismatch")

    checkout = _launcher_identity()
    verdict = {"status": "operator_accepted", "creative_acceptance": "accepted", "verdict": "keep", "verdict_source": OPERATOR_VERDICT_SOURCE, "acceptance_record_path": CANONICAL_ACCEPTANCE_REPO_PATH, "acceptance_record_sha256": acceptance_sha, "recorded_utc": acceptance["recorded_utc"]}
    final["status"] = "operator_accepted"
    final["creative_acceptance"] = "accepted"
    final["operator_verdict"] = verdict
    final["status_history"] = [{"record_class": "historical_pre_verdict", "status": historical_status}]
    if isinstance(final.get("post_execution_recovery"), dict):
        final["post_execution_recovery"]["final_status"] = "operator_accepted"
        final["post_execution_recovery"]["status_history"] = [{"record_class": "historical_pre_verdict", "status": historical_status}]
        final["post_execution_recovery"]["operator_verdict"] = verdict
        final["post_execution_recovery"]["reconciliation"] = {"render_rerun": False, "production_run_rerun": False, "acceptance_record_sha256": acceptance_sha}
    final["launcher_reconciliation"] = {"as_executed": {"launcher_sha256": EXECUTED_LAUNCHER_SHA256, "source": "inputs.launcher_sha256"}, "current_checkout": checkout}
    postprocess["final_status"] = "operator_accepted"
    postprocess["status_history"] = [{"record_class": "historical_pre_verdict", "status": historical_status}]
    postprocess["operator_verdict"] = verdict
    postprocess["reconciliation"] = {"render_rerun": False, "production_run_rerun": False, "acceptance_record_sha256": acceptance_sha}
    sidecar["status"] = "operator_accepted"
    sidecar["record_class"] = "historical_pre_verdict_snapshot"
    sidecar["historical_status"] = historical_status
    sidecar["superseded_by"] = verdict
    ledger_extra = {key: value for key, value in ledger.items() if key not in {"schema_version", "run_id", "status"}}
    ledger_extra["operator_verdict"] = verdict
    ledger_extra["operator_reconciliation"] = {"repository": checkout["repository"], "launcher_as_executed_sha256": EXECUTED_LAUNCHER_SHA256, "launcher_current_checkout_sha256": checkout["launcher_sha256"], "scripts_run_film_sha256": checkout["scripts_run_film_sha256"], "scripts_run_film_git_blob": checkout["scripts_run_film_git_blob"], "render_rerun": False}

    canonical.parent.mkdir(parents=True, exist_ok=True)
    canonical.write_bytes(acceptance_bytes)
    write_json(final_path, final)
    write_json(postprocess_path, postprocess)
    write_json(sidecar_path, sidecar)
    review_path.write_text("# LF004 56-frame recovery — operator review\n\nStatus: `operator_accepted`; operator verdict: `keep`. Verdict source: `operator message: \"i approve\"`. Acceptance record SHA-256: `" + acceptance_sha + "`. Final film SHA-256: `" + FINAL_MEDIA_SHA256 + "`.\n\n## Pre-verdict history\n\nBefore the operator verdict, this review was `" + historical_status + "`. This reconciliation recorded that verdict without a render, probe, contact-sheet, GPU, host, network, or queue operation.\n\nFilm contact sheet: `review/film.contact_sheet.jpg`; per-cut sheets and full evidence are in this directory.\n", encoding="utf-8")
    write_run_ledger(ledger_path, run_id=RUN_ID, identity=ledger["repository"], status="operator_accepted", extra=ledger_extra)
    return {"action": "reconciled", "status": "operator_accepted", "changed_paths": [str(path) for path in (canonical, final_path, postprocess_path, sidecar_path, review_path, ledger_path)], "acceptance_record_sha256": acceptance_sha, "final_sha256": FINAL_MEDIA_SHA256, "repository_head": checkout["repository"]["commit_sha"], "current_launcher_sha256": checkout["launcher_sha256"]}


def main(argv: list[str]) -> int:
    if argv == ["reconcile"]:
        reconcile()
    elif argv == ["correct-fingerprints"]:
        correct_fingerprints()
    elif argv == ["run-film"]:
        run_film_once()
    elif len(argv) >= 3 and argv[0] == "stage-assets" and argv[1] == "--root":
        rest = argv[3:]
        dry_run = "--dry-run" in rest
        values = [item for item in rest if item != "--dry-run"]
        stage_assets(Path(argv[2]), dry_run=dry_run, output=Path(values[0]) if values else None)
    elif argv == ["finalize"]:
        finalize()
    elif argv and argv[0] == "record-operator-verdict":
        values = argv[1:]
        if len(values) % 2 or any(flag not in {"--acceptance", "--output-root"} for flag in values[::2]):
            raise SystemExit("usage: recover_once.py record-operator-verdict [--acceptance PATH] [--output-root PATH]")
        flags = dict(zip(values[::2], values[1::2], strict=True))
        print(json.dumps(record_operator_verdict(Path(flags["--acceptance"]) if "--acceptance" in flags else None, Path(flags["--output-root"]) if "--output-root" in flags else None), sort_keys=True))
    else:
        raise SystemExit("usage: recover_once.py reconcile|finalize|record-operator-verdict")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
