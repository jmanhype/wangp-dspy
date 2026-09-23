"""The no-GPU ``wgp finish`` planning and reconstruction surface."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from predict.finishing import FinishingCapabilityError
from services.finishing.pipeline import (
    compile_finishing_request,
    enqueue_plan,
    load_request,
    reconstruct_plan_database,
)
from wangp.diagnostics import FailureDiagnostic, render_diagnostic


EXIT_OK = 0
EXIT_INPUT = 2


def _error(exc: FinishingCapabilityError, *, as_json: bool) -> int:
    diagnostic = FailureDiagnostic(
        code=exc.code,
        severity="error",
        title="Typed finishing rejection",
        observed=exc.observed,
        why="Finishing must preserve immutable source bytes and cannot execute without a separately authorized host.",
        remediation=exc.remediation,
        next_command=exc.next_command,
        metadata=exc.metadata,
    )
    if as_json:
        print(json.dumps(
            {"diagnostics": [diagnostic.mapping()]},
            sort_keys=True,
            separators=(",", ":"),
        ))
    else:
        print(render_diagnostic(diagnostic), file=sys.stderr)
    return EXIT_INPUT


def _print(payload: dict[str, Any], *, as_json: bool, human: str) -> None:
    if as_json:
        print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    else:
        print(human)


def _plan(args: argparse.Namespace, *, as_json: bool) -> int:
    if args.reconstruct:
        database = Path(args.db).expanduser().resolve()
        results = reconstruct_plan_database(database)
        payload = {
            "schema_version": "wangp-dspy.finishing-reconstruction/v1",
            "records": results,
            "all_match": all(item["match"] for item in results),
            "hidden_mutation": any(item["hidden_mutation"] for item in results),
        }
        _print(
            payload,
            as_json=as_json,
            human=(
                f"records={len(results)} "
                f"all_match={str(payload['all_match']).lower()} "
                f"hidden_mutation={str(payload['hidden_mutation']).lower()}"
            ),
        )
        return EXIT_OK if payload["all_match"] else EXIT_INPUT

    if args.db is None and not args.dry_run:
        raise FinishingCapabilityError(
            "FINISH_QUEUE_PATH_MISSING",
            "queue planning requires --db",
            "Supply a new SQLite database path, or use --dry-run.",
        )
    request = load_request(args.request)
    plan = compile_finishing_request(request).mapping()
    record_ids: list[str] | None = None
    if not args.dry_run:
        record_ids = enqueue_plan(plan, args.db)
        plan = dict(plan)
        plan["queue"] = {
            "database": str(Path(args.db).expanduser().resolve()),
            "record_ids": record_ids,
            "executable_jobs": 0,
        }
    summary = plan["summary"]
    _print(
        plan,
        as_json=as_json,
        human=(
            f"backend={plan['backend']} records={plan['record_count']} "
            f"capability_status={plan['capability_status']}\n"
            "gpu_work=false media_generated=false "
            f"queue_submitted={str(summary['queue_submitted']).lower()} "
            f"host_contact={str(summary['host_contact']).lower()}"
        ),
    )
    return EXIT_OK


def _probe(args: argparse.Namespace, *, as_json: bool) -> int:
    request = load_request(args.request)
    plan = compile_finishing_request(request).mapping()
    record = plan["records"][0]
    payload = {
        "schema_version": "wangp-dspy.finishing-probe/v1",
        "request_sha256": plan["request_sha256"],
        "backend": plan["backend"],
        "capability_status": plan["capability_status"],
        "source_sha256": record["source"]["sha256"],
        "command_graph": record["command_graph"],
        "measurement_status": "unverified",
        "executed": False,
        "host_contact": False,
    }
    _print(
        payload,
        as_json=as_json,
        human=(
            f"backend={payload['backend']} stages={len(payload['command_graph'])} "
            f"measurement_status={payload['measurement_status']} executed=false host_contact=false"
        ),
    )
    return EXIT_OK


def _run_finish(args: argparse.Namespace) -> int:
    as_json = bool(args.json)
    try:
        if args.finish_verb == "plan":
            return _plan(args, as_json=as_json)
        if args.finish_verb == "probe":
            return _probe(args, as_json=as_json)
        raise FinishingCapabilityError(
            "FINISH_EXECUTION_UNAUTHORIZED",
            "wgp finish run has no separately authorized host execution record",
            "Use wgp finish plan for deterministic planning; request a separately authorized host run for execution.",
            next_command="wgp finish plan --request <request> --dry-run --json",
        )
    except FinishingCapabilityError as exc:
        return _error(exc, as_json=as_json)
    except (OSError, UnicodeError, ValueError) as exc:
        return _error(
            FinishingCapabilityError(
                "FINISH_REQUEST_INVALID",
                f"cannot process finishing request: {exc}",
                "Fix the typed request JSON, then rerun the deterministic no-GPU plan.",
            ),
            as_json=as_json,
        )


def register_finish_parser(
    commands: argparse._SubParsersAction,
) -> argparse._SubParsersAction:
    finish = commands.add_parser(
        "finish", help="plan media finishing without GPU or host work"
    )
    verbs = finish.add_subparsers(dest="finish_verb", required=True)
    finish.set_defaults(handler=_run_finish)
    plan = verbs.add_parser("plan", help="compile or reconstruct a durable plan")
    modes = plan.add_mutually_exclusive_group(required=True)
    modes.add_argument("--request", help="typed finishing request JSON")
    modes.add_argument("--reconstruct", action="store_true", help="rebuild stored hashes")
    plan.add_argument("--db", help="new durable plan database")
    plan.add_argument("--dry-run", action="store_true", help="plan without a database")
    plan.add_argument("--json", action="store_true")

    run = verbs.add_parser("run", help="show the authorized-execution boundary")
    run.add_argument("--request", required=True, help="typed finishing request JSON")
    run.add_argument("--json", action="store_true")

    probe = verbs.add_parser("probe", help="compile the planned ffprobe/metadata graph")
    probe.add_argument("--request", required=True, help="typed finishing request JSON")
    probe.add_argument("--json", action="store_true")
    return commands


__all__ = ["register_finish_parser"]
