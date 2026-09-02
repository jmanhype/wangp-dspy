"""RED tests — semantic product-mode routing table (PR #62 amendment).

Five product modes, typed enforcement before any config emits, model_type
DERIVED (never input), render_profile as the only not-a-mode list, turbo
gate reuse, CONTINUATION verified-prior + unwrap. No GPU.
"""
import pytest

from services.jobs.modes import (
    ModeError,
    ProductMode,
    derive_model_type,
    unwrap_continuation,
    validate_mode_inputs,
)


def _spec(**kw):
    base = {"mode": "FL2VA_TEXT", "prompt": "a shot"}
    base.update(kw)
    return {k: v for k, v in base.items() if v is not None}


class TestRule1Enum:
    def test_unknown_mode_rejected(self):
        with pytest.raises(ModeError):
            validate_mode_inputs(_spec(mode="I2VA_GOLD"))

    def test_missing_mode_rejected(self):
        with pytest.raises(ModeError):
            validate_mode_inputs({"prompt": "x"})

    def test_exactly_five_modes(self):
        assert {m.value for m in ProductMode} == {
            "FL2VA_TEXT", "FL2VA_START_END", "FL2VA_END_ONLY",
            "REF2VA_IDENTITY_AUDIO", "CONTINUATION"}


class TestRule2Inputs:
    def test_fl2va_text_forbids_frames_and_audio_refs(self):
        with pytest.raises(ModeError):
            validate_mode_inputs(_spec(image_start="a.png"))
        with pytest.raises(ModeError):
            validate_mode_inputs(_spec(audio_guide="a.wav"))

    def test_start_end_requires_both(self):
        with pytest.raises(ModeError):
            validate_mode_inputs(_spec(mode="FL2VA_START_END",
                                       image_start="a.png"))
        validate_mode_inputs(_spec(mode="FL2VA_START_END",
                                   image_start="a.png",
                                   image_end="b.png"))

    def test_end_only_requires_exactly_one_end_no_start(self):
        validate_mode_inputs(_spec(mode="FL2VA_END_ONLY",
                                   image_end=["b.png"]))
        with pytest.raises(ModeError):
            validate_mode_inputs(_spec(mode="FL2VA_END_ONLY"))  # none
        with pytest.raises(ModeError):
            validate_mode_inputs(_spec(mode="FL2VA_END_ONLY",
                                       image_end=["b.png", "c.png"]))
        with pytest.raises(ModeError):
            validate_mode_inputs(_spec(mode="FL2VA_END_ONLY",
                                       image_start="a.png",
                                       image_end=["b.png"]))

    def test_ref2va_requires_images_and_audio(self):
        with pytest.raises(ModeError):
            validate_mode_inputs(_spec(mode="REF2VA_IDENTITY_AUDIO",
                                       audio_guide="a.wav"))
        with pytest.raises(ModeError):
            validate_mode_inputs(_spec(mode="REF2VA_IDENTITY_AUDIO",
                                       image_refs=["a.png"]))
        validate_mode_inputs(_spec(mode="REF2VA_IDENTITY_AUDIO",
                                   image_refs=["a.png"],
                                   audio_guide="a.wav"))


class TestRule3ModelTypeDerived:
    def test_raw_model_type_input_rejected(self):
        with pytest.raises(ModeError):
            validate_mode_inputs(
                _spec(model_type="minimax_h3_fl2va_pruned"))

    def test_derive_never_user_entered(self):
        assert derive_model_type("FL2VA_TEXT") == (
            "minimax_h3_fl2va_pruned")
        assert derive_model_type("FL2VA_START_END") == (
            "minimax_h3_fl2va_pruned")
        assert derive_model_type("FL2VA_END_ONLY") == (
            "minimax_h3_fl2va_pruned")
        assert derive_model_type("REF2VA_IDENTITY_AUDIO") == (
            "minimax_h3_ref2va_lip_sync")


class TestRule4RenderProfile:
    def test_render_profile_keys_whitelisted(self):
        validate_mode_inputs(_spec(render_profile={
            "pruned": True, "int8": False, "pdd": False, "turbo": False,
            "attention": "sdpa", "steps": 20, "cache": "spectrum"}))
        with pytest.raises(ModeError):
            validate_mode_inputs(_spec(render_profile={"mode": "x"}))

    def test_render_profile_not_a_dict_rejected(self):
        with pytest.raises(ModeError):
            validate_mode_inputs(_spec(render_profile="pruned"))


