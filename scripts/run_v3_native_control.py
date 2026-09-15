"""Repo-owned reproduction of the recovered v3 pair with native H3 audio.

This is a controlled experiment, not a new creative recipe.  It imports the
old v3 guide WAVs and image refs through ``SshHost.fetch_file`` when they are
not already present, plans the pair through ``DirectorRun``/the durable queue,
renders through ``render_for_job``, and assembles the pulled ``raw.mp4``
artifacts instead of the runtime's external-audio remux.  The runtime preserves native AV byte-for-byte and QC reads it. No external
audio replacement is allowed; an output is a candidate, never automatic KEEP.
"""
from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from host.render_host import SshHost
from predict.continuation_lane import ContinuationExtras
from services.director.premises import Premise
from services.director.run import DirectorRun, DirectorRunPlan
from services.director.wiring import assemble_media
from services.director.run_records import append_dataset_run
from predict.v3_recipe import golden_prompt, V3_RECIPE
from services.jobs.queue import JobQueue
from scripts import run_jobs


FPS = 24
FRAMES = 56
TARGET_S = FRAMES / FPS
SEED = 904

REMOTE_ASSETS = {
    "grandma_frame2.png": "/home/straughter/speaker_test/grandma_frame2.png",
    "soul_frame.png": "/home/straughter/speaker_test/soul_frame.png",
    "grandma_frame.png": "/home/straughter/speaker_test/grandma_frame.png",
    "dgshort_g.wav": "/home/straughter/marathon/v2/dialogue/dgshort_g.wav",
    "dgshort_s.wav": "/home/straughter/marathon/v2/dialogue/dgshort_s.wav",
}


def _legacy_prompt(speaker: str, *, first: bool) -> str:
    if (speaker, first) not in {("grandma", True), ("soul", False)}:
        raise ValueError("not a golden pair turn")
    return golden_prompt(1 if first else 2)


def _host(root: Path) -> SshHost:
    # Asset mapping is explicit and scoped to this control's imported fixture
    # directory.  The host seam, not scp or a direct shell bridge, owns all
    # transport.
    asset_root = root / "assets" / "acceptance" / "v3-control"
    return SshHost(
        target=os.environ.get("WANGP_SSH_TARGET") or "3090",
        wgp_root="/home/straughter/Wan2GP",
        pull_root=str(root / "datasets" / "runs" / "pull"),
        asset_map={str(asset_root): "/home/straughter/acceptance/v3-native-control-fixtures"},
    )


def _ensure_assets(host: SshHost, root: Path) -> dict[str, str]:
    local_root = root / "assets" / "acceptance" / "v3-control"
    local_root.mkdir(parents=True, exist_ok=True)
    out: dict[str, str] = {}
    for name, remote in REMOTE_ASSETS.items():
        local = local_root / name
        if not local.is_file():
            host.fetch_file(remote, str(local))
        if not local.is_file():
            raise RuntimeError(f"fixture pull did not materialize {local}")
        out[name] = str(local.resolve())
    return out


def _build_plan(run_id: str, assets: dict[str, str], ledger: Path):
    premise = Premise(
        id="dg-v3-control",
        title="Devil's Grandma v3 control",
        logline="A grandmother feeds cookies to a tormented soul in hell.",
        style_ref="",
        characters=(
            {"name": "grandma", "sn_tag": "S1",
             "description": "the elderly grandmother with round glasses and cardigan"},
            {"name": "soul", "sn_tag": "S2",
             "description": "the skinny tormented soul on the rack"},
        ),
    )
    script = [
        {"speaker": "grandma", "text": "Oh hush now, dear. Have a cookie."},
        {"speaker": "soul", "text": "Lady, I am on fire!"},
    ]
    anchor = assets["grandma_frame2.png"]
    media = {
        "premise_id": premise.id,
        "style_ref": "",
        "plates": {
            "anchor": anchor,
            "grandma": assets["grandma_frame.png"],
            "soul": assets["soul_frame.png"],
        },
        "audio": [
            {"path": assets["dgshort_g.wav"], "speaker": "grandma"},
            {"path": assets["dgshort_s.wav"], "speaker": "soul"},
        ],
    }
    plate_pairs = [[anchor, assets["soul_frame.png"]],
                   [anchor, assets["grandma_frame.png"]]]
    run = DirectorRun(run_id=run_id, premise=premise,
                      dataset_run_path=str(ledger))
    plan = run.plan(
        script, audio_paths=[media["audio"][0]["path"],
                             media["audio"][1]["path"]],
        plate_paths=plate_pairs, media_manifest=media,
        expected_cuts=2, recipe_name="golden_v3", seed_override=SEED,
        durations_s=[TARGET_S, TARGET_S],
    )

    # Replace only the prompt carrier with the verbatim v3 S1/S2 envelope and
    # mark the compatibility lane explicitly.  All typed plan/queue fields
    # remain repo-owned and validated.
    clips = []
    for clip, line in zip(plan.clips, script):
        speaker = line["speaker"]
        item = dict(clip)
        item["prompt"] = _legacy_prompt(
            speaker, first=clip["clip_index"] == 1)
        item["dialogue_text"] = line["text"]
        extra = ContinuationExtras.from_dict(item["continuation_extras"])
        extra = dataclasses.replace(extra, legacy_v2_prompt=True)
        item["continuation_extras"] = extra.to_extra()
        clips.append(item)
    plan = DirectorRunPlan(plan.run_id, plan.premise_id, plan.chain_plan,
                           tuple(clips), plan.media_manifest)
    return premise, plan, media


