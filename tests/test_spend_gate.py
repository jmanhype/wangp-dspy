from __future__ import annotations

import io, json, os, shutil, subprocess, sys, tarfile
import hashlib
import sqlite3
from pathlib import Path

import pytest

from predict.content_brief import AUDIO_DURATION_TOLERANCE_S
from services.jobs.spend_gate import (SpendGateRecordingError, SpendGateSourceError, _canonicalize_paths, _gate,
                                 _canonical_stored_path, _is_path_field, _load_queue_rows, _queue_match, _queue_record_key, _row_identity,
                                 build_corpus, canonical_json, normalize_row, verify_artifact,
                                 write_completed_run_rows,
                                 write_live_row)
from training.spend_gate_replay import (_decision_rule, _deterministic_eval, _raw_probability_decision,
                                        _bootstrap, _score, _threshold_probability_decision, replay_baselines)

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
        comparable = _canonicalize_paths(expected, ROOT)
        assert all(row[key] == value for key, value in comparable.items()) and row["queue_join_status"] == "matched"
        assert row["qc_evidence_path"] == f"{row['source_path']}/qc-evidence.json"
    assert [row["queue"]["attempt_count"] for row in corpus.values() if row["run_group_id"].startswith("lf004")] == [2, 0, 0, 0]
    qc = Path(corpus[provenance["cuts"][0]["qc_evidence_sha256"]]["source_path"]) / "qc-evidence.json"
    live = json.loads(write_live_row(qc, repository_root=ROOT).read_text())
    live_expected = _canonicalize_paths(provenance["cuts"][0], ROOT)
    assert all(live[key] == value for key, value in live_expected.items()); (qc.parent / "spend-gate-row.json").unlink()
    missing = tmp_path / "missing" / "qc-evidence.json"
    with pytest.raises(SpendGateRecordingError):
        write_live_row(missing, repository_root=ROOT)
    assert not list(missing.parent.glob("*.tmp-*"))


def test_fresh_corpus_replay_is_deterministic_group_safe_and_honest(tmp_path: Path) -> None:
    checkout = tmp_path / "checkout"; checkout.mkdir()
    archive = subprocess.check_output(["git", "archive", "--format=tar", "HEAD"], cwd=ROOT)
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:*") as bundle:
        bundle.extractall(checkout, filter="data")
    for relative in ("training/spend_gate_replay.py", "scripts/build_spend_gate_corpus.py", "services/jobs/executor.py", "services/jobs/spend_gate.py"):
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
        recorded = json.loads(output.read_text())
        comparable = _canonicalize_paths(cut, ROOT)
        assert all(recorded[key] == value for key, value in comparable.items()); output.unlink()


def test_probability_polarity_admits_low_bad_risk_only() -> None:
    """P(bad) is a failure probability, so only a low value may admit."""

    report = replay_baselines(ARTIFACT / "corpus.jsonl", bootstrap_samples=20)
    probabilities = sorted(report.metrics["model_probability_rows"], key=lambda row: row["raw_probability"])
    low, high = probabilities[0], probabilities[-1]
    assert _raw_probability_decision(low["raw_probability"]) == "admit"
    assert _raw_probability_decision(high["raw_probability"]) == "reject"
    assert low["decision"] == "admit"
    assert high["decision"] != "admit"
    assert _threshold_probability_decision(0.1, 0.5) == "admit"
    assert _threshold_probability_decision(0.9, 0.5) == "reject"
    assert report.metrics["model_probability_definition"] == "P(bad)"
    assert report.metrics["decision_polarity"].startswith("admit iff P(bad) is below")


