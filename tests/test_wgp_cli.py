"""Real-subprocess integration tests for the stable wgp surface."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BRIEF = ROOT / "datasets/content_briefs/lf004-operator-dogfood-56f/brief.json"
PLATES = ROOT / "datasets/content_briefs/lf004-operator-dogfood/plates"
QUEUE = ROOT / "datasets/lf004-operator-dogfood-56f-recovery-20260921.jobs.db"
RUN = ROOT / "datasets/runs/pull/lf004-operator-dogfood-56f-recovery-20260921"
JOB = "job-1789954232380-922bf583"


def _wgp(
    *args: str, env_updates: dict[str, str | None] | None = None
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    for key, value in (env_updates or {}).items():
        if value is None:
            env.pop(key, None)
        else:
            env[key] = value
    return subprocess.run(
        ["uv", "run", "--frozen", "--extra", "dev", "wgp", *args],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        timeout=180,
        check=False,
    )


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_help_exposes_exactly_stable_verbs() -> None:
    result = _wgp("--help")
    assert result.returncode == 0, result.stdout + result.stderr
    for verb in ("brief", "doctor", "plan", "review", "status"):
        assert verb in result.stdout
    assert "run_content_brief" not in result.stdout


def test_brief_validate_uses_typed_loader_without_writing(tmp_path: Path) -> None:
    result = _wgp("brief", "validate", str(BRIEF))
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.startswith("brief=sha256:")
    assert "valid=true" in result.stdout
    assert not list(tmp_path.iterdir())

    invalid = json.loads(BRIEF.read_text(encoding="utf-8"))
    invalid["dialogue"][0]["speaker"] = "NotInRoster"
    invalid_path = tmp_path / "invalid-brief.json"
    invalid_path.write_text(json.dumps(invalid), encoding="utf-8")
    rejected = _wgp("brief", "validate", str(invalid_path))
    assert rejected.returncode == 2
    combined = rejected.stdout + rejected.stderr
    assert "dialogue[0].speaker" in combined
    assert "Traceback" not in combined


def test_wgp_plan_wraps_gateway_with_no_gpu_work(tmp_path: Path) -> None:
    output = tmp_path / "plans" / "plan.json"
    run_dir = tmp_path / "run"
    result = _wgp(
        "plan",
        "--brief",
        str(BRIEF),
        "--plates",
        str(PLATES),
        "--out",
        str(output),
        "--run-dir",
        str(run_dir),
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "clips=4" in result.stdout
    assert f"plan={output.resolve()}" in result.stdout
    assert "gpu_work=false" in result.stdout
    assert "queue_submitted=false" in result.stdout
    assert f"ledger={(run_dir / 'run_ledger.json').resolve()}" in result.stdout
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "wangp-dspy.content-plan/v1"
    assert payload["summary"] == {
        "clip_count": 4,
        "speakers": ["Tess", "Rho", "Tess", "Rho"],
        "planned_duration_s": 9.332,
        "dry_run": True,
        "gpu_work": False,
        "queue_submitted": False,
    }
    assert (run_dir / "run_ledger.json").is_file()

    machine = _wgp(
        "plan",
        "--brief",
        str(BRIEF),
        "--plates",
        str(PLATES),
        "--out",
        str(output),
        "--run-dir",
        str(run_dir),
        "--json",
    )
    assert machine.returncode == 0, machine.stdout + machine.stderr
    machine_payload = json.loads(machine.stdout)
    assert machine_payload["plan"] == output.resolve().as_posix()
    assert machine_payload["summary"]["clip_count"] == 4


def test_status_reads_queue_and_mutates_no_bytes(tmp_path: Path) -> None:
    copied = tmp_path / QUEUE.name
    shutil.copy2(QUEUE, copied)
    source_digest = _digest(QUEUE)
    copied_digest = _digest(copied)
    result = _wgp(
        "status", "--db", str(copied), "--json", env_updates={
            "WANGP_SSH_TARGET": None,
        }
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["state_counts"]["done"] == 4
    assert payload["state_counts"]["pending"] == 0
    selected = next(job for job in payload["jobs"] if job["job_id"] == JOB)
    assert selected["state"] == "done"
    assert selected["failure_summary"].startswith("render_error x1:")
    assert len(payload["attempts"][JOB]) == 2
    assert _digest(QUEUE) == source_digest
    assert _digest(copied) == copied_digest


def test_review_reports_queue_attempts_and_evidence(tmp_path: Path) -> None:
    copied = tmp_path / QUEUE.name
    shutil.copy2(QUEUE, copied)
    before = _digest(copied)
    result = _wgp("review", "--db", str(copied), "--job", JOB)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "clip=1" in result.stdout
    assert "kind=ref2va_render" in result.stdout
    assert "attempt=1" in result.stdout
    assert "reapply recorded LF004" in result.stdout
    assert "evidence:" in result.stdout
    assert _digest(copied) == before


def test_review_verifies_final_provenance_artifact_hashes() -> None:
    result = _wgp("review", str(RUN))
    assert result.returncode == 0, result.stdout + result.stderr
    assert f"film={RUN / 'assembled.mp4'}" in result.stdout
    assert f"probe={RUN / 'probe.json'}" in result.stdout
    assert "contact_sheet=" in result.stdout
    assert "hash_checks=21 passed=true" in result.stdout
    assert "sha256 mismatch" not in result.stdout


def test_local_doctor_is_ready_without_host_and_reports_missing_manifest(
    tmp_path: Path,
) -> None:
    no_host = _wgp(
        "doctor", "--db", str(QUEUE), env_updates={
            "WANGP_SSH_TARGET": None,
        }
    )
    assert no_host.returncode == 0, no_host.stdout + no_host.stderr
    assert "[PASS] python:" in no_host.stdout
    assert "[PASS] uv:" in no_host.stdout
    assert "[PASS] ffprobe:" in no_host.stdout
    assert "[PASS] ffmpeg:" in no_host.stdout
    assert "[PASS] database_reachability:" in no_host.stdout
    assert "[SKIP] host_configuration:" in no_host.stdout
    assert "no host call was made" not in no_host.stdout
    assert "ready=yes" in no_host.stdout
    assert "ssh_reachable" not in no_host.stdout

    missing = tmp_path / "missing-model.safetensors"
    manifest = tmp_path / "models.json"
    manifest.write_text(
        json.dumps([{"path": str(missing), "sha256": "0" * 64}]),
        encoding="utf-8",
    )
    failed = _wgp(
        "doctor", "--models", str(manifest), env_updates={
            "WANGP_SSH_TARGET": None,
        }
    )
    assert failed.returncode == 3
    assert f"[FAIL] model_files: missing {missing}" in failed.stdout
    assert "remediation:" in failed.stdout
    assert "ssh_reachable" not in failed.stdout
    assert "Traceback" not in failed.stdout + failed.stderr


def test_configured_host_is_reported_without_implicit_probe() -> None:
    result = _wgp(
        "doctor", env_updates={"WANGP_SSH_TARGET": "unreachable.invalid"}
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "[PASS] host_configuration: Render host configured" in result.stdout
    assert "ssh_reachable" not in result.stdout


def test_explicit_host_probe_reports_five_existing_preflight_kinds(
    tmp_path: Path,
) -> None:
    manifest = tmp_path / "models.json"
    manifest.write_text(
        json.dumps(
            [{"path": "/does/not/exist.bin", "sha256": "0" * 64}]
        ),
        encoding="utf-8",
    )
    result = _wgp(
        "doctor",
        "--probe-host",
        "--models",
        str(manifest),
        env_updates={"WANGP_SSH_TARGET": "127.0.0.1"},
    )
    assert result.returncode == 3
    kinds = {
        line.split("] ", 1)[1].split(":", 1)[0]
        for line in result.stdout.splitlines()
        if line.startswith(("[FAIL]", "[PASS]"))
        and not line.startswith("       ")
    }
    assert {
        "ssh_reachable",
        "model_files",
        "disk_headroom",
        "gpu_state",
        "qc_available",
    }.issubset(kinds)
    assert "Traceback" not in result.stdout + result.stderr


def test_doctor_json_is_deterministic_and_secret_free() -> None:
    first = _wgp("doctor", "--json", env_updates={"WANGP_SSH_TARGET": None})
    second = _wgp("doctor", "--json", env_updates={"WANGP_SSH_TARGET": None})
    assert first.returncode == second.returncode == 0
    assert first.stdout == second.stdout
    payload = json.loads(first.stdout)
    assert payload["ready"] is True
    assert "unreachable.invalid" not in first.stdout


def test_documented_failure_exit_codes_are_stable(tmp_path: Path) -> None:
    usage = _wgp("status", "--db")
    assert usage.returncode == 2
    assert "Traceback" not in usage.stderr

    copied = tmp_path / QUEUE.name
    shutil.copy2(QUEUE, copied)
    connection = sqlite3.connect(copied)
    connection.execute("UPDATE jobs SET clips='not-json'")
    connection.commit()
    connection.close()
    internal = _wgp("status", "--db", str(copied))
    assert internal.returncode == 4
    assert "unexpected internal error" in internal.stderr
    assert "Traceback" not in internal.stderr
