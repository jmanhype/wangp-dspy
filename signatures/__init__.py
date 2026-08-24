"""DSPy Signature layer — I/O contracts, separate from module logic.

Per repo-structure research (2026-08-24): every real-world DSPy app
layout separates signatures (the declarative contracts) from modules
(the logic that consumes them) — dspy-cli makes this a REQUIRED
directory; upstream dspy keeps signatures/ as its own layer. GEPA's
per-predictor optimization (j9nx-4) targets signature-bearing
predictors, so contracts live here, once.
"""
from signatures.profile import ProfileSelectorSignature
from signatures.qc import RenderQCSignature

__all__ = ["ProfileSelectorSignature", "RenderQCSignature"]
