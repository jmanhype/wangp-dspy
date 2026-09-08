# Finding #41 — local judge timeout is shorter than the live deployment latency

**Status:** Confirmed by the first post-#39 acceptance rerun,
2026-09-07.

The fixed adapter reached the 3090 host and rendered the first 56-frame cut,
but its visual request exhausted the 180-second local-judge deadline with no
response.  A standalone adapter smoke immediately before/after the run did
return a valid score object, so this is not a response-contract failure.
The live llama-server process is currently launched with
`--n-gpu-layers 0` (CPU inference for the 27B Qwen-VL model), making latency
variable and close to the current deadline.

## Minimal PR / operations change

Prefer a GPU-layered llama-server launch for the judge, with a readiness and
bounded-latency smoke before the acceptance drain.  If CPU inference is an
intentional deployment, configure `WANGP_LOCAL_VISION_TIMEOUT` to a measured
budget (at least 300 seconds) rather than silently weakening the gate; the
adapter must continue to fail closed on timeout.
