"""The no-GPU ``wgp voice`` planning, package, and reconstruction surface."""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

from pydantic import ValidationError

from predict.speech_capabilities import (
    SpeechCapabilityError,
    SpeechMode,
    attach_manifest_model,
    load_speech_model_manifest,
)
from predict.voice_registry import export_voice_package, import_voice_package
from services.voice.segment_compiler import (
    compile_speech_request,
    enqueue_speech_plan,
    reconstruct_speech_database,
)
from wangp.diagnostics import FailureDiagnostic, render_diagnostic

EXIT_OK = 0
EXIT_INPUT = 2


def _error(exc: SpeechCapabilityError, *, as_json: bool) -> int:
    diagnostic = FailureDiagnostic(
        code=exc.code,
        severity="error",
        title="Typed speech request rejection",
        observed=exc.observed,
        why="Speech planning requires complete immutable inputs and never proves audio generation.",
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
        raise SpeechCapabilityError(
            "MODEL_MANIFEST_MISSING",
            "speech planning requires --models",
            "Supply an operator-recorded manifest; Wangp does not download models.",
        )
    source = Path(path).expanduser().resolve()
    payload = json.loads(source.read_text(encoding="utf-8"))
    return attach_manifest_model(payload, load_speech_model_manifest(models_path))


def _plan(args: argparse.Namespace, *, as_json: bool) -> int:
    expected_mode = None
    if args.voice_verb == "generate":
        expected_mode = SpeechMode.speech
    elif args.voice_verb == "clone":
        expected_mode = SpeechMode.voice_clone
    request = _load_request(args.request, args.models)
    if expected_mode is not None and request.mode is not expected_mode:
        raise SpeechCapabilityError(
            "SPEECH_MODE_MISMATCH",
            f"wgp voice {args.voice_verb} requires mode={expected_mode.value}, got {request.mode.value}",
            "Use generate for plain speech and clone for one/two-reference cloning.",
        )
    plan = compile_speech_request(request).mapping()
    record_ids = None
    database = Path(args.db).expanduser().resolve() if args.db else None
    if database is not None:
        record_ids = enqueue_speech_plan(plan, database)
        plan = dict(plan)
        plan["queue"] = {"database": str(database), "record_ids": record_ids, "executable_jobs": 0}
    if as_json:
        print(json.dumps(plan, sort_keys=True, separators=(",", ":")))
    else:
        summary = plan["summary"]
        print(
            f"mode={plan['mode']} engine={plan['engine']['family']} "
            f"segments={plan['segment_count']} capability_status={plan['capability_status']}"
        )
        print(
            f"assembly_order={','.join(str(item) for item in plan['assembly']['order'])} "
            f"gpu_work={str(summary['gpu_work']).lower()} "
            f"audio_created={str(summary['audio_created']).lower()} "
            f"queue_submitted={str(summary['queue_submitted']).lower()} "
            f"host_contact={str(summary['host_contact']).lower()}"
        )
        if record_ids is not None:
            print(f"records={','.join(record_ids)}")
    return EXIT_OK


def _run_voice(args: argparse.Namespace) -> int:
    as_json = bool(args.json)
    if args.voice_verb == "plan" and args.reconstruct:
        try:
            records = reconstruct_speech_database(args.db)
        except SpeechCapabilityError as exc:
            return _error(exc, as_json=as_json)
        except (OSError, KeyError, TypeError, ValueError, ValidationError, sqlite3.Error) as exc:
            return _error(
                SpeechCapabilityError(
                    "SPEECH_RECONSTRUCTION_INVALID",
                    f"cannot reconstruct database {args.db}: {exc}",
                    "Use a database emitted by wgp voice planning.",
                    next_command="wgp voice plan --db <plan.db> --reconstruct --json",
                ),
                as_json=as_json,
            )
        payload = {
            "schema_version": "wangp-dspy.speech-reconstruction/v1",
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
    if args.voice_verb == "import":
        try:
            payload = import_voice_package(args.package, args.destination)
        except SpeechCapabilityError as exc:
            return _error(exc, as_json=as_json)
        if as_json:
            print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
        else:
            character = payload["manifest"]["character"]
            print(
                f"character={character['character_id']} package_sha256={payload['package_sha256']} "
                f"audio_claimed=false host_contact=false destination={payload['destination']}"
            )
        return EXIT_OK
    try:
        if args.voice_verb == "export":
            request = _load_request(args.request, args.models)
            package, manifest = export_voice_package(request, args.package)
            payload = {
                "schema_version": manifest["schema_version"],
                "package": str(package),
                "package_sha256": _package_hash(package),
                "manifest": manifest,
                "audio_claimed": False,
                "host_contact": False,
            }
            if as_json:
                print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
            else:
                print(
                    f"character={manifest['character']['character_id']} "
                    f"package={package} package_sha256={payload['package_sha256']} "
                    "audio_claimed=false host_contact=false"
                )
            return EXIT_OK
        return _plan(args, as_json=as_json)
    except SpeechCapabilityError as exc:
        return _error(exc, as_json=as_json)
    except ValidationError as exc:
        return _error(
            SpeechCapabilityError(
                "SPEECH_REQUEST_INVALID",
                f"request validation failed: {exc.error_count()} field errors",
                "Fix the typed speech request, then rerun the deterministic plan.",
            ),
            as_json=as_json,
        )
    except FileNotFoundError as exc:
        return _error(
            SpeechCapabilityError(
                "SPEECH_REQUEST_MISSING",
                f"request does not exist: {exc.filename}",
                "Pass an existing request JSON file.",
            ),
            as_json=as_json,
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        return _error(
            SpeechCapabilityError(
                "SPEECH_REQUEST_INVALID",
                f"cannot read request: {exc}",
                "Fix the request JSON.",
            ),
            as_json=as_json,
        )


def _package_hash(package: Path) -> str:
    import hashlib

    return hashlib.sha256(package.read_bytes()).hexdigest()


def register_voice_parser(commands: argparse._SubParsersAction) -> argparse._SubParsersAction:
    voice = commands.add_parser("voice", help="plan speech and portable voices without GPU or host work")
    verbs = voice.add_subparsers(dest="voice_verb", required=True)
    for verb, help_text in (
        ("plan", "normalize or reconstruct one typed speech request"),
        ("generate", "plan plain speech without synthesis"),
        ("clone", "plan one/two-reference cloning without synthesis"),
        ("export", "write a portable character voice package"),
        ("import", "read a namespace-safe portable voice package"),
    ):
        parser = verbs.add_parser(verb, help=help_text)
        if verb in {"plan", "generate", "clone", "export"}:
            if verb == "plan":
                modes = parser.add_mutually_exclusive_group(required=True)
                modes.add_argument("--request", help="typed speech request JSON")
                modes.add_argument("--reconstruct", action="store_true", help="reconstruct segment recipes")
            else:
                parser.add_argument("--request", required=True, help="typed speech request JSON")
            parser.add_argument("--models", help="operator-supplied immutable model manifest")
        if verb == "import":
            parser.add_argument("--package", required=True, help=".wgpvoice portable package")
            parser.add_argument("--destination", required=True, help="new import directory")
        if verb == "export":
            parser.add_argument("--package", required=True, help="new .wgpvoice output path")
        if verb != "import":
            parser.add_argument("--db", help="new durable speech plan database")
        parser.add_argument("--json", action="store_true")
        parser.set_defaults(handler=_run_voice)
    return commands


__all__ = ["register_voice_parser"]
