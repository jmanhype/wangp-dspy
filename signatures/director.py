"""Director planner signatures — the three Maestro-port LLM pass
contracts, DSPy-native (follow-up to PR #54).

Each Signature's docstring carries the legacy `_PASS*_SYSTEM` prompt
VERBATIM (behavior must not change — golden tests pin this). The
output fields are strict-JSON strings; parsing/validation stays in
services/director/planners/short_film.py (typed PlannerError /
GridError discipline — the module, not the LM, owns the schema).
"""
import dspy


class ScreenplayBeats(dspy.Signature):
    """You are a screenwriter. Read the script and character list. Return STRICT JSON: {"beats": [{"index": int (1..N in order), "speaker": str (a character name), "text": str (the spoken line), "section": str}]}. One beat per spoken line. Creative and performance-focused."""
    script: str = dspy.InputField(desc="the screenplay text")
    characters: str = dspy.InputField(
        desc='JSON list of {"name": str, "description": str}')
    beats: str = dspy.OutputField(
        desc='STRICT JSON: {"beats": [{"index": int (1..N in order), '
             '"speaker": str (a character name), "text": str (the spoken '
             'line), "section": str}]} — one beat per spoken line')


class ShotBreakdown(dspy.Signature):
    """You are a shot-breakdown artist for a single-character-per-shot dialogue film. Input: screenplay beats, characters, plate paths (camera-facing master plates), audio guides with durations. Return STRICT JSON: {"shots": [{"index": int, "speaker": str, "dialogue_ref": str (guide key), "framing": "wide"|"medium-wide"|"medium", "movement": "static", "lighting": "bright"|"natural", "start_image_ref": str (plate path), "audio_guide_ref": {"path": str, "duration_s": float}, "duration_s": float (MUST equal the guide duration and be on the 5/22/39/56/73/90/107/...s grid), "section": str}]}."""
    beats: str = dspy.InputField(desc="JSON list of dialogue beats")
    characters: str = dspy.InputField(
        desc='JSON list of {"name": str, "plate": str|null}')
    plates: str = dspy.InputField(
        desc="camera-facing master plate paths by character")
    guides: str = dspy.InputField(
        desc='audio guides: {"key": {"path": str, "duration_s": float}}')
    duration_grid: str = dspy.InputField(
        desc="allowed shot durations in seconds (the 17k+5 grid)")
    shots: str = dspy.OutputField(
        desc='STRICT JSON: {"shots": [{"index": int, "speaker": str, '
             '"dialogue_ref": str (guide key), "framing": '
             '"wide"|"medium-wide"|"medium", "movement": "static", '
             '"lighting": "bright"|"natural", "start_image_ref": str '
             '(plate path), "audio_guide_ref": {"path": str, '
             '"duration_s": float}, "duration_s": float (MUST equal the '
             'guide duration and be on the 5/22/39/56/73/90/107/...s '
             'grid), "section": str}]}')


class ShotPolish(dspy.Signature):
    """You are a script doctor. Review the shot list for pacing, redundancy, and emotional arc. Return STRICT JSON: {"notes": str, "approved": bool}. Do NOT alter the shot structure."""
    beats: str = dspy.InputField(desc="JSON list of dialogue beats")
    shots: str = dspy.InputField(
        desc="JSON list of shot summaries for pacing review")
    notes: str = dspy.OutputField(
        desc='STRICT JSON: {"notes": str, "approved": bool} — do NOT '
             'alter the shot structure')


__all__ = ["ScreenplayBeats", "ShotBreakdown", "ShotPolish"]
