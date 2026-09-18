# 81 — Ref2VA completion had no temporal audiovisual synchrony gate

Status: implemented on this branch.

## Failure boundary

Every accepted Ref2VA cut retained:

```json
"mouth_sync": null,
"av_sync_verified": false
```

The still-frame vision judge can verify identity, composition, mouth activity,
and speaker attribution, but cannot observe full-video motion or hear audio.
The LF003 strict film completed even though Rho’s native post-Whisper transcript
was noisy, and the repo had no temporal method for rejecting an audio/lip
embedding mismatch.

## Change

Ref2VA QC now requires two complementary visual stages:

1. the existing identity-aware still-frame judge; and
2. a blocking SyncNet v2 temporal gate.

The still-frame prompt now returns a normalized `speaker_mouth_bbox`. SyncNet
runs through `RenderHost.run_argv` in the WanGP Python environment, creates
three deterministic crops around that bbox, compares audio and lip embeddings,
and records:

* per-crop offset, confidence, and minimum embedding distance;
* median 25-fps offset and confidence;
* content-addressed model identity;
* pass bars;
* explicit `phonetic_sync_verified=false`.

Pass bars are initially calibrated to:

```text
abs(median offset) <= 10 frames at 25 fps (0.4 s)
median confidence  >= 1.0
```

Failed SyncNet gates preserve evidence in `qc-evidence.json`, append
`av_sync_rejections`, and use the existing audited bounded seed retry. No score
is fabricated and no phoneme/viseme claim is made.

The SyncNet model is not committed. `scripts/fetch_syncnet_model.py` downloads
the official Oxford VGG weight file and enforces:

```text
SHA-256 961e8696f888fce4f3f3a6c3d5b3267cf5b343100b238e79b2659bff2c605442
```

It can also stage that exact file to the render host. The model-equipped host
must provide the repository checkout and Python environment selected by
`WANGP_SYNCNET_REPO` and `WANGP_SYNCNET_PYTHON`.

## Live calibration

The vendored runner was exercised on the 3090 against preserved operator-
accepted artifacts and the strict LF003 pair:

| Cut | Median offset | Confidence | Result |
|---|---:|---:|---|
| v3 original cut 1 (operator perfect) | `-3` | `1.320` | PASS |
| v3 original cut 2 (operator perfect) | `-2` | `2.889` | PASS |
| LF002 Nell (operator PERFECT) | `-1` | `4.387` | PASS |
| LF002 Orin (operator PERFECT) | `0` | `3.068` | PASS |
| LF003 Tess | `-1` | `2.491` | PASS |
| LF003 Rho | `8` | `0.481` | FAIL |

The LF003 Rho rejection is consistent with its noisy post-render transcript and
the operator’s unresolved audiovisual review. This calibration is evidence for
these artifacts, not a universal quality guarantee.

## Verification

Model-free tests cover bbox validation, evidence validation, failed-evidence
preservation, median aggregation, remote argv dispatch, bounded process
diagnostics, model fetch hash enforcement, integrated QC persistence, and
executor wiring. Host-side model-free tests do not claim a live GPU run; the
live calibration above is the measured backend evidence.
