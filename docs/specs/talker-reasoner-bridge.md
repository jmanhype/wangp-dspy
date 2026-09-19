# SPEC — Thin Talker-Reasoner Bridge

Status: DRAFT — review contract, not an implementation · Story: WD-dd81 ·
Date: 2026-09-19 · Verified source baseline: commit `9007abf`

## Goal

Define a fail-closed boundary between a low-latency conversational talker and
a small, auditable reasoner, while preserving the existing Ref2VA film
pipeline as the only path for release-quality artifacts.

**Success invariant.** A fresh implementer can build the first three-route,
no-durable-memory slice from this document alone, prove that the talker never
receives or executes tools, and prove that every release-quality film action
entered through `scripts/run_acceptance.py::run_bundle()` rather than a new
shortcut.

## Scope and non-goals

This story creates a decision contract and follow-up map only. It adds no
Python, credentials, live model calls, tracker mutations, or seam changes.
Letta/Mem0/Cognee/Zep stay deferred until the thin loop is measured. Local
typed fixtures come first; live inference requires explicit consent, a named
endpoint, and a recorded privacy decision. PersonaPlex/Moshi receives final
safe dialogue text only—never a tool schema, callable, credential, or authority.
This design must not alter, weaken, or bypass Ref2VA QC. `Pipeline.forward()`
is non-release only; release-quality film execution calls `run_bundle()` so
provenance, staging, Whisper, identity vision, mouth-box consensus, and blocking
SyncNet remain governed by their current owner.

## Research facts retained as constraints

- PersonaPlex/Moshi is the low-latency duplex talker, not a native
  tool-calling model. The inspected NVIDIA repository shipped no
  `tools`, `tool_choice`, or `tool_calls` protocol.
- Voxtral Small 24B 2507 can emit structured `tool_calls` from audio, but it
  does not execute tools.
- Voxtral Realtime is transcription-oriented and is not the tool-calling
  component.
- The old VAOS gist used Voxtral for transcription/classification and Letta
  as the actual System-2 runtime. That does not make Moshi/PersonaPlex a
  native tool caller.
- Jev belongs at the calibrated routing and confidence gate. It is not the
  executor and does not replace the talker.
- The first build is intentionally three routes, one small validated action
  surface, measured latency/routing quality, and no durable memory.

## Minimal route state

The router emits exactly one label:

| Route | Meaning | Required behavior |
|---|---|---|
| `chitchat` | No film action is requested | Talker answers without waking the reasoner or creating an action |
| `film_request` | A film request has the minimum fields needed for a governed candidate | Validate a candidate action, then use only an approved existing execution seam |
| `clarify` | Intent is ambiguous or confidence is below threshold | Ask one bounded clarifying question; do not execute |

`unsafe` is absent because safety needs its own policy, red-team fixtures,
review boundary, and kill behavior; until then ambiguous/unsafe input fails
closed to `clarify` or rejection, never action. Rich taxonomies and arbitrary
caller schemas are deferred because the fixed three-label surface makes
calibration, replay, validation, false wakeups, and QC ownership observable
first and avoids expanding prompt-injection and authorization surface.

## Capability matrix

| Capability | PersonaPlex/Moshi | Voxtral Small 24B 2507 | Voxtral Realtime | Jev | Letta | Repo VibeVoice |
|---|---|---|---|---|---|---|
| Low-latency duplex talker | Yes | No | No | No | No | No |
| Transcription | No | Audio/text model, but not the selected transcription-only service | Yes, primary purpose | No | No | No |
| Structured call emission | No native protocol | Yes, may emit `tool_calls` | No | No | Runtime may request/invoke tools under its own integration | No |
| Tool execution | No | No | No | No | Yes, only if separately deployed and authorized | No |
| Calibrated routing/confidence gate | No | No | No | Yes | No | No |
| Durable memory | No | No | No | No | Yes with its configured stores | No |
| Repo-owned dialogue audio backend | No | No | No | No | No | Yes |
| First-slice role | Future talker only | Future candidate reasoner only | Future transcriber only | Router pattern/gate only | Deferred | Existing governed voice seam only |

No column above authorizes a model to touch the filesystem, network, SSH host,
credentials, or job queue. The bridge's action broker is the only component
that can submit a validated, allowlisted action to an existing execution seam.

## Thin architecture

```text
ephemeral typed fixture/transcript
  -> local deterministic/Jev-style calibrated router
     chitchat -> talker text policy -> PersonaPlex/Moshi (later)
     clarify  -> bounded question    -> talker (later)
     film_request -> small reasoner (Voxtral Small later)
  -> fixed-schema action validator (route/confidence/allowlist/authorization)
  -> reject with event | validated action
     non-release -> Pipeline.forward()
     release     -> run_bundle() -> existing repo render/audio/host seams
```

