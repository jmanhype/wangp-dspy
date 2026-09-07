"""Single source of truth for WanGP model identifiers.

Only the production handler names live here.  Legacy strings are retained
solely as input aliases for old manifests; no builder may emit them.
"""
from __future__ import annotations

from typing import FrozenSet

H3_FL2VA_MODEL_TYPE = "minimax_h3_fl2va_pruned"
REF2VA_MODEL_TYPE = "minimax_h3_ref2va_pruned"
REF2VA_MODEL_TYPE_LEGACY = "minimax_h3_ref2va_lip_sync"

HOST_MODEL_ALLOWLIST: FrozenSet[str] = frozenset({
    H3_FL2VA_MODEL_TYPE,
    "minimax_h3_ref2va",
    REF2VA_MODEL_TYPE,
})

__all__ = [
    "H3_FL2VA_MODEL_TYPE",
    "REF2VA_MODEL_TYPE",
    "REF2VA_MODEL_TYPE_LEGACY",
    "HOST_MODEL_ALLOWLIST",
]
