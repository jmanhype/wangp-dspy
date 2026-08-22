"""Production critic wiring for RenderQC (WD-t6i7 wiring slice).

The ONLY place a real LM endpoint enters the pipeline. Injectable and
typed: the LM class is module-level (``_lm_cls``) so tests stub it; no
endpoint is hardcoded in the adapter or RenderQC — the caller passes
api_base (the T0 runbook tunnels 127.0.0.1:11434 on the 3090 to
localhost). Fails closed: empty/invalid model or api_base is a typed
ValueError, never a guessed default endpoint.
"""
from __future__ import annotations

import dspy

DEFAULT_CRITIC_MODEL = "ollama_chat/q38u-v2"

# injectable seam: tests monkeypatch this to a fake LM class
_lm_cls = dspy.LM

_configured: dspy.LM | None = None


def _require_url(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("api_base is required (no default endpoint)")
    v = value.strip()
    if not (v.startswith("http://") or v.startswith("https://")):
        raise ValueError("api_base must be an http(s) URL")
    return v


def configure_critic(model: str = DEFAULT_CRITIC_MODEL, *,
                     api_base: str,
                     timeout_secs: float = 60.0,
                     **lm_kwargs) -> dspy.LM:
    """Construct the critic LM and wire it as the dspy default.

    Returns the LM instance; ``critic_lm()`` exposes the same object
    afterwards. Typed ValueError on empty/invalid model, api_base, or
    timeout. No live call happens here — construction only.
    """
    global _configured
    if not isinstance(model, str) or not model.strip():
        raise ValueError("model must be a nonempty string")
    api_base = _require_url(api_base)
    if not isinstance(timeout_secs, (int, float)) \
            or isinstance(timeout_secs, bool) or timeout_secs <= 0:
        raise ValueError("timeout_secs must be a positive number")
    lm = _lm_cls(model, api_base=api_base,
                 timeout=float(timeout_secs), **lm_kwargs)
    dspy.configure(lm=lm)
    _configured = lm
    return lm


def critic_lm() -> dspy.LM | None:
    """The configured critic LM, or None before configure_critic."""
    return _configured
