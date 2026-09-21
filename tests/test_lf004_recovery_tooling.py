from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from services.jobs.queue import JobQueue, effective_render_fingerprint

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "datasets/content_briefs/lf004-operator-dogfood-56f/run"
SPEC = importlib.util.spec_from_file_location("lf004_recover_once", RUN / "recover_once.py")
recover = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(recover)


def make_queue(path: Path) -> tuple[JobQueue, list[str]]:
    plan = json.loads((ROOT / "datasets/content_briefs/lf004-operator-dogfood-56f/plan.json").read_text())
    queue = JobQueue(str(path))
    first = dict(plan["clips"][0], status="done", log="cut1.log", mp4="cut1.mp4", qc_verdict={"verdict": "NEEDS REVIEW", "path": "cut1-qc.json"})
    ids = [queue.submit_completed(plan_ref="test", clips=[first])]
    for clip in plan["clips"][1:]:
        ids.append(queue.submit(plan_ref="test", clips=[dict(clip, needs=ids[-1])]))
    queue.set_state(ids[1], "preflight")
    queue.record_failure(ids[1], failure_class="test_gate")
    queue.set_state(ids[1], "failed")
    queue.set_failure_detail(ids[1], "later-cut failure fixture")
    return queue, ids


def test_reconcile_covers_done_and_reopens_only_later_failure(tmp_path: Path) -> None:
    queue, ids = make_queue(tmp_path / "jobs.db")
    queue.close()
    recover.reconcile(tmp_path / "jobs.db", tmp_path)
    corrected = JobQueue(str(tmp_path / "jobs.db"))
    states = {corrected.get(job_id).clips[0]["clip_index"]: corrected.get(job_id).state for job_id in ids}
    assert states == {1: "done", 2: "pending", 3: "pending", 4: "pending"}
    for job_id in ids:
        clip = corrected.get(job_id).clips[0]
        assert clip["render_fingerprint"] == effective_render_fingerprint(clip)
        assert clip["audio_carrier"] == "native_h3"
        assert clip["speaker_manifest"]["schema"] == "wangp-dspy.speaker-manifest/v1"
    corrected.close()


def test_reconcile_rejects_changed_plan_before_queue_work(tmp_path: Path) -> None:
    plan = json.loads((ROOT / "datasets/content_briefs/lf004-operator-dogfood-56f/plan.json").read_text())
    plan["summary"]["planned_duration_s"] = 17.832
    changed = tmp_path / "plan.json"
    changed.write_text(json.dumps(plan))
    with pytest.raises(ValueError, match="approved LF004 input hash mismatch"):
        recover.reconcile(tmp_path / "unused.db", tmp_path, plan_path=changed)
    assert not (tmp_path / "unused.db").exists()


def test_programmatic_run_film_uses_story_ledger(monkeypatch: pytest.MonkeyPatch) -> None:
    captured = {}

    def fake_run_film(*args, **kwargs):
        captured.update(kwargs)
        return [captured]

    import scripts.run_film as run_film_module
    monkeypatch.setattr(run_film_module, "run_film", fake_run_film)
    assert recover.run_film_once() == [captured]
    assert Path(captured["run_ledger_path"]) == recover.LEDGER
    assert Path(captured["db_path"]) == recover.DB


def make_launcher_root(target: Path) -> Path:
    target.mkdir(parents=True)
    for name in ("services", "host", "predict", "qc", "scripts"):
        os.symlink(ROOT / name, target / name)
    briefs = target / "datasets/content_briefs"
    briefs.mkdir(parents=True)
    os.symlink(ROOT / "datasets/content_briefs/lf004-operator-dogfood", briefs / "lf004-operator-dogfood")
    shutil.copytree(ROOT / "datasets/content_briefs/lf004-operator-dogfood-56f", briefs / "lf004-operator-dogfood-56f", ignore=shutil.ignore_patterns("__pycache__"))
    runs = target / "datasets/runs"
    provenance = runs / "provenance"
    provenance.mkdir(parents=True)
    for name in ("lf003-vibevoice-audition-20260917", "lf003-vibevoice-rho-strong-20260918", "lf003-four-cut-fullgate-20260919"):
        os.symlink(ROOT / "datasets/runs/provenance" / name, provenance / name)
    return briefs / "lf004-operator-dogfood-56f/run/run_recovery_once.sh"


def run_launcher(launcher: Path, cwd: Path) -> subprocess.CompletedProcess[str]:
    cwd.mkdir(parents=True, exist_ok=True)
    environment = {**os.environ, "RECOVERY_PYTHON": sys.executable, "WANGP_RECOVERY_SETUP_ONLY": "1"}
    return subprocess.run(["bash", str(launcher)], cwd=cwd, text=True, capture_output=True, env=environment, check=False)


def test_launcher_setup_is_root_relative_from_foreign_cwd(tmp_path: Path) -> None:
    launcher = make_launcher_root(tmp_path / "root")
    first = run_launcher(launcher, tmp_path / "cwd-a")
    assert first.returncode == 0, first.stderr
    stage_path = tmp_path / "root/datasets/runs/provenance/lf004-operator-dogfood-56f-recovery-20260921/stage-plan.json"
    first_stage = stage_path.read_bytes()
    stage_path.unlink()
    second = run_launcher(launcher, tmp_path / "cwd-b")
    assert second.returncode == 0, second.stderr
    assert stage_path.read_bytes() == first_stage
    payload = json.loads(stage_path.read_text())
    assert payload["root"] == str(tmp_path / "root")
    assert len(payload["assets"]) == 7
    assert all(item["local"].startswith(str(tmp_path / "root")) for item in payload["assets"])
    assert not (tmp_path / "root/datasets/runs/provenance/lf004-operator-dogfood-56f-recovery-20260921/execution-command.json").exists()


def test_launcher_hash_failure_aborts_before_setup_or_staging(tmp_path: Path) -> None:
    launcher = make_launcher_root(tmp_path / "root")
    brief = launcher.parents[1] / "brief.json"
    payload = json.loads(brief.read_text())
    payload["title"] = "unapproved"
    brief.write_text(json.dumps(payload))
    result = run_launcher(launcher, tmp_path / "foreign")
    assert result.returncode != 0
    provenance = tmp_path / "root/datasets/runs/provenance/lf004-operator-dogfood-56f-recovery-20260921"
    assert (provenance / "input-verification.json").exists()
    assert not (provenance / "execution-command.json").exists()
    assert not (provenance / "setup-command.json").exists()
    assert not (provenance / "stage-plan.json").exists()
    assert not (provenance / "preflight.txt").exists()
