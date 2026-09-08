# Finding #39 — local Qwen-VL did not honor the structured score contract

**Status:** Confirmed and fixed in the repo-owned local-judge adapter,
2026-09-07.

With `WANGP_VISION_BACKEND=local`, the first cut rendered on the 3090 and the
repo reached the host's llama-server successfully. The model response did not
contain a JSON object with `mouth_sync`, `action_match`, and
`speaker_attribution`; the strict parser rejected it and the queue recorded a
terminal `qc_gate` failure. No visual scores were invented, and cuts 2–6
remained pending.

## Root cause

The local deployment is a reasoning Qwen model.  With a short generation
budget it can finish with `finish_reason: "length"`, an empty OpenAI
`message.content`, and the useful answer in `message.reasoning_content`.
The adapter was correct to reject the empty content, but its request and
response handling did not account for this deployment behavior.

## Fix

The local adapter now requests a 1024-token response budget and llama-server's
JSON-object response grammar, while both adapters ask for a single JSON
object on the final line.  The local llama-server adapter additionally sends
`chat_template_kwargs.enable_thinking=false` to disable Qwen's reasoning
trace when supported.  Parsing remains strict:
non-empty `content` is preferred, then `reasoning_content` is used only as a
fallback and must still contain all three numeric 0..1 scores.  Missing or
ambiguous scores continue to fail closed.  Regression fixtures cover the
observed empty-content reasoning response.
