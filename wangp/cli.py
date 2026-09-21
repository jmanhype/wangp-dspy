"""Thin, stable ``wgp`` dispatcher over existing engine seams."""

from __future__ import annotations

import argparse
import contextlib
import json
import io
import shlex
import sqlite3
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

from predict.content_brief import ContentBriefError, load_content_brief
from services.jobs.queue import JobNotFoundError
from wangp import __version__
from wangp.doctor import DoctorCheck, collect_doctor_checks
from wangp.diagnostics import (
    classify_input_failure,
    classify_provenance_failures,
    redact_sensitive,
    render_diagnostic,
    render_diagnostic_mapping,
)
from wangp.queue_view import (
    collect_queue_review,
    collect_status,
    render_run_review,
    render_queue_review,
    render_status,
    review_run,
)


EXIT_OK = 0
EXIT_INPUT = 2
EXIT_DOCTOR = 3
EXIT_INTERNAL = 4


def _emit_json(payload: Mapping[str, Any]) -> None:
    print(json.dumps(
        redact_sensitive(dict(payload)), sort_keys=True,
        separators=(",", ":"), ensure_ascii=False
    ))


def _error(message: str) -> None:
    print(f"wgp: error: {redact_sensitive(message)}", file=sys.stderr)


def _load_models(path: str | None) -> list[dict[str, str]] | None:
    if path is None:
        return None
    source = Path(path).expanduser()
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read model manifest {source}: {exc}") from exc
    if isinstance(payload, dict) and isinstance(payload.get("models"), list):
        payload = payload["models"]
    if not isinstance(payload, list):
        raise ValueError("model manifest must be a list of model objects")
    models: list[dict[str, str]] = []
    for item in payload:
        if not isinstance(item, dict):
            raise ValueError("model manifest must be a list of model objects")
        digest = item.get("sha256")
        if not isinstance(digest, str) or len(digest) != 64 or any(
            character not in "0123456789abcdef" for character in digest.lower()
        ):
            raise ValueError("each model sha256 must be a 64-character hexadecimal digest")
        local_path = item.get("local_path", item.get("path"))
        remote_path = item.get("remote_path")
        if not isinstance(local_path, str) and not isinstance(remote_path, str):
            raise ValueError(
                "each model needs local_path or remote_path plus sha256 "
                "(path is accepted as a legacy local_path alias)"
            )
        model = {"sha256": digest.lower()}
        if isinstance(local_path, str):
            model["local_path"] = local_path
        if isinstance(remote_path, str):
            model["remote_path"] = remote_path
        models.append(model)
    return models


def _database_reachability(path: str) -> DoctorCheck:
    database = Path(path).expanduser()
    if not database.is_file():
        return DoctorCheck(
            kind="database_reachability",
            status="failed",
            detail=f"queue database does not exist: {database}",
            remediation="Create or select the run's jobs.db before retrying doctor.",
        )
    try:
        connection = sqlite3.connect(f"file:{database.resolve()}?mode=ro", uri=True)
        try:
            connection.execute("SELECT 1").fetchone()
        finally:
            connection.close()
    except sqlite3.Error as exc:
        return DoctorCheck(
            kind="database_reachability",
            status="failed",
            detail=f"queue database is not readable: {exc}",
            remediation="Restore the SQLite database from durable run evidence.",
        )
    return DoctorCheck(
        kind="database_reachability",
        status="pass",
        detail=f"queue database reachable: {database}",
    )


def _run_doctor(args: argparse.Namespace) -> int:
    report = collect_doctor_checks(args.models, probe_host=args.probe_host)
    if args.db is not None:
        report.checks.append(_database_reachability(args.db))
    if args.json:
        _emit_json(report.mapping())
    else:
        for check in report.checks:
            symbol = {"pass": "PASS", "failed": "FAIL", "skipped": "SKIP"}[
                check.status
            ]
            print(f"[{symbol}] {check.kind}: {redact_sensitive(check.detail)}")
            if check.status != "pass":
                print(
                    f"       remediation: {redact_sensitive(check.remediation)}"
                )
        for diagnostic in report.diagnostics:
            print(render_diagnostic(diagnostic))
        print(f"ready={'yes' if report.ready else 'no'}")
    return EXIT_OK if report.ready else EXIT_DOCTOR


def _validate_brief(args: argparse.Namespace) -> int:
    brief = load_content_brief(args.brief)
    if args.json:
        _emit_json({"brief": brief.brief_hash, "valid": True})
    else:
        print(f"brief={brief.brief_hash} valid=true")
    return EXIT_OK


def _run_plan(args: argparse.Namespace) -> int:
    from scripts.run_content_brief import main as plan_gateway

    output = args.out.expanduser().resolve()
    run_dir = (
        args.run_dir.expanduser().resolve()
        if args.run_dir is not None
        else output.parent / "run"
    )
    gateway_argv = ["--brief", str(args.brief.expanduser().resolve()), "--plates", str(args.plates.expanduser().resolve()), "--output", str(output), "--run-dir", str(run_dir)]
    if args.json:
        with contextlib.redirect_stdout(io.StringIO()):
            plan_gateway(gateway_argv)
    else:
        plan_gateway(gateway_argv)
    payload = json.loads(output.read_text(encoding="utf-8"))
    summary = payload["summary"]
    ledger = run_dir / "run_ledger.json"
    result = {"plan": output.as_posix(), "ledger": ledger.as_posix(), "summary": summary}
    if args.json:
        _emit_json(result)
    else:
        print(
            f"summary clips={summary['clip_count']} "
            f"duration_s={summary['planned_duration_s']} "
            f"gpu_work={str(summary['gpu_work']).lower()} "
            f"queue_submitted={str(summary['queue_submitted']).lower()}"
        )
        print(f"ledger={ledger}")
    return EXIT_OK


