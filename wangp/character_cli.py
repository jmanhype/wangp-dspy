"""The no-GPU ``wgp character`` package and continuity surface."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pydantic import ValidationError

from predict.character_packages import CharacterPackageError
from services.character.package_service import (
    CharacterRegistry,
    bind_saved_voice,
    export_character_package,
    import_character_package,
    inspect_character_package,
    load_definition,
    recover_native_source,
    write_definition,
)
from services.character.plan_compiler import (
    compile_character_request,
    enqueue_plan,
    load_request,
    reconstruct_plan_database,
)
from wangp.diagnostics import FailureDiagnostic, render_diagnostic

EXIT_OK = 0
EXIT_INPUT = 2


def _error(exc: CharacterPackageError, *, as_json: bool) -> int:
    diagnostic = FailureDiagnostic(
        code=exc.code,
        severity="error",
        title="Typed portable character rejection",
        observed=exc.observed,
        why="Portable characters require immutable identity, appearance, voice, and continuity bindings.",
        remediation=exc.remediation,
        next_command=exc.next_command,
        metadata=exc.metadata,
    )
    if as_json:
        print(json.dumps({"diagnostics": [diagnostic.mapping()]}, sort_keys=True, separators=(",", ":")))
    else:
        print(render_diagnostic(diagnostic), file=sys.stderr)
    return EXIT_INPUT


def _print(payload: dict[str, object], *, as_json: bool, human: str) -> None:
    if as_json:
        print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    else:
        print(human)


def _run_character(args: argparse.Namespace) -> int:
    as_json = bool(args.json)
    verb = args.character_verb
    try:
        if verb == "create":
            definition = load_definition(args.definition)
            output = write_definition(definition, args.out)
            payload = {
                "schema_version": definition.schema_version,
                "definition": str(output),
                "character_id": definition.character_id,
                "generation_claimed": False,
            }
            _print(payload, as_json=as_json, human=f"character={definition.character_id} definition={output}")
            return EXIT_OK
        if verb == "bind-voice":
            definition = load_definition(args.definition)
            bound = bind_saved_voice(definition, args.voice)
            output = write_definition(bound, args.out)
            _print(
                {
                    "schema_version": bound.schema_version,
                    "definition": str(output),
                    "voice_binding_id": bound.voice.voice_binding_id if bound.voice else None,
                },
                as_json=as_json,
                human=f"voice_binding_id={bound.voice.voice_binding_id if bound.voice else ''} definition={output}",
            )
            return EXIT_OK
        if verb == "export":
            definition = load_definition(args.definition)
            package, manifest = export_character_package(definition, args.package)
            inspected = inspect_character_package(package)
            _print(
                inspected,
                as_json=as_json,
                human=(
                    f"character={manifest.character_id} package_sha256={inspected['package_sha256']} "
                    "generation_claimed=false host_contact=false"
                ),
            )
            return EXIT_OK
        if verb == "import":
            payload = import_character_package(args.package, args.destination)
            manifest = payload["manifest"]
            _print(
                payload,
                as_json=as_json,
                human=(
                    f"character={manifest['character_id']} "
                    f"package_sha256={payload['package_sha256']} "
                    f"members={len(payload['imported_members'])} "
                    "generation_claimed=false host_contact=false"
                ),
            )
            return EXIT_OK
        if verb == "show":
            payload = inspect_character_package(args.package)
            manifest = payload["manifest"]
            _print(
                payload,
                as_json=as_json,
                human=(
                    f"character={manifest['character_id']} speaker={manifest['speaker_label']} "
                    f"identity_sha256={manifest['identity_sha256']} "
                    f"appearance={len(manifest['appearance'])} modes={','.join(manifest['continuity']['modes'])}"
                ),
            )
            return EXIT_OK
        if verb == "recover":
            payload = recover_native_source(args.package, args.destination, role=args.role)
            _print(
                payload,
                as_json=as_json,
                human=f"recovered={payload['recovered']} sha256={payload['sha256']} transcoded=false",
            )
            return EXIT_OK
        if verb == "resolve":
            registry = CharacterRegistry.from_directory(args.registry)
            entry = registry.resolve(args.identity)
            payload = {
                "schema_version": entry.manifest.schema_version,
                "identity": args.identity,
                "character_id": entry.manifest.character_id,
                "speaker_label": entry.manifest.speaker_label,
                "identity_sha256": entry.manifest.identity_sha256,
                "package": str(entry.package_path),
                "package_sha256": entry.package_sha256,
            }
            _print(
                payload,
                as_json=as_json,
                human=f"character={entry.manifest.character_id} package_sha256={entry.package_sha256}",
            )
            return EXIT_OK
        if verb == "plan" and args.reconstruct:
            results = reconstruct_plan_database(args.db)
            payload = {
                "schema_version": "wangp-dspy.character-reconstruction/v1",
                "records": results,
                "all_match": all(item["match"] for item in results),
                "hidden_mutation": any(item["hidden_mutation"] for item in results),
            }
            _print(
                payload,
                as_json=as_json,
                human=(
                    f"records={len(results)} all_match={str(payload['all_match']).lower()} "
                    f"hidden_mutation={str(payload['hidden_mutation']).lower()}"
                ),
            )
            return EXIT_OK if payload["all_match"] else EXIT_INPUT

        if args.db is None and not args.dry_run:
            raise CharacterPackageError(
                "CHARACTER_QUEUE_PATH_MISSING",
                "character continuity planning requires --db",
                "Supply a new SQLite database path, or use --dry-run.",
            )
        request = load_request(args.request)
        plan = compile_character_request(request).mapping()
        record_ids: list[str] | None = None
        if not args.dry_run:
            record_ids = enqueue_plan(plan, args.db)
            plan = dict(plan)
            plan["queue"] = {
                "database": str(Path(args.db).expanduser().resolve()),
                "record_ids": record_ids,
                "executable_jobs": 0,
            }
        _print(
            plan,
            as_json=as_json,
            human=(
                f"mode={plan['mode']} operation={plan['operation']} "
                f"capability_status={plan['capability_status']}"
                "\n"
                "gpu_work=false media_generated=false queue_submitted=false host_contact=false"
            ),
        )
        return EXIT_OK
    except CharacterPackageError as exc:
        return _error(exc, as_json=as_json)
    except ValidationError as exc:
        failure = CharacterPackageError(
            "CHARACTER_REQUEST_INVALID",
            f"typed character request validation failed: {exc.error_count()} field errors",
            "Fix the typed request, then rerun the deterministic no-GPU plan.",
        )
        return _error(failure, as_json=as_json)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        failure = CharacterPackageError(
            "CHARACTER_PACKAGE_INVALID",
            f"cannot process portable character input: {exc}",
            "Use inputs emitted by wgp character without manual archive edits.",
        )
        return _error(failure, as_json=as_json)


def register_character_parser(
    commands: argparse._SubParsersAction,
) -> argparse._SubParsersAction:
    character = commands.add_parser(
        "character", help="plan portable characters without GPU or host work"
    )
    verbs = character.add_subparsers(dest="character_verb", required=True)
    for verb, help_text in (
        ("create", "normalize one typed character definition"),
        ("bind-voice", "bind a saved .wgpvoice package"),
        ("export", "write one portable .wgpcharacter package"),
        ("import", "read one namespace-safe portable package"),
        ("show", "inspect package hashes and identity"),
        ("recover", "copy the recorded native source without transcoding"),
        ("resolve", "resolve one registry identity"),
        ("plan", "validate image/video continuity or reconstruct records"),
    ):
        parser = verbs.add_parser(verb, help=help_text)
        parser.add_argument("--json", action="store_true")
        if verb in {"create", "bind-voice"}:
            parser.add_argument("--definition", required=True)
            parser.add_argument("--out", required=True)
            if verb == "bind-voice":
                parser.add_argument("--voice", required=True)
        elif verb == "export":
            parser.add_argument("--definition", required=True)
            parser.add_argument("--package", required=True)
        elif verb == "import":
            parser.add_argument("--package", required=True)
            parser.add_argument("--destination", required=True)
        elif verb == "show":
            parser.add_argument("--package", required=True)
        elif verb == "recover":
            parser.add_argument("--package", required=True)
            parser.add_argument("--destination", required=True)
            parser.add_argument("--role", default="native")
        elif verb == "resolve":
            parser.add_argument("--registry", required=True)
            parser.add_argument("--identity", required=True)
        elif verb == "plan":
            modes = parser.add_mutually_exclusive_group(required=True)
            modes.add_argument("--request")
            modes.add_argument("--reconstruct", action="store_true")
            parser.add_argument("--db")
            parser.add_argument("--dry-run", action="store_true")
        parser.set_defaults(handler=_run_character)
    return commands


__all__ = ["register_character_parser"]
