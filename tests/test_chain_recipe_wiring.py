"""Shot-1 configs must be built by renderers/h3_recipe.py (not inline)."""
import pytest

import services.chain.controller as controller_module
from services.chain.controller import build_chain_plan, emit_render_manifest
from services.director.renderers.h3_recipe import H3RecipeError


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


DURATIONS = [2.3333333333333335, 2.3333333333333335, 2.3333333333333335]


def _plan():
    return build_chain_plan(_script(), _characters(), DURATIONS,
                            audio_paths=["a0.wav", "a1.wav", "a2.wav"])


class TestShot1GoesThroughRecipe:
    def test_build_render_config_called_for_shot1(self, monkeypatch):
        calls = []
        real = controller_module.build_render_config

        def spy(anchor_plate, character_plates, speaker_index, line,
                audio_path, duration_s, **kwargs):
            calls.append((anchor_plate, character_plates, speaker_index,
                          line, audio_path, duration_s, kwargs))
            return real(anchor_plate, character_plates, speaker_index,
                        line, audio_path, duration_s, **kwargs)

        monkeypatch.setattr(controller_module, "build_render_config", spy)
        manifest = emit_render_manifest(_plan())
        assert len(calls) == 1  # shot 1 only; shots 2+ are continuations
        anchor, plates, speaker_index, line, audio_path, duration_s, _kw = \
            calls[0]
        assert anchor == "plates/s1-anchor.png"
        assert [p["path"] for p in plates] == [
            "plates/s1-plate.png", "plates/s2-plate.png"]
        assert plates[0]["description"] == "engineer, red jacket"
        assert speaker_index == 0  # Ada (S1) speaks shot 1
        assert line == "The reactor is waking up."
        assert audio_path == "a0.wav"
        assert duration_s == pytest.approx(56 / 24)
        assert len(manifest) == 3

    def test_shot1_carries_distinctive_recipe_outputs(self):
        manifest = emit_render_manifest(_plan())
        cfg1 = manifest[0]
        # recipe prompt template footer
        assert "Non-diegetic music: none" in cfg1["prompt"]
        assert "two-shot composition anchor" in cfg1["prompt"]
        # recipe config envelope (spectrum cache, sdpa, profile 3)
        recipe = cfg1["recipe"]
        assert recipe["skip_steps_cache_type"] == "spectrum"
        assert recipe["skip_steps_multiplier"] == 0.08
        assert recipe["attention"] == "sdpa"
        assert recipe["profile"] == 3
        assert recipe["width"], recipe["height"] == (480, 832)
        # chain envelope preserved
        assert cfg1["kind"] == "shot1_three_ref_recipe"
        assert cfg1["image_start"] is None
        assert len(cfg1["image_refs"]) == 3
        assert cfg1["frames"] == 56

    def test_plate_paths_override_defaults(self):
        manifest = emit_render_manifest(
            _plan(),
            plate_paths=["anchor.png", "ada.png", "bo.png"])
        assert manifest[0]["image_refs"] == [
            "anchor.png", "ada.png", "bo.png"]

    def test_recipe_gates_active_through_chain_path(self):
        with pytest.raises(H3RecipeError):
            emit_render_manifest(_plan(), loras=["wan2.2_turbo"])

    def test_recipe_gate_passes_single_ref_turbo(self):
        # turbo with a single character plate (single-ref) is allowed
        script = [{"speaker": "Ada", "text": "Solo line here."}]
        plan = build_chain_plan(script, _characters()[:1],
                                [2.3333333333333335])
        manifest = emit_render_manifest(plan, loras=["wan2.2_turbo"])
        assert manifest[0]["recipe"]["loras"] == ["wan2.2_turbo"]