def _resolve_database(args: argparse.Namespace) -> Path:
    if args.db is not None:
        return Path(args.db).expanduser().resolve()
    run = Path(args.run).expanduser().resolve()
    for candidate in (run / "jobs.db", run / "run" / "jobs.db"):
        if candidate.is_file():
            return candidate
    raise ValueError(f"no jobs.db found in run directory {run}")


def _run_status(args: argparse.Namespace) -> int:
    status = collect_status(_resolve_database(args), job_id=args.job)
    if args.json:
        _emit_json(status.mapping())
    else:
        print(render_status(status))
    return EXIT_OK


def _run_review(args: argparse.Namespace) -> int:
    if args.db is None and args.run is None:
        raise ValueError("review requires --db or a RUN directory")
    payload: dict[str, Any] = {}
    try:
        if args.db is not None:
            queue_payload, evidence = collect_queue_review(
                args.db, job_id=args.job
            )
            payload["queue"] = queue_payload
            payload["evidence"] = evidence
        if args.run is not None:
            payload["run_review"] = review_run(args.run)
    except (FileNotFoundError, ValueError, JobNotFoundError) as exc:
        message = str(exc)
        if isinstance(exc, JobNotFoundError):
            message = f"queue job not found: {args.job or exc.args[0]}"
        if args.run is not None:
            next_command = f"wgp review {shlex.quote(str(args.run))}"
        elif args.db is not None:
            next_command = shlex.join([
                "wgp", "review", "--db", str(args.db)
            ])
        else:
            next_command = None
        diagnostic = classify_input_failure(
            message,
            source=args.run if args.run is not None else args.db,
            next_command=next_command,
        )
        if args.json:
            _emit_json({"diagnostics": [diagnostic.mapping()]})
        else:
            print(render_diagnostic(diagnostic), file=sys.stderr)
        return EXIT_INPUT
    failed_hashes = [item for item in payload.get("run_review", {}).get("hash_checks", []) if item["status"] != "pass"]
    diagnostics = [
        diagnostic.mapping()
        for diagnostic in classify_provenance_failures(failed_hashes, args.run or "")
    ]
    if args.json:
        if diagnostics:
            payload["diagnostics"] = diagnostics
        _emit_json(payload)
    else:
        if "queue" in payload:
            print(render_queue_review(payload["queue"], payload["evidence"]))
        if "run_review" in payload:
            print(render_run_review(payload["run_review"]))
        for diagnostic in diagnostics:
            print(render_diagnostic_mapping(diagnostic))
    if failed_hashes:
        return EXIT_INPUT
    return EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    """Build the stable parser without registering unstable verbs."""

    parser = argparse.ArgumentParser(
        prog="wgp", description="Wangp planning, readiness, and review CLI"
    )
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="verb", required=True)

    doctor = commands.add_parser(
        "doctor", help="report local readiness and optionally probe a host"
    )
    doctor.add_argument("--json", action="store_true")
    doctor.add_argument("--db", help="also check one queue database")
    doctor.add_argument("--models", help="JSON model manifest")
    doctor.add_argument(
        "--probe-host",
        action="store_true",
        help="run five existing remote checks; never implied",
    )
    doctor.set_defaults(handler=_run_doctor, models=None)

    brief = commands.add_parser("brief", help="typed content-brief operations")
    brief_commands = brief.add_subparsers(dest="brief_verb", required=True)
    validate = brief_commands.add_parser(
        "validate", help="validate one JSON brief without planning"
    )
    validate.add_argument("brief", type=Path)
    validate.add_argument("--json", action="store_true")
    validate.set_defaults(handler=_validate_brief)

    plan = commands.add_parser("plan", help="emit the existing no-GPU dry plan")
    plan.add_argument("--brief", required=True, type=Path)
    plan.add_argument("--plates", required=True, type=Path)
    plan.add_argument("--out", required=True, type=Path)
    plan.add_argument("--run-dir", type=Path)
    plan.add_argument("--json", action="store_true")
    plan.set_defaults(handler=_run_plan)

    status = commands.add_parser("status", help="summarize durable queue state")
    source = status.add_mutually_exclusive_group(required=True)
    source.add_argument("--db", help="path to jobs.db")
    source.add_argument("--run", help="run directory containing jobs.db")
    status.add_argument("--job", help="select one job id")
    status.add_argument("--json", action="store_true")
    status.set_defaults(handler=_run_status, db=None, run=None)

    review = commands.add_parser("review", help="review queue and run evidence")
    review.add_argument("run", nargs="?", help="review-bundle directory")
    review.add_argument("--db", help="path to jobs.db")
    review.add_argument("--job", help="select one queue job id")
    review.add_argument("--json", action="store_true")
    review.set_defaults(handler=_run_review)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Dispatch one stable verb using the documented exit-code contract."""

    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.verb == "doctor":
            args.models = _load_models(args.models)
        return int(args.handler(args))
    except json.JSONDecodeError as exc:
        _error(f"unexpected internal error: JSONDecodeError: {exc}")
        return EXIT_INTERNAL
    except ContentBriefError as exc:
        diagnostic = classify_input_failure(
            str(exc), source=str(getattr(args, "brief", "") or "")
        )
        if getattr(args, "json", False):
            _emit_json({"diagnostics": [diagnostic.mapping()]})
        else:
            print(render_diagnostic(diagnostic), file=sys.stderr)
        return EXIT_INPUT
    except (
        FileNotFoundError,
        JobNotFoundError,
        ValueError,
    ) as exc:
        _error(str(exc))
        return EXIT_INPUT
    except Exception as exc:
        _error(f"unexpected internal error: {type(exc).__name__}: {exc}")
        return EXIT_INTERNAL


__all__ = ["build_parser", "main"]
