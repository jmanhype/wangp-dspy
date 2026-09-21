"""Typed, read-only operator diagnostics for infrastructure and gate failures.

The classifier consumes durable preflight, queue, and review shapes without
changing admission, gate, retry, or provenance decisions.  Diagnostics may read
referenced evidence files, but never mutate queues, hosts, models, or artifacts.
"""
from __future__ import annotations

import json
import re
import shlex
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Mapping, Sequence

from services.jobs.preflight import PreflightCheck, PreflightReport
from wangp.config import ENVIRONMENT_KEYS, HostConfig, missing_host_keys


_SECRET_ASSIGNMENT = re.compile(
    r"(?i)\b(api[_-]?key|token|password|secret|authorization)\b\s*[:=]\s*\S+"
)
_BEARER = re.compile(r"(?i)\bbearer\s+[a-z0-9._~+/=-]+", re.IGNORECASE)
_LONG_KEY = re.compile(r"\b(?:sk|rk)-[A-Za-z0-9_-]{16,}\b")
_DISK = re.compile(
    r"(?P<available>\d+(?:\.\d+)?)G free on (?P<path>.+?) "
    r"\(min (?P<minimum>\d+(?:\.\d+)?)G\)$"
)
_MODEL_MISSING = re.compile(r"(?<!hash )missing\s+(?P<path>.+?)(?:\s*:|\s*$)")
_MODEL_HASH = re.compile(
    r"(?:sha256 mismatch|hash mismatch)\s+(?P<path>.+?)[:(]\s*expected\s+"
    r"(?P<expected>[0-9a-f]+)…,?\s+"
    r"got\s+(?P<actual>[0-9a-f]*)…",
    re.IGNORECASE,
)


