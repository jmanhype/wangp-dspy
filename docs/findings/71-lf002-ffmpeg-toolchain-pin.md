# 71 — LF002 golden assembly depended on ambient PATH ffmpeg

Status: OPEN; source repair staged for review.

## Evidence

Qodo review of PR #101 found that local LF002 golden assembly invoked bare
`ffmpeg` from the caller’s `PATH`. The exact pair requires the
operator-accepted `Lavf62.3.100` ffmpeg build. Another workstation can have
no ffmpeg or a different build, causing either an assembly crash or a canary
failure without identifying the toolchain mismatch.

## Minimal fix

For LF002 golden-canary runs:

- require `WANGP_LF002_FFMPEG` to name an absolute executable;
- default the expected build identity to `Lavf62.3.100`;
- allow `WANGP_LF002_FFMPEG_EXPECTED` to pin another explicitly validated
  build;
- probe the selected executable before assembly;
- fail closed on missing executables and version mismatches;
- use the selected executable in the assembly argv;
- persist the selected executable and probed version in assembly evidence.

The exact artifact canary remains the final authority.

## Validation

The strict single-ledger run at `ae15b7a` produced the exact pinned pair with
the local `Lavf62.3.100` ffmpeg build. This PR adds the missing preflight and
explicit executable selection for future workstations.

## Follow-up

Finding #72 corrects the ffmpeg identity parser and moves LF002 toolchain
validation ahead of staging and rendering.
