"""image_end FLF support (phase 3c): settings carry image_end + SE flag."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from host.wangp_adapter import _build_fl2va_settings_doc  # noqa: E402
from predict.profile_selector import ProfileDecision  # noqa: E402


def _job(**kw):
    base = {"prompt": "subject", "frames": 56, "steps": 20}
    base.update(kw)
    return base


DEC = ProfileDecision(model="h3", resolution="768p",
                      shot_length_frames=56, seed_policy="fixed_per_shot",
                      wangp_profile="profile3")


def test_no_image_end_no_flag():
    s, _ = _build_fl2va_settings_doc(_job(), DEC)
    assert "image_end" not in s
    assert s.get("image_prompt_type", "I") != "SE" or "image_start" in s


def test_image_end_string_sets_se():
    s, _ = _build_fl2va_settings_doc(
        _job(image_end="/tmp/pose.png"), DEC)
    assert s["image_end"] == "/tmp/pose.png"
    assert s["image_prompt_type"] == "SE"


def test_image_end_dict_unwraps_path():
    s, _ = _build_fl2va_settings_doc(
        _job(image_end={"path": "/tmp/p2.png", "kind": "pose"}), DEC)
    assert s["image_end"] == "/tmp/p2.png"
    assert s["image_prompt_type"] == "SE"


def test_image_end_only_sets_E():
    s, _ = _build_fl2va_settings_doc(
        _job(image_end="/tmp/pose.png"), DEC)
    assert s["image_end"] == "/tmp/pose.png"
    assert s["image_prompt_type"] == "E"


def test_image_start_and_end_both_carry():
    s, _ = _build_fl2va_settings_doc(
        _job(image_start="/tmp/a.png", image_end="/tmp/b.png"), DEC)
    assert s["image_start"] == "/tmp/a.png"
    assert s["image_end"] == "/tmp/b.png"
    assert s["image_prompt_type"] == "SE"
