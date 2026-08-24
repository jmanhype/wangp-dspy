"""Task registry — genre -> dataset -> metric -> QC profile.

WD-pt60 (j9nx-1), per the dspy-gepa-example per-task pattern: adding a
task = one registry entry, zero edits to existing ones. j9nx-3 renders
self-register here; j9nx-4 GEPA runs target one genre at a time via
the same entries.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from evaluate.render_qc import GENRE_THRESHOLDS


@dataclass(frozen=True)
class TaskSpec:
    genre: str                      # QC profile key (GENRE_THRESHOLDS)
    dataset: str                    # datasets/<name>.py module name
    metric: str                     # metrics/<name>.py callable name
    description: str = ""
    tags: tuple = ()


_REGISTRY: Dict[str, TaskSpec] = {}


def register(spec: TaskSpec) -> TaskSpec:
    if spec.genre in _REGISTRY:
        raise ValueError(
            f"task {spec.genre!r} already registered; tasks are "
            f"append-only — pick a new genre name")
    if spec.genre not in GENRE_THRESHOLDS:
        raise ValueError(
            f"task {spec.genre!r} has no QC profile; known genres: "
            f"{sorted(GENRE_THRESHOLDS)}")
    _REGISTRY[spec.genre] = spec
    return spec


def get(genre: str) -> TaskSpec:
    try:
        return _REGISTRY[genre]
    except KeyError:
        raise KeyError(
            f"no task registered for genre {genre!r}; registered: "
            f"{sorted(_REGISTRY)}") from None


def all_tasks() -> List[TaskSpec]:
    return list(_REGISTRY.values())


# ── seed tasks (the four QC genres wired at this pin) ──────────────
register(TaskSpec(
    genre="surreal",
    dataset="surreal",
    metric="qc_feedback",
    description="surreal lane (threshold 4.5) — the WD-t6i7 smoke genre"))
register(TaskSpec(
    genre="music",
    dataset="music",
    metric="qc_feedback",
    description="music lane (threshold 5.0) — MV beat-grid territory"))
