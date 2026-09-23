"""Local, typed implementation of the stable ``wgp first-run`` surface."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from predict.model_assets import (
    asset_report,
    load_asset_manifest,
    load_download_state,
    operator_download_command,
    pause_asset,
    resume_asset,
    write_download_state,
)
from wangp.config import load_host_config
from wangp.diagnostics import FailureDiagnostic, redact_sensitive, render_diagnostic
from wangp.llm_runtime import (
    LlmRuntimeError,
    load_runtime_config,
    render_runtime,
    resolve_runtime,
)
from wangp.platform_profile import (
    PlatformInventory,
    collect_inventory,
    profile_mapping,
    render_profile,
)
from wangp.recovery import (
    RecoveryError,
    diagnose_oom,
    load_oom_record,
    render_recovery,
)
from wangp.remote import remote_report, render_remote


EXIT_OK = 0
EXIT_INPUT = 2
EXIT_CONFIGURATION = 3


def _emit_json(payload: dict[str, Any]) -> None:
    print(
        json.dumps(
            redact_sensitive(payload), sort_keys=True,
            separators=(",", ":"), ensure_ascii=False,
        )
    )


def _validation_diagnostic(exc: ValidationError, source: str) -> FailureDiagnostic:
    fields = []
    for error in exc.errors(include_url=False):
        fields.append(".".join(str(item) for item in error["loc"]) or "<object>")
    return FailureDiagnostic(
        code="PLATFORM_INPUT_INVALID",
        severity="error",
        title="Typed first-run input is invalid",
        observed=(
            f"validation failed with {exc.error_count()} error(s): "
            f"{', '.join(dict.fromkeys(fields))}"
        ),
        why="First-run preflight refuses incomplete hardware, asset, runtime, or recovery evidence.",
        remediation="Fix the recorded typed fields; no substitute value is inferred.",
        next_command="wgp first-run --help",
        evidence_refs=(source,),
        metadata={"field_count": len(fields)},
    )


def _typed_diagnostic(
    code: str,
    observed: str,
    remediation: str,
    *,
    next_command: str | None = None,
    source: str = "<first-run>",
) -> FailureDiagnostic:
    return FailureDiagnostic(
        code=code,
        severity="error",
        title="First-run preflight stopped before action",
        observed=observed,
        why="The no-GPU surface reports typed state instead of inferring an unsafe action.",
        remediation=remediation,
        next_command=next_command,
        evidence_refs=(source,),
    )


def _emit_diagnostic(
    diagnostic: FailureDiagnostic, *, as_json: bool, exit_code: int
) -> int:
    if as_json:
        _emit_json({"diagnostics": [diagnostic.mapping()]})
    else:
        print(render_diagnostic(diagnostic), file=sys.stderr)
    return exit_code


def _fail(
    code: str,
    observed: str,
    remediation: str,
    *,
    as_json: bool,
    source: str,
    next_command: str | None = None,
) -> int:
    return _emit_diagnostic(
        _typed_diagnostic(
            code, observed, remediation,
            next_command=next_command, source=source,
        ),
        as_json=as_json, exit_code=EXIT_INPUT,
    )


def _run_profile(args: argparse.Namespace) -> int:
    try:
        if args.inventory is None:
            inventory = collect_inventory(Path.cwd())
        else:
            inventory = PlatformInventory.model_validate_json(
                Path(args.inventory).expanduser().read_text(encoding="utf-8")
            )
        payload = profile_mapping(inventory)
    except ValidationError as exc:
        return _emit_diagnostic(_validation_diagnostic(exc, str(args.inventory or "<local>")), as_json=args.json, exit_code=EXIT_INPUT)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        return _fail("PLATFORM_INVENTORY_INVALID", f"cannot collect or read inventory: {exc}", "Fix the typed inventory JSON or run against a readable repository root.", as_json=args.json, source=str(args.inventory or "<local>"))
    if args.json:
        _emit_json(payload)
    else:
        print(render_profile(payload))
    return EXIT_OK


def _run_download(args: argparse.Namespace) -> int:
    try:
        manifest = load_asset_manifest(args.manifest)
        state = load_download_state(args.state)
        if args.pause is not None:
            state = pause_asset(manifest, state, args.pause)
            write_download_state(args.state, state)
        resume_diagnostic = None
        if args.resume is not None:
            state, asset = resume_asset(manifest, state, args.resume)
            write_download_state(args.state, state)
            resume_diagnostic = _typed_diagnostic(
                "DOWNLOAD_REQUIRES_OPERATOR",
                f"asset {asset.id} is not complete; Wangp did not fetch it",
                "Run the exact operator-reviewed command, verify the hash, then rerun status.",
                next_command=operator_download_command(asset),
                source=str(args.manifest),
            )
        payload = asset_report(manifest, state)
    except ValidationError as exc:
        return _emit_diagnostic(_validation_diagnostic(exc, str(args.manifest)), as_json=args.json, exit_code=EXIT_INPUT)
    except KeyError as exc:
        return _fail("ASSET_ID_UNKNOWN", str(exc.args[0]), "Use an id exactly as recorded in the asset manifest.", as_json=args.json, source=str(args.manifest), next_command="wgp first-run download --manifest <manifest> --state <state>")
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        return _fail("DOWNLOAD_STATE_INVALID", f"cannot read typed download inputs: {exc}", "Fix the manifest or state JSON; no download is attempted.", as_json=args.json, source=str(args.manifest))
    if args.json:
        machine: dict[str, Any] = dict(payload)
        if resume_diagnostic is not None:
            machine["diagnostics"] = [resume_diagnostic.mapping()]
        _emit_json(machine)
    else:
        for item in payload["assets"]:
            print(
                f"asset={item['id']} status={item['status']} "
                f"bytes={item['bytes_present']}/{item['size_bytes']}"
            )
        plan = dict(payload["download_plan"])
        print(
            f"would_download={plan['asset_count']} "
            f"total_size_bytes={plan['total_size_bytes']} "
            "wangp_downloads=false"
        )
        if resume_diagnostic is not None:
            print(render_diagnostic(resume_diagnostic), file=sys.stderr)
    return EXIT_INPUT if resume_diagnostic is not None else EXIT_OK


def _run_runtime(args: argparse.Namespace) -> int:
    try:
        config = load_runtime_config(args.config)
        payload = resolve_runtime(config, environ=os.environ)
    except ValidationError as exc:
        return _emit_diagnostic(_validation_diagnostic(exc, str(args.config)), as_json=args.json, exit_code=EXIT_INPUT)
    except LlmRuntimeError as exc:
        return _fail(exc.code, exc.observed, exc.remediation, as_json=args.json, source=str(args.config), next_command="wgp first-run runtime --config <config> --json")
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        return _fail("LLM_RUNTIME_CONFIG_INVALID", f"cannot read runtime configuration: {exc}", "Fix the typed local/external configuration; no provider is contacted.", as_json=args.json, source=str(args.config))
    if args.json:
        _emit_json(payload)
    else:
        print(render_runtime(payload))
    return EXIT_OK


def _run_recovery(args: argparse.Namespace) -> int:
    try:
        record = load_oom_record(args.record)
        payload = diagnose_oom(record)
    except ValidationError as exc:
        return _emit_diagnostic(_validation_diagnostic(exc, str(args.record)), as_json=args.json, exit_code=EXIT_INPUT)
    except RecoveryError as exc:
        return _fail(exc.code, exc.observed, exc.remediation, as_json=args.json, source=str(args.record), next_command="wgp first-run recovery --record <record> --json")
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        return _fail("OOM_RECORD_INVALID", f"cannot read failure record: {exc}", "Supply the recorded typed OOM evidence and original command.", as_json=args.json, source=str(args.record))
    if args.json:
        _emit_json(payload)
    else:
        print(render_recovery(payload))
    return EXIT_OK


def _run_remote(args: argparse.Namespace) -> int:
    config = load_host_config()
    payload = remote_report(config)
    if args.json:
        _emit_json(payload)
    else:
        print(render_remote(payload))
        for raw in payload["diagnostics"]:
            diagnostic = FailureDiagnostic(
                code=raw["code"],
                severity=raw["severity"],
                title=raw["title"],
                observed=raw["observed"],
                why=raw["why"],
                remediation=raw["remediation"],
                next_command=raw["next_command"],
                evidence_refs=tuple(raw["evidence_refs"]),
                metadata=dict(raw["metadata"]),
            )
            print(render_diagnostic(diagnostic), file=sys.stderr)
    return EXIT_OK if payload["ready"] else EXIT_CONFIGURATION


def _run_first_run(args: argparse.Namespace) -> int:
    if args.platform_verb == "profile":
        return _run_profile(args)
    if args.platform_verb == "download":
        return _run_download(args)
    if args.platform_verb == "runtime":
        return _run_runtime(args)
    if args.platform_verb == "recovery":
        return _run_recovery(args)
    return _run_remote(args)


def register_platform_parser(
    commands: argparse._SubParsersAction,
) -> argparse._SubParsersAction:
    first_run = commands.add_parser(
        "first-run",
        help="report local platform, asset, runtime, recovery, and host readiness",
    )
    modes = first_run.add_subparsers(dest="platform_verb", required=True)
    profile = modes.add_parser("profile", help="report local hardware and advisory profile")
    profile.add_argument("--inventory", help="typed inventory JSON; defaults to local collection")
    profile.add_argument("--json", action="store_true")
    download = modes.add_parser("download", help="report durable asset state without downloading")
    download.add_argument("--manifest", required=True)
    download.add_argument("--state", required=True)
    transition = download.add_mutually_exclusive_group()
    transition.add_argument("--pause", help="record one asset as paused")
    transition.add_argument("--resume", help="record one explicit resume request")
    download.add_argument("--json", action="store_true")
    runtime = modes.add_parser("runtime", help="preflight bundled-local or external LLM configuration")
    runtime.add_argument("--config", required=True)
    runtime.add_argument("--json", action="store_true")
    recovery = modes.add_parser("recovery", help="map recorded OOM evidence to bounded guidance")
    recovery.add_argument("--record", required=True)
    recovery.add_argument("--json", action="store_true")
    remote = modes.add_parser("remote", help="preview explicit host access without SSH")
    remote.add_argument("--json", action="store_true")
    first_run.set_defaults(handler=_run_first_run)
    return commands


__all__ = ["register_platform_parser"]
