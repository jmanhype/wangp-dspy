"""PromptDirector — DSPy-native translation of user intent into
H3/WanGP render briefs (WD-tq6z).

Brief structure: exactly four sections (subject, motion, camera,
style). Editor meta-hints (cuts, transitions, beat grids, titles,
audio) are H3-SHOT territory per flux3 conventions and are FORBIDDEN
here — the module validates and rejects them.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass

import dspy


@dataclass(frozen=True)
class RenderBrief:
    """Structured H3/WanGP render brief. Four core sections + four
    craft sections (WD-mhr2 follow-up: the official H3 prompting guide
    — fal.ai/learn/devs/minimax-h3-prompting-guide — shows the model
    reads cinematography vocabulary directly and that audio direction,
    negative direction, and identity locks are high-leverage). Core
    sections nonempty; craft sections optional but validated when
    present; no editor meta-hints allowed."""
    subject: str
    motion: str
    camera: str
    style: str
    # craft extensions (H3 guide techniques 3,4,5): sound design,
    # what NOT to render, features that must survive the shot
    audio_direction: str = ""
    negatives: str = ""
    identity_lock: str = ""

    def __post_init__(self) -> None:
        for name in ("subject", "motion", "camera", "style"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"render brief section {name!r} must be a nonempty "
                    f"string, got {value!r}")
        _reject_meta_hints(self)


# Editor meta-hints live in H3 shots ONLY (flux3 convention). If one
# appears in a render brief the brief is wrong — reject loudly.
_META_HINT_RE = re.compile(
    r"\b(cut|cuts|transition\w*|dissolve|flash|beat\s*grid|B[\s-]*roll|"
    r"montage|sfx|VO|voice[\s-]*over|lower[\s-]*third|title\s*card)\b", re.I)


def _reject_meta_hints(brief: RenderBrief) -> None:
    for section in (brief.subject, brief.motion, brief.camera,
                    brief.style):
        m = _META_HINT_RE.search(section)
        if m:
            raise ValueError(
                f"editor meta-hint {m.group(0)!r} is forbidden in a "
                "render brief (belongs to H3 shots only)")
    # audio_direction legitimately DESCRIBES sound (that is its job);
    # it is exempt. It must still be a string when present.
    for field in ("audio_direction", "negatives", "identity_lock"):
        v = getattr(brief, field)
        if v is not None and not isinstance(v, str):
            raise ValueError(f"{field} must be a string, got {type(v)}")


class RenderBriefSignature(dspy.Signature):
    """Translate a user's video intent into a WanGP/H3 render brief.

    Output ONE JSON object with EXACTLY these keys:
      subject: what is on screen (entity, wardrobe, environment) —
               enumerate identity-defining details explicitly
      motion: how the subject moves within the shot (physical,
              specific: weight, drag, secondary motion like cloth
              and hair, water displacement)
      camera: REAL cinematography vocabulary — lens character
              (wide-angle distortion, long-lens compression), move
              (push, rack focus, orbit, handheld sway), framing,
              exposure behavior (backlit breathing, halation)
      style: film stock / palette / texture look (grain structure,
             highlight halation, color restraint, stock character)
      audio_direction: sound design the model generates natively —
               instrumentation/tone over time, specific sources
               (sub-bass pulse, fabric movement, room air)
      negatives: what NOT to render — "no soft dissolves or morphs,
               no tearing, no extra figures, no text artifacts"
      identity_lock: the features that MUST survive the whole shot,
               named concretely (wardrobe, colors, props, proportions)

    NEVER include editing meta-hints (cuts, transitions, montages,
    beat grids, titles) — those belong to H3 shot assembly, not to a
    render brief. Be SPECIFIC: lens, light, motion physics, texture.
    Output the JSON object only.
    """
    intent: str = dspy.InputField(desc="user's video intent, any form")
    brief: str = dspy.OutputField(
        desc="JSON object with keys subject, motion, camera, style, "
             "audio_direction, negatives, identity_lock")


class PromptDirector(dspy.ChainOfThought):
    """ChainOfThought module producing validated RenderBriefs."""

    def __init__(self):
        super().__init__(RenderBriefSignature)

    def forward(self, *args, **kwargs):  # pragma: no cover - thin
        out = super().forward(*args, **kwargs)
        brief = _parse_brief(out.brief)
        return dspy.Prediction(brief=brief)


def _parse_brief(raw: str) -> RenderBrief:
    try:
        doc = json.loads(raw)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ValueError(f"LM output is not valid JSON: {raw!r}") from exc
    if not isinstance(doc, dict):
        raise ValueError(f"brief JSON must be an object, got {doc!r}")
    missing = [k for k in ("subject", "motion", "camera", "style")
               if k not in doc]
    if missing:
        raise ValueError(f"brief JSON missing sections: {missing}")
    try:
        return RenderBrief(
            subject=str(doc["subject"]), motion=str(doc["motion"]),
            camera=str(doc["camera"]), style=str(doc["style"]),
            audio_direction=str(doc.get("audio_direction", "") or ""),
            negatives=str(doc.get("negatives", "") or ""),
            identity_lock=str(doc.get("identity_lock", "") or ""))
    except ValueError:
        raise
