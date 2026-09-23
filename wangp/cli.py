"""Thin, stable ``wgp`` dispatcher over existing engine seams."""

from __future__ import annotations

import argparse
import contextlib
import json
import io
import os
import importlib
import re
import shlex
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping, Sequence

from predict.content_brief import (
    ContentBriefError,
    build_run_film_inputs,
    load_content_brief,
)
from predict.model_assets import AssetManifest, load_download_state
from services.jobs.queue import JobNotFoundError
from wangp import __version__
from wangp.content import (
    ContentRequest,
    HostSubmissionError,
    HostRequirement,
    build_content_request,
    submission_diagnostic,
    _validate_line_safe_dialogue,
)
from wangp.doctor import DoctorCheck, collect_doctor_checks
from wangp.environment import describe_capabilities
from wangp.config import load_host_config, missing_host_keys
from wangp.diagnostics import (
    FailureDiagnostic,
    classify_input_failure,
    classify_provenance_failures,
    redact_sensitive,
    render_diagnostic,
    render_diagnostic_mapping,
)
from wangp.image_cli import register_image_parser
from wangp.video_cli import register_video_parser
from wangp.music_cli import register_music_parser
from wangp.platform_cli import register_platform_parser
from wangp.sfx_cli import register_sfx_parser
from wangp.voice_cli import register_voice_parser
from wangp.character_cli import register_character_parser
from wangp.finish_cli import register_finish_parser
from wangp.queue_view import (
    collect_queue_review,
    collect_status,
    render_run_review,
    render_queue_review,
    render_status,
    review_run,
)
from wangp.release import ReleaseError, verify_release
from wangp.recipe import (
    RecipeError,
    build_recipe,
    load_recipe,
    pinned_field_count,
    verify_recipe,
    write_recipe,
)


EXIT_OK = 0
EXIT_INPUT = 2
EXIT_DOCTOR = 3
EXIT_INTERNAL = 4

REPOSITORY_ROOT_ENVIRONMENT = "WANGP_REPOSITORY_ROOT"


def _emit_json(payload: Mapping[str, Any]) -> None:
    print(json.dumps(
        redact_sensitive(dict(payload)), sort_keys=True,
        separators=(",", ":"), ensure_ascii=False
    ))


class RepositoryRootResolutionError(ValueError):
    """A repository-scoped verb has no safe Wangp checkout to use."""

    def __init__(self, diagnostic: FailureDiagnostic) -> None:
        super().__init__(diagnostic.observed)
        self.diagnostic = diagnostic


