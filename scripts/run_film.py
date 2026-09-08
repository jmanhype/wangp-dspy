"""run_film — the director entrypoint (PR feat/director-wiring).

    .venv/bin/python scripts/run_film.py --script film.txt \
        --plates plates/ --characters Grandma:S1:Sdescr Seth:S2:Sdescr \
        --whisper-map s4/.../whisper_map.json [--db jobs.db] [--dry-run]

Script format: one `SPEAKER: line` row per line; blank lines ignored.
Planning: ShortFilmPlanner under the DSPY_LLM sentinel when an LM is
wired (dspy.settings); otherwise deterministic beat-splitting — the
script lines ARE the beats, no LM needed. Both paths feed the SAME
plan_to_clips (proven job shape) and the SAME executor the smoke runs
used (scripts/run_jobs.build_executor — in-repo, not a /tmp wrapper).

The executor accepts a pre_render hook (phased QC kill/restart before
the render leg); the llama-kill implementation itself is ops config,
out of scope here.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class RunFilmError(ValueError):
    """Typed run_film rejection (bad script/plates/roster)."""


def parse_script(path) -> List[Dict[str, str]]:
    """`SPEAKER: line` rows; blank lines and #-comments ignored."""
    rows: List[Dict[str, str]] = []
    text = Path(path).read_text(encoding="utf-8")
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            raise RunFilmError(
                f"script row has no SPEAKER: prefix: {line!r}")
        speaker, _, spoken = line.partition(":")
        speaker = speaker.strip()
        spoken = spoken.strip()
        if not speaker or not spoken:
            raise RunFilmError(
                f"script row needs nonempty speaker and line: {line!r}")
        rows.append({"speaker": speaker, "text": spoken})
    if not rows:
        raise RunFilmError("script produced no rows")
    return rows


def plates_from_dir(plates_dir, character_names) -> Dict[str, str]:
    """Discover plates: <dir>/anchor.<ext> + <dir>/<Name>.<ext>."""
    d = Path(plates_dir)
    plates: Dict[str, str] = {}
    anchors = sorted(d.glob("anchor.*"))
    if anchors:
        plates["anchor"] = str(anchors[0])
    for name in character_names:
        hits = sorted(d.glob(f"{name}.*"))
        if hits:
            plates[name] = str(hits[0])
    return plates


def plan_beats(script_rows, characters, lm=None):
    """Planning step. LM path (opt-in: pass DSPY_LLM): ShortFilmPlanner
    under the ambient dspy LM. Sentinel-safe default: deterministic
    beat-splitting — the script lines become the beats directly, no LM
    needed (and immune to ambient-LM leakage from other tests/callers).
    """
    from services.director.planners.short_film import DSPY_LLM
    if lm is not DSPY_LLM:
        # deterministic beat-splitting: rows ARE the beats
        return [dict(r) for r in script_rows]
    import dspy
    if dspy.settings.get("lm", None) is None:
        return [dict(r) for r in script_rows]  # sentinel-safe fallback
    from services.director.planners.short_film import (
        PlannerError, ShortFilmPlanner)
    planner = ShortFilmPlanner(llm=DSPY_LLM)
    script_text = "\n".join(f"{r['speaker']}: {r['text']}"
                            for r in script_rows)
    try:
        doc = planner._call(
            "pass1", "", json.dumps({"script": script_text}),
            fields={"script": script_text, "characters": json.dumps(
                [{"name": c["name"], "description": c["description"]}
                 for c in characters])},
            predictor=planner.pass_beats)
        beats = doc.get("beats", [])
        rows = [{"speaker": b["speaker"], "text": b["text"]}
                for b in beats]
        if not rows:
            raise PlannerError("pass1 produced no beats")
        return rows
    except PlannerError:
        raise
    except Exception as e:
        raise RunFilmError(f"planner pass1 failed: {e}") from e


def _plan_with_lm(rows, characters, *, lm=None):
    """Plan under an ambient dspy LM when one is given.

    A real dspy.LM (e.g. build_lm("glm")) is installed via
    dspy.settings.context so the ShortFilmPlanner Signature path
    (DSPY_LLM sentinel) picks it up for pass1. None keeps the
    deterministic beat-splitting default.
    """
    if lm is None:
        return plan_beats(rows, characters, lm=None)
    import dspy
    from services.director.planners.short_film import DSPY_LLM
    with dspy.settings.context(lm=lm):
        return plan_beats(rows, characters, lm=DSPY_LLM)


LM_CHOICES = ("none", "glm")


