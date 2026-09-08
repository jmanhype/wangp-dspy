# Finding #42 — GPU-offloaded local judge blocks WanGP model loading

**Status:** Confirmed and fixed in the production executor lifecycle seam;
acceptance rerun pending, 2026-09-07.

The local Qwen judge was moved to GPU (`-ngl 24`) and its latency dropped to
the expected range, but the next repo-only acceptance run failed before the
first denoising line.  WanGP's load-stall watchdog killed the render after
302 seconds; the captured `nvidia-smi` value was `7874 MiB / 24576 MiB`, and
the remote log recommends `PYTORCH_ALLOC_CONF=expandable_segments:True`.
The GPU-offloaded vision server remained resident while H3 loaded, so the
render did not have the memory headroom assumed by the operator's estimate.

No visual scores or assembly were fabricated; the five dependent jobs stayed
pending.

## Fix

`run_jobs.py` now uses the configured `WANGP_JUDGE_CTL` control script for
both SSH and localhost targets.  The hook starts and health-checks the judge
before preflight; the render seam stops it immediately before
`render_for_job()`, then starts it again in a `finally` block before visual
QC.  Control-script failures remain durable render failures, and regression
tests cover the stop/sleep/start ordering.  A server-side
memory/readiness smoke should still run before the six-cut drain.
