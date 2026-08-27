"""ProfileSelectorSignature — brief -> render-profile decision."""

import dspy


class ProfileSelectorSignature(dspy.Signature):
    """Choose a WanGP/H3 render profile for a render brief.

    Output ONE JSON object with EXACTLY these keys:
      model: "h3" or "wan2gp"
      resolution: "720p" or "768p"
      shot_length_frames: integer >= 96 (4s @ 24fps hard floor)
      seed_policy: "fixed_per_story" | "fixed_per_shot" |
                   "derived_from_brief"
      wangp_profile: one of profile1, profile2, profile3

    Choose based on the brief's style/texture demands (H3 for
    photoreal film looks), camera complexity, and motion intensity.
    Output the JSON object only.

    LANGUAGE-CLASS CONTRACT (WD-c4gw): `decision` is ENGINE-BOUND —
    LOCKED ENGLISH (machine-parsed JSON; profile-pass.md:16).
    """
    subject: str = dspy.InputField()
    motion: str = dspy.InputField()
    camera: str = dspy.InputField()
    style: str = dspy.InputField()
    decision: str = dspy.OutputField(
        desc="JSON object: model, resolution, shot_length_frames, "
             "seed_policy, wangp_profile")
