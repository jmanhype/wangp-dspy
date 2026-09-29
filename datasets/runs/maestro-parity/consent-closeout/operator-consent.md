# WD-32hk scoped cloning-reference consent

## Anchor identity boundary

Byte identity was verified read-only against the accepted repository artifacts
before the approval below is applied to any matrix disposition.

- Primary WD-cpow anchor `inputs/target-voice.wav`:
  SHA-256 `b013bad88be5b44609304764aaa6b10afb9f0299d768c8abc48c2d1afd4bed18`.
- Primary WD-bxhc destination `inputs/voice-primary-vibe.wav`:
  SHA-256 `b013bad88be5b44609304764aaa6b10afb9f0299d768c8abc48c2d1afd4bed18`.
- Primary `cmp --silent` result: identical (`exit 0`).
- Secondary WD-cpow anchor `outputs/wd_cpow_vibevoice_raw.prepared.wav`:
  SHA-256 `e371ebe7ee1ce9964657b4f34f61d32fbff2a5345bdb90add6c3e7dba1ee2175`.
- Secondary WD-bxhc destination `inputs/voice-secondary.wav`:
  SHA-256 `e371ebe7ee1ce9964657b4f34f61d32fbff2a5345bdb90add6c3e7dba1ee2175`.
- Secondary `cmp --silent` result: identical (`exit 0`).
- Recheck timestamp: `2026-09-28T13:40:57Z`.

The historical WD-bxhc `reference-consent-rework.md` remains the authoritative
pre-consent boundary. It correctly recorded both true sources and the fact that
cross-story cloning-reuse consent was then absent. WD-cpow
`operator-authorization.md` remains the ownership and evaluation-rights source;
ownership alone was not treated as cloning consent.

## Operator approval

Verbatim operator input:

> Approve

- Approved by: operator via `/root` parent authorization.
- Recorded at: `2026-09-28T13:20:11Z`.
- Question answered: the three-way authorization question for cross-story
  cloning-reference reuse.

## Consent scope and limits

- The operator approves reuse of the two WD-cpow anchors named above as
  WD-bxhc VibeVoice cloning references.
- Destination scope: the WD-bxhc evidence chain only.
- Use is limited to operator-owned research/evaluation.
- No redistribution, publication, training, provider spend, new inference,
  download, host mutation, or use outside this consent is authorized.
