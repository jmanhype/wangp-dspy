"""Closure 3 — audience-signal memory + experiment-selection record layer.

Deliberately isolated lane: no imports from the generic training-baseline,
QC-feedback, render-QC, or optimization-lane modules. Pure stdlib.
"""
from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path

_HASH_RE = re.compile(r"^[0-9a-f]{64}$")
_METRIC_STATUSES = ("observed", "unavailable")
_DECISIONS = ("accepted", "rejected", "withheld")


class ExperimentRecordError(ValueError):
    """Raised when an experiment record fails validation."""


def _require_mapping(rec, key):
    v = rec.get(key)
    if not isinstance(v, dict) or not v:
        raise ExperimentRecordError(f"{key} must be a non-empty mapping")
    return v


def validate_record(rec):
    """Validate one experiment record; return a normalized deep copy."""
    if not isinstance(rec, dict):
        raise ExperimentRecordError("record must be a mapping")
    for key in ("experiment_id", "candidate", "brief", "decision",
                "next_action"):
        if not isinstance(rec.get(key), str) or not rec[key].strip():
            raise ExperimentRecordError(f"{key} must be a non-empty string")
    _require_mapping(rec, "references")
    _require_mapping(rec, "settings")
    _require_mapping(rec, "resources")

    hashes = _require_mapping(rec, "artifact_hashes")
    for name, h in hashes.items():
        if not isinstance(h, str) or not _HASH_RE.match(h):
            raise ExperimentRecordError(
                f"artifact hash for {name!r} must be a 64-hex sha256")

    qc = _require_mapping(rec, "qc")
    verdict = qc.get("verdict")
    if not isinstance(verdict, str) or verdict not in ("pass", "fail"):
        raise ExperimentRecordError("qc.verdict must be 'pass' or 'fail'")
    if not isinstance(qc.get("score"), (int, float)) or \
            isinstance(qc.get("score"), bool):
        raise ExperimentRecordError("qc.score must be numeric")
    failures = qc.get("gate_failures")
    if not isinstance(failures, list) or any(
            not isinstance(f, str) for f in failures):
        raise ExperimentRecordError("qc.gate_failures must be a str list")
    if qc.get("artifacts_verified") is not True:
        raise ExperimentRecordError(
            "qc.artifacts_verified must be True — unverified artifacts")
    if rec["decision"] == "accepted" and (verdict == "fail" or failures):
        raise ExperimentRecordError(
            "accepted records cannot have failed/unverified gates")

    am = rec.get("audience_metrics")
    if not isinstance(am, list) or not am:
        raise ExperimentRecordError("audience_metrics must be a non-empty list")
    for m in am:
        if not isinstance(m, dict):
            raise ExperimentRecordError("audience metric must be a mapping")
        name = m.get("name")
        if not isinstance(name, str) or not name.strip():
            raise ExperimentRecordError("audience metric needs a name")
        status = m.get("status")
        if status not in _METRIC_STATUSES:
            raise ExperimentRecordError(
                f"metric {name!r}: status must be one of {_METRIC_STATUSES}")
        value = m.get("value")
        if status == "observed":
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ExperimentRecordError(
                    f"metric {name!r}: observed value must be numeric "
                    "(text-only scores are rejected)")
        elif value is not None:
            raise ExperimentRecordError(
                f"metric {name!r}: unavailable value must be None")
        if not isinstance(m.get("source"), str) or not m["source"].strip():
            raise ExperimentRecordError(
                f"metric {name!r}: source is required")
        if not isinstance(m.get("observation"), dict):
            raise ExperimentRecordError(
                f"metric {name!r}: observation metadata is required")

    return json.loads(canonical_json(rec))


