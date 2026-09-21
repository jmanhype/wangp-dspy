"""Offline normalization of recorded render outcomes into spend-gate rows."""
from __future__ import annotations

import hashlib, json, os, sqlite3, subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Mapping

from predict.content_brief import load_content_brief
from services.director.run_ledger import repository_identity

ROW_SCHEMA = "wangp-dspy.spend-gate-row/v1"
SIDEARS = ("qc-evidence.json", "settings.json", "wgp-settings.json", "runtime-evidence.json", "speaker_manifest.json", "conditioning-evidence.json", "audio_manifest.json", "render.log", "raw.mp4", "remux.mp4")


class SpendGateSourceError(ValueError):
    """A source artifact is malformed, unreadable, or not hashable."""


class SpendGateRecordingError(RuntimeError):
    """The post-QC recorder could not persist its row."""


@dataclass(frozen=True)
class SpendGateRow:
    """One manifest-addressed render outcome; ``payload`` is canonical."""

    payload: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return dict(self.payload)


@dataclass(frozen=True)
class SpendGateCorpus:
    """Deterministic rows plus read-only queue and repository attribution."""

    rows: tuple[SpendGateRow, ...]
    evidence_mode: Literal["tracked", "all-local"]
    queue_rows: dict[str, dict[str, Any]]
    repository: dict[str, Any]


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False) + "\n"


def _hash_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _hash_file(path: Path) -> str:
    try:
        return _hash_bytes(path.read_bytes())
    except OSError as exc:
        raise SpendGateSourceError(f"cannot hash {path}: {exc}") from exc


def _json(path: Path, *, required: bool = True) -> Any:
    if not path.exists():
        if required: raise SpendGateSourceError(f"missing source: {path}")
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise SpendGateSourceError(f"malformed JSON {path}: {exc}") from exc


def _tracked(repository_root: Path, relative: Path) -> bool:
    result = subprocess.run(["git", "ls-files", "--", relative.as_posix()], cwd=repository_root, check=True, text=True, capture_output=True)
    return bool(result.stdout.strip())


