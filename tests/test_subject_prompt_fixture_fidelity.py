"""Golden-fidelity test: builder output vs the verified reference config.

The fixture (tests/fixtures/subject_mode_verified_config.json) is the exact
config that produced the measured winning render (VLM 8/10, per-third luma
motion 3.86-5.06 vs 0.26-0.37 prose baseline) on the 3090, 2026-08-30.
It is copied byte-identical into the repo so the "verified working reference
format" claim is auditable without leaving the repository.

This is STRUCTURAL fidelity, not byte equality: we rebuild the same scene
through the typed builder and assert every structural marker of the fixture
prompt appears in the builder output, in the same relative order.

Documented phrasing mappings (builder's OWN phrasing asserted, not the
fixture's literal token):
- fixture "fully_preserved" (snake_case, machine label) -> builder emits
  "fully preserved" (prose); both spellings of the concept are asserted
  on the fixture side, the builder side asserts "fully preserved".
- fixture speaker line names the character by voice ("the prisoner with
  the hollow wary voice (S1) says:") -> builder binds via the subject's
  name/voice_description with the same "(S1) says: <d>[English] ...</d>"
  envelope.
"""

import json
from pathlib import Path

import pytest

from predict.subject_prompt import (
    SceneCast,
    SpeakerLine,
    SubjectSpec,
    build_subject_prompt,
)

FIXTURE = Path(__file__).parent / "fixtures" / "subject_mode_verified_config.json"


def load_fixture() -> dict:
    return json.loads(FIXTURE.read_text())


def build_fixture_scene():
    """SceneCast/SpeakerLine representing the same scene as the fixture."""
    subs = (
        SubjectSpec(
            subject_id=1,
            name="the elderly grandmother",
            description=(
                "gray hair in a bun, tattered brown cloak, gripping the "
                "metal gate bars with both hands, weathered face with "
                "sharp observant eyes"
            ),
            ambient_actions=(
                "stands at the gate, her hands slowly tightening and "
                "loosening on the bars, her cloak hem swaying gently"
            ),
        ),
        SubjectSpec(
            subject_id=2,
            name="the gaunt young prisoner",
            description=(
                "disheveled, chained at wrists and ankles to a low stool, "
                "hollow cheeks, wary expression, wearing faded rags"
            ),
            is_speaker=True,
            ambient_actions=(
                "looks up at her warily and answers in a low voice while "
                "his chains hang slack, occasionally clinking as he "
                "shifts slightly on the stool"
            ),
        ),
        SubjectSpec(
            subject_id=3,
            name="the tall pale horned figure",
            description=(
                "long dark coat, arms crossed, smirking, two curved horns, "
                "standing against the far wall"
            ),
            ambient_actions=(
                "shifts his weight against the far wall, the hem of his "
                "long dark coat swaying with the movement, his smirk "
                "widening slightly"
            ),
        ),
        SubjectSpec(
            subject_id=4,
            name="the dungeon environment",
            description=(
                "dim stone cell, single hanging lantern with warm "
                "flickering glow, iron gate, rough-hewn walls"
            ),
            ambient_actions=(
                "the lantern flame flickers and sways, casting shifting "
                "warm light across the stone walls, dust motes drifting "
                "through the beam"
            ),
        ),
    )
    cast = SceneCast(
        subjects=subs,
        environment_subject=True,
        style=(
            "hand-painted gothic realism, dark browns and blacks, stark "
            "chiaroscuro lamplight, cinematic 16mm grain"
        ),
        shot_description=(
            "The scene is continuously alive with ambient motion and no "
            "camera movement."
        ),
        soundscape=(
            "quiet dungeon room tone, faint chain clinks, distant water "
            "drip, the soft crackle of the lantern flame"
        ),
        music="N/A",
    )
    line = SpeakerLine(
        subject_id=2,
        text="No ma'am. But the devil's been expecting you.",
        language="English",
        voice_description="prisoner with the hollow wary voice",
    )
    return cast, line


def fixture_prompt() -> str:
    return load_fixture()["prompt"]


def built_prompt() -> str:
    cast, line = build_fixture_scene()
    return build_subject_prompt(cast, line)


# ------------------------------------------------------------ fixture sanity


