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
from collections.abc import Mapping
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import run_jobs  # noqa: E402
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


def run_bundle(bundle_path: str | Path, *, db_path: str | Path | None = None,
               ledger_path: str | Path | None = None,
               output_path: str | Path | None = None,
               host=None, vision_judge=None) -> dict:
    """Execute one acceptance bundle through repo-owned seams."""
    bundle_file = Path(bundle_path).expanduser().resolve()
    bundle = _load_bundle(bundle_file)
    premise = _premise(bundle)
    inputs = _normalize_inputs(bundle, premise, root=ROOT)
    run_id = str(bundle["run_id"])
    if not run_id.strip():
        raise AcceptanceBundleError("run_id must be non-empty")
    db = Path(db_path or ROOT / "datasets" / f"{run_id}.jobs.db").resolve()
    ledger = Path(ledger_path or ROOT / "datasets" / f"{run_id}.runs.jsonl").resolve()
    output = Path(output_path or ROOT / "datasets" / "runs" / "pull" /
                  run_id / "assembled.mp4").resolve()

    from services.director.run import DirectorRun
    from services.jobs.queue import JobQueue
    run = DirectorRun(run_id=run_id, premise=premise,
                      dataset_run_path=str(ledger))
    plan = run.plan(inputs["script"], audio_paths=inputs["audio"],
                    plate_paths=inputs["plates"],
                    media_manifest=inputs["media"],
                    recipe_name=bundle.get("recipe_name", "golden_v3"),
                    expected_cuts=bundle.get("expected_cuts", 6),
                    durations_s=bundle.get("durations_s"),
                    seed_override=bundle.get("seed", 904))
    queue = JobQueue(str(db))
    try:
        # Resolve credentials and host before submitting anything.  Missing
        # vision credentials must not leave a queue full of renderable jobs.
        host = host or run_jobs._default_host()
        judge = vision_judge or run_jobs._default_vision_judge(host=host)
        job_ids = run.submit(plan, queue)
        handled = run_jobs.drain_once(
            queue, host=host, vision_judge=judge)
        jobs = [queue.get(jid) for jid in job_ids]
        if any(job.state != "done" for job in jobs):
            states = {job.job_id: job.state for job in jobs}
            raise AcceptanceBundleError(
                f"acceptance drain did not complete all jobs: {states}")
        videos = [job.clips[0]["mp4"] for job in jobs]
        assembly = assemble_media(videos, str(output))
    finally:
        queue.close()

    from services.director.run_records import append_dataset_run
    completed = append_dataset_run(
        ledger, run_id=run_id, status="needs_review",
        payload={"premise_id": premise.id, "clip_count": len(job_ids),
                 "handled": handled, "assembly": assembly,
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
