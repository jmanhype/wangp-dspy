# Finding #34 — the blocking vision contract has no live production adapter

**Status:** Confirmed 2026-09-07; blocks the requested rerun.

`qc/audio_critic/vision_judge.py` intentionally exposes only an injected
callable returning `mouth_sync`, `action_match`, and
`speaker_attribution`. `scripts/run_jobs.py` has no default judge wiring or
CLI configuration. `predict/continuation_lane.py` documents Qwen3.8 as a
separate API-side component, but no adapter implements that contract.

The older `scripts/run_qc.py` path is an out-of-band scalar comic critic; it
does not return the required three metrics and is not connected to the
`render_for_job` queue executor. Supplying a fake callable would defeat the
new hard gate and produce another meaningless verdict.

## Minimal PR

Implement a repo-owned `VisionJudge` adapter for the configured 3090/API VLM,
including local/remote media mapping, a typed response parser for the three
required scores, timeout/error handling, and an explicit `run_jobs` wiring
option. Add an integration test proving a live response is persisted before a
`KEEP` verdict is emitted.
