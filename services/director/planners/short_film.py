"""Short-film planner — DSPy-native 3-pass module with a legacy shim.

Pattern reimplemented from Maestro's planners/short_film.py (WanGP NCE
1.1; see docs/render-knowledge/maestro-port.md). Pass 1: creative
screenplay beats from script + characters. Pass 2: structured shot
breakdown to ShotPlan JSON (validated + policy-checked). Pass 3:
polish notes.

Follow-up to PR #54: the three passes are now proper dspy.Signatures
(signatures/director.py) composed as a dspy.Module with NAMED
predictors (self.pass_beats / self.pass_shots / self.pass_polish) so
GEPA/teleprompt optimizers can target them per-predictor later. LLM
selection is the caller's job — wrap the call in
`predict.lm_wiring.run_creative(...)` or `dspy.settings.context(lm=...)`;
this module has NO endpoints of its own.

Back-compat shim: the injected-callable constructor
`ShortFilmPlanner(llm=callable)` still works unchanged (same system
prompts, same call order) — existing tests pass as-is. Passing the
`DSPY_LLM` sentinel switches the passes to the Signature path.

Deterministic given the same LLM responses (same input -> same
prompts -> same parsed plan; no time/random/ordering deps). The
golden test pins that both paths produce identical ProductionPlans.
"""
from __future__ import annotations

import json
from typing import Callable, Dict, List, Sequence, Tuple

import dspy

from services.director.schema import (
    CameraPlan,
    CharacterProfile,
    DialogueBeat,
    ProductionPlan,
    SchemaError,
    ShotPlan,
)
from services.director.renderers.policy import check_duration_on_grid
from signatures.director import ScreenplayBeats, ShotBreakdown, ShotPolish

LLM = Callable[[str, str, str], str]

_PASS1_SYSTEM = (
    "You are a screenwriter. Read the script and character list. "
    "Return STRICT JSON: {\"beats\": [{\"index\": int (1..N in order), "
    "\"speaker\": str (a character name), \"text\": str (the spoken "
    "line), \"section\": str}]}. One beat per spoken line. Creative and "
    "performance-focused.")

_PASS2_SYSTEM = (
    "You are a shot-breakdown artist for a single-character-per-shot "
    "dialogue film. Input: screenplay beats, characters, plate paths "
    "(camera-facing master plates), audio guides with durations. "
    "Return STRICT JSON: {\"shots\": [{\"index\": int, \"speaker\": str, "
    "\"dialogue_ref\": str (guide key), \"framing\": \"wide\"|"
    "\"medium-wide\"|\"medium\", \"movement\": \"static\", \"lighting\": "
    "\"bright\"|\"natural\", \"start_image_ref\": str (plate path), "
    "\"audio_guide_ref\": {\"path\": str, \"duration_s\": float}, "
    "\"duration_s\": float (MUST equal the guide duration and be on "
    "the 5/22/39/56/73/90/107/...s grid), \"section\": str}]}.")

_PASS3_SYSTEM = (
    "You are a script doctor. Review the shot list for pacing, "
    "redundancy, and emotional arc. Return STRICT JSON: {\"notes\": "
    "str, \"approved\": bool}. Do NOT alter the shot structure.")


class PlannerError(ValueError):
    """Typed planner failure (bad LLM output, unresolvable refs)."""


class _DspyLMSentinel:
    """Sentinel: route the three passes through the named dspy
    predictors (Signature path) using the ambient dspy.settings LM."""

    def __repr__(self) -> str:  # pragma: no cover - cosmetic
        return "DSPY_LLM (use dspy.settings.context / run_creative)"


DSPY_LLM = _DspyLMSentinel()

# signature field carrying each pass's strict-JSON output
_PASS_OUT_FIELD = {"pass1": "beats", "pass2": "shots", "pass3": "notes"}