def test_fixture_is_readable_json_and_prompt_present():
    doc = load_fixture()
    assert isinstance(doc["prompt"], str) and doc["prompt"].strip()
    assert doc["model_type"] == "minimax_h3_ref2va_pruned"


def test_fixture_contains_its_own_markers():
    fp = fixture_prompt()
    for marker in (
        "<Subject 1> (from <Picture 1>)",
        "<Subject 4>",
        "Summary: [reference generation]",
        "Retention analysis:",
        "fully_preserved",  # fixture's machine label spelling
        "Detailed description:",
        "Static Shot",
        "(S1) says: <d>[English]",
        "Overall soundscape:",
        "Non-diegetic music: N/A",
        "lips completely closed",
    ):
        assert marker in fp, marker


# ------------------------------------------------- structural relative order


def test_builder_marker_order_matches_fixture_order():
    """Every fixture structural marker, in fixture order, also appears in
    the builder output in the same relative order."""
    # Same marker sequence, each side's OWN spelling:
    # fixture spells the retention concept "fully_preserved"; the builder
    # consistently emits the prose form "fully preserved" (mapping
    # documented at module top).
    fixture_markers = [
        "<Subject 1> (from <Picture 1>)",
        "<Subject 2>",
        "<Subject 3>",
        "<Subject 4>",
        "Summary: [reference generation]",
        "Retention analysis:",
        "fully_preserved",
        "Detailed description:",
        "Static Shot",
        "(S1) says: <d>[English]",
        "Overall soundscape:",
        "Non-diegetic music: N/A",
    ]
    builder_markers = [
        "<Subject 1> (from <Picture 1>)",
        "<Subject 2>",
        "<Subject 3>",
        "<Subject 4>",
        "Summary: [reference generation]",
        "Retention analysis:",
        "fully preserved",
        "Detailed description:",
        "Static Shot",
        "(S1) says: <d>[English]",
        "Overall soundscape:",
        "Non-diegetic music: N/A",
    ]
    fp, bp = fixture_prompt(), built_prompt()
    fp_pos = [fp.index(m) for m in fixture_markers]
    bp_pos = [bp.index(m) for m in builder_markers]
    assert fp_pos == sorted(fp_pos)
    assert bp_pos == sorted(bp_pos)


def test_ambient_action_phrases_present_per_character():
    """Each character's ambient-action phrase from the fixture appears in
    the builder output (inside the Detailed description body)."""
    bp = built_prompt()
    det = bp.split("Detailed description:")[1]
    for phrase in (
        "tightening and loosening on the bars",      # Subject 1
        "chains hang slack",                         # Subject 2 (speaker)
        "smirk widening slightly",                    # Subject 3
        "lantern flame flickers and sways",           # Subject 4 (env)
    ):
        assert phrase in det, phrase


def test_lips_closed_clauses_for_each_nonspeaker():
    """Non-speakers (Subjects 1 and 3) each keep a lips-closed clause with
    their ambient-action sentence in the Detailed description body; the
    speaker's sentence must NOT carry one."""
    bp = built_prompt()
    det = bp.split("Detailed description:")[1].split("Overall soundscape:")[0]
    s1 = det.split("<Subject 1>")[1].split("<Subject 2>")[0]
    s3 = det.split("<Subject 3>")[1]
    assert "lips completely closed" in s1
    assert "lips completely closed" in s3
    s2 = det.split("<Subject 2>")[1].split("<Subject 3>")[0]
    assert "lips completely closed" not in s2


def test_subject_definitions_are_identity_only():
    """Subject definitions contain identity/appearance only — ambient
    actions, lips-closed clauses and the speaker <d> line live in the
    Detailed description body, not inside subject definitions."""
    bp = built_prompt()
    defs = bp.split("Summary:")[0]
    for phrase in (
        "Ambient action:",
        "lips completely closed",
        "says:",
        "tightening and loosening",
        "chains hang slack",
        "smirk widening",
        "flame flickers",
    ):
        assert phrase not in defs, phrase


def test_speaker_line_inside_detailed_description_body():
    bp = built_prompt()
    det = bp.split("Detailed description:")[1].split("Overall soundscape:")[0]
    assert "says: <d>[English] No ma'am. But the devil's been expecting you.</d>" in det