Routing decides whether to wake the reasoner. The reasoner proposes but never
executes an action. Validation precedes any response or execution, and the
broker can only select an existing governed seam, never construct a render
path. A validated `film_request` is a candidate, not render authorization;
release execution also requires a complete acceptance bundle, clean-tree policy
decision, operator approval, and `run_bundle()`. Dirty/fixture experiments stay
labeled non-release and are not promoted merely because media exists.

## Target audio bus and staged adaptation

The eventual user-facing system is broader than this repository's first slice:
PersonaPlex owns duplex presence; Voxtral Realtime supplies streaming
transcription; Jev supplies calibrated routing; an asynchronous reasoner
proposes typed actions; a policy gate handles confirmation and refusal; a
response renderer speaks safe text; hot state, a durable event log, semantic
memory, and observability remain separately measured stages. The source
architecture's `needs_tools` label maps to this repo's narrower `film_request`;
`chitchat` and `clarify` retain their meanings. Slow reasoner work never blocks
the talker loop: it runs asynchronously, becomes stale on interruption/topic
change, and returns a rendered result only after validation.

The first response renderer is clean TTS or typed text, not PersonaPlex context
injection. This avoids the known text-prompt, burst-injection, and audio-stream
collision failures until routing and action validation are stable. A policy
preflight runs even though the route enum remains three labels: destructive,
external-message, payment, credential, privacy, and release-render requests
require explicit operator confirmation; ambiguous policy input fails to
`clarify` or rejection. Redis, Postgres, Mem0, Cognee, Zep, and Letta are not
enabled here. They are later stories with retention, deletion, access,
provenance, latency, and GPU-contention gates; the initial bridge keeps only
typed transient state plus its hash-bearing append-only event.

## Existing API seams and consumers

These signatures were verified at `9007abf`; source spells Pipeline's annotation `Optional[CaptionSpec]` (same declared type), and follow-ups must re-read source.

```python
# predict/pipeline.py
    def forward(self, intent: str, *, n_shots: int = 1,
                caption_spec: CaptionSpec | None = None) -> PipelineResult:

# scripts/run_acceptance.py
def run_bundle(bundle_path: str | Path, *, db_path: str | Path | None = None,
               ledger_path: str | Path | None = None,
               output_path: str | Path | None = None,
               host=None, vision_judge=None) -> dict:

# host/render_host.py
    def run_argv(self, cmd, *, cwd, timeout):

    def push_file(self, local: str, remote: str) -> str:

    def fetch_file(self, remote: str, local: str) -> str:

# predict/vibevoice.py
    def generate(
        self,
        turn: VibeVoiceTurn,
        destination: str | Path,
        seed: int,
    ) -> Path:
```

Consumer map:

- `PipelineExperimentAdapter` consumes `Pipeline.forward()` after validation,
  only for a non-release experiment; it never replaces `run_bundle()`.
- `GovernedFilmExecutor` is the sole release-quality `run_bundle()` consumer
  and records run/job/output/ledger identifiers in the bridge event.
- `SshHostTransportAdapter` injects the three host methods into the existing
  governed stack; the bridge never calls them directly or creates alternate
  remote command/file paths.
- `RepoDialogueAudioSupplier` consumes VibeVoice only for a future validated
  dialogue turn under existing manifest/provenance discipline; it is not a
  router, reasoner, or executor, and release film audio remains bundle-owned.

## Typed event and provenance contract

Every routing/reasoner decision emits one append-only JSON event with schema
identifier `wangp-dspy.talker-reasoner-event/v1`. Unknown fields fail
validation in follow-up implementations.

```json
{
  "schema": "wangp-dspy.talker-reasoner-event/v1",
  "event_id": "UUIDv7",
  "dialogue_turn_id": "opaque-stable-id",
  "route": "chitchat | film_request | clarify",
  "confidence": 0.0,
  "input": {"transcript_sha256": "64 hex|null", "audio_sha256": "64 hex|null",
            "audio_bytes": "integer|null", "media_type": "typed descriptor",
            "raw_prompt_persisted": false, "raw_audio_persisted": false},
  "selected_action": {"type": "none|talk|clarify|candidate_film",
                      "parameters_sha256": "64 hex|null",
                      "authorization": "local_fixture|operator_explicit|rejected"},
  "tool_call": {"schema": "wangp-dspy.bridge.action/v1",
                "name": "none|request_clarification|request_film",
                "status": "not_requested|emitted|validated|rejected",
                "arguments_sha256": "64 hex|null"},
  "artifacts": [{"role": "dialogue_response|governed_film|ledger|bridge_event",
                 "path": "owned path|null", "sha256": "64 hex",
                 "media_type": "IANA or logical type"}],
  "latency_ms": {"router": 0, "reasoner": 0, "validation": 0,
                 "execution": 0, "total": 0},
  "rejection": {"code": "none|low_confidence|invalid_route|invalid_schema|forbidden_tool|authorization_failed|qc_failed",
                "stage": "router|reasoner|validator|executor",
                "detail_sha256": "64 hex|null"},
  "repository_identity": {"repo_root": "absolute root", "commit_sha": "40 hex",
                          "clean_tree": false, "dirty_tree": true,
                          "status_sha256": "64 hex",
                          "tracked_diff_sha256": "64 hex",
                          "untracked_content_sha256": "64 hex",
                          "changed_path_count": 0,
                          "untracked_path_count": 0}
}
```

