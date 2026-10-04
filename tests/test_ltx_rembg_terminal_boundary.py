from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUN_DIR = ROOT / "datasets/runs/maestro-parity/ltx-dependency-terminalization"
BOUNDARY_DIR = RUN_DIR / "corrected-native-operations/gate15-terminal-boundary"
DIAGNOSIS_DIR = RUN_DIR / "corrected-native-operations/dependency-diagnosis"


def test_corrected_first_attempt_reached_rembg_import_boundary() -> None:
    result = json.loads((BOUNDARY_DIR / "batch.stdout").read_text(encoding="utf-8"))
    native_log = (BOUNDARY_DIR / "ltx25-outpaint/native.log").read_text(
        encoding="utf-8"
    )

    assert result["status"] == "failed_closed"
    assert result["terminal_operation"] == "ltx25-outpaint"
    assert result["boundary"]["code"] == "NATIVE_NO_OUTPUT"
    assert len(result["operations"]) == 1
    operation = result["operations"][0]
    assert operation["attempt"] == 1
    assert operation["status"] == "failed"
    assert operation["runtime_preflight"] == {
        "directory": (
            "/home/straughter/wd-28ac-final-gate7-20261003/runtime/mmgp-3.7.14"
        ),
        "mmgp_version": "3.7.14",
        "payload_sha256": (
            "d39fa7a56869387410d299ab139eb724e3be3f04055fd5d0da69d32dec9f309b"
        ),
        "status": "passed",
        "system_mmgp_present": False,
    }
    assert "from rembg import remove, new_session" in native_log
    assert "ModuleNotFoundError: No module named 'rembg'" in native_log
    assert hashlib.sha256(
        (BOUNDARY_DIR / "ltx25-outpaint/native.log").read_bytes()
    ).hexdigest() == (
        "60c2d272e1ad8908c9f465aefb6140210b4ce6f0f7c7cb52d2fe5baec30e7b12"
    )


def test_corrected_boundary_queue_has_one_failed_job_and_six_not_attempted() -> None:
    summary = json.loads(
        (BOUNDARY_DIR / "queue-summary.json").read_text(encoding="utf-8")
    )
    queue_db = BOUNDARY_DIR / "jobs.db"
    connection = sqlite3.connect(f"file:{queue_db}?mode=ro", uri=True)
    try:
        rows = {
            state: count
            for state, count in connection.execute(
                "SELECT state, count(*) FROM jobs GROUP BY state"
            )
        }
    finally:
        connection.close()

    assert rows == {"failed": 1}
    assert summary["states"]["failed"]
    assert len(summary["states"]["failed"]) == 1
    assert all(summary["states"][state] == [] for state in (
        "pending", "preflight", "rendering", "rendered_pending_qc", "qc", "done",
        "dead_letter",
    ))


def test_post_boundary_preserves_exact_host_runtime_and_assets() -> None:
    state = json.loads(
        (BOUNDARY_DIR / "preflight/host-state.json").read_text(encoding="utf-8")
    )

    assert state["read_only"] is True
    assert state["gpu"]["compute_apps"]["stdout"] == ""
    assert all(
        item["final"]["hash_match"] and item["final"]["size_match"]
        and not item["partial"]["exists"]
        for item in state["models"].values()
    )
    assert all(item["hash_match"] for item in state["references"].values())
    assert all(item["commit_match"] for item in state["execution_trees"].values())
    assert state["isolated_runtime"]["payload"]["canonical_sha256"] == (
        "d39fa7a56869387410d299ab139eb724e3be3f04055fd5d0da69d32dec9f309b"
    )
    assert state["isolated_runtime"]["isolated_import"]["returncode"] == 0
    assert state["isolated_runtime"]["system_mmgp_present"] is False


def test_rembg_inventory_and_compatibility_do_not_authorize_substitution() -> None:
    authorization = json.loads(
        (RUN_DIR / "operator-authorization.json").read_text(encoding="utf-8")
    )
    inventory = json.loads(
        (DIAGNOSIS_DIR / "rembg-readonly-inventory.json").read_text(encoding="utf-8")
    )
    compatibility = json.loads(
        (DIAGNOSIS_DIR / "rembg-compatibility.json").read_text(encoding="utf-8")
    )

    gate = authorization["jev_corrected_native_retry_host_authorization"]
    assert gate["dependency_install_authorized"] is False
    assert gate["download_authorized"] is False
    assert gate["substitution_authorized"] is False
    assert gate["runtime_mutation_authorized"] is False
    assert gate["retry"] == "never"

    assert inventory["read_only"] is True
    assert all(
        not root["matching_files"]
        for path, root in inventory["bounded_roots"].items()
        if "Wan2GP-story" not in path and "model-offload" not in path
    )
    comfy = inventory["import_probes"][
        "/home/straughter/ComfyUI/venv/bin/python"
    ]
    assert comfy["returncode"] == 0
    assert comfy["payload"]["version"] == "2.0.69"
    assert inventory["import_probes"]["/usr/bin/python3"]["returncode"] == 1

    assert compatibility["read_only"] is True
    assert compatibility["accepted_requirement_pin"].startswith(
        'rembg[gpu]==2.0.65;'
    )
    assert compatibility["package"]["canonical_sha256"] == (
        "0fcb5ad95f856416d299c9e02b88deb35b5e135643c31704dad19f6415608637"
    )
    assert all(probe["returncode"] == 0 for probe in compatibility["import_probes"])
    assert compatibility["gpu_before"] == compatibility["gpu_after"]
