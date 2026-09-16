# 53 — golden-v3 must reject external-source remux

Status: OPEN; source repair staged for review.

## Evidence

The recovered `/tmp/v3_pair.py` generator and the byte-identical repo replay prove
the winning recipe preserves WanGP/H3's native multiplexed audio/video output.
The prepared guide conditions generation; it is not overlaid afterward. The only
post-render media operations in the winning path are last-frame extraction and
concatenation of two complete native A/V cuts.

The working tree briefly reintroduced `audio_carrier=external_source_remux` as a
golden-v3 compatibility mode. `render-0068` demonstrated why that is unsafe: it
kept the failed seed-904 video, replaced its native audio with the clean guide,
and still failed the visual gate. A derivative with clean words is not evidence
that H3 generated a synchronized result.

## Minimal fix

- `golden_v3` and the Ref2VA continuation lane accept only native H3 output.
- `discard_rendered_audio=true` fails plan/runtime validation.
- The canonical final artifact must hash identically to `raw.mp4`.
- Ref2VA QC must read native generated audio, never a guide-overlaid derivative.
- Any non-Ref2VA external-audio lane must remain separate and cannot borrow the
  golden-v3 contract or verdict.

Acceptance tests reject an explicit external carrier, reject discard=true, prove
the remux runner is never invoked, and prove native/final hashes match.