class ShortFilmPlanner(dspy.Module):
    """3-pass planner: beats -> shots -> polish.

    A dspy.Module composing the three Maestro-port passes as NAMED
    predictors (GEPA readiness — teleprompt/GEPA can target
    self.pass_beats / self.pass_shots / self.pass_polish individually;
    we do NOT run optimizers here). The LLM is injected either as a
    legacy callable `llm(pass_tag, system, user) -> str` or as the
    DSPY_LLM sentinel (Signature path under the ambient
    dspy.settings LM — wire it with predict.lm_wiring.run_creative
    or dspy.settings.context at the call site).
    """

    def __init__(self, *, llm: LLM) -> None:
        super().__init__()
        if llm is DSPY_LLM:
            pass  # Signature path — validated by construction
        elif not callable(llm):
            raise TypeError("llm must be a callable "
                            "(pass_tag, system, user) -> str")
        self._llm = llm
        # Named submodules — per-predictor optimization targets
        self.pass_beats = dspy.Predict(ScreenplayBeats)
        self.pass_shots = dspy.Predict(ShotBreakdown)
        self.pass_polish = dspy.Predict(ShotPolish)

    # ── public ───────────────────────────────────────────────────────

    def forward(self, script: str,
                characters: Sequence[CharacterProfile],
                plate_paths: Dict[str, str],
                guide_paths: Dict[str, Tuple[str, float]],
                film_id: str = "film") -> ProductionPlan:
        return self.plan(script, characters, plate_paths, guide_paths,
                         film_id=film_id)

    def plan(self, script: str, characters: Sequence[CharacterProfile],
             plate_paths: Dict[str, str],
             guide_paths: Dict[str, Tuple[str, float]],
             film_id: str = "film") -> ProductionPlan:
        beats = self._pass1(script, characters)
        shots = self._pass2(beats, characters, plate_paths, guide_paths)
        self._pass3(beats, shots)
        return ProductionPlan(film_id=film_id,
                              characters=tuple(characters),
                              shots=tuple(shots))

    # ── passes ───────────────────────────────────────────────────────

    def _pass1(self, script, characters) -> List[DialogueBeat]:
        payload = {
            "script": script,
            "characters": [{"name": c.name, "description": c.description}
                           for c in characters],
        }
        user = json.dumps(payload)
        fields = {"script": script,
                  "characters": json.dumps(payload["characters"])}
        doc = self._call("pass1", _PASS1_SYSTEM, user, fields=fields,
                         predictor=self.pass_beats)
        beats = []
        for b in doc.get("beats", []):
            try:
                beats.append(DialogueBeat(
                    index=b["index"], speaker=b["speaker"],
                    text=b["text"], section=b.get("section", "main")))
            except (KeyError, SchemaError) as e:
                raise PlannerError(f"pass1 produced an invalid beat: {e}")
        if not beats:
            raise PlannerError("pass1 produced no beats")
        return beats

    def _pass2(self, beats, characters, plate_paths,
               guide_paths) -> List[ShotPlan]:
        user = json.dumps({
            "beats": [b.__dict__ for b in beats],
            "characters": [{"name": c.name, "plate": plate_paths.get(c.name)}
                           for c in characters],
            "guides": {k: {"path": v[0], "duration_s": v[1]}
                       for k, v in guide_paths.items()},
            "duration_grid_s": [5, 22, 39, 56, 73, 90, 107, 124, 141],
        })
        fields = {
            "beats": json.dumps([b.__dict__ for b in beats]),
            "characters": json.dumps(
                [{"name": c.name, "plate": plate_paths.get(c.name)}
                 for c in characters]),
            "plates": json.dumps(plate_paths),
            "guides": json.dumps({k: {"path": v[0], "duration_s": v[1]}
                                  for k, v in guide_paths.items()}),
            "duration_grid": json.dumps(
                [5, 22, 39, 56, 73, 90, 107, 124, 141]),
        }
        doc = self._call("pass2", _PASS2_SYSTEM, user, fields=fields,
                         predictor=self.pass_shots)
        shots: List[ShotPlan] = []
        for i, s in enumerate(doc.get("shots", []), 1):
            try:
                # Resolve refs against the trusted local mappings —
                # never trust LLM-supplied paths directly.
                plate = plate_paths.get(s.get("speaker"))
                if not plate:
                    raise PlannerError(
                        f"shot {i}: no plate for speaker "
                        f"{s.get('speaker')!r}")
                g = guide_paths.get(s.get("dialogue_ref"))
                if g is None:
                    raise PlannerError(
                        f"shot {i}: unknown dialogue_ref "
                        f"{s.get('dialogue_ref')!r}")
                dur = self._snap_duration(s.get("duration_s", g[1]))
                shot = ShotPlan(
                    index=i,
                    speaker=s["speaker"],
                    dialogue_ref=s["dialogue_ref"],
                    camera_plan=CameraPlan(
                        framing=s.get("framing", "wide"),
                        movement=s.get("movement", "static"),
                        lighting=s.get("lighting", "bright")),
                    start_image_ref=plate,
                    audio_guide_ref={"path": g[0], "duration_s": g[1]},
                    duration_s=dur,
                    section=s.get("section", "main"),
                )
                # fail fast on off-grid (typed) even before the renderer
                check_duration_on_grid(shot.duration_s)
                shots.append(shot)
            except (KeyError, SchemaError) as e:
                raise PlannerError(f"pass2 produced an invalid shot: {e}")
        if not shots:
            raise PlannerError("pass2 produced no shots")
        return shots

    def _pass3(self, beats, shots) -> dict:
        user = json.dumps({
            "beats": [b.__dict__ for b in beats],
            "shots": [
                {"index": s.index, "speaker": s.speaker,
                 "duration_s": s.duration_s, "section": s.section}
                for s in shots],
        })
        fields = {"beats": json.dumps([b.__dict__ for b in beats]),
                  "shots": json.dumps(
                      [{"index": s.index, "speaker": s.speaker,
                        "duration_s": s.duration_s, "section": s.section}
                       for s in shots])}
        return self._call("pass3", _PASS3_SYSTEM, user, fields=fields,
                          predictor=self.pass_polish)

    # ── helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _snap_duration(d) -> float:
        """Validate a proposed duration against the 17k+5 grid.

        A tiny float tolerance (1e-6) is absorbed; anything genuinely
        off-grid raises the typed GridError so the caller sees the
        rejection rather than a silently moved cut.
        """
        try:
            d = float(d)
        except (TypeError, ValueError):
            raise PlannerError(f"non-numeric duration {d!r}")
        from services.director.renderers.policy import check_duration_on_grid
        # d is seconds; validate then snap to the exact grid frame count
        frames = check_duration_on_grid(d, fps=24)
        return frames / 24.0

    def _call(self, tag: str, system: str, user: str, *, fields,
              predictor) -> dict:
        """One LLM round-trip: legacy callable (verbatim system/user)
        or the Signature path (named predictor under the ambient
        dspy LM — never an endpoint of our own)."""
        if self._llm is DSPY_LLM:
            pred = predictor(**fields)
            raw = getattr(pred, _PASS_OUT_FIELD[tag])
        else:
            raw = self._llm(tag, system, user)
        try:
            return json.loads(raw)
        except ValueError as e:
            raise PlannerError(
                f"{tag} LLM returned non-JSON output: {e}") from e


__all__ = ["ShortFilmPlanner", "PlannerError", "DSPY_LLM"]