def _package_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _wangp_git_root(
    candidate: Path, *, candidate_must_be_root: bool = False
) -> Path | None:
    """Return a canonical Wangp Git root, or ``None`` for any other path."""

    try:
        completed = subprocess.run(
            ["git", "-C", str(candidate), "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if completed.returncode != 0:
        return None
    root = Path(completed.stdout.strip()).resolve()
    if candidate_must_be_root and candidate.resolve() != root:
        return None
    if not (root / "pyproject.toml").is_file():
        return None
    if not (root / "wangp" / "cli.py").is_file():
        return None
    return root


def _repository_diagnostic(
    observed: str, next_command: str
) -> FailureDiagnostic:
    return FailureDiagnostic(
        code="INPUT_INVALID",
        severity="error",
        title="A Wangp Git checkout is required",
        observed=observed,
        why=(
            "This repository-scoped verb records checkout provenance and must "
            "not attribute an installed package to a repository."
        ),
        remediation=(
            "Run inside a Wangp Git checkout, or point at one explicitly with "
            "--repository-root or WANGP_REPOSITORY_ROOT."
        ),
        next_command=next_command,
        evidence_refs=("<repository-root>",),
        metadata={"environment_variable": REPOSITORY_ROOT_ENVIRONMENT},
    )


def _explicit_repository_root(
    args: argparse.Namespace, next_command: str | None = None
) -> Path | None:
    selected = getattr(args, "repository_root", None)
    source = "--repository-root"
    if selected is None:
        value = os.environ.get(REPOSITORY_ROOT_ENVIRONMENT, "").strip()
        if not value:
            return None
        selected = Path(value)
        source = REPOSITORY_ROOT_ENVIRONMENT
    root = selected.expanduser().resolve()
    checked = _wangp_git_root(root)
    if checked is None:
        command = next_command or (
            "WANGP_REPOSITORY_ROOT=<repository> wgp plan --brief <brief> "
            "--plates <plates> --out <plan> --run-dir <run>"
        )
        raise RepositoryRootResolutionError(_repository_diagnostic(
            f"{source} does not name a Wangp Git checkout: <repository-root>",
            command,
        ))
    return checked


def _repository_root(
    args: argparse.Namespace, next_command: str
) -> Path:
    """Resolve one explicit or checkout-local Wangp repository root."""

    explicit = _explicit_repository_root(args, next_command)
    if explicit is not None:
        return explicit
    package_root = _package_root()
    if _wangp_git_root(package_root, candidate_must_be_root=True) is not None:
        return package_root
    cwd_root = _wangp_git_root(Path.cwd())
    if cwd_root is not None:
        return cwd_root
    raise RepositoryRootResolutionError(_repository_diagnostic(
        "wgp is installed outside a Git checkout and no repository root is set",
        next_command,
    ))


@contextlib.contextmanager
def _checkout_provenance(repository_root: Path):
    """Bind installed-package gateway calls to one explicit checkout."""

    from services.director import run_ledger

    original_identity = run_ledger.repository_identity
    plan_module = importlib.import_module("scripts.run_content_brief")
    original_root = plan_module.ROOT

    def identity(repo_root=None):
        return original_identity(
            repository_root if repo_root is None else repo_root
        )

    run_ledger.repository_identity = identity
    plan_module.ROOT = repository_root
    try:
        yield
    finally:
        run_ledger.repository_identity = original_identity
        plan_module.ROOT = original_root


def _error(message: str) -> None:
    print(f"wgp: error: {redact_sensitive(message)}", file=sys.stderr)


def _load_models(path: str | None) -> list[dict[str, str]] | AssetManifest | None:
    if path is None:
        return None
    source = Path(path).expanduser()
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read model manifest {source}: {exc}") from exc
    if isinstance(payload, dict) and isinstance(payload.get("assets"), list):
        try:
            return AssetManifest.model_validate(payload)
        except ValueError as exc:
            raise ValueError("typed model-assets manifest is invalid") from exc
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


def _content_host_requirement() -> HostRequirement:
    config = load_host_config(
        repository_root=_package_root(), environ=os.environ
    )
    missing = missing_host_keys(config)
    if config.wgp_python is None:
        missing += ("host.wgp_python",)
    return HostRequirement(
        configured=not missing, missing_keys=missing
    )


def _content_request_without_provenance(
    brief_path: Path, plates: Path, run_dir: Path
) -> ContentRequest:
    """Build the checkout-free content summary without claiming provenance."""

    brief = load_content_brief(brief_path)
    _validate_line_safe_dialogue(brief)
    build_run_film_inputs(brief, plates, run_dir=run_dir)
    return ContentRequest(
        title=brief.title,
        brief_hash=brief.brief_hash,
        summary={
            "clip_count": len(brief.dialogue),
            "speakers": [line.speaker for line in brief.dialogue],
            "planned_duration_s": round(sum(brief.durations_s), 6),
            "dry_run": True,
            "gpu_work": False,
            "queue_submitted": False,
        },
        host=_content_host_requirement(),
        queue_command=None,
        queue_command_template=(
            "uv run --frozen --extra dev python -m scripts.run_jobs "
            "--db <run-dir>/jobs.db"
        ),
    )


def _run_doctor(args: argparse.Namespace) -> int:
    if args.capabilities:
        if args.db is not None or args.probe_host:
            diagnostic = classify_input_failure(
                "--capabilities is a standalone local report and cannot be "
                "combined with --db or --probe-host",
                next_command="wgp doctor --capabilities",
            )
            if args.json:
                _emit_json({"diagnostics": [diagnostic.mapping()]})
            else:
                print(render_diagnostic(diagnostic), file=sys.stderr)
            return EXIT_INPUT
        capabilities_root = _explicit_repository_root(
            args,
            "WANGP_REPOSITORY_ROOT=<repository> wgp doctor --capabilities",
        )
        if capabilities_root is None:
            capabilities_root = _package_root()
        report = describe_capabilities(
            capabilities_root,
            environ=os.environ,
            models=args.models,
            download_state=args.download_state,
        )
        if report.mapping()["model_manifest"]["status"] == "invalid":
            diagnostic = classify_input_failure(
                "auto-discovered model manifest is invalid or empty",
                next_command="wgp doctor --capabilities",
            )
            if args.json:
                _emit_json({"diagnostics": [diagnostic.mapping()]})
            else:
                print(render_diagnostic(diagnostic), file=sys.stderr)
            return EXIT_INPUT
        if args.json:
            _emit_json(report.mapping())
        else:
            print(report.render())
        return EXIT_OK
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


def _content_diagnostic(
    message: str, args: argparse.Namespace
) -> FailureDiagnostic:
    """Redact caller-specific paths while retaining the typed failure."""

    brief = args.brief.expanduser().resolve()
    plates = args.plates.expanduser().resolve()
    replacements = {
        str(brief): "<brief>",
        str(plates): "<plates>",
    }
    if args.out is not None:
        replacements[str(args.out.expanduser().resolve())] = "<plan>"
    for source, replacement in replacements.items():
        message = message.replace(source, replacement)
    message = re.sub(r"/[^\s',]+", "<path>", message)
    source = "<plates>" if "plates" in message else "<brief>"
    return classify_input_failure(
        message,
        source=source,
        next_command=(
            "wgp content --brief <brief> --plates <plates> "
            "--out <plan>"
        ),
    )


def _run_content(args: argparse.Namespace) -> int:
    temporary_root: Path | None = None
    if args.out is None:
        temporary_root = Path(tempfile.mkdtemp(prefix="wangp-content-"))
        output = temporary_root / "plan.json"
    else:
        output = args.out.expanduser().resolve()
    run_dir = (
        args.run_dir.expanduser().resolve()
        if args.run_dir is not None
        else output.parent / "run"
    )
    repository_root = _explicit_repository_root(
        args,
        "WANGP_REPOSITORY_ROOT=<repository> wgp content --brief <brief> "
        "--plates <plates> --out <plan>",
    )
    try:
        if (
            repository_root is None
            and _wangp_git_root(
                _package_root(), candidate_must_be_root=True
            ) is None
        ):
            requirement = _content_host_requirement()
            if args.submit and requirement.missing_keys:
                raise HostSubmissionError(
                    "missing host keys: "
                    f"{', '.join(requirement.missing_keys)}"
                )
            if args.submit:
                raise RepositoryRootResolutionError(_repository_diagnostic(
                    "content --submit needs Wangp repository provenance",
                    "WANGP_REPOSITORY_ROOT=<repository> wgp content "
                    "--brief <brief> --plates <plates> --out <plan> --submit",
                ))
            request = _content_request_without_provenance(
                args.brief, args.plates, run_dir
            )
        else:
            if repository_root is None:
                repository_root = _package_root()
            build = lambda: build_content_request(
                args.brief,
                args.plates,
                output=output,
                run_dir=run_dir,
                submit=args.submit,
                repository_root=repository_root,
                environ=os.environ,
            )
            if repository_root == _package_root():
                request = build()
            else:
                with _checkout_provenance(repository_root):
                    request = build()
    except HostSubmissionError:
        diagnostic = submission_diagnostic(
            repository_root or _package_root(), os.environ
        )
        if args.json:
            _emit_json({"diagnostics": [diagnostic.mapping()]})
        else:
            print(render_diagnostic(diagnostic), file=sys.stderr)
        return EXIT_DOCTOR
    except RepositoryRootResolutionError:
        if temporary_root is not None:
            shutil.rmtree(temporary_root, ignore_errors=True)
        raise
    except (ContentBriefError, FileNotFoundError, OSError, ValueError) as exc:
        if temporary_root is not None:
            shutil.rmtree(temporary_root, ignore_errors=True)
        diagnostic = _content_diagnostic(str(exc), args)
        if args.json:
            _emit_json({"diagnostics": [diagnostic.mapping()]})
        else:
            print(render_diagnostic(diagnostic), file=sys.stderr)
        return EXIT_INPUT
    if args.json:
        _emit_json(request.mapping())
    else:
        print(request.render())
    return EXIT_OK


def _validate_brief(args: argparse.Namespace) -> int:
    brief = load_content_brief(args.brief)
    if args.json:
        _emit_json({"brief": brief.brief_hash, "valid": True})
    else:
        print(f"brief={brief.brief_hash} valid=true")
    return EXIT_OK


def _run_plan(args: argparse.Namespace) -> int:
    repository_root = _repository_root(
        args,
        "WANGP_REPOSITORY_ROOT=<repository> wgp plan --brief <brief> "
        "--plates <plates> --out <plan> --run-dir <run>",
    )
    output = args.out.expanduser().resolve()
    run_dir = (
        args.run_dir.expanduser().resolve()
        if args.run_dir is not None
        else output.parent / "run"
    )
    gateway_argv = ["--brief", str(args.brief.expanduser().resolve()), "--plates", str(args.plates.expanduser().resolve()), "--output", str(output), "--run-dir", str(run_dir)]
    plan_module = importlib.import_module("scripts.run_content_brief")
    plan_gateway = plan_module.main
    provenance = (
        contextlib.nullcontext()
        if repository_root == _package_root()
        else _checkout_provenance(repository_root)
    )
    with provenance:
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


def _run_recipe_write(args: argparse.Namespace) -> int:
    try:
        recipe = build_recipe(
            args.run,
            _repository_root(
                args,
                "WANGP_REPOSITORY_ROOT=<repository> wgp recipe write "
                "--run <run> --out <recipe>",
            ),
        )
        path, digest = write_recipe(recipe, args.out)
    except RecipeError as exc:
        diagnostic = classify_input_failure(
            str(exc), source=args.run, next_command=f"wgp review {shlex.quote(str(args.run))}")
        if args.json:
            _emit_json({"diagnostics": [diagnostic.mapping()]})
        else:
            print(render_diagnostic(diagnostic), file=sys.stderr)
        return EXIT_INPUT
    pinned = pinned_field_count(recipe)
    run_id = (recipe.get("pinned") or {}).get("run_id")
    if args.json:
        _emit_json({"recipe": {"path": str(path), "sha256": digest,
                               "schema_version": recipe["schema_version"],
                               "run_id": run_id, "pinned_fields": pinned}})
    else:
        print(f"recipe={path}")
        print(f"sha256={digest}")
        print(f"run_id={run_id} pinned_fields={pinned}")
    return EXIT_OK


def _run_recipe_verify(args: argparse.Namespace) -> int:
    try:
        recipe = load_recipe(args.recipe)
        drift = verify_recipe(
            args.recipe,
            args.run,
            _repository_root(
                args,
                "WANGP_REPOSITORY_ROOT=<repository> wgp recipe verify "
                "--recipe <recipe> --run <run>",
            ),
        )
    except RecipeError as exc:
        diagnostic = classify_input_failure(
            str(exc), source=args.recipe,
            next_command=f"wgp recipe write --run {shlex.quote(str(args.run))} --out <path>")
        if args.json:
            _emit_json({"diagnostics": [diagnostic.mapping()]})
        else:
            print(render_diagnostic(diagnostic), file=sys.stderr)
        return EXIT_INPUT
    if args.json:
        _emit_json({"recipe": {"path": str(Path(args.recipe).expanduser().resolve()),
                               "run_id": (recipe.get("pinned") or {}).get("run_id"),
                               "drift": drift, "drift_count": len(drift),
                               "verified": not drift}})
    else:
        print(f"recipe={Path(args.recipe).expanduser().resolve()}")
        for entry in drift:
            print(f"drift field={entry['field']} status={entry['status']} "
                  f"expected={entry['expected']!r} observed={entry['observed']!r}")
        print(f"drift={len(drift)} verified={'true' if not drift else 'false'}")
    return EXIT_OK if not drift else EXIT_INPUT


def _run_release_verify(args: argparse.Namespace) -> int:
    try:
        repository_root = _repository_root(
            args,
            "WANGP_REPOSITORY_ROOT=<repository> wgp release verify",
        )
        verification = verify_release(repository_root)
    except ReleaseError as exc:
        diagnostic = classify_input_failure(
            str(exc), source=str(repository_root),
            next_command="wgp release verify --json")
        if args.json:
            payload = {"diagnostics": [diagnostic.mapping()]}
            if exc.verification is not None:
                payload["release"] = redact_sensitive(
                    exc.verification.mapping())
            _emit_json(payload)
        else:
            if exc.verification is not None:
                for check in exc.verification.checks:
                    expected = redact_sensitive(check.expected)
                    observed = redact_sensitive(check.observed)
                    print(
                        f"check={check.name} status={check.status} "
                        f"expected={expected!r} observed={observed!r}")
                print("release=not_ready")
            print(render_diagnostic(diagnostic), file=sys.stderr)
        return EXIT_INPUT

    if args.json:
        _emit_json({"release": redact_sensitive(verification.mapping())})
    else:
        print(f"version={verification.version}")
        for check in verification.checks:
            print(f"check={check.name} status={check.status}")
        print(f"tag-ready={verification.tag}\n"
              f"tag_created={str(verification.tag_created).lower()}\n"
              f"{verification.guidance}\nrelease=ready")
    return EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    """Build the stable parser without registering unstable verbs."""

    parser = argparse.ArgumentParser(
        prog="wgp", description="Wangp planning, readiness, and review CLI"
    )
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="verb", required=True)
    register_video_parser(commands)
    register_image_parser(commands)
    register_music_parser(commands)
    register_platform_parser(commands)
    register_sfx_parser(commands)
    register_voice_parser(commands)
    register_character_parser(commands)
    register_finish_parser(commands)

    doctor = commands.add_parser(
        "doctor", help="report local readiness and optionally probe a host"
    )
    doctor.add_argument("--json", action="store_true")
    doctor.add_argument(
        "--capabilities",
        action="store_true",
        help="report honest first-run capabilities without probing anything",
    )
    doctor.add_argument("--db", help="also check one queue database")
    doctor.add_argument("--models", help="JSON model manifest")
    doctor.add_argument(
        "--download-state",
        help="typed durable state for a model-assets/v1 capability manifest",
    )
    doctor.add_argument(
        "--repository-root", type=Path,
        help="Wangp Git checkout for repository capability discovery",
    )
    doctor.add_argument(
        "--probe-host",
        action="store_true",
        help="run five existing remote checks; never implied",
    )
    doctor.set_defaults(
        handler=_run_doctor,
        models=None,
        download_state=None,
        capabilities=False,
    )

    content = commands.add_parser(
        "content", help="turn a brief and plates into a governed content summary"
    )
    content.add_argument("--brief", required=True, type=Path)
    content.add_argument("--plates", required=True, type=Path)
    content.add_argument("--out", type=Path)
    content.add_argument("--run-dir", type=Path)
    content.add_argument("--submit", action="store_true")
    content.add_argument("--json", action="store_true")
    content.add_argument(
        "--repository-root", type=Path,
        help="Wangp Git checkout to use for repository provenance",
    )
    content.set_defaults(handler=_run_content)

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
    plan.add_argument(
        "--repository-root", type=Path,
        help="Wangp Git checkout to use for repository provenance",
    )
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

    recipe = commands.add_parser(
        "recipe", help="write or verify a versioned render recipe")
    recipe_commands = recipe.add_subparsers(dest="recipe_verb", required=True)
    recipe_write = recipe_commands.add_parser(
        "write", help="pin a finished run's logical recipe to a file")
    recipe_write.add_argument("--run", required=True, help="run review-bundle directory")
    recipe_write.add_argument("--out", required=True, help="recipe output path")
    recipe_write.add_argument("--json", action="store_true")
    recipe_write.add_argument(
        "--repository-root", type=Path,
        help="Wangp Git checkout to use for repository provenance",
    )
    recipe_write.set_defaults(handler=_run_recipe_write)
    recipe_verify = recipe_commands.add_parser(
        "verify", help="verify a run against its recipe and report drift")
    recipe_verify.add_argument("--recipe", required=True, help="recipe file to verify")
    recipe_verify.add_argument("--run", required=True, help="run review-bundle directory")
    recipe_verify.add_argument("--json", action="store_true")
    recipe_verify.add_argument(
        "--repository-root", type=Path,
        help="Wangp Git checkout to use for repository provenance",
    )
    recipe_verify.set_defaults(handler=_run_recipe_verify)

    release = commands.add_parser("release",
                                  help="verify local release readiness without releasing")
    release_commands = release.add_subparsers(dest="release_verb", required=True)
    release_verify = release_commands.add_parser(
        "verify", help="check version, changelog, recipe, and tree readiness")
    release_verify.add_argument("--json", action="store_true")
    release_verify.add_argument(
        "--repository-root", type=Path,
        help="Wangp Git checkout to use for repository provenance",
    )
    release_verify.set_defaults(handler=_run_release_verify)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Dispatch one stable verb using the documented exit-code contract."""

    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.verb == "doctor":
            try:
                models = _load_models(args.models)
                download_state = (
                    load_download_state(args.download_state)
                    if args.download_state is not None else None
                )
            except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
                source = (
                    str(Path(args.models).expanduser().resolve())
                    if isinstance(args.models, str) else None
                )
                message = str(exc).replace(source, "<models>") if source else str(exc)
                diagnostic = classify_input_failure(
                    message, source="<models>",
                    next_command="wgp doctor --capabilities --models <models>",
                )
                if args.json:
                    _emit_json({"diagnostics": [diagnostic.mapping()]})
                else:
                    print(render_diagnostic(diagnostic), file=sys.stderr)
                return EXIT_INPUT
            args.models = models
            args.download_state = download_state
        return int(args.handler(args))
    except RepositoryRootResolutionError as exc:
        if getattr(args, "json", False):
            _emit_json({"diagnostics": [exc.diagnostic.mapping()]})
        else:
            print(render_diagnostic(exc.diagnostic), file=sys.stderr)
        return EXIT_INPUT
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
