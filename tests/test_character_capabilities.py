"""Real-process no-GPU coverage for portable character continuity."""
from __future__ import annotations

from predict.character_packages import (
    PACKAGE_SCHEMA_VERSION,
    AppearanceInput,
    AppearanceRole,
    CharacterDefinition,
    ContinuityConstraint,
    ContinuityContract,
    ContinuityMode,
    IdentityMetric,
)


def test_character_definition_format_is_typed() -> None:
    definition = CharacterDefinition.model_validate(
        {
            "schema_version": PACKAGE_SCHEMA_VERSION,
            "character_id": "Orin Vale",
            "speaker_label": "Orin",
            "version": 1,
            "description": "Operator-created fictional scientist",
            "appearance": [
                {
                    "path": "appearance/native.png",
                    "sha256": "a" * 64,
                    "role": "native",
                    "width": 2048,
                    "height": 2048,
                    "source_path": "/authorized/originals/orin-native.png",
                    "license": "operator-recorded licence",
                    "consent_ref": "orin-appearance-consent",
                }
            ],
            "continuity": {
                "modes": ["image", "video"],
                "constraints": [
                    {"metric": "face_embedding_cosine", "threshold": 0.75},
                    {"metric": "cross_mode_binding", "threshold": 1.0},
                ],
            },
            "recipe_seed": 907,
        }
    )
    assert definition.appearance[0].role is AppearanceRole.native
    assert definition.continuity.modes == (
        ContinuityMode.image,
        ContinuityMode.video,
    )
    assert IdentityMetric.cross_mode_binding in {
        constraint.metric for constraint in definition.continuity.constraints
    }