def build_lm(which: str):
    """Construct the planner LM for a --lm choice.

    "glm": z.ai GLM-5.3 through the OpenAI-compatible endpoint
    (operator ruling: GLM for creative gen; ModelScope NEVER).
    Returns None for "none" (deterministic beat-splitting).

    Raises ValueError for unknown choices so argparse errors stay
    typed and testable.
    """
    if which == "none":
        return None
    if which == "glm":
        import dspy
        import os
        api_key = os.environ.get("ZAI_API_KEY", "")
        if not api_key:
            raise RunFilmError(
                "--lm glm requires ZAI_API_KEY in the environment")
        # LIVE FIX (2026-09-03, GLM-directed film run): the card's
        # nominal base https://api.z.ai/v1 404s with the operator's
        # key; the SAME key returns 200 on the coding-paas v4 route.
        # Divergence documented here deliberately.
        return dspy.LM(
            "openai/glm-5.3",
            api_base="https://api.z.ai/api/coding/paas/v4",
            api_key=api_key,
            model_type="chat",
        )
    raise ValueError(f"unknown --lm choice: {which!r}")


def run_film(script_file, plates_dir, *, characters, whisper_map="",
             durations=None, audio_paths=None, db_path=None,
             host=None, pre_render=None, lm=None, dry_run=False,
             run_ledger_path=None, dataset_run_path=None,
             premise_id=None, continuation_mode=False,
             whisper_transcriber=None, vision_judge=None):
    """Director entrypoint: script + plates -> clips (-> jobs -> drain).

    dry_run=True stops after plan_to_clips: emits the N job clips with
    NO queue submission and NO host calls. Otherwise builds the SAME
    executor the smoke runs used (scripts.run_jobs.build_executor with
    the pre_render hook seam), submits chain jobs to the durable queue
    and drains until all clips are done (auto-advance included).
    """
    from services.director.run_ledger import (
        repository_identity, write_run_ledger)
    from services.director.run_records import append_dataset_run
    from services.director.wiring import plan_to_clips

    # Finding 0: every run is attributed before planning or host work.  A
    # caller may supply an explicit ledger path; otherwise a production
    # db_path gets a sibling ledger.  Dry runs without a db path stay
    # side-effect free (the caller can opt in with run_ledger_path).
    ledger_path = run_ledger_path
    if ledger_path is None and db_path is not None:
        ledger_path = str(Path(db_path).resolve().parent / "run_ledger.json")
    identity = repository_identity()
    run_id = (Path(ledger_path).resolve().parent.name
              if ledger_path is not None else "dry-run")
    if ledger_path is not None:
        write_run_ledger(
            ledger_path,
            run_id=run_id,
            identity=identity,
            status="started",
            extra={"script": str(Path(script_file).resolve()),
                   "plates_dir": str(Path(plates_dir).resolve()),
                   "dry_run": bool(dry_run)},
        )
    if dataset_run_path is not None:
        append_dataset_run(
            dataset_run_path, run_id=run_id, status="started",
            payload={"premise_id": premise_id,
                     "script": str(Path(script_file).resolve()),
                     "dry_run": bool(dry_run)})

    rows = parse_script(script_file)
    names = [c["name"] for c in characters]
    plates = plates_from_dir(plates_dir, names)
    missing = [n for n in names + ["anchor"] if n not in plates]
    if missing:
        raise RunFilmError(
            f"missing plate(s) in {plates_dir}: {missing} — expected "
            "anchor.* plus one plate per character")
    beats = _plan_with_lm(rows, characters, lm=lm)
    if continuation_mode:
        from services.chain.controller import (
            build_chain_plan, emit_render_manifest,
        )
        if durations is None:
            durations = [2.0] * len(beats)
        if audio_paths is None:
            raise RunFilmError(
                "continuation_mode requires six existing single-speaker "
                "audio_paths; VibeVoice generation is not available")
        ordered_plates = [plates["anchor"]] + [
            plates[c["name"]] for c in characters]
        try:
            chain = build_chain_plan(
                beats, characters, durations, audio_paths=audio_paths,
                continuation_mode=True)
            clips = emit_render_manifest(chain, plate_paths=ordered_plates)
        except Exception as exc:
            raise RunFilmError(
                f"strict continuation plan rejected: {exc}") from exc
    else:
        clips = plan_to_clips(
            beats, characters, plates, durations=durations,
            audio_paths=audio_paths, whisper_map=whisper_map,
            run_dir=(str(Path(db_path).resolve().parent) if db_path
                     else str(Path(script_file).resolve().parent)
                     if audio_paths is None else None))
    if ledger_path is not None:
        write_run_ledger(
            ledger_path,
            run_id=run_id,
            identity=identity,
            status="planned",
            extra={"script": str(Path(script_file).resolve()),
                   "plates_dir": str(Path(plates_dir).resolve()),
                   "dry_run": bool(dry_run),
                   "clip_count": len(clips), "premise_id": premise_id},
        )
    if dataset_run_path is not None:
        append_dataset_run(
            dataset_run_path, run_id=run_id, status="planned",
            payload={"premise_id": premise_id, "clip_count": len(clips)})
    if dry_run:
        return clips

    from services.jobs.queue import JobQueue
    import scripts.run_jobs as rj

    host = host or rj._default_host()
    if vision_judge is None:
        # Production renders must carry a real visual judge before the first
        # job is submitted.  Tests/operators can still inject a deterministic
        # callable explicitly; the selected backend fails before GPU work.
        vision_judge = rj._default_vision_judge(host=host)

    q = JobQueue(str(db_path or "jobs.db"))
    try:
        prev = None
        for c in clips:
            clip = dict(c)
            clip["needs"] = prev
            prev = q.submit(plan_ref="film", clips=[clip])
        hook = pre_render if pre_render is not None \
            else rj._pre_render_default(host)
        _drain(q, host, pre_render=hook,
               whisper_transcriber=whisper_transcriber,
               vision_judge=vision_judge)
        if ledger_path is not None:
            write_run_ledger(
                ledger_path,
                run_id=run_id,
                identity=identity,
                status="completed",
                extra={"script": str(Path(script_file).resolve()),
                       "plates_dir": str(Path(plates_dir).resolve()),
                       "dry_run": False,
                       "clip_count": len(clips), "premise_id": premise_id},
            )
            if dataset_run_path is not None:
                append_dataset_run(
                    dataset_run_path, run_id=run_id, status="completed",
                    payload={"premise_id": premise_id,
                             "clip_count": len(clips)})
        return clips
    finally:
        q.close()


