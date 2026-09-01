"""Preflight — ALL checks BEFORE a job is admitted to the queue.

Highest-priority operator ruling (2026-09-01): SSH reachable, exact
model file paths + sha256 hashes, disk headroom, GPU state (idle /
stale-tenant detection), QC service availability. Any failure blocks
admission with a check-level failure naming the offending artifact.

Host interactions go through host/render_host.SshHost — this module
ONLY consumes a `run_probe(argv, timeout) -> (rc, stdout, stderr)`
method; tests stub the host layer (no real SSH in unit tests). The
`run_probe` method is added to SshHost (host seam extension, not a
duplicate).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional, Sequence

PROBE_TIMEOUT_SECS = 30


class PreflightError(Exception):
    """Preflight refused admission (report carried, not raised raw)."""


@dataclass(frozen=True)
class PreflightCheck:
    kind: str          # ssh_reachable | model_files | disk_headroom |
                       # gpu_state | qc_available
    passed: bool
    detail: str = ""


@dataclass(frozen=True)
class PreflightReport:
    passed: bool
    checks: List[PreflightCheck]
    detail: str = ""

    def check(self, kind: str) -> PreflightCheck:
        for c in self.checks:
            if c.kind == kind:
                return c
        raise KeyError(f"no check of kind {kind!r}")

    @property
    def failed_checks(self) -> List[PreflightCheck]:
        return [c for c in self.checks if not c.passed]


# nvidia-smi --query-compute-apps output: pid, process name — a row
# with a digit-led pid means SOMETHING holds the GPU (stale tenant).
_GPU_PROC_RE = re.compile(r"^\s*(\d+)\s+\S+", re.M)


def _safe_probe(host, argv, timeout=PROBE_TIMEOUT_SECS):
    """Run one probe; a raising host becomes (rc=255, '', error)."""
    try:
        return host.run_probe(argv, timeout=timeout)
    except Exception as e:
        return 255, "", f"{type(e).__name__}: {e}"


def _probe_ssh(host) -> PreflightCheck:
    rc, _out, err = _safe_probe(host, ["true"])
    ok = rc == 0
    return PreflightCheck(
        "ssh_reachable", ok,
        "" if ok else f"ssh probe rc={rc}: {err.strip()[:200]}")


def _probe_models(host, models) -> PreflightCheck:
    problems = []
    for spec in models:
        path, expected = spec["path"], spec["sha256"]
        rc, out, err = _safe_probe(host, ["sha256sum", path],
                                   timeout=PROBE_TIMEOUT_SECS * 4)
        if rc != 0:
            problems.append(f"missing {path}: {err.strip()[:120]}")
            continue
        actual = out.split()[0] if out.split() else ""
        if actual != expected:
            problems.append(
                f"hash mismatch {path}: expected {expected[:12]}… "
                f"got {actual[:12]}…")
    return PreflightCheck(
        "model_files", not problems, "; ".join(problems))


def _probe_disk(host, disk_path, min_free_gb) -> PreflightCheck:
    rc, out, _err = _safe_probe(
        host, ["df", "-BG", "--output=avail", disk_path])
    if rc != 0:
        return PreflightCheck("disk_headroom", False,
                              f"df {disk_path} rc={rc}")
    try:
        avail_gb = float(re.search(r"(\d+)", out).group(1))
    except (AttributeError, ValueError):
        return PreflightCheck("disk_headroom", False,
                              f"unparseable df output: {out.strip()!r}")
    ok = avail_gb >= min_free_gb
    return PreflightCheck(
        "disk_headroom", ok,
        f"{avail_gb:.0f}G free on {disk_path} "
        f"(min {min_free_gb}G)" if True else "")


def _probe_gpu(host) -> PreflightCheck:
    rc, out, _err = _safe_probe(
        host, ["nvidia-smi", "--query-compute-apps=pid,process_name",
               "--format=csv,noheader"])
    if rc != 0:
        return PreflightCheck("gpu_state", False,
                              f"nvidia-smi rc={rc}")
    m = _GPU_PROC_RE.search(out or "")
    if m:
        return PreflightCheck(
            "gpu_state", False,
            f"GPU busy: stale tenant pid {m.group(1)} "
            f"({out.strip().splitlines()[0]})")
    return PreflightCheck("gpu_state", True, "idle")


def _probe_qc(host, qc_url) -> PreflightCheck:
    rc, _out, err = _safe_probe(
        host, ["curl", "-fsS", "-m", str(PROBE_TIMEOUT_SECS), qc_url],
        timeout=PROBE_TIMEOUT_SECS + 5)
    ok = rc == 0
    return PreflightCheck(
        "qc_available", ok,
        f"qc healthz ok ({qc_url})" if ok
        else f"QC unavailable at {qc_url} (curl rc={rc}: "
             f"{err.strip()[:120]})")


def run_preflight(host, *, models: Sequence[dict], min_free_gb: float,
                  disk_path: str, qc_url: str) -> PreflightReport:
    checks = [
        _probe_ssh(host),
        _probe_models(host, models),
        _probe_disk(host, disk_path, min_free_gb),
        _probe_gpu(host),
        _probe_qc(host, qc_url),
    ]
    failed = [c for c in checks if not c.passed]
    return PreflightReport(
        passed=not failed, checks=checks,
        detail="; ".join(c.detail for c in failed))


__all__ = [
    "PreflightCheck", "PreflightReport", "PreflightError",
    "run_preflight", "PROBE_TIMEOUT_SECS",
]
