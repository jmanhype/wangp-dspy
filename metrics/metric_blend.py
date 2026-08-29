"""WD-k2ua — GEPA metric blend over RenderQC feedback.

Blend contract:
- Typed inputs: SectionWeights / MetricBlend dataclasses refuse bad
  weights (non-numeric, negative, not summing to ~1.0) with ValueError.
- Critique-weighted: each brief section's F1 is weighted by the
  RenderQC critique field it maps to (coherence, brief_adherence,
  concept_encoding), scaled by the gold run's REAL qc score — high-
  scoring golds teach harder, exactly as before but per-section.
- Artifacts: record_scores() writes a provenance-stamped JSON artifact
  (baseline + validation + blend id); readback via load_scores()
  round-trips byte-identically.
- No GPU rendering during optimization: the metric is pure logic.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

# Map brief sections -> RenderQC critique fields (the QC feedback the
# blend optimizes against; see evaluate/render_qc.py CRITIQUE_FIELDS).
SECTION_CRITIQUE_MAP = {
    "subject": "brief_adherence",
    "motion": "coherence",
    "camera": "coherence",
    "style": "concept_encoding",
}

CRITIQUE_FIELDS = ("coherence", "brief_adherence", "concept_encoding")


@dataclass(frozen=True)
class SectionWeights:
    """Typed per-section weights for the blend (must sum to 1.0)."""
    weights: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        unknown = set(self.weights) - set(SECTION_CRITIQUE_MAP)
        if unknown:
            raise ValueError(f"unknown sections {sorted(unknown)}; "
                             f"known: {sorted(SECTION_CRITIQUE_MAP)}")
        for sec, w in self.weights.items():
            if isinstance(w, bool) or not isinstance(w, (int, float)):
                raise ValueError(f"weight for {sec!r} must be numeric")
            if w < 0:
                raise ValueError(f"weight for {sec!r} must be >= 0")
        total = sum(self.weights.values())
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"weights must sum to 1.0, got {total}")


@dataclass(frozen=True)
class MetricBlend:
    """Typed record of one blend configuration — rides the artifact."""
    section_weights: SectionWeights
    qc_scale: float = 1.0  # multiplier from the gold's qc_score/10

    def __post_init__(self) -> None:
        if isinstance(self.qc_scale, bool) or \
                not isinstance(self.qc_scale, (int, float)) or \
                not 0.0 < self.qc_scale <= 1.0:
            raise ValueError(
                f"qc_scale must be in (0, 1], got {self.qc_scale!r}")

    @property
    def blend_id(self) -> str:
        import hashlib
        payload = json.dumps(
            {"weights": self.section_weights.weights,
             "qc_scale": self.qc_scale},
            sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode()).hexdigest()[:16]


def blended_score(f1s: dict, critique: dict, blend: MetricBlend) -> float:
    """Combine per-section F1s, critique-weighted and QC-scaled.

    f1s: section -> F1 in [0,1]. critique: critique field -> score
    0-10 (RenderQC vocabulary). Sections missing from f1s count 0.0.
    """
    w = blend.section_weights.weights
    if not w:
        raise ValueError("blend carries no section weights")
    total = 0.0
    for sec, weight in w.items():
        cf = SECTION_CRITIQUE_MAP[sec]
        critique_norm = float(critique.get(cf, 5.0)) / 10.0
        total += weight * f1s.get(sec, 0.0) * critique_norm
    return total * blend.qc_scale


def record_scores(path: Path, baseline: float, validation: float,
                  blend: MetricBlend, n_val: int,
                  story: str = "WD-k2ua") -> Path:
    """Write the provenance-stamped scoring artifact (deterministic)."""
    artifact = {
        "baseline": baseline,
        "validation": validation,
        "n_val": n_val,
        "blend_id": blend.blend_id,
        "blend": {"weights": blend.section_weights.weights,
                  "qc_scale": blend.qc_scale},
        "story": story,
    }
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(artifact, sort_keys=True, indent=2) + "\n")
    return path


def load_scores(path: Path) -> dict:
    """Read back a scoring artifact (compile/readback verification)."""
    return json.loads(Path(path).read_text())
