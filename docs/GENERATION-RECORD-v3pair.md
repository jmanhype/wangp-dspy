# GENERATION RECORD — v3_pair ("perfect", ledger #4)

**The only operator-rated "perfect" artifact.** Compiled 2026-09-09 from
live-artifact verification + session record (Codex's request).

## Artifacts (verified on 3090, all survive)

| file | bytes | md5 |
|---|---|---|
| speaker_test/v3_pair.mp4 | 757,629 | c523919b6ac93a29edd43de75e424033 |
| speaker_test/v3_c1.mp4 | 1,195,705 | be96a3027d1fa8f4b14454118ab4d97a |
| speaker_test/v3_c2.mp4 | 1,229,480 | 6b485e84f875ccc30a87476b34bf38d3 |
| speaker_test/v3_c2seed.png | 612,688 | (cut 1 last frame — the chain seed) |
| speaker_test/grandma_frame2.png | 632,920 | cut 1 anchor (dungeon plate frame-grab @3s) |
| speaker_test/soul_frame.png | 671,448 | soul face-ref (from dg_2_soul @2s) |
| speaker_test/grandma_frame.png | 719,721 | grandma face-ref (from dg_1_grandma @3s) |
| marathon/v2/dialogue/dgshort_g.wav | — | grandma line (VibeVoice, trimmed+boosted) |
| marathon/v2/dialogue/dgshort_s.wav | — | soul line (VibeVoice, trimmed+boosted) |

## Recipe (from session record — the generator script lived in /tmp, gone)

```
Cut 1 (grandma speaks):
  model_type minimax_h3_ref2va_pruned, seed 904, profile 2
  704x576, 24fps, 56 frames (~2.33s)
  image_start grandma_frame2.png
  image_refs [grandma_frame2.png, soul_frame.png]   # 2 refs MAX
  audio_guide dgshort_g.wav
  prompt: (S1) grandmother speaks in exact sync / (S2) the man in
          Picture 2 keeps his mouth fully closed while she speaks

Cut 2 (soul speaks — chained, reverse attribution):
  seed 904, profile 2, 56 frames
  image_start v3_c2seed.png   # = cut 1's LAST frame (ffmpeg -sseof -0.05)
  image_refs [v3_c2seed.png, grandma_frame.png]  # HER face holds HER shut
  audio_guide dgshort_s.wav
  prompt: mirrored (S1)/(S2) swap

Audio prep: silenceremove → highpass f=100 → volume +9dB → atrim 0:2.4
Assembly: raw concat (no crossfade)
```

## QC evidence (v3d.log, survives)

```
wav gates:        cut1 0.86, cut2 0.80
post-render whisper: c1 0.71 ("who hushed now, dear? have a cookie.")
                     c2 0.60 ("matey, i am on fight!" — whisper-small
                              mishear; operator ears heard it correctly)
operator verdict: "perfect" — 2026-09-06T13:55Z, ledger entry #4
                  (docs/verdict-ledger.json, commit 1138c2a)
```

## Notes

- MP4 carries NO embedded prompt/seed/profile — that metadata lives here,
  in the session record, and the ledger. This file IS the durable record.
- The recipe above became `predict/continuation_lane.py` and the acceptance
  pipeline's job contract — this pair is the origin artifact of the
  validated config.
