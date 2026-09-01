"""H3-Ref2VA renderer — ShotPlan -> validated gated job config.

THE key adaptation of the Maestro Director renderer pattern: instead
of emitting LTX prompt strings, we emit OUR verified gated job config:
(a) the prompt in predict/subject_prompt.py's Ref2VA subject-mode
format via build_subject_prompt (PR #52 — reused, not duplicated);
(b) audio_prompt_type 'A', video_prompt_type 'I', multi_prompts_gen_type
'FG', guide sliced to the exact shot duration; (c) renderer policy as
typed rejections (facing / framing / 17k+5 grid / guide==shot).
"""
from __future__ import annotations

from typing import Any, Dict

from predict.subject_prompt import (
    SceneCast,
    SpeakerLine,
    SubjectSpec,
    build_subject_prompt,
)
from services.director.schema import (
    CameraPlan,
    CharacterProfile,
    ProductionPlan,
    ShotPlan,
)
from services.director.renderers.policy import (
    FacingError,
    FramingError,
    GridError,
    GuideDurationError,
    check_duration_on_grid,
    check_facing,
    check_framing,
    check_guide_duration,
)


class H3Ref2VARenderer:
    """Renders one ShotPlan into an emission-only job-config dict."""

    name = "h3_ref2va"

    def render(self, plan: ProductionPlan, shot: ShotPlan) -> Dict[str, Any]:
        chars = {c.name: c for c in plan.characters}
        speaker = chars.get(shot.speaker)
        if speaker is None:
            raise FacingError(
                f"shot {shot.index}: speaker {shot.speaker!r} has no "
                "CharacterProfile in the plan")

        # (c) renderer policy — typed rejections, checked in order.
        frames = check_duration_on_grid(shot.duration_s)
        check_guide_duration(shot.audio_guide_ref["duration_s"],
                             shot.duration_s)
        check_facing(shot.start_image_ref, speaker.facing_requirement)
        check_framing(shot.camera_plan.framing, shot.camera_plan.lighting)

        # (a) subject-mode prompt via the PR #52 builder.
        prompt = self._build_prompt(plan, shot, speaker)

        # (b) job config.
        guide = shot.audio_guide_ref
        return {
            "shot_index": shot.index,
            "film_id": plan.film_id,
            "speaker": shot.speaker,
            "section": shot.section,
            "prompt": prompt,
            "video_prompt_type": "I",
            "audio_prompt_type": "A",
            "multi_prompts_gen_type": "FG",
            "image_refs": [shot.start_image_ref],
            "audio_guide": guide["path"],
            "guide_slice": {
                "start_s": 0.0,
                "end_s": float(shot.duration_s),
                "duration_s": float(shot.duration_s),
            },
            "shot_duration_s": float(shot.duration_s),
            "frames": frames,
            "fps": 24,
            "camera_plan": {
                "framing": shot.camera_plan.framing,
                "movement": shot.camera_plan.movement,
                "lighting": shot.camera_plan.lighting,
            },
        }

    # ── prompt assembly (delegates to build_subject_prompt) ─────────

    def _build_prompt(self, plan: ProductionPlan, shot: ShotPlan,
                      speaker: CharacterProfile) -> str:
        subjects = []
        # environment subject is the first non-speaking entry when the
        # shot has a distinct location; single-character shots keep it
        # simple: the speaker is subject 1.
        subj_id = 1
        subjects.append(SubjectSpec(
            subject_id=subj_id,
            name=speaker.name,
            description=speaker.description,
            is_speaker=True,
            ambient_actions=self._ambient(shot.camera_plan),
        ))
        for c in plan.characters:
            if c.name == shot.speaker:
                continue
            subj_id += 1
            subjects.append(SubjectSpec(
                subject_id=subj_id,
                name=c.name,
                description=c.description,
                is_speaker=False,
                ambient_actions="listens attentively, gaze on the speaker",
            ))
        cast = SceneCast(
            subjects=tuple(subjects),
            style="Photorealistic cinematic film look, natural color, "
                  "subtle film grain",
            shot_description=(
                f"[Shot 1] {shot.camera_plan.framing} framing, "
                f"{shot.camera_plan.lighting} lighting, "
                f"{shot.camera_plan.movement} camera; all subjects hold "
                "their exact identities and positions from <Picture 1>"),
            soundscape="Room tone with the speaker's voice prominent",
            music="N/A",
        )
        line = SpeakerLine(
            subject_id=1,
            text=self._dialogue_text(shot),
            language="English",
        )
        return build_subject_prompt(cast, line)

    @staticmethod
    def _ambient(cam: CameraPlan) -> str:
        return (f"holds {cam.framing} position with natural micro-motion "
                "and blinks")

    @staticmethod
    def _dialogue_text(shot: ShotPlan) -> str:
        # dialogue_ref is a key the caller resolves; for emission the
        # literal ref text is bound at plan time — use the ref verbatim
        # (planner pass 1 binds real text into refs like 'd1').
        return shot.dialogue_ref


def render_shot(plan: ProductionPlan, shot: ShotPlan) -> Dict[str, Any]:
    """Convenience functional entry point."""
    return H3Ref2VARenderer().render(plan, shot)


__all__ = [
    "H3Ref2VARenderer", "render_shot", "FacingError", "FramingError",
    "GridError", "GuideDurationError",
]
