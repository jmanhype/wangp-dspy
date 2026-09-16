
# 54 — transcript gate ignores insertions and repeated phrases

Status: CLOSED in PR #84 / commit `7aafac1`; sequence scoring is on `main`.

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

## Resolution

`predict.continuation_lane.transcript_wer` now computes token-level edit
distance, and `transcript_match_score` exposes `1 - WER`. Insertions,
deletions, substitutions, and repeated phrases reduce the score while normal
punctuation/case differences remain free.

The required regression cases are present in
`tests/test_continuation_lane.py`:

- the repeated LF002 line has WER above 0.5 and similarity below 0.5;
- “matey, I am on fight!” remains at or above 0.6 against the intended line;
- the grandma Whisper mishearing remains at or above 0.6;
- unrelated gibberish fails the transcript judge.

Finding #63 subsequently added per-turn error attribution so a strong turn
cannot mask an omitted or repeated neighboring turn.

Validation at `main` commit `23d46f842ac58fc3bc34f6e79ff2731038bebfc1`:
`tests/test_continuation_lane.py tests/test_whisper_gate.py` passed 19/19,
and the full suite passed 1380 tests with one intentional skip and no
failures.
