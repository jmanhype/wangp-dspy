"""Deterministic prompt gates (no LLM, no network)."""
from gates.no_names_gate import (  # noqa: F401
    NameViolation, check_no_proper_nouns, load_registry)
