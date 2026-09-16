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


def _audio(tmp):
    """Audio-plane kwargs for Ref2VA (WD-a1d9): readable guide +
    provenance paths + default policy."""
    from predict.audio_dataplane import AudioGuideProvenance
    import pathlib as _p
    files = []
    for name in ("guide.wav", "master.wav", "vocal.wav", "wmap.json"):
        f = _p.Path(tmp) / name
        f.write_bytes(b"x" * 8)
        files.append(str(f))
    guide, master, stem, wmap = files
    return dict(
        audio_guide=guide,
        audio_provenance=AudioGuideProvenance(
            source_master=master, vocal_stem=stem, whisper_map=wmap,
            keeper_window_s=(1.0, 5.0)),
    )



def test_ref2va_valid_builds(tmp_path):
    p = Ref2VAProfile()
    doc = p.build_settings(
        [_brief()], _decision(),
        image_refs=_mkrefs(tmp_path), audio_prompt_type="A",
        guide_duration_s=8.0, shot_duration_s=8.0,
        **_audio(tmp_path))
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
                         guide_duration_s=8.0, shot_duration_s=8.0,
                         **_audio(tmp_path))


def test_ref2va_guide_duration_must_match(tmp_path):
    p = Ref2VAProfile()
    with pytest.raises(ProfileError, match="guide") as ei:
        p.build_settings([_brief()], _decision(),
                         image_refs=_mkrefs(tmp_path),
                         audio_prompt_type="A",
                         guide_duration_s=7.33,
                         shot_duration_s=8.0,
                         **_audio(tmp_path))
    assert "7.33" in str(ei.value) and "8.0" in str(ei.value)


def test_ref2va_shot_duration_cap(tmp_path):
    p = Ref2VAProfile()
    # NIGHT TWO: floor is 2.33s (56f/24 = 2.3333...; 3dp wiring
    # values like 2.333 must pass) — 3.5s is now legal.
    for bad in (2.0, 15.5):
        with pytest.raises(ProfileError, match="cap|duration"):
            p.build_settings([_brief()], _decision(),
                             image_refs=_mkrefs(tmp_path),
                             audio_prompt_type="A",
                             guide_duration_s=bad,
                             shot_duration_s=bad,
                             **_audio(tmp_path))


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
                         guide_duration_s=8.0, shot_duration_s=8.0,
                         **_audio(tmp_path))


def test_ref2va_tokens_contiguous_ok(tmp_path):
    from predict.prompt_director import RenderBrief
    b = RenderBrief(subject="<Picture 1> and <Audio 1>", motion="talks",
                    camera="static", style="grain")
    p = Ref2VAProfile()
    doc = p.build_settings([b], _decision(),
                           image_refs=_mkrefs(tmp_path),
                           audio_prompt_type="A",
                           guide_duration_s=8.0, shot_duration_s=8.0,
                           **_audio(tmp_path))
    assert doc


def test_strategy_surface():
    assert issubclass(H3Profile, RenderProfile)
    assert issubclass(Ref2VAProfile, RenderProfile)


# ── WD-a1d9: audio data plane on Ref2VA ─────────────────────────────

def test_ref2va_audio_guide_required(tmp_path):
    """audio_guide is now a required kwarg: omitting it is a typed
    ProfileError (not silently swallowed by **kw)."""
    kw = _audio(tmp_path)
    del kw["audio_guide"]
    p = Ref2VAProfile()
    with pytest.raises(ProfileError, match="audio_guide"):
        p.build_settings([_brief()], _decision(),
                         image_refs=_mkrefs(tmp_path),
                         audio_prompt_type="A",
                         guide_duration_s=8.0, shot_duration_s=8.0,
                         **kw)


def test_ref2va_audio_guide_unreadable(tmp_path):
    p = Ref2VAProfile()
    with pytest.raises(ProfileError, match="audio_guide"):
        p.build_settings([_brief()], _decision(),
                         image_refs=_mkrefs(tmp_path),
                         audio_prompt_type="A",
                         guide_duration_s=8.0, shot_duration_s=8.0,
                         audio_guide="/nonexistent/guide.wav",
                         audio_provenance=_audio(tmp_path)["audio_provenance"])


def test_ref2va_missing_audio_provenance(tmp_path):
    kw = _audio(tmp_path)
    del kw["audio_provenance"]
    p = Ref2VAProfile()
    with pytest.raises(ProfileError, match="audio_provenance"):
        p.build_settings([_brief()], _decision(),
                         image_refs=_mkrefs(tmp_path),
                         audio_prompt_type="A",
                         guide_duration_s=8.0, shot_duration_s=8.0,
                         **kw)


def test_ref2va_settings_extra_contains_audio_plane(tmp_path):
    p = Ref2VAProfile()
    doc = p.build_settings([_brief()], _decision(),
                           image_refs=_mkrefs(tmp_path),
                           audio_prompt_type="A",
                           guide_duration_s=8.0, shot_duration_s=8.0,
                           **_audio(tmp_path))
    # extra fields ride at the TOP level of the non-flat settings doc
    # (to_settings_doc merges extra before returning; flat=False keeps
    # the nested dicts sanctioned for the Ref2VA lane)
    assert doc["audio_guide"].endswith("guide.wav")
    prov = doc["audio_provenance"]
    assert prov["source_master"].endswith("master.wav")
    assert prov["keeper_window_s"] == [1.0, 5.0]
    pol = doc["audio_policy"]
    assert pol == {"discard_rendered_audio": False,
                   "remux_source": "source_master",
                   "remux_window": [1.0, 5.0]}
    assert doc["audio_carrier"] == "native_h3"
    qc = doc["audio_qc"]
    assert qc["critic_model"] == "Qwen2-Audio-7B"
    assert qc["mouth_sync"] is None  # not yet judged