def _resume_jobs(queue, run_id: str, recovery: dict | None,
                 retry_qc_reason: str | None = None) -> list[str]:
    """Resume exactly this pair; never enqueue duplicates or reopen implicitly."""
    from services.jobs.states import ALLOWED_TRANSITIONS
    jobs = [queue.get(jid) for state in ALLOWED_TRANSITIONS
            for jid in queue.list_state(state)]
    if any(j.plan_ref != run_id or len(j.clips) != 1 for j in jobs):
        raise ValueError('golden resume requires a dedicated database for this pair')
    jobs.sort(key=lambda j: j.clips[0].get('clip_index', 0) if j.clips else 0)
    if len(jobs) != 2 or [j.clips[0].get('clip_index') for j in jobs] != [1, 2]:
        raise ValueError('resume requires exactly the existing two-cut golden plan')
    for idx, job in enumerate(jobs, 1):
        clip = job.clips[0]
        if (len(job.clips) != 1 or clip.get('recipe_name') != 'golden_v3'
                or clip.get('seed') != SEED or clip.get('prompt') != golden_prompt(idx)):
            raise ValueError('existing plan is not the exact golden control')
        if job.state not in {'done', 'pending', 'failed'}:
            raise ValueError(f'resume refuses active/dead-letter state {job.state}')
    failed = [j for j in jobs if j.state == 'failed']
    if recovery is not None and retry_qc_reason:
        raise ValueError('choose completed-render recovery or existing-artifact re-QC, not both')
    if recovery is not None:
        if (len(failed) != 1 or failed[0].failure_class not in {'render_error', 'truncated_render_log'}
                or not failed[0].retryable):
            raise ValueError('recovery requires one retryable render/transport/log failure')
        job = failed[0]
        clips = [dict(c) for c in job.clips]
        clips[0]['completed_render_recovery'] = dict(recovery)
        queue.update_clips(job.job_id, clips)
        queue.requeue_failed(job.job_id, reason=recovery['reason'])
    elif retry_qc_reason:
        if (len(failed) != 1 or failed[0].failure_class != 'qc_gate'
                or failed[0].clips[0].get('status') != 'rendered'
                or not Path(failed[0].clips[0].get('mp4') or '').is_file()):
            raise ValueError('re-QC requires one failed QC job with a preserved rendered artifact')
        queue.requeue_failed(failed[0].job_id, reason=retry_qc_reason)
    elif failed:
        raise ValueError('failed control requires explicit completed-render recovery')
    return [job.job_id for job in jobs]