def _ffprobe(path: Path) -> dict[str, Any]:
    result = subprocess.run(["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)], text=True, capture_output=True, check=False, timeout=15)
    if result.returncode:
        raise SpendGateSourceError(f"ffprobe failed for {path}: {result.stderr.strip()}")
    try:
        value = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise SpendGateSourceError(f"ffprobe returned malformed JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise SpendGateSourceError(f"ffprobe returned non-object for {path}")
    return value


def _gate(qc: Mapping[str, Any], key: str) -> dict[str, Any]:
    def coverage(declared: bool, recorded: bool, usable: bool, outcome: str | None, failure: str | None) -> dict[str, Any]:
        return {"declared": declared, "evidence_recorded": recorded, "usable": usable, "outcome": outcome, "failure_class": failure}
    value = qc.get(key)
    if key not in qc:
        return coverage(False, False, False, None, "undeclared")
    if value is None:
        return coverage(True, False, False, None, "null_value")
    if isinstance(value, dict) and value.get("status") == "failed":
        return coverage(True, True, False, None, "execution_error")
    passed = value.get("passed") if isinstance(value, dict) else None
    if isinstance(passed, bool):
        return coverage(True, True, True, "pass" if passed else "fail", None)
    return coverage(True, True, False, None, "malformed")


def _lf004_reference(repository_root: Path, qc_hash: str) -> dict[str, Any] | None:
    provenance = repository_root / "datasets/runs/pull/lf004-operator-dogfood-56f-recovery-20260921/final-provenance.json"
    document = _json(provenance, required=False)
    for cut in document.get("cuts", []) if isinstance(document, dict) else []:
        if isinstance(cut, dict) and cut.get("qc_evidence_sha256") == qc_hash:
            return cut
    return None


def _queue_match(queue_rows: Mapping[str, Mapping[str, Any]] | None, render_dir: Path, job_id: str | None, clip_index: int | None) -> tuple[str | None, Mapping[str, Any] | None]:
    if job_id and queue_rows and job_id in queue_rows:
        return job_id, queue_rows[job_id]
    for candidate, row in sorted((queue_rows or {}).items()):
        if (row.get("clip_index") == clip_index and row.get("render_dir") == render_dir.name
                and row.get("render_parent") == render_dir.parent.name):
            return candidate, row
    return None, None


def normalize_row(render_dir: Path, *, repository_root: Path,
                  queue_rows: Mapping[str, Mapping[str, object]] | None = None, job_id: str | None = None, clip_index: int | None = None) -> SpendGateRow:
    """Normalize one render directory without changing any gate verdict."""
    render_dir = render_dir.resolve()
    repository_root = repository_root.resolve()
    relative_dir = render_dir.relative_to(repository_root)
    qc_path = render_dir / "qc-evidence.json"
    qc = _json(qc_path)
    if not isinstance(qc, dict):
        raise SpendGateSourceError(f"QC evidence must be an object: {qc_path}")
    qc_hash = _hash_file(qc_path)
    settings, wgp = _json(render_dir / "settings.json", required=False) or {}, _json(render_dir / "wgp-settings.json", required=False) or {}
    conditioning, speaker_doc = _json(render_dir / "conditioning-evidence.json", required=False) or {}, _json(render_dir / "speaker_manifest.json", required=False) or {}
    if not isinstance(settings, dict) or not isinstance(wgp, dict): raise SpendGateSourceError(f"settings must be objects in {render_dir}")
    turns = speaker_doc.get("turns", []) if isinstance(speaker_doc, dict) else []
    turn = turns[0] if turns and isinstance(turns[0], dict) else {}
    index = clip_index or int(render_dir.name.split("-")[-1]) + 1
    whisper_doc = qc.get("whisper_gates") if isinstance(qc.get("whisper_gates"), dict) else {}
    whisper_pre = _gate(whisper_doc, "pre")
    whisper_post = _gate(whisper_doc, "post")
    gates = {"whisper_pre": None if not whisper_pre["usable"] else whisper_pre["outcome"] == "pass", "whisper_post": None if not whisper_post["usable"] else whisper_post["outcome"] == "pass"}
    vision_gate = _gate(qc, "vision_judge")
    av_gate = _gate(qc, "av_sync_gate")
    gates.update({"vision_identity_composition": None if not vision_gate["usable"] else vision_gate["outcome"] == "pass", "syncnet_av": None if not av_gate["usable"] else av_gate["outcome"] == "pass"})
    matched_id, queue = _queue_match(queue_rows, render_dir, job_id, index)
    brief_path = repository_root / "datasets/content_briefs/lf004-operator-dogfood/brief.json"
    try:
        brief_hash = load_content_brief(brief_path).brief_hash if brief_path.exists() else None
    except Exception:
        brief_hash = None
    prompt = str(wgp.get("prompt") or settings.get("prompt") or "")
    plate_path = str(settings.get("image_start") or wgp.get("image_start") or "")
    plate_sidecar = Path(str(plate_path).rsplit(".", 1)[0] + ".plate.json") if plate_path else None
    plate_json = _json(plate_sidecar, required=False) if plate_sidecar else None
    resolution = str(wgp.get("resolution") or settings.get("resolution") or "")
    dimensions = [int(value) for value in resolution.split("x")] if "x" in resolution else []
    width, height = (dimensions + [None, None])[:2]
    source_hashes = {name: _hash_file(render_dir / name) for name in SIDEARS}
    availability = {name: _tracked(repository_root, relative_dir / name) for name in SIDEARS}
    media = {"path": (relative_dir / "remux.mp4").as_posix(), "sha256": source_hashes["remux.mp4"], "ffprobe": _ffprobe(render_dir / "remux.mp4")}
    row: dict[str, Any] = {
        "schema": ROW_SCHEMA, "run_group_id": str(queue.get("plan_ref") if queue and queue.get("plan_ref") else f"legacy-repo-{conditioning.get('repo_sha', 'unknown')}"),
        "clip_index": index, "job_id": matched_id, "dialogue": turn.get("intended_text"),
        "speaker": turn.get("speaker_id"), "seed": wgp.get("seed", settings.get("seed")),
        "render_fingerprint": (queue or {}).get("render_fingerprint") or conditioning.get("wire_settings_sha256"),
        "qc_evidence_path": qc_path.as_posix(), "qc_evidence_sha256": qc_hash,
        "gates": gates, "whisper": qc.get("whisper_gates"), "vision": qc.get("vision_judge"),
        "av_sync": qc.get("av_sync_gate"), "media": media,
        "gate_coverage": {"whisper_pre": whisper_pre, "whisper_post": whisper_post, "vision": vision_gate, "av_sync": av_gate},
        "failure_classes": {k: v["failure_class"] for k, v in (("vision", vision_gate), ("av_sync", av_gate))},
        "preflight": {"audio_carrier": settings.get("audio_carrier"), "model_type": wgp.get("model_type"), "guide_duration_s": settings.get("guide_duration_s"), "declared_shot_duration_s": conditioning.get("cut_duration_s"), "requested_frames": settings.get("requested_frames", settings.get("video_length")), "fps": settings.get("force_fps"), "resolution": resolution, "width": width, "height": height, "prompt_sha256": _hash_bytes(prompt.encode()), "prompt_chars": len(prompt), "prompt_words": len(prompt.split()), "plate_path": plate_path, "plate_available": bool(plate_path and Path(plate_path).is_file()), "plate_facing": plate_json.get("facing") if isinstance(plate_json, dict) else None, "whisper_pre_passed": gates["whisper_pre"]},
        "plan": {"brief_hash": brief_hash, "wire_settings_sha256": conditioning.get("wire_settings_sha256"), "repo_sha": conditioning.get("repo_sha"), "mode": settings.get("audio_carrier")},
        "queue_join_status": "matched" if queue else "unavailable",
        "queue": None if not queue else {k: queue.get(k) for k in ("job_id", "state", "failure_count", "failure_class", "attempt_count", "last_failure")},
        "source_hashes": source_hashes, "source_git_available": availability, "source_path": relative_dir.as_posix(),
    }
    reference = _lf004_reference(repository_root, qc_hash)
    if reference is not None:
        for key in ("av_sync", "clip_index", "dialogue", "gates", "job_id", "media", "qc_evidence_path", "qc_evidence_sha256", "render_fingerprint", "seed", "speaker", "vision", "whisper"):
            row[key] = reference.get(key)
        reference_queue = queue_rows.get(str(reference.get("job_id"))) if queue_rows else None
        if reference_queue:
            row["queue_join_status"] = "matched"; row["queue"] = {k: reference_queue.get(k) for k in ("job_id", "state", "failure_count", "failure_class", "attempt_count", "last_failure")}
        row["run_group_id"] = "lf004-operator-dogfood-56f-recovery-20260921"
    row["row_id"] = f"sg-{_hash_bytes(canonical_json(row).encode())}"; return SpendGateRow(row)


def _load_queue_rows(repository_root: Path) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for db_path in sorted((repository_root / "datasets").glob("*.jobs.db")):
        relative = db_path.relative_to(repository_root)
        if not _tracked(repository_root, relative): continue
        uri = f"file:{db_path}?mode=ro"
        with sqlite3.connect(uri, uri=True) as db:
            db.row_factory = sqlite3.Row
            jobs = {row["job_id"]: dict(row) for row in db.execute("SELECT * FROM jobs")}
            attempts = {job_id: [dict(row) for row in db.execute("SELECT * FROM job_attempts WHERE job_id=? ORDER BY attempt_no", (job_id,))] for job_id in jobs}
        for job_id, job in jobs.items():
            clips = json.loads(job["clips"]); clip = clips[0] if clips else {}
            qc_value = clip.get("qc_verdict")
            qc_path = qc_value.get("path") if isinstance(qc_value, dict) else None
            history = attempts.get(job_id, [])
            rows[job_id] = {"job_id": job_id, "state": job["state"], "failure_count": job["failure_count"], "failure_class": job["failure_class"], "attempt_count": len(history), "last_failure": history[-1] if history else None, "plan_ref": job["plan_ref"], "clip_index": clip.get("clip_index"), "render_fingerprint": clip.get("render_fingerprint"), "render_dir": Path(qc_path).parent.name if qc_path else None, "render_parent": Path(qc_path).parent.parent.name if qc_path else None, "queue_db_path": relative.as_posix(), "queue_db_sha256": _hash_file(db_path)}
    return rows


def build_corpus(repository_root: Path, *, evidence_mode: Literal["tracked", "all-local"] = "tracked") -> SpendGateCorpus:
    """Build rows from tracked evidence, or all local evidence when explicit."""
    repository_root = repository_root.resolve()
    paths = sorted((repository_root / "datasets/runs").glob("**/qc-evidence.json"))
    if evidence_mode == "tracked":
        tracked = {Path(line) for line in subprocess.check_output(["git", "ls-files", "--", "datasets/runs"], cwd=repository_root, text=True).splitlines()}
        paths = [path for path in paths if path.relative_to(repository_root) in tracked]
    queue_rows = _load_queue_rows(repository_root)
    rows = [normalize_row(path.parent, repository_root=repository_root, queue_rows=queue_rows) for path in paths]
    if any(coverage["failure_class"] == "malformed" for row in rows for coverage in row.to_dict()["gate_coverage"].values()): raise SpendGateSourceError("malformed gate evidence")
    return SpendGateCorpus(tuple(rows), evidence_mode, queue_rows, repository_identity(repository_root))


def schema_drift(corpus: SpendGateCorpus) -> dict[str, Any]:
    groups: dict[str, dict[str, Any]] = {}
    for row in corpus.rows:
        value = row.to_dict()
        group = groups.setdefault(value["run_group_id"], {"rows": 0, "declared": {}, "usable": {}, "outcomes": {}})
        group["rows"] += 1
        for gate, coverage in value["gate_coverage"].items():
            for field in ("declared", "usable"):
                group[field][gate] = group[field].get(gate, 0) + int(bool(coverage[field]))
            outcome = coverage["outcome"]
            key = f"{gate}:{outcome or coverage['failure_class']}"
            group["outcomes"][key] = group["outcomes"].get(key, 0) + 1
    return {"schema": "wangp-dspy.spend-gate-drift/v1", "run_groups": dict(sorted(groups.items()))}


def _atomic(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + f".tmp-{os.getpid()}")
    temporary.write_text(text, encoding="utf-8"); os.replace(temporary, path)
    return path


def write_corpus(corpus: SpendGateCorpus, output_dir: Path) -> Path:
    """Write canonical corpus, drift, preregistration, and manifest artifacts."""
    output_dir.mkdir(parents=True, exist_ok=True)
    repository_root = Path(corpus.repository["repo_root"])
    corpus_path, payload = output_dir / "corpus.jsonl", "".join(canonical_json(row.to_dict()) for row in corpus.rows)
    _atomic(corpus_path, payload)
    drift = schema_drift(corpus)
    _atomic(output_dir / "schema-drift.json", canonical_json(drift))
    prereg = {"schema": "wangp-dspy.spend-gate-prereg/v1", "label": "bad iff whisper_post, vision, or av_sync usable outcome is fail",
        "group_key": "run_group_id", "folds": "sorted leave-one-run-group-out", "seed": 17,
        "bootstrap_samples": 2000, "false_admit_budget": 0.10, "calibrated_confidence_threshold": 0.70,
        "transparent_heuristic": "admit only when native_h3, guide duration equals 56/24 within 1e-9, and prompt length is at least 500 characters",
        "primary_metric": "mean failed-render-attempts avoided per production run at false-admit <= 0.10",
        "decision_rule": ["insufficient_data if complete<50 or bad<10 or groups<8", "not_warranted if no feasible policy or CI does not beat both baselines", "warrant_future_training_story otherwise"]}
    _atomic(output_dir / "preregistration.json", canonical_json(prereg))
    manifest = {"schema": "wangp-dspy.spend-gate-manifest/v1", "row_count": len(corpus.rows), "evidence_mode": corpus.evidence_mode, "corpus_sha256": _hash_bytes(payload.encode()), "schema_drift_sha256": _hash_bytes(canonical_json(drift).encode()), "repository": {k: corpus.repository[k] for k in ("repo_root", "commit_sha", "dirty_tree")},
        "queue_sources": sorted({row["queue_db_path"]: {"path": row["queue_db_path"], "sha256": row["queue_db_sha256"], "git_tracked": _tracked(repository_root, Path(row["queue_db_path"]))} for row in corpus.queue_rows.values()}.values(), key=lambda item: item["path"]),
        "gate_counts": _gate_counts(corpus)}
    manifest["manifest_sha256"] = _hash_bytes(canonical_json(manifest).encode())
    return _atomic(output_dir / "manifest.json", canonical_json(manifest))


def _gate_counts(corpus: SpendGateCorpus) -> dict[str, Any]:
    counts: dict[str, Any] = {f"{gate}_{outcome}": 0 for gate in ("whisper_pre", "whisper_post", "vision", "av_sync") for outcome in ("pass", "fail")}
    complete = bad = 0
    for row in corpus.rows:
        coverages, usable, failed = row.to_dict()["gate_coverage"], True, False
        for gate in counts:
            gate_name, outcome = gate.rsplit("_", 1)
            coverage = coverages[gate_name]
            if coverage["usable"]:
                counts[gate] += coverage["outcome"] == outcome
                failed |= gate_name != "whisper_pre" and coverage["outcome"] == "fail"
            usable &= coverage["usable"]
        complete += usable
        bad += usable and failed
    counts.update(complete_rows=complete, complete_bad_rows=bad)
    return counts


def verify_artifact(output_dir: Path) -> dict[str, Any]:
    manifest = _json(output_dir / "manifest.json")
    if not isinstance(manifest, dict): raise SpendGateSourceError("manifest must be an object")
    corpus = (output_dir / "corpus.jsonl").read_text(encoding="utf-8")
    expected = manifest.get("corpus_sha256")
    if expected != _hash_bytes(corpus.encode()): raise SpendGateSourceError("corpus SHA-256 does not match manifest")
    recorded = manifest.pop("manifest_sha256", None)
    if recorded != _hash_bytes(canonical_json(manifest).encode()):
        raise SpendGateSourceError("manifest SHA-256 does not match payload")
    return manifest


def write_live_row(qc_evidence_path: Path, *, repository_root: Path,
                   queue_rows: Mapping[str, Mapping[str, object]] | None = None,
                   job_id: str | None = None, clip_index: int | None = None) -> Path:
    """Atomically record one post-QC row; gate decisions remain untouched."""
    try:
        queue_rows = queue_rows if queue_rows is not None else _load_queue_rows(repository_root.resolve())
        row = normalize_row(qc_evidence_path.parent, repository_root=repository_root,
                            queue_rows=queue_rows, job_id=job_id, clip_index=clip_index)
        return _atomic(qc_evidence_path.parent / "spend-gate-row.json", canonical_json(row.to_dict()))
    except Exception as exc:
        raise SpendGateRecordingError(f"cannot record spend-gate row for {qc_evidence_path}: {exc}") from exc


def write_completed_run_rows(run_id: str, repository_root: Path) -> tuple[Path, ...]:
    """Post-run recorder for every cut recorded in a completed run manifest."""
    try:
        for provenance_path in sorted((repository_root / "datasets/runs").glob("**/final-provenance.json")):
            document = _json(provenance_path, required=False)
            if not isinstance(document, dict) or run_id not in {document.get("run_id"), provenance_path.parent.name}:
                continue
            expected = {cut.get("qc_evidence_sha256") for cut in document.get("cuts", []) if isinstance(cut, dict)}
            outputs = tuple(write_live_row(path, repository_root=repository_root) for path in sorted(
                (repository_root / "datasets/runs").glob("**/qc-evidence.json")) if _hash_file(path) in expected)
            if len(outputs) != len(expected): raise SpendGateRecordingError(f"run {run_id} is missing QC rows")
            return outputs
        raise SpendGateRecordingError(f"completed run not found: {run_id}")
    except SpendGateRecordingError:
        raise
    except Exception as exc:
        raise SpendGateRecordingError(f"cannot post-record completed run {run_id}: {exc}") from exc
