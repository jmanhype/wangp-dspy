"""WD-oa4i STEP 1 — loader hardening (strict TDD).

load_examples() must enforce:
  1. exact-intent dedup (keep best-QC record per identical intent)
  2. normalized-subject dedup (same brief subject modulo case/space =
     same scene -> keep best-QC record)
  3. cross-split guard: RAISE if a brief-hash appears in both train and
     val after the split (no accidental adjacency protection)
"""
import json

import pytest

from metrics.qc_feedback import load_examples

LG = ("a lighthouse beacon sweeping a black ocean at night, "
      "storm building, waves exploding against the rocks")

KJ = "a kaiju silhouette rising through fog over a harbor city"

NR = "rain on neon streets at midnight, reflections rippling"


def _run(tmp_path, run_id, intent, qc, subject=None):
    subject = subject or (
        "A weathered stone lighthouse on a jagged black headland"
        if "lighthouse" in intent else
        "A vast silhouette of something enormous behind the fog"
        if "kaiju" in intent else
        "A rain-slick street of neon signage at midnight")
    return {
        "run_id": run_id,
        "genre": "surreal",
        "intent": intent,
        "briefs": [{"subject": subject, "motion": "m", "camera": "c",
                    "style": "s"}],
        "qc": {"score": qc},
    }


def _bank(tmp_path, runs):
    for r in runs:
        (tmp_path / f"{r['run_id']}.json").write_text(json.dumps(r))
    return str(tmp_path)


def test_exact_intent_dedup_keeps_best_qc(tmp_path):
    d = _bank(tmp_path, [
        _run(tmp_path, "a1", LG, 8),
        _run(tmp_path, "a2", LG, 9),
        _run(tmp_path, "a3", LG, 8),
    ])
    train, val = load_examples(d)
    kept = train + val
    assert len(kept) == 1
    assert kept[0].qc_score == 9


def test_normalized_subject_dedup(tmp_path):
    # different intent strings, same subject modulo whitespace/case
    d = _bank(tmp_path, [
        _run(tmp_path, "b1", "lighthouse variant alpha", 7,
             subject="A weathered stone lighthouse on a jagged black headland"),
        _run(tmp_path, "b2", "lighthouse variant beta", 9,
             subject="a  weathered  STONE lighthouse  on a jagged black headland"),
    ])
    train, val = load_examples(d)
    kept = train + val
    assert len(kept) == 1
    assert kept[0].qc_score == 9


def test_cross_split_duplicate_raises(tmp_path):
    # two DISTINCT intents+subjects, but brief-hash collision forced by
    # identical full briefs is already caught by dedup; the cross-split
    # guard covers a same brief-hash sneaking into both splits — simulate
    # by monkeypatching the splitter boundary via many distinct runs where
    # two share a brief hash only after normalization edge (fallback):
    runs = [_run(tmp_path, f"c{i}", f"unique intent number {i}", 5 + i % 3,
                 subject=f"Distinct subject {i}") for i in range(4)]
    d = _bank(tmp_path, runs)
    # duplicate a brief into a differently-named run so dedup-by-subject
    # sees it, but bypass via slight punctuation that normalization keeps:
    dupe = _run(tmp_path, "c9", "totally other intent", 9,
                subject="Distinct subject 3")
    (tmp_path / "c9.json").write_text(json.dumps(dupe))
    # identical normalized subject -> dedup must collapse to 4, never a
    # cross-split collision; the raise path is exercised in the next test
    train, val = load_examples(d)
    assert len(train) + len(val) == 4

    # force the raise: inject a train example and val example with equal
    # brief hashes directly through the guard function
    from metrics.qc_feedback import _assert_no_cross_split_duplicates
    with pytest.raises(ValueError, match="cross-split"):
        _assert_no_cross_split_duplicates([train[0]], [train[0]])
