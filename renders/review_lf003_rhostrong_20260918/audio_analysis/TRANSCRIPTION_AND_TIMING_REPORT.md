# LF003 strong-guide transcription and timing report

## Machine QC

- Tess Whisper pre: `0.833`
- Tess Whisper post: `0.833`
- Tess SyncNet: confidence `3.336197`, offset `-1` frame
- Rho Whisper pre: `0.833`
- Rho Whisper post: `0.667`
- Rho SyncNet: confidence `1.967893`, offset `-1` frame
- Both cuts: identity/composition vision PASS
- Both cuts: three mouth boxes agree exactly

## Independent local Whisper

```text
Cut 1 [00:00.000 --> 00:02.340]
  Tomorrow's sunrise is only a project.

Cut 2 [00:00.000 --> 00:01.880]
  can give me a real horizon here.

Assembled [00:00.000 --> 00:02.000]
  Tomorrow's sunrise is only a project

Assembled [00:02.000 --> 00:04.000]
  that can give me a real horizon.
```

## Decision

Mechanically eligible final candidate. Phonetic correctness remains operator-reviewed; SyncNet does not claim phoneme correctness.
