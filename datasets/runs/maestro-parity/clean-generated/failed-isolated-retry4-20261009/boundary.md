# WD-bw0h clean-machine retry4 — 2026-10-09

## Outcome

The one-shot v3 retry4 authorization was consumed and stopped fail-closed. It did **not** produce a generated artifact.

## What worked

- Clean install, disposable checkout, repository identity, local tools, remote-root freshness, storage, four-model identity, offline wrapper, and host preflight passed.
- The retry3 settings-staging defect was cleared: `settings.json` existed at the mapped remote acceptance path and WanGP successfully loaded it.
- Exactly one local queue job was admitted and attempted.
- H3 loaded the authorized models and completed all 20 denoising steps.

## New terminal boundary

After denoising, WanGP's downstream `torchvision.io.write_video` call failed in PyAV:

```text
File "av/video/frame.py", line 313, in av.video.frame.VideoFrame.pict_type.__set__
TypeError: an integer is required
```

The native queue consequently reported:

```text
Queue completed: 0/1 tasks in 6m 40s (1 skipped)
```

The queue failed with `WanGPError: WanGP queue completed with an unexpected task count 0/1; expected 1/1`. No MP4 was emitted.

## Authorization disposition

The v3 authorization canonical SHA-256 is:

```text
4957b87064d0e7a93b566f426ee352084af8c5ebb7d1af876ce11e22fa68f969
```

It is recorded consumed in `authorization-consumption.json`. Replay fails closed. A future attempt requires a new operator authorization after a separately reviewed media-write compatibility repair; this retry4 authorization cannot be reused.
