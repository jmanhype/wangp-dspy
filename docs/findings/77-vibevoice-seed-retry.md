# 77 — VibeVoice scored rejections need bounded seed retries

Status: implemented in local changeset; full model-free suite passing.

## Failure boundary

The #76 live rerun at main `0cca49b` preserved the exact failure: Nell passed
at `0.857`, while Orin scored `0.000` and transcribed as
`When you ring, what shall come?`. The raw and prepared Orin SHA-256 values
matched the earlier seed-42 attempt byte-for-byte:

```text
raw:      a57e0223ed31990113332e8dc8a72940e5c150f13455f3e98a848eec90ae01e2
prepared: 3eb1bdde6b00d7919e87ed264717c75999f044f3dd1afb134b674744c32661f3
```

Repeating that seed cannot recover the turn. A separate repo-native Orin
manifest changing only the seed from `42` to `43` passed the same Whisper gate
at `1.000` with the exact intended transcript. The supplier nevertheless
treated the first scored rejection as terminal, even though the queue already
uses bounded seed retries for probabilistic visual-gate misses.

## Change

Fresh local and remote VibeVoice supplies now use a bounded seed-retry policy:

* default two retries, with seeds `manifest.seed`, `+1`, and `+2`;
* retries only after a scored Whisper rejection carrying transcript evidence;
* no retry for generation, preparation, transport, or unscored transcription
  failures;
* every rejected pre-retry attempt is moved intact to
  `<output>.attempt-N[.prepared].wav` plus provenance;
* report records and final provenance retain `generation_seed`, attempt index,
  and append-only `seed_rejections`;
* the failed final attempt remains at the canonical paths so #76 rejection
  bundling continues to work;
* remote supply validates and fetches every prior attempt bundle, localizing
  its raw/prepared/provenance paths into both successful runs and #76 rejected
  bundles — host-only evidence paths are not accepted as a local record;
* a generation failure after a preserved scored rejection remains a terminal
  failure but retrieves that prior attempt evidence into the rejected bundle;
* canonical outputs, prepared outputs, provenance, and every enabled retry path
  are checked for cross-turn collisions before generation;
* resumed reports retain the effective seed, attempt count, and rejection history;
* the gate bar and transcript scoring are unchanged.

`--seed-retries 0` preserves the old one-attempt policy. The accepted budget
is 0 through 10; invalid values fail before model construction or generation.

## Verification scope

Model-free tests cover retry on the first scored miss, preserved failed audio
and provenance, terminal behavior after the budget is exhausted, no retry for
unscored transcription failures, and pre-generation budget validation. Remote
dispatch passes the explicit retry budget through the repo module invocation.
They also cover retry success and rejection fetch/localization, including
attempt hash and provenance validation.

Local validation at the changeset:

```text
.venv/bin/python -m py_compile predict/vibevoice.py tests/test_vibevoice.py
.venv/bin/pytest -q tests/test_vibevoice.py tests/test_render_host.py tests/test_whisper_gate.py
.venv/bin/pytest -q
git diff --check
```

All exited `0`; the full suite reported 1,447 selected tests, zero failures,
zero collection errors, and its normal one skipped test. The JUnit record is
SHA-256 `cc021d8344a6317eed7007356d1e3a917041229d9836fd96da640eeffe28c733`.

No claim is made that a particular seed universally passes. The live seed-43
artifact is evidence for this turn and reference, not a replacement contract.
