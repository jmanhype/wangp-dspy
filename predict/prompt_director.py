"""PromptDirector — DSPy-native translation of user intent into
H3/WanGP render briefs (WD-tq6z).

Brief structure: exactly four sections (subject, motion, camera,
style). Editor meta-hints (cuts, transitions, beat grids, titles,
audio) are H3-SHOT territory per flux3 conventions and are FORBIDDEN
here — the module validates and rejects them.
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass

import dspy

logger = logging.getLogger(__name__)


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
    # no-proper-nouns gate (ADOPT, no-names-doctrine.md): registry of
    # named entities; None = no registry available -> gate skipped
    # LOUDLY (warning), never silently (doctrine: missing --cast skips
    # loudly). Default None keeps backward compat for LM-brief paths
    # that have no bible context.
    registry: dict | None = None
    # provenance tiers (ADOPT WD-oyti, inferred-marker-convention.md):
    # canon citations backing the identity claims in this brief.
    # None/empty = no citation context -> every identity claim must
    # carry exactly one (inferred) marker; markers are stripped at
    # brief_to_prompt() so they never reach a render prompt.
    canon_citations: tuple | list | None = None

    def __post_init__(self) -> None:
        for name in ("subject", "motion", "camera", "style"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"render brief section {name!r} must be a nonempty "
                    f"string, got {value!r}")
        _reject_meta_hints(self)
        _reject_registry_names(self)
        _reject_risky_actions(self)
        _reject_non_english_engine_fields(self)
        _reject_unmarked_provenance(self)


# Editor meta-hints live in H3 shots ONLY (flux3 convention). If one
# appears in a render brief the brief is wrong — reject loudly.
# WD-9dia: bare tokens 'cut'/'cuts'/'flash' over-triggered on lighting
# vocabulary (muzzle flash, lightning flash, light cut) in aesthetic
# briefs. Industry-standard fix for word-sense ambiguity in blocklists
# (the Scunthorpe class): match editing OPERATIONS as phrase patterns,
# never bare ambiguous nouns. Unambiguous terms (dissolve, montage,
# lower third...) stay as tokens.
_META_HINT_RE = re.compile(
    r"\b("
    r"(?:hard|jump|smash|flash|match|ax|cross)\s+cuts?\b"  # cut TYPES
    r"|cuts?\s+(?:to|between|away|back)\b"                 # cut VERBS
    r"|cutting\s+(?:to|between|away|back)\b"
    r"|transition\w*"                                       # unambiguous
    r"|dissolve"
    r"|flash\s+(?:cut|frame|transition|forward)\b"          # flash+edit
    r"|beat\s*grid|B[\s-]*roll"
    r"|montage|sfx|VO|voice[\s-]*over|lower[\s-]*third|title\s*card"
    r")\b", re.I)

# lighting/cinematography contexts where remaining ambiguous tokens are
# legitimate (belt-and-suspenders; the phrase patterns above already
# avoid most false fires)
_LIGHTING_CONTEXT_RE = re.compile(
    r"\b(flash(?:es|ing)?\s+(?:of\s+)?(?:light|lightning|muzzle|strobe)"
    r"|light(?:ing)?\s+(?:flash|cut)|flash\s+exposure|strobe\s+flash"
    r"|exposure\s+flash)\b", re.I)


def _reject_registry_names(brief: "RenderBrief") -> None:
    """No-proper-nouns gate (ADOPT, no-names-doctrine.md): named
    entities (characters, aliases, places, IP) from the entity
    registry are forbidden in render briefs — image models draw their
    memorized version of the name. Same typed-failure pattern as the
    meta-hint guard. No registry -> LOUD skip, never silent."""
    if brief.registry is None:
        logger.warning(
            "no-names gate SKIPPED: no entity registry provided "
            "(pass registry=... — load via gates.load_registry)")
        return
    from gates.no_names_gate import check_no_proper_nouns
    for field in ("subject", "motion", "camera", "style",
                  "audio_direction", "negatives", "identity_lock"):
        v = getattr(brief, field) or ""
        for viol in check_no_proper_nouns(v, brief.registry):
            raise ValueError(
                f"proper noun {viol.matched_name!r} (entity "
                f"{viol.canonical_name!r}) is forbidden in render brief "
                f"section {field!r} — image models bias toward their "
                "memorized version of named entities "
                "(no-names-doctrine.md); describe the entity instead")


def _reject_risky_actions(brief: "RenderBrief") -> None:
    """Common-actions gate (ADOPT, WD-7185: script-pass L10-18 +
    RUBRIC A4.2): video models only act what they've seen millions
    of times — precise physics interaction, micro-expression
    direction, and inch-scale displacement produce mush. ALWAYS
    ACTIVE (patterns are bundled in datasets/common-actions.json;
    no per-production registry, hence no registry=None skip —
    documented decision). Same typed-failure pattern as the
    meta-hint and no-names guards."""
    from gates.common_actions import check_common_actions
    for field in ("subject", "motion", "camera", "style",
                  "audio_direction", "negatives", "identity_lock"):
        v = getattr(brief, field) or ""
        if not v:
            continue
        for viol in check_common_actions(v):
            raise ValueError(
                f"risky action {viol.matched_text!r} (pattern "
                f"{viol.id!r}, category {viol.category}) in render "
                f"brief section {field!r} — not a common real-life-"
                "video action; rewrite the beat as something the "
                "model has seen millions of times "
                "(common-actions doctrine, docs/common-actions.md)")


def _reject_non_english_engine_fields(brief: "RenderBrief") -> None:
    """Language-class gate (ADOPT WD-c4gw: language-split-contract.md
    — profile-pass.md:16): ALL RenderBrief sections are ENGINE-BOUND
    prompt fragments — LOCKED ENGLISH. Same typed-failure path as
    the meta-hint/no-names/actions guards."""
    from gates.language_gate import (check_language_class,
                                     LanguageGateError,
                                     FIELD_CLASSES)
    classes = FIELD_CLASSES["RenderBrief"]
    for field in ("subject", "motion", "camera", "style",
                  "audio_direction", "negatives", "identity_lock"):
        v = getattr(brief, field) or ""
        if not v:
            continue
        try:
            violations = check_language_class(
                v, field_class=classes[field])
        except LanguageGateError:
            continue
        if violations:
            raise ValueError(
                f"engine-bound brief section {field!r} contains "
                f"{violations[0].matched_text} — engine fields are "
                "LOCKED ENGLISH (language-split-contract.md, "
                "profile-pass.md:16); rewrite in English")


def _reject_unmarked_provenance(brief: "RenderBrief") -> None:
    """Provenance-tier gate (ADOPT WD-oyti: inferred-marker-convention.md
    — profile-pass.md:24/42-44): identity claims in the brief carry
    exactly one provenance tier — a canon citation OR one (inferred)
    marker. No unmarked middle ground, no double-marking.

    Scope: identity_lock is the brief's identity surface (the render
    prompt fragment that must survive the shot). subject/motion/
    camera/style are scene direction, not identity claims — they stay
    out of scope (documented decision; the extraction's rule 1 targets
    persona.appearance / persona.identity specifically).

    - canon_citations provided (nonempty): the brief's identity claims
      are canon-grounded; an (inferred) marker on top is redundant
      double-tiering -> reject.
    - no citations: every identity claim in identity_lock must carry
      exactly one (inferred) marker. Empty identity_lock = no identity
      claims = nothing to tier (loud skip, same pattern as the
      no-names registry=None skip).

    The markers themselves are STRIPPED at brief_to_prompt() — this
    gate only tiers; it never lets a marker into a prompt.
    """
    from gates.provenance_gate import (check_provenance_tier,
                                       ProvenanceGateError)
    lock = (brief.identity_lock or "").strip()
    if not lock:
        return  # no identity claims in this brief — nothing to tier
    has_citation = bool(brief.canon_citations)
    try:
        violations = check_provenance_tier(
            lock, field="identity_lock",
            has_canon_citation=has_citation)
    except ProvenanceGateError:
        return
    for viol in violations:
        raise ValueError(
            f"provenance violation in render brief section "
            f"{viol.field!r}: {viol.reason} "
            "(inferred-marker-convention.md)")


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

    LANGUAGE-CLASS CONTRACT (WD-c4gw, language-split-contract.md):
    EVERY output field (subject, motion, camera, style,
    audio_direction, negatives, identity_lock) is ENGINE-BOUND —
    LOCKED ENGLISH (profile-pass.md:16: 机器字段不跟随 lang). The
    brief feeds the WanGP render prompt verbatim; non-English
    content is rejected by gates/language_gate.py.
    """
    intent: str = dspy.InputField(desc="user's video intent, any form")
    brief: str = dspy.OutputField(
        desc="JSON object with keys subject, motion, camera, style, "
             "audio_direction, negatives, identity_lock")


