"""Explicit auto/manual review policy without weakening real gates."""
from __future__ import annotations

from typing import Any

from services.director.composition import DirectorError, DirectorRequest

MANDATORY_GATES = (
    "whisper_transcript",
    "identity_vision",
    "mouth_box_consensus",
    "syncnet_av",
)


def review_policy(request: DirectorRequest) -> dict[str, Any]:
    mode = request.review.mode.value
    if mode == "auto" and request.review.manual_checkpoint_required:
        raise DirectorError(
            "DIRECTOR_REVIEW_MODE_CONFLICT",
            "review mode auto cannot require a manual-only checkpoint",
            "Use manual review, or let every mandatory gate decide automatic advancement.",
            next_command="wgp director plan --request <request> --json",
        )
    checkpoints = [
        {"name": "before_queue", "decision": "planning_admission"},
        {"name": "after_clip", "decision": "all_mandatory_gates"},
        {"name": "before_assembly", "decision": "all_mandatory_gates"},
        {"name": "final_film", "decision": "all_mandatory_gates"},
    ]
    return {
        "mode": mode,
        "reviewer": request.review.reviewer,
        "manual_checkpoint_required": request.review.manual_checkpoint_required,
        "mandatory_gates": list(MANDATORY_GATES),
        "checkpoints": checkpoints,
        "auto_advancement": mode == "auto" and all(
            checkpoint["decision"] == "all_mandatory_gates" for checkpoint in checkpoints[1:]
        ),
        "bypasses_gate": False,
        "generated_media_reviewed": False,
    }


__all__ = ["MANDATORY_GATES", "review_policy"]
