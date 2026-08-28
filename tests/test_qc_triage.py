"""VLM QC failure triage classifier (WD-rty2, ADOPT #7).

Three-tier escalation ladder (shuohao-skills changelog-design-
rationale.md section B; CHANGELOG:384-398): when a QC failure
recurs, decide EXPLICITLY which tier absorbs it — gate / rule /
example. Central axiom: "误拦的门比没有门更糟——门的信用比数量重要"
(a false-blocking gate is worse than no gate; a gate's credibility
matters more than its count) — extraction :12, CHANGELOG:355-356.

ZERO-MODEL: deterministic field logic over STRUCTURED failure
records, same contract as gates/provenance_gate.py.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from gates.qc_triage import (  # noqa: E402
    EXAMPLE_GAP, GATE_FALSE_POSITIVE, RULE_VIOLATION, QCTriageError,
    classify_qc_failure, load_ledger, stats, write_record,
)


def _event(**kw):
    base = {
        "event_id": "ev-1",
        "timestamp": "2026-08-28T00:00:00Z",
        "genre": "music",
        "gate_id": "render_qc_threshold",
        "verdict": "reject",
        "scores": {"coherence": 2.0, "brief_adherence": 8.0,
                   "concept_encoding": 9.0},
        "anchor_field": "coherence",
        "notes": "the shot reads as static",
    }
    base.update(kw)
    return base


# ── 1: classification semantics — the three tiers ──────────────────

def test_human_overridden_reject_is_gate_false_positive():
    """Gate fired REJECT but a human review passed the material —
    the gate blocked good material: fix or remove the gate."""
    out = classify_qc_failure(_event(human_review="pass"))
    assert out.classification == GATE_FALSE_POSITIVE
    assert out.confidence in ("high", "medium")


def test_gate_fired_but_material_later_passed_is_gate_false_positive():
    out = classify_qc_failure(_event(later_pass=True))
    assert out.classification == GATE_FALSE_POSITIVE


def test_named_rule_violation_without_gate_fire_is_rule_violation():
    """Human flagged a violation of a NAMED rule and no gate fired
    on it — the material genuinely violates a stated rule: fix the
    material/brief."""
    out = classify_qc_failure(_event(
        verdict="pass", gate_fired=False,
        named_rule="no-names-in-briefs",
        notes="brief contains a proper name — violates no-names rule"))
    assert out.classification == RULE_VIOLATION


def test_no_named_rule_no_deterministic_signal_is_example_gap():
    """Human flagged something with NO named rule and no
    deterministic signal — the exemplar set doesn't demonstrate
    the norm: add/fix an exemplar, do NOT build a keyword gate."""
    out = classify_qc_failure(_event(
        verdict="revise", gate_fired=False,
        notes="the motion feels lifeless, hard to say why"))
    assert out.classification == EXAMPLE_GAP


def test_ambiguous_event_is_typed_rejection():
    """Both signals present (human pass AND named-rule violation)
    — never silently defaulted: typed rejection."""
    with pytest.raises(QCTriageError) as ei:
        classify_qc_failure(_event(
            human_review="pass",
            named_rule="no-names-in-briefs",
            notes="conflicting signals"))
    assert ei.value.kind == "ambiguous"


def test_unknown_verdict_is_typed_rejection():
    with pytest.raises(QCTriageError):
        classify_qc_failure(_event(verdict="maybe"))


def test_empty_input_loud_skip(caplog):
    """kind=empty_text pattern: empty event raises typed loud skip."""
    with pytest.raises(QCTriageError) as ei:
        classify_qc_failure({})
    assert ei.value.kind == "empty_text"


def test_evidence_is_verbatim_excerpt():
    out = classify_qc_failure(_event(human_review="pass"))
    assert out.evidence  # nonempty verbatim excerpt from the event


# ── 2: ledger schema + append-only + stats ─────────────────────────

def test_write_record_roundtrip(tmp_path):
    p = tmp_path / "ledger.jsonl"
    ev = _event(human_review="pass")
    rec = write_record(p, ev, action_taken="gate-fixed",
                       follow_up_story="WD-gate-fix")
    assert rec["classification"] == GATE_FALSE_POSITIVE
    assert rec["action_taken"] == "gate-fixed"
    assert rec["follow_up_story"] == "WD-gate-fix"
    lines = p.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    back = json.loads(lines[0])
    for key in ("event_id", "timestamp", "genre", "gate_id",
                "verdict", "scores", "classification", "confidence",
                "evidence", "action_taken", "follow_up_story"):
        assert key in back, f"missing {key}"


def test_append_only_multiple_records(tmp_path):
    p = tmp_path / "ledger.jsonl"
    write_record(p, _event(human_review="pass"),
                 action_taken="gate-fixed")
    write_record(p, _event(event_id="ev-2", verdict="pass",
                           gate_fired=False,
                           named_rule="r", notes="n"),
                 action_taken="brief-fixed")
    lines = p.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["event_id"] == "ev-1"


def test_stats_counts_per_class_and_gates(tmp_path):
    p = tmp_path / "ledger.jsonl"
    write_record(p, _event(human_review="pass"),
                 action_taken="gate-fixed")
    write_record(p, _event(event_id="e2", gate_id="language_gate",
                           human_review="pass"),
                 action_taken="gate-fixed")
    write_record(p, _event(event_id="e3", verdict="pass",
                           gate_fired=False, named_rule="r",
                           notes="n"), action_taken="brief-fixed")
    s = stats(p, known_gates=("render_qc_threshold", "language_gate",
                              "provenance_gate"))
    assert s["per_class"][GATE_FALSE_POSITIVE] == 2
    assert s["per_class"][RULE_VIOLATION] == 1
    assert s["per_gate"]["render_qc_threshold"] == 2
    assert s["never_fired"] == ["provenance_gate"]


def test_stats_empty_ledger(tmp_path):
    p = tmp_path / "ledger.jsonl"
    s = stats(p, known_gates=("g1",))
    assert s["per_class"] == {}
    assert s["per_gate"] == {}
    assert s["never_fired"] == ["g1"]


def test_invalid_action_taken_rejected(tmp_path):
    p = tmp_path / "ledger.jsonl"
    with pytest.raises(ValueError):
        write_record(p, _event(human_review="pass"),
                     action_taken="auto-rewrite")


# ── 3: CLI smoke — exit codes 0/1/2 ────────────────────────────────

def _cli(*args):
    return subprocess.run(
        [sys.executable, str(REPO / "scripts" / "check_qc_triage.py"),
         *args], capture_output=True, text=True, cwd=str(REPO))


def test_cli_clean_event_exit_0(tmp_path):
    f = tmp_path / "ev.json"
    f.write_text(json.dumps(_event(human_review="pass")),
                 encoding="utf-8")
    r = _cli(str(f))
    assert r.returncode == 0, r.stderr


def test_cli_ambiguous_event_exit_1(tmp_path):
    f = tmp_path / "ev.json"
    f.write_text(json.dumps(_event(human_review="pass",
                                   named_rule="r", notes="x")),
                 encoding="utf-8")
    r = _cli(str(f))
    assert r.returncode == 1, r.stdout + r.stderr


def test_cli_usage_error_exit_2():
    r = _cli("--nonexistent-flag")
    assert r.returncode == 2
