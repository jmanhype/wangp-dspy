"""FL2VA keyframe targets + R2I pose-target step — RED-first tests.

Contract source (scraped 2026-09-01, see docs/fl2va-keyframes.md):
- 4-beat FL2VA prompt + MANDATORY-first alignment line (official/
  community guides; minimax3.com first-last-frame blog).
- R2I technique: @yu_ichi_suzuki — 5-frame R2V with refs + pose,
  extract final frame as the FL2VA last-frame still.
"""
from __future__ import annotations

import dataclasses
import json

import dspy
import pytest

from services.chain.controller import build_chain_plan, emit_render_manifest
from services.chain.keyframes import (
    KeyframePromptError,
    build_fl2va_prompt,
    emit_fl2va_job,
    emit_r2i_job,
)
from services.chain.plan import ChainPlan, ChainClip
from signatures.director import EndPoseDescriber


def _script():
    return [
        {"speaker": "Ada", "text": "The reactor is waking up."},
        {"speaker": "Bo", "text": "Then we leave now."},
        {"speaker": "Ada", "text": "Not without the core."},
    ]


def _characters():
    return [
        {"name": "Ada", "sn_tag": "S1", "description": "engineer, red jacket"},
        {"name": "Bo", "sn_tag": "S2", "description": "pilot, gray coat"},
    ]


DURATIONS = [2.3333333333333335] * 3  # 56f grid @24fps

PARTS = dict(
    picture1="Ada stands at the console, both hands flat on the panel",
    camera={"type": "pushes in"},
    middle_states=[
        "Ada lifts her right hand off the panel and turns her head",
        "she is half-turned toward the doorway, arm still rising",
    ],
    soundscape="A low reactor hum builds under the dialogue.",
)


def _plan():
    return build_chain_plan(_script(), _characters(), DURATIONS)


def _plan_with_end_pose(clip_index=2, end_pose="Ada faces the doorway, "
                           "one arm raised toward the exit"):
    base = _plan()
    clips = list(base.clips)
    clips[clip_index - 1] = dataclasses.replace(
        clips[clip_index - 1], end_pose=end_pose)
    return ChainPlan(global_prompt=base.global_prompt,
                     characters=base.characters, clips=tuple(clips),
                     overlap_frames=base.overlap_frames, fps=base.fps)


# ── 1: clip schema ───────────────────────────────────────────────────

def test_clip_end_pose_optional_default_none():
    plan = _plan()
    assert all(c.end_pose is None for c in plan.clips)


def test_clip_end_pose_rejects_blank():
    with pytest.raises(Exception):
        dataclasses.replace(_plan().clips[0], end_pose="   ")


def test_end_pose_round_trips_json():
    plan = _plan_with_end_pose()
    doc = plan.to_json()
    assert doc["clips"][1]["end_pose"].startswith("Ada faces")
    back = ChainPlan.from_json(doc)
    assert back.clips[1].end_pose == plan.clips[1].end_pose
    assert back.clips[0].end_pose is None


# ── 2: prompt contract ───────────────────────────────────────────────

def test_alignment_line_first_with_correct_marks():
    plan = _plan()
    clip = plan.clips[1]
    prompt = build_fl2va_prompt(clip, plan, **PARTS)
    ss = f"{clip.duration_s:.2f}"
    alignment = (
        "How the reference pictures align with the target video — "
        "Picture 1 (from Shot 1) aligns with the 0.00-second mark of "
        "the target video; Picture 2 (from Shot 1) aligns with the "
        f"{ss}-second mark of the target video.")
    assert prompt.splitlines()[0] == alignment


def test_four_beat_structure():
    plan = _plan()
    prompt = build_fl2va_prompt(plan.clips[1], plan, **PARTS)
    body = prompt.splitlines()[-3]
    assert body.startswith("[Shot 1]")
    assert "matching the position, framing, and lighting established " \
        "by Picture 1" in body
    assert "The camera pushes in." in body
    assert "Toward the end of the shot the differences narrow until" in body
    ss = f"{plan.clips[1].duration_s:.2f}"
    assert (f"landing on the exact pose, spacing, and composition "
            f"established by Picture 2 at the {ss}-second mark") in body


