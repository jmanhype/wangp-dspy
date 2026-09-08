# Finding #42 — GPU-offloaded local judge blocks WanGP model loading

**Status:** Confirmed by the GPU-vision acceptance rerun,
2026-09-07.

The local Qwen judge was moved to GPU (`-ngl 24`) and its latency dropped to
the expected range, but the next repo-only acceptance run failed before the
first denoising line.  WanGP's load-stall watchdog killed the render after
302 seconds; the captured `nvidia-smi` value was `7874 MiB / 24576 MiB`, and
the remote log recommends `PYTORCH_ALLOC_CONF=expandable_segments:True`.
The GPU-offloaded vision server remained resident while H3 loaded, so the
render did not have the memory headroom assumed by the operator's estimate.

No visual scores or assembly were fabricated; the five dependent jobs stayed
pending.

## Minimal PR / operations change

Make local-judge VRAM lifecycle explicit in the production executor: keep the
judge available for preflight, stop or CPU-offload it before WanGP model load,
then restart and health-check it before the post-render vision gate.  A
server-side memory/readiness smoke should run before the six-cut drain, and a
render load stall must remain a durable fail-closed error.
