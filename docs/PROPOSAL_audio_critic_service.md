# PROPOSAL: shared Qwen2-Audio critic service (profile-driven rubrics)

Status: DESIGN (no code). Two consumers, one service, one schema.

- **music lane** (proven): SGFLIX audio factory Auto-Producer loop on the
  3090 — 3-critic stack (rule_critic objective gates + qwen2_audio_critic
  prose critique feeding proxy_critic + keeper/reject). Known weakness:
  Qwen2-Audio emits chatty prose; the loop's parsing lives downstream in
  proxy_critic.
- **delivery lane** (new): comic_critics eval lane in paivot-hermes —
  vision+transcript judging is deaf to comedic delivery/timing/pacing.

Hard constraints:
1. **Music-lane gate behavior must not change.** The existing keeper/
   reject decisions and their provenance (critique JSONs under
   sgflix_audio_factory/critiques + logs) are the artifact of record for
   shipped keepers; the service must reproduce, not reinterpret.
2. 24GB GPU shared with the 27B vLLM judge and the wgp render queue —
   contention is real and must be designed for, not hoped away.
3. Repo is PR-only with tests; nothing lands without the team loop.

## Architecture

**One HTTP service on the 3090, transformers-loaded Qwen2-Audio-7B-Instruct
(bfloat16), PROFILE-driven rubrics, schema-locked output.**

```
┌ paivot-hermes repo (client side) ─────────────┐   ┌ 3090 (service side) ─┐
│ tools/comic_critics/                            │   │ audio_critic_svc/    │
│  judges.py: AudioDeliveryJudge ────────────────┼──►│  POST /critique      │
│   (new judge backend, feeds DummyLM-testable   │   │  profile=music|      │
│    double-eval machinery like the others)       │   │         delivery     │
└─────────────────────────────────────────────────┘   │  FastAPI, 1 worker,  │
                                                      │  model warm, single- │
┌ SGFLIX audio factory (3090, local) ────────────┐   │  GPU stream, lock-   │
│ auto_producer_loop.py ──► qwen2_audio_critic   ├──►│  serialized          │
│  (slice 3 swaps the subprocess call for HTTP;  │   └──────────────────────┘
│   proxy_critic untouched)                      │
└─────────────────────────────────────────────────┘
```