def test_middle_states_in_order():
    plan = _plan()
    prompt = build_fl2va_prompt(plan.clips[1], plan, **PARTS)
    a = prompt.index(PARTS["middle_states"][0])
    b = prompt.index(PARTS["middle_states"][1])
    assert a < b


def test_camera_amplitude_speed_sentence_and_defaults_omitted():
    plan = _plan()
    prompt = build_fl2va_prompt(
        plan.clips[1], plan,
        picture1=PARTS["picture1"],
        camera={"type": "pushes in", "amplitude": "small",
                "speed": "slow"},
        middle_states=PARTS["middle_states"],
        soundscape=PARTS["soundscape"])
    assert "The camera pushes in with small amplitude at slow speed." \
        in prompt
    assert "medium amplitude" not in prompt and "normal speed" not in prompt


def test_sound_footer_soundscape_and_na_music():
    plan = _plan()
    prompt = build_fl2va_prompt(plan.clips[1], plan, **PARTS)
    assert "Overall soundscape:" in prompt
    assert "Non-diegetic music: N/A." in prompt


# ── 3: gates ─────────────────────────────────────────────────────────

def test_gate_too_few_intermediate_states():
    plan = _plan()
    parts = dict(PARTS, middle_states=["only one state"])
    with pytest.raises(KeyframePromptError):
        build_fl2va_prompt(plan.clips[1], plan, **parts)


def test_gate_middle_redescribes_picture1():
    plan = _plan()
    parts = dict(PARTS, middle_states=[
        PARTS["middle_states"][0],
        "Ada stands at the console, both hands flat on the panel",
    ])
    with pytest.raises(KeyframePromptError):
        build_fl2va_prompt(plan.clips[1], plan, **parts)


def test_gate_middle_redescribes_end_pose():
    plan = _plan_with_end_pose()
    clip = plan.clips[1]
    parts = dict(PARTS, middle_states=[
        PARTS["middle_states"][0],
        "Ada faces the doorway, one arm raised toward the exit",
    ])
    with pytest.raises(KeyframePromptError):
        build_fl2va_prompt(clip, plan, **parts)


def test_gate_stacked_camera_tags():
    plan = _plan()
    with pytest.raises(KeyframePromptError):
        build_fl2va_prompt(plan.clips[1], plan,
                           picture1=PARTS["picture1"],
                           camera="push in, small amplitude, slow speed",
                           middle_states=PARTS["middle_states"],
                           soundscape=PARTS["soundscape"])


def test_gate_multishot_requires_shots():
    plan = _plan()
    with pytest.raises(KeyframePromptError):
        build_fl2va_prompt(plan.clips[1], plan, multi_shot=True, **PARTS)


def test_gate_multishot_timestamps_must_increase():
    plan = _plan()
    clip = plan.clips[1]
    with pytest.raises(KeyframePromptError):
        build_fl2va_prompt(clip, plan, multi_shot=True,
                           shots=[{"shot": 2, "timestamp_s": 1.0},
                                  {"shot": 3, "timestamp_s": 1.0}],
                           **PARTS)


def test_gate_multishot_timestamp_within_clip_duration():
    plan = _plan()
    clip = plan.clips[1]
    with pytest.raises(KeyframePromptError):
        build_fl2va_prompt(clip, plan, multi_shot=True,
                           shots=[{"shot": 2, "timestamp_s": 99.0}],
                           **PARTS)


def test_gate_multishot_alignment_uses_final_shot_index():
    plan = _plan()
    clip = plan.clips[0]  # full 56f duration (2.33s) for in-range stamps
    prompt = build_fl2va_prompt(
        clip, plan, multi_shot=True,
        shots=[{"shot": 2, "timestamp_s": 1.0},
               {"shot": 3, "timestamp_s": 2.0}],
        **PARTS)
    assert "Picture 2 (from Shot 3) aligns" in prompt.splitlines()[0]