def test_queue_records_are_keyed_by_job_and_clip(tmp_path: Path) -> None:
    root = tmp_path / "repository"; datasets = root / "datasets"; datasets.mkdir(parents=True)
    subprocess.run(["git", "init", "."], cwd=root, check=True, capture_output=True, text=True)
    db_path = datasets / "two-clip.jobs.db"
    clips = [
        {"clip_index": 1, "render_fingerprint": "clip-1",
         "qc_verdict": {"path": str(root / "datasets/runs/acceptance/worker/render-0000/qc-evidence.json")}},
        {"clip_index": 2, "render_fingerprint": "clip-2",
         "qc_verdict": {"path": str(root / "datasets/runs/acceptance/worker/render-0001/qc-evidence.json")}},
    ]
    with sqlite3.connect(db_path) as db:
        db.execute("CREATE TABLE jobs (job_id TEXT PRIMARY KEY, state TEXT NOT NULL, plan_ref TEXT, clips TEXT NOT NULL, failure_count INTEGER NOT NULL, failure_class TEXT, failure_detail TEXT, created_at REAL NOT NULL, owner_pid INTEGER, last_heartbeat REAL, retryable INTEGER NOT NULL)")
        db.execute("CREATE TABLE job_attempts (attempt_id INTEGER PRIMARY KEY, job_id TEXT NOT NULL, attempt_no INTEGER NOT NULL, parent_attempt_id INTEGER, status TEXT NOT NULL, reopen_reason TEXT, attempt_reason TEXT, created_at REAL NOT NULL)")
        db.execute("INSERT INTO jobs VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                   ("job-two-clips", "completed", "plan", json.dumps(clips), 0, None, None, 1.0, None, None, 1))
    subprocess.run(["git", "add", str(db_path.relative_to(root))], cwd=root, check=True, capture_output=True, text=True)
    records = _load_queue_rows(root)
    assert set(records) == {_queue_record_key("job-two-clips", 1), _queue_record_key("job-two-clips", 2)}
    assert [record["render_fingerprint"] for record in records.values()] == ["clip-1", "clip-2"]
    _, second = _queue_match(records, root / "datasets/runs/acceptance/worker/render-0001", "job-two-clips", 2)
    assert second is not None and second["render_fingerprint"] == "clip-2"


def test_unknown_attempts_and_bootstrap_budget_are_not_fabricated() -> None:
    def row(identifier: str, group: str, bad: bool, attempts: int | None) -> dict:
        outcome = "fail" if bad else "pass"
        return {"row_id": identifier, "run_group_id": group,
                "gate_coverage": {name: {"outcome": outcome} for name in ("whisper_post", "vision", "av_sync")},
                "queue": None if attempts is None else {"attempt_count": attempts}}

    good, known_bad, unknown_bad = row("good", "a", False, 0), row("known", "b", True, 2), row("unknown", "c", True, None)
    decisions = {"good": "admit", "known": "reject", "unknown": "reject"}
    score = _score([good, known_bad, unknown_bad], decisions)
    assert score["failed_attempts_avoided"] == 3
    assert score["known_attempt_rejected_bad_rows"] == 1
    assert score["unknown_attempt_rejected_bad_rows_excluded"] == 1
    assert score["failed_attempts_avoided_per_run"] == 1.0
    duplicated_group = [good, known_bad, unknown_bad, good]
    assert _score(duplicated_group, {**decisions, "good": "admit"}, group_draws=4)["failed_attempts_avoided_per_run"] == 0.75
    mixed = [row("bad", "a", True, 0), row("good", "b", False, 0)]
    strict = _score(mixed, {"bad": "admit", "good": "admit"}, false_admit_budget=0.10)
    permissive = _score(mixed, {"bad": "admit", "good": "admit"}, false_admit_budget=0.50)
    assert strict["budget_met"] is False and permissive["budget_met"] is True
    bootstrap_rows = [row("a-bad", "a", True, 0), row("a-good", "a", False, 0),
                      row("b-bad", "b", True, 0), row("b-good", "b", False, 0)]
    admitted = {identifier: "admit" for identifier in ("a-bad", "a-good", "b-bad", "b-good")}
    assert _bootstrap(bootstrap_rows, admitted, 17, 10, 0.10) == []
    assert len(_bootstrap(bootstrap_rows, admitted, 17, 10, 0.50)) == 10


def test_preregistered_decision_requires_beating_both_baselines() -> None:
    def policy(lower: float, upper: float, feasible: bool = True) -> dict:
        return {"budget_met": feasible, "bootstrap_ci_2_5": lower, "bootstrap_ci_97_5": upper}

    baselines = {
        "always_admit": policy(0, 0, False),
        "deterministic_preflight": policy(1.0, 2.0),
        "transparent_heuristic": policy(1.5, 2.5),
        "calibrated_model": policy(1.2, 3.0),
    }
    assert _decision_rule(50, 10, 8, baselines)[0] == "not_warranted"
    baselines["calibrated_model"] = policy(3.0, 4.0)
    decision, evaluation = _decision_rule(50, 10, 8, baselines)
    assert decision == "warrant_future_training_story"
    assert evaluation["qualified_policies"] == ["calibrated_model"]
    assert all(value["beats"] for value in evaluation["comparisons"]["calibrated_model"].values())


def test_canonical_paths_do_not_participate_in_row_identity() -> None:
    def absolute_strings(value):
        if isinstance(value, dict): return [item for child in value.values() for item in absolute_strings(child)]
        if isinstance(value, list): return [item for child in value for item in absolute_strings(child)]
        return [value] if isinstance(value, str) and value.startswith("/") else []

    assert absolute_strings(rows()) == []
    source = rows()[0]
    variant = json.loads(json.dumps(source))
    variant["qc_evidence_path"] = "/tmp/another-checkout/qc-evidence.json"
    variant["source_path"] = "another/checkout"
    variant["preflight"]["plate_path"] = "/tmp/another-plate.png"
    variant["preflight"]["plate_available"] = not source["preflight"]["plate_available"]
    variant["source_git_available"] = {key: not value for key, value in source["source_git_available"].items()}
    assert canonical_json(_row_identity(variant)) == canonical_json(_row_identity(source))
    variant["qc_evidence_sha256"] = "0" * 64
    assert canonical_json(_row_identity(variant)) != canonical_json(_row_identity(source))
    canonical = _canonicalize_paths({
        "qc_evidence_path": "/tmp/other-root/datasets/runs/a/qc-evidence.json",
        "media": {"path": "/tmp/other-root/datasets/runs/a/remux.mp4"},
        "external_path": "/tmp/renderer-host/render/remux.mp4",
    }, ROOT)
    assert canonical == {"qc_evidence_path": "datasets/runs/a/qc-evidence.json",
                         "media": {"path": "datasets/runs/a/remux.mp4"},
                        "external_path": "external/remux.mp4"}


def test_historical_nested_worktree_paths_are_checkout_independent() -> None:
    recorded = Path("/Users/Shared/HermesWorkspace/wangp-dspy/.claude/worktrees/dev-WD-g125/datasets/runs/pull/acceptance/worker-511ee9ee6a8f/render-0000/qc-evidence.json")
    main_root = ROOT.parents[2]
    roots = (main_root, main_root / ".claude/worktrees/dev-WD-g125", Path("/tmp/not-this-repository"))
    expected = "datasets/runs/pull/acceptance/worker-511ee9ee6a8f/render-0000/qc-evidence.json"
    assert {_canonical_stored_path(recorded.as_posix(), root.resolve()) for root in roots} == {expected}

    def path_fields(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if _is_path_field(key) and isinstance(item, str): yield item
                yield from path_fields(item)
        elif isinstance(value, list):
            for item in value: yield from path_fields(item)

    canonical_cuts = _canonicalize_paths(json.loads(LF004.read_text())["cuts"], main_root)
    cut_paths = list(path_fields(canonical_cuts))
    corpus_paths = [path for row in rows() for path in path_fields(row)]
    assert cut_paths and corpus_paths
    assert all(".claude" not in Path(path).parts for path in [*cut_paths, *corpus_paths])


def test_verify_artifact_checks_drift_digest_and_declared_row_count(tmp_path: Path) -> None:
    artifact = tmp_path / "artifact"; shutil.copytree(ARTIFACT, artifact)
    (artifact / "schema-drift.json").write_text('{"tampered":true}\n', encoding="utf-8")
    with pytest.raises(SpendGateSourceError, match="schema-drift SHA-256"):
        verify_artifact(artifact)
    shutil.rmtree(artifact); shutil.copytree(ARTIFACT, artifact)
    manifest_path = artifact / "manifest.json"; manifest = json.loads(manifest_path.read_text())
    manifest.pop("manifest_sha256"); manifest["row_count"] = 35
    manifest["manifest_sha256"] = hashlib.sha256(canonical_json(manifest).encode()).hexdigest()
    manifest_path.write_text(canonical_json(manifest), encoding="utf-8")
    with pytest.raises(SpendGateSourceError, match="row count"):
        verify_artifact(artifact)


def rows_by_hash() -> dict[str, dict]:
    return {row["qc_evidence_sha256"]: row for row in rows()}


def test_unknown_preflight_feature_never_becomes_zero(tmp_path: Path) -> None:
    changed, path = [dict(row, preflight=dict(row["preflight"], guide_duration_s=None)) for row in rows()], tmp_path / "corpus.jsonl"
    path.write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in changed)); report = replay_baselines(path, bootstrap_samples=20)
    assert report.metrics["baselines"]["deterministic_preflight"]["abstained"] == 18 and report.metrics["recording_errors"]


