# 70 — LF002 golden-pair assembly used the wrong ffmpeg environment

Status: CLOSED in PR #101 / commit `ae15b7a`; LF002 golden assembly is local
on `main`.

## Evidence

The first single-ledger, no-prefix fresh-main run rendered both cuts exactly:

```text
cut1  64916cd42d40e0f81a51dd750d2134d194dd59c8318bf3d6f75fbc8649d97770
cut2  c3131c041a2b586e15ab19280a0ede64aa294b2e6bdc9f26fde0e35fbc29ceb
chain 1c1d86b0108c31a8318d428fcf626d3af6ffd0c0ba6269a8a69859eca6fb53de
```

The mandatory canary then rejected only the assembled pair. Its container
identified `Lavf60.16.100` (remote Linux ffmpeg 6.1.1), while the pinned
operator-accepted pair identifies `Lavf62.3.100` and was produced by the local
acceptance ffmpeg environment. Remote assembly therefore changed the output
bytes despite byte-identical native inputs.

## Minimal fix

For an LF002 golden-canary run:

1. derive each job’s sibling `raw.mp4`;
2. assemble those native inputs locally;
3. run the exact-hash canary after local assembly.

Do not route this specific golden-pair assembly through the renderer host.
The canary remains the authority on whether the resulting bytes match the
pinned control.

## Follow-up

Finding #71 pins and validates the explicit local ffmpeg executable/build so
this contract no longer depends on ambient `PATH` lookup.

## Resolution

The LF002 runner assembles sibling native `raw.mp4` artifacts locally before
the exact-hash canary; regression coverage is in
`tests/test_run_acceptance.py`. The committed strict single-ledger run
reproduced both native cuts and the accepted pair. Findings #71 and #72 later
pinned and prefetched the ffmpeg toolchain. The full suite at `9b70be1`
passed 1380 tests with one intentional skip and no failures.
