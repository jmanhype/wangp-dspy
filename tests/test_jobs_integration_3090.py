"""OPTIONAL integration test — skipped unless the 3090 is reachable.

Run explicitly with:
  WANgp_3090=1 .venv/bin/python -m pytest tests/test_jobs_integration_3090.py

Verifies the REAL preflight against the real box: ssh probe,
sha256sum on the pinned model files, df on the bulk disk, nvidia-smi
compute-apps, and the QC healthz. NO render is performed (ruling: no
GPU use in CI/tests).
"""
import os

import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("WANGP_3090") != "1",
    reason="set WANGP_3090=1 to run the live 3090 preflight probe")


def test_live_preflight_against_3090():
    from host.render_host import SshHost
    from services.jobs.preflight import run_preflight

    host = SshHost(target="3090",
                   wgp_root="/home/straughter/Wan2GP",
                   pull_root="/tmp/wangp-preflight-pull")
    report = run_preflight(
        host,
        # pinned by memory + wangp_adapter defaults; hash pinned to
        # the H3 model card of record — update deliberately.
        models=[
            {"path": "/home/straughter/Wan2GP/wgp.py",
             "sha256": _sha_of_any(),  # presence probe, see below
             },
        ],
        min_free_gb=50,
        disk_path="/mnt/bulk",
        qc_url="http://127.0.0.1:8420/healthz")
    # we only assert the probes RAN and returned a report; pass/fail
    # is environment state, not a CI gate.
    assert {c.kind for c in report.checks} == {
        "ssh_reachable", "model_files", "disk_headroom", "gpu_state",
        "qc_available"}


def _sha_of_any():
    # a presence/hash probe can't be pinned in CI without leaking the
    # box state; use a hash that always mismatches so the check runs
    # end-to-end and reports the REAL hash in its detail for pinning.
    return "0" * 64