class TestRule5TurboMultiRef:
    def test_turbo_rejected_on_multi_ref_ref2va(self):
        with pytest.raises(ModeError):
            validate_mode_inputs(_spec(
                mode="REF2VA_IDENTITY_AUDIO",
                image_refs=["a.png", "b.png"], audio_guide="a.wav",
                render_profile={"turbo": True}))

    def test_turbo_ok_single_ref_ref2va(self):
        validate_mode_inputs(_spec(
            mode="REF2VA_IDENTITY_AUDIO", image_refs=["a.png"],
            audio_guide="a.wav", render_profile={"turbo": True}))


class TestRule6ContinuationVerifiedPrior:
    def _cont(self, **kw):
        base = {"mode": "CONTINUATION",
                "temporal_strategy": "last_frame_chain",
                "continuation_mode": "FL2VA_START_END",
                "image_end": "b.png",
                "prior_clip": {"path": "/renders/cut1.mp4",
                               "last_frame": "/frames/cut1_last.png"}}
        base.update(kw)
        return {k: v for k, v in base.items() if v is not None}

    def test_bad_temporal_strategy_rejected(self):
        with pytest.raises(ModeError):
            validate_mode_inputs(
                self._cont(temporal_strategy="hope"),
                verified_artifacts=set())

    def test_unverified_prior_rejected(self):
        with pytest.raises(ModeError):
            validate_mode_inputs(self._cont(
                prior_clip={"path": "/made/up.mp4"}),
                verified_artifacts=set())

    def test_verified_prior_passes(self):
        validate_mode_inputs(
            self._cont(),
            verified_artifacts={"/renders/cut1.mp4",
                                "/frames/cut1_last.png"})

    def test_fabricated_frame_path_rejected(self):
        with pytest.raises(ModeError):
            validate_mode_inputs(
                self._cont(prior_clip={"path": "/renders/cut1.mp4",
                                       "last_frame": "/nope.png"}),
                verified_artifacts={"/renders/cut1.mp4"})


class TestUnwrap:
    def test_continuation_unwraps_before_render(self):
        spec = {"mode": "CONTINUATION",
                "temporal_strategy": "last_frame_chain",
                "continuation_mode": "FL2VA_START_END",
                "image_end": "b.png",
                "prior_clip": {"path": "/renders/cut1.mp4",
                               "last_frame": "/frames/cut1_last.png"},
                "prompt": "next shot"}
        out = unwrap_continuation(
            spec, verified_artifacts={"/renders/cut1.mp4",
                                      "/frames/cut1_last.png"})
        assert out["mode"] == "FL2VA_START_END"
        assert out["temporal_strategy"] == "last_frame_chain"
        # last_frame_chain: the verified prior last frame seeds the start
        assert out["image_start"] == "/frames/cut1_last.png"
        assert out["image_end"] == "b.png"
        assert "CONTINUATION" not in str(out["mode"])


class TestL2VAMapping:
    def test_l2va_maps_to_end_frame_only(self):
        """WanGP ground truth: FL2VA-family allows TSEVL; flags come
        from image_start/image_end — end-only renders as image_prompt_type
        'E' with NO start image (an S flag requires image_start)."""
        doc = derive_model_type("FL2VA_END_ONLY", detail=True)
        assert doc["image_prompt_type"] == "E"
        doc2 = derive_model_type("FL2VA_TEXT", detail=True)
        assert doc2["image_prompt_type"] == "T"
        doc3 = derive_model_type("FL2VA_START_END", detail=True)
        assert doc3["image_prompt_type"] == "SE"
        doc4 = derive_model_type("REF2VA_IDENTITY_AUDIO", detail=True)
        assert doc4["image_prompt_type"] == "I"


class TestExecutorWiring:
    def test_render_lane_for_accepts_enum_modes(self):
        from services.jobs.executor import render_lane_for
        assert render_lane_for("REF2VA_IDENTITY_AUDIO") == "ref2va"
        assert render_lane_for("FL2VA_TEXT") == "fl2va"
        assert render_lane_for("FL2VA_START_END") == "fl2va"
        assert render_lane_for("FL2VA_END_ONLY") == "fl2va"
        # CONTINUATION is not a model mode: it must unwrap, not dispatch
        with pytest.raises(ModeError):
            render_lane_for("CONTINUATION")
