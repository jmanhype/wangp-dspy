"""FL2VA keyframe targets + the R2I pose-target step.

Contract sources (scraped 2026-09-01; see docs/fl2va-keyframes.md):
- Official/community FL2VA guides: 4-beat prompt path with a
  MANDATORY-first alignment line, ordered intermediate states (never
  re-describing the frames — the crossfade failure mode), natural
  camera-motion sentences, soundscape footer.
- minimax3.com/blog/minimax-h3-first-last-frame — first/last mode.
- @yu_ichi_suzuki technique post — R2I: render a MINIMUM-length
  (5-frame on the 17k+5 grid) R2V with the standard plates and the
  target pose described, then extract its final frame as the FL2VA
  last-frame still. Both keyframes stay H3-native (animatable).

WanGP handler semantics (verified against the Wan2GP checkout,
models/minimax_h3/minimax_h3_handler.py: image_prompt_types_allowed
"TSEVL", end_frames_always_enabled=True): first+last-frame mode is
image_prompt_type "SE" with image_start/image_end inputs. There is NO
video_prompt_type "F+" — "F+" is not a WanGP token; the FL2VA job
encodes the SE mapping.
"""
from __future__ import annotations

import hashlib
import re
from typing import Any, Dict, List, Optional, Sequence

from services.chain.plan import ChainClip, ChainPlan

__all__ = [
    "KeyframePromptError", "DEFAULT_FL2VA_PARTS", "build_fl2va_prompt",
    "emit_r2i_job", "emit_fl2va_job",
]


class KeyframePromptError(ValueError):
    """Typed FL2VA prompt-contract violation (gate fired)."""


# Gates fire on parts that re-describe a keyframe picture with this
# much normalized-token overlap (a middle state must be a NEW
# intermediate state, not a restatement of Picture 1/2 content —
# restatements are the documented crossfade failure mode).
_REDESCRIBE_OVERLAP = 0.75
_STOPWORDS = frozenset(
    "a an the and or of to with at in on toward until by her his their "
    "is are".split())

# Camera grammar: type + amplitude + speed as ONE natural sentence.
# Defaults (medium amplitude / normal speed) are OMITTED per contract.
_DEFAULT_AMPLITUDE = "medium"
_DEFAULT_SPEED = "normal"
_TAGGY_CAMERA_RE = re.compile(r"^[^.]*(,[^.]*){$2,}$")  # 3+ comma segments

# Minimum R2V length on the 17k+5 grid (5/22/39/...): 5 frames.
R2I_FRAMES = 5

# model_type from the existing recipe surface (host/wangp_adapter.py
# H3_MODEL_TYPE) — the pruned FL2VA-capable architecture this repo
# already renders with.
H3_FL2VA_MODEL_TYPE = "minimax_h3_fl2va_pruned"

# Standard plate refs: two-shot composition anchor + one identity plate
# per character — same shape as the shot-1 recipe envelope.
RECIPE_STEPS = 20
RESOLUTION = [480, 832]
FPS = 24

DEFAULT_FL2VA_PARTS: Dict[str, Any] = {
    "picture1": ("two-shot at the console, both characters in frame, "
                 "eye-level, cool panel light"),
    "camera": {"type": "pushes in"},
    "middle_states": [
        "the speaker turns from the panel toward the listener, "
        "mouth still moving",
        "the turn completes, both characters now angled toward the "
        "doorway, motion settling",
    ],
    "soundscape": (
        "Quiet room tone with a faint reactor hum under the dialogue."),
}


def _tokens(text: str) -> List[str]:
    return [t for t in re.findall(r"[a-z]+", text.lower())
            if t not in _STOPWORDS]


def _overlap(a: str, b: str) -> float:
    ta, tb = set(_tokens(a)), set(_tokens(b))
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / min(len(ta), len(tb))


def _check_middle_states(middle_states: Sequence[str], picture1: str,
                         end_pose: Optional[str]) -> None:
    states = [s.strip() for s in middle_states if s and s.strip()]
    if len(states) < 2:
        raise KeyframePromptError(
            f"middle clause needs >= 2 ordered intermediate states, got "
            f"{len(states)} — the contract requires 2-3 IN ORDER")
    for i in range(len(states) - 1):
        if states[i] == states[i + 1]:
            raise KeyframePromptError(
                "middle intermediate states must be distinct and ordered")
    for s in states:
        if _overlap(s, picture1) >= _REDESCRIBE_OVERLAP:
            raise KeyframePromptError(
                "middle state re-describes Picture 1 content "
                f"(crossfade failure mode): {s!r}")
        if end_pose and _overlap(s, end_pose) >= _REDESCRIBE_OVERLAP:
            raise KeyframePromptError(
                "middle state re-describes the Picture 2 target pose "
                f"(crossfade failure mode): {s!r}")


