"""Repo-owned acceptance bundle runner.

Consumes the committed ``staging_r2.json`` shape and performs the complete
production path without an ad-hoc wrapper: resolve premise -> DirectorRun
plan -> durable queue submit -> run_jobs drain -> repo-owned media assembly.
The command refuses incomplete bundles before a queue is created.
"""
from __future__ import annotations

import argparse
import json
import sys
import os
from collections.abc import Mapping
from pathlib import Path
from pathlib import PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import run_jobs  # noqa: E402
from services.director.run_ledger import repository_identity  # noqa: E402
from services.director.wiring import assemble_media  # noqa: E402


class AcceptanceBundleError(ValueError):
    """Typed rejection of an incomplete or unresolvable bundle."""


def _path(value, *, root: Path, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AcceptanceBundleError(f"{label}: non-empty path required")
    p = Path(value).expanduser()
    if not p.is_absolute():
        p = root / p
    return str(p.resolve())


def _load_bundle(path: Path) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AcceptanceBundleError(f"bundle unreadable: {path}: {exc}") from exc
    if not isinstance(payload, Mapping):
        raise AcceptanceBundleError("bundle root must be an object")
    required = {"run_id", "media_manifest", "script_lines",
                "audio_paths", "plate_paths"}
    missing = sorted(required - set(payload))
    if missing:
        raise AcceptanceBundleError(
            f"bundle missing required field(s): {missing}")
    return dict(payload)


def _premise(bundle: Mapping):
    from services.director.premises import Premise, resolve_premise

    raw = bundle.get("premise")
    if isinstance(raw, Mapping):
        try:
            return Premise(
                id=str(raw["id"]), title=str(raw["title"]),
                logline=str(raw["logline"]),
                characters=tuple(dict(c) for c in raw["characters"]),
                style_ref=str(raw.get("style_ref", "")).strip(),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise AcceptanceBundleError(
                f"bundle premise is malformed: {exc}") from exc
    premise_id = (bundle.get("media_manifest") or {}).get("premise_id")
    try:
        return resolve_premise(str(premise_id))
    except Exception as exc:
        raise AcceptanceBundleError(
            f"premise {premise_id!r} is not registered in the Lost Futures "
            "index; add bundle.premise (with character descriptions) or "
            "register it before queueing") from exc


def _speaker_lookup(premise):
    by_name = {str(c["name"]): c for c in premise.characters}
    by_fold = {name.casefold(): name for name in by_name}
    by_sn = {str(c["sn_tag"]): str(c["name"])
             for c in premise.characters}
    return by_name, by_fold, by_sn


def _canonical_speaker(value, *, by_name, by_fold, by_sn, label):
    if not isinstance(value, str) or not value.strip():
        raise AcceptanceBundleError(f"{label}: speaker required")
    if value in by_name:
        return value
    if value.casefold() in by_fold:
        return by_fold[value.casefold()]
    if value in by_sn:
        return by_sn[value]
    raise AcceptanceBundleError(
        f"{label}: speaker {value!r} is not in premise roster")


def _normalize_inputs(bundle: Mapping, premise, *, root: Path) -> dict:
    try:
        script = list(bundle["script_lines"])
        for line_index, line in enumerate(script, 1):
            if not isinstance(line, Mapping):
                raise AcceptanceBundleError(
                    f"script_lines[{line_index}]: each entry must be an object")
        audio = [_path(p, root=root, label=f"audio_paths[{i}]")
                 for i, p in enumerate(bundle["audio_paths"], 1)]
        plates_raw = bundle["plate_paths"]
        plates = []
        for i, item in enumerate(plates_raw, 1):
            if isinstance(item, (list, tuple)):
                plates.append([_path(p, root=root,
                                     label=f"plate_paths[{i}][{j}]")
                               for j, p in enumerate(item)])
            else:
                plates.append(_path(item, root=root,
                                    label=f"plate_paths[{i}]"))
        media = dict(bundle["media_manifest"])
    except (KeyError, TypeError) as exc:
        raise AcceptanceBundleError(f"bundle media fields malformed: {exc}") from exc

    by_name, by_fold, by_sn = _speaker_lookup(premise)
    raw_plates = media.get("plates")
    if not isinstance(raw_plates, Mapping):
        raise AcceptanceBundleError(
            "media_manifest.plates must map anchor and character identities")
    anchor = raw_plates.get("anchor")
    canonical_plates = {"anchor": _path(anchor, root=root,
                                         label="media_manifest.plates.anchor")}
    for name in by_name:
        value = raw_plates.get(name)
        if value is None:
            value = next((v for k, v in raw_plates.items()
                          if isinstance(k, str) and k.casefold() == name.casefold()),
                         None)
        if value is None:
            value = raw_plates.get(next(
                (str(c["sn_tag"]) for c in premise.characters
                 if str(c["name"]) == name), ""))
        canonical_plates[name] = _path(
            value, root=root, label=f"media_manifest.plates.{name}")

    raw_audio = media.get("audio")
    if not isinstance(raw_audio, (list, tuple)):
        raise AcceptanceBundleError(
            "media_manifest.audio must contain one {path, speaker} per turn")
    canonical_audio = []
    for i, entry in enumerate(raw_audio, 1):
        if not isinstance(entry, Mapping):
            raise AcceptanceBundleError(
                f"media_manifest.audio[{i}] must be an object")
        canonical_audio.append({
            "path": _path(entry.get("path"), root=root,
                           label=f"media_manifest.audio[{i}].path"),
            "speaker": _canonical_speaker(
                entry.get("speaker"), by_name=by_name, by_fold=by_fold,
                by_sn=by_sn, label=f"media_manifest.audio[{i}]"),
        })
    canonical_media = {
        "premise_id": str(media.get("premise_id")),
        "style_ref": str(media.get("style_ref", "") or "").strip(),
        "plates": canonical_plates,
        "audio": canonical_audio,
    }
    # DirectorRun's guard remains the single authority for the final shape;
    # this normalization only makes bundle paths/names deterministic.
    if canonical_media["premise_id"] != premise.id:
        raise AcceptanceBundleError(
            f"bundle premise_id {canonical_media['premise_id']!r} does not "
            f"resolve to {premise.id!r}")
    return {"script": script, "audio": audio, "plates": plates,
            "media": canonical_media}


def _require_completed_qc_evidence(clip: Mapping, *,
                                   producer_root: Path) -> None:
    from services.jobs.queue import validate_completed_qc_verdict

    verdict = clip.get("qc_verdict")
    try:
        validate_completed_qc_verdict(verdict)
    except ValueError as exc:
        raise AcceptanceBundleError(
            f"completed_prefix QC verdict rejected: {exc}") from exc
    evidence = verdict.get("path")
    if isinstance(evidence, str):
        evidence_path = Path(evidence)
        if not evidence_path.is_absolute():
            evidence_path = producer_root / evidence_path
        evidence_path = evidence_path.resolve()
        if not evidence_path.is_file():
            raise AcceptanceBundleError(
                f"completed_prefix QC evidence does not exist: {evidence!r}")
        return


def _lf002_ffmpeg_config() -> tuple[str, str]:
    """Resolve the explicit local ffmpeg used by the pinned LF002 pair."""
    executable = os.environ.get("WANGP_LF002_FFMPEG", "").strip()
    expected = os.environ.get(
        "WANGP_LF002_FFMPEG_EXPECTED", "Lavf62.3.100").strip()
    if not executable:
        raise AcceptanceBundleError(
            "LF002 golden assembly requires WANGP_LF002_FFMPEG to name the "
            "explicit local executable that matches the pinned ffmpeg build")
    if not expected:
        raise AcceptanceBundleError(
            "WANGP_LF002_FFMPEG_EXPECTED must be nonempty")
    path = Path(executable).expanduser()
    if (not path.is_absolute() or not path.is_file()
            or not os.access(path, os.X_OK)):
        raise AcceptanceBundleError(
            f"WANGP_LF002_FFMPEG is not an executable absolute path: "
            f"{executable!r}")
    return str(path), expected


def _prepare_completed_prefix(plan, prefix: Mapping,
                              *, root: Path) -> Mapping:
    """Validate and materialize one verified completed cut without staging.

    A completed-prefix replay is evidence reuse, not silent artifact adoption.
    The source job must be done, its effective renderer fingerprint must match
    the newly planned cut, native raw/final hashes must match, and the caller
    must pin the expected SHA-256. The successor still renders through the
    normal queue and gains its chain frame through ``advance_chain``.
    """
    from services.jobs.queue import JobQueue, effective_render_fingerprint

    index = prefix.get("clip_index", 1)
    if isinstance(index, bool) or not isinstance(index, int) or index != 1:
        raise AcceptanceBundleError(
            "completed_prefix.clip_index must be integer 1")
    if len(plan.clips) < 2:
        raise AcceptanceBundleError(
            "completed_prefix requires a dependent successor clip")
    db_path = _path(prefix.get("jobs_db"), root=root,
                    label="completed_prefix.jobs_db")
    job_id = prefix.get("job_id")
    if not isinstance(job_id, str) or not job_id.strip():
        raise AcceptanceBundleError("completed_prefix.job_id is required")
    expected = prefix.get("expected_sha256")
    if (not isinstance(expected, str)
            or len(expected) != 64):
        raise AcceptanceBundleError(
            "completed_prefix.expected_sha256 must be a SHA-256 hex digest")

    source_queue = JobQueue(db_path)
    try:
        try:
            source = source_queue.get(job_id)
        except Exception as exc:
            raise AcceptanceBundleError(
                f"completed_prefix job unreadable: {exc}") from exc
        if source.state != "done":
            raise AcceptanceBundleError(
                f"completed_prefix job is {source.state!r}, not done")
        matches = [c for c in source.clips
                   if int(c.get("clip_index", -1)) == index]
        if len(matches) != 1:
            raise AcceptanceBundleError(
                "completed_prefix job must contain exactly one matching clip")
        old = matches[0]
        if old.get("status") != "done":
            raise AcceptanceBundleError(
                "completed_prefix source clip is "
                f"{old.get('status')!r}, not done")
        _require_completed_qc_evidence(
            old, producer_root=Path(db_path).parent.parent.resolve())
    finally:
        source_queue.close()

    planned = dict(plan.clips[index - 1])
    old_fingerprint = effective_render_fingerprint(old)
    planned_fingerprint = effective_render_fingerprint(planned)
    if old_fingerprint != planned_fingerprint:
        raise AcceptanceBundleError(
            "completed_prefix effective renderer inputs differ from the new "
            f"plan ({old_fingerprint[:12]}… != {planned_fingerprint[:12]}…)")

    final = Path(str(old.get("mp4") or ""))
    raw = final.with_name("raw.mp4")
    log = Path(str(old.get("log") or ""))
    if not final.is_file() or not raw.is_file() or not log.is_file():
        raise AcceptanceBundleError(
            "completed_prefix log/raw/final artifacts must exist on disk")
    import hashlib
    final_hash = hashlib.sha256(final.read_bytes()).hexdigest()
    raw_hash = hashlib.sha256(raw.read_bytes()).hexdigest()
    if final_hash != expected or raw_hash != expected:
        raise AcceptanceBundleError(
            "completed_prefix SHA-256 mismatch or raw/final divergence")
    try:
        runtime = json.loads(
            (final.parent / "runtime-evidence.json").read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise AcceptanceBundleError(
            f"completed_prefix runtime evidence unreadable: {exc}") from exc
    if (runtime.get("runtime", {}).get("audio_carrier") != "native_h3"
            or runtime.get("runtime", {}).get("native_preserved") is not True
            or runtime.get("raw_render_hash") != raw_hash
            or runtime.get("remux_hash") != final_hash):
        raise AcceptanceBundleError(
            "completed_prefix is not verified native H3 A/V evidence")

    completed = dict(planned)
    completed.update({
        "status": "done",
        "log": str(log.resolve()),
        "mp4": str(final.resolve()),
        "qc_verdict": old.get("qc_verdict"),
        "completed_prefix_source": {
            "jobs_db": db_path,
            "job_id": job_id,
            "clip_index": index,
            "sha256": final_hash,
        },
    })
    return completed


def _submit_prepared_completed_prefix(plan, queue,
                                      completed: Mapping) -> list[str]:
    """Insert a validated completed prefix and chain every dependent."""
    prefix_job = queue.submit_completed(
        plan_ref=plan.run_id, clips=[dict(completed)])
    ids = [prefix_job]
    previous_job = prefix_job
    index = int(completed["clip_index"])
    for clip in plan.clips[index:]:
        job = dict(clip)
        job["needs"] = previous_job
        job_id = queue.submit(plan_ref=plan.run_id, clips=[job])
        ids.append(job_id)
        previous_job = job_id
    return ids


def _submit_completed_prefix(plan, queue, prefix: Mapping,
                             *, root: Path) -> list[str]:
    """Compatibility wrapper: validate, then submit a completed prefix."""
    completed = _prepare_completed_prefix(plan, prefix, root=root)
    return _submit_prepared_completed_prefix(plan, queue, completed)


def _stage_media_inputs(inputs: Mapping, host) -> None:
    """Publish every local bundle input through the RenderHost contract."""
    mapper = getattr(host, "map_asset", None)
    makedirs = getattr(host, "makedirs", None)
    pusher = getattr(host, "push_asset", None)
    if not all(callable(value) for value in (mapper, makedirs, pusher)):
        raise AcceptanceBundleError(
            "acceptance staging requires RenderHost map_asset/makedirs/"
            "push_asset; refusing direct transport")
    paths = {str(path) for path in inputs["media"]["plates"].values()}
    paths.update(str(entry["path"]) for entry in inputs["media"]["audio"])
    for item in inputs["plates"]:
        values = item if isinstance(item, (list, tuple)) else (item,)
        paths.update(str(path) for path in values)
    missing = sorted(path for path in paths if not Path(path).is_file())
    if missing:
        raise AcceptanceBundleError(
            f"acceptance bundle inputs missing locally: {missing}")
    for local in sorted(paths):
        try:
            remote = mapper(local)
            remote_parent = str(PurePosixPath(remote).parent)
            if remote_parent not in {"", "."}:
                makedirs(remote_parent)
            pusher(local)
        except Exception as exc:
            raise AcceptanceBundleError(
                f"RenderHost staging failed for {local}: {exc}") from exc


def run_bundle(bundle_path: str | Path, *, db_path: str | Path | None = None,
               ledger_path: str | Path | None = None,
               output_path: str | Path | None = None,
               host=None, vision_judge=None) -> dict:
    """Execute one acceptance bundle through repo-owned seams."""
    bundle_file = Path(bundle_path).expanduser().resolve()
    bundle = _load_bundle(bundle_file)
    identity = repository_identity(ROOT)
    dirty_run_reason = None
    if identity.get("dirty_tree", True):
        if os.environ.get("WANGP_ALLOW_DIRTY_RUN") != "1":
            raise AcceptanceBundleError(
                "acceptance requires a clean repository tree; set "
                "WANGP_ALLOW_DIRTY_RUN=1 and WANGP_DIRTY_RUN_REASON for "
                "an explicitly non-release experiment")
        dirty_run_reason = str(
            os.environ.get("WANGP_DIRTY_RUN_REASON", "")).strip()
        if not dirty_run_reason:
            raise AcceptanceBundleError(
                "dirty acceptance runs require WANGP_DIRTY_RUN_REASON")
    premise = _premise(bundle)
    inputs = _normalize_inputs(bundle, premise, root=ROOT)
    golden_canary_spec = bundle.get("golden_canary")
    if golden_canary_spec is not None and (
            not isinstance(golden_canary_spec, Mapping)
            or golden_canary_spec.get("recipe_version")
            != "lf002-archive-of-rain-20260916-seed905-native-v1"):
        raise AcceptanceBundleError(
            "golden_canary.recipe_version must identify the pinned LF002 "
            "native control")
    durations_s = bundle.get("durations_s")
    if durations_s is not None:
        if not isinstance(durations_s, (list, tuple)):
            raise AcceptanceBundleError(
                "durations_s: must be a list or tuple when provided")
        for duration_index, value in enumerate(durations_s, 1):
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise AcceptanceBundleError(
                    f"durations_s[{duration_index}]: numeric value required")
    run_id = str(bundle["run_id"])
    if not run_id.strip():
        raise AcceptanceBundleError("run_id must be non-empty")
    db = Path(db_path or ROOT / "datasets" / f"{run_id}.jobs.db").resolve()
    ledger = Path(ledger_path or ROOT / "datasets" / f"{run_id}.runs.jsonl").resolve()
    output = Path(output_path or ROOT / "datasets" / "runs" / "pull" /
                  run_id / "assembled.mp4").resolve()

    from services.director.run import DirectorRun, DirectorRunError
    from services.jobs.queue import JobQueue
    run = DirectorRun(run_id=run_id, premise=premise,
                      dataset_run_path=str(ledger))
    try:
        plan = run.plan(inputs["script"], audio_paths=inputs["audio"],
                        plate_paths=inputs["plates"],
                        media_manifest=inputs["media"],
                        recipe_name=bundle.get("recipe_name", "golden_v3"),
                        expected_cuts=bundle.get("expected_cuts", 6),
                        durations_s=durations_s,
                        seed_override=bundle.get("seed", 904),
                        emit_record=False)
    except DirectorRunError as exc:
        raise AcceptanceBundleError(f"bundle plan rejected: {exc}") from exc

    prepared_prefix = None
    prefix = bundle.get("completed_prefix")
    if prefix is not None:
        if not isinstance(prefix, Mapping):
            raise AcceptanceBundleError(
                "completed_prefix must be an object")
        prepared_prefix = _prepare_completed_prefix(
            plan, prefix, root=ROOT)

    # Complete pure planning before remote staging, but stage before creating
    # a renderable queue. The planned ledger is emitted only after staging.
    host = host or run_jobs._default_host()
    judge = vision_judge or run_jobs._default_vision_judge(host=host)
    _stage_media_inputs(inputs, host)
    run.emit_plan_record(plan, durations_s=bundle.get("durations_s"))
    queue = JobQueue(str(db))
    try:
        # Credentials and input staging have already succeeded; queue only
        # the fully resolved plan.
        if prepared_prefix is None:
            job_ids = run.submit(plan, queue)
        else:
            job_ids = _submit_prepared_completed_prefix(
                plan, queue, prepared_prefix)
            from services.director.wiring import advance_chain
            advance_chain(queue, host, job_ids[0])
        handled = run_jobs.drain_once(
            queue, host=host, vision_judge=judge)
        jobs = [queue.get(jid) for jid in job_ids]
        if any(job.state != "done" for job in jobs):
            states = {job.job_id: job.state for job in jobs}
            raise AcceptanceBundleError(
                f"acceptance drain did not complete all jobs: {states}")
        videos = [job.clips[0]["mp4"] for job in jobs]
        assembly_videos = videos
        assembly_host = None
        ffmpeg_executable = "ffmpeg"
        expected_ffmpeg_version = None
        if golden_canary_spec is not None:
            # The pinned LF002 pair is a byte-exact local ffmpeg derivative:
            # assemble sibling native raw artifacts with the same local ffmpeg
            # environment that produced the operator-accepted control. Remote
            # Linux ffmpeg produces a different muxer/encoder container even
            # from byte-identical cuts.
            assembly_videos = [
                str(Path(video).with_name("raw.mp4"))
                for video in videos
            ]
            assembly_host = None
            ffmpeg_executable, expected_ffmpeg_version = (
                _lf002_ffmpeg_config())
        assembly = assemble_media(
            assembly_videos, str(output), host=assembly_host,
            ffmpeg_executable=ffmpeg_executable,
            expected_ffmpeg_version=expected_ffmpeg_version)
        golden_canary = None
        if golden_canary_spec is not None:
            if len(jobs) < 2:
                raise AcceptanceBundleError(
                    "LF002 golden canary requires two completed cuts")
            from predict import lf002_canary
            try:
                golden_canary = lf002_canary.verify_lf002_canary(
                    cut1=str(Path(jobs[0].clips[0]["mp4"]).with_name(
                        "raw.mp4")),
                    cut2=str(Path(jobs[1].clips[0]["mp4"]).with_name(
                        "raw.mp4")),
                    pair=str(output),
                    chain=str(jobs[1].clips[0].get("image_start")),
                    report_path=str(output.parent / "lf002-canary.json"))
            except lf002_canary.LF002CanaryError as exc:
                raise AcceptanceBundleError(
                    f"LF002 golden canary rejected the run: {exc}") from exc
    finally:
        queue.close()

    from services.director.run_records import append_dataset_run
    completed = append_dataset_run(
        ledger, run_id=run_id, status="needs_review",
        payload={"premise_id": premise.id, "clip_count": len(job_ids),
                 "audio_carrier": "native_h3",
                 "handled": handled, "assembly": assembly,
                 "golden_canary": golden_canary,
                 "repository_provenance": identity,
                 "dirty_run_reason": dirty_run_reason,
                 "bundle": str(bundle_file),
                 "bundle_sha256": __import__("hashlib").sha256(
                     bundle_file.read_bytes()).hexdigest()})
    return {"run_id": run_id, "job_ids": job_ids,
            "output_path": assembly["output_path"],
            "ledger_path": str(ledger), "completed_record": completed}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="run_acceptance",
        description="Run a committed acceptance bundle through repo seams")
    parser.add_argument("--bundle", required=True)
    parser.add_argument("--db")
    parser.add_argument("--ledger")
    parser.add_argument("--output")
    args = parser.parse_args(argv)
    try:
        result = run_bundle(args.bundle, db_path=args.db,
                            ledger_path=args.ledger, output_path=args.output)
    except Exception as exc:
        print(f"acceptance refused: {type(exc).__name__}: {exc}",
              file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