def test_gate_soundscape_sentence_count():
    plan = _plan()
    with pytest.raises(KeyframePromptError):
        build_fl2va_prompt(plan.clips[1], plan, soundscape="",
                           **{k: v for k, v in PARTS.items()
                              if k != "soundscape"})
    five = " ".join(f"Sentence {i} of the soundscape." for i in range(5))
    with pytest.raises(KeyframePromptError):
        build_fl2va_prompt(plan.clips[1], plan,
                           soundscape=five,
                           **{k: v for k, v in PARTS.items()
                              if k != "soundscape"})


def test_gates_fire_before_job_emission():
    plan = _plan_with_end_pose()
    clip = plan.clips[1]
    # a parts payload that violates the middle-state gate must raise
    # from emit_r2i_job too — no config escapes a broken contract.
    bad_parts = dict(PARTS, middle_states=["only one"])
    with pytest.raises(KeyframePromptError):
        emit_r2i_job(clip, plan, parts=bad_parts)


# ── 4: R2I / FL2VA jobs ──────────────────────────────────────────────

def test_r2i_job_shape():
    plan = _plan_with_end_pose()
    clip = plan.clips[1]
    job = emit_r2i_job(clip, plan, parts=PARTS)
    assert job["kind"] == "r2i_pose_target"
    assert job["frames"] == 5          # minimum video_length, 5-frame R2V
    assert job["model_type"] == "minimax_h3_fl2va_pruned"
    assert len(job["image_refs"]) == 3  # anchor + one plate per character
    assert clip.end_pose in job["prompt"]
    assert job["clip_index"] == clip.index


def test_fl2va_job_shape():
    plan = _plan_with_end_pose()
    clip = plan.clips[1]
    job = emit_fl2va_job(clip, plan, "render/clip0002/r2i_last_frame.png",
                         parts=PARTS)
    assert job["kind"] == "fl2va_first_last"
    assert job["image_prompt_type"] == "SE"  # start+end per WanGP handler
    assert job["image_end"] == "render/clip0002/r2i_last_frame.png"
    assert job["image_start"]["kind"] == "last_frame"
    assert job["image_start"]["clip_index"] == 1
    assert job["frames"] == clip.frames
    assert job["prompt"].startswith("How the reference pictures align")


# ── 5: manifest dependency ordering ──────────────────────────────────

def test_manifest_two_dependent_jobs_when_end_pose_present():
    plan = _plan_with_end_pose()
    manifest = emit_render_manifest(plan)
    # 3 clips + one extra job for the end-pose clip
    assert len(manifest) == 4
    r2i = manifest[1]
    fl2va = manifest[2]
    assert r2i["kind"] == "r2i_pose_target"
    assert fl2va["kind"] == "fl2va_first_last"
    assert fl2va["needs"] == r2i["job_id"]
    # r2i precedes fl2va in render order
    assert manifest.index(r2i) < manifest.index(fl2va)
    # the last clip keeps the unchanged continuation path
    assert manifest[3]["kind"] == "first_frame_continuation"


def test_manifest_unchanged_when_end_pose_absent():
    manifest = emit_render_manifest(_plan())
    assert len(manifest) == 3
    assert [c["kind"] for c in manifest] == [
        "shot1_three_ref_recipe", "first_frame_continuation",
        "first_frame_continuation"]


# ── 6: EndPoseDescriber signature + planner post-pass ────────────────

def test_end_pose_describer_signature_shape():
    assert set(EndPoseDescriber.input_fields) == {"beats", "shots"}
    assert set(EndPoseDescriber.output_fields) == {"end_poses"}


def test_planner_end_pose_post_pass_stub_lm():
    from services.director.planners.short_film import DSPY_LLM, ShortFilmPlanner
    out = json.dumps({"end_poses": [
        {"shot_index": 1,
         "end_pose": "Ada faces the doorway, one arm raised"}]})
    lm = dspy.utils.DummyLM([{"end_poses": out}])
    planner = ShortFilmPlanner(llm=DSPY_LLM)
    with dspy.context(lm=lm):
        poses = planner.describe_end_poses(
            beats_json=json.dumps([{"index": 1}]),
            shots_json=json.dumps([{"index": 1, "speaker": "Ada"}]))
    assert poses == {1: "Ada faces the doorway, one arm raised"}