def test_deterministic_preflight_rejection_is_attributed_not_hidden() -> None:
    """The measured-vs-declared comparison must use the production tolerance.

    A 1e-9 comparison flags every ffprobe-rounded guide against its declared
    shot duration, which silently turned this baseline into reject-everything.
    """
    report = replay_baselines(ARTIFACT / "corpus.jsonl", bootstrap_samples=20)
    baseline, complete = report.metrics["baselines"]["deterministic_preflight"], report.metrics["complete_row_count"]
    assert baseline["admitted"] == complete and baseline["abstained"] == 0
    assert baseline["rejected_bad"] == baseline["rejected_good"] == 0
    assert report.metrics["deterministic_preflight_reasons"] == {}
    rounding_gap = [row for row in rows()
                    if abs(float(row["preflight"]["guide_duration_s"])
                           - float(row["preflight"]["declared_shot_duration_s"])) > AUDIO_DURATION_TOLERANCE_S]
    assert rounding_gap == []
    assert "typed resolution_transform" in report.markdown
    assert "not tracked by git" in report.markdown


def test_resolution_request_is_typed_against_reference_geometry() -> None:
    """A renderer request is not implicitly a delivered-media contract.

    The H3 request remains 480x832, while the recorded handler maps reference
    conditioning to a 704x576 output grid. The replay must admit that typed
    transform, abstain when the transform is unavailable, and still reject a
    delivered geometry that contradicts the typed contract.
    """
    source = next(row for row in rows() if row["source_path"] ==
                  "datasets/runs/pull/acceptance/worker-511ee9ee6a8f/render-0000")
    normalized = normalize_row(ROOT / source["source_path"], repository_root=ROOT).to_dict()
    transform = normalized["preflight"]["resolution_transform"]
    assert normalized["preflight"]["resolution_semantics"] == "renderer_request"
    assert transform["kind"] == "wgp_h3_reference_output_resize"
    assert transform["renderer_handler_sha256"] == (
        "e5c470257bac14f49aa2d5dba2feb257d838efababa0a2e387227fedf4765ae6")
    assert (transform["request_width"], transform["request_height"]) == (480, 832)
    assert (transform["reference_width"], transform["reference_height"]) == (704, 576)
    assert (transform["expected_delivered_width"], transform["expected_delivered_height"]) == (704, 576)
    assert _deterministic_eval(normalized) == ("admit", None)

    contradiction = json.loads(json.dumps(normalized))
    video = next(stream for stream in contradiction["media"]["ffprobe"]["streams"]
                 if stream.get("codec_type") == "video")
    video["width"], video["height"] = 640, 480
    assert _deterministic_eval(contradiction) == (
        "reject", "delivered_resolution_contradicts_typed_envelope")

    unknown = json.loads(json.dumps(normalized))
    unknown["preflight"].pop("resolution_transform")
    assert _deterministic_eval(unknown) == ("abstain", "unknown_resolution_transform")