def redact_sensitive(value: Any) -> Any:
    """Redact credential-shaped text while retaining paths, states, and hashes."""

    if isinstance(value, str):
        value = _SECRET_ASSIGNMENT.sub(
            lambda match: f"{match.group(1)}=<redacted>", value
        )
        value = _BEARER.sub("Bearer <redacted>", value)
        return _LONG_KEY.sub("<redacted-key>", value)
    if isinstance(value, Mapping):
        return {str(key): redact_sensitive(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [redact_sensitive(item) for item in value]
    return value


@dataclass(frozen=True)
class FailureDiagnostic:
    """One stable machine/human diagnostic value object."""

    code: str
    severity: str
    title: str
    observed: str
    why: str
    remediation: str
    next_command: str | None = None
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def mapping(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "severity": self.severity,
            "title": self.title,
            "observed": redact_sensitive(self.observed),
            "why": self.why,
            "remediation": self.remediation,
            "next_command": self.next_command,
            "evidence_refs": list(self.evidence_refs),
            "metadata": redact_sensitive(dict(self.metadata)),
        }


def render_diagnostic(diagnostic: FailureDiagnostic) -> str:
    """Render the diagnostic contract without a traceback or secret value."""

    lines = [
        f"diagnostic code={diagnostic.code} severity={diagnostic.severity}: {diagnostic.title}",
        f"  observed: {redact_sensitive(diagnostic.observed)}",
        f"  why: {redact_sensitive(diagnostic.why)}",
        f"  remediation: {redact_sensitive(diagnostic.remediation)}",
    ]
    if diagnostic.next_command:
        lines.append(f"  next: {diagnostic.next_command}")
    lines.extend(f"  evidence: {path}" for path in diagnostic.evidence_refs)
    if diagnostic.metadata:
        lines.append(
            "  details: "
            + json.dumps(
                redact_sensitive(diagnostic.metadata), sort_keys=True, ensure_ascii=False
            )
        )
    return "\n".join(lines)


def render_diagnostic_mapping(payload: Mapping[str, Any]) -> str:
    """Render a previously serialized diagnostic without widening its shape."""

    values = {key: payload[key] for key in (
        "code", "severity", "title", "observed", "why", "remediation"
    )}
    return render_diagnostic(FailureDiagnostic(
        **values, next_command=payload.get("next_command"),
        evidence_refs=tuple(payload.get("evidence_refs", ())),
        metadata=dict(payload.get("metadata", {})),
    ))


def _ssh_cause(detail: str) -> tuple[str, str, str, str]:
    lowered = detail.casefold()
    if "host key verification failed" in lowered or "host key" in lowered:
        return (
            "HOST_KEY_REJECTED",
            "Render host rejected an unknown or changed host key",
            "SSH stopped before authentication because the host key is unknown or changed.",
            "Verify the host fingerprint out of band and update known_hosts intentionally; never disable host-key checking.",
        )
    if "permission denied" in lowered or "authentication failed" in lowered:
        return (
            "HOST_AUTHENTICATION_FAILED",
            "Render host rejected the configured SSH identity",
            "The host was reachable, but SSH did not accept the available identity.",
            "Load the correct key/agent identity or correct the SSH alias; do not put a secret in Wangp configuration.",
        )
    return (
        "HOST_UNREACHABLE",
        "Render host is unreachable",
        "SSH could not establish the configured connection.",
        "Verify network/VPN reachability and the resolved SSH alias, then rerun the explicit doctor probe.",
    )


def _host_unreachable(check: PreflightCheck, target: str | None) -> FailureDiagnostic:
    code, title, why, remediation = _ssh_cause(check.detail)
    command = (
        f"ssh -o BatchMode=yes {shlex.quote(target)} true"
        if target
        else "wgp doctor --probe-host --models models.json"
    )
    if code == "HOST_KEY_REJECTED" and target:
        command = f"ssh-keygen -F {shlex.quote(target)}"
    return FailureDiagnostic(
        code=code,
        severity="error",
        title=title,
        observed=f"ssh_reachable failed for {target or 'configured target'}: {check.detail}",
        why=why,
        remediation=remediation,
        next_command=command,
        evidence_refs=("preflight:ssh_reachable",),
        metadata={"check_kind": "ssh_reachable", "target": target, "cause": code},
    )


def _model_diagnostic(problem: str) -> FailureDiagnostic:
    missing = _MODEL_MISSING.search(problem)
    mismatch = _MODEL_HASH.search(problem)
    if mismatch:
        path, expected, actual = mismatch.groups()
        path = path.rstrip()
        return FailureDiagnostic(
            code="MODEL_HASH_MISMATCH",
            severity="error",
            title="Model file hash does not match the manifest",
            observed=f"{path}: expected sha256 {expected}…, got {actual or '<unavailable>'}…",
            why="The file exists but its bytes are not the manifest-recorded model.",
            remediation="Restore the exact manifest-recorded model bytes; Wangp will not download or overwrite them.",
            next_command="wgp doctor --models models.json",
            evidence_refs=(path, "preflight:model_files"),
            metadata={
                "path": path,
                "expected_sha256_prefix": expected,
                "actual_sha256_prefix": actual,
            },
        )
    if missing:
        path = missing.group("path").rstrip(": ")
        return FailureDiagnostic(
            code="MODEL_MISSING",
            severity="error",
            title="Manifest-declared model file is absent",
            observed=f"missing model path: {path}",
            why="Preflight refuses renderer admission when a required model file is absent.",
            remediation="Place the manifest-recorded file at that exact path; Wangp will not download it.",
            next_command="wgp doctor --models models.json",
            evidence_refs=(path, "preflight:model_files"),
            metadata={"path": path},
        )
    return FailureDiagnostic(
        code="MODEL_CHECK_FAILED",
        severity="error",
        title="Model manifest verification failed",
        observed=problem or "preflight model check failed",
        why="The model check did not produce a missing-path or hash comparison.",
        remediation="Inspect the manifest entry and rerun doctor; do not alter the expected hash.",
        next_command="wgp doctor --models models.json",
        evidence_refs=("preflight:model_files",),
        metadata={"check_kind": "model_files"},
    )


def _disk_diagnostic(check: PreflightCheck) -> FailureDiagnostic:
    match = _DISK.search(check.detail)
    failed = re.search(r"df\s+(?P<path>.+?)\s+rc=", check.detail)
    available = float(match.group("available")) if match else None
    minimum = float(match.group("minimum")) if match else None
    path = (
        match.group("path") if match else
        (failed.group("path") if failed else "unknown render path")
    )
    measured = match is not None
    return FailureDiagnostic(
        code="DISK_HEADROOM_BELOW_THRESHOLD" if measured else "DISK_CHECK_FAILED",
        severity="error",
        title=(
            "Render volume has insufficient free space" if measured
            else "Render volume disk measurement failed"
        ),
        observed=check.detail or "disk_headroom failed",
        why=(
            f"The render volume reports {available!r} GiB free, below the required {minimum!r} GiB."
            if measured else "The render volume's available-space measurement could not be read."
        ),
        remediation=(
            "Preserve needed evidence, then manually free or select sanctioned storage; Wangp never deletes artifacts automatically."
            if measured else "Rerun the read-only disk probe after restoring host reachability."
        ),
        next_command=f"df -BG --output=avail {shlex.quote(path)}",
        evidence_refs=(path, "preflight:disk_headroom"),
        metadata={
            "path": path,
            "available_gb": available,
            "minimum_gb": minimum,
            "check_kind": "disk_headroom",
        },
    )


def classify_preflight(
    report: PreflightReport, *, target: str | None = None
) -> tuple[FailureDiagnostic, ...]:
    """Classify failed preflight checks without rerunning a probe."""

    diagnostics: list[FailureDiagnostic] = []
    for check in report.failed_checks:
        if check.kind == "ssh_reachable":
            diagnostics.append(_host_unreachable(check, target))
        elif check.kind == "model_files":
            diagnostics.extend(_model_diagnostic(item) for item in check.detail.split("; "))
        elif check.kind == "disk_headroom":
            diagnostics.append(_disk_diagnostic(check))
        elif check.kind in {"gpu_state", "qc_available"}:
            gpu = check.kind == "gpu_state"
            diagnostics.append(FailureDiagnostic(
                "GPU_STATE_FAILED" if gpu else "QC_UNAVAILABLE", "error",
                "Render GPU is unavailable or busy" if gpu else "QC service is unavailable",
                check.detail,
                "The declared GPU/QC precondition did not pass before renderer admission.",
                "Coordinate GPU/QC recovery and rerun the explicit probe; diagnostics take no action.",
                "wgp doctor --probe-host --models models.json",
                (f"preflight:{check.kind}",), {"check_kind": check.kind},
            ))
        else:
            diagnostics.append(FailureDiagnostic(
                "PREFLIGHT_UNKNOWN", "error", "Unrecognized preflight check failed", check.detail,
                "A failed check is outside the diagnosed infrastructure catalog.",
                "Inspect the check evidence and file the unknown kind rather than bypassing preflight.",
                None, (f"preflight:{check.kind}",), {"check_kind": check.kind},
            ))
    return tuple(diagnostics)


def classify_host_configuration(config: HostConfig) -> FailureDiagnostic | None:
    """Return the shared diagnostic for an incomplete explicit render host."""

    missing = missing_host_keys(config)
    if not missing:
        return None
    variables = [ENVIRONMENT_KEYS[key] for key in missing]
    target = config.target.value if config.target is not None else None
    return FailureDiagnostic(
        code="HOST_CONFIGURATION_INCOMPLETE",
        severity="error",
        title="Explicit render probe cannot resolve a complete host",
        observed=f"missing {', '.join(missing)}; resolved target={target or 'unconfigured'}",
        why="A partial host configuration cannot identify one safe renderer machine.",
        remediation=(
            f"Set {', '.join(variables)} or the corresponding [host] keys in "
            f"{config.repository_config} or {config.user_config}, then review resolution with doctor."
        ),
        next_command="wgp doctor",
        evidence_refs=(str(config.repository_config), str(config.user_config)),
        metadata={
            "missing_keys": list(missing),
            "environment_keys": variables,
            "target": target,
        },
    )


def _evidence_paths(record: Any) -> list[str]:
    paths: list[str] = []
    clips = record.clips if isinstance(record.clips, list) else []
    for clip in clips:
        if not isinstance(clip, Mapping):
            continue
        for key in ("log", "mp4", "qc_evidence_path"):
            value = clip.get(key)
            if isinstance(value, str) and value.strip() and value not in paths:
                paths.append(value)
        verdict = clip.get("qc_verdict")
        if isinstance(verdict, Mapping) and isinstance(verdict.get("path"), str):
            if verdict["path"] not in paths:
                paths.append(verdict["path"])
        for history_key in (
            "whisper_retry_history", "vision_rejections", "av_sync_rejections"
        ):
            history = clip.get(history_key)
            for entry in history if isinstance(history, list) else []:
                if not isinstance(entry, Mapping):
                    continue
                for key in ("qc_evidence_path", "mp4", "log"):
                    value = entry.get(key)
                    if isinstance(value, str) and value.strip() and value not in paths:
                        paths.append(value)
    return paths


def _read_json(path: str) -> Any:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None


def _metric_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _gate_summary(record: Any) -> tuple[list[str], dict[str, Any], list[str]]:
    paths = [path for path in _evidence_paths(record) if path.endswith("qc-evidence.json")]
    metrics: dict[str, Any] = {}
    gates: list[str] = []
    reason = str(record.failure_detail or "gate rejection reason unavailable")
    for path in paths:
        payload = _read_json(path)
        if not isinstance(payload, Mapping):
            continue
        whisper = payload.get("whisper_gates")
        if isinstance(whisper, Mapping):
            metrics["whisper"] = {}
            for phase in ("pre", "post"):
                item = whisper.get(phase)
                if isinstance(item, Mapping):
                    metrics["whisper"][phase] = {
                        "score": _metric_number(item.get("score")),
                        "pass_bar": _metric_number(item.get("pass_bar")),
                        "passed": item.get("passed"),
                        "transcript": item.get("transcript"),
                    }
                    if item.get("passed") is False and f"whisper_{phase}" not in gates:
                        gates.append(f"whisper_{phase}")
        vision = payload.get("vision_judge") or payload.get("vision_rejection")
        scores = vision.get("scores") if isinstance(vision, Mapping) else None
        if not isinstance(scores, Mapping) and isinstance(vision, Mapping):
            scores = vision
        if isinstance(scores, Mapping):
            boxes = scores.get("speaker_mouth_bboxes")
            if not isinstance(boxes, list) and isinstance(vision, Mapping):
                boxes = vision.get("speaker_mouth_bboxes")
            metrics["vision"] = {
                "action_match": _metric_number(scores.get("action_match")),
                "speaker_attribution": _metric_number(scores.get("speaker_attribution")),
                "mouth_activity": _metric_number(scores.get("mouth_activity")),
                "pass_bar": _metric_number(scores.get("pass_bar")),
                "passed": scores.get(
                    "passed", vision.get("passed") if isinstance(vision, Mapping) else None
                ),
                "speaker_mouth_bboxes": boxes,
                "speaker_mouth_center_spread": (
                    vision.get("speaker_mouth_center_spread")
                    if isinstance(vision, Mapping) else None
                ),
            }
            if metrics["vision"]["passed"] is False and "identity_action_vision" not in gates:
                gates.append("identity_action_vision")
            if not isinstance(boxes, list) or len(boxes) != 3:
                gates.append("mouth_box_localization")
        sync = payload.get("av_sync_gate")
        if isinstance(sync, Mapping):
            metrics["syncnet"] = {
                "confidence": _metric_number(sync.get("confidence")),
                "offset_frames_25fps": sync.get("offset_frames_25fps"),
                "offset_seconds": _metric_number(sync.get("offset_seconds")),
                "passed": sync.get("passed"),
                "model_sha256": sync.get("model_sha256"),
            }
            if sync.get("passed") is False and "syncnet_audiovisual_sync" not in gates:
                gates.append("syncnet_audiovisual_sync")
    if not gates:
        lowered = reason.casefold()
        if "whisper" in lowered:
            gates.append("whisper")
        elif "mouth" in lowered and ("bbox" in lowered or "box" in lowered):
            gates.append("mouth_box_localization")
        elif "vision" in lowered or "visual gate" in lowered:
            gates.append("identity_action_vision")
        elif "syncnet" in lowered or "audiovisual" in lowered:
            gates.append("syncnet_audiovisual_sync")
        else:
            gates.append(str(record.failure_class or "qc"))
    return gates, {"gate_metrics": metrics, "recorded_reason": reason}, paths


def _review_command(db_path: str | Path | None, job_id: str) -> str:
    database = shlex.quote(str(db_path or "jobs.db"))
    return f"wgp review --db {database} --job {shlex.quote(job_id)}"


def _retry_command(db_path: str | Path | None, *, dead_letter: bool) -> str:
    database = shlex.quote(str(db_path or "jobs.db"))
    if dead_letter:
        return (
            f".venv/bin/python scripts/run_jobs.py --db {database} "
            "--retry-dead-letter --reason \"operator reviewed preserved evidence\""
        )
    return f".venv/bin/python scripts/run_jobs.py --db {database} --retry-failed"


def _with_queue_context(
    diagnostic: FailureDiagnostic,
    metadata: Mapping[str, Any],
    evidence_refs: Sequence[str],
) -> FailureDiagnostic:
    return replace(
        diagnostic,
        evidence_refs=tuple(evidence_refs),
        metadata={**metadata, **diagnostic.metadata},
    )


def classify_queue_failure(
    record: Any,
    history: Sequence[Mapping[str, object]],
    *,
    db_path: str | Path | None = None,
) -> FailureDiagnostic:
    """Classify one durable job failure while retaining immutable evidence."""

    failure_class = str(record.failure_class or "")
    detail = str(record.failure_detail or "no detail recorded")
    attempts = list(history)
    paths = _evidence_paths(record)
    base_metadata: dict[str, Any] = {
        "job_id": record.job_id,
        "state": record.state,
        "failure_class": failure_class,
        "failure_detail": detail,
        "attempt_count": len(attempts),
        "failure_count": record.failure_count,
        "retryable": bool(record.retryable),
    }
    review = _review_command(db_path, record.job_id)
    evidence_refs = [str(db_path), *paths] if db_path else paths

    if record.state not in {"failed", "dead_letter"} or not failure_class:
        return FailureDiagnostic(
            "NO_ACTIVE_FAILURE", "info", "No active failure to diagnose",
            f"job {record.job_id} state={record.state} with no current failure class",
            "The durable row is not a failed or dead-letter diagnostic target.",
            "No action is required.",
            None, tuple(evidence_refs), base_metadata,
        )

    if record.state == "dead_letter":
        metadata = dict(base_metadata)
        if failure_class in {"qc_gate", "qc_reject"}:
            gates, gate_data, gate_paths = _gate_summary(record)
            metadata.update(gate_data, gates=gates)
            evidence_refs.extend(path for path in gate_paths if path not in evidence_refs)
        metadata["next_commands"] = [review, _retry_command(db_path, dead_letter=True)]
        return FailureDiagnostic(
            "RETRY_EXHAUSTED", "error", "Retry budget exhausted; job is dead-lettered",
            f"job {record.job_id} recorded {record.failure_count} "
            f"{failure_class or 'unknown'} failure(s) across {len(attempts)} immutable "
            f"attempt row(s); retryable={str(bool(record.retryable)).lower()}",
            "The queue reached its terminal retry policy and will not retry this job automatically.",
            "Inspect preserved attempts/evidence first; only reopen with an audited reason after the cause is fixed.",
            _retry_command(db_path, dead_letter=True), tuple(evidence_refs), metadata,
        )

    if failure_class in {"qc_gate", "qc_reject"}:
        gates, gate_data, gate_paths = _gate_summary(record)
        metadata = {**gate_data, **base_metadata, "gates": gates}
        evidence_refs.extend(path for path in gate_paths if path not in evidence_refs)
        commands = [review]
        if record.state == "failed" and record.retryable:
            commands.append(_retry_command(db_path, dead_letter=False))
            remediation = (
                "Inspect the exact scores and preserved attempt below; fix the effective input or gate implementation. "
                "Do not change a threshold or bypass the gate. "
                "If still eligible, the existing audited retry command is: " + commands[-1]
            )
        else:
            remediation = "Inspect the exact scores and preserved attempt below; do not change a threshold or bypass the gate."
        metadata["next_commands"] = commands
        return FailureDiagnostic(
            "GATE_REJECTED", "error", "A declared QC gate refused the attempt",
            f"gate(s): {', '.join(gates)}; recorded reason: {metadata['recorded_reason']}",
            "The recorded gate evidence did not meet its declared pass bar or contract.",
            remediation, review, tuple(evidence_refs), metadata,
        )

    if record.state == "failed" and not record.retryable:
        return FailureDiagnostic(
            "DETERMINISTIC_REPLAY_BLOCKED", "error", "Repeated failure signature disabled retry",
            f"job {record.job_id} repeated failure signature for "
            f"{failure_class or 'unknown'}; retryable=false after {len(attempts)} attempt row(s)",
            "Retrying identical effective renderer inputs would reproduce the same failure.",
            "Change an effective input such as seed/prompt/refs/guide, or obtain explicit operator replay authorization; never set allow_deterministic_replay merely to loop.",
            review, tuple(evidence_refs), base_metadata,
        )

    lowered = detail.casefold()
    if failure_class == "preflight" or "ssh" in lowered or "renderhosterror" in lowered:
        return _with_queue_context(
            _host_unreachable(PreflightCheck("ssh_reachable", False, detail), None),
            base_metadata, evidence_refs,
        )

    if failure_class in {"model_missing", "model_hash_mismatch"} or "model" in lowered:
        return _with_queue_context(_model_diagnostic(detail), base_metadata, evidence_refs)
    if _DISK.search(detail):
        return _with_queue_context(
            _disk_diagnostic(PreflightCheck("disk_headroom", False, detail)),
            base_metadata, evidence_refs,
        )

    known_retry_class = failure_class in {
        "render_error", "truncated_render_log", "unresolved_chain_ref"
    }
    if record.state == "failed" and record.retryable and known_retry_class:
        return FailureDiagnostic(
            "RETRY_ELIGIBLE", "error", "Job failed but remains eligible for retry",
            f"job {record.job_id} failed with {failure_class or 'unknown'} "
            f"x{record.failure_count}: {detail}",
            "The durable failure is below the terminal retry budget and its signature has not repeated on a retry.",
            "Inspect the attempt evidence, fix the cause, then use the existing retry command; diagnostics do not retry it.",
            _retry_command(db_path, dead_letter=False), tuple(evidence_refs), base_metadata,
        )

    return FailureDiagnostic(
        "UNKNOWN_FAILURE", "error", "Unrecognized failure class needs diagnosis",
        f"job {record.job_id} state={record.state} class={failure_class or 'none'}: {detail}",
        "No diagnostic rule claims to understand this durable failure class.",
        "Inspect the preserved rows/evidence and file the unknown class with its original detail; do not relabel it as understood.",
        review, tuple(evidence_refs), base_metadata,
    )


def classify_provenance_failures(
    checks: Sequence[Mapping[str, Any]], run: str | Path
) -> tuple[FailureDiagnostic, ...]:
    """Classify review-bundle hash failures using the existing evidence rows."""

    diagnostics: list[FailureDiagnostic] = []
    provenance = (
        str(run / "final-provenance.json") if isinstance(run, Path)
        else f"{run}/final-provenance.json"
    )
    for check in checks:
        if check.get("status") == "pass":
            continue
        missing = check.get("detail") == "artifact is missing"
        diagnostics.append(FailureDiagnostic(
            "PROVENANCE_ARTIFACT_MISSING" if missing else "PROVENANCE_HASH_MISMATCH",
            "error",
            "Review bundle provenance is incomplete" if missing else "Review bundle provenance hash mismatch",
            f"{check.get('path')}: {check.get('detail')} "
            f"(expected sha256 {check.get('expected_sha256')})",
            "A missing or changed artifact makes the run identity inconsistent and unreviewable.",
            "Restore the recorded artifact from durable evidence or regenerate it under a new provenance identity; do not edit the expected hash.",
            f"wgp review {shlex.quote(str(run))} --json",
            (str(check.get("path", "")), provenance),
            dict(check),
        ))
    return tuple(diagnostics)


def classify_input_failure(
    message: str,
    *,
    source: str | None = None,
    next_command: str | None = None,
) -> FailureDiagnostic:
    """Return the shared CLI diagnostic for one expected input/configuration error."""

    return FailureDiagnostic(
        "INPUT_INVALID", "error", "Typed input or configuration check failed", message,
        "The CLI rejected the request before an engine side effect.",
        "Fix the named field/path/configuration value, then rerun the same command.",
        next_command or (f"wgp brief validate {shlex.quote(source)}" if source else None),
        (source,) if source else (),
        {"source": source},
    )


__all__ = [
    "FailureDiagnostic",
    "classify_host_configuration",
    "classify_input_failure",
    "classify_preflight",
    "classify_provenance_failures",
    "classify_queue_failure",
    "redact_sensitive",
    "render_diagnostic",
    "render_diagnostic_mapping",
]
