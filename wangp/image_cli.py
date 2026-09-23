"""The no-GPU ``wgp image`` planning and reconstruction surface."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pydantic import ValidationError

from predict.image_capabilities import (
    ImageCapabilityError,
    ImageOperation,
    attach_manifest_model,
    load_image_model_manifest,
)
from services.image.request_compiler import (
    compile_image_request,
    enqueue_plan,
    reconstruct_plan_database,
)
from wangp.diagnostics import FailureDiagnostic, render_diagnostic


EXIT_OK = 0
EXIT_INPUT = 2
VERB_OPERATIONS = {
    "plan": frozenset(item.value for item in ImageOperation),
    "edit": frozenset((ImageOperation.edit.value, ImageOperation.identity_edit.value)),
    "upscale": frozenset((ImageOperation.upscale.value,)),
    "outpaint": frozenset((ImageOperation.outpaint.value,)),
}


def _error(exc: ImageCapabilityError, *, as_json: bool) -> int:
    diagnostic = FailureDiagnostic(
        code=exc.code,
        severity="error",
        title="Typed image request rejection",
        observed=exc.observed,
        why="The request cannot enter governed planning without complete immutable inputs.",
        remediation=exc.remediation,
        next_command=exc.next_command,
        metadata=exc.metadata,
    )
    if as_json:
        print(json.dumps({"diagnostics": [diagnostic.mapping()]}, sort_keys=True, separators=(",", ":")))
    else:
        print(render_diagnostic(diagnostic), file=sys.stderr)
    return EXIT_INPUT


def _typed(exc: Exception, code: str, remediation: str, *, command: str) -> ImageCapabilityError:
    return ImageCapabilityError(code, str(exc), remediation, next_command=command)


def _run_image(args: argparse.Namespace) -> int:
    as_json = bool(args.json)
    command = f"wgp image {args.image_verb} --request <request> --models <models> --dry-run --json"
    if args.image_verb == "plan" and args.reconstruct:
        database = Path(args.db).expanduser().resolve()
        try:
            results = reconstruct_plan_database(database)
        except ImageCapabilityError as exc:
            return _error(exc, as_json=as_json)
        except (OSError, KeyError, TypeError, ValueError, ValidationError) as exc:
            failure = _typed(
                exc,
                "IMAGE_RECONSTRUCTION_RECORD_INVALID",
                "Use a database produced by wgp image.",
                command="wgp image plan --db <plan.db> --reconstruct --json",
            )
            return _error(failure, as_json=as_json)
        payload = {
            "schema_version": "wangp-dspy.image-reconstruction/v1",
            "records": results,
            "all_match": all(item["match"] for item in results),
            "hidden_mutation": any(item["hidden_mutation"] for item in results),
        }
        if as_json:
            print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
        else:
            print(
                f"records={len(results)} all_match={str(payload['all_match']).lower()} "
                f"hidden_mutation={str(payload['hidden_mutation']).lower()}"
            )
        return EXIT_OK if payload["all_match"] else EXIT_INPUT

    try:
        if args.models is None:
            raise ImageCapabilityError(
                "MODEL_MANIFEST_MISSING",
                "image planning requires --models",
                "Supply an operator-recorded manifest; Wangp does not download models.",
            )
        if args.db is None and not args.dry_run:
            raise ImageCapabilityError(
                "IMAGE_QUEUE_PATH_MISSING",
                "image planning requires --db",
                "Supply a new SQLite database path, or use --dry-run.",
            )
        request_path = Path(args.request).expanduser().resolve()
        payload = json.loads(request_path.read_text(encoding="utf-8"))
        operation = payload.get("operation") if isinstance(payload, dict) else None
        if operation not in VERB_OPERATIONS[args.image_verb]:
            raise ImageCapabilityError(
                "IMAGE_REQUEST_INVALID",
                f"wgp image {args.image_verb} cannot process operation {operation!r}",
                f"Use an operation in {sorted(VERB_OPERATIONS[args.image_verb])}.",
            )
        request = attach_manifest_model(payload, load_image_model_manifest(args.models))
        plan = compile_image_request(request).mapping()
        record_id = None
        if not args.dry_run:
            record_id = enqueue_plan(plan, args.db)
            plan = dict(plan)
            plan["queue"] = {
                "database": str(Path(args.db).expanduser().resolve()),
                "record_ids": [record_id],
                "executable_jobs": 0,
            }
    except ImageCapabilityError as exc:
        return _error(exc, as_json=as_json)
    except ValidationError as exc:
        failure = _typed(exc, "IMAGE_REQUEST_INVALID", "Fix the typed image request.", command=command)
        return _error(failure, as_json=as_json)
    except ValueError as exc:
        failure = _typed(exc, "IMAGE_REQUEST_INVALID", "Fix the typed image request.", command=command)
        return _error(failure, as_json=as_json)
    except FileNotFoundError as exc:
        failure = _typed(exc, "IMAGE_REQUEST_MISSING", "Pass an existing request JSON file.", command=command)
        return _error(failure, as_json=as_json)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        failure = _typed(exc, "IMAGE_REQUEST_INVALID", "Fix the request JSON.", command=command)
        return _error(failure, as_json=as_json)

    if as_json:
        print(json.dumps(plan, sort_keys=True, separators=(",", ":")))
        return EXIT_OK
    record = plan["records"][0]
    summary = plan["summary"]
    print(
        f"operation={plan['operation']} images={plan['image_count']} "
        f"capability_status={plan['capability_status']} "
        f"references={record['reference_count']}/{record['reference_limit']}"
    )
    print(
        f"format={record['output']['format']} alpha_mode={record['alpha_mode']} "
        f"gpu_work={str(summary['gpu_work']).lower()} "
        f"queue_submitted={str(summary['queue_submitted']).lower()} "
        f"host_contact={str(summary['host_contact']).lower()}"
    )
    if record_id is not None:
        print(f"records={record_id}")
    return EXIT_OK


def register_image_parser(commands: argparse._SubParsersAction) -> argparse._SubParsersAction:
    image = commands.add_parser("image", help="plan Maestro image breadth without GPU or host work")
    verbs = image.add_subparsers(dest="image_verb", required=True)
    for verb, help_text in (
        ("plan", "normalize any typed image request"),
        ("edit", "plan an edit or identity-preserving edit"),
        ("upscale", "plan an image upscale"),
        ("outpaint", "plan an image outpaint"),
    ):
        parser = verbs.add_parser(verb, help=help_text)
        if verb == "plan":
            modes = parser.add_mutually_exclusive_group(required=True)
            modes.add_argument("--request", help="typed image request JSON")
            modes.add_argument("--reconstruct", action="store_true", help="reconstruct plan recipes")
        else:
            parser.add_argument("--request", required=True, help="typed image request JSON")
        parser.add_argument("--models", help="operator-supplied immutable model manifest")
        parser.add_argument("--db", help="new temporary durable plan database")
        parser.add_argument("--dry-run", action="store_true", help="normalize without a durable record")
        parser.add_argument("--json", action="store_true")
        parser.set_defaults(handler=_run_image)
    return commands


__all__ = ["register_image_parser"]
