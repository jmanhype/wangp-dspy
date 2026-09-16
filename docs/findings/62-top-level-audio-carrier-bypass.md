# 62 — top-level external audio carriers bypass native validation

Status: OPEN; source repair staged for review.

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
