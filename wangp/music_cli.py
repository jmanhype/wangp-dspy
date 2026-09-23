"""The no-GPU ``wgp music`` planning, compilation, and comparison surface."""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

from pydantic import ValidationError

from predict.music_capabilities import (
    MusicCapabilityError,
    MusicMode,
    attach_manifest_model,
    load_music_model_manifest,
)
from services.music.song_compiler import (
    compile_music_request,
    enqueue_music_plan,
    reconstruct_music_database,
    write_score_artifact,
)
from wangp.diagnostics import FailureDiagnostic, render_diagnostic

EXIT_OK = 0
EXIT_INPUT = 2


def _error(exc: MusicCapabilityError, *, as_json: bool) -> int:
    diagnostic = FailureDiagnostic(
        code=exc.code,
        severity="error",
        title="Typed music request rejection",
        observed=exc.observed,
        why="Music planning requires complete immutable inputs and never proves generation.",
        remediation=exc.remediation,
        next_command=exc.next_command,
        metadata=exc.metadata,
    )
    if as_json:
        print(json.dumps({"diagnostics": [diagnostic.mapping()]}, sort_keys=True, separators=(",", ":")))
    else:
        print(render_diagnostic(diagnostic), file=sys.stderr)
    return EXIT_INPUT


def _load_request(path: str, models_path: str | None):
    if models_path is None:
        raise MusicCapabilityError(
            "MODEL_MANIFEST_MISSING",
            "music planning requires --models",
            "Supply an operator-recorded manifest; Wangp does not download models.",
        )
    request_path = Path(path).expanduser().resolve()
    payload = json.loads(request_path.read_text(encoding="utf-8"))
    return attach_manifest_model(payload, load_music_model_manifest(models_path))


def _mode_for(verb: str) -> MusicMode | None:
    return MusicMode.generate if verb in {"plan", "compile"} else MusicMode.style_adaptation


def _run_plan(args: argparse.Namespace, *, as_json: bool) -> int:
    expected_mode = _mode_for(args.music_verb)
    database = Path(args.db).expanduser().resolve() if args.db else None
    if args.music_verb == "compile" and database is None:
        raise MusicCapabilityError(
            "MUSIC_QUEUE_PATH_MISSING",
            "music compilation requires --db",
            "Supply a new SQLite path, or use wgp music plan/style without --db.",
        )
    request = _load_request(args.request, args.models)
    if expected_mode is not None and request.mode is not expected_mode:
        raise MusicCapabilityError(
            "MUSIC_MODE_MISMATCH",
            f"{args.music_verb} requires mode={expected_mode.value}, got {request.mode.value}",
            "Use wgp music plan/compile for generate and wgp music style for style_adaptation.",
        )
    plan = compile_music_request(request).mapping()
    if args.score_out is not None:
        write_score_artifact(plan, args.score_out)
    record_ids = None
    if database is not None:
        record_ids = enqueue_music_plan(plan, database)
        plan = dict(plan)
        plan["queue"] = {"database": str(database), "record_ids": record_ids, "executable_jobs": 0}
    if as_json:
        print(json.dumps(plan, sort_keys=True, separators=(",", ":")))
    else:
        summary = plan["summary"]
        print(
            f"operation={plan['operation']} tracks={plan['track_count']} "
            f"capability_status={plan['capability_status']}"
        )
        print(
            f"gpu_work={str(summary['gpu_work']).lower()} "
            f"training_executed={str(summary['training_executed']).lower()} "
            f"audio_created={str(summary['audio_created']).lower()} "
            f"host_contact={str(summary['host_contact']).lower()}"
        )
        if plan["operation"] == "style_adaptation":
            comparison = plan["tracks"][0]["style_adaptation"]["comparison"]
            print(
                f"comparison={comparison['mode']} "
                f"before_sha256={comparison['before']['sha256']} "
                "after_status=planned aesthetic_verdict=none"
            )
        if record_ids is not None:
            print(f"records={','.join(record_ids)}")
    return EXIT_OK


def _run_music(args: argparse.Namespace) -> int:
    as_json = bool(args.json)
    if args.music_verb == "compare":
        try:
            records = reconstruct_music_database(args.db)
        except MusicCapabilityError as exc:
            return _error(exc, as_json=as_json)
        except (OSError, KeyError, TypeError, ValueError, ValidationError, sqlite3.Error) as exc:
            return _error(
                MusicCapabilityError(
                    "MUSIC_RECONSTRUCTION_INVALID",
                    f"cannot reconstruct database {args.db}: {exc}",
                    "Use a database emitted by wgp music compile.",
                    next_command="wgp music compare --db <plan.db> --json",
                ),
                as_json=as_json,
            )
        payload = {
            "schema_version": "wangp-dspy.music-reconstruction/v1",
            "records": records,
            "all_match": all(item["match"] for item in records),
            "hidden_mutation": any(item["hidden_mutation"] for item in records),
        }
        if as_json:
            print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
        else:
            print(
                f"records={len(records)} all_match={str(payload['all_match']).lower()} "
                f"hidden_mutation={str(payload['hidden_mutation']).lower()}"
            )
        return EXIT_OK if payload["all_match"] else EXIT_INPUT
    try:
        return _run_plan(args, as_json=as_json)
    except MusicCapabilityError as exc:
        return _error(exc, as_json=as_json)
    except ValidationError as exc:
        return _error(
            MusicCapabilityError(
                "MUSIC_REQUEST_INVALID",
                f"request validation failed: {exc.error_count()} field errors",
                "Fix the typed request fields, then rerun the deterministic no-GPU music plan.",
            ),
            as_json=as_json,
        )
    except FileNotFoundError as exc:
        return _error(
            MusicCapabilityError(
                "MUSIC_REQUEST_MISSING",
                f"request does not exist: {exc.filename}",
                "Pass an existing request JSON file.",
            ),
            as_json=as_json,
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        return _error(
            MusicCapabilityError(
                "MUSIC_REQUEST_INVALID",
                f"cannot read request: {exc}",
                "Fix the request JSON.",
            ),
            as_json=as_json,
        )


def register_music_parser(commands: argparse._SubParsersAction) -> argparse._SubParsersAction:
    music = commands.add_parser("music", help="plan Maestro music without GPU or host work")
    verbs = music.add_subparsers(dest="music_verb", required=True)
    for verb, help_text in (
        ("plan", "normalize one song request"),
        ("compile", "persist immutable song plan records"),
        ("style", "validate one style-adaptation plan"),
        ("compare", "reconstruct and compare plan records"),
    ):
        command = verbs.add_parser(verb, help=help_text)
        if verb != "compare":
            command.add_argument("--request", required=True)
            command.add_argument("--models", required=True)
            command.add_argument("--score-out", help="new deterministic ABC artifact path")
        command.add_argument("--db", help="new durable plan database")
        command.add_argument("--json", action="store_true")
        command.set_defaults(handler=_run_music)
    return commands


__all__ = ["register_music_parser"]
