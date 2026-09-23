"""Headless validation and deterministic governance export for editor projects."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping

from services.editor.assembly_exporter import enqueue_export, export_project, write_export
from services.editor.project_store import ProjectStore
from wangp.diagnostics import FailureDiagnostic, render_diagnostic
from wangp.editor_project import EditorProjectError, project_sha256


EXIT_OK = 0
EXIT_INPUT = 2
VALIDATE_NEXT_COMMAND = "wgp editor validate --project <project> --json"
EXPORT_NEXT_COMMAND = "wgp editor export --project <project> --out <export.json> --json"


def _print(payload: Mapping[str, Any], *, as_json: bool, human: str) -> None:
    if as_json:
        print(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False))
    else:
        print(human)


def _failure(exc: EditorProjectError, *, as_json: bool) -> int:
    diagnostic = FailureDiagnostic(
        code=exc.code,
        severity="error",
        title="Typed editor project rejection",
        observed=exc.observed,
        why=(
            "Editor decisions are serialized and pinned to immutable source bytes; "
            "Wangp never fetches, regenerates, renders, or overwrites a source."
        ),
        remediation=exc.remediation,
        next_command=exc.next_command,
        metadata=exc.metadata,
    )
    if as_json:
        print(json.dumps({"diagnostics": [diagnostic.mapping()]}, sort_keys=True, separators=(",", ":")))
    else:
        print(render_diagnostic(diagnostic), file=sys.stderr)
    return EXIT_INPUT


def _run_validate(args: argparse.Namespace, *, as_json: bool) -> int:
    store = ProjectStore(args.project)
    document = store.load()
    sources = store.verify_sources(document.project)
    payload = {
        "schema_version": "wangp-dspy.editor-validation/v1",
        "project": str(store.path),
        "project_sha256": project_sha256(document.project),
        "revision": document.project.revision,
        "history_entries": len(document.history),
        "history_cursor": document.history_cursor,
        "source_count": len(sources),
        "source_manifest": {source.asset_id: source.sha256 for source in sources},
        "sources_verified": True,
        "gpu_work": False,
        "host_contact": False,
        "media_generated": False,
    }
    _print(
        payload,
        as_json=as_json,
        human=(
            f"project={store.path} revision={document.project.revision} "
            f"history={len(document.history)} sources={len(sources)} verified=true\n"
            "gpu_work=false host_contact=false media_generated=false source_mutated=false"
        ),
    )
    return EXIT_OK


def _run_export(args: argparse.Namespace, *, as_json: bool) -> int:
    store = ProjectStore(args.project)
    document = store.load()
    store.verify_sources(document.project)
    payload = export_project(store, document.project)
    output = write_export(payload, args.out)
    queue_job_id: str | None = None
    queue_database: str | None = None
    if args.queue_db:
        queue_database = str(Path(args.queue_db).expanduser().resolve())
        queue_job_id = enqueue_export(payload, output, queue_database)
    result = dict(payload)
    result["export"] = {
        "path": str(output),
        "queue_database": queue_database,
        "queue_job_id": queue_job_id,
        "queue_submitted": queue_job_id is not None,
    }
    _print(
        result,
        as_json=as_json,
        human=(
            f"export={output} project_sha256={payload['project_sha256']} "
            f"continuity_digest={payload['assembly']['continuity_digest']}\n"
            f"queue_submitted={str(queue_job_id is not None).lower()} "
            "gpu_work=false host_contact=false media_generated=false source_mutated=false"
        ),
    )
    return EXIT_OK


def _run_editor(args: argparse.Namespace) -> int:
    as_json = bool(args.json)
    if args.editor_verb == "validate":
        try:
            return _run_validate(args, as_json=as_json)
        except EditorProjectError as exc:
            return _failure(exc, as_json=as_json)
    try:
        return _run_export(args, as_json=as_json)
    except EditorProjectError as exc:
        return _failure(exc, as_json=as_json)
    except (OSError, ValueError) as exc:
        failure = EditorProjectError(
            "EDITOR_EXPORT_WRITE_FAILED",
            f"cannot complete editor export: {exc}",
            "Check the output and optional queue paths, then rerun the no-GPU export.",
            next_command=EXPORT_NEXT_COMMAND,
        )
        return _failure(failure, as_json=as_json)


def register_editor_parser(commands: argparse._SubParsersAction) -> argparse._SubParsersAction:
    editor = commands.add_parser("editor", help="validate and export non-destructive edits without GPU work")
    verbs = editor.add_subparsers(dest="editor_verb", required=True)
    validate = verbs.add_parser("validate", help="verify project schema, history, and pinned source bytes")
    validate.add_argument("--project", required=True)
    validate.add_argument("--json", action="store_true")
    validate.set_defaults(handler=_run_editor)
    export = verbs.add_parser("export", help="emit deterministic director and assembly planning JSON")
    export.add_argument("--project", required=True)
    export.add_argument("--out", required=True)
    export.add_argument("--queue-db")
    export.add_argument("--json", action="store_true")
    export.set_defaults(handler=_run_editor)
    return commands


__all__ = ["register_editor_parser"]
