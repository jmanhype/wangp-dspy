from __future__ import annotations

import io, json, os, shutil, subprocess, sys, tarfile
from pathlib import Path

import pytest

from training.spend_gate import SpendGateRecordingError, _gate, build_corpus, write_completed_run_rows, write_live_row
from training.spend_gate_replay import replay_baselines

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "datasets/spend-gate/v1"
LF004 = ROOT / "datasets/runs/pull/lf004-operator-dogfood-56f-recovery-20260921/final-provenance.json"


def rows() -> list[dict]:
    return [json.loads(line) for line in (ARTIFACT / "corpus.jsonl").read_text().splitlines()]


def test_committed_counts_null_and_execution_error_semantics() -> None:
    manifest, values = json.loads((ARTIFACT / "manifest.json").read_text()), rows()
    assert manifest["row_count"] == 36
    assert manifest["gate_counts"] == {"whisper_pre_pass": 36, "whisper_pre_fail": 0, "whisper_post_pass": 27, "whisper_post_fail": 9, "vision_pass": 25, "vision_fail": 0, "av_sync_pass": 13, "av_sync_fail": 5, "complete_rows": 18, "complete_bad_rows": 5}
    assert sum(row["gate_coverage"]["av_sync"]["failure_class"] == "null_value" for row in values) == 4
    assert sum(row["gate_coverage"]["av_sync"]["failure_class"] == "execution_error" for row in values) == 1
    assert len(manifest["queue_sources"]) == 5 and all(source["git_tracked"] and len(source["sha256"]) == 64 for source in manifest["queue_sources"])
    assert all(row["gate_coverage"][gate]["outcome"] is None for row in values for gate in row["gate_coverage"] if not row["gate_coverage"][gate]["usable"])
    assert _gate({"gate": {"passed": "not-boolean"}}, "gate")["failure_class"] == "malformed"


def test_full_local_build_and_deterministic_identity() -> None:
    local, required = list((ROOT / "datasets/runs").glob("**/qc-evidence.json")), {"qc-evidence.json", "settings.json", "wgp-settings.json", "runtime-evidence.json", "speaker_manifest.json", "conditioning-evidence.json", "audio_manifest.json", "render.log", "raw.mp4", "remux.mp4"}
    if len(local) == 36:
        first, second = build_corpus(ROOT, evidence_mode="all-local"), build_corpus(ROOT, evidence_mode="all-local")
        assert len(first.rows) == len(second.rows) == 36 and [row.to_dict()["row_id"] for row in first.rows] == [row.to_dict()["row_id"] for row in second.rows]
        assert all(required <= {item.name for item in path.parent.iterdir()} for path in local)
        availability = [row.to_dict()["source_git_available"] for row in first.rows]
        assert sum(not item["qc-evidence.json"] for item in availability) == 15 and sum(not all(item.values()) for item in availability) == 16
    else:
        assert len(local) == 21 and len(rows()) == 36


def test_lf004_parity_queue_join_and_live_atomic_recorder(tmp_path: Path) -> None:
    provenance = json.loads(LF004.read_text())
    corpus = {row["qc_evidence_sha256"]: row for row in rows()}
    for expected in provenance["cuts"]:
        row = corpus[expected["qc_evidence_sha256"]]
        assert all(row[key] == expected[key] for key in expected) and row["queue_join_status"] == "matched"
    assert [row["queue"]["attempt_count"] for row in corpus.values() if row["run_group_id"].startswith("lf004")] == [2, 0, 0, 0]
    qc = Path(corpus[provenance["cuts"][0]["qc_evidence_sha256"]]["source_path"]) / "qc-evidence.json"
    live = json.loads(write_live_row(qc, repository_root=ROOT).read_text()); assert all(live[key] == value for key, value in provenance["cuts"][0].items()); (qc.parent / "spend-gate-row.json").unlink()
    missing = tmp_path / "missing" / "qc-evidence.json"
    with pytest.raises(SpendGateRecordingError):
        write_live_row(missing, repository_root=ROOT)
    assert not list(missing.parent.glob("*.tmp-*"))