def _check_camera(camera: Any) -> Dict[str, str]:
    if isinstance(camera, str):
        # Stacked-tag rejection: "push in, small amplitude, slow speed"
        segs = [s for s in camera.split(",")]
        if len(segs) >= 3 and all(s.strip() for s in segs):
            raise KeyframePromptError(
                "camera motion must be a natural sentence (type + "
                f"amplitude + speed), never stacked tags: {camera!r}")
        return {"type": camera.strip()}
    if not isinstance(camera, dict) or not str(
            camera.get("type", "")).strip():
        raise KeyframePromptError(
            f"camera must be a dict with a 'type': {camera!r}")
    return {k: str(v) for k, v in camera.items()}


def _camera_sentence(camera: Dict[str, str]) -> str:
    mtype = camera["type"].strip()
    amplitude = str(camera.get("amplitude", _DEFAULT_AMPLITUDE)).strip()
    speed = str(camera.get("speed", _DEFAULT_SPEED)).strip()
    parts = [mtype]
    if amplitude and amplitude != _DEFAULT_AMPLITUDE:
        parts.append(f"with {amplitude} amplitude")
    if speed and speed != _DEFAULT_SPEED:
        parts.append(f"at {speed} speed")
    return f"The camera {' '.join(parts)}."


def _check_soundscape(soundscape: str) -> str:
    s = (soundscape or "").strip()
    n = len([x for x in re.split(r"[.!?]+", s) if x.strip()])
    if not 1 <= n <= 4:
        raise KeyframePromptError(
            f"overall_soundscape must be 1-4 sentences, got {n}")
    return s


def _check_multi_shot(clip: ChainClip, multi_shot: bool,
                      shots: Optional[Sequence[Dict[str, Any]]]) -> None:
    if not multi_shot:
        if shots:
            raise KeyframePromptError(
                "shots given but multi_shot=False — later shots require "
                "multi_shot=True")
        return
    if not shots:
        raise KeyframePromptError(
            "multi_shot=True requires shots with strictly increasing "
            "timestamps")
    prev = 0.0
    for s in shots:
        ts = s.get("timestamp_s")
        if not isinstance(ts, (int, float)):
            raise KeyframePromptError(
                f"shot timestamp_s must be numeric: {ts!r}")
        if ts <= prev:
            raise KeyframePromptError(
                f"multi-shot timestamps must strictly increase: {ts} "
                f"after {prev}")
        if ts >= clip.duration_s:
            raise KeyframePromptError(
                f"shot timestamp {ts}s outside clip duration "
                f"{clip.duration_s:.2f}s")
        prev = float(ts)


def _final_shot_index(multi_shot: bool,
                      shots: Optional[Sequence[Dict[str, Any]]]) -> int:
    if multi_shot and shots:
        return int(shots[-1]["shot"])
    return 1


def build_fl2va_prompt(clip: ChainClip, plan: ChainPlan, *,
                       picture1: str,
                       camera: Any,
                       middle_states: Sequence[str],
                       soundscape: str,
                       multi_shot: bool = False,
                       shots: Optional[Sequence[Dict[str, Any]]] = None,
                       non_diegetic_music: str = "N/A") -> str:
    """4-beat FL2VA prompt + mandatory-first alignment line.

    Gates (raise KeyframePromptError) run BEFORE any string is
    assembled: (a) middle >=2 ordered non-redescribing states,
    (b) single [Shot] unless multi_shot with increasing in-duration
    timestamps, (c) camera as natural sentence (no stacked tags),
    (d) 1-4 sentence soundscape.
    """
    if not (picture1 or "").strip():
        raise KeyframePromptError("picture1 must be nonempty")
    end_pose = clip.end_pose

    # (a) middle states
    _check_middle_states(middle_states, picture1, end_pose)
    # (b) multi-shot timestamps
    _check_multi_shot(clip, multi_shot, shots)
    # (c) camera grammar
    cam = _check_camera(camera)
    # (d) soundscape
    scape = _check_soundscape(soundscape)

    ss = f"{clip.duration_s:.2f}"  # existing frame math: duration_s*fps
    final_shot = _final_shot_index(multi_shot, shots)

    # MANDATORY alignment line, first line of the prompt.
    alignment = (
        "How the reference pictures align with the target video — "
        "Picture 1 (from Shot 1) aligns with the 0.00-second mark of "
        "the target video; Picture 2 (from Shot "
        f"{final_shot}) aligns with the {ss}-second mark of the "
        "target video.")

    # 4-beat body. Picture 2 = clip.end_pose when present (the R2I
    # final-frame target); otherwise the last beat restates where the
    # shot should land.
    if end_pose:
        landing = end_pose
    else:  # pragma: no cover - default parts always carry end poses
        landing = "the composition settles, motion easing to a stop"

    middle = ". ".join(s.rstrip(".") for s in middle_states if s.strip())
    body = (
        f"[Shot 1] {picture1.rstrip('.')}, matching the position, "
        "framing, and lighting established by Picture 1. "
        f"{_camera_sentence(cam)} {middle}. Toward the end of the shot "
        f"the differences narrow until {landing}, landing on the exact "
        "pose, spacing, and composition established by Picture 2 at "
        f"the {ss}-second mark.")

    for s in (shots or []):
        body += (f" [Shot {s['shot']}] At {s['timestamp_s']:.2f}s the "
                 "shot continues from the established composition.")

    footer = (f"Overall soundscape: {scape} Non-diegetic music: "
              f"{non_diegetic_music}.")
    return f"{alignment}\n\n{body}\n\n{footer}"