def test_tracked_build_requires_a_git_worktree(tmp_path: Path) -> None:
    with pytest.raises(SpendGateSourceError) as error:
        build_corpus(tmp_path, evidence_mode="tracked")
    assert "requires a git working tree" in str(error.value)


def test_missing_facing_sidecar_still_reaches_admit() -> None:
    """Production falls back to the declared facing requirement without a sidecar.

    The real corpus rows already carry their typed resolution transform. Keep
    the delivered geometry consistent with it so this reaches the facing check.
    """
    source = next(row for row in rows()
                  if row["preflight"].get("plate_available") and row["preflight"]["plate_facing"] is None)
    row = json.loads(json.dumps(source))
    video = next(stream for stream in row["media"]["ffprobe"]["streams"] if stream["codec_type"] == "video")
    transform = row["preflight"]["resolution_transform"]
    video["width"], video["height"] = (
        transform["expected_delivered_width"], transform["expected_delivered_height"])
    video["nb_frames"] = row["preflight"]["requested_frames"]
    assert _deterministic_eval(row) == ("admit", None)
    row["preflight"]["plate_facing"] = "profile"
    assert _deterministic_eval(row) == ("reject", "plate_not_camera_facing")


def test_clipped_probability_disclosure_is_protected() -> None:
    report = replay_baselines(ARTIFACT / "corpus.jsonl", bootstrap_samples=20)
    raw, calibrated = report.metrics["raw_probability_policy"], report.metrics["calibrated_probability_policy"]
    assert raw["log_loss_clip"] == 1e-15 and calibrated["log_loss_clip"] == 1e-15
    assert raw["clipped_probability_rows"] == report.metrics["complete_row_count"]
    assert calibrated["clipped_probability_rows"] == 0
    assert raw["log_loss"] > 5.0
    assert "Clipped probability rows" in report.markdown


def test_live_row_replacement_is_atomic_and_leaves_no_temporary() -> None:
    """Replacement must be atomic and content-bound, not environment-dependent.

    row_id folds in source-git availability, which legitimately differs between
    this evidence checkout and a fresh clone, so equality is asserted on
    content-derived fields instead of the whole row.
    """
    cut = json.loads(LF004.read_text())["cuts"][0]
    row = next(item for item in rows() if item["qc_evidence_sha256"] == cut["qc_evidence_sha256"])
    qc = Path(row["source_path"]) / "qc-evidence.json"
    target = qc.parent / "spend-gate-row.json"
    assert qc.is_file()
    first, first_bytes = write_live_row(qc, repository_root=ROOT), None
    first_bytes = first.read_bytes()
    assert write_live_row(qc, repository_root=ROOT).read_bytes() == first_bytes
    payload = json.loads(first.read_text())
    assert payload["qc_evidence_sha256"] == row["qc_evidence_sha256"]
    assert payload["clip_index"] == row["clip_index"] and payload["source_path"] == row["source_path"]
    assert not list(qc.parent.glob("*.tmp-*"))
    target.unlink()
