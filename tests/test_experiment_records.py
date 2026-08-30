"""Closure 3 RED — audience-signal memory + experiment-selection record layer.

Isolated lane: experiments/records.py must not import from training/
run_baseline_then_gepa.py, metrics/qc_feedback.py, evaluate/render_qc.py,
or any GEPA module. Fails until experiments/records.py exists.
"""
import json
import pathlib

import pytest

from experiments.records import (
    AudienceMemory,
    ExperimentRecordError,
    canonical_json,
    read_record,
    select_next_experiment,
    validate_record,
    write_record,
)


def _observed_metric(name="retention_3s", value=0.41, source="yt_studio"):
    return {
        "name": name,
        "value": value,
        "status": "observed",
        "source": source,
        "observation": {"window": "48h", "n": 1200},
    }


def _base_record(**over):
    rec = {
        "experiment_id": "exp-001",
        "candidate": "ektachrome-v2",
        "brief": "warmer grade for kaiju reveal",
        "references": {"world": "world-bible-7", "continuity": "shot-014"},
        "settings": {"profile": "3", "seed": 11, "comparison": {
            "role": "baseline", "held_out": True, "metric": "retention_3s"}},
        "resources": {"gpu_minutes": 16.2, "shots": 1},
        "artifact_hashes": {"final.mp4": "a" * 64},
        "qc": {
            "verdict": "pass",
            "score": 7.8,
            "gate_failures": [],
            "artifacts_verified": True,
        },
        "audience_metrics": [_observed_metric()],
        "decision": "accepted",
        "next_action": "hold as baseline",
    }
    rec.update(over)
    return rec


# --- validation -----------------------------------------------------------

def test_valid_record_passes():
    assert validate_record(_base_record())["experiment_id"] == "exp-001"


@pytest.mark.parametrize("missing", [
    "experiment_id", "candidate", "brief", "references", "settings",
    "resources", "artifact_hashes", "qc", "audience_metrics", "decision",
    "next_action",
])
def test_missing_required_field_rejected(missing):
    rec = _base_record()
    del rec[missing]
    with pytest.raises(ExperimentRecordError):
        validate_record(rec)


def test_unverified_artifacts_rejected():
    rec = _base_record()
    rec["qc"]["artifacts_verified"] = False
    with pytest.raises(ExperimentRecordError):
        validate_record(rec)


def test_invalid_hash_rejected():
    rec = _base_record()
    rec["artifact_hashes"]["final.mp4"] = "not-a-hash"
    with pytest.raises(ExperimentRecordError):
        validate_record(rec)


def test_accepted_with_gate_failures_rejected():
    rec = _base_record()
    rec["qc"]["gate_failures"] = ["seam_tolerance"]
    with pytest.raises(ExperimentRecordError):
        validate_record(rec)


def test_text_audience_score_rejected():
    rec = _base_record()
    rec["audience_metrics"] = [{
        "name": "retention_3s", "value": "pretty good", "status": "observed",
        "source": "vibe", "observation": {},
    }]
    with pytest.raises(ExperimentRecordError):
        validate_record(rec)


def test_unavailable_audience_data_is_explicit_not_fabricated():
    rec = _base_record()
    rec["audience_metrics"] = [{
        "name": "retention_3s", "value": None, "status": "unavailable",
        "source": "yt_studio", "observation": {"reason": "window not elapsed"},
    }]
    out = validate_record(rec)
    assert out["audience_metrics"][0]["status"] == "unavailable"
    assert out["audience_metrics"][0]["value"] is None


def test_observed_without_numeric_value_rejected():
    rec = _base_record()
    rec["audience_metrics"][0]["value"] = None
    with pytest.raises(ExperimentRecordError):
        validate_record(rec)


# --- deterministic JSON round-trip + atomic persistence --------------------

def test_deterministic_json_round_trip():
    rec = _base_record()
    text1 = canonical_json(rec)
    text2 = canonical_json(json.loads(text1))
    assert text1 == text2
    assert json.loads(text1)["experiment_id"] == "exp-001"


def test_atomic_write_and_read_round_trip(tmp_path):
    rec = _base_record()
    p = pathlib.Path(tmp_path) / "recs" / "exp-001.json"
    write_record(p, rec)
    assert read_record(p) == validate_record(rec)
    # no partial temp files left behind
    leftovers = [q.name for q in p.parent.iterdir() if q.name != p.name]
    assert leftovers == []


# --- audience memory --------------------------------------------------------

def test_audience_memory_stores_and_returns_prior_signals(tmp_path):
    mem = AudienceMemory(tmp_path / "audience")
    mem.store(_base_record())
    rec2 = _base_record(
        experiment_id="exp-002", decision="rejected", next_action="revise",
        settings={"profile": "3", "seed": 12, "comparison": {
            "role": "challenger", "held_out": True,
            "metric": "retention_3s"}})
    mem.store(rec2)
    signals = mem.prior_signals("retention_3s")
    assert len(signals) == 2
    assert all(s["metric"]["status"] == "observed" for s in signals)
    assert {s["experiment_id"] for s in signals} == {"exp-001", "exp-002"}


