# 85 — LF004 cut failures: declared clip duration vs guide audio length

Status: root cause identified. No gate relaxed, no retry policy extended,
no additional render started, no live artifact modified.
Story: WD-42no (LF004 operator dogfood, approved plan
sha256:70280fdcd6fb7f54bc4f7027e03de54e4897178dd41adcf92ef31bd347d7bd86)
Date: 2026-09-20

## Symptom

Cut 1 needed two governed retries before passing. Cut 2 exhausted the accepted
three-attempt QC policy and dead-lettered; cuts 3/4 remained pending behind it.

Measured cut-2 failure modes (`cut2-deadletter-review/evidence.json`):

| Seed | Raw SHA-256 (first 16) | Result | Transcript / verdict |
| --- | --- | --- | --- |
| 904 | `7351334145399bd4` | post-Whisper 0.167 | intended line preceded by an extra utterance |
| 905 | `93075b7b7633289b` | post-Whisper 0.167 | intended line appears twice |
| 906 | `cb1293c6e987f6a5` | Whisper pre/post pass (post 1.0) | vision rejects ghosting/double exposure (`action_match` 0.1, `speaker_attribution` 0.1) |

## Root cause

The approved brief pairs 2.333 s audio guides with 4.458 s clips.

| Item | Value | Source |
| --- | --- | --- |
| brief `durations_s` | `4.458333` ×4 | `datasets/content_briefs/lf004-operator-dogfood/brief.json` |
| plan `frames` / `shot_duration_s` | 107 / 4.458 per clip | `plan.json` (clips 1–4) |
| actual guide audio, all four | 2.333333 s = 56 frames @24fps | `ffprobe` on `tess.prepared.wav`, `rho.prepared.wav`, `tess-cut3.prepared.wav`, `rho-cut4.prepared.wav` |
| Content Brief Gateway default | `56.0/24.0` = 2.333 s | `predict/content_brief.py` (`DEFAULT_DURATION_S`) |
| LF003 accepted per-cut policy | 56 frames/cut; assembly 224 frames / 9.333 s | WD-rij6 accepted summary |

Consequences:

1. Every 107-frame clip carries ~2.125 s of speech time with no guide content.
   The renderer fills it, observed directly as the intended line spoken twice
   (seeds 904/905) or as double-exposure motion (seed 906).
2. `plan.json` sets `guide_duration_s := shot_duration_s` (4.458) instead of the
   guide's measured 2.333 s. `services/director/renderers/policy.py::
   check_guide_duration()` requires guide == shot exactly, so it compares two
   plan-declared values and passes trivially; it never inspects the audio file.
3. `audio_provenance.keeper_window_s` and the runtime
   `audio_policy.remux_window` are both `[0.0, 4.458333]` although the master
   file is 2.333 s long.

The accepted LF003 four-cut run used these same guides with 56-frame cuts —
exactly the guide length — and passed pre/post Whisper, identity vision,
three-frame mouth localization, and blocking SyncNet.

## Why nothing caught it

`predict/content_brief.py` validates `durations_s` only as positive numbers, and
`check_guide_duration()` compares two plan-declared values. Nothing in the
no-GPU planning path measures the guide audio and compares it with the declared
duration, so an internally consistent but physically impossible plan is accepted
and only fails after GPU work.

## Corrective actions

1. Fail-closed preflight (no GPU): reject any brief or plan whose declared
   per-turn duration does not match the measured guide audio length, unless an
   explicit, recorded filler policy is declared. This would have refused the
   LF004 plan before a single render.
2. Recovery: a corrected plan using the gateway default `56/24` s per turn
   reproduces the LF003-accepted per-cut policy against these same guides.
   Because the plan hash changes, it requires explicit operator approval of the
   new plan hash; the current approval covers only `70280fdc…`.

## Explicitly not done

- No QC/AV/retry gate was relaxed or reordered.
- No fourth render was started (the approved policy allows three attempts).
- No live or accepted artifact was overwritten.
