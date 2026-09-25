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

import csv
import io
import re
from dataclasses import dataclass, field
from typing import List, Literal, Optional, Sequence

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


@dataclass(frozen=True)
class GpuComputeProcess:
    pid: int
    memory_mib: int
    process_name: str


@dataclass(frozen=True)
class GpuComputeState:
    verdict: Literal["idle", "occupied", "unknown"]
    processes: tuple[GpuComputeProcess, ...]
    reason: str = ""


def _parse_gpu_compute_apps(output: str) -> GpuComputeState:
    """Parse nvidia-smi CSV compute-app rows, failing closed on surprises."""
    text = (output or "").strip()
    if text == "" or text == "No running processes found":
        return GpuComputeState("idle", ())

    processes = []
    for row in csv.reader(io.StringIO(text), skipinitialspace=True):
        if len(row) != 3:
            return GpuComputeState(
                "unknown", tuple(processes),
                f"expected 3 CSV fields, got {len(row)}: {row!r}")
        pid_text, memory_text, process_name = (value.strip() for value in row)
        try:
            pid = int(pid_text)
        except ValueError:
            return GpuComputeState(
                "unknown", tuple(processes), f"invalid pid {pid_text!r}")
        memory_match = re.fullmatch(r"(\d+)\s*(?:MiB)?", memory_text)
        if memory_match is None or not process_name:
            return GpuComputeState(
                "unknown", tuple(processes),
                f"invalid compute-app row: pid={pid}, "
                f"used_memory={memory_text!r}, "
                f"process_name={process_name!r}")
        processes.append(GpuComputeProcess(
            pid, int(memory_match.group(1)), process_name))
    return GpuComputeState("occupied", tuple(processes))


def _gpu_check_from_state(state: GpuComputeState) -> PreflightCheck:
    if state.verdict == "idle":
        return PreflightCheck("gpu_state", True, "idle")
    if state.verdict == "occupied":
        occupants = _gpu_occupant_detail(state.processes)
        return PreflightCheck("gpu_state", False, f"GPU occupied: {occupants}")
    detail = f"GPU state unknown (fail closed): {state.reason}"
    if state.processes:
        detail += f"; observed {_gpu_occupant_detail(state.processes)}"
    return PreflightCheck(
        "gpu_state", False, detail)


def _gpu_occupant_detail(processes):
    return ", ".join(
        f"pid={proc.pid} memory={proc.memory_mib}MiB "
        f"process={proc.process_name}" for proc in processes)


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
        host, [
            "nvidia-smi",
            "--query-compute-apps=pid,used_memory,process_name",
            "--format=csv,noheader",
        ])
    if rc != 0:
        return PreflightCheck("gpu_state", False,
                              f"nvidia-smi rc={rc}")
    return _gpu_check_from_state(_parse_gpu_compute_apps(out))


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
    "GpuComputeProcess", "GpuComputeState",
    "run_preflight", "PROBE_TIMEOUT_SECS",
]
