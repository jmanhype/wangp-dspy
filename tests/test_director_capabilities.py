"""Real-process no-GPU coverage for the director composition lane."""
from __future__ import annotations


def test_typed_director_request_models_are_frozen() -> None:
    from services.director.composition import DirectorMode, DirectorRequest

    request = DirectorRequest.model_validate({
        "schema_version": "wangp-dspy.director-request/v1",
        "mode": "prompt",
        "title": "Typed model checkpoint",
        "prompt": "A projected sunrise fails over an observatory dome.",
        "pacing": {
            "strategy": "even", "target_duration_s": 4.666666666666667,
            "clip_count": 2,
        },
        "review": {"mode": "manual", "manual_checkpoint_required": True, "reviewer": "operator"},
        "recipe_seed": 914,
    })
    assert request.mode is DirectorMode.prompt
    assert request.model_config["frozen"] is True
