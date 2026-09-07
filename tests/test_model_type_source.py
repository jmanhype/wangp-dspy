"""Finding 14: model identifiers are emitted from one shared module."""
from __future__ import annotations


def test_ref2va_model_constant_is_shared_by_emitters():
    from host.wangp_adapter import REF2VA_MODEL_TYPE as host_name
    from host.ref2va_runtime import REF2VA_MODEL_TYPE as runtime_name
    from predict.model_types import REF2VA_MODEL_TYPE as source_name
    from predict.render_profiles import REF2VA_MODEL_TYPE as profile_name
    from services.jobs.modes import CANONICAL_H3_FOR_MODE, ProductMode

    assert host_name == runtime_name == source_name == profile_name
    assert CANONICAL_H3_FOR_MODE[ProductMode.REF2VA_IDENTITY_AUDIO] == source_name


def test_shared_source_never_emits_legacy_name(tmp_path):
    from predict.model_types import (
        REF2VA_MODEL_TYPE,
        REF2VA_MODEL_TYPE_LEGACY,
    )
    assert REF2VA_MODEL_TYPE != REF2VA_MODEL_TYPE_LEGACY
    assert REF2VA_MODEL_TYPE == "minimax_h3_ref2va_pruned"
