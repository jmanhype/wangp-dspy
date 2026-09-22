"""Run the production no-GPU lane as one stranger-facing session."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path
from types import SimpleNamespace
from tempfile import TemporaryDirectory
from typing import Iterator

import pytest


ROOT = Path(__file__).resolve().parents[2]
BRIEF = "datasets/content_briefs/lf004-operator-dogfood-56f/brief.json"
PLATES = "datasets/content_briefs/lf004-operator-dogfood/plates"
RUN = "datasets/runs/pull/lf004-operator-dogfood-56f-recovery-20260921"
PROVENANCE = "datasets/runs/provenance/lf004-operator-dogfood-56f-recovery-20260921"
WORKERS = (
    "worker-511ee9ee6a8f",
    "worker-8c113b8f1396",
    "worker-99f88572dfb7",
    "worker-fda9bc258c06",
)
UV = ["uv", "run", "--frozen", "--extra", "dev"]


def _run(
    command: list[str], *, cwd: Path, env: dict[str, str]
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, env=env, text=True,
                          capture_output=True, timeout=240, check=False)


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _evidence_digest(worktree: Path) -> str:
    digest = hashlib.sha256()
    roots = [worktree / RUN, worktree / PROVENANCE,
             worktree / "datasets/lf004-operator-dogfood-56f-recovery-20260921.jobs.db",
             *(worktree / "datasets/runs/pull/acceptance" / worker for worker in WORKERS)]
    for root in roots:
        paths = [root] if root.is_file() else sorted(path for path in root.rglob("*") if path.is_file())
        for path in paths:
            digest.update(path.relative_to(worktree).as_posix().encode() + b"\0")
            digest.update(path.read_bytes())
    return digest.hexdigest()


def _output(result: subprocess.CompletedProcess[str]) -> str:
    return result.stdout + result.stderr


@pytest.fixture(scope="module")
def production_session() -> Iterator[SimpleNamespace]:
    """Create and exercise a real clean checkout without host configuration."""

    with TemporaryDirectory(prefix="wangp-production-e2e-") as temporary:
        outside = Path(temporary)
        worktree = outside / "repo"
        outputs = outside / "outputs"
        outputs.mkdir()
        (outputs / "config").mkdir()
        subprocess.run(["git", "worktree", "add", "--detach", str(worktree), "HEAD"],
                       cwd=ROOT, check=True, text=True, capture_output=True)
        try:
            env = {
                **os.environ,
                "TMPDIR": str(outputs),
                "XDG_CONFIG_HOME": str(outputs / "config"),
            }
            for variable in ("WANGP_CONFIG", "WANGP_SSH_TARGET", "WANGP_WGP_ROOT",
                             "WANGP_PULL_ROOT", "WANGP_WGP_PYTHON", "WANGP_3090"):
                env.pop(variable, None)

            queue_copy = outputs / "lf004-jobs.db"
            failure_queue_copy = outputs / "lf003-jobs.db"
            shutil.copy2(worktree / "datasets/lf004-operator-dogfood-56f-recovery-20260921.jobs.db", queue_copy)
            shutil.copy2(worktree / "datasets/lf003-four-cut-fullgate-20260919.jobs.db", failure_queue_copy)
            invalid_brief = outputs / "invalid-brief.json"
            brief = json.loads((worktree / BRIEF).read_text(encoding="utf-8"))
            brief["title"] = ""
            invalid_brief.write_text(json.dumps(brief), encoding="utf-8")
            model_manifest = outputs / "remote-model.json"
            model = {"remote_path": "/home/straughter/models/syncnet_v2/syncnet_v2.model",
                     "sha256": "961e8696f888fce4f3f3a6c3d5b3267cf5b343100b238e79b2659bff2c605442"}
            model_manifest.write_text(json.dumps({"models": [model]}), encoding="utf-8")
            queue_before = _digest(queue_copy)
            failure_queue_before = _digest(failure_queue_copy)
            evidence_before = _evidence_digest(worktree)

            def wgp(*arguments: str) -> subprocess.CompletedProcess[str]:
                return _run([*UV, "wgp", *arguments], cwd=worktree, env=env)

            setup = _run(["uv", "sync", "--extra", "dev"], cwd=worktree, env=env)
            assert setup.returncode == 0, _output(setup)
            quickstart = _run(
                [
                    *UV,
                    "python",
                    "scripts/run_content_brief.py",
                    "--brief",
                    BRIEF,
                    "--plates",
                    PLATES,
                    "--output",
                    str(outputs / "quickstart/plan.json"),
                    "--run-dir",
                    str(outputs / "quickstart/run"),
                ],
                cwd=worktree,
                env=env,
            )
            assert quickstart.returncode == 0, _output(quickstart)

            results = {
                "quickstart": quickstart,
                "validate": wgp("brief", "validate", BRIEF),
                "doctor": wgp("doctor"),
                "status": wgp("status", "--db", str(queue_copy)),
                "review": wgp("review", RUN),
                "failure_status": wgp("status", "--db", str(failure_queue_copy)),
                "invalid": wgp("brief", "validate", str(invalid_brief)),
                "host_probe": wgp(
                    "doctor", "--probe-host", "--models", str(model_manifest)
                ),
                "recipe_write": wgp("recipe", "write", "--run", RUN,
                                    "--out", str(outputs / "recipe.json")),
                "recipe_verify": wgp("recipe", "verify", "--run", RUN,
                                     "--recipe", str(outputs / "recipe.json")),
                "release": wgp("release", "verify"),
            }
            clean = subprocess.run(
                ["git", "status", "--short"],
                cwd=worktree,
                check=True,
                text=True,
                capture_output=True,
            )
            yield SimpleNamespace(
                worktree=worktree,
                recipe_path=outputs / "recipe.json",
                queue_before=queue_before,
                failure_queue_before=failure_queue_before,
                evidence_before=evidence_before,
                queue_after=_digest(queue_copy),
                failure_queue_after=_digest(failure_queue_copy),
                evidence_after=_evidence_digest(worktree),
                clean_status=clean.stdout,
                **results,
            )
        finally:
            subprocess.run(["git", "worktree", "remove", "--force", str(worktree)],
                           cwd=ROOT, check=False, capture_output=True)
            subprocess.run(["git", "worktree", "prune"], cwd=ROOT,
                           check=False, capture_output=True)


def test_stranger_onboarding_reaches_no_gpu_plan(
    production_session: SimpleNamespace,
) -> None:
    session = production_session
    assert "clips=4" in session.quickstart.stdout
    assert "valid=true" in session.validate.stdout
    assert session.validate.returncode == 0
    plan = json.loads(
        (session.worktree.parent / "outputs/quickstart/plan.json").read_text(
            encoding="utf-8"
        )
    )
    assert plan["summary"] == {
        "clip_count": 4,
        "speakers": ["Tess", "Rho", "Tess", "Rho"],
        "planned_duration_s": 9.332,
        "dry_run": True,
        "gpu_work": False,
        "queue_submitted": False,
    }
    assert len(plan["clips"]) == 4
    assert plan["repository"]["clean_tree"] is True


def test_unconfigured_host_and_failures_stay_actionable(
    production_session: SimpleNamespace,
) -> None:
    session = production_session
    assert session.doctor.returncode == 0
    assert "[SKIP] host_configuration:" in session.doctor.stdout
    assert "ready=yes" in session.doctor.stdout
    assert "ssh_reachable" not in session.doctor.stdout

    assert session.status.returncode == 0
    assert "done=4" in session.status.stdout
    assert "failed=0" in session.status.stdout
    assert session.review.returncode == 0
    assert "hash_checks=21 passed=true" in session.review.stdout

    assert session.host_probe.returncode == 3
    host_output = _output(session.host_probe)
    assert "HOST_CONFIGURATION_INCOMPLETE" in host_output
    assert "missing host.target, host.wgp_root" in host_output
    assert "WANGP_SSH_TARGET, WANGP_WGP_ROOT" in host_output
    assert "next: wgp doctor" in host_output
    assert "ssh_reachable" not in host_output

    assert session.invalid.returncode == 2
    invalid_output = _output(session.invalid)
    assert "diagnostic code=INPUT_INVALID" in invalid_output
    assert "observed: title must be a non-empty string" in invalid_output
    assert "remediation:" in invalid_output and "next:" in invalid_output
    assert "evidence:" in invalid_output

    assert session.failure_status.returncode == 0
    failure_output = session.failure_status.stdout
    assert "diagnostic code=GATE_REJECTED" in failure_output
    assert "remediation:" in failure_output and "next:" in failure_output
    assert "evidence:" in failure_output
    assert "Traceback" not in invalid_output + host_output + failure_output


def test_recipe_and_release_are_verifiable_without_gpu(
    production_session: SimpleNamespace,
) -> None:
    session = production_session
    assert session.recipe_write.returncode == 0
    assert "pinned_fields=64" in session.recipe_write.stdout
    assert session.recipe_verify.returncode == 0
    assert "drift=0 verified=true" in session.recipe_verify.stdout
    recipe = json.loads(session.recipe_path.read_text(encoding="utf-8"))
    assert recipe["pinned"]["repository_version"] == "0.1.0"
    assert session.release.returncode == 0
    assert "version=0.1.0" in session.release.stdout
    assert "tag-ready=v0.1.0" in session.release.stdout
    assert "tag_created=false" in session.release.stdout
    assert "release=ready" in session.release.stdout
    assert session.queue_after == session.queue_before
    assert session.failure_queue_after == session.failure_queue_before
    assert session.evidence_after == session.evidence_before
    assert session.clean_status == ""
