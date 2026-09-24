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


def make_verdict_fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    output = tmp_path / "output"
    provenance = output / "provenance"
    provenance.mkdir(parents=True)
    media = tmp_path / "assembled.mp4"
    media.write_bytes(b"LF004 deterministic reconciliation fixture")
    media_sha = recover.sha(media)
    acceptance_path = provenance / "operator-acceptance.json"
    acceptance = json.loads((recover.PROVENANCE / "operator-acceptance.json").read_text())
    assert (acceptance["schema_version"], acceptance["status"], acceptance["creative_acceptance"], acceptance["verdict"], acceptance["verdict_source"]) == ("wangp-dspy.operator-acceptance/v1", "operator_accepted", "accepted", "keep", 'operator message: "i approve"')
    acceptance["artifact"]["sha256"] = media_sha
    acceptance_path.write_text(json.dumps(acceptance, indent=1) + "\n")
    monkeypatch.setattr(recover, "FINAL_MEDIA_SHA256", media_sha)
    monkeypatch.setattr(recover, "OPERATOR_ACCEPTANCE_SHA256", recover.sha(acceptance_path))

    source = recover.PULL
    final = json.loads((source / "final-provenance.json").read_text())
    final["final_media"]["path"] = str(media)
    final["final_media"]["sha256"] = media_sha
    final["assembly"]["output_sha256"] = media_sha
    final["status"] = "operator_review_pending"
    final["creative_acceptance"] = "none"
    if isinstance(final.get("post_execution_recovery"), dict):
        final["post_execution_recovery"]["final_status"] = "operator_review_pending"
        for field in ("status_history", "operator_verdict", "reconciliation"):
            final["post_execution_recovery"].pop(field, None)
    for field in ("operator_verdict", "status_history", "launcher_reconciliation"):
        final.pop(field, None)
    recover.write_json(output / "final-provenance.json", final)
    sidecar = json.loads((source / "operator_review_pending.json").read_text())
    sidecar["final_sha256"] = media_sha
    sidecar["status"] = "operator_review_pending"
    for field in ("record_class", "historical_status", "superseded_by"):
        sidecar.pop(field, None)
    recover.write_json(output / "operator_review_pending.json", sidecar)
    postprocess = json.loads((source / "postprocess-recovery.json").read_text())
    postprocess["final_status"] = "operator_review_pending"
    for field in ("status_history", "operator_verdict", "reconciliation"):
        postprocess.pop(field, None)
    recover.write_json(output / "postprocess-recovery.json", postprocess)
    (output / "review.md").write_text((source / "review.md").read_text())
    ledger = json.loads(recover.LEDGER.read_text())
    ledger["final_sha256"] = media_sha
    ledger["status"] = "operator_review_pending"
    for field in ("operator_verdict", "operator_reconciliation"):
        ledger.pop(field, None)
    recover.write_json(output / "run-ledger.json", ledger)
    return output


def snapshot(root: Path) -> dict[str, bytes]:
    return {str(path.relative_to(root)): path.read_bytes() for path in sorted(root.rglob("*")) if path.is_file()}


