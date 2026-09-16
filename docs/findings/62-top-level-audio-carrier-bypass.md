# 62 — top-level external audio carriers bypass native validation

Status: CLOSED in PR #93 / commit `0e79a71`; all three native-carrier
boundaries reject external carriers on `main`.

## Evidence

Qodo review of PR #83 found that `_build_ref2va_runtime_input` checked the
carrier only inside the nested `audio_policy`. Jobs carry `audio_carrier` as a
top-level field, so a request such as:

```json
{
  "audio_policy": {"discard_rendered_audio": false},
  "audio_carrier": "external_source_remux"
}
```

passed the adapter. The profile also accepted an arbitrary `audio_carrier`
keyword through `**kw` and then emitted `native_h3`, silently normalizing the
request instead of rejecting it. A directly supplied prebuilt settings document
likewise lacked a top-level carrier check.

## Minimal fix

Reject any top-level carrier other than `native_h3` at all three boundaries:

1. adapter/job envelope;
2. `Ref2VAProfile.build_settings`;
3. prebuilt runtime settings validation.

Regression tests cover the job envelope, direct profile construction, and a
mutated prebuilt settings document.

## Resolution

The adapter envelope, `Ref2VAProfile.build_settings`, and prebuilt settings
validation all require `native_h3`. Regression coverage spans
`tests/test_continuation_chain_extras.py`, `tests/test_ref2va_runtime.py`,
and `tests/test_render_profiles.py`. The full suite at `9b70be1` passed 1380
tests with one intentional skip and no failures.
