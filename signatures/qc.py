"""RenderQCSignature — rendered clip + brief -> critique JSON."""

import dspy


class RenderQCSignature(dspy.Signature):
    """Critique a rendered video clip against its brief and profile.

    Output ONE JSON object with EXACTLY these keys:
      coherence: 0-10, does the clip hold together visually
      brief_adherence: 0-10, does it match subject/motion/camera/style
      concept_encoding: 0-10, is the core concept legible on screen
      scores: {"coherence": n, "brief_adherence": n,
               "concept_encoding": n}
      notes: one sentence

    Judge strictly; output the JSON object only.
    """
    subject: str = dspy.InputField()
    motion: str = dspy.InputField()
    camera: str = dspy.InputField()
    style: str = dspy.InputField()
    model: str = dspy.InputField()
    shot_length_frames: int = dspy.InputField()
    # QB1: the gate critiques the RENDERED material itself (path to the
    # produced video — the VLM provider resolves frames from it), not a
    # text-only description of the expectation.
    video: str = dspy.InputField(
        desc="path to the rendered video clip to critique")
    critique: str = dspy.OutputField(
        desc="JSON: coherence, brief_adherence, concept_encoding, "
             "scores, notes")