def test_record_operator_verdict_command_reconciles_and_is_idempotent(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    output = make_verdict_fixture(tmp_path, monkeypatch)
    assert recover.sha(recover.PROVENANCE / "operator-acceptance.json") == "e10e3e2180c9570a4ed731f428bab6a2e036b94b4988bd092f943c7b2dd1c76d"
    assert recover.main(["record-operator-verdict", "--acceptance", str(output / "provenance/operator-acceptance.json"), "--output-root", str(output)]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["action"] == "reconciled"
    final = json.loads((output / "final-provenance.json").read_text())
    identity = final["launcher_reconciliation"]
    assert identity["as_executed"]["launcher_sha256"] == recover.EXECUTED_LAUNCHER_SHA256
    assert identity["current_checkout"]["launcher_sha256"] != recover.EXECUTED_LAUNCHER_SHA256
    assert identity["current_checkout"]["scripts_run_film_sha256"] == recover.sha(recover.ROOT / "scripts/run_film.py")
    assert identity["current_checkout"]["scripts_run_film_git_blob"] == "f8af9b7eaee0da2a3b7af95a6845788f1c6a8aca"
    assert final["repository"] == json.loads(recover.PULL.joinpath("final-provenance.json").read_text())["repository"]
    ledger = json.loads((output / "run-ledger.json").read_text())
    assert ledger["status"] == "operator_accepted"
    assert ledger["repository"] == json.loads(recover.LEDGER.read_text())["repository"]
    assert json.loads((output / "postprocess-recovery.json").read_text())["final_status"] == "operator_accepted"
    sidecar = json.loads((output / "operator_review_pending.json").read_text())
    assert (sidecar["record_class"], sidecar["historical_status"]) == ("historical_pre_verdict_snapshot", "operator_review_pending")
    before = snapshot(output)
    second = recover.record_operator_verdict(output_root=output)
    assert second["action"] == "no_change"
    assert snapshot(output) == before


def test_record_operator_verdict_output_root_ignores_external_acceptance(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    output = make_verdict_fixture(tmp_path, monkeypatch)
    external_pull = tmp_path / "machine-local-pull"
    external_pull.mkdir()
    external_acceptance = external_pull / "operator-acceptance.json"
    external_acceptance.write_bytes(b"ignored machine-local acceptance")
    monkeypatch.setattr(recover, "PULL", external_pull)
    before = snapshot(output)

    result = recover.record_operator_verdict(output_root=output)

    assert result["action"] == "reconciled"
    assert snapshot(output) != before
    assert external_acceptance.read_bytes() == b"ignored machine-local acceptance"


@pytest.mark.parametrize("redirected_input", ["acceptance", "run_ledger"])
def test_record_operator_verdict_scoped_rejects_symlink_escape(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, redirected_input: str) -> None:
    output = make_verdict_fixture(tmp_path, monkeypatch)
    scoped_path = output / ("provenance/operator-acceptance.json" if redirected_input == "acceptance" else "run-ledger.json")
    external = tmp_path / "external-input.json"
    external.write_bytes(b"external acceptance decoy" if redirected_input == "acceptance" else scoped_path.read_bytes())
    scoped_path.unlink()
    scoped_path.symlink_to(external)
    external_sha = recover.sha(external)
    before = snapshot(output)

    with pytest.raises(ValueError, match="path escapes output root") as error:
        recover.record_operator_verdict(output_root=output)

    message = str(error.value)
    assert str(external.resolve()) not in message
    assert external_sha not in message
    assert snapshot(output) == before
    assert external.read_bytes() == (b"external acceptance decoy" if redirected_input == "acceptance" else before["run-ledger.json"])


def test_record_operator_verdict_scoped_missing_source_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    output = make_verdict_fixture(tmp_path, monkeypatch)
    before = snapshot(output)
    before.pop("provenance/operator-acceptance.json")
    (output / "provenance/operator-acceptance.json").unlink()

    with pytest.raises(FileNotFoundError, match="not found in output root"):
        recover.record_operator_verdict(output_root=output)

    assert snapshot(output) == before


def test_record_operator_verdict_rejects_explicit_acceptance_outside_output_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    output = make_verdict_fixture(tmp_path, monkeypatch)
    outside = tmp_path / "outside-operator-acceptance.json"
    outside.write_bytes((output / "provenance/operator-acceptance.json").read_bytes())
    before = snapshot(output)

    with pytest.raises(ValueError, match="escapes output root"):
        recover.record_operator_verdict(outside, output)

    assert snapshot(output) == before


def test_record_operator_verdict_real_path_prefers_canonical_without_local_copy(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    output = make_verdict_fixture(tmp_path, monkeypatch)
    assert recover.record_operator_verdict(output_root=output)["action"] == "reconciled"
    monkeypatch.setattr(recover, "PULL", output)
    monkeypatch.setattr(recover, "PROVENANCE", output / "provenance")
    monkeypatch.setattr(recover, "LEDGER", output / "run-ledger.json")
    before = snapshot(output)

    result = recover.record_operator_verdict()

    assert result["action"] == "no_change"
    assert snapshot(output) == before


def test_record_operator_verdict_real_path_fails_closed_when_candidates_disagree(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    output = make_verdict_fixture(tmp_path, monkeypatch)
    assert recover.record_operator_verdict(output_root=output)["action"] == "reconciled"
    (output / "operator-acceptance.json").write_bytes(b"machine-local acceptance")
    monkeypatch.setattr(recover, "PULL", output)
    monkeypatch.setattr(recover, "PROVENANCE", output / "provenance")
    monkeypatch.setattr(recover, "LEDGER", output / "run-ledger.json")
    before = snapshot(output)

    with pytest.raises(ValueError, match="acceptance candidate records disagree"):
        recover.record_operator_verdict()

    assert snapshot(output) == before


@pytest.mark.parametrize("damage", ["media_bytes", "media_record", "acceptance_hash", "verdict_source", "missing_sidecar"])
def test_record_operator_verdict_fails_closed_without_partial_writes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, damage: str) -> None:
    output = make_verdict_fixture(tmp_path, monkeypatch)
    acceptance_path = output / "provenance/operator-acceptance.json"
    if damage == "media_bytes":
        (tmp_path / "assembled.mp4").write_bytes(b"changed after acceptance")
    elif damage == "media_record":
        final_path = output / "final-provenance.json"
        final = json.loads(final_path.read_text())
        final["final_media"]["sha256"] = "0" * 64
        recover.write_json(final_path, final)
    elif damage == "acceptance_hash":
        acceptance_path.write_text("{}\n")
    elif damage == "verdict_source":
        acceptance = json.loads(acceptance_path.read_text())
        acceptance["verdict_source"] = "inferred approval"
        acceptance_path.write_text(json.dumps(acceptance, indent=1) + "\n")
        monkeypatch.setattr(recover, "OPERATOR_ACCEPTANCE_SHA256", recover.sha(acceptance_path))
    else:
        (output / "operator_review_pending.json").unlink()
    before = snapshot(output)
    with pytest.raises((ValueError, FileNotFoundError)):
        recover.record_operator_verdict(acceptance_path, output)
    assert snapshot(output) == before