def canonical_json(obj):
    """Deterministic JSON: sorted keys, stable separators."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False)


def write_record(path, rec):
    """Atomic write of a validated record."""
    rec = validate_record(rec)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(canonical_json(rec))
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    return path


def read_record(path):
    """Read + validate one record file."""
    with open(path, encoding="utf-8") as f:
        return validate_record(json.load(f))


class AudienceMemory:
    """Stores/loads experiment records; returns prior audience signals.

    Touches only its own directory — never datasets, runs, or GEPA state.
    """

    def __init__(self, root):
        self.root = Path(root)

    def store(self, rec):
        rec = validate_record(rec)
        write_record(self.root / f"{rec['experiment_id']}.json", rec)
        return rec["experiment_id"]

    def load_all(self):
        if not self.root.exists():
            return []
        return [read_record(p) for p in sorted(self.root.glob("*.json"))]

    def prior_signals(self, metric_name):
        """Validated prior signals for one named metric (observed only)."""
        out = []
        for rec in self.load_all():
            for m in rec["audience_metrics"]:
                if m["name"] == metric_name and m["status"] == "observed":
                    out.append({"experiment_id": rec["experiment_id"],
                                "candidate": rec["candidate"],
                                "decision": rec["decision"],
                                "metric": m})
        return out


def _comparison(rec):
    comp = rec.get("settings", {}).get("comparison")
    if not isinstance(comp, dict):
        return None
    if comp.get("held_out") is not True:
        return None
    role, metric = comp.get("role"), comp.get("metric")
    if role not in ("baseline", "challenger") or not isinstance(metric, str):
        return None
    return role, metric


def _observed_value(rec, metric_name):
    values = [m["value"] for m in rec["audience_metrics"]
              if m["name"] == metric_name and m["status"] == "observed"]
    return values[0] if len(values) == 1 else None


def select_next_experiment(records):
    """Deterministic selection of the next controlled experiment.

    Requires comparable accepted baseline + challenger records with
    held-out, numerically observed audience metrics and no increased gate
    failures. Never returns 'improved' otherwise.
    """
    valid = []
    for rec in records:
        try:
            valid.append(validate_record(rec))
        except ExperimentRecordError:
            continue

    accepted = [r for r in valid if r["decision"] == "accepted"]
    if not accepted:
        return {"decision": "insufficient_evidence",
                "next_action": "run a candidate experiment to accepted "
                               "validation with artifact-verified QC evidence"}

    # group by comparison metric
    by_metric = {}
    for rec in accepted:
        comp = _comparison(rec)
        if not comp:
            continue
        role, metric = comp
        value = _observed_value(rec, metric)
        if value is None:
            continue  # unavailable/text audience data -> withheld
        by_metric.setdefault(metric, {})[role] = (rec, value)

    for metric in sorted(by_metric):
        pair = by_metric[metric]
        if set(pair) != {"baseline", "challenger"}:
            continue
        base_rec, base_val = pair["baseline"]
        chall_rec, chall_val = pair["challenger"]
        base_fails = len(base_rec["qc"]["gate_failures"])
        chall_fails = len(chall_rec["qc"]["gate_failures"])
        if chall_fails > base_fails:
            return {"decision": "withhold",
                    "metric": metric,
                    "next_action": "challenger regressed gate stability "
                                   f"({base_fails}->{chall_fails} failures); "
                                   "fix gates before promoting"}
        if chall_val > base_val:
            return {"decision": "improved",
                    "metric": metric,
                    "evidence": {"baseline": base_val,
                                 "challenger": chall_val,
                                 "held_out": True,
                                 "gate_failures": chall_fails},
                    "next_action": f"promote {chall_rec['candidate']} as the "
                                   f"new baseline for {metric}"}
        return {"decision": "not_improved",
                "metric": metric,
                "evidence": {"baseline": base_val, "challenger": chall_val},
                "next_action": f"keep {base_rec['candidate']} as baseline "
                               f"for {metric}; iterate candidate"}

    return {"decision": "insufficient_evidence",
            "next_action": "no held-out baseline/challenger pair with "
                           "observed numeric audience metrics; run a "
                           "controlled held-out comparison"}
