"""The no-GPU ``wgp director`` composition and plan-record surface."""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any, Mapping

from services.director.composition import DirectorError
from services.director.plan_compiler import (
    compile_director_request,
    enhance_director_database,
    enqueue_director_plan,
    inspect_queue_database,
    load_enhancement_request,
    load_request,
    reconstruct_director_records,
)
from wangp.diagnostics import FailureDiagnostic, render_diagnostic

EXIT_OK = 0
EXIT_INPUT = 2


def _error(exc: DirectorError, *, as_json: bool) -> int:
    diagnostic = FailureDiagnostic(
        code=exc.code,
        severity="error",
        title="Typed director planning rejection",
        observed=exc.observed,
        why=(
            "Director composition requires complete local evidence and never "
            "proves generated media."
        ),
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


def _print(payload: Mapping[str, Any], *, as_json: bool, human: str) -> None:
    if as_json:
        print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    else:
        print(human)


def _run_plan(args: argparse.Namespace, *, as_json: bool) -> int:
    request = load_request(args.request)
    plan = compile_director_request(request).mapping()
    database = Path(args.db).expanduser().resolve()
    record_ids = enqueue_director_plan(plan, database)
    plan = dict(plan)
    plan["queue"] = {
        "database": str(database),
        "record_ids": record_ids,
        "executable_jobs": 0,
    }
    _print(
        plan,
        as_json=as_json,
        human=(
            f"mode={plan['mode']} clips={plan['clip_count']} "
            f"duration_s={plan['duration_s']:.9f} capability_status=planned\n"
            "gpu_work=false media_generated=false queue_submitted=false "
            "host_contact=false"
        ),
    )
    return EXIT_OK


def _run_enhance(args: argparse.Namespace, *, as_json: bool) -> int:
    request = load_enhancement_request(args.request)
    payload = enhance_director_database(request, args.output_db)
    _print(
        payload,
        as_json=as_json,
        human=(
            f"records={len(payload['record_ids'])} "
            f"changed_fields={','.join(payload['changed_fields'])}\n"
            f"original_request_sha256={payload['original_request_sha256']}\n"
            f"enhanced_request_sha256={payload['enhanced_request_sha256']}\n"
            "source_mutated=false executable_jobs=0 queue_submitted=false "
            "host_contact=false media_generated=false"
        ),
    )
    return EXIT_OK


def _run_queue(args: argparse.Namespace, *, as_json: bool) -> int:
    payload = inspect_queue_database(args.db)
    _print(
        payload,
        as_json=as_json,
        human=(
            f"records={payload['record_count']} pending_jobs=0 "
            f"selected_job={payload['selected_job']} "
            f"drainable={str(payload['drainable']).lower()}\n"
            "real_admission_selector="
            "services.jobs.queue.JobQueue.next_admissible "
            "mutation_performed=false queue_submitted=false host_contact=false"
        ),
    )
    return EXIT_OK


def _run_review(args: argparse.Namespace, *, as_json: bool) -> int:
    records = reconstruct_director_records(args.db)
    payload = {
        "schema_version": "wangp-dspy.director-reconstruction/v1",
        "records": records,
        "all_match": all(item["match"] for item in records),
        "hidden_mutation": any(item["hidden_mutation"] for item in records),
    }
    _print(
        payload,
        as_json=as_json,
        human=(
            f"records={len(records)} all_match={str(payload['all_match']).lower()} "
            f"hidden_mutation={str(payload['hidden_mutation']).lower()}"
        ),
    )
    return EXIT_OK if payload["all_match"] else EXIT_INPUT


def _run_director(args: argparse.Namespace) -> int:
    as_json = bool(args.json)
    verb = args.director_verb
    try:
        if verb == "plan":
            return _run_plan(args, as_json=as_json)
        if verb == "enhance":
            return _run_enhance(args, as_json=as_json)
        if verb == "queue":
            return _run_queue(args, as_json=as_json)
        return _run_review(args, as_json=as_json)
    except DirectorError as exc:
        return _error(exc, as_json=as_json)
    except sqlite3.Error as exc:
        failure = DirectorError(
            "DIRECTOR_QUEUE_DATABASE_INVALID",
            f"director database operation failed: {exc}",
            "Use a new output path or an undamaged database emitted by wgp director.",
            next_command="wgp director queue --db <plan.db> --json",
        )
        return _error(failure, as_json=as_json)


def register_director_parser(
    commands: argparse._SubParsersAction,
) -> argparse._SubParsersAction:
    director = commands.add_parser(
        "director",
        help="plan governed composition without GPU or host work",
    )
    verbs = director.add_subparsers(dest="director_verb", required=True)
    for verb, help_text in (
        ("plan", "compile one typed composition into immutable records"),
        ("enhance", "copy a plan with one authorized queue enhancement"),
        ("queue", "prove plan records are invisible to real admission"),
        ("review", "reconstruct and review immutable director records"),
    ):
        parser = verbs.add_parser(verb, help=help_text)
        parser.add_argument("--json", action="store_true")
        if verb == "plan":
            parser.add_argument("--request", required=True)
            parser.add_argument("--db", required=True)
        elif verb == "enhance":
            parser.add_argument("--request", required=True)
            parser.add_argument("--output-db", required=True)
        else:
            parser.add_argument("--db", required=True)
        parser.set_defaults(handler=_run_director)
    return commands


__all__ = ["register_director_parser"]
