"""WD-txt9 training scripts — baseline first, then GEPA.

Research prescription order (dspy.ai choosing-an-optimizer economics
+ dspy-gepa-optimization skill):
  1. LabeledFewShot baseline — near-zero cost; if it suffices, STOP.
  2. GEPA only on plateau, with checkpoint hygiene: clear/UUID log
     dirs (stale-checkpoint contamination), seed pinned, reflection
     via GLM-5.3, verify learning by SIDE-BY-SIDE outputs.
"""
import os
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

import dspy  # noqa: E402

from predict.lm_wiring import creative_lm  # noqa: E402
from predict.prompt_director import PromptDirector  # noqa: E402
from metrics.qc_feedback import (  # noqa: E402
    qc_feedback_metric, load_examples)
from metrics.metric_blend import (  # noqa: E402
    MetricBlend, SectionWeights, record_scores, load_scores,
    blended_score)


def wire_lm() -> dspy.LM:
    lm = creative_lm()
    dspy.settings.configure(lm=lm)  # baseline needs the default LM
    return lm


def _patch_gepa_row_alignment():
    """WD-txt9 live finding (runs 1-4, identical crash at rollout 3):
    gepa's DSPy adapter Evaluate-fallback returns fewer rows than the
    devset when examples error (res.results drops them), and
    gepa.core.engine then misaligns outputs[j] -> IndexError. Our
    forward cannot raise (zero-score briefs), so the drops come from
    the adapter's own error absorption. Wrap the engine's
    _batch_evaluate: pad every returned EvaluationBatch to the true
    batch length with failure rows — alignment guaranteed, dropped
    rows count as failures (which they are)."""
    import gepa.core.engine as gepa_engine

    orig = gepa_engine.GEPAEngine._batch_evaluate

    def padded(self, items):
        batches = orig(self, items)
        out = []
        for (candidate, batch), eb in zip(items, batches):
            need = len(batch)
            if len(eb.outputs) < need:
                missing = need - len(eb.outputs)
                eb.outputs = list(eb.outputs) + [None] * missing
                eb.scores = list(eb.scores) + [0.0] * missing
                if eb.trajectories is not None:
                    eb.trajectories = (list(eb.trajectories)
                                       + [None] * missing)
                if eb.objective_scores is not None:
                    eb.objective_scores = (list(eb.objective_scores)
                                           + [{}] * missing)
            out.append(eb)
        return out

    gepa_engine.GEPAEngine._batch_evaluate = padded
    print("[gepa-patch] row-alignment guard installed")


def evaluate(director, valset, label):
    scores = []
    for ex in valset:
        pred = director(intent=ex.intent)
        scores.append(qc_feedback_metric(ex, pred))
    avg = sum(scores) / max(1, len(scores))
    print(f"[{label}] valset {len(valset)} examples -> {avg:.3f}")
    return avg


def main():
    trainset, valset = load_examples(REPO / "datasets" / "runs")
    print(f"dataset: {len(trainset)} train / {len(valset)} val")
    if not valset:
        valset = trainset  # tiny-data fallback; noted honestly

    wire_lm()
    _patch_gepa_row_alignment()

    # ── 1. baseline: LabeledFewShot, no optimization cost ──────────
    baseline = dspy.LabeledFewShot(k=min(4, len(trainset)))
    base_dir = baseline.compile(PromptDirector(),
                                trainset=trainset)
    base_score = evaluate(base_dir, valset, "baseline")
    Path(REPO / "compiled").mkdir(exist_ok=True)
    base_dir.save(str(REPO / "compiled" / "baseline_director.json"))

    # ── 2. GEPA (checkpoint hygiene per the skill) ────────────────
    import shutil
    ckpt = REPO / ".gepa_checkpoint_director"
    if ckpt.exists():
        shutil.rmtree(ckpt)
        print("[gepa] cleared stale checkpoint")

    gepa = dspy.GEPA(
        metric=qc_feedback_metric,
        # exactly ONE budget knob (auto XOR max_metric_calls);
        # 80 calls answers improved-vs-plateau in <1h at 40-55s/rollout
        max_metric_calls=80,
        reflection_lm=dspy.settings.lm,
        log_dir=str(ckpt),
        seed=42,
    )
    t0 = time.time()
    gepa_dir = gepa.compile(base_dir, trainset=trainset,
                            valset=valset)
    print(f"[gepa] compiled in {time.time()-t0:.0f}s")
    gepa_score = evaluate(gepa_dir, valset, "gepa")

    gepa_dir.save(str(REPO / "compiled" / "gepa_director.json"))

    # ── 3. verify learning by SIDE-BY-SIDE outputs, not just scores ──
    print("\n===== side-by-side (skill: identical scores can hide "
          "learning) =====")
    probe = "a kaiju silhouette rising through fog over a harbor city"
    b = base_dir(intent=probe).brief
    g = gepa_dir(intent=probe).brief
    for name, brief in (("baseline", b), ("gepa", g)):
        print(f"\n-- {name} --")
        print(f"  subject: {brief.subject[:100]}")
        print(f"  camera:  {brief.camera[:100]}")
        print(f"  audio:   {(brief.audio_direction or '(none)')[:80]}")
        print(f"  negs:    {(brief.negatives or '(none)')[:80]}")

    verdict = ("IMPROVED" if gepa_score > base_score
               else "PLATEAU/REGRESS — documented per AC #4")
    print(f"\nRESULT: baseline {base_score:.3f} -> gepa {gepa_score:.3f} "
          f"({verdict})")

    # ── 4. WD-k2ua: record + verify the scoring artifact ───────────
    blend = MetricBlend(section_weights=SectionWeights(
        weights={"subject": 0.3, "motion": 0.2, "camera": 0.2,
                 "style": 0.3}),
        qc_scale=1.0)
    artifact = record_scores(
        REPO / "compiled" / "metric_blend_scores.json",
        baseline=base_score, validation=gepa_score,
        blend=blend, n_val=len(valset))
    readback = load_scores(artifact)
    assert readback["blend_id"] == blend.blend_id, "readback mismatch"
    assert readback["baseline"] == base_score
    assert readback["validation"] == gepa_score
    print(f"[wd-k2ua] scoring artifact verified: {artifact} "
          f"(blend_id {blend.blend_id})")


if __name__ == "__main__":
    main()
