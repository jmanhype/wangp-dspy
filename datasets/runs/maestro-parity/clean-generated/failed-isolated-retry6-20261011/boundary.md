# WD-bw0h clean-machine retry6 — 2026-10-11

## Outcome

The operator-authorized one-shot retry6 stopped fail-closed at generic host preflight.
It did **not** admit a queue job, render video, or produce canonical generated-artifact
evidence.

- Wangp execution head: `238aaeca42fd7b0a012d2d606301e56cfe6bb6d1`
- Exact-head main CI run `38174638107`: success
- Operator authorization canonical SHA-256:
  `591fe7f933eeb45ce34e965b9fcad94966bec8267b90069e999097c75b901014`
- Fresh remote root:
  `/home/straughter/Wan2GP/wd-bw0h-clean-generated-retry6-20261011`

## What succeeded before the boundary

- Clean disposable workspace and checkout.
- Exact committed reference-frame and prompt provenance validation.
- Fresh remote-root creation.
- Exact-host reference staging and byte round-trip.
- PyAV compatibility staging and model-free media-write preflight.
- All four exact model hashes.
- SSH, GPU-idle, and QC-health checks.
- Authorized storage preparation preserved two inactive, non-H3 model trees as
  reversible HDD copies/symlinks:
  - PinkCherry: 34,038,892,728 bytes, manifest SHA-256
    `393df27ecea7fffeb16cdcae6ce0649e797f4ebfc8a48dc5c8c209529963de69`
  - Glyph-SDXL-v2: 2,080,399,558 bytes, manifest SHA-256
    `2300519493b080e684ce30a81d17cbde4b9639f2b4f8a5fcbd853df7d62ddb60`

The recorder's decimal-byte storage gate observed `51,758,321,664` bytes free,
above its explicit `50,000,000,000`-byte floor.

## Terminal boundary

The protected generic preflight in `services/jobs/preflight.py` probes disk with
`df -BG`. That output is binary GiB rounded to an integer, while `min_free_gb=50`
is treated as a unitless number. The observed `51,758,321,664` bytes are
`51.758` decimal GB but only `48.18` binary GiB; `df -BG` rounded/truncated the
available value to `49G`, so the generic gate failed `49G < 50G`.

This unit mismatch stopped the run before queue admission. No protected engine
file or threshold was changed during the authorized attempt.

No retry, queue admission, render, substitution, model download, package download,
provider spend, training, deletion, or threshold change occurred. Retry6 is now
consumed/replay-blocked; a future attempt requires fresh authorization and a fresh
remote root.
