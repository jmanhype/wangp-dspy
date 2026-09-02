"""Host-truth model names (operator audit 2026-09-01, production
render seam PR).

The 3090 Wan2GP handler exposes ONLY `minimax_h3_ref2va` and
`minimax_h3_ref2va_pruned` — canonical derivations must be REAL
handler names, and a derivation result off host truth fails closed
(typed ModeError), never crashes on the GPU box.
"""
import pytest

from services.jobs.modes import (
    CANONICAL_H3_FOR_MODE,
    HOST_MODEL_ALLOWLIST,
    ModeError,
    ProductMode,
    derive_model_type,
)
import services.jobs.modes as modes


class TestHostTruthNames:
    def test_ref2va_derives_real_handler_name(self):
        assert derive_model_type(
            "REF2VA_IDENTITY_AUDIO") == "minimax_h3_ref2va_pruned"

    def test_every_canonical_name_is_a_real_host_handler(self):
        for mode, name in CANONICAL_H3_FOR_MODE.items():
            assert name in HOST_MODEL_ALLOWLIST, (mode, name)

    def test_allowlist_is_exactly_both_real_ref2va_handlers(self):
        assert "minimax_h3_ref2va" in HOST_MODEL_ALLOWLIST
        assert "minimax_h3_ref2va_pruned" in HOST_MODEL_ALLOWLIST
        # the old wrong name is NOT host truth
        assert "minimax_h3_ref2va_lip_sync" not in HOST_MODEL_ALLOWLIST

    def test_detail_record_carries_real_name(self):
        out = derive_model_type("REF2VA_IDENTITY_AUDIO", detail=True)
        assert out["model_type"] == "minimax_h3_ref2va_pruned"


class TestFailClosed:
    def test_fake_name_in_map_raises_typed(self, monkeypatch):
        monkeypatch.setitem(
            CANONICAL_H3_FOR_MODE, ProductMode.FL2VA_TEXT,
            "minimax_h3_totally_fake")
        with pytest.raises(ModeError, match="HOST_MODEL_ALLOWLIST"):
            derive_model_type("FL2VA_TEXT")

    def test_fake_ref2va_name_raises_typed(self, monkeypatch):
        monkeypatch.setitem(
            CANONICAL_H3_FOR_MODE, ProductMode.REF2VA_IDENTITY_AUDIO,
            "minimax_h3_ref2va_lip_sync")
        with pytest.raises(ModeError):
            derive_model_type("REF2VA_IDENTITY_AUDIO")


class TestAdapterHostTruth:
    def test_adapter_ref2va_model_type_is_pruned(self):
        from host.wangp_adapter import (
            REF2VA_MODEL_TYPE, REF2VA_MODEL_TYPE_LEGACY,
        )
        assert REF2VA_MODEL_TYPE == "minimax_h3_ref2va_pruned"
        # legacy alias kept for git archaeology only
        assert REF2VA_MODEL_TYPE_LEGACY == "minimax_h3_ref2va_lip_sync"

    def test_job_lane_accepts_both_real_handler_names(self):
        from host.wangp_adapter import job_lane
        assert job_lane({"model_type": "minimax_h3_ref2va"}) == "ref2va"
        assert job_lane(
            {"model_type": "minimax_h3_ref2va_pruned"}) == "ref2va"
        assert job_lane({}) == "fl2va"
