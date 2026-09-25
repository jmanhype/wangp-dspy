"""Preflight tests — the host layer is STUBBED (no real SSH in tests)."""
import pytest

from services.jobs.preflight import (
    GpuComputeProcess,
    GpuComputeState,
    PreflightCheck,
    PreflightReport,
    PreflightError,
    run_preflight,
    _gpu_check_from_state,
    _parse_gpu_compute_apps,
)

CAPTURED_RT3090_OUTPUT = (
    "1007225, 7808 MiB, "
    "/home/straughter/llama.cpp/build/bin/llama-server"
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
                 nvidia_rc=0,
                 qc_ok=True):
        self.files = dict(files or
                          {m["path"]: m["sha256"] for m in MODEL_SPECS})
        self.reachable = reachable
        self.disk_free_gb = disk_free_gb
        self.nvidia_out = nvidia_out
        self.nvidia_rc = nvidia_rc
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
            return self.nvidia_rc, self.nvidia_out, ""
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


def test_gpu_busy_with_real_captured_compute_process_fails():
    host = StubHost(nvidia_out=CAPTURED_RT3090_OUTPUT)
    report = run_preflight(host, models=MODEL_SPECS, min_free_gb=50,
                           disk_path="/mnt/bulk", qc_url="http://x/h")
    check = report.check("gpu_state")
    assert not check.passed
    nvidia_probe = next(p for p in host.probes if p[0] == "nvidia-smi")
    assert nvidia_probe == [
        "nvidia-smi",
        "--query-compute-apps=pid,used_memory,process_name",
        "--format=csv,noheader",
    ]


def test_gpu_probe_nonzero_return_code_fails():
    host = StubHost(nvidia_rc=9, nvidia_out="")
    report = run_preflight(host, models=MODEL_SPECS, min_free_gb=50,
                           disk_path="/mnt/bulk", qc_url="http://x/h")
    assert not report.check("gpu_state").passed


def test_gpu_idle_passes():
    host = StubHost(nvidia_out="No running processes found")
    report = run_preflight(host, models=MODEL_SPECS, min_free_gb=50,
                           disk_path="/mnt/bulk", qc_url="http://x/h")
    assert report.check("gpu_state").passed


def test_gpu_parser_accepts_byte_for_byte_real_captured_output():
    state = _parse_gpu_compute_apps(CAPTURED_RT3090_OUTPUT + "\n")
    assert state == GpuComputeState(
        "occupied",
        (GpuComputeProcess(
            pid=1007225,
            memory_mib=7808,
            process_name="/home/straughter/llama.cpp/build/bin/llama-server",
        ),),
    )


def test_gpu_parser_accepts_quoted_process_path_with_commas_and_spaces():
    state = _parse_gpu_compute_apps(
        '1007225, 7808 MiB, "/opt/renderer/one, two, three"\n')
    assert state.processes == (
        GpuComputeProcess(1007225, 7808,
                          "/opt/renderer/one, two, three"),
    )


@pytest.mark.parametrize("output", [
    "7808 MiB, 1007225, /tmp/renderer",
    "1007225, /tmp/renderer",
    "1007225, 7808 MiB",
    "1007225, 7808 MiB, /tmp/renderer, extra",
    "not-a-pid, 7808 MiB, /tmp/renderer",
    "1007225, 7808 GiB, /tmp/renderer",
])
def test_gpu_parser_fails_closed_on_malformed_or_alternate_columns(output):
    state = _parse_gpu_compute_apps(output)
    assert state.verdict == "unknown"
    assert state.processes == ()
    assert state.reason


@pytest.mark.parametrize("output", ["", "No running processes found"])
def test_gpu_parser_accepts_genuine_no_compute_processes(output):
    assert _parse_gpu_compute_apps(output) == GpuComputeState("idle", ())


def test_gpu_check_mapping_occupied_unknown_and_idle():
    occupied = GpuComputeState(
        "occupied",
        (GpuComputeProcess(1007225, 7808,
                           "/home/straughter/llama.cpp/build/bin/llama-server"),),
    )
    unknown = GpuComputeState("unknown", (), "invalid pid 'not-a-pid'")
    idle = GpuComputeState("idle", ())

    occupied_check = _gpu_check_from_state(occupied)
    unknown_check = _gpu_check_from_state(unknown)
    idle_check = _gpu_check_from_state(idle)

    assert not occupied_check.passed
    assert all(value in occupied_check.detail for value in (
        "pid=1007225", "memory=7808MiB",
        "process=/home/straughter/llama.cpp/build/bin/llama-server"))
    assert not unknown_check.passed
    assert "invalid pid 'not-a-pid'" in unknown_check.detail
    assert idle_check.passed
    assert idle_check.detail == "idle"


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
