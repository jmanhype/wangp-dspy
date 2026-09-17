# LF002 VibeVoice two-cut transcription and timing report

## Artifact

- Status: final candidate, awaiting operator audiovisual review
- Output: `datasets/runs/pull/lf002-two-cut-vibevoice-20260917/assembled.mp4`
- SHA-256: `c3aa318cda87b56ae53a0994a09ea1ae21808cc7383ab9e63e09d24f616bead2`
- Duration: 4.666667 seconds
- Frames: 112 at 24 fps
- Resolution: 704×576
- Audio: AAC, stereo, 32 kHz
- Repository commit: `322af7cc05accf63b60f59865c8875ccf49533c2`
- Repository tree at execution: clean

## Dialogue timing

Local Whisper-small, word timestamps enabled:

```text
00:00.000–00:01.920  This is the last rain we have.
00:02.280–00:04.340  And don't spill a single drop.
```

Cut 2 begins at 2.333333 seconds. Its first transcribed word begins at
2.280 seconds in the assembled timeline, i.e. the first word spans the cut
boundary by about 53 ms; speech remains continuous through the chained turn.

## Gate evidence

### Accepted cut 1 — Nell, seed 906

- Raw/remux SHA-256:
  `b53e5d37457f61db8c1bfa31d11d8d873139bf0aabddf97e0efa245de4d702a3`
- Pre-Whisper: PASS, `0.857`
- Post-Whisper: PASS, `1.000`
- Vision: PASS (`mouth_activity 0.85`, `action_match 0.80`,
  `speaker_attribution 0.90`)

### Accepted cut 2 — Orin, seed 907

- Raw/remux SHA-256:
  `395b78195a0aa7da284a8cff9e43cb19e757e18977b83c2028cdc212063c39e8`
- Pre-Whisper: PASS, `1.000`
- Post-Whisper: PASS, `0.833`
- Transcript: `And don't spill a single drop.` — first word `Then` is heard as
  `And`; remaining words and meaning are intact.
- Vision: PASS (`mouth_activity 0.85`, `action_match 0.90`,
  `speaker_attribution 0.95`)

## Rejected attempts retained

| Cut | Seed | Post transcript | Score | Disposition |
|---:|---:|---|---:|---|
| 1 | 905 | This is the last great land we have to. | 0.571 | rejected, evidence retained |
| 2 | 905 | Don't spill a demated dare | 0.500 | rejected, evidence retained |
| 2 | 906 | Single speed is no drop. | 0.167 | rejected, evidence retained |

## Honest limitation

The blocking vision gate inspects still frames and does not measure phonetic
A/V synchrony (`av_sync_verified=false` by contract). The Whisper gates verify
the spoken words, but final perceived lip synchronization and creative quality
require operator review of `assembled.mp4`.
