"""The no-GPU ``wgp sfx`` planning and reconstruction surface."""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

from pydantic import ValidationError

from predict.audio_post import (
    AudioPostCapabilityError,
    AudioPostOperation,
    attach_manifest_model,
    load_audio_post_model_manifest,
)
from services.audio_post.plan_compiler import (
    compile_audio_post_request,
    enqueue_audio_post_plan,
    reconstruct_audio_post_database,
)
from wangp.diagnostics import FailureDiagnostic, render_diagnostic

EXIT_OK = 0
EXIT_INPUT = 2


def _error(exc: AudioPostCapabilityError, *, as_json: bool) -> int:
    diagnostic = FailureDiagnostic(
        code=exc.code,
        severity="error",
        title="Typed audio-post request rejection",
        observed=exc.observed,
        why="Audio-post planning requires immutable inputs and never proves audio or video output.",
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
        raise AudioPostCapabilityError(
            "MODEL_MANIFEST_MISSING",
            "audio-post planning requires --models",
            "Supply an operator-recorded manifest; Wangp does not download models.",
        )
    source = Path(path).expanduser().resolve()
    payload = json.loads(source.read_text(encoding="utf-8"))
    return attach_manifest_model(payload, load_audio_post_model_manifest(models_path))


def _plan(args: argparse.Namespace, *, as_json: bool) -> int:
    expected = {
        "effect": AudioPostOperation.sfx,
        "revoice": AudioPostOperation.revoice,
        "refine": AudioPostOperation.refine,
    }[args.sfx_verb]
    request = _load_request(args.request, args.models)
    if request.operation is not expected:
        raise AudioPostCapabilityError(
            "AUDIO_POST_MODE_MISMATCH",
            f"wgp sfx {args.sfx_verb} requires operation={expected.value}, got {request.operation.value}",
            "Use effect for sound effects, revoice for an existing clip, or refine for audio refinement.",
        )
    plan = compile_audio_post_request(request).mapping()
    record_ids = None
    database = Path(args.db).expanduser().resolve() if args.db else None
    if database is not None:
        record_ids = enqueue_audio_post_plan(plan, database)
        plan = dict(plan)
        plan["queue"] = {"database": str(database), "record_ids": record_ids, "executable_jobs": 0}
    if as_json:
        print(json.dumps(plan, sort_keys=True, separators=(",", ":")))
    else:
        summary = plan["summary"]
        print(
            f"operation={plan['operation']} engine={plan['model']['family']} "
            f"records={plan['record_count']} capability_status={plan['capability_status']}"
        )
        print(
            f"gpu_work={str(summary['gpu_work']).lower()} "
            f"audio_created={str(summary['audio_created']).lower()} "
            f"video_changed={str(summary['video_changed']).lower()} "
            f"queue_submitted={str(summary['queue_submitted']).lower()} "
            f"host_contact={str(summary['host_contact']).lower()}"
        )
        if record_ids is not None:
            print(f"records={','.join(record_ids)}")
    return EXIT_OK


def _run_sfx(args: argparse.Namespace) -> int:
    as_json = bool(args.json)
    if args.sfx_verb == "plan" and args.reconstruct:
        try:
            records = reconstruct_audio_post_database(args.db)
        except AudioPostCapabilityError as exc:
            return _error(exc, as_json=as_json)
        except (OSError, KeyError, TypeError, ValueError, ValidationError, sqlite3.Error) as exc:
            return _error(
                AudioPostCapabilityError(
                    "AUDIO_POST_RECONSTRUCTION_INVALID",
                    f"cannot reconstruct database {args.db}: {exc}",
                    "Use a database emitted by wgp sfx planning.",
                    next_command="wgp sfx plan --db <plan.db> --reconstruct --json",
                ),
                as_json=as_json,
            )
        payload = {
            "schema_version": "wangp-dspy.audio-post-reconstruction/v1",
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
        return _plan(args, as_json=as_json)
    except AudioPostCapabilityError as exc:
        return _error(exc, as_json=as_json)
    except ValidationError as exc:
        return _error(
            AudioPostCapabilityError(
                "AUDIO_POST_REQUEST_INVALID",
                f"request validation failed: {exc.error_count()} field errors",
                "Fix the typed audio-post request, then rerun the deterministic plan.",
            ),
            as_json=as_json,
        )
    except FileNotFoundError as exc:
        return _error(
            AudioPostCapabilityError(
                "AUDIO_POST_REQUEST_MISSING",
                f"request does not exist: {exc.filename}",
                "Pass an existing request JSON file.",
            ),
            as_json=as_json,
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        return _error(
            AudioPostCapabilityError(
                "AUDIO_POST_REQUEST_INVALID",
                f"cannot read request: {exc}",
                "Fix the request JSON.",
            ),
            as_json=as_json,
        )


def register_sfx_parser(commands: argparse._SubParsersAction) -> argparse._SubParsersAction:
    sfx = commands.add_parser("sfx", help="plan audio post work without GPU or host access")
    verbs = sfx.add_subparsers(dest="sfx_verb", required=True)
    for verb, help_text in (
        ("plan", "normalize or reconstruct one typed audio-post request"),
        ("effect", "plan a sound effect without synthesis"),
        ("revoice", "plan revoice while holding source video fixed"),
        ("refine", "plan audio refinement without video mutation"),
    ):
        parser = verbs.add_parser(verb, help=help_text)
        if verb == "plan":
            modes = parser.add_mutually_exclusive_group(required=True)
            modes.add_argument("--request", help="typed audio-post request JSON")
            modes.add_argument("--reconstruct", action="store_true", help="reconstruct command recipes")
        else:
            parser.add_argument("--request", required=True, help="typed audio-post request JSON")
        if verb != "plan":
            parser.add_argument("--models", required=True, help="operator-supplied immutable model manifest")
        else:
            parser.add_argument("--models", help="operator-supplied immutable model manifest")
        parser.add_argument("--db", help="new durable audio-post plan database")
        parser.add_argument("--json", action="store_true")
        parser.set_defaults(handler=_run_sfx)
    return commands


__all__ = ["register_sfx_parser"]