def _drain(queue, host, pre_render=None, whisper_transcriber=None,
           vision_judge=None) -> List[str]:
    """Drain loop: run admissible jobs until none remain; after each
    DONE chain job, advance the chain (extract last frame + patch the
    next clip's image_refs[0]) so the dependent becomes admissible."""
    from services.director.wiring import advance_chain

    handled = []
    while True:
        jid = rj_next_admissible(queue)
        if jid is None:
            return handled
        from scripts.run_jobs import build_executor
        ex = build_executor(
            queue, host=host, pre_render=pre_render,
            whisper_transcriber=whisper_transcriber,
            vision_judge=vision_judge)
        ex.run_once()
        handled.append(jid)
        fresh = queue.get(jid)
        if fresh.state == "done":
            advance_chain(queue, host, jid)


def rj_next_admissible(queue):
    from services.jobs.queue import next_admissible
    return next_admissible(queue)


def main(argv=None):
    p = argparse.ArgumentParser(
        prog="run_film", description="Director entrypoint: script -> "
        "plan -> chain clips -> renders.")
    p.add_argument("--script", required=True)
    p.add_argument("--plates", required=True)
    p.add_argument("--characters", required=True, nargs="+",
                   help="NAME:SN_TAG:DESCRIPTION per character")
    p.add_argument("--whisper-map", default="")
    p.add_argument("--db", default="jobs.db")
    p.add_argument("--lm", default="none", choices=LM_CHOICES,
                   help="planner LM: none (deterministic beats) or glm "
                        "(z.ai GLM-5.3; needs ZAI_API_KEY)")
    p.add_argument("--dry-run", action="store_true",
                   help="emit the job clips; no queue, no host calls")
    p.add_argument("--continuation", action="store_true",
                   help="strict six-cut Ref2VA continuation (requires turn wavs)")
    args = p.parse_args(argv)

    characters = []
    for spec in args.characters:
        parts = spec.split(":", 2)
        if len(parts) != 3:
            raise SystemExit(
                f"--characters entries need NAME:SN_TAG:DESCRIPTION, "
                f"got {spec!r}")
        characters.append({"name": parts[0], "sn_tag": parts[1],
                           "description": parts[2]})
    clips = run_film(args.script, args.plates,
                     characters=characters,
                     whisper_map=args.whisper_map,
                     lm=build_lm(args.lm),
                     db_path=None if args.dry_run else args.db,
                     dry_run=args.dry_run,
                     continuation_mode=args.continuation)
    print(json.dumps(
        {"clips": len(clips), "dry_run": args.dry_run}, indent=2))
    for c in clips:
        print(f"clip {c['clip_index']:04d}: speaker={c['speaker']} "
              f"frames={c['frames']} re_anchor={c['chain']['re_anchor']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
