"""Model-agnostic critique core (slice 2).

Contract: docs/PROPOSAL_audio_critic_service.md — "conversation
assembly (mono reference+candidate pattern, matching the proven
script), generation params, strict output parsing with typed
retry-on-malformed (one retry with an 'obey the schema' nudge, then
typed failure — never silent prose passthrough)".

The conversation shape and generation params are pinned to the proven
factory script (fixtures/qwen2_audio_critic.py): single user turn,
audio parts (reference first when present) then text prompt;
max_new_tokens=512; torch_dtype bfloat16. The model callable is
INJECTED — tests pass a fake; the 3090 service passes the real
transformers pipeline.
"""
from __future__ import annotations

from typing import Callable, Optional

from qc.audio_critic.extract import extract_structured
from qc.audio_critic.profiles import PROFILES
from qc.audio_critic.schema import (
    AudioCriticError, build_critique,
)

MAX_NEW_TOKENS = 512          # pinned to the factory script
MODEL_DTYPE = "bfloat16"      # pinned to the factory script
DEFAULT_MODEL_ID = "Qwen/Qwen2-Audio-7B-Instruct"

NUDGE = ("Your previous reply could not be parsed for a score. Obey "
         "the schema: critique briefly, then give an explicit score "
         "as 'N out of 40'.")

# CANONICAL SEAM SHAPE (fix/audio-critic-generate-contract): the
# single contract every generate callable must satisfy — exactly
# what run_critique passes and exactly what the service core and
# tests may rely on. The callable receives a PROMPT STRING (never a
# prebuilt conversation) plus optional audio (waveform array or
# list of arrays; Qwen2-Audio feature extractor resamples) plus
# generation kwargs; it returns the prose string. Chat-format
# assembly (audio part(s) first, then text — factory-script
# pattern) happens INSIDE the callable via apply_chat_template.
GenerateCallable = Callable[..., str]


def assemble_conversation(profile: str, *, audio_path: str,
                          reference_path: Optional[str] = None) -> list:
    """Build the chat-template conversation exactly like the proven
    script: one user turn, content parts audio(+ref first)+text."""
    if profile not in PROFILES:
        raise AudioCriticError(f"unknown profile: {profile!r}")
    content: list = []
    if reference_path is not None:
        content.append({"type": "audio", "audio_url": reference_path})
    content.append({"type": "audio", "audio_url": audio_path})
    content.append({"type": "text",
                    "text": PROFILES[profile]["system_prompt"]})
    return [{"role": "user", "content": content}]


def generation_kwargs() -> dict:
    """Decoding params pinned to the factory script.

    Judge-consistency fix (PR #17 follow-up): greedy decode gave
    perfect determinism but INVERTED ordering (operator's best
    take 8/40, mediocre 35 — classic greedy degeneration on judge
    tasks). DEFAULT is now light sampling: do_sample=True,
    temperature=0.3, top_p=1.0, paired with the service-level
    median ensemble for stability. Greedy remains reachable via
    caller kw override (seam intact)."""
    return {"max_new_tokens": MAX_NEW_TOKENS,
            "do_sample": True, "temperature": 0.3, "top_p": 1.0}


def ensemble_scores(scores: list) -> float:
    """Median of an odd-length score list (middle element)."""
    ordered = sorted(scores)
    n = len(ordered)
    if n == 0:
        raise ValueError("ensemble_scores: empty list")
    mid = n // 2
    return ordered[mid]


def aggregate_ensemble(runs: list) -> dict:
    """Aggregate ensemble runs by MEDIAN score; the prose of the
    median-scoring run is kept; all scores recorded."""
    if not runs:
        raise ValueError("aggregate_ensemble: empty runs")
    med = ensemble_scores([r["score"] for r in runs])
    keeper = min(
        runs, key=lambda r: (abs(r["score"] - med),))
    # exact member of the median (prefer the first equal-scored)
    for r in runs:
        if r["score"] == med:
            keeper = r
            break
    out = dict(keeper)
    out["score"] = med
    out["scores_list"] = [r["score"] for r in runs]
    out["ensemble"] = len(runs) > 1
    return out


def criticize_once(profile: str, prose: str, *, model: str) -> dict:
    """Parse one raw generation through the slice-1 extractor."""
    structured = extract_structured(profile, prose)
    return {"prose": prose, "structured": structured}