Service boundary decision: **HTTP (FastAPI) on localhost + LAN**, not a
CLI-per-call. Rationale: model load is ~1-2 min and currently happens
EVERY critique invocation (the subprocess script reloads weights each
time — that's minutes of GPU-pegged dead time per song); a warm service
amortizes it and gives both consumers one schema-enforcement point.
Clients: the factory loop calls localhost; the comic lane calls over the
existing LAN/tunnel pattern.

**Module layout (repo, PR-only):**

- `tools/audio_critic/schema.py` — the shared schema + validation (pure,
  unit-testable, no GPU). Single source of truth imported by BOTH the
  service and the client judges.
- `tools/audio_critic/profiles.py` — rubric registry: `music` and
  `delivery` profiles as data (system prompt, scale bounds, flag
  vocabulary), not code paths.
- `tools/audio_critic/service.py` — the 3090-side FastAPI app (thin:
  audio in → profile lookup → model generate → schema-validate →
  respond). Deliberately NOT imported by tests; its logic lives in
  schema/profiles/criticize so tests never need the model.
- `tools/audio_critic/criticize.py` — model-agnostic core:
  conversation assembly (mono reference+candidate pattern, matching the
  proven script), generation params, **strict output parsing with typed
  retry-on-malformed** (one retry with an "obey the schema" nudge, then
  typed failure — never silent prose passthrough).
- `tools/comic_critics/judges.py` — grows `AudioDeliveryJudge`
  (implements the existing `vote_pair` interface; audio extracted from
  the candidate video via ffmpeg → temp wav → service; verdict text fed
  into the same [VOTING]/[WINNER] parse machinery as the other judges).

## Output schema (both profiles, identical)

```json
{
  "schema": "audio-critic/1",
  "profile": "music",
  "score": 31,                      // int, profile-defined bounds
  "score_scale": [0, 40],           // from profile, echoed back
  "flags": ["timing_drift", "muddy_vocals"],
                                     // CLOSED vocabulary per profile
  "reason": "compact 1-3 sentence justification",
  "decision": "keeper_candidate",   // profile-defined enum
  "model": "Qwen/Qwen2-Audio-7B-Instruct",
  "parse_ok": true                  // false => typed retry happened
}
```

- `flags` is a **closed vocab** per profile (schema validates; unknown
  flag → validation failure → retry path). This is the structural fix
  for the prose weakness: the model must slot its critique into named
  bins, and downstream code branches on flags, never on prose matching.
- `decision` enums: music = `keeper_candidate | reject` (mirroring the
  factory's existing decision vocabulary exactly); delivery =
  `pass | revise | reject` (mirroring RenderQC's verdict enum so the
  comic lane's QC machinery composes without translation).

## Music lane adoption WITHOUT behavior change — the compatibility design

The invariant to preserve: **same prompt text, same generation params,
same model revision, and the loop's downstream decisions unchanged.**

Slice approach (critical): the service's `music` profile prompt is
byte-identical to today's `--prompt` default, temperature/`max_new_
tokens=512`/decoding identical, and the structured fields are
**extracted additively**:

1. The service returns BOTH: `prose` (the raw generation, exactly what
   the script printed today) AND the structured fields (score/flags/
   reason/decision parsed from that same generation by a deterministic
   extractor — for music, initially a regex/keyword extractor tuned on
   the existing critique corpus in `sgflix_audio_factory/critiques/`,
   which is real training data for the parser).
2. proxy_critic keeps consuming what it consumes today (the prose via
   `--qwen-critique` JSON) — **untouched in slices 1-3.**
3. The keeper/reject gate keeps being rule_critic's decision (as today
   — the qwen critique is advisory in the loop). Nothing moves.
4. Only when the structured extractor has been validated against the
   historical corpus (flags match what a human would say the prose
   said, scores within tolerance) does anything downstream switch to
   the structured fields — and that's a separate, explicitly gated
   slice with its own before/after comparison on archived batches.

This is "adopt the service, keep the behavior" — the schema fix lands
for the service without re-litigating proven keeper decisions.

## Contention strategy (24GB, three consumers)

Qwen2-Audio-7B bf16 ≈ 15-16GB. The 27B vLLM judge cannot co-reside.
wgp render takes the whole GPU while running. Therefore:

- **Sequential, not concurrent.** The service is a *singleton* with an
  in-process lock: one critique at a time; concurrent requests queue
  (bounded queue, typed 503 when full — comic lane backs off, it's not
  latency-critical).
- **On-demand lifecycle, not always-on**: the service stays down by
  default. A tiny supervisor script (`up`/`down`) that (a) checks
  nvidia-smi free memory ≥ threshold, (b) refuses to start while wgp
  render or vLLM holds the GPU, (c) idles out (unloads) after N minutes
  without requests. The factory loop and comic lane both call
  `up` before their batch and `down` (or let idle-timeout) after.
  Precedent: the audio factory already runs sequential per-song
  crits — this just makes the sequencing explicit and cross-consumer.
- Requests carry audio as small wav/flac (16kHz mono where the profile
  allows) — Qwen2-Audio's feature extractor resamples anyway
  (librosa already does this in the proven script); caps: 90s audio
  per request, typed rejection beyond.
- Timeout posture mirrors the loop's proven values: 300s per critique
  (the loop already uses this), typed failure, no retry storm — one
  in-service retry on schema-malformed only.

## Slice breakdown (team loop)

**Slice 1 — schema + profiles + parser core (repo, pure tests).**
schema.py, profiles.py, deterministic extractor; RED tests: schema
validation (all fields, closed flag vocabs, scale bounds per profile),
extractor on recorded fixture critiques (drawn from the historical
corpus), music-profile prompt byte-equality vs the factory script's
default. No GPU, no service.

**Slice 2 — service + criticize core.** FastAPI app + generation
assembly (conversation shape, decoding params pinned to the proven
script), schema-locked response, single-flight lock, bounded queue,
503 semantics. Tests with a fake model callable (recorded generations:
one clean, one malformed→retry→clean, one persistent-malformed→typed
error). Service deploy = operator step, not CI.

**Slice 3 — music lane adopts the service, behavior-frozen.** Factory
loop's subprocess call → HTTP call to localhost (fallback: on
connection failure, fall back to the OLD subprocess path so the factory
never hard-depends on the new service — the loop is a production
artifact). Acceptance: a re-run of one archived batch produces critique
JSON whose prose field is within normal generation variance and whose
extracted fields match the historical extractor on the same prose;
keeper decisions identical. **Explicitly gated by operator** since it
touches the shipped factory.

**Slice 4 — delivery profile + comic-lane judge.** `delivery` rubric
(flags: e.g. flat_delivery, rushed_pacing, timing_off, weak_commit,
mumbled; decision enum pass/revise/reject), `AudioDeliveryJudge`
implementing vote_pair (audio extraction from video via ffmpeg,
deterministic fallback + parse_error like the other judges), wired
into comic_critics' double-eval machinery. RED tests: judge parsing,
fallback determinism, flag-vocab validation, judge failure isolation
(audio critic error must degrade to the deterministic candidate-1
fallback, never crash the eval run).

**Slice 5 (optional, later) — structured-field switchover in the music
lane** (proxy_critic consuming flags/decision instead of prose
matching), only after slice-3 corpus validation says the extractor is
trustworthy.

## Risks / honest caveats

- Same-model determinism is impossible (sampling); the behavior-freeze
  argument for the music lane rests on prompt+params+decision-path
  equality, with generation variance acknowledged — that's why slice 3's
  acceptance compares extracted-fields-vs-extractor, not raw text
  equality.
- The extractor's initial accuracy is a guess until run against the
  corpus; slice 1 measures it and may force flag-vocab iteration.
- LAN exposure of the service must bind to the tailscale/LAN interface
  with no auth-free public bind; keep it localhost+tailscale only.