`repository_identity` must preserve the shape returned by the repo's existing
canonical identity helper rather than invent a second provenance format.

Prompt/audio bytes may exist transiently in memory for an explicitly consented
live request, but serializers must write only lengths, media types, and SHA-256
digests by default. A future retention exception must be a separate approved
story with minimization, deletion, access control, and consent checks. Event
paths and artifact references must be validated to remain within the owning
run directory. Rejection details are hashed unless a follow-up story defines a
redacted, non-sensitive diagnostic representation.

## First-slice selection decision

Use typed transcript fixtures plus a local deterministic/Jev-style router.
Do not require a live PersonaPlex or Voxtral endpoint in the first vertical
slice.

This choice is reproducible and unit-testable, sends no prompt/audio off-device,
avoids duplex-speech latency during calibration, and does not contend with
render/Whisper/vision/VibeVoice GPUs. Live components belong in a later
consented shadow benchmark, not as a prerequisite to the contract.

## Rollout and kill criteria

All gates use frozen, versioned fixtures and are measured twice before a
stage change. A gate is a stop/fix boundary, not a threshold to average away.

| Dimension | Rollout gate | Kill/rollback criteria |
|---|---|---|
| Routing correctness | At least 95% exact route accuracy on a 200-fixture frozen set, with 100% on adversarial no-action and incomplete-request fixtures | Below 90%, any unsafe label treated as an action, or inconsistent repeat results |
| False reasoner wakeups | No more than 5% of `chitchat` fixtures invoke the reasoner | More than 10% in either repeat run, or any reasoner call for a malformed route |
| Routing/validation latency | Local fixture p95 <=250 ms router and <=500 ms router+validator, excluding talker/executor | Either p95 >1.5x gate in two runs, or missing per-stage latency fields |
| Action validation | 100% of emitted calls pass fixed-schema and allowlist checks; zero forbidden tool names/arguments | Any unvalidated execution, unknown route, arbitrary schema, or missing rejection event |
| Privacy | 100% of persisted events omit prompt/audio bytes and carry all required hashes/identity | Any raw prompt/audio persisted by default, absent retention evidence, or undeclared network inference |
| Governed artifact production | First three approved film candidates complete through `run_bundle()` with `needs_review`/completed ledger provenance and output+ledger hashes | Any direct render/SSH/audio shortcut, missing provenance, QC bypass, or release promotion from a dirty/non-release run |

Rollback restores the previous bridge revision and preserves rejected events.
It never rolls back or rewrites Ref2VA ledger/QC history.

## Follow-up story map

| Story | Depends on | Boundary and explicit non-goals |
|---|---|---|
| Fixture corpus + event contract | Approved spec | Typed transcripts/audio descriptors and hash serializer; no models, execution, or memory |
| Deterministic/Jev-style router | Fixtures | Three calibrated routes, thresholds, replay/false-wakeup metrics; no tools or network |
| Fixed action validator | Router | Three-name allowlisted schema, authorization, rejection provenance; no dynamic schema/execution |
| Voxtral Small reasoner adapter | Router + validator | Consented structured-call shadow benchmark; never executes, never uses Realtime as caller |
| PersonaPlex/Moshi talker adapter | Router + validator | Speaks approved final text only; no native tool calling, schema, credentials, or authority |
| Governed film action broker | Validator | Complete bundle through `run_bundle()` only; no QC/SSH/VibeVoice changes or shortcuts |
| Non-release Pipeline adapter | Validator | Explicit `Pipeline.forward()` experiment labeling; no release promotion |
| Live shadow benchmark + contention plan | Model/broker adapters | Consent, privacy, latency and GPU measurements; no memory or unconsented calls |
| Durable memory evaluation | All thin-loop gates | One privacy/retention/deletion/access decision at a time; never enable every store together |

## Verification for this docs-only story

```bash
$ git diff --check
$ ./.venv/bin/pytest -q tests/test_pipeline.py
```

If the virtual environment is absent or fails, report its exact error; never invent a summary.
