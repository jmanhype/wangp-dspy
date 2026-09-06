"""Preflight tests — the host layer is STUBBED (no real SSH in tests)."""
import pytest

from services.jobs.preflight import (
    PreflightCheck,
    PreflightReport,
    PreflightError,
    run_preflight,
)

MODEL_SPECS = [
    {"path": "/home/straughter/Wan2GP/models/h3/model.safetensors",
     "sha256": "aa" * 32},
    {"path": "/home/straughter/Wan2GP/models/vae/vae.safetensors",
     "sha256": "bb" * 32},
]


class StubHost:
    """Records probes; scriptable outcomes."""

    def __init__(self, *, reachable=True, files=None, disk_free_gb=200.0,
                 gpu_procs="nvidia-smi --query-compute-apps --format=csv,noheader",
                 nvidia_out="No running processes found",
                 qc_ok=True):
        self.files = dict(files or
                          {m["path"]: m["sha256"] for m in MODEL_SPECS})
        self.reachable = reachable
        self.disk_free_gb = disk_free_gb
        self.nvidia_out = nvidia_out
        self.qc_ok = qc_ok
        self.probes = []

    # -- probe surface (what SshHost.run_probe returns) -------------
    def run_probe(self, argv, timeout=30):
        self.probes.append(list(argv))
        joined = " ".join(argv)
        if not self.reachable:
            return 255, "", "ssh: connect timed out"
        if joined.startswith("sha256sum"):
            path = argv[-1]
            if path in self.files:
                return 0, f"{self.files[path]}  {path}", ""
            return 1, "", f"sha256sum: {path}: No such file or directory"
        if joined.startswith("df"):
            return 0, f"  {self.disk_free_gb:.0f}G", ""
        if joined.startswith("nvidia-smi"):
            return 0, self.nvidia_out, ""
        if joined.startswith("curl"):
            return (0, "ok", "") if self.qc_ok else (7, "", "refused")
        return 0, "", ""


def test_report_shape_all_pass():
    host = StubHost()
    report = run_preflight(
        host, models=MODEL_SPECS, min_free_gb=50,
        disk_path="/mnt/bulk", qc_url="http://127.0.0.1:8420/healthz")
    assert report.passed
    assert report.failed_checks == []
    kinds = [c.kind for c in report.checks]
    assert kinds == ["ssh_reachable", "model_files", "disk_headroom",
                     "gpu_state", "qc_available"]


def test_empty_model_specs_fail_closed():
    report = run_preflight(
        StubHost(), models=[], min_free_gb=50,
        disk_path="/mnt/bulk", qc_url="http://x/h")
    check = report.check("model_files")
    assert not check.passed
    assert "no model path" in check.detail


def test_ssh_unreachable_fails_and_names_target():
    host = StubHost(reachable=False)
    report = run_preflight(host, models=MODEL_SPECS, min_free_gb=50,
                           disk_path="/mnt/bulk", qc_url="http://x/h")
    assert not report.passed
    ssh = report.check("ssh_reachable")
    assert not ssh.passed


def test_missing_model_file_fails_with_path():
    host = StubHost(files={MODEL_SPECS[0]["path"]: "aa" * 32})
    report = run_preflight(host, models=MODEL_SPECS, min_free_gb=50,
                           disk_path="/mnt/bulk", qc_url="http://x/h")
    check = report.check("model_files")
    assert not check.passed
    assert MODEL_SPECS[1]["path"] in check.detail


def test_model_hash_mismatch_fails_with_path_and_expected_hash():
    host = StubHost(files={m["path"]: "ff" * 32 for m in MODEL_SPECS})
    report = run_preflight(host, models=MODEL_SPECS, min_free_gb=50,
                           disk_path="/mnt/bulk", qc_url="http://x/h")
    check = report.check("model_files")
    assert not check.passed
    assert MODEL_SPECS[0]["sha256"][:12] in check.detail


def test_disk_headroom_below_min_fails():
    host = StubHost(disk_free_gb=12.0)
    report = run_preflight(host, models=MODEL_SPECS, min_free_gb=50,
                           disk_path="/mnt/bulk", qc_url="http://x/h")
    assert not report.check("disk_headroom").passed


def test_gpu_busy_with_render_proc_fails_stale_tenant_detection():
    host = StubHost(nvidia_out="12345  C  python  wgp.py")
    report = run_preflight(host, models=MODEL_SPECS, min_free_gb=50,
                           disk_path="/mnt/bulk", qc_url="http://x/h")
    check = report.check("gpu_state")
    assert not check.passed
    assert "12345" in check.detail  # names the stale tenant pid


def test_gpu_idle_passes():
    host = StubHost(nvidia_out="No running processes found")
    report = run_preflight(host, models=MODEL_SPECS, min_free_gb=50,
                           disk_path="/mnt/bulk", qc_url="http://x/h")
    assert report.check("gpu_state").passed


def test_gpu_qc_tenant_is_allowed():
    host = StubHost(
        nvidia_out="1761038, /home/straughter/llama.cpp/build/bin/llama-server")
    report = run_preflight(host, models=MODEL_SPECS, min_free_gb=50,
                           disk_path="/mnt/bulk", qc_url="http://x/h")
    check = report.check("gpu_state")
    assert check.passed
    assert "QC tenant" in check.detail


def test_qc_unavailable_fails_check():
    host = StubHost(qc_ok=False)
    report = run_preflight(host, models=MODEL_SPECS, min_free_gb=50,
                           disk_path="/mnt/bulk",
                           qc_url="http://127.0.0.1:8420/healthz")
    assert not report.check("qc_available").passed
    assert "8420" in report.check("qc_available").detail


def test_preflight_error_when_host_probe_raises():
    class ExplodingHost(StubHost):
        def run_probe(self, argv, timeout=30):
            raise OSError("ssh: connect to host 3090 port 22: timed out")
    report = run_preflight(ExplodingHost(), models=MODEL_SPECS,
                           min_free_gb=50, disk_path="/mnt/bulk",
                           qc_url="http://x/h")
    assert not report.passed
    assert not report.check("ssh_reachable").passed
