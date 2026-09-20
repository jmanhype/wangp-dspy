#!/usr/bin/env python3
"""Turn a typed content brief into a no-GPU run_film dry-run plan."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from predict.content_brief import (  # noqa: E402
    ContentBriefError,
    build_run_film_inputs,
    load_content_brief,
)
from scripts.run_film import run_film  # noqa: E402
from services.director.run_ledger import repository_identity  # noqa: E402


def _canonical_write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False, default=str,
    ).encode("utf-8")
    path.write_bytes(encoded + b"\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="run_content_brief",
        description="Validate a content brief and emit a no-GPU run_film dry-run plan.",
    )
    parser.add_argument("--brief", required=True, type=Path)
    parser.add_argument("--plates", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--run-dir", type=Path)
    args = parser.parse_args(argv)

    output = args.output.expanduser().resolve()
    run_dir = (
        args.run_dir.expanduser().resolve()
        if args.run_dir is not None
        else output.parent / "run"
    )
    brief = load_content_brief(args.brief)
    inputs = build_run_film_inputs(
        brief, args.plates, run_dir=run_dir
    )
    clips = run_film(
        inputs["script_path"],
        args.plates,
        characters=inputs["characters"],
        durations=inputs["durations"],
        audio_paths=inputs["audio_paths"],
        db_path=inputs["run_dir"] / "jobs.db",
        run_ledger_path=inputs["run_dir"] / "run_ledger.json",
        premise_id=brief.title,
        dry_run=True,
    )
    identity = repository_identity(ROOT)
    planned_duration = sum(
        float(clip.get("guide_duration_s", clip.get("shot_duration_s", 0.0)))
        for clip in clips
    )
    payload = {
        "schema_version": "wangp-dspy.content-plan/v1",
        "brief_hash": brief.brief_hash,
        "repository": identity,
        "input": {
            "brief": str(brief.source_path),
            "plates_dir": str(Path(args.plates).expanduser().resolve()),
            "script": str(inputs["script_path"]),
            "audio_paths": inputs["audio_paths"],
            "plates": inputs["plates"],
        },
        "title": brief.title,
        "premise": brief.premise,
        "characters": inputs["characters"],
        "dialogue": [line.mapping() for line in brief.dialogue],
        "clips": clips,
        "summary": {
            "clip_count": len(clips),
            "speakers": [line.speaker for line in brief.dialogue],
            "planned_duration_s": round(planned_duration, 6),
            "dry_run": True,
            "gpu_work": False,
            "queue_submitted": False,
        },
    }
    _canonical_write(output, payload)
    print(
        f"brief={brief.brief_hash} clips={len(clips)} "
        f"plan={output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