def test_fresh_corpus_replay_is_deterministic_group_safe_and_honest(tmp_path: Path) -> None:
    checkout = tmp_path / "checkout"; checkout.mkdir()
    archive = subprocess.check_output(["git", "archive", "--format=tar", "HEAD"], cwd=ROOT)
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:*") as bundle:
        bundle.extractall(checkout)
    for relative in ("training/spend_gate.py", "training/spend_gate_replay.py", "scripts/build_spend_gate_corpus.py", "services/jobs/executor.py"):
        shutil.copyfile(ROOT / relative, checkout / relative)
    shutil.copytree(ARTIFACT, checkout / ARTIFACT.relative_to(ROOT), dirs_exist_ok=True)
    command = [sys.executable, "scripts/build_spend_gate_corpus.py", "--repository-root", ".", "--evidence-mode", "tracked", "--output-dir", "datasets/spend-gate/v1", "--replay", "--verify-artifact"]
    environment = {**os.environ, "PYTHONPATH": str(checkout)}
    first_run = subprocess.run(command, cwd=checkout, env=environment, check=True, capture_output=True, text=True)
    metrics_path, first_bytes = checkout / "datasets/spend-gate/v1/replay-metrics.json", None
    first_bytes = metrics_path.read_bytes()
    subprocess.run(command, cwd=checkout, env=environment, check=True, capture_output=True, text=True)
    assert metrics_path.read_bytes() == first_bytes and b"rows=36" in first_run.stdout.encode()
    metrics = json.loads(metrics_path.read_text())
    assert (metrics["row_count"], metrics["complete_row_count"], metrics["bad_complete_rows"]) == (36, 18, 5)
    assert metrics["decision"] == "insufficient_data" and metrics["primary_result"] == "infeasible_at_budget"
    assert len(metrics["grouped_folds"]) == len(metrics["run_groups"]) and all(fold["held_out_run_group"] in metrics["run_groups"] for fold in metrics["grouped_folds"])
    assert all(not set(fold["training_row_ids"]) & set(fold["held_out_row_ids"]) for fold in metrics["grouped_folds"])
    assert "post" not in " ".join(metrics["preflight_feature_names"])
    assert len(metrics["model_probability_rows"]) == 18 and set(metrics["baselines"]) == {"always_admit", "deterministic_preflight", "transparent_heuristic", "calibrated_model"}
    assert metrics["raw_probability_policy"]["confidence_bins"] and metrics["calibrated_probability_policy"]["confidence_bins"]
    assert "underpowered" in (checkout / "datasets/spend-gate/v1/replay-report.md").read_text()


def test_post_run_recorder_reproduces_all_lf004_rows() -> None:
    provenance, expected = json.loads(LF004.read_text()), json.loads(LF004.read_text())["cuts"]
    outputs = write_completed_run_rows("lf004-operator-dogfood-56f-recovery-20260921", ROOT)
    assert len(outputs) == 4
    for output, cut in zip(outputs, expected, strict=True):
        recorded = json.loads(output.read_text()); assert all(recorded[key] == value for key, value in cut.items()); output.unlink()


def rows_by_hash() -> dict[str, dict]:
    return {row["qc_evidence_sha256"]: row for row in rows()}


def test_unknown_preflight_feature_never_becomes_zero(tmp_path: Path) -> None:
    changed, path = [dict(row, preflight=dict(row["preflight"], guide_duration_s=None)) for row in rows()], tmp_path / "corpus.jsonl"
    path.write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in changed)); report = replay_baselines(path, bootstrap_samples=20)
    assert report.metrics["baselines"]["deterministic_preflight"]["abstained"] == 18 and report.metrics["recording_errors"]
