"""Explicit cross-clip continuity declarations for director plans."""
from __future__ import annotations

from typing import Any

from services.director.composition import DirectorError, DirectorMode, DirectorRequest
from services.director.pacing import PacingWindow


def _error(observed: str, remediation: str, **metadata: Any) -> DirectorError:
    return DirectorError(
        "DIRECTOR_CONTINUITY_INVALID",
        observed,
        remediation,
        next_command="wgp director plan --request <request> --db <plan.db> --json",
        metadata=metadata,
    )


def continuity_declarations(
    request: DirectorRequest, windows: list[PacingWindow]
) -> dict[str, Any]:
    """Return checked state transitions; presence of a name is not continuity."""

    if request.mode is not DirectorMode.screenplay:
        declarations = []
        for window in windows:
            declarations.append({
                "clip_index": window.index,
                "kind": "single_source_continuity",
                "location": "source-declared composition location",
                "appearance": "source-declared appearance carries forward unchanged",
                "voice": "source-declared voice carries forward unchanged",
                "changes": [],
            })
        return {
            "mode": request.mode.value,
            "status": "declared",
            "characters": [],
            "clips": declarations,
        }

    assert request.screenplay is not None
    roster = {character.name: character for character in request.screenplay.characters}
    if len(roster) != len(request.screenplay.characters):
        raise _error("screenplay character roster contains duplicate names")
    by_scene = {scene.scene_index: scene for scene in request.screenplay.scenes}
    declarations = []
    previous = {
        character.name: character for character in request.screenplay.characters
    }
    for window in windows:
        scene = by_scene.get(window.scene_index)
        if scene is None:
            raise _error(f"clip {window.index} has no screenplay scene")
        unknown = set(scene.characters) - set(roster)
        if unknown:
            raise DirectorError(
                "DIRECTOR_CHARACTER_REFERENCE_UNKNOWN",
                f"scene {scene.scene_index} references unknown characters {sorted(unknown)}",
                "Add an explicit roster entry and appearance/voice state for every scene character.",
                next_command="wgp director plan --request <request> --db <plan.db> --json",
                metadata={"scene_index": scene.scene_index, "characters": sorted(unknown)},
            )
        scene_states = {state.name: state for state in scene.states}
        changed = []
        for name in sorted(scene.characters):
            before = previous[name]
            state = scene_states[name]
            if state.appearance != before.appearance or state.voice != before.voice:
                changed.append({
                    "character": name,
                    "appearance": state.appearance,
                    "voice": state.voice,
                    "from": {"appearance": before.appearance, "voice": before.voice},
                })
        previous = scene_states
        declarations.append({
            "clip_index": window.index,
            "scene_index": scene.scene_index,
            "slugline": scene.slugline,
            "location": scene.location,
            "characters": list(scene.characters),
            "states": [state.model_dump(mode="json") for state in scene.states],
            "changes": changed,
            "carried_forward": sorted(set(scene.characters) - {item["character"] for item in changed}),
        })
    return {
        "mode": "screenplay",
        "status": "declared_and_checked",
        "characters": [item.model_dump(mode="json") for item in request.screenplay.characters],
        "clips": declarations,
    }


__all__ = ["continuity_declarations"]