class PromptDirector(dspy.ChainOfThought):
    """ChainOfThought module producing validated RenderBriefs.

    WD-txt9 live finding: GEPA's batch executor drops the output row
    for a candidate whose forward RAISES (json parse failure, meta-hint
    rejection), misaligning outputs[j] -> IndexError in the engine.
    Optimization must see failures as ZERO-SCORE predictions, never
    exceptions — same discipline as Evaluate's failure_score."""

    def __init__(self):
        super().__init__(RenderBriefSignature)

    def forward(self, *args, **kwargs):
        # WD-c4gw registry fold-in: pop BEFORE super() — dspy's
        # forward does not understand registry; missing registry =
        # LOUD skip (warning), never silent.
        registry = kwargs.pop("registry", None)
        if registry is None:
            import logging as _lg
            _lg.getLogger(__name__).warning(
                "no-names gate SKIPPED on LM path: no entity registry "
                "provided to PromptDirector.forward (pass registry=... "
                "— load via gates.load_registry)")
        try:
            out = super().forward(*args, **kwargs)
        except Exception as exc:
            # WD-txt9: GEPA's Evaluate fallback DROPS rows for raising
            # calls (res.results shorter than devset -> outputs[j]
            # IndexError in gepa.engine). Any LM/adaptation failure on
            # a mutated candidate becomes a zero-score brief so the
            # batch stays aligned and the optimizer sees the failure.
            brief = RenderBrief(
                subject=f"(lm failure: {type(exc).__name__}: "
                        f"{str(exc)[:60]})",
                motion="", camera="", style="")
            return dspy.Prediction(brief=brief)
        try:
            brief = _parse_brief(out.brief, registry=registry)
        except (ValueError, TypeError, KeyError) as exc:
            # WD-c4gw: gate rejections (registry names, risky
            # actions, language) raise ValueError INSIDE
            # RenderBrief.__post_init__ — those must surface, not be
            # masked by a fallback that itself fails validation.
            if "proper noun" in str(exc) or "risky action" in str(exc) \
                    or "engine-bound" in str(exc):
                raise
            brief = RenderBrief(
                subject=f"(invalid brief: {str(exc)[:80]})",
                motion="(invalid)", camera="(invalid)",
                style="(invalid)")
        return dspy.Prediction(brief=brief)


def _parse_brief(raw: str,
                 registry: dict | None = None) -> RenderBrief:
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
            identity_lock=str(doc.get("identity_lock", "") or ""),
            registry=registry)
    except ValueError:
        raise
