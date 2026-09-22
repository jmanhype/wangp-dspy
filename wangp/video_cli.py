"""The no-GPU ``wgp video`` planning and reconstruction surface."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pydantic import ValidationError

from predict.video_capabilities import (
    VideoCapabilityError,
    attach_manifest_model,
    load_video_model_manifest,
)
from services.video.operation_compiler import (
    compile_video_request,
    enqueue_plan,
    reconstruct_plan_database,
)
from wangp.diagnostics import FailureDiagnostic, render_diagnostic


EXIT_OK = 0
EXIT_INPUT = 2


def _error(exc: VideoCapabilityError, *, as_json: bool) -> int:
    diagnostic = FailureDiagnostic(
        code=exc.code,
        severity="error",
        title="Typed video request rejection",
        observed=exc.observed,
        why="The request cannot enter the governed queue without complete immutable inputs.",
        remediation=exc.remediation,
        next_command=exc.next_command,
        metadata=exc.metadata,
    )
    if as_json:
        print(
            json.dumps(
                {"diagnostics": [diagnostic.mapping()]},
                sort_keys=True,
                separators=(",", ":"),
            )
        )
    else:
        print(render_diagnostic(diagnostic), file=sys.stderr)
    return EXIT_INPUT


def _run_video(args: argparse.Namespace) -> int:
    as_json = bool(args.json)
    if args.reconstruct:
        database = Path(args.db).expanduser().resolve()
        try:
            results = reconstruct_plan_database(database)
        except VideoCapabilityError as exc:
            return _error(exc, as_json=as_json)
        except (OSError, KeyError, TypeError, ValueError, ValidationError) as exc:
            failure = VideoCapabilityError(
                "VIDEO_RECONSTRUCTION_INVALID",
                f"cannot reconstruct queue {database}: {exc}",
                "Use a database produced by wgp video; do not edit queue records.",
                next_command="wgp video --db <jobs.db> --reconstruct --json",
            )
            return _error(failure, as_json=as_json)
        payload = {
            "schema_version": "wangp-dspy.video-reconstruction/v1",
            "records": results,
            "all_match": all(item["match"] for item in results),
            "hidden_mutation": any(item["hidden_mutation"] for item in results),
        }
        if as_json:
            print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
        else:
            print(
                f"records={len(results)} "
                f"all_match={str(payload['all_match']).lower()} "
                f"hidden_mutation={str(payload['hidden_mutation']).lower()}"
            )
        return EXIT_OK if payload["all_match"] else EXIT_INPUT

    try:
        if args.models is None:
            raise VideoCapabilityError(
                "MODEL_MANIFEST_MISSING",
                "video planning requires --models",
                "Supply an operator-recorded manifest; Wangp does not download models.",
            )
        if args.db is None and not args.dry_run:
            raise VideoCapabilityError(
                "VIDEO_QUEUE_PATH_MISSING",
                "queue planning requires --db",
                "Supply a new SQLite database path, or use --dry-run.",
            )
        request_path = Path(args.request).expanduser().resolve()
        payload = json.loads(request_path.read_text(encoding="utf-8"))
        models, _raw = load_video_model_manifest(args.models)
        request = attach_manifest_model(payload, models)
        plan = compile_video_request(request).mapping()
        record_ids = None
        if not args.dry_run:
            record_ids = enqueue_plan(plan, args.db)
            plan = dict(plan)
            plan["queue"] = {
                "database": str(Path(args.db).expanduser().resolve()),
                "record_ids": record_ids,
                "executable_jobs": 0,
            }
    except VideoCapabilityError as exc:
        return _error(exc, as_json=as_json)
    except ValidationError as exc:
        return _error(
            VideoCapabilityError(
                "VIDEO_REQUEST_INVALID",
                f"request validation failed: {exc.error_count()} field errors",
                "Fix the typed request fields, then rerun the deterministic no-GPU plan.",
            ),
            as_json=as_json,
        )
    except ValueError as exc:
        return _error(
            VideoCapabilityError(
                "VIDEO_REQUEST_INVALID",
                str(exc),
                "Fix the typed request fields, then rerun the deterministic no-GPU plan.",
            ),
            as_json=as_json,
        )
    except FileNotFoundError as exc:
        return _error(
            VideoCapabilityError(
                "VIDEO_REQUEST_MISSING",
                f"request does not exist: {exc.filename}",
                "Pass an existing request JSON file.",
            ),
            as_json=as_json,
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return _error(
            VideoCapabilityError(
                "VIDEO_REQUEST_INVALID",
                f"cannot read request: {exc}",
                "Fix the request JSON.",
            ),
            as_json=as_json,
        )
    if as_json:
        print(json.dumps(plan, sort_keys=True, separators=(",", ":")))
    else:
        summary = plan["summary"]
        print(
            f"operation={plan['operation']} clips={plan['clip_count']} "
            f"capability_status={plan['capability_status']} "
            f"long_form_mode={plan['long_form_mode']} "
            f"overlap_strategy={plan['overlap_strategy']}"
        )
        print(
            f"gpu_work={str(summary['gpu_work']).lower()} "
            f"queue_submitted={str(summary['queue_submitted']).lower()} "
            f"host_contact={str(summary['host_contact']).lower()}"
        )
        if record_ids is not None:
            print(f"records={','.join(record_ids)}")
    return EXIT_OK


def register_video_parser(
    commands: argparse._SubParsersAction,
) -> argparse._SubParsersAction:
    video = commands.add_parser(
        "video", help="plan Maestro video breadth without GPU or host work"
    )
    modes = video.add_mutually_exclusive_group(required=True)
    modes.add_argument("--request", help="typed video request JSON")
    modes.add_argument(
        "--reconstruct", action="store_true", help="reconstruct queue recipes"
    )
    video.add_argument("--models", help="operator-supplied immutable model manifest")
    video.add_argument("--db", help="temporary durable queue database")
    video.add_argument(
        "--dry-run", action="store_true", help="normalize and plan without a queue"
    )
    video.add_argument("--json", action="store_true")
    video.set_defaults(handler=_run_video)
    return commands


__all__ = ["register_video_parser"]
