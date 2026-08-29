"""qc_feedback_metric — the GEPA-facing metric (WD-txt9).

Research-derived contract (dspy.ai metrics-and-evaluation + GEPA paper
+ dspy-gepa-optimization skill):

- Program level (pred is a full pipeline result): return FLOAT —
  GEPA's progress reporter sums floats; dicts/int mixes raise
  TypeError (skill pitfall #1).
- Predictor level (pred_name is not None): return
  dspy.Prediction(score, feedback) — GEPA is the only optimizer that
  reads the natural-language feedback and threads it into reflection
  proposals. The feedback must say WHY, naming what the gold brief did
  that the prediction missed (the RenderQC critique vocabulary).
- trace toggle (skill pitfall + docs pattern): continuous score at
  eval time (trace is None), binarized at optimization time
  (trace is not None) so the search chases clean pass/fail.
- Gold labels come from banked runs whose REAL renders earned known
  QC scores (datasets/runs/*.json) — no rendering during optimization.

Scoring (program level): section-overlap F1 between predicted brief
sections and the gold brief (the director's job is to reproduce
director-grade specificity, so token-level recall of craft vocabulary
matters), plus bonuses for craft-sections present (audio_direction,
negatives, identity_lock — the H3-guide fields) weighted by the gold's
QC score so high-scoring golds teach harder.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Optional

import dspy

_CRAFT_FIELDS = ("audio_direction", "negatives", "identity_lock")
_STOP = set("a an the of in on at to with and or for is are was were "
            "its it this that as by from".split())


def _tokens(text: str) -> set:
    return {t for t in re.findall(r"[a-z0-9]+", (text or "").lower())
            if t not in _STOP and len(t) > 2}


def _section_f1(pred_text: str, gold_text: str) -> float:
    p, g = _tokens(pred_text), _tokens(gold_text)
    if not p or not g:
        return 0.0
    overlap = len(p & g)
    precision = overlap / len(p)
    recall = overlap / len(g)
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def qc_feedback_metric(gold, pred, trace=None, pred_name=None,
                       pred_trace=None):
    """Gold example fields: brief (dict of sections), qc_score (float
    0-10). Pred: a RenderBrief-like object (attrs) or Prediction with
    .brief."""
    target = getattr(pred, "brief", pred)
    gold_brief = gold.brief if hasattr(gold, "brief") else {}
    qc = float(getattr(gold, "qc_score", 7.0))

    core_f1 = sum(
        _section_f1(getattr(target, f, "") or "",
                    gold_brief.get(f, ""))
        for f in ("subject", "motion", "camera", "style")) / 4.0

    craft_presence = sum(
        1 for f in _CRAFT_FIELDS if (getattr(target, f, "") or "").strip()
    ) / len(_CRAFT_FIELDS)

    # continuous: core overlap dominates, craft presence is the tiebreak;
    # the gold's real QC score scales how much this example teaches
    score = (0.75 * core_f1 + 0.25 * craft_presence) * (qc / 10.0)

    if pred_name is None:
        # program level: float only (GEPA reporter sums floats)
        return score if trace is None else (score >= 0.5)

    # predictor level: feedback for reflection
    if score >= 0.5:
        feedback = (f"Good: brief overlaps the gold's craft vocabulary "
                    f"(F1 {core_f1:.2f}) and carries "
                    f"{round(craft_presence * 3)}/3 craft sections.")
    else:
        missing = [f for f in _CRAFT_FIELDS
                   if not (getattr(target, f, "") or "").strip()]
        weakest = min(
            ("subject", "motion", "camera", "style"),
            key=lambda f: _section_f1(getattr(target, f, "") or "",
                                      gold_brief.get(f, "")))
        feedback = (
            f"Weak: section {weakest!r} lost the gold's specificity "
            f"(gold: {str(gold_brief.get(weakest, ''))[:120]!r}). "
            + (f"Missing craft sections: {missing} — the gold brief "
               f"directs audio, negatives, and identity locks "
               f"(H3 guide: high-leverage). "
               if missing else "")
            + f"Target the vocabulary: lens/light/texture specifics, "
              f"not generic subject nouns.")
    return dspy.Prediction(score=score, feedback=feedback)


def _norm(text: str) -> str:
    """Lowercase, collapse whitespace — for subject-level identity."""
    return re.sub(r"\s+", " ", (text or "").lower()).strip()


def _brief_hash(brief: dict) -> str:
    """Stable hash of the normalized brief sections (subject..identity_lock)."""
    payload = "\x1f".join(
        _norm(brief.get(f, "")) for f in
        ("subject", "motion", "camera", "style", "audio_direction",
         "negatives", "identity_lock"))
    return hashlib.sha256(payload.encode()).hexdigest()


def _assert_no_cross_split_duplicates(train, val):
    """RAISE on train/val brief-hash collision — no adjacency protection."""
    val_hashes = {_brief_hash(ex.brief) for ex in val}
    collisions = sorted({_brief_hash(ex.brief) for ex in train} & val_hashes)
    if collisions:
        raise ValueError(
            f"cross-split duplicate brief(s): {len(collisions)} brief-hash "
            f"collision(s) between train and val "
            f"(first hash {collisions[0][:12]}…) — dedup failed upstream")


from gates.provenance_gate import MARKER_RE as _MARKER_RE  # noqa: E402


def load_examples(runs_dir: str = "datasets/runs",
                  split: float = 0.7):
    """Banked run records -> train/val dspy.Examples.

    Loader hardening (WD-oa4i STEP 1):
    - exact-intent dedup: identical intent strings keep only the
      best-QC record;
    - normalized-subject dedup: identical brief subjects (case/whitespace
      normalized) likewise keep the best-QC record;
    - cross-split guard: after splitting, any brief-hash present in both
      train and val raises ValueError.
    """
    best = {}  # key -> Example (best QC wins)
    for p in sorted(Path(runs_dir).glob("*.json")):
        r = json.loads(p.read_text())
        if not r.get("qc"):
            continue
        brief = r["briefs"][0]
        brief = brief if isinstance(brief, dict) else {}
        # WD-y9ab validity repair: pre-convention banked golds carry
        # unmarked identity_locks — every LM brief copying them was
        # rejected by the provenance gate (26/26 gold identity_locks
        # violate; baseline fallback storm 2026-08-29). Normalize at
        # load: nonempty unmarked identity_locks get exactly one
        # (inferred) prefix. Semantics-preserving: markers are STRIPPED
        # at brief_to_prompt() and never scored as text content.
        lock = (brief.get("identity_lock", "") or "").strip()
        if lock and not _MARKER_RE.search(lock):
            brief = {**brief, "identity_lock": f"(inferred) {lock}"}
        ex = dspy.Example(
            intent=r.get("intent", ""),
            brief={f: brief.get(f, "") for f in
                   ("subject", "motion", "camera", "style",
                    "audio_direction", "negatives", "identity_lock")},
            qc_score=float(r["qc"]["score"]),
        ).with_inputs("intent")
        for key in (("intent", r.get("intent", "")),
                    ("subject", _norm(brief.get("subject", "")))):
            if not key[1]:
                continue
            prev = best.get(key)
            if prev is None or ex.qc_score > prev.qc_score:
                best[key] = ex

    # exact-intent and subject keys may both survive; collapse to unique
    # examples by brief hash, keeping best QC.
    unique = {}
    for ex in best.values():
        h = _brief_hash(ex.brief)
        prev = unique.get(h)
        if prev is None or ex.qc_score > prev.qc_score:
            unique[h] = ex
    records = list(unique.values())

    k = max(1, int(len(records) * split))
    train, val = records[:k], records[k:]
    _assert_no_cross_split_duplicates(train, val)
    return train, val
