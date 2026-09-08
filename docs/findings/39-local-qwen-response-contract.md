# Finding #39 — local Qwen-VL did not honor the structured score contract

**Status:** Confirmed by the repo-owned local-judge acceptance rerun,
2026-09-07.

With `WANGP_VISION_BACKEND=local`, the first cut rendered on the 3090 and the
repo reached the host's llama-server successfully. The model response did not
contain a JSON object with `mouth_sync`, `action_match`, and
`speaker_attribution`; the strict parser rejected it and the queue recorded a
terminal `qc_gate` failure. No visual scores were invented, and cuts 2–6
remained pending.

## Minimal PR

Pin the local llama-server request to a vision-capable message shape and a
JSON-constrained response format supported by that deployment (or add a
strict, bounded response-normalization step that still rejects missing or
ambiguous scores). Add a live-contract fixture covering the server's actual
response shape. Keep the gate fail-closed when the model cannot return all
three numeric scores.