def test_audience_memory_does_not_touch_datasets(tmp_path):
    datasets = tmp_path / "datasets"
    datasets.mkdir()
    mem = AudienceMemory(tmp_path / "audience")
    mem.store(_base_record())
    assert list(datasets.iterdir()) == []


# --- selector ---------------------------------------------------------------

def _challenger(metric_value, gate_failures=None, decision="accepted",
                held_out=True, status="observed", exp="exp-002"):
    comp = {"role": "challenger", "held_out": held_out,
            "metric": "retention_3s"}
    m = _observed_metric(value=metric_value)
    m["status"] = status
    if status != "observed":
        m["value"] = None
    return _base_record(
        experiment_id=exp, settings={"profile": "3", "seed": 12,
                                     "comparison": comp},
        audience_metrics=[m],
        qc={"verdict": "pass", "score": 8.1,
            "gate_failures": gate_failures or [],
            "artifacts_verified": True},
        decision=decision, next_action="compare")


def test_selector_insufficient_evidence_when_no_accepted_records(tmp_path):
    rec = _base_record(decision="rejected", next_action="revise")
    out = select_next_experiment([rec])
    assert out["decision"] == "insufficient_evidence"
    assert isinstance(out["next_action"], str) and out["next_action"]


def test_selector_withholds_when_audience_data_unavailable():
    base = _base_record(
        audience_metrics=[{
            "name": "retention_3s", "value": None, "status": "unavailable",
            "source": "yt_studio", "observation": {"reason": "pending"}}])
    out = select_next_experiment([base, _challenger(0.5)])
    assert out["decision"] in ("insufficient_evidence", "withhold")


def test_selector_improved_on_heldout_numeric_gain_with_stable_gates():
    out = select_next_experiment([_base_record(), _challenger(0.55)])
    assert out["decision"] == "improved"
    assert out["evidence"]["baseline"] == 0.41
    assert out["evidence"]["challenger"] == 0.55


def test_selector_not_improved_when_metric_drops():
    out = select_next_experiment([_base_record(), _challenger(0.30)])
    assert out["decision"] == "not_improved"


def test_selector_rejects_improved_on_more_gate_failures():
    base = _base_record()
    base["qc"]["gate_failures"] = []          # baseline clean
    chall = _challenger(0.55, gate_failures=["seam_tolerance"])
    # challenger with gate failures cannot be accepted at all
    chall["decision"] = "rejected"
    chall["next_action"] = "fix seams"
    out = select_next_experiment([base, chall])
    assert out["decision"] != "improved"


def test_selector_requires_heldout_comparison():
    out = select_next_experiment(
        [_base_record(), _challenger(0.55, held_out=False)])
    assert out["decision"] == "insufficient_evidence"


def test_selector_rejects_non_comparable_records():
    other = _challenger(0.55)
    other["settings"]["comparison"]["metric"] = "share_rate"
    out = select_next_experiment([_base_record(), other])
    assert out["decision"] == "insufficient_evidence"


# --- generic lane preservation / isolation ----------------------------------

def test_records_module_imports_nothing_from_generic_lanes():
    import sys
    before = set(sys.modules)
    import experiments.records  # noqa: F401
    newly = set(sys.modules) - before
    banned = ("run_baseline_then_gepa", "qc_feedback", "render_qc", "gepa")
    src = pathlib.Path(experiments.records.__file__).read_text()
    for b in banned:
        assert b not in src, f"experiments/records.py references {b}"
    for mod in newly:
        assert not any(b in mod for b in banned), mod


# --- experiment_id filename safety (path traversal) ------------------------

@pytest.mark.parametrize("bad_id", [
    "../escape",           # traversal up
    "..",                  # dotdot alone
    "a/b",                 # slash separator
    "a\\b",               # backslash separator
    "/abs",                # absolute path
    "exp/../../etc",       # mixed traversal
    "exp\x00id",           # NUL byte
    "exp id",              # whitespace
    "exp;rm",              # punctuation outside ._- 
    "éxperiment",          # non-ASCII
    "",                    # empty
    "e" * 129,             # over length bound
])
def test_unsafe_experiment_id_rejected(bad_id):
    with pytest.raises(ExperimentRecordError):
        validate_record(_base_record(experiment_id=bad_id))


def test_audience_memory_cannot_write_outside_root(tmp_path):
    root = tmp_path / "memory"
    am = AudienceMemory(root)
    outside_marker = tmp_path / "outside.txt"
    outside_marker.write_text("sentinel")
    with pytest.raises(ExperimentRecordError):
        am.store(_base_record(experiment_id="../pwned"))
    assert not (tmp_path / "pwned.json").exists()
    assert outside_marker.read_text() == "sentinel"
    # nothing escaped the root
    assert list(root.glob("**/*")) == [] or all(
        root in p.parents or p == root for p in root.glob("**/*"))
