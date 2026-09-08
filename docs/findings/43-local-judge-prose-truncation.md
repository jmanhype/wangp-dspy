# Finding #43 — local judge can fill the output budget with prose

**Status:** Confirmed and fixed in the local judge request contract,
2026-09-08.

Cut 1 passed the new GPU-timeshare lifecycle, but cut 2 returned
`finish_reason: "length"` with a long explanatory `content` string and no
score object.  The 512-token reasoning fallback from #39 cannot recover a
JSON object that was never emitted.  This is a response-shape failure, not a
visual score, so the gate correctly rejected the cut.

## Fix

The local adapter now requests a 1024-token budget and llama-server's
OpenAI-compatible `response_format: {"type": "json_object"}` grammar, and
the shared prompt explicitly forbids analysis/prose outside the final JSON
object.  Strict three-score validation and fail-closed behavior remain
unchanged.
