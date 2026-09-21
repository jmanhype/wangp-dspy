"""Real failure-input coverage for typed Wangp operator diagnostics."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import shlex
from pathlib import Path
from typing import Any

from services.jobs.preflight import PreflightCheck, PreflightReport
from services.jobs.queue import JobQueue
from wangp.diagnostics import (
    FailureDiagnostic,
    classify_preflight,
    classify_queue_failure,
    render_diagnostic,
)


ROOT = Path(__file__).resolve().parents[1]
BRIEF = ROOT / "datasets/content_briefs/lf004-operator-dogfood-56f/brief.json"
CURRENT_GATE_EVIDENCE = ROOT / (
    "datasets/runs/pull/acceptance/worker-56d7f6cd7b8a/render-0001/"
    "qc-evidence.json"
)
PRODUCTION_REJECTION_EVIDENCE = ROOT / (
    "datasets/runs/provenance/lf004-operator-dogfood-20260920/"
    "cut2-deadletter-review/evidence.json"
)


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _wgp(
    *args: str,
    env_updates: dict[str, str | None] | None = None,
    path: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    if path is not None:
        env["PATH"] = f"{path}:{env['PATH']}"
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


def _record_failure(
    queue: JobQueue,
    job_id: str,
    *,
    failure_class: str,
    detail: str,
    dead_letter: bool = False,
) -> None:
    if queue.get(job_id).state == "pending":
        queue.set_state(job_id, "preflight")
    queue.record_failure(job_id, failure_class=failure_class)
    queue.set_failure_detail(job_id, detail)
    queue.record_attempt_failure(
        job_id, failure_class=failure_class, failure_detail=detail
    )
    if queue.get(job_id).state != "failed":
        queue.set_state(job_id, "failed")
    if dead_letter:
        queue.set_state(job_id, "dead_letter")


def _queue(
    path: Path,
    *,
    evidence_path: Path | None = None,
) -> tuple[JobQueue, str]:
    queue = JobQueue(path)
    clip: dict[str, Any] = {
        "clip_index": 1,
        "kind": "ref2va_render",
        "status": "pending",
        "seed": 905,
    }
    if evidence_path is not None:
        clip["qc_evidence_path"] = str(evidence_path)
    job_id = queue.submit(plan_ref="plan.json", clips=[clip])
    return queue, job_id


def _dead_letter_queue(path: Path, failure_class: str, detail: str) -> str:
    queue, job_id = _queue(path)
    for attempt in range(1, 4):
        _record_failure(
            queue,
            job_id,
            failure_class=failure_class,
            detail=f"{detail} #{attempt}",
        )
        if attempt < 3:
            queue.requeue_failed(job_id, reason="deterministic test retry")
    queue.set_state(job_id, "dead_letter")
    queue.close()
    return job_id


def _gate_evidence(path: Path) -> None:
    payload = {
        "whisper_gates": {
            "pre": {
                "phase": "pre",
                "score": 1.0,
                "pass_bar": 0.6,
                "passed": True,
                "transcript": "expected line",
            },
            "post": {
                "phase": "post",
                "score": 0.42,
                "pass_bar": 0.6,
                "passed": False,
                "transcript": "unexpected line",
            },
        },
        "vision_rejection": {
            "failure_detail": "visual gate failed",
            "scores": {
                "action_match": 0.4,
                "speaker_attribution": 0.5,
                "mouth_activity": 0.8,
                "pass_bar": 0.7,
                "passed": False,
                "speaker_mouth_bboxes": [[0.2, 0.3, 0.05, 0.05]],
                "speaker_mouth_center_spread": [0.01, 0.02],
            },
        },
        "av_sync_gate": {
            "method": "syncnet_v2_multicrop/v1",
            "model_sha256": "1" * 64,
            "offset_frames_25fps": 8,
            "offset_seconds": 0.32,
            "confidence": 0.2,
            "passed": False,
            "phonetic_sync_verified": False,
            "crop_results": [],
        },
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_preflight_model_and_disk_diagnostics_preserve_measured_evidence(
    tmp_path: Path,
) -> None:
    missing = tmp_path / "manifest" / "missing.safetensors"
    corrupt = tmp_path / "manifest" / "wrong.safetensors"
    corrupt.parent.mkdir(parents=True)
    corrupt.write_bytes(b"actual bytes")
    expected = hashlib.sha256(b"expected bytes").hexdigest()
    actual = hashlib.sha256(corrupt.read_bytes()).hexdigest()
    report = PreflightReport(
        passed=False,
        checks=[
            PreflightCheck(
                "model_files",
                False,
                f"missing {missing}: No such file; "
                f"hash mismatch {corrupt}: expected {expected[:12]}… "
                f"got {actual[:12]}…",
            ),
            PreflightCheck(
                "disk_headroom", False, "49G free on /render-root (min 50G)"
            ),
        ],
    )

    diagnostics = classify_preflight(report)
    by_code = {diagnostic.code: diagnostic for diagnostic in diagnostics}

    assert by_code["MODEL_MISSING"].observed == f"missing model path: {missing}"
    assert by_code["MODEL_MISSING"].metadata["path"] == str(missing)
    assert by_code["MODEL_HASH_MISMATCH"].metadata == {
        "path": str(corrupt),
        "expected_sha256_prefix": expected[:12],
        "actual_sha256_prefix": actual[:12],
    }
    assert by_code["DISK_HEADROOM_BELOW_THRESHOLD"].metadata == {
        "path": "/render-root",
        "available_gb": 49.0,
        "minimum_gb": 50.0,
        "check_kind": "disk_headroom",
    }
    assert by_code["DISK_HEADROOM_BELOW_THRESHOLD"].next_command == (
        "df -BG --output=avail /render-root"
    )
    failed_measurement = classify_preflight(PreflightReport(False, [
        PreflightCheck("disk_headroom", False, "df /render-root rc=255")
    ]))[0]
    assert failed_measurement.code == "DISK_CHECK_FAILED"
    assert failed_measurement.next_command == "df -BG --output=avail /render-root"
    local_format = classify_preflight(PreflightReport(False, [PreflightCheck(
        "model_files", False,
        f"sha256 mismatch {corrupt} (expected {expected[:12]}…, got {actual[:12]}…)",
    )]))[0]
    assert local_format.code == "MODEL_HASH_MISMATCH"
    assert local_format.metadata["expected_sha256_prefix"] == expected[:12]
    rendered = "\n".join(render_diagnostic(item) for item in diagnostics)
    assert "what happened" not in rendered
    assert "Wangp never deletes artifacts automatically" in rendered


def test_preflight_distinguishes_ssh_failure_causes() -> None:
    details = {
        "HOST_KEY_REJECTED": "ssh probe rc=255: Host key verification failed.",
        "HOST_AUTHENTICATION_FAILED": "ssh probe rc=255: Permission denied (publickey).",
        "HOST_UNREACHABLE": "ssh probe rc=255: Could not resolve hostname renderer.",
    }
    for expected_code, detail in details.items():
        report = PreflightReport(
            passed=False,
            checks=[PreflightCheck("ssh_reachable", False, detail)],
        )
        diagnostic = classify_preflight(report, target="renderer")[0]
        assert diagnostic.code == expected_code
        assert diagnostic.metadata["target"] == "renderer"
        assert "Traceback" not in render_diagnostic(diagnostic)
    assert (
        classify_preflight(PreflightReport(False, [
            PreflightCheck("ssh_reachable", False, details["HOST_KEY_REJECTED"])
        ]), target="renderer")[0].next_command
        == "ssh-keygen -F renderer"
    )


def test_real_queue_failure_emits_remediation_and_resume_hint(
    tmp_path: Path,
) -> None:
    database = tmp_path / "jobs.db"
    job_id = _dead_letter_queue(database, "render_error", "renderer transport failed")
    before = _digest(database)
    before_names = sorted(path.name for path in tmp_path.iterdir())

    human = _wgp("status", "--db", str(database), "--job", job_id)
    machine = _wgp("status", "--db", str(database), "--job", job_id, "--json")
    review = _wgp("review", "--db", str(database), "--job", job_id)

    assert human.returncode == 0, human.stdout + human.stderr
    assert machine.returncode == 0, machine.stdout + machine.stderr
    assert review.returncode == 0, review.stdout + review.stderr
    combined = human.stdout + review.stdout
    assert "diagnostic code=RETRY_EXHAUSTED" in combined
    assert "renderer transport failed #3" in combined
    assert "attempt row(s)" in combined
    assert "will not retry this job automatically" in combined
    assert f".venv/bin/python scripts/run_jobs.py --db {database} --retry-dead-letter" in combined
    assert "--reason" in combined
    payload = json.loads(machine.stdout)
    diagnostic = payload["diagnostics"][job_id][0]
    assert diagnostic["metadata"]["attempt_count"] == 3
    assert diagnostic["metadata"]["failure_count"] == 3
    assert diagnostic["metadata"]["retryable"] is True
    assert diagnostic["evidence_refs"] == [str(database)]
    assert _digest(database) == before
    assert sorted(path.name for path in tmp_path.iterdir()) == before_names


def test_gate_rejection_surfaces_qc_scores_path_and_review_command(
    tmp_path: Path,
) -> None:
    evidence = tmp_path / "attempt-905" / "qc-evidence.json"
    evidence.parent.mkdir()
    _gate_evidence(evidence)
    database = tmp_path / "jobs.db"
    queue, job_id = _queue(database, evidence_path=evidence)
    _record_failure(
        queue,
        job_id,
        failure_class="qc_gate",
        detail="audiovisual SyncNet gate failed; seed=905",
    )
    queue.close()

    result = _wgp("status", "--db", str(database), "--job", job_id)
    machine = _wgp("status", "--db", str(database), "--job", job_id, "--json")
    review = _wgp("review", "--db", str(database), "--job", job_id)

    assert result.returncode == 0, result.stdout + result.stderr
    assert machine.returncode == 0, machine.stdout + machine.stderr
    assert review.returncode == 0, review.stdout + review.stderr
    human = result.stdout + review.stdout
    assert "diagnostic code=GATE_REJECTED" in human
    assert "gate(s): whisper_post, identity_action_vision, syncnet_audiovisual_sync" in human
    assert '"post": {"pass_bar": 0.6, "passed": false, "score": 0.42' in human
    assert '"action_match": 0.4' in human
    assert '"speaker_attribution": 0.5' in human
    assert '"speaker_mouth_bboxes": [[0.2, 0.3, 0.05, 0.05]]' in human
    assert '"confidence": 0.2' in human
    assert '"offset_frames_25fps": 8' in human
    assert str(evidence) in human
    assert f"wgp review --db {database} --job {job_id}" in human
    assert "Do not change a threshold or bypass the gate" in human
    assert "retry-failed" in human
    payload = json.loads(machine.stdout)
    metrics = payload["diagnostics"][job_id][0]["metadata"]["gate_metrics"]
    assert metrics["whisper"]["post"]["score"] == 0.42
    assert metrics["vision"]["pass_bar"] == 0.7
    assert metrics["syncnet"]["offset_seconds"] == 0.32


def test_retryable_and_deterministic_replay_queue_branches(tmp_path: Path) -> None:
    eligible_db = tmp_path / "eligible.db"
    queue, eligible_id = _queue(eligible_db)
    _record_failure(
        queue, eligible_id, failure_class="render_error", detail="bounded transport error"
    )
    history = queue.attempt_history(eligible_id)
    record = queue.get(eligible_id)
    queue.close()
    eligible = classify_queue_failure(record, history, db_path=eligible_db)
    assert eligible.code == "RETRY_ELIGIBLE"
    assert eligible.next_command == (
        f".venv/bin/python scripts/run_jobs.py --db {eligible_db} --retry-failed"
    )

    blocked_db = tmp_path / "blocked.db"
    queue, blocked_id = _queue(blocked_db)
    _record_failure(
        queue, blocked_id, failure_class="render_error", detail="same deterministic error"
    )
    queue.requeue_failed(blocked_id, reason="operator attempted one fix")
    _record_failure(
        queue, blocked_id, failure_class="render_error", detail="same deterministic error"
    )
    record = queue.get(blocked_id)
    history = queue.attempt_history(blocked_id)
    queue.close()
    blocked = classify_queue_failure(record, history, db_path=blocked_db)
    assert blocked.code == "DETERMINISTIC_REPLAY_BLOCKED"
    assert blocked.metadata["retryable"] is False
    assert "never set allow_deterministic_replay merely to loop" in blocked.remediation


def test_queue_preflight_rows_classify_recorded_subchecks(tmp_path: Path) -> None:
    cases = {
        "MODEL_MISSING": (
            "preflight failed: missing /models/wan.safetensors: "
            "No such file or directory"
        ),
        "MODEL_HASH_MISMATCH": (
            "preflight failed: hash mismatch /models/wan.safetensors: "
            "expected abc123456789… got def987654321…"
        ),
        "DISK_HEADROOM_BELOW_THRESHOLD": (
            "preflight failed: 49G free on /render-root (min 50.0G)"
        ),
    }
    for index, (expected_code, detail) in enumerate(cases.items()):
        database = tmp_path / f"preflight-{index}.db"
        queue, job_id = _queue(database)
        _record_failure(
            queue,
            job_id,
            failure_class="preflight",
            detail=detail,
        )
        queue.close()

        result = _wgp("status", "--db", str(database), "--job", job_id, "--json")

        assert result.returncode == 0, result.stdout + result.stderr
        diagnostic = json.loads(result.stdout)["diagnostics"][job_id][0]
        assert diagnostic["code"] == expected_code
        assert diagnostic["metadata"]["failure_class"] == "preflight"


def test_production_vision_rejection_uses_real_persisted_shape(
    tmp_path: Path,
) -> None:
    evidence = tmp_path / "qc-evidence.json"
    committed = json.loads(PRODUCTION_REJECTION_EVIDENCE.read_text(encoding="utf-8"))
    evidence.write_text(
        json.dumps(committed["906"]["qc_evidence"], indent=2), encoding="utf-8"
    )
    database = tmp_path / "jobs.db"
    queue, job_id = _queue(database, evidence_path=evidence)
    _record_failure(
        queue,
        job_id,
        failure_class="qc_gate",
        detail=(
            "visual gate failed: mouth/action/speaker attribution below pass bar; "
            "seed=906"
        ),
    )
    queue.close()

    result = _wgp("status", "--db", str(database), "--job", job_id, "--json")

    assert result.returncode == 0, result.stdout + result.stderr
    diagnostic = json.loads(result.stdout)["diagnostics"][job_id][0]
    assert diagnostic["code"] == "GATE_REJECTED"
    assert diagnostic["metadata"]["gates"] == ["identity_action_vision"]
    vision = diagnostic["metadata"]["gate_metrics"]["vision"]
    assert vision == {
        "action_match": 0.1,
        "speaker_attribution": 0.1,
        "mouth_activity": 0.2,
        "pass_bar": 0.7,
        "passed": False,
        "speaker_mouth_bboxes": None,
        "speaker_mouth_center_spread": None,
    }


def test_current_gate_evidence_wins_over_labelled_history(tmp_path: Path) -> None:
    historical = tmp_path / "attempt-1-qc-evidence.json"
    historical_payload = json.loads(CURRENT_GATE_EVIDENCE.read_text(encoding="utf-8"))
    historical_payload["av_sync_gate"]["confidence"] = 0.11
    historical_payload["av_sync_gate"]["offset_frames_25fps"] = 99
    historical_payload["whisper_gates"]["post"]["score"] = 0.11
    historical.write_text(json.dumps(historical_payload, indent=2), encoding="utf-8")
    database = tmp_path / "jobs.db"
    queue, job_id = _queue(database, evidence_path=CURRENT_GATE_EVIDENCE)
    current_clips = queue.get(job_id).clips
    current_clips[0]["av_sync_rejections"] = [{
        "attempt": 1,
        "qc_evidence_path": str(historical),
        "failure_class": "qc_gate",
        "failure_detail": "historical audiovisual SyncNet gate failed; seed=904",
    }]
    queue.update_clips(job_id, current_clips)
    _record_failure(
        queue,
        job_id,
        failure_class="qc_gate",
        detail="audiovisual SyncNet gate failed; seed=905",
    )
    queue.close()

    result = _wgp("status", "--db", str(database), "--job", job_id, "--json")

    assert result.returncode == 0, result.stdout + result.stderr
    metadata = json.loads(result.stdout)["diagnostics"][job_id][0]["metadata"]
    metrics = metadata["gate_metrics"]
    assert metrics["syncnet"]["confidence"] == 0.58634
    assert metrics["syncnet"]["offset_frames_25fps"] == -1
    assert metrics["whisper"]["post"]["score"] == 0.667
    historical_metrics = metadata["historical_gate_metrics"]
    assert len(historical_metrics) == 1
    assert historical_metrics[0]["attempt"] == 1
    assert historical_metrics[0]["source"] == str(historical)
    assert historical_metrics[0]["gate_metrics"]["syncnet"]["confidence"] == 0.11
    assert historical_metrics[0]["gate_metrics"]["syncnet"]["offset_frames_25fps"] == 99
    assert historical_metrics[0]["gate_metrics"]["whisper"]["post"]["score"] == 0.11


def test_executor_retryable_lane_and_admission_classes_keep_retry_guidance(
    tmp_path: Path,
) -> None:
    cases = {
        "ref2va_lane_unavailable": (
            "clip 1 is a ref2va_render job but no ref2va renderer was wired "
            "into the executor — refusing to fall back to fl2va"
        ),
        "queue_admission_error": (
            "[lane=ref2va] failed to persist render-admission marker for clip 1: "
            "ValueError: stale attempt"
        ),
    }
    for index, (failure_class, detail) in enumerate(cases.items()):
        database = tmp_path / f"retry-{index}.db"
        queue, job_id = _queue(database)
        _record_failure(queue, job_id, failure_class=failure_class, detail=detail)
        record = queue.get(job_id)
        history = queue.attempt_history(job_id)
        queue.close()

        diagnostic = classify_queue_failure(record, history, db_path=database)

        assert diagnostic.code == "RETRY_ELIGIBLE"
        assert diagnostic.metadata["failure_class"] == failure_class
        assert diagnostic.next_command == (
            f".venv/bin/python scripts/run_jobs.py --db {database} --retry-failed"
        )


def test_credential_shaped_queue_path_is_redacted_in_both_renderers(
    tmp_path: Path,
) -> None:
    database = tmp_path / "api_key=super-secret-value" / "jobs.db"
    database.parent.mkdir()
    queue, job_id = _queue(database)
    _record_failure(
        queue,
        job_id,
        failure_class="new_transport",
        detail="upstream rejected authorization: Basic abcdef123456",
    )
    queue.close()

    human = _wgp("status", "--db", str(database), "--job", job_id)
    machine = _wgp("status", "--db", str(database), "--job", job_id, "--json")

    assert human.returncode == machine.returncode == 0
    for output in (human.stdout, machine.stdout):
        assert "super-secret-value" not in output
        assert "abcdef123456" not in output
        assert "api_key=<redacted>" in output
    assert json.loads(machine.stdout)["db_path"].endswith("api_key=<redacted>/jobs.db")
    direct = FailureDiagnostic(
        "SECRET_URL", "error", "credential URL", "https://user:pass@example.test",
        "query token=super-secret-value", "inspect both credential forms",
        f"wgp inspect {shlex.quote('https://user:pass@example.test')}",
        ("https://user:pass@example.test?token=super-secret-value",),
    )
    mapped = direct.mapping()
    rendered = render_diagnostic(direct)
    for output in (json.dumps(mapped), rendered):
        assert "user:pass" not in output
        assert "super-secret-value" not in output
        assert "https://<redacted>@example.test" in output
        assert "token=<redacted>" in output
    assert shlex.split(mapped["next_command"])[1] == "inspect"


def test_invalid_review_run_command_is_shell_safe(tmp_path: Path) -> None:
    unsafe_name = "run-' ; TOUCHED=1; #"
    run = tmp_path / unsafe_name
    run.mkdir()
    expected_command = f"wgp review {shlex.quote(str(run))}"

    human = _wgp("review", str(run))
    machine = _wgp("review", str(run), "--json")

    assert human.returncode == machine.returncode == 2
    assert f"next: {expected_command}" in human.stderr
    payload = json.loads(machine.stdout)
    assert payload["diagnostics"][0]["next_command"] == expected_command
    assert shlex.split(payload["diagnostics"][0]["next_command"])[1] == "review"


def test_review_missing_job_json_returns_structured_diagnostic(
    tmp_path: Path,
) -> None:
    database = tmp_path / "jobs.db"
    queue, _ = _queue(database)
    queue.close()

    result = _wgp(
        "review", "--db", str(database), "--job", "missing-job", "--json"
    )

    assert result.returncode == 2
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    diagnostic = payload["diagnostics"][0]
    assert diagnostic["code"] == "INPUT_INVALID"
    assert "missing-job" in diagnostic["observed"]
    assert diagnostic["metadata"]["source"] == str(database)


def test_unknown_failure_and_secret_redaction(tmp_path: Path) -> None:
    database = tmp_path / "jobs.db"
    queue, job_id = _queue(database)
    _record_failure(
        queue,
        job_id,
        failure_class="new_transport",
        detail="api_key=super-secret-value bearer ABCDEFGHIJKLMNOPQRSTUVWXYZ1234",
    )
    queue.close()
    result = _wgp("status", "--db", str(database), "--job", job_id, "--json")
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    diagnostic = payload["diagnostics"][job_id][0]
    assert diagnostic["code"] == "UNKNOWN_FAILURE"
    assert diagnostic["metadata"]["failure_class"] == "new_transport"
    assert "super-secret-value" not in result.stdout
    assert "ABCDEFGHIJKLMNOPQRSTUVWXYZ1234" not in result.stdout
    assert "api_key=<redacted>" in result.stdout
    assert "bearer <redacted>" in result.stdout

    direct = FailureDiagnostic(
        "SECRET_EXAMPLE", "error", "Redaction", "token=abc123",
        "why", "remediation", metadata={"authorization": "Bearer abc123"},
    )
    assert direct.mapping()["observed"] == "token=<redacted>"
    assert "abc123" not in render_diagnostic(direct)


def test_doctor_host_diagnostics_are_explicit_and_default_makes_no_ssh_call(
    tmp_path: Path,
) -> None:
    commands = tmp_path / "command-bin"
    commands.mkdir()
    ssh_log = tmp_path / "ssh.log"
    ssh = commands / "ssh"
    log_target = shlex.quote(str(ssh_log))
    ssh.write_text(
        "#!/bin/sh\n"
        f'printf "%s\\n" "$*" >> {log_target}\n'
        "printf 'renderer.test: Connection refused\\n' >&2\n"
        "exit 255\n",
        encoding="utf-8",
    )
    ssh.chmod(0o755)
    host_env = {
        "WANGP_SSH_TARGET": "renderer.test",
        "WANGP_WGP_ROOT": "/remote/wgp",
        "WANGP_PULL_ROOT": str(tmp_path / "pull"),
        "WANGP_WGP_PYTHON": "/remote/bin/python",
    }
    manifest = tmp_path / "models.json"
    manifest.write_text(
        json.dumps([{"remote_path": "ckpts/model.bin", "sha256": "a" * 64}]),
        encoding="utf-8",
    )

    default = _wgp("doctor", env_updates=host_env, path=commands)
    assert default.returncode == 0, default.stdout + default.stderr
    assert "[PASS] host_configuration:" in default.stdout
    assert "diagnostic code=" not in default.stdout
    assert not ssh_log.exists() or ssh_log.read_text() == ""

    explicit = _wgp(
        "doctor", "--probe-host", "--models", str(manifest),
        env_updates=host_env, path=commands,
    )
    assert explicit.returncode == 3, explicit.stdout + explicit.stderr
    assert "diagnostic code=HOST_UNREACHABLE" in explicit.stdout
    assert "renderer.test: Connection refused" in explicit.stdout
    assert "Verify network/VPN reachability" in explicit.stdout
    assert "ssh -o BatchMode=yes renderer.test true" in explicit.stdout
    assert "renderer.test true" in ssh_log.read_text()

    machine = _wgp(
        "doctor", "--probe-host", "--models", str(manifest), "--json",
        env_updates=host_env, path=commands,
    )
    assert machine.returncode == 3
    payload = json.loads(machine.stdout)
    assert set(payload["diagnostics"][0]) == {
        "code", "severity", "title", "observed", "why", "remediation",
        "next_command", "evidence_refs", "metadata",
    }
    assert payload["diagnostics"][0]["code"] == "HOST_UNREACHABLE"


def test_review_provenance_failure_uses_shared_diagnostic_vocabulary(
    tmp_path: Path,
) -> None:
    bundle = tmp_path / "review-bundle"
    bundle.mkdir()
    artifact = bundle / "assembled.mp4"
    artifact.write_bytes(b"changed bytes")
    provenance = bundle / "final-provenance.json"
    provenance.write_text(
        json.dumps({"path": str(artifact), "sha256": "0" * 64}),
        encoding="utf-8",
    )
    human = _wgp("review", str(bundle))
    machine = _wgp("review", str(bundle), "--json")
    assert human.returncode == machine.returncode == 2
    assert "diagnostic code=PROVENANCE_HASH_MISMATCH" in human.stdout
    assert str(artifact) in human.stdout
    assert f"wgp review {bundle} --json" in human.stdout
    payload = json.loads(machine.stdout)
    assert payload["diagnostics"][0]["code"] == "PROVENANCE_HASH_MISMATCH"
    assert "run identity inconsistent" in payload["diagnostics"][0]["why"]
    assert payload["diagnostics"][0]["metadata"]["expected_sha256"] == "0" * 64
    assert "Traceback" not in human.stdout + human.stderr + machine.stderr


def test_invalid_brief_gets_typed_diagnostic_at_cli_boundary(
    tmp_path: Path,
) -> None:
    payload = json.loads(BRIEF.read_text(encoding="utf-8"))
    payload["dialogue"][0]["speaker"] = "NotInRoster"
    invalid = tmp_path / "invalid-brief.json"
    invalid.write_text(json.dumps(payload), encoding="utf-8")
    human = _wgp("brief", "validate", str(invalid))
    machine = _wgp("brief", "validate", str(invalid), "--json")
    assert human.returncode == machine.returncode == 2
    assert "diagnostic code=INPUT_INVALID" in human.stderr
    assert "dialogue[0].speaker" in human.stderr
    assert f"wgp brief validate {invalid}" in human.stderr
    machine_payload = json.loads(machine.stdout)
    assert machine_payload["diagnostics"][0]["metadata"]["source"] == str(invalid)
    assert "Traceback" not in human.stdout + human.stderr + machine.stderr
