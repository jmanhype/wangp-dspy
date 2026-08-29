"""Per-stage LM wiring — creative stages on a hosted API, critic on
the ear-calibrated local model.

WD-mhr2 prep. Before this, the pipeline had ONE dspy default LM for
everything (critic.py's configure_critic set the global). The live
setup wants:

- director/selector (creative): glm-5.3 via the z.ai coding-plan
  endpoint (OpenAI-compatible; live-tested 2026-08-24: 24/24 200s,
  zero 429s — Max plan budget ~1,600 prompts/5h vs ~10/cycle).
- RenderQC (judge): ollama_chat/q38u-v2 on the 3090 (127.0.0.1:11434
  via ssh tunnel) — the ear-calibrated critic; swapping it would
  invalidate that calibration.

Implementation: dspy.settings.context(lm=...) per stage — the
documented multi-model pattern; no globals are mutated.

GLM quirk (live-probed): completion budget is consumed by reasoning
tokens FIRST — max_tokens=10 returns empty content. Creative stages
get generous completion budgets.
"""
from __future__ import annotations

import os
from typing import Optional

import dspy

DEFAULT_CREATIVE_MODEL = "openai/glm-5.3"
DEFAULT_CREATIVE_BASE = "https://api.z.ai/api/coding/paas/v4"
# generous: GLM spends tokens on reasoning before content
# GLM spends completion budget on reasoning before emitting the JSON brief.
# 4096 truncated LabeledFewShot responses in the live WD-y9ab baseline.
CREATIVE_COMPLETION_TOKENS = 8192


class LMWiringError(Exception):
    """Typed failure for missing/invalid LM wiring (no guessed
    endpoints — critic.py's fail-closed discipline, applied here)."""


def creative_lm(model: str = DEFAULT_CREATIVE_MODEL, *,
                api_base: Optional[str] = None,
                api_key: Optional[str] = None,
                **lm_kwargs) -> dspy.LM:
    """The director/selector LM. Credentials come from explicit args
    or GLM_API_KEY/GLM_BASE_URL env (never hardcoded)."""
    base = (api_base or os.environ.get("GLM_BASE_URL")
            or DEFAULT_CREATIVE_BASE)
    key = api_key or os.environ.get("GLM_API_KEY")
    if not key:
        raise LMWiringError(
            "GLM_API_KEY not set and no api_key given — refusing to "
            "guess credentials (fail closed)")
    return dspy.LM(
        model, api_base=base, api_key=key,
        max_tokens=CREATIVE_COMPLETION_TOKENS, **lm_kwargs)


def run_creative(module_fn, lm: dspy.LM):
    """Run a director/selector call under the creative LM context."""
    with dspy.settings.context(lm=lm):
        return module_fn()
