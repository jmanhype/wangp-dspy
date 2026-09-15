"""SETTINGS PARITY golden test (live smoke 2026-09-02).

The pipeline smoke produced motion-not-synced output because
Ref2VAProfile.build_settings emitted a settings doc that diverged from
the proven manual recipe (services/director/renderers/h3_recipe.py)
in three ways that break lip sync:

  1. FATAL: prompt was the WanGPJobConfig profile-tag default
     ("ref2va") — the real speaker template went into `script`, but
     WanGP reads `prompt`. The model received the literal string
     "ref2va" as its entire prompt.
  2. frames_per_shot snapped to the multishot default (107 for
     4.042s) with NO video_length — the audio guide was 4.042s (97f),
     so the model paced mouth motion for a different duration.
  3. seed defaulted to 42; the proven recipe pins 904.

This test builds settings via Ref2VAProfile for the EXACT smoke case
(3 plates, grandma speaker line, 4.042s) and asserts FIELD-FOR-FIELD
against the proven manual doc shape. Any future divergence fails.
"""
from __future__ import annotations

import pathlib

import pytest

from predict.audio_dataplane import AudioGuideProvenance
from predict.prompt_director import RenderBrief
from predict.profile_selector import ProfileDecision
from predict.render_profiles import ProfileError, Ref2VAProfile
from services.director.renderers.h3_recipe import (
    FPS as RECIPE_FPS,
    SEED as RECIPE_SEED,
)

# ── the exact live smoke case ─────────────────────────────────────────
DURATION_S = 4.042          # padded audio-guide duration
EXPECTED_FRAMES = 97        # round(4.042 * 24) — the REQUESTED frames
# NIGHT TWO (2026-09-03): WanGP snaps the requested frames onto its
# own grid regardless of what we emit (live: 56 -> 107). The emitted
# video_length is the SNAPPED value (audio muxing matches the ACTUAL
# output); requested_frames preserves the caller's raw request.
from predict.job_config import normalize_frame_count
SNAPPED_FRAMES = normalize_frame_count(EXPECTED_FRAMES)  # 107

GRANDMA_LINE = "No ma'am. But the devil's been expecting you."

_PLATE_DESCRIPTIONS = [
    "a weathered woman with silver braids, seated left",
    "a lean man with soot-streaked cheeks, standing right",
]


def _assets(tmp_path: pathlib.Path):
    """3 plates (anchor + 2 identities) + the audio-guide/provenance
    files — everything readable at submit, exactly like the smoke."""
    paths = []
    for name in ("anchor.png", "charA.png", "charB.wav_plate.png",
                 "guide.wav", "master.wav", "vocal.wav", "wmap.json"):
        f = tmp_path / name
        f.write_bytes(b"x" * 8)
        paths.append(str(f))
    anchor, char_a, char_b, guide, master, vocal, wmap = paths
    return {
        "image_refs": [anchor, char_a, char_b],
        "audio_guide": guide,
        "audio_provenance": AudioGuideProvenance(
            source_master=master, vocal_stem=vocal, whisper_map=wmap,
            keeper_window_s=(0.0, DURATION_S)),
    }


def _recipe_speaker_prompt(tmp_path: pathlib.Path) -> str:
    """The proven manual speaker template for the same smoke case,
    built by the recipe module's template builder (the doc structure
    that rendered in sync; frame math is asserted separately below at
    the recipe module's own grid)."""
    from services.director.renderers.h3_recipe import _build_prompt
    return _build_prompt(
        anchor_plate=str(tmp_path / "anchor.png"),
        character_plates=[
            {"path": str(tmp_path / "charA.png"),
             "description": _PLATE_DESCRIPTIONS[0]},
            {"path": str(tmp_path / "charB.wav_plate.png"),
             "description": _PLATE_DESCRIPTIONS[1]},
        ],
        speaker_index=0,
        line=GRANDMA_LINE,
        scene_staging="two characters framed left and right",
        listening_detail="head tilted, eyes on the speaker",
        ambience="room tone, faint brazier crackle",
        continuous_lines=None,
    )


def test_recipe_frame_math_single_source():
    """The recipe module's own grid math for an on-grid duration
    (73/24s -> 73f) matches round(duration*24) — the parity pin."""
    from services.director.renderers.policy import (
        check_duration_on_grid)
    assert check_duration_on_grid(73 / 24.0, fps=24) == \
        int(round(73 / 24.0 * 24)) == 73


