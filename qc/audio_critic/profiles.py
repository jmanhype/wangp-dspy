"""audio critic rubric profiles — data, not code paths (slice 1).

Contract: docs/PROPOSAL_audio_critic_service.md.

MUSIC_SYSTEM_PROMPT is BYTE-IDENTICAL to the SGFLIX audio factory
script's --prompt default (3090:/mnt/bulk/home/straughter/
sgflix_audio_factory/scripts/qwen2_audio_critic.py, argparse default).
That byte-equality is the compatibility invariant for the music lane
("adopt the service, keep the behavior") and is pinned by a RED test
that parses the actual script from fixtures/.
"""
from __future__ import annotations

MUSIC_SYSTEM_PROMPT = (
    "Analyze this audio track. Do the vocals sound on-beat at 130 BPM? "
    "Critique the flow, timing, and vocal clarity, then give a score "
    "from 0 to 40 based on its quality."
)

# delivery lane rubric (slice 4 defines the judge; the data lands now)
DELIVERY_SYSTEM_PROMPT = (
    "Analyze this comedic delivery. Critique the pacing, timing, "
    "commitment to the bit, and vocal clarity, then give a score from "
    "0 to 40 based on the delivery quality."
)

PROFILES = {
    "music": {
        # decisions mirror the factory's existing vocabulary exactly
        "system_prompt": MUSIC_SYSTEM_PROMPT,
        "score_scale": [0, 40],
        "flags": [
            "timing_drift",     # off-beat vocals (prose: "off-beat")
            "muddy_vocals",     # unclear/clarity complaints
            "background_noise", # "background noises"
            "weak_flow",        # flow complaints without timing
            "good_clarity",     # explicit clarity praise
        ],
        "decisions": ("keeper_candidate", "reject"),
    },
    "delivery": {
        # decisions mirror RenderQC's verdict enum so the comic lane
        # composes without translation
        "system_prompt": DELIVERY_SYSTEM_PROMPT,
        "score_scale": [0, 40],
        "flags": [
            "flat_delivery",
            "rushed_pacing",
            "timing_off",
            "weak_commit",
            "mumbled",
        ],
        "decisions": ("pass", "revise", "reject"),
    },
}
