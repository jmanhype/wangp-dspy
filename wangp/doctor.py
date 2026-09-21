"""Readiness checks for the local no-GPU lane and explicit host probes."""

from __future__ import annotations

import importlib
import hashlib
import os
import platform
import shutil
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping, Sequence

from wangp.config import (
    ALL_HOST_KEYS,
    HostConfig,
    OPTIONAL_HOST_KEYS,
    ENVIRONMENT_KEYS,
    load_host_config,
    missing_host_keys,
    render_host,
)
from wangp.diagnostics import (
    FailureDiagnostic,
    classify_host_configuration,
    classify_preflight,
)
from services.jobs.preflight import PreflightCheck, PreflightReport


_REQUIRED_IMPORTS = ("dspy", "fastapi", "pydantic", "requests", "soundfile", "librosa", "numpy", "uvicorn")
_MINIMUM_FREE_GB = 1.0
REMOTE_MINIMUM_FREE_GB = 50.0


@dataclass(frozen=True)
class DoctorCheck:
    """One independently actionable readiness result."""

    kind: str
    status: str
    detail: str
    remediation: str = ""

    def mapping(self) -> dict[str, str]:
        return {
            "kind": self.kind,
            "status": self.status,
            "detail": self.detail,
            "remediation": self.remediation,
        }


@dataclass
class DoctorReport:
    """Doctor output with no timestamps or environment-variable dumps."""

    checks: list[DoctorCheck] = field(default_factory=list)
    diagnostics: list[FailureDiagnostic] = field(default_factory=list)

    @property
    def ready(self) -> bool:
        return not any(check.status == "failed" for check in self.checks)

    def mapping(self) -> dict[str, object]:
        return {
            "ready": self.ready,
            "checks": [check.mapping() for check in self.checks],
            "diagnostics": [diagnostic.mapping() for diagnostic in self.diagnostics],
        }


def _pass(kind: str, detail: str) -> DoctorCheck:
    return DoctorCheck(kind=kind, status="pass", detail=detail)


def _fail(kind: str, detail: str, remediation: str) -> DoctorCheck:
    return DoctorCheck(kind, "failed", detail, remediation)


def _skip(kind: str, detail: str, remediation: str) -> DoctorCheck:
    return DoctorCheck(kind, "skipped", detail, remediation)


def _python_check() -> DoctorCheck:
    version = platform.python_version()
    if version >= "3.11":
        return _pass("python", f"Python {version}")
    return _fail(
        "python",
        f"Python {version}; 3.11 or newer is required",
        "Install Python 3.11 or newer and recreate the uv environment.",
    )


def _dependency_check() -> DoctorCheck:
    missing: list[str] = []
    for module in _REQUIRED_IMPORTS:
        try:
            importlib.import_module(module)
        except Exception as exc:
            missing.append(f"{module} ({type(exc).__name__})")
    if not missing:
        return _pass(
            "dependency_imports", f"{len(_REQUIRED_IMPORTS)} imports available"
        )
    return _fail(
        "dependency_imports",
        "; ".join(missing),
        "Run 'uv sync --extra dev' and inspect the failed package install.",
    )


def _tool_check(name: str) -> DoctorCheck:
    path = shutil.which(name)
    if path is None:
        return _fail(
            name,
            f"{name} was not found on PATH",
            f"Install {name} and ensure it is on PATH.",
        )
    return _pass(name, f"{name} available at {path}")