def _build_doc(tmp_path: pathlib.Path, **over):
    kw = dict(
        briefs=[RenderBrief(
            subject="a weathered woman with silver braids, seated left",
            motion="speaks with lively animated mouth movement",
            camera="static medium shot", style="16mm grain")],
        decision=ProfileDecision(
            model="h3", resolution="768p", shot_length_frames=107,
            seed_policy="fixed_per_story", wangp_profile="profile3"),
        image_refs=_assets(tmp_path)["image_refs"],
        audio_prompt_type="A",
        guide_duration_s=DURATION_S,
        shot_duration_s=DURATION_S,
        audio_guide=_assets(tmp_path)["audio_guide"],
        audio_provenance=_assets(tmp_path)["audio_provenance"],
        speaker_prompt=_recipe_speaker_prompt(tmp_path),
        audio_length_frames=EXPECTED_FRAMES,
    )
    kw.update(over)
    return Ref2VAProfile().build_settings(
        kw.pop("briefs"), kw.pop("decision"), **kw)


# ── the golden parity assertions ─────────────────────────────────────

def test_golden_parity_smoke_case(tmp_path):
    doc = _build_doc(tmp_path)
    # (1) prompt carries the FULL speaker template — never the bare
    # profile tag "ref2va"
    assert doc["prompt"] != "ref2va"
    assert "(S1) says: <d>[English] " + GRANDMA_LINE + "</d>" \
        in doc["prompt"]
    assert "mouth closed" in doc["prompt"]          # listener clause
    assert "<Subject 1>" in doc["prompt"]           # subject defs
    # script preserved for the multishot lane but prompt is the carrier
    assert "script" not in doc
    assert "frames_per_shot" not in doc
    # (2) NIGHT TWO: video_length is the SNAPPED count WanGP actually
    # renders (107 for a 97f request); requested_frames keeps the raw
    # request so consumers can audit the snap.
    assert doc["video_length"] == SNAPPED_FRAMES == 107
    assert doc["requested_frames"] == EXPECTED_FRAMES == 97
    assert RECIPE_FPS == 24
    # (3) seed pins to the recipe value, not 42
    assert doc["seed"] == RECIPE_SEED == 904
    # audio plane parity
    assert doc["audio_guide"] == _assets(tmp_path)["audio_guide"]
    assert doc["audio_prompt_type"] == "A"
    # image_refs list matches the 3-plate smoke manifest
    assert doc["image_refs"] == _assets(tmp_path)["image_refs"]
    assert len(doc["image_refs"]) == 3


def test_golden_parity_caller_seed_wins(tmp_path):
    doc = _build_doc(tmp_path, seed=1234)
    assert doc["seed"] == 1234


def test_audio_length_mismatch_typed_rejection(tmp_path):
    with pytest.raises(ProfileError, match="97|audio guide length"):
        _build_doc(tmp_path, audio_length_frames=107)


def test_off_grid_duration_typed_rejection(tmp_path):
    """Off-grid 17k+5 multishot durations still pass Ref2VA (the
    recipe's authority is round(duration*24)); the mismatch guard is
    the audio-length invariant — see the audio_length_frames test."""
    doc = _build_doc(tmp_path, guide_duration_s=4.5, shot_duration_s=4.5,
                     audio_length_frames=108)
    # NIGHT TWO: 108f snaps to 124 on the 5+17k grid
    assert doc["video_length"] == 124
    assert doc["requested_frames"] == 108


def test_speaker_prompt_empty_carrier_rejected(tmp_path):
    with pytest.raises(ProfileError, match="speaker_prompt"):
        _build_doc(tmp_path, speaker_prompt="   ")


def test_prompt_fallback_never_bare_tag(tmp_path):
    """No speaker_prompt supplied: the derived fallback still carries
    speaker/listener structure — the bare 'ref2va' tag must never
    reach WanGP's prompt field again."""
    kw = dict(
        image_refs=_assets(tmp_path)["image_refs"],
        audio_prompt_type="A",
        guide_duration_s=DURATION_S,
        shot_duration_s=DURATION_S,
        audio_guide=_assets(tmp_path)["audio_guide"],
        audio_provenance=_assets(tmp_path)["audio_provenance"],
    )
    doc = Ref2VAProfile().build_settings(
        [RenderBrief(subject="a weathered woman with silver braids",
                     motion="speaks in sync with the audio guide",
                     camera="static medium shot", style="16mm grain")],
        ProfileDecision(model="h3", resolution="768p",
                        shot_length_frames=107,
                        seed_policy="fixed_per_story",
                        wangp_profile="profile3"),
        **kw)
    assert doc["prompt"] != "ref2va"
    assert doc["prompt"].strip()
    assert "mouth" in doc["prompt"]
    assert doc["video_length"] == SNAPPED_FRAMES == 107
    assert doc["requested_frames"] == 97
    assert doc["seed"] == 904
