"""Short-film planner — 3-pass LLM pipeline with INJECTED callables.

Pattern reimplemented from Maestro's planners/short_film.py (WanGP NCE
1.1; see docs/render-knowledge/maestro-port.md). Pass 1: creative
screenplay beats from script + characters. Pass 2: structured shot
breakdown to ShotPlan JSON (validated + policy-checked). Pass 3:
polish notes. The LLM is a required injected callable
`llm(pass_tag, system, user) -> str` — no hard-coded endpoint; tests
use fakes. Deterministic given the same LLM responses (same input ->
same prompts -> same parsed plan; no time/random/ordering deps).
"""
from __future__ import annotations

import json
from typing import Callable, Dict, List, Sequence, Tuple

from services.director.schema import (
    CameraPlan,
    CharacterProfile,
    DialogueBeat,
    ProductionPlan,
    SchemaError,
    ShotPlan,
)
from services.director.renderers.policy import check_duration_on_grid

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


class ShortFilmPlanner:
    """3-pass planner: beats -> shots -> polish."""

    def __init__(self, *, llm: LLM) -> None:
        if not callable(llm):
            raise TypeError("llm must be a callable "
                            "(pass_tag, system, user) -> str")
        self._llm = llm

    # ── public ───────────────────────────────────────────────────────

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
        user = json.dumps({
            "script": script,
            "characters": [{"name": c.name, "description": c.description}
                           for c in characters],
        })
        doc = self._call("pass1", _PASS1_SYSTEM, user)
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
        doc = self._call("pass2", _PASS2_SYSTEM, user)
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
        return self._call("pass3", _PASS3_SYSTEM, user)

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
        check_duration_on_grid(d)
        return d

    def _call(self, tag: str, system: str, user: str) -> dict:
        raw = self._llm(tag, system, user)
        try:
            return json.loads(raw)
        except ValueError as e:
            raise PlannerError(
                f"{tag} LLM returned non-JSON output: {e}") from e


__all__ = ["ShortFilmPlanner", "PlannerError"]