def _queue_check() -> DoctorCheck:
    return _pass(
        "queue_database",
        f"SQLite {sqlite3.sqlite_version} is available for JobQueue databases",
    )


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as model:
        for chunk in iter(lambda: model.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _model_check(models: Sequence[Mapping[str, str]] | None) -> DoctorCheck:
    if models is None:
        return _skip(
            "model_files",
            "No model manifest supplied; not required for no-GPU planning",
            "Supply --models with path and sha256 entries before host work.",
        )
    if not models:
        return _fail(
            "model_files",
            "model manifest is empty",
            "Supply at least one local_path or remote_path entry.",
        )
    local_specs = [
        spec for spec in models if isinstance(spec.get("local_path"), str)
    ]
    if not local_specs:
        return _skip(
            "model_files",
            f"{len(models)} remote-only manifest entries; local files are not required",
            "Supply local_path entries when local model verification is needed.",
        )
    problems: list[str] = []
    for spec in local_specs:
        path = Path(str(spec["local_path"])).expanduser()
        if not path.is_file():
            problems.append(f"missing {path}")
            continue
        try:
            actual = _sha256_file(path)
        except OSError as exc:
            problems.append(f"unreadable {path}: {exc}")
            continue
        expected = str(spec["sha256"]).lower()
        if actual != expected:
            problems.append(
                f"sha256 mismatch {path} "
                f"(expected {expected[:12]}…, got {actual[:12]}…)"
            )
    if problems:
        return _fail(
            "model_files",
            "; ".join(problems),
            "Place each manifest file at its recorded local path before host work.",
        )
    return _pass("model_files", f"{len(local_specs)} manifest entries hashed locally")


def _host_setting(config: HostConfig, key: str, setting) -> str:
    if setting is None:
        return f"{key}=unconfigured [unconfigured]"
    return f"{key}={setting.value} [{setting.provenance()}]"


def _host_detail(config: HostConfig) -> str:
    return "; ".join(
        _host_setting(config, key, setting)
        for key, setting in zip(
            ALL_HOST_KEYS,
            config.settings(),
            strict=True,
        )
    )


def _host_check(config: HostConfig) -> DoctorCheck:
    missing_render_keys = missing_host_keys(config)
    if config.wgp_python is None:
        missing_render_keys += OPTIONAL_HOST_KEYS
    if missing_render_keys:
        variables = ", ".join(
            ENVIRONMENT_KEYS[key] for key in missing_render_keys
        )
        return _skip(
            "host_configuration",
            _host_detail(config) + "; the no-GPU lane remains ready",
            f"Set {variables} (or the corresponding [host] keys) "
            "for GPU work.",
        )
    return _pass(
        "host_configuration",
        _host_detail(config) + "; no host call was made",
    )


def _disk_check() -> DoctorCheck:
    usage = shutil.disk_usage(Path.cwd())
    free_gb = usage.free / (1000**3)
    if free_gb < _MINIMUM_FREE_GB:
        return _fail(
            "local_disk_headroom",
            f"{free_gb:.1f}G free (minimum {_MINIMUM_FREE_GB:.0f}G)",
            "Free at least 1G on the repository volume before planning runs.",
        )
    return _pass(
        "local_disk_headroom", f"{free_gb:.0f}G free on the repository volume"
    )


def remote_model_specs(
    models: Sequence[Mapping[str, str]], *, wgp_root: str | Path
) -> list[dict[str, str]]:
    """Normalize explicit remote paths into the remote Wan2GP namespace."""

    root = Path(wgp_root)
    specs: list[dict[str, str]] = []
    for model in models:
        raw = Path(str(model["remote_path"]))
        remote_path = raw if raw.is_absolute() else root / raw
        specs.append({"path": str(remote_path), "sha256": str(model["sha256"])})
    return specs


def _preflight_doctor_result(
    host: object,
    models: Sequence[Mapping[str, str]],
    *,
    wgp_root: str | Path,
    disk_path: str | Path,
) -> tuple[list[DoctorCheck], list[FailureDiagnostic]]:
    from services.jobs.preflight import run_preflight

    report = run_preflight(
        host,
        models=remote_model_specs(models, wgp_root=wgp_root),
        min_free_gb=REMOTE_MINIMUM_FREE_GB,
        disk_path=str(disk_path),
        qc_url=os.environ.get("WANGP_QC_URL", "http://localhost:8000/health"),
    )
    remediations = {"ssh_reachable": "Verify SSH with 'ssh <target> true'.", "model_files": "Copy each model to the host and verify its manifest sha256.", "disk_headroom": "Free remote disk space or choose sanctioned storage.", "gpu_state": "Stop stale GPU tenants or diagnose nvidia-smi.", "qc_available": "Start QC or set WANGP_QC_URL."}
    checks = [
        DoctorCheck(
            kind=check.kind,
            status="pass" if check.passed else "failed",
            detail=check.detail,
            remediation="" if check.passed else remediations[check.kind],
        )
        for check in report.checks
    ]
    return checks, classify_preflight(report, target=getattr(host, "target", None))


def _preflight_doctor_checks(
    host: object,
    models: Sequence[Mapping[str, str]],
    *,
    wgp_root: str | Path,
    disk_path: str | Path,
) -> list[DoctorCheck]:
    """Compatibility helper for callers that need only the five doctor checks."""

    return _preflight_doctor_result(
        host, models, wgp_root=wgp_root, disk_path=disk_path
    )[0]


def _host_manifest_check(
    models: Sequence[Mapping[str, str]] | None,
) -> DoctorCheck:
    if models is None:
        return _fail(
            "model_files",
            "--probe-host requires --models with at least one remote_path entry",
            "Supply a manifest entry with remote_path and sha256 before probing.",
        )
    if not models:
        return _fail(
            "model_files",
            "--probe-host requires a nonempty model manifest",
            "Add at least one remote_path and sha256 entry before probing.",
        )
    if not any(isinstance(spec.get("remote_path"), str) for spec in models):
        return _fail(
            "model_files",
            "no model entry contains remote_path; host probing was not attempted",
            "Add remote_path and sha256 for each model in the remote Wan2GP namespace.",
        )
    return _pass("model_files", "remote manifest entries available for probing")


def _host_probe_checks(
    models: Sequence[Mapping[str, str]],
    config: HostConfig,
) -> tuple[list[DoctorCheck], list[FailureDiagnostic]]:
    if missing_host_keys(config):
        configuration = classify_host_configuration(config)
        assert configuration is not None
        return [
            _fail(
                "host_configuration",
                "Host probing was requested but the render host is incomplete",
                "Set WANGP_SSH_TARGET, WANGP_WGP_ROOT, and WANGP_PULL_ROOT "
                "(or the corresponding [host] keys), then run 'wgp doctor'.",
            )
        ], [configuration]
    host = render_host(config)
    checks, diagnostics = _preflight_doctor_result(
        host,
        models,
        wgp_root=config.wgp_root.value,
        disk_path=config.wgp_root.value,
    )
    return checks, diagnostics


def _local_failure_diagnostics(report: DoctorReport) -> list[FailureDiagnostic]:
    diagnostics: list[FailureDiagnostic] = []
    for check in report.checks:
        if check.status != "failed" or check.kind != "model_files":
            continue
        diagnostics.extend(classify_preflight(PreflightReport(
            passed=False,
            checks=[PreflightCheck(check.kind, False, check.detail)],
        )))
    return diagnostics


def collect_doctor_checks(
    models: Sequence[Mapping[str, str]] | None = None,
    *,
    probe_host: bool = False,
) -> DoctorReport:
    """Collect local readiness without implicit SSH or hosted-service calls."""

    config = load_host_config()
    report = DoctorReport(
        [
            _python_check(),
            _tool_check("uv"),
            _dependency_check(),
            _tool_check("ffprobe"),
            _tool_check("ffmpeg"),
            _queue_check(),
            _model_check(models),
            _host_check(config),
            _disk_check(),
        ]
    )
    report.diagnostics.extend(_local_failure_diagnostics(report))
    if probe_host:
        manifest_check = _host_manifest_check(models)
        if manifest_check.status == "pass":
            checks, diagnostics = _host_probe_checks(models, config)
            report.checks.extend(checks)
            report.diagnostics.extend(diagnostics)
        else:
            report.checks.append(manifest_check)
            configuration = classify_host_configuration(config)
            if configuration is not None:
                report.diagnostics.append(configuration)
    return report


__all__ = ["DoctorCheck", "DoctorReport", "collect_doctor_checks"]
