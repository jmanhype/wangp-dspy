from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

from services.jobs.executor import JobExecutor
from services.jobs.queue import JobQueue
from services.jobs.spend_gate import (
    SpendGateRecordingFailure,
    SpendGateRecorder,
    write_live_row,
)


ROOT = Path(__file__).resolve().parents[1]
PROVENANCE = (
    ROOT
    / "datasets/runs/pull/lf004-operator-dogfood-56f-recovery-20260921"
    / "final-provenance.json"
)


def _lf004_evidence() -> list[tuple[dict, Path]]:
    document = json.loads(PROVENANCE.read_text(encoding="utf-8"))
    corpus = ROOT / "datasets/spend-gate/v1/corpus.jsonl"
    rows = {
        row["qc_evidence_sha256"]: row
        for row in (
            json.loads(line)
            for line in corpus.read_text(encoding="utf-8").splitlines()
        )
    }
    evidence: list[tuple[dict, Path]] = []
    for cut in document["cuts"]:
        row = rows[cut["qc_evidence_sha256"]]
        path = ROOT / row["source_path"] / "qc-evidence.json"
        assert path.is_file()
        evidence.append((cut, path))
    return evidence


def _unused_phase(message: str):
    def phase(_value):
        raise AssertionError(message)

    return phase


def _completed_qc(clip: dict) -> tuple[bool, str]:
    """Return the real recorded verdict and evidence path for a clip."""

    path = Path(clip["qc_evidence_path"])
    assert path.is_file()
    return True, str(path)


def _rendered_queue(
    database: Path, cuts: list[tuple[dict, Path]]
) -> tuple[JobQueue, str]:
    queue = JobQueue(database)
    clips = [
        {
            "clip_index": cut["clip_index"],
            "status": "pending",
            "log": str(path.parent / "render.log"),
            "mp4": str(path.parent / "remux.mp4"),
            "qc_verdict": None,
            "qc_evidence_path": str(path),
        }
        for cut, path in cuts
    ]
    job_id = queue.submit(plan_ref="lf004-recovery", clips=clips)
    queue.set_state(job_id, "preflight")
    queue.set_state(job_id, "rendering")
    record = queue.get(job_id)
    for clip in record.clips:
        clip["status"] = "rendered"
    queue.update_clips(job_id, record.clips)
    queue.set_state(job_id, "rendered_pending_qc")
    queue.set_state(job_id, "qc")
    return queue, job_id


def _executor(queue: JobQueue, recorder: SpendGateRecorder) -> JobExecutor:
    return JobExecutor(
        queue=queue,
        preflight=_unused_phase("preflight must not run"),
        render=_unused_phase("render must not run"),
        qc=_completed_qc,
        spend_gate_recorder=recorder,
    )


def _queue_outcome(queue: JobQueue, job_id: str) -> dict:
    record = queue.get(job_id)
    return {
        "state": record.state,
        "failure_count": record.failure_count,
        "failure_class": record.failure_class,
        "retryable": record.retryable,
        "dead_letter": queue.dead_letter_due(job_id, max_failures=3),
        "clip_order": tuple(clip["clip_index"] for clip in record.clips),
        "clip_states": tuple(clip["status"] for clip in record.clips),
    }


def test_recording_failure_is_typed_and_fail_open(tmp_path: Path) -> None:
    def failing_writer(*_args, **_kwargs) -> Path:
        raise OSError("recording filesystem unavailable")

    recorder = SpendGateRecorder(
        write_row=failing_writer, repository_root=tmp_path
    )
    evidence = tmp_path / "qc-evidence.json"

    recorder.record(evidence, job_id="job", clip_index=1)
    recorder.record(evidence, job_id="job", clip_index=1)

    assert recorder.failures == {
        SpendGateRecordingFailure.WRITE: 2
    }
    assert isinstance(recorder.last_error, OSError)


def test_services_layer_does_not_import_training() -> None:
    for path in (ROOT / "services").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                assert node.module != "training" and not (
                    node.module or "").startswith("training.")
            elif isinstance(node, ast.Import):
                assert all(not alias.name.startswith("training") for alias in node.names)


def test_production_qc_rows_match_standalone_lf004_recorder(
    tmp_path: Path,
) -> None:
    evidence = _lf004_evidence()
    assert len(evidence) == 4
    queue, job_id = _rendered_queue(tmp_path / "production.jobs.db", evidence)
    executor = _executor(queue, SpendGateRecorder(repository_root=ROOT))
    executor._qc_clips(queue.get(job_id))
    for cut, qc_path in evidence:
        production = qc_path.parent / "spend-gate-row.json"
        production_bytes = production.read_bytes()
        production_digest = hashlib.sha256(production_bytes).hexdigest()
        production.unlink()

        standalone = write_live_row(
            qc_path,
            repository_root=ROOT,
            job_id=job_id,
            clip_index=cut["clip_index"],
        )
        standalone_digest = hashlib.sha256(standalone.read_bytes()).hexdigest()
        standalone.unlink()

        assert standalone_digest == production_digest
        assert not list(qc_path.parent.glob("*.tmp-*"))


def test_forced_recording_failure_preserves_queue_and_retry_admission(
    tmp_path: Path,
) -> None:
    evidence = _lf004_evidence()[:2]
    baseline_queue, job_id = _rendered_queue(
        tmp_path / "baseline.jobs.db", evidence
    )
    _executor(baseline_queue, SpendGateRecorder(repository_root=ROOT))._qc_clips(
        baseline_queue.get(job_id)
    )
    baseline = _queue_outcome(baseline_queue, job_id)
    for _cut, path in evidence:
        (path.parent / "spend-gate-row.json").unlink()

    def forced_failure(*_args, **_kwargs) -> Path:
        raise OSError("forced spend-gate recording failure")

    failure_queue, failure_job_id = _rendered_queue(
        tmp_path / "failure.jobs.db", evidence
    )
    recorder = SpendGateRecorder(
        write_row=forced_failure, repository_root=ROOT
    )
    _executor(failure_queue, recorder)._qc_clips(
        failure_queue.get(failure_job_id)
    )

    assert _queue_outcome(failure_queue, failure_job_id) == baseline
    assert recorder.failures == {
        SpendGateRecordingFailure.WRITE: 2
    }
    assert isinstance(recorder.last_error, OSError)
    assert all(
        not (path.parent / "spend-gate-row.json").exists()
        for _cut, path in evidence
    )
