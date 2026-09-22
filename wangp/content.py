"""The content-facing wrapper over the deterministic no-GPU planner."""

from __future__ import annotations

import contextlib
import io
import json
import os
import shlex
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from predict.content_brief import ContentBrief, ContentBriefError, load_content_brief
from wangp.config import (
    ENVIRONMENT_KEYS,
    HostConfig,
    load_host_config,
    missing_host_keys,
)
from wangp.diagnostics import FailureDiagnostic, redact_sensitive


class HostSubmissionError(RuntimeError):
    """A submission was requested before one complete host resolved."""


@dataclass(frozen=True)
class HostRequirement:
    configured: bool
    missing_keys: tuple[str, ...]


@dataclass(frozen=True)
class ContentRequest:
    """A redacted content summary plus the governed queue continuation."""

    title: str
    brief_hash: str
    summary: Mapping[str, Any]
    host: HostRequirement
    queue_command: str | None
    queue_command_template: str
    submission_requested: bool = False

    def mapping(self) -> dict[str, Any]:
        return redact_sensitive({
            "schema_version": "wangp-dspy.content-request/v1",
            "brief_hash": self.brief_hash,
            "what_will_be_generated": {
                "clip_count": self.summary["clip_count"],
                "speakers": list(self.summary["speakers"]),
                "planned_duration_s": self.summary["planned_duration_s"],
            },
            "host_requirement": {
                "configured": self.host.configured,
                "missing_keys": list(self.host.missing_keys),
                "contacted": False,
            },
            "governed_queue_command": (
                self.queue_command_template if self.queue_command else None
            ),
            "summary": dict(self.summary),
            "submission_requested": self.submission_requested,
        })

    def render(self) -> str:
        speakers = ",".join(dict.fromkeys(self.summary["speakers"]))
        missing = ",".join(self.host.missing_keys)
        host = (
            "configured (not contacted)"
            if self.host.configured
            else f"unconfigured (missing {missing}); no-GPU planning needs no host"
        )
        lines = [
            f"content={self.title}",
            (
                f"would_generate clip_count={self.summary['clip_count']} "
                f"speakers={speakers} "
                f"planned_duration_s={self.summary['planned_duration_s']}"
            ),
            f"host_requirement={host}",
            (
                f"governed_queue_command={self.queue_command}"
                if self.queue_command is not None
                else "governed_queue_command=not constructed (nothing was queued)"
            ),
            (
                f"gpu_work={str(self.summary['gpu_work']).lower()} "
                f"queue_submitted={str(self.summary['queue_submitted']).lower()}"
            ),
        ]
        if self.submission_requested:
            lines.append(
                "submission=queued; queue worker not executed"
            )
        return str(redact_sensitive("\n".join(lines)))


def _required_host_keys(config: HostConfig) -> tuple[str, ...]:
    missing = missing_host_keys(config)
    if config.wgp_python is None:
        missing += ("host.wgp_python",)
    return missing


def _check_submission_host(
    repository_root: Path, environ: Mapping[str, str]
) -> HostConfig:
    config = load_host_config(
        repository_root=repository_root, environ=environ
    )
    missing = _required_host_keys(config)
    if missing:
        variables = ", ".join(ENVIRONMENT_KEYS[key] for key in missing)
        raise HostSubmissionError(
            f"missing host keys: {', '.join(missing)} "
            f"(environment variables: {variables})"
        )
    return config


def _queue_command(run_dir: Path, *, stable: bool = False) -> str:
    database = "<run-dir>/jobs.db" if stable else (run_dir / "jobs.db").as_posix()
    return shlex.join([
        "uv", "run", "--frozen", "--extra", "dev", "python",
        "-m", "scripts.run_jobs", "--db", database,
    ])


def _enqueue_plan(payload: Mapping[str, Any], run_dir: Path, plan: Path) -> None:
    """Atomically persist the planned clips without draining or rendering."""

    from services.jobs.queue import JobQueue

    database = run_dir / "jobs.db"
    if database.exists():
        raise ValueError(f"queue database already exists: {database}")
    clips = payload.get("clips")
    if not isinstance(clips, list) or not clips:
        raise ValueError("content plan contains no clips to queue")
    staging = run_dir / f".jobs.db.{os.urandom(8).hex()}.tmp"
    queue = None
    try:
        queue = JobQueue(staging)
        previous: str | None = None
        for clip in clips:
            queued_clip = dict(clip)
            queued_clip["needs"] = previous
            previous = queue.submit(
                plan_ref=plan.name, clips=[queued_clip]
            )
        queue.close()
        queue = None
        os.replace(staging, database)
    except Exception:
        if queue is not None:
            queue.close()
        for suffix in ("", "-wal", "-shm"):
            Path(str(staging) + suffix).unlink(missing_ok=True)
        raise


