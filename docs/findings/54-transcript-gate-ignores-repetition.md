
# 54 — transcript gate ignores insertions and repeated phrases

Status: OPEN; source repair staged for review.

## Evidence

LF002's prepared guide transcribed as:

```text
This is the last grain we have.
```

The native seed-904 H3 output transcribed as:

```text
This is the last, this is the last grain we have.
```

The old `transcript_match_score` converted both strings to unordered word sets.
Duplicate insertions therefore did not lower the score, so a repeated phrase
could pass a word-overlap bar.

## Minimal fix

Use sequence-sensitive token-level WER and expose transcript similarity as
`1 - WER`. Insertions, deletions, substitutions, and repeated phrases reduce
the score while retaining tolerance for known Whisper mishearings.

Regression cases:

- repeated LF002 line fails;
- “matey, I am on fight” versus “Lady, I am on fire!” remains above the bar;
- the grandma Whisper mishearing remains above the bar;
- unrelated gibberish fails.
