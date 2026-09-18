# 83 — A single still-frame mouth box destabilized SyncNet localization

Status: implemented on this branch.

## Failure boundary

The first fully gated LF003 rerun rendered Tess three times. Every attempt failed
SyncNet with an offset at the search boundary and low confidence:

```text
seed 906: confidence 0.889, offset +10
seed 907: confidence 0.584, offset  +9
seed 908: confidence 0.903, offset +10
```

Offline re-judging disproved “systematically desynchronized video.” With a tight
mouth box centered on the visible lips, all three artifacts pass strongly:

```text
seed 906: confidence 2.491, offset -1
seed 907: confidence 2.846, offset -1
seed 908: confidence 3.739, offset -1
```

The live one-box prompt returned y-centers around `0.22–0.24`, drifting toward
the chin/jaw, while the visible-lip center was around `0.19`. The renders were
stable; the localizer was not.

## Change

The local Qwen judge now makes two bounded requests:

1. **Identity/composition still QC** — scores action and speaker attribution,
   but does not treat a closed/static mouth as disqualification. Temporal
   speech motion belongs to SyncNet.
2. **Dedicated mouth localization** — returns one tight normalized mouth bbox
   for each generated start/middle/end frame.

`run_vision_judge()` requires all three boxes, validates their bounds, rejects
center spread above `0.03` normalized units, and derives a per-coordinate median
box for SyncNet. It preserves all three source boxes in evidence.

The still-frame `mouth_activity` score remains descriptive evidence but is no
longer a pass/fail authority. Visual passage is determined by `action_match` and
`speaker_attribution`; temporal speech motion is determined by the blocking
SyncNet gate.

## Live verification

On the same seed-906 artifact, the dedicated consensus localizer returned:

```text
[0.33, 0.19, 0.02, 0.01] × 3
```

Identity QC passed (`action_match=0.9`, `speaker_attribution=1.0`), and SyncNet
using that median box passed:

```text
confidence 3.336197
offset     -1 frame (-0.04 s)
```

No SyncNet threshold was weakened.