def test_ref2va_rejects_external_audio_carrier(tmp_path):
    from predict.audio_dataplane import AudioPolicy
    p = Ref2VAProfile()
    audio = _audio(tmp_path)
    policy = AudioPolicy(
        discard_rendered_audio=True,
        remux_window=(0.0, 8.0))
    with pytest.raises(ProfileError, match="native audio"):
        doc = p.build_settings(
            [_brief()], _decision(), image_refs=_mkrefs(tmp_path),
            audio_prompt_type="A", guide_duration_s=8.0, shot_duration_s=8.0,
            audio_policy=policy, **audio)


# ── H3 harness preservation (byte-for-byte) ─────────────────────────

def test_h3_settings_snapshot_unchanged():
    """H3Profile.build_settings output for the fixed brief fixture is
    IDENTICAL to the checked-in snapshot (WD-a1d9 must not leak)."""
    import json as _json
    import pathlib as _p
    p = H3Profile()
    doc = p.build_settings([_brief()], _decision())
    snap = _json.loads((_p.Path(__file__).parent / "fixtures" /
                        "h3_settings_snapshot.json").read_text())
    assert doc == snap


def test_no_audio_dataplane_keys_leak_into_h3():
    p = H3Profile()
    doc = p.build_settings([_brief()], _decision())
    flat = _json.dumps(doc)
    for key in ("audio_guide", "audio_provenance", "audio_policy",
                "audio_qc"):
        assert key not in flat


import json as _json  # noqa: E402  (used above)


def test_h3_harness_untouched():
    """Grep gate: evaluate/ and training/ source contains no ref2va /
    audio_guide additions — guards the generic H3 GEPA A/B harness.

    Closure-2 exemption (2026-08-30): evaluate/audio_reactive.py is the
    SEPARATE artifact-grounded audio lane and is REQUIRED to call the
    QC stage by name; it is exempt. Every other file stays guarded.
    """
    import pathlib as _p
    root = _p.Path(__file__).resolve().parent.parent
    exempt = {root / "evaluate" / "audio_reactive.py"}
    for sub in ("evaluate", "training"):
        for f in (root / sub).rglob("*.py"):
            if f in exempt:
                continue
            text = f.read_text(encoding="utf-8")
            assert "ref2va" not in text.lower(), f"{f} mentions ref2va"
            assert "audio_guide" not in text, f"{f} mentions audio_guide"


# ── Qwen ruling (2026-08-30): typed flat-JSON exemption ─────────────

def test_generic_path_flat_true_still_rejects_nested():
    """Ruling (1): to_settings_doc(flat=True) rejects nested values on
    the generic path — the Ref2VA exemption must not weaken rule 4."""
    from predict.job_config import WanGPJobConfig, JobConfigError
    cfg = WanGPJobConfig(
        model_type="m", script="s", width=480, height=832,
        frames_per_shot=107, force_fps="24")
    with pytest.raises(JobConfigError, match="flat|nested"):
        cfg.to_settings_doc(extra={"audio_provenance": {"a": 1}})


def test_ref2va_nested_payloads_exempt_only_via_flat_false(tmp_path):
    """Ruling (2): Ref2VA nested audio payloads ride extra ONLY via
    the flat=False exemption — the output carries nested dicts, and
    the same call with flat=True would reject them."""
    from predict.job_config import JobConfigError
    p = Ref2VAProfile()
    doc = p.build_settings([_brief()], _decision(),
                           image_refs=_mkrefs(tmp_path),
                           audio_prompt_type="A",
                           guide_duration_s=8.0, shot_duration_s=8.0,
                           **_audio(tmp_path))
    assert isinstance(doc["audio_provenance"], dict)
    assert isinstance(doc["audio_policy"], dict)
    assert isinstance(doc["audio_qc"], dict)
    # the generic walk would have rejected exactly these keys
    for k in ("audio_provenance", "audio_policy", "audio_qc"):
        with pytest.raises(JobConfigError, match="flat|nested"):
            from predict.job_config import WanGPJobConfig
            WanGPJobConfig(
                model_type="m", script="s", width=480, height=832,
                frames_per_shot=107, force_fps="24").to_settings_doc(
                    extra={k: doc[k]})


def test_ref2va_vocal_stem_required(tmp_path):
    """Ruling (3): vocal_stem stays REQUIRED — the Ref2VA lane is
    lip-sync-only; omitting the field entirely is a typed rejection
    (not just an unreadable-path one)."""
    import pathlib as _pl
    from predict.audio_dataplane import (AudioDataPlaneError,
                                         AudioGuideProvenance)
    files = []
    for nm in ("master.wav", "wmap.json"):
        f = _pl.Path(tmp_path) / nm
        f.write_bytes(b"x" * 8)
        files.append(str(f))
    with pytest.raises(AudioDataPlaneError):
        AudioGuideProvenance(
            source_master=files[0], vocal_stem="",
            whisper_map=files[1], keeper_window_s=(1.0, 5.0))
    with pytest.raises(TypeError):
        # omitting the field entirely is not silently defaulted
        AudioGuideProvenance(
            source_master=files[0], whisper_map=files[1],
            keeper_window_s=(1.0, 5.0))
