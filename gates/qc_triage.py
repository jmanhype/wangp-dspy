"""VLM QC failure triage classifier + ledger (WD-rty2, ADOPT #7).

ADOPT of the shuohao-skills three-tier escalation ladder
(docs/extraction/shuohao-skills/changelog-design-rationale.md
section B; CHANGELOG:384-398): when a QC failure recurs, decide
EXPLICITLY which tier absorbs it —

  1. deterministically judgeable -> hard gate/rule
  2. semantic/ungateable         -> craft rule + reasoning, NO
     keyword gate ("keyword scans leak both ways")
  3. example-as-norm             -> fix the bundled exemplar so
     every instance demonstrates the rule ("样例即规范")

Central axiom (extraction :12, CHANGELOG:355-356):
"误拦的门比没有门更糟——门的信用比数量重要" — a false-blocking gate
is worse than no gate; a gate's credibility matters more than its
count.

Classification is DETERMINISTIC field logic over STRUCTURED
failure records (QC verdicts + human-review overrides) — the same
ZERO-MODEL contract as gates/provenance_gate.py. The ledger is
APPEND-ONLY (retention=none, append anytime); stats() is a pure
read answering the .gates.jsonl discipline (section G): which
class dominates, which gate fires most (rewrite that gate's
wording), which never fires (dead gate or internalized). No
auto-rewriting of rules/docs from the ledger — we log and a human
decides ("没有评测集的自动改文档就是瞎改").
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

__all__ = [
    "QCTriageError", "QCTriageResult",
    "GATE_FALSE_POSITIVE", "RULE_VIOLATION", "EXAMPLE_GAP",
    "ACTIONS", "classify_qc_failure", "write_record", "load_ledger",
    "stats",
]

# ── the three classes ──────────────────────────────────────────────
GATE_FALSE_POSITIVE = "gate_false_positive"
RULE_VIOLATION = "rule_violation"
EXAMPLE_GAP = "example_gap"

VERDICTS = ("pass", "revise", "reject")

# sanctioned actions (human decides; no auto-rewrite class exists)
ACTIONS = ("gate-fixed", "brief-fixed", "exemplar-added",
           "escalated-human")


class QCTriageError(ValueError):
    """Typed triage failure. kind marks the loud-skip / ambiguity
    case."""

    def __init__(self, message: str, *, kind: str | None = None):
        self.kind = kind
        super().__init__(message)


@dataclass(frozen=True)
class QCTriageResult:
    classification: str
    confidence: str          # high | medium
    evidence: str            # verbatim excerpt from the event
    reason: str


def _require(event: dict, key: str):
    if not isinstance(event, dict):
        raise QCTriageError(
            f"qc triage: event must be a dict, got {type(event)}",
            kind="empty_text")
    v = event.get(key)
    if v is None or (isinstance(v, str) and not v.strip()):
        raise QCTriageError(
            f"qc triage: event missing required field {key!r} "
            "(loud skip — structured input only)", kind="empty_text")
    return v


def classify_qc_failure(event: dict) -> QCTriageResult:
    """Classify one recorded QC failure event into exactly one of
    {GATE_FALSE_POSITIVE, RULE_VIOLATION, EXAMPLE_GAP}.

    Documented heuristics (decision procedure: FIRST ask 'is this
    deterministically judgeable?'):

    - human_review == 'pass' on a fired gate (verdict revise/reject)
      OR later_pass=True -> GATE_FALSE_POSITIVE (high): the gate
      blocked material a human judged good — 误拦; fix or remove
      the gate.
    - a NAMED rule was violated (named_rule set) AND no gate fired
      on it -> RULE_VIOLATION (high): the material genuinely
      violates a stated rule — fix the material/brief.
    - a human flagged something with NO named rule and no
      deterministic signal -> EXAMPLE_GAP (medium): the exemplar
      set doesn't demonstrate the norm — add/fix an exemplar, do
      NOT build a keyword gate.

    Ambiguous events (both gate-false-positive and rule-violation
    signals present) are a TYPED rejection — never silently
    defaulted. Unknown verdicts reject typed. Empty events raise
    kind=empty_text (loud-skip pattern).
    """
    _require(event, "event_id")
    _require(event, "genre")
    _require(event, "gate_id")
    verdict = str(_require(event, "verdict")).lower()
    if verdict not in VERDICTS:
        raise QCTriageError(
            f"qc triage: unknown verdict {verdict!r}; expected one "
            f"of {VERDICTS}", kind="unknown_verdict")
    notes = str(event.get("notes") or "")
    scores = event.get("scores") or {}
    anchor = event.get("anchor_field") or ""
    human_review = str(event.get("human_review") or "").lower()
    later_pass = bool(event.get("later_pass"))
    named_rule = str(event.get("named_rule") or "").strip()
    gate_fired = bool(event.get("gate_fired",
                                verdict in ("revise", "reject")))

    # A named-rule violation is an independent signal regardless of
    # whether a gate fired elsewhere on this event: the human can
    # have judged the gated aspect good (FP) while ALSO flagging a
    # separate named-rule breach (RV) — both at once is genuinely
    # ambiguous (which fix wins?).
    fp_signal = (human_review == "pass" and gate_fired) or \
        (later_pass and gate_fired)
    rv_signal = bool(named_rule)
    gap_signal = (not gate_fired) and (not named_rule) and \
        (not fp_signal) and bool(notes.strip())

    if fp_signal and rv_signal:
        raise QCTriageError(
            f"qc triage: event {event['event_id']!r} carries BOTH a "
            f"gate-false-positive signal (human passed gated "
            f"material) and a named-rule violation — ambiguous, "
            f"refusing to default (human adjudication required)",
            kind="ambiguous")
    if not (fp_signal or rv_signal or gap_signal):
        raise QCTriageError(
            f"qc triage: event {event['event_id']!r} is "
            f"unclassifiable — no gate-false-positive, named-rule, "
            f"or example-gap signal present (verdict={verdict}, "
            f"gate_fired={gate_fired}, named_rule={named_rule!r})",
            kind="unclassifiable")

    evidence = notes[:200] or \
        f"{event['gate_id']} fired verdict={verdict} " \
        f"scores={json.dumps(scores, sort_keys=True)}"

    if fp_signal:
        why = ("human review passed material the gate rejected "
               "(误拦 — a false-blocking gate is worse than no gate)"
               if human_review == "pass" else
               "material later passed after the gate fired")
        return QCTriageResult(
            classification=GATE_FALSE_POSITIVE, confidence="high",
            evidence=evidence,
            reason=f"{why}; fix or remove gate "
                   f"{event['gate_id']!r}")
    if rv_signal:
        return QCTriageResult(
            classification=RULE_VIOLATION, confidence="high",
            evidence=evidence,
            reason=(f"named rule {named_rule!r} violated without a "
                    f"gate firing — fix the material/brief, not the "
                    f"gate"))
    return QCTriageResult(
        classification=EXAMPLE_GAP, confidence="medium",
        evidence=evidence,
        reason=("no named rule and no deterministic signal — the "
                "exemplar set doesn't demonstrate the norm; add/"
                "fix an exemplar, do NOT build a keyword gate "
                "(keyword scans leak both ways)"))


# ── ledger (append-only JSONL) + stats ─────────────────────────────

_REQUIRED_RECORD_KEYS = (
    "event_id", "timestamp", "genre", "gate_id", "verdict", "scores",
    "classification", "confidence", "evidence", "action_taken",
    "follow_up_story",
)


def write_record(path, event: dict, *, action_taken: str,
                 follow_up_story: str = "") -> dict:
    """Classify *event* and APPEND one ledger record to *path*.

    Append-only by construction (open 'a'); the record carries the
    full schema (datasets/qc-triage-ledger.schema.json). No
    rewriting of prior lines ever happens here.
    """
    if action_taken not in ACTIONS:
        raise ValueError(
            f"action_taken {action_taken!r} not in {ACTIONS} — the "
            "ledger records HUMAN decisions; there is no "
            "auto-rewrite action class")
    res = classify_qc_failure(event)
    rec = {
        "event_id": event["event_id"],
        "timestamp": event.get("timestamp") or "",
        "genre": event["genre"],
        "gate_id": event["gate_id"],
        "verdict": str(event["verdict"]).lower(),
        "scores": event.get("scores") or {},
        "classification": res.classification,
        "confidence": res.confidence,
        "evidence": res.evidence,
        "action_taken": action_taken,
        "follow_up_story": follow_up_story,
    }
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


def load_ledger(path) -> list:
    """Pure read of the append-only ledger (missing file = empty)."""
    p = Path(path)
    if not p.exists():
        return []
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rec = json.loads(line)
        for key in _REQUIRED_RECORD_KEYS:
            if key not in rec:
                raise ValueError(
                    f"ledger record missing {key!r}: {line[:80]}")
        out.append(rec)
    return out


def stats(path, *, known_gates: tuple = ()) -> dict:
    """The section-G stats view (pure read): counts per class,
    per-gate fire counts, never-fired gate list. Answers: which
    class dominates, which gate fires most (rewrite that gate's
    wording), which never fires (dead gate or internalized)."""
    records = load_ledger(path)
    per_class: dict = {}
    per_gate: dict = {}
    for rec in records:
        per_class[rec["classification"]] = \
            per_class.get(rec["classification"], 0) + 1
        per_gate[rec["gate_id"]] = per_gate.get(rec["gate_id"], 0) + 1
    never = [g for g in known_gates if g not in per_gate]
    return {"per_class": per_class, "per_gate": per_gate,
            "never_fired": never, "total": len(records)}
