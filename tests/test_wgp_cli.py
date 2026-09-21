"""Real-subprocess integration tests for the stable wgp surface."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import stat
from pathlib import Path

from wangp.doctor import (
    REMOTE_MINIMUM_FREE_GB,
    _preflight_doctor_checks,
    remote_model_specs,
)


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


class _LocalCommandHost:
    """A real subprocess host seam for deterministic local preflight checks."""

    def __init__(self, command_dir: Path) -> None:
        self.command_dir = command_dir

    def run_probe(self, argv: list[str], timeout: int = 30) -> tuple[int, str, str]:
        completed = subprocess.run(
            [str(self.command_dir / argv[0]), *argv[1:]],
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
            env={"PATH": f"{self.command_dir}:/usr/bin:/bin"},
        )
        return completed.returncode, completed.stdout, completed.stderr


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
    before_names = sorted(path.name for path in tmp_path.iterdir())
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
    assert sorted(path.name for path in tmp_path.iterdir()) == before_names


def test_review_reports_queue_attempts_and_evidence(tmp_path: Path) -> None:
    copied = tmp_path / QUEUE.name
    shutil.copy2(QUEUE, copied)
    before = _digest(copied)
    before_names = sorted(path.name for path in tmp_path.iterdir())
    result = _wgp("review", "--db", str(copied), "--job", JOB)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "clip=1" in result.stdout
    assert "kind=ref2va_render" in result.stdout
    assert "attempt=1" in result.stdout
    assert "reapply recorded LF004" in result.stdout
    assert "evidence:" in result.stdout
    assert _digest(copied) == before
    assert sorted(path.name for path in tmp_path.iterdir()) == before_names


def test_review_verifies_final_provenance_artifact_hashes() -> None:
    result = _wgp("review", str(RUN))
    assert result.returncode == 0, result.stdout + result.stderr
    assert f"film={RUN / 'assembled.mp4'}" in result.stdout
    assert f"probe={RUN / 'probe.json'}" in result.stdout
    assert "contact_sheet=" in result.stdout
    assert "hash_checks=21 passed=true" in result.stdout
    assert "sha256 mismatch" not in result.stdout


def test_review_rejects_missing_and_empty_provenance(tmp_path: Path) -> None:
    absent = tmp_path / "incomplete-run"
    absent.mkdir()
    absent_result = _wgp("review", str(absent))
    assert absent_result.returncode == 2
    assert "final-provenance.json is missing" in absent_result.stderr

    empty_run = tmp_path / "empty-provenance"
    empty_run.mkdir()
    (empty_run / "final-provenance.json").write_text("{}", encoding="utf-8")
    empty_result = _wgp("review", str(empty_run))
    assert empty_result.returncode == 2
    assert "no recognized path/sha256 pairs" in empty_result.stderr


def _legacy_queue(path: Path, job_id: str = "legacy-job") -> None:
    connection = sqlite3.connect(path)
    connection.executescript(
        """
        CREATE TABLE jobs (
          job_id TEXT PRIMARY KEY,
          state TEXT NOT NULL,
          plan_ref TEXT NOT NULL,
          clips TEXT NOT NULL,
          failure_count INTEGER NOT NULL DEFAULT 0,
          failure_class TEXT,
          failure_detail TEXT,
          created_at REAL NOT NULL
        );
        """
    )
    connection.execute(
        "INSERT INTO jobs VALUES (?,?,?,?,?,?,?,?)",
        (
            job_id,
            "done",
            "legacy",
            json.dumps([{"kind": "legacy"}]),
            0,
            None,
            None,
            1.0,
        ),
    )
    connection.commit()
    connection.close()


def test_status_and_review_open_legacy_queues_read_only(tmp_path: Path) -> None:
    original_mode = stat.S_IMODE(tmp_path.stat().st_mode)
    for verb in ("status", "review"):
        database = tmp_path / f"{verb}-jobs.db"
        _legacy_queue(database)
        before = _digest(database)
        database.chmod(0o444)
        tmp_path.chmod(0o555)
        try:
            args = [verb, "--db", str(database)]
            if verb == "review":
                args.extend(["--job", "legacy-job"])
            result = _wgp(*args)
            assert result.returncode == 0, result.stdout + result.stderr
            assert _digest(database) == before
            assert not list(tmp_path.glob(f"{database.name}-*"))
        finally:
            tmp_path.chmod(original_mode)
            database.chmod(0o644)


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


def test_local_doctor_hashes_manifest_model_contents(tmp_path: Path) -> None:
    model = tmp_path / "model.safetensors"
    model.write_bytes(b"corrupt model bytes")
    expected = hashlib.sha256(b"unrelated bytes").hexdigest()
    manifest = tmp_path / "models.json"
    manifest.write_text(
        json.dumps([{"local_path": str(model), "sha256": expected}]),
        encoding="utf-8",
    )
    result = _wgp(
        "doctor",
        "--models",
        str(manifest),
        env_updates={"WANGP_SSH_TARGET": None},
    )
    assert result.returncode == 3
    assert f"[FAIL] model_files: sha256 mismatch {model}" in result.stdout
    assert "expected" in result.stdout
    assert "remediation:" in result.stdout
    assert "ssh_reachable" not in result.stdout


def test_configured_host_is_reported_without_implicit_probe() -> None:
    result = _wgp(
        "doctor", env_updates={"WANGP_SSH_TARGET": "unreachable.invalid"}
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "[PASS] host_configuration: Render host configured" in result.stdout
    assert "ssh_reachable" not in result.stdout


def test_explicit_host_probe_requires_a_manifest() -> None:
    result = _wgp(
        "doctor", "--probe-host", env_updates={"WANGP_SSH_TARGET": None}
    )
    assert result.returncode == 3
    assert "[FAIL] model_files:" in result.stdout
    assert "--models with at least one remote_path" in result.stdout
    assert "ssh_reachable" not in result.stdout
    assert "Traceback" not in result.stdout + result.stderr


def _probe_command_dir(path: Path) -> None:
    path.mkdir()
    commands = {
        "true": "#!/bin/sh\nexit 0\n",
        "sha256sum": '#!/bin/sh\nexec openssl dgst -sha256 -r "$1"\n',
        "df": "#!/bin/sh\nprintf '49G\\n'\n",
        "nvidia-smi": "#!/bin/sh\nexit 0\n",
        "curl": '#!/bin/sh\nprintf \'{"status":"ok"}\\n\'\n',
    }
    for name, body in commands.items():
        command = path / name
        command.write_text(body, encoding="utf-8")
        command.chmod(0o755)


def test_host_probe_uses_remote_paths_and_nonzero_disk_minimum(
    tmp_path: Path,
) -> None:
    commands = tmp_path / "probe-bin"
    _probe_command_dir(commands)
    model = tmp_path / "remote-root" / "ckpts" / "model.bin"
    model.parent.mkdir(parents=True)
    model.write_bytes(b"valid remote model bytes")
    specs = [
        {
            "local_path": "/does/not/exist/local.bin",
            "remote_path": "ckpts/model.bin",
            "sha256": _digest(model),
        },
        {
            "local_path": "/does/not/exist/local.bin",
            "remote_path": str(model),
            "sha256": _digest(model),
        },
    ]
    normalized = remote_model_specs(specs, wgp_root=tmp_path / "remote-root")
    assert normalized[0]["path"] == str(model)
    assert normalized[1]["path"] == str(model)

    report = _preflight_doctor_checks(
        _LocalCommandHost(commands),
        specs,
        wgp_root=tmp_path / "remote-root",
        disk_path=tmp_path / "remote-root",
    )
    by_kind = {check.kind: check for check in report}
    assert by_kind["model_files"].status == "pass"
    assert by_kind["disk_headroom"].status == "failed"
    assert "49G free" in by_kind["disk_headroom"].detail
    assert f"(min {REMOTE_MINIMUM_FREE_GB}G)" in by_kind["disk_headroom"].detail
    assert by_kind["ssh_reachable"].status == "pass"
    assert by_kind["gpu_state"].status == "pass"
    assert by_kind["qc_available"].status == "pass"


def test_host_probe_rejects_a_genuinely_missing_remote_model(
    tmp_path: Path,
) -> None:
    commands = tmp_path / "probe-bin"
    _probe_command_dir(commands)
    specs = [{"remote_path": "ckpts/missing.bin", "sha256": "0" * 64}]
    report = _preflight_doctor_checks(
        _LocalCommandHost(commands),
        specs,
        wgp_root=tmp_path / "remote-root",
        disk_path=tmp_path / "remote-root",
    )
    model_check = next(check for check in report if check.kind == "model_files")
    assert model_check.status == "failed"
    missing = tmp_path / "remote-root" / "ckpts" / "missing.bin"
    assert f"missing {missing}" in model_check.detail


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


def test_built_wheel_installs_and_doctor_runs_outside_source(
    tmp_path: Path,
) -> None:
    dist = tmp_path / "dist"
    build = subprocess.run(
        ["uv", "build", "--out-dir", str(dist)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=600,
        check=False,
    )
    assert build.returncode == 0, build.stdout + build.stderr
    wheels = list(dist.glob("*.whl"))
    sdists = list(dist.glob("*.tar.gz"))
    assert len(wheels) == 1
    assert len(sdists) == 1

    venv = tmp_path / "installed-venv"
    environment = subprocess.run(
        ["uv", "venv", str(venv)],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )
    assert environment.returncode == 0, environment.stdout + environment.stderr
    install = subprocess.run(
        [
            "uv",
            "pip",
            "install",
            "--python",
            str(venv / "bin" / "python"),
            str(wheels[0]),
        ],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        timeout=600,
        check=False,
    )
    assert install.returncode == 0, install.stdout + install.stderr

    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    doctor = subprocess.run(
        [str(venv / "bin" / "wgp"), "doctor", "--json"],
        cwd=tmp_path,
        env=env,
        text=True,
        capture_output=True,
        timeout=180,
        check=False,
    )
    assert doctor.returncode == 0, doctor.stdout + doctor.stderr
    payload = json.loads(doctor.stdout)
    assert payload["ready"] is True

    origin = subprocess.run(
        [
            str(venv / "bin" / "python"),
            "-c",
            "import scripts, wangp; print(scripts.__file__); print(wangp.__file__)",
        ],
        cwd=tmp_path,
        env=env,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert origin.returncode == 0, origin.stdout + origin.stderr
    scripts_path, wangp_path = origin.stdout.splitlines()
    assert str(ROOT) not in scripts_path
    assert str(ROOT) not in wangp_path
