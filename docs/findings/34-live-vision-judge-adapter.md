# Finding #34 — the blocking vision contract has no live production adapter

**Status:** Confirmed and adapter implemented 2026-09-07; live credentials and
premise roster are still required for the rerun.

`qc/audio_critic/vision_judge.py` intentionally exposes only an injected
callable returning `mouth_sync`, `action_match`, and
`speaker_attribution`. `scripts/run_jobs.py` has no default judge wiring or
CLI configuration. `predict/continuation_lane.py` documents Qwen3.8 as a
separate API-side component, but no adapter implements that contract.

The older `scripts/run_qc.py` path is an out-of-band scalar comic critic; it
does not return the required three metrics and is not connected to the
`render_for_job` queue executor. Supplying a fake callable would defeat the
new hard gate and produce another meaningless verdict.

## Closing PR (implemented)

`qc/audio_critic/modelscope_vision_judge.py` now implements the ModelScope
Qwen-VL callable: it extracts start/middle/end frames, sends identity-aware
image prompts, parses the three required scores, and fails closed on missing
credentials, malformed responses, or extraction/API errors. `run_jobs.py` and
`run_film.py` load it from `MODELSCOPE_API_KEY`, `MODELSCOPE_TOKEN`, or
`MODELSCOPE_API_TOKEN` before production work; tests cover the API and frame
contract.