def run_control(*, run_id: str, db: Path, ledger: Path, output: Path,
                resume: bool = False, recovery: dict | None = None,
                retry_qc_reason: str | None = None) -> dict:
    if (recovery is not None or retry_qc_reason) and not resume:
        raise ValueError('completed-render recovery requires --resume')
    host = _host(ROOT)
    assets = _ensure_assets(host, ROOT)
    if not resume:
        premise, plan, media = _build_plan(run_id, assets, ledger)

    for path in set(assets.values()):
        remote = host.map_asset(path)
        host.makedirs(remote.rsplit("/", 1)[0])
        host.push_asset(path)

    queue = JobQueue(str(db))
    try:
        judge = run_jobs._default_vision_judge(host=host)
        if resume:
            job_ids = _resume_jobs(queue, run_id, recovery, retry_qc_reason)
            if recovery is not None:
                append_dataset_run(ledger, run_id=run_id, status='recovery_requested',
                                   payload={'job_ids': job_ids, **recovery})
            if retry_qc_reason:
                append_dataset_run(ledger, run_id=run_id, status='re_qc_requested',
                                   payload={'job_ids':job_ids,'reason':retry_qc_reason,
                                            're_rendered':False, 'threshold_changed':False})
        else:
            job_ids = DirectorRun.submit(plan, queue)
        handled = run_jobs.drain_once(queue, host=host, vision_judge=judge)
        jobs = [queue.get(jid) for jid in job_ids]
        states = {job.job_id: job.state for job in jobs}
        if any(job.state != "done" for job in jobs):
            raise RuntimeError(f"control did not complete: {states}")
        remux_videos = [job.clips[0]["mp4"] for job in jobs]
        native_videos = []
        for remux in remux_videos:
            raw = str(Path(remux).with_name("raw.mp4"))
            if not Path(raw).is_file():
                raise RuntimeError(f"native raw artifact missing: {raw}")
            native_videos.append(raw)
        # The original concat ran on the renderer host. Local macOS ffmpeg
        # is a different codec build and cannot satisfy a byte-level canary.
        assembly = assemble_media(native_videos, str(output.resolve()), host=host)
        from predict.v3_canary import verify_v3_canary
        canary = verify_v3_canary(
            cut1=native_videos[0], cut2=native_videos[1], pair=output,
            seed=jobs[1].clips[0]['image_start'],
            report_path=output.parent / 'golden-canary.json')
    finally:
        queue.close()

    record = append_dataset_run(
        ledger, run_id=run_id, status="needs_review",
        payload={
            "premise_id": "dg-v3-control",
            "clip_count": 2,
            "recipe_name": "v3_native_control",
            "profile": 2,
            "resolution_request": V3_RECIPE.resolution,
            "seed": SEED,
            "frames": [FRAMES, FRAMES],
            "target_duration_s": TARGET_S,
            "audio_carrier": "native_h3",
            "verdict": "NEEDS REVIEW",
            "recipe_version": V3_RECIPE.version,
            "golden_canary": canary,
            "remux_artifacts": remux_videos,
            "native_artifacts": native_videos,
            "handled": handled,
            "assembly": assembly,
            "fixture_md5": {name: hashlib.md5(
                Path(path).read_bytes()).hexdigest()
                for name, path in assets.items()},
        },
    )
    return {"run_id": run_id, "job_ids": job_ids,
            "output_path": assembly["output_path"],
            "ledger_path": str(ledger.resolve()), "record": record}


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="run_v3_native_control")
    p.add_argument("--run-id", required=True)
    p.add_argument("--db", required=True)
    p.add_argument("--ledger", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--resume", action="store_true")
    p.add_argument("--recover-render-dir")
    p.add_argument("--native-sha256")
    p.add_argument("--reason")
    p.add_argument("--retry-qc", action="store_true")
    args = p.parse_args(argv)
    os.environ.setdefault("WANGP_VISION_BACKEND", "local")
    try:
        recovery = None
        if args.retry_qc and (not (args.reason or '').strip() or args.recover_render_dir or args.native_sha256):
            raise ValueError('--retry-qc requires --reason and excludes render-recovery flags')
        if not args.retry_qc and any((args.recover_render_dir, args.native_sha256, args.reason)):
            if not all((args.recover_render_dir, args.native_sha256,
                        (args.reason or '').strip())):
                raise ValueError('recovery requires directory, native SHA256 and reason')
            recovery = {'source_dir': str(Path(args.recover_render_dir).resolve()),
                        'native_sha256': args.native_sha256, 'reason': args.reason}
        result = run_control(
            run_id=args.run_id, db=Path(args.db).resolve(),
            ledger=Path(args.ledger).resolve(),
            output=Path(args.output).resolve(), resume=args.resume, recovery=recovery,
            retry_qc_reason=(args.reason if args.retry_qc else None))
    except Exception as exc:
        print(f"v3 native control refused: {type(exc).__name__}: {exc}",
              file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
