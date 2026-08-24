"""WD-izly RED tests: multishot separator must be line-delimited.

Root cause (live, proven twice by the PR#12 readback verification):
wgp parse_script (Wan2GP/models/minimax_h3/multishot.py:49) splits
scripts on the regex `(?m)^---\\s*$` — the separator must be on its
OWN LINE. Our SCRIPT_SEPARATOR='---' joined briefs INLINE, so 3 shots
parsed as 1 giant prompt and wgp rendered a single shot with exit 0.
"""
import re

from prompt_director import RenderBrief
from profile_selector import ProfileDecision
from wangp_adapter import build_settings, build_script


# EXACT mirror of wgp's parsing regex — multishot.py:49
_WGP_SPLIT = re.compile(r"(?m)^---\s*$")


def _brief(subject="astronaut, cracked visor"):
    return RenderBrief(subject=subject, motion="slow head turn",
                       camera="dolly in", style="16mm archival grain")


def _decision():
    return ProfileDecision(model="h3", resolution="768p",
                           shot_length_frames=175,
                           seed_policy="fixed_per_story",
                           wangp_profile="profile3")


def test_three_briefs_split_into_exactly_three_shots():
    """The exact live bug: 3 briefs must parse as 3 shots under wgp's
    OWN regex (mirrored from multishot.py:49)."""
    settings = build_settings(
        [_brief("shot A"), _brief("shot B"), _brief("shot C")],
        _decision())
    parts = [p for p in _WGP_SPLIT.split(settings["script"]) if p.strip()]
    assert len(parts) == 3, parts
    assert "shot A" in parts[0]
    assert "shot B" in parts[1]
    assert "shot C" in parts[2]


def test_single_brief_has_no_separator_line():
    settings = build_settings([_brief("solo")], _decision())
    assert not _WGP_SPLIT.search(settings["script"])
    assert "---" not in settings["script"]


def test_build_script_joins_with_own_line_separator():
    out = build_script(["a", "b"])
    parts = [p.strip() for p in _WGP_SPLIT.split(out) if p.strip()]
    assert parts == ["a", "b"]  # wgp strips each segment
