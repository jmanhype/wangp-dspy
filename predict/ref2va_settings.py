"""The single-cut Ref2VA wire schema. Never serialize a multishot job here.

WanGP treats the *presence of nonempty script* as executable dispatch, not
metadata. Its multishot shortcut drops image/audio conditioning. Keep the
queue envelope separate and fail on routing fields rather than stripping a
dangerous payload silently. Unknown audit metadata is not sent to WanGP.
"""
from __future__ import annotations

from predict.job_config import normalize_continuation_frame_count
from predict.model_types import REF2VA_MODEL_TYPE


class Ref2VASettingsError(ValueError):
    pass


WIRE_FIELDS = frozenset({
    'model_type', 'prompt', 'image_prompt_type', 'image_start', 'image_refs',
    'video_prompt_type', 'audio_prompt_type', 'audio_guide', 'audio_guide2',
    'video_source', 'video_guide', 'keep_frames_video_source', 'video_length',
    'resolution', 'seed', 'num_inference_steps', 'force_fps',
    'guidance_scale', 'embedded_guidance_scale', 'negative_prompt',
})
MULTISHOT_FIELDS = frozenset({'script', 'shots', 'shot_count', 'frames_per_shot',
                             'memory_mode', 'memory_frames', 'anchor_frames'})


def ref2va_wire_settings(doc: dict) -> dict:
    if not isinstance(doc, dict):
        raise Ref2VASettingsError('Ref2VA settings must be a dict')
    forbidden = MULTISHOT_FIELDS.intersection(doc)
    if forbidden:
        raise Ref2VASettingsError(
            f'Ref2VA refuses multishot dispatch fields: {sorted(forbidden)}; re-plan the job')
    if doc.get('model_type') != REF2VA_MODEL_TYPE:
        raise Ref2VASettingsError('Ref2VA model_type mismatch')
    for name in ('prompt', 'audio_guide'):
        value = doc.get(name)
        if not isinstance(value, str) or not value.strip() or value.startswith('chain://'):
            raise Ref2VASettingsError(f'{name}: nonempty resolved string required')
    if doc.get('audio_prompt_type') != 'A' or doc.get('video_prompt_type') != 'I':
        raise Ref2VASettingsError("Ref2VA requires audio_prompt_type=A, video_prompt_type=I")
    refs = doc.get('image_refs')
    if not isinstance(refs, list) or not refs:
        raise Ref2VASettingsError('image_refs must be a nonempty list of paths')
    if any(not isinstance(p, str) or not p.strip() or p.startswith('chain://') for p in refs):
        raise Ref2VASettingsError('image_refs must contain resolved path strings')
    start = doc.get('image_start')
    if start is not None:
        if not isinstance(start, str) or not start or start.startswith('chain://'):
            raise Ref2VASettingsError('image_start must be a resolved path string')
        if doc.get('image_prompt_type') != 'S' or start != refs[0]:
            raise Ref2VASettingsError('image_start must bind refs[0] with image_prompt_type=S')
    frames = doc.get('video_length')
    if type(frames) is not int or frames != normalize_continuation_frame_count(frames):
        raise Ref2VASettingsError('video_length must be on the Ref2VA 56f+17k grid')
    for name in ('video_source', 'video_guide', 'audio_guide2'):
        if doc.get(name) is not None:
            raise Ref2VASettingsError(f'{name}: unsupported secondary conditioning in single-turn Ref2VA')
    if doc.get('keep_frames_video_source', ''):
        raise Ref2VASettingsError('keep_frames_video_source must be empty')
    return {key: value for key, value in doc.items() if key in WIRE_FIELDS}
