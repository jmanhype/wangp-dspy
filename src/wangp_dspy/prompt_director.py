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
    """Structured H3/WanGP render brief. Exactly four sections; every
    section nonempty; no editor meta-hints allowed."""
    subject: str
    motion: str
    camera: str
    style: str

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
    r"\b(cut|cuts|transition\w*|dissolve|flash|beat\s*grid|B[\s-]?roll|"
    r"montage|sfx|VO|voice[\s-]?over|lower[\s-]?third|title\s*card)\b", re.I)


def _reject_meta_hints(brief: RenderBrief) -> None:
    for section in (brief.subject, brief.motion, brief.camera,
                    brief.style):
        m = _META_HINT_RE.search(section)
        if m:
            raise ValueError(
                f"editor meta-hint {m.group(0)!r} is forbidden in a "
                "render brief (belongs to H3 shots only)")


class RenderBriefSignature(dspy.Signature):
    """Translate a user's video intent into a WanGP/H3 render brief.

    Output ONE JSON object with EXACTLY these keys:
      subject: what is on screen (entity, wardrobe, environment)
      motion: how the subject moves within the shot
      camera: camera movement, framing, frame rate character
      style: film stock / palette / texture look

    NEVER include editing meta-hints (cuts, transitions, montages,
    beat grids, titles, sound) — those belong to H3 shot assembly, not
    to a render brief. Output the JSON object only.
    """
    intent: str = dspy.InputField(desc="user's video intent, any form")
    brief: str = dspy.OutputField(
        desc="JSON object with keys subject, motion, camera, style")


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
            camera=str(doc["camera"]), style=str(doc["style"]))
    except ValueError:
        raise