def run_critique(profile: str,
                 generate: Callable[..., str],
                 *,
                 model: str = DEFAULT_MODEL_ID,
                 prompt: Optional[str] = None,
                 audio=None, audios=None) -> dict:
    """Full critique loop with the ONE-retry malformed policy.

    generate(prompt, **generation_kwargs) -> prose str. On a
    not-parse_ok generation: exactly one retry with NUDGE appended;
    still malformed -> typed AudioCriticError (never silent prose
    passthrough).

    audio (16kHz mono float waveform) and audios (separate
    waveforms, e.g. references) are forwarded to generate per the
    GenerateCallable contract (PR #49); injected fakes may ignore
    them."""
    kwargs = {}
    if audio is not None:
        kwargs["audio"] = audio
    if audios is not None:
        kwargs["audios"] = audios
    if profile not in PROFILES:
        raise AudioCriticError(f"unknown profile: {profile!r}")
    base_prompt = prompt if prompt is not None \
        else PROFILES[profile]["system_prompt"]

    prose = generate(base_prompt, **generation_kwargs(), **kwargs)
    first = criticize_once(profile, prose, model=model)
    if first["structured"]["parse_ok"]:
        record = build_critique(
            dict(first["structured"], model=model), model=model)
        return {"prose": prose, "record": record, "retried": False}

    prose2 = generate(base_prompt + "\n\n" + NUDGE,
                      **generation_kwargs(), **kwargs)
    second = criticize_once(profile, prose2, model=model)
    if second["structured"]["parse_ok"]:
        record = build_critique(
            dict(second["structured"], model=model), model=model)
        return {"prose": prose2, "record": record, "retried": True}

    raise AudioCriticError(
        "parse: model output malformed after one nudge retry; "
        "no score could be extracted (refusing silent prose "
        "passthrough)")


def load_real_model():
    """Default deployment loader (3090-side).

    Loads Qwen2-Audio-7B-Instruct via transformers (AutoProcessor +
    Qwen2AudioForConditionalGeneration, bfloat16, device_map auto;
    model id from env AC_MODEL_ID, default DEFAULT_MODEL_ID) and
    returns generate(prompt, **kw) -> prose str matching the
    injected-callable interface (apply_chat_template, processor
    audio handling, max_new_tokens pinned to the factory value).

    torch/transformers are imported INSIDE the function so
    CPU-only test environments never need them.
    """
    import os

    import torch  # lazy: GPU-side only
    from transformers import (  # lazy: GPU-side only
        AutoProcessor, Qwen2AudioForConditionalGeneration,
    )

    model_id = os.environ.get("AC_MODEL_ID", DEFAULT_MODEL_ID)
    processor = AutoProcessor.from_pretrained(model_id)
    model = Qwen2AudioForConditionalGeneration.from_pretrained(
        model_id, torch_dtype=torch.bfloat16, device_map="auto")

    sr = processor.feature_extractor.sampling_rate

    def generate(prompt, audio=None, **kw):
        """GenerateCallable: prompt STR (+ optional waveform audio).

        Builds the chat conversation here — the live 3090 crash was
        this callable handing apply_chat_template the prompt string
        directly (AttributeError 'str' object has no attribute
        'get'). Factory-script pattern: audio part(s) first, then
        the text prompt, single user turn."""
        content = []
        audios = None
        if audio is not None:
            # factory-script semantics: audio= is ONE waveform (or
            # array-like); an explicit list of SEPARATE waveforms
            # (e.g. [reference, candidate]) is passed via audios=.
            audios = audio
            content.append({"type": "audio", "audio_url": "audio-0"})
        if kw.get("audios") is not None:
            for i, _ in enumerate(kw.pop("audios"), start=0):
                content.insert(
                    len(content) - (1 if audio is not None else 0),
                    {"type": "audio", "audio_url": f"audio-ref-{i}"})
        content.append({"type": "text", "text": prompt})
        conversation = [{"role": "user", "content": content}]
        text = processor.apply_chat_template(
            conversation, add_generation_prompt=True, tokenize=False)
        inputs = processor(text=text, audio=audios,
                           return_tensors="pt", padding=True)
        inputs = {k: v.to(model.device) for k, v in inputs.items()}
        gkw = dict(generation_kwargs())
        gkw.update(kw)
        with torch.no_grad():
            ids = model.generate(**inputs, **gkw)
        trimmed = [o[len(i):] for o, i in
                   zip(ids, inputs.get("input_ids", ids))]
        return processor.batch_decode(
            trimmed, skip_special_tokens=True,
            clean_up_tokenization_spaces=False)[0]

    generate.sampling_rate = sr
    return generate