# ── job emitters ─────────────────────────────────────────────────────

def _job_id(kind: str, clip: ChainClip) -> str:
    basis = f"{kind}|{clip.index}|{clip.seed}"
    h = hashlib.sha256(basis.encode()).hexdigest()[:10]
    return f"{kind}_{clip.index:04d}_{h}"


def _plate_refs(plan: ChainPlan, clip: ChainClip,
                plate_paths: Optional[Sequence[str]]) -> List[str]:
    if plate_paths is not None:
        return list(plate_paths)
    anchor = f"plates/{clip.speaker_sn.lower()}-anchor.png"
    return [anchor] + [f"plates/{c.sn_tag.lower()}-plate.png"
                       for c in plan.characters]


def emit_r2i_job(clip: ChainClip, plan: ChainPlan, *,
                 parts: Optional[Dict[str, Any]] = None,
                 plate_paths: Optional[Sequence[str]] = None
                 ) -> Dict[str, Any]:
    """Minimum-5-frame R2V pose-target job (the R2I step).

    Standard plate refs + the end pose described in the prompt; its
    final frame becomes the FL2VA last-frame still. Gates run first —
    no config escapes a broken prompt contract.
    """
    if not clip.end_pose:
        raise KeyframePromptError(
            f"clip {clip.index}: end_pose required for an R2I job")
    p = dict(DEFAULT_FL2VA_PARTS)
    if parts:
        p.update(parts)
    # gates + prompt build (raises before any config is assembled)
    prompt = build_fl2va_prompt(clip, plan, **p)
    return {
        "job_id": _job_id("r2i", clip),
        "clip_index": clip.index,
        "kind": "r2i_pose_target",
        "model_type": H3_FL2VA_MODEL_TYPE,
        "prompt": f"{plan.global_prompt} {clip.end_pose}. {prompt}",
        "image_refs": _plate_refs(plan, clip, plate_paths),
        "image_start": None,
        "steps": RECIPE_STEPS,
        "spectrum_cache": True,
        "resolution": list(RESOLUTION),
        "frames": R2I_FRAMES,
        "force_fps": FPS,
        "seed": clip.seed,
        "audio": {"path": clip.audio.path, "apad": True,
                  "start_s": clip.audio.start_s,
                  "padded_duration_s": clip.audio.padded_duration_s},
    }


def emit_fl2va_job(clip: ChainClip, plan: ChainPlan,
                    r2i_output_frame_path: str, *,
                    parts: Optional[Dict[str, Any]] = None,
                    needs: Optional[str] = None) -> Dict[str, Any]:
    """First+last-frame (FL2VA) job consuming the R2I final frame.

    WanGP mapping (verified in the Wan2GP checkout): first+last mode
    is image_prompt_type "SE" with image_start/image_end — there is no
    video_prompt_type "F+" token.
    """
    if not clip.end_pose:
        raise KeyframePromptError(
            f"clip {clip.index}: end_pose required for an FL2VA job")
    if not (r2i_output_frame_path or "").strip():
        raise KeyframePromptError(
            f"clip {clip.index}: r2i_output_frame_path must be nonempty")
    p = dict(DEFAULT_FL2VA_PARTS)
    if parts:
        p.update(parts)
    prompt = build_fl2va_prompt(clip, plan, **p)
    ref = clip.previous_clip_end_frame or {}
    job = {
        "job_id": _job_id("fl2va", clip),
        "clip_index": clip.index,
        "kind": "fl2va_first_last",
        "model_type": H3_FL2VA_MODEL_TYPE,
        "image_prompt_type": "SE",
        "prompt": prompt,
        "image_start": {
            "kind": "last_frame",
            "clip_index": ref.get("clip_index"),
            "frame": ref.get("frame"),
        },
        "image_end": r2i_output_frame_path,
        "image_refs": None,  # plates stand down (keyframes carry identity)
        "steps": RECIPE_STEPS,
        "spectrum_cache": True,
        "resolution": list(RESOLUTION),
        "frames": clip.frames,
        "force_fps": FPS,
        "seed": clip.seed,
        "audio": {"path": clip.audio.path, "apad": True,
                  "start_s": clip.audio.start_s,
                  "padded_duration_s": clip.audio.padded_duration_s},
    }
    if needs:
        job["needs"] = needs
    return job
