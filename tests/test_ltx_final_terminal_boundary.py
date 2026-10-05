from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUN_DIR = ROOT / "datasets/runs/maestro-parity/ltx-dependency-terminalization"
BOUNDARY_DIR = RUN_DIR / "final-native-operations/terminal-boundary"
BOUNDARY = BOUNDARY_DIR / "boundary.json"
LOG = BOUNDARY_DIR / "ltx25-outpaint.native.log"
QUEUE_DB = BOUNDARY_DIR / "jobs.db"


def test_first_native_attempt_is_exact_import_boundary() -> None:
    boundary = json.loads(BOUNDARY.read_text(encoding="utf-8"))
    first = boundary["first_operation"]

    assert boundary["status"] == "failed_closed"
    assert boundary["boundary"]["runner_code"] == "NATIVE_NO_OUTPUT"
    assert boundary["boundary"]["diagnostic_code"] == "NATIVE_IMPORT_MMGP_MISSING"
    assert boundary["boundary"]["exact_native_error"] == (
        "ModuleNotFoundError: No module named 'mmgp'"
    )
    assert boundary["boundary"]["not_a_hardware_verdict"] is True
    assert boundary["boundary"]["retry_attempted"] is False
    assert first["native_exit"] == 1
    assert first["output_count"] == 0
    assert first["native_log"]["sha256"] == hashlib.sha256(
        LOG.read_bytes()
    ).hexdigest()
    assert boundary["boundary_counters"] == {
        "native_attempts": 1,
        "retries": 0,
        "downloads": 0,
        "model_mutations": 0,
        "reference_mutations": 0,
        "queue_admissions": 1,
        "matrix_changes": 0,
        "protected_file_changes": 0,
    }


def test_durable_queue_contains_one_failed_attempt_and_no_pending_work() -> None:
    boundary = json.loads(BOUNDARY.read_text(encoding="utf-8"))
    connection = sqlite3.connect(f"file:{QUEUE_DB}?mode=ro", uri=True)
    try:
        rows = {
            state: count for state, count in connection.execute(
                "SELECT state, count(*) FROM jobs GROUP BY state"
            )
        }
        jobs = connection.execute("SELECT job_id FROM jobs").fetchall()
    finally:
        connection.close()

    assert rows == {"failed": 1}
    assert [row[0] for row in jobs] == [boundary["first_operation"]["durable_job_id"]]
    assert boundary["queue"]["pending_count"] == 0
    assert boundary["queue"]["active_count"] == 0
    assert boundary["queue"]["failed_count"] == 1
    assert len(boundary["not_attempted"]) == 6


def test_terminal_postflight_preserves_models_references_and_idle_host() -> None:
    boundary = json.loads(BOUNDARY.read_text(encoding="utf-8"))
    postflight = json.loads(
        (BOUNDARY_DIR / "postflight.json").read_text(encoding="utf-8")
    )

    assert len(postflight["models"]) == 5
    assert all(item["match"] for item in postflight["models"].values())
    assert len(postflight["references"]) == 7
    assert all(item["match"] for item in postflight["references"].values())
    assert all(item["match"] for item in postflight["trees"].values())
    assert postflight["gpu"]["apps"]["stdout"].strip() == ""
    assert postflight["judge"]["health"]["reachable"] is False
    assert postflight["native_processes"]["returncode"] != 0
    assert boundary["postflight"] == {
        "evidence": "terminal-boundary/postflight.json",
        "models_match": True,
        "references_match": True,
        "trees_match": True,
        "gpu_idle": True,
        "judge_unreachable": True,
        "native_processes": 0,
        "outputs": 0,
    }
