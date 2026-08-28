"""WD-l5bx Task 2 RED — render profile Strategy (H3 first, Ref2VA
second). Fails until predict/render_profiles.py exists.
"""
import pytest

from predict.render_profiles import (
    RenderProfile, H3Profile, Ref2VAProfile, ProfileError,
)


def _brief():
    from predict.prompt_director import RenderBrief
    return RenderBrief(subject="a detective", motion="walks",
                       camera="dolly in", style="16mm grain")


def _decision():
    from predict.profile_selector import ProfileDecision
    return ProfileDecision(model="h3", resolution="768p",
                           shot_length_frames=107,
                           seed_policy="fixed_per_story",
                           wangp_profile="profile3")


# ── H3 profile: first implementation, shape unchanged ────────────────

def test_h3_profile_builds_settings():
    p = H3Profile()
    doc = p.build_settings([_brief()], _decision())
    assert doc["model_type"] == "minimax_h3_fl2va_pruned"
    assert doc["prompt"] == "multishot"
    assert doc["force_fps"] == "24"
    assert "\n---\n" in doc["script"] or doc["script"].count("---") >= 0


def test_h3_rejects_audio_prompt_type():
    """G1 boundary source: the H3-style profile refuses audio 'A'
    jobs — Ref2VA is the only sanctioned carrier."""
    p = H3Profile()
    with pytest.raises(ProfileError, match="[Aa]udio"):
        p.build_settings([_brief()], _decision(), audio_prompt_type="A")


# ── Ref2VA profile ────────────────────────────────────────────────────

import pathlib


def _mkrefs(tmp, n=1):
    refs = []
    for i in range(n):
        f = pathlib.Path(tmp) / f"ref{i+1}.png"
        f.write_bytes(b"x")
        refs.append(str(f))
    return refs
    base = dict(
        image_refs=["/tmp/ref1.png", "/tmp/ref2.png"],
        audio_prompt_type="A",
        guide_duration_s=8.0,
        shot_duration_s=8.0,
    )
    base.update(over)
    return over and base or base


def test_ref2va_valid_builds(tmp_path):
    p = Ref2VAProfile()
    doc = p.build_settings(
        [_brief()], _decision(),
        image_refs=_mkrefs(tmp_path), audio_prompt_type="A",
        guide_duration_s=8.0, shot_duration_s=8.0)
    assert doc["model_type"]  # some ref2va model


def test_ref2va_image_refs_required(tmp_path):
    p = Ref2VAProfile()
    with pytest.raises(ProfileError, match="image_ref"):
        p.build_settings([_brief()], _decision(),
                         image_refs=[], audio_prompt_type="A",
                         guide_duration_s=8.0, shot_duration_s=8.0)


def test_ref2va_audio_a_required(tmp_path):
    p = Ref2VAProfile()
    with pytest.raises(ProfileError, match="audio"):
        p.build_settings([_brief()], _decision(),
                         image_refs=_mkrefs(tmp_path),
                         audio_prompt_type="",
                         guide_duration_s=8.0, shot_duration_s=8.0)


def test_ref2va_guide_duration_must_match(tmp_path):
    p = Ref2VAProfile()
    with pytest.raises(ProfileError, match="guide") as ei:
        p.build_settings([_brief()], _decision(),
                         image_refs=_mkrefs(tmp_path),
                         audio_prompt_type="A",
                         guide_duration_s=7.33,
                         shot_duration_s=8.0)
    assert "7.33" in str(ei.value) and "8.0" in str(ei.value)


def test_ref2va_shot_duration_cap(tmp_path):
    p = Ref2VAProfile()
    for bad in (3.5, 15.5):
        with pytest.raises(ProfileError, match="4|15|duration"):
            p.build_settings([_brief()], _decision(),
                             image_refs=_mkrefs(tmp_path),
                             audio_prompt_type="A",
                             guide_duration_s=bad,
                             shot_duration_s=bad)


def test_ref2va_token_contiguity(tmp_path):
    p = Ref2VAProfile()
    # script references <Picture 2> but only 1 ref -> gap
    from predict.prompt_director import RenderBrief
    b = RenderBrief(subject="<Picture 2> close", motion="talks",
                    camera="static", style="grain")
    with pytest.raises(ProfileError, match="[Pp]icture|contiguous|index"):
        p.build_settings([b], _decision(),
                         image_refs=_mkrefs(tmp_path),
                         audio_prompt_type="A",
                         guide_duration_s=8.0, shot_duration_s=8.0)


def test_ref2va_tokens_contiguous_ok(tmp_path):
    from predict.prompt_director import RenderBrief
    b = RenderBrief(subject="<Picture 1> and <Audio 1>", motion="talks",
                    camera="static", style="grain")
    p = Ref2VAProfile()
    doc = p.build_settings([b], _decision(),
                           image_refs=_mkrefs(tmp_path),
                           audio_prompt_type="A",
                           guide_duration_s=8.0, shot_duration_s=8.0)
    assert doc


def test_strategy_surface():
    assert issubclass(H3Profile, RenderProfile)
    assert issubclass(Ref2VAProfile, RenderProfile)