def _host_requirement(
    repository_root: Path, environ: Mapping[str, str]
) -> HostRequirement:
    config = load_host_config(
        repository_root=repository_root, environ=environ
    )
    missing = _required_host_keys(config)
    return HostRequirement(configured=not missing, missing_keys=missing)


def _load_plan(path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload, payload["summary"]


def _validate_line_safe_dialogue(brief: ContentBrief) -> None:
    """Reject control characters before the line-oriented script is written."""

    for index, line in enumerate(brief.dialogue):
        text = line.text
        if any(ord(character) < 32 or ord(character) == 127 for character in text):
            raise ContentBriefError(
                f"dialogue[{index}].text contains a control character; use one "
                "line of text per dialogue turn"
            )


def build_content_request(
    brief: ContentBrief | str | Path,
    plates: str | Path,
    *,
    output: str | Path,
    run_dir: str | Path | None = None,
    submit: bool = False,
    repository_root: str | Path | None = None,
    environ: Mapping[str, str] | None = None,
) -> ContentRequest:
    """Validate and plan through the existing gateway, then summarize it."""

    from scripts.run_content_brief import main as plan_gateway

    environment = os.environ if environ is None else environ
    root = (
        Path(repository_root).expanduser().resolve()
        if repository_root is not None
        else Path(__file__).resolve().parents[1]
    )
    if submit:
        _check_submission_host(root, environment)
    else:
        _host_requirement(root, environment)

    validated = brief if isinstance(brief, ContentBrief) else load_content_brief(brief)
    _validate_line_safe_dialogue(validated)
    brief_path = validated.source_path
    if brief_path is None:
        raise ContentBriefError("content brief has no source path")
    plan_output = Path(output).expanduser().resolve()
    destination = (
        Path(run_dir).expanduser().resolve()
        if run_dir is not None
        else plan_output.parent / "run"
    )
    gateway_argv = [
        "--brief", str(Path(brief_path).expanduser().resolve()),
        "--plates", str(Path(plates).expanduser().resolve()),
        "--output", str(plan_output),
        "--run-dir", str(destination),
    ]
    # The gateway's path-oriented progress line is an implementation detail;
    # content owns the operator-facing summary.
    with contextlib.redirect_stdout(io.StringIO()):
        plan_gateway(gateway_argv)
    payload, summary = _load_plan(plan_output)
    summary = dict(summary)
    queue_command = None
    if submit:
        _enqueue_plan(payload, destination, plan_output)
        summary["dry_run"] = False
        summary["queue_submitted"] = True
        queue_command = _queue_command(destination)
    else:
        summary["queue_submitted"] = False
    return ContentRequest(
        title=str(payload.get("title", "")),
        brief_hash=str(payload.get("brief_hash", "")),
        summary=summary,
        host=_host_requirement(root, environment),
        queue_command=queue_command,
        queue_command_template=_queue_command(destination, stable=True),
        submission_requested=submit,
    )


def submission_diagnostic(
    repository_root: str | Path, environ: Mapping[str, str]
) -> FailureDiagnostic:
    """Return the one diagnostic for an incomplete --submit host."""

    try:
        _check_submission_host(Path(repository_root), environ)
    except HostSubmissionError as exc:
        message = str(exc)
    else:  # pragma: no cover - callers invoke this only after a failure
        message = "render host is not configured"
    return FailureDiagnostic(
        code="HOST_CONFIGURATION_INCOMPLETE",
        severity="error",
        title="Content submission requires a complete render host",
        observed=message,
        why="A partial host configuration cannot identify one safe renderer.",
        remediation=(
            "Set the named keys in the environment or wangp.toml, then review "
            "the resolved local capability report before submission."
        ),
        next_command="wgp doctor --capabilities",
        evidence_refs=(),
        metadata={"host_contact": False},
    )


__all__ = [
    "ContentRequest",
    "HostSubmissionError",
    "build_content_request",
    "submission_diagnostic",
]
