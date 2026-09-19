---
id: WD-dd81
title: "Define the thin Talker-Reasoner bridge contract"
status: in_progress
priority: 1
type: task
parent: WD-1te5
created_at: 2026-09-19T04:14:14Z
created_by: speed
updated_at: 2026-09-19T04:15:44Z
content_hash: "sha256:f8ab9dc8ad3b570a5e5805531a20978683a4415c49904157950f18ed25ab0848"
assignee: dev-WD-dd81
---

## Description
## Context (Embedded)

### Operator-selected research inputs

- Public precursor: “VAOS Voice Bridge: Building a Talker-Reasoner on
  PersonaPlex/Moshi” —
  <https://gist.github.com/jmanhype/5aefd67d9e67b37a8b408abdab39b6d3>.
- Jev precursor: secret gist `e0ea5d0279a14f500c824c47a9ff079e` (architecture
  verification notes; do not publish its contents).
- Paper synthesis target: <https://arxiv.org/abs/2410.08328>.
- Codex research session: `01a0b607-e9df-7d90-8a3e-3193b5d35b32`.

### Verified capability facts that must not be reversed

- PersonaPlex/Moshi is the low-latency duplex talker, not a native
  tool-calling model. The inspected NVIDIA repository had no shipped
  `tools`/`tool_choice`/`tool_calls` protocol; issues #93 and #66 asked for
  that capability without a maintainer roadmap.
- Voxtral Small 24B 2507 can emit structured `tool_calls` from audio, but it
  does not execute tools. Voxtral Realtime is transcription-oriented and is
  not the tool-calling component.
- The old VAOS gist routed transcription/classification through Voxtral and
  delegated actual tool use to Letta. Letta was therefore the System-2 runtime,
  not evidence that Moshi/PersonaPlex natively called tools.
- Jev belongs at the calibrated routing/confidence gate, not as the tool
  executor or replacement talker.
- The recommended first build is deliberately thin: three route labels, one
  small tool-calling reasoner, measured latency/routing quality, and memory
  deferred. Do not start with Letta + Mem0 + Cognee + temporal graphs all
  enabled.

### Current wangp-dspy baseline

- Repository: `/Users/Shared/HermesWorkspace/wangp-dspy`.
- HEAD inspected for this story: `35201a1`.
- The original 2026-09-07 gap audit is historical. Its major production-path
  findings were subsequently implemented; current findings extend through
  `docs/findings/83-mouth-box-consensus.md`.
- Current Ref2VA acceptance combines repository-executed renders, provenance,
  pre/post Whisper, identity vision, dedicated mouth-box consensus, and a
  blocking SyncNet AV gate.
- No existing source path or issue in this repository mentions PersonaPlex,
  Voxtral, Talker-Reasoner, Letta, Mem0, Cognee, or Jev.

## USER INTENT

Start a new Talker-Reasoner lane from the operator-selected research without
destabilizing the already-governed film pipeline. The immediate user-visible
outcome is a reviewable boundary contract that says exactly what the first
thin prototype will and will not do.

## Goal

Create `docs/specs/talker-reasoner-bridge.md` and a matching implementation
plan fragment. The document must be self-contained enough for a fresh Codex
session to create follow-up stories without rereading the three chats.

## Required Design Content

1. **Minimal route state.** Start with only `chitchat`, `film_request`, and
   `clarify`. Explain why `unsafe`, rich intent taxonomies, and arbitrary tool
   schemas are later extensions.
2. **Capability matrix.** Distinguish talker, transcription, structured call
   emission, tool execution, calibrated routing, and durable memory. Include
   PersonaPlex/Moshi, Voxtral Small, Voxtral Realtime, Jev, Letta, and the
   repo-owned VibeVoice dialogue backend.
3. **Thin architecture.** Show where routing, reasoner validation, and governed
   film execution meet without allowing the talker to execute tools.
4. **Typed event/provenance contract.** Define versioned JSON fields for route,
   confidence, input hash, selected action, tool-call schema, artifact hashes,
   latency, rejection reason, and repository identity. Raw prompt text and raw
   audio must not be persisted by default.
5. **Existing seams.** Copy the exact signatures below into the design and map
   each to a proposed consumer:
   - `predict/pipeline.py -> Pipeline.forward(intent: str, *, n_shots: int = 1,
     caption_spec: CaptionSpec | None = None) -> PipelineResult`
   - `scripts/run_acceptance.py -> run_bundle(bundle_path: str | Path, *,
     db_path: str | Path | None = None, ledger_path: str | Path | None = None,
     output_path: str | Path | None = None, host=None, vision_judge=None) -> dict`
   - `host/render_host.py -> SshHost.run_argv(cmd, *, cwd, timeout)`,
     `SshHost.push_file(local: str, remote: str) -> str`, and
     `SshHost.fetch_file(remote: str, local: str) -> str`
   - `predict/vibevoice.py -> VibeVoiceBackend.generate(turn: VibeVoiceTurn,
     destination: str | Path, seed: int) -> Path`
6. **Selection decision.** Recommend whether the first vertical slice should
   use typed transcript fixtures plus a local deterministic/Jev-style router,
   or require a live PersonaPlex/Voxtral endpoint immediately. Justify the
   recommendation with testability, latency, privacy, and GPU contention.
7. **Rollout and kill criteria.** Include measurable gates for routing
   correctness, false reasoner wakeups, route latency, action validation, and
   end-to-end governed artifact production.
8. **Follow-up backlog enumeration.** List candidate stories with boundaries,
   dependencies, and explicit non-goals. Do not implement them here.

## OUT OF SCOPE

- Any Python/module implementation: this is the boundary/design story; follow-up
  stories own code.
- Live external model calls or credentials: no secret is required to complete
  this design.
- Letta/Mem0/Cognee/Zep integration: the research recommendation is to defer
  durable memory until the thin loop works.
- Changing `Pipeline.forward()`, `run_bundle()`, `RenderHost`, or VibeVoice:
  consume their current contracts only.
- Publishing or quoting the secret Jev gist contents.

## DIFF BUDGET

- ~2 files, under 300 changed LOC: the spec plus a plan fragment or tracker
  notes. A gross overrun signals implementation creep.

## Boundary Map

PRODUCES:
- `docs/specs/talker-reasoner-bridge.md` -> an accepted, versioned design
  contract and follow-up story map.

CONSUMES:
- (existing): `predict/pipeline.py` -> `Pipeline.forward(intent: str, *,
  n_shots: int = 1, caption_spec: CaptionSpec | None = None) -> PipelineResult`
- (existing): `scripts/run_acceptance.py` -> `run_bundle(bundle_path: str |
  Path, *, db_path: str | Path | None = None, ledger_path: str | Path | None =
  None, output_path: str | Path | None = None, host=None,
  vision_judge=None) -> dict`
- (existing): `host/render_host.py` -> `SshHost.run_argv(cmd, *, cwd,
  timeout)`, `SshHost.push_file(local: str, remote: str) -> str`,
  `SshHost.fetch_file(remote: str, local: str) -> str`
- (existing): `predict/vibevoice.py` -> `VibeVoiceBackend.generate(turn:
  VibeVoiceTurn, destination: str | Path, seed: int) -> Path`

## Acceptance Criteria

1. `docs/specs/talker-reasoner-bridge.md` exists and is self-contained.
2. It copies the four existing API seams verbatim and identifies which proposed
   component consumes each seam.
3. Its capability matrix does not claim PersonaPlex/Moshi native tool calling
   and does not confuse Voxtral Small with Voxtral Realtime.
4. Its first implementation is explicitly thin: three route labels, a small
   validated action surface, no durable memory platform, and no unconsented
   network inference.
5. It defines a versioned, hash-bearing event contract that never persists raw
   prompt text or raw audio by default.
6. It contains measurable rollout/kill criteria and an enumerated follow-up
   story map with dependencies.
7. It states that this design must not alter the existing Ref2VA QC gates or
   bypass `run_bundle()` for release-quality film execution.
8. `git diff --check` passes.
9. `./.venv/bin/pytest -q tests/test_pipeline.py` passes, proving the docs-only
   delivery did not disturb the existing pipeline contract.

## Testing Requirements

- Unit: not applicable to a docs-only story; do not add placeholder tests.
- Integration: run the exact pipeline test command above and paste the summary.
- Static/diff: run `git diff --check`; paste the result.
- Evidence review: PM must verify every API signature in the document against
  current source, not merely trust the story text.

## Skills To Use

- `pvg` for story delivery/acceptance.
- `codebase-memory` only as a structural locator; because current graph
  coverage reported the relevant top-level paths untracked, direct source
  reads are authoritative for signature verification.

## Delivery Requirements

- Developer must paste command output for AC #8 and #9 into nd notes.
- Developer must include an AC verification table.
- Developer must record the changed spec hash.
- PM acceptance must independently re-read the four cited source functions.

## nd_contract
status: new

### evidence
- Created from operator-selected Codex sessions and current repository
  inspection on 2026-09-19.
- Wangp-dspy HEAD: `35201a1`.
- Source searches found no existing Talker-Reasoner implementation in this
  repository.

### proof
- [ ] Pending implementation

## Acceptance Criteria


## Design


## Notes


## History
- 2026-09-19T04:15:44Z status: open -> in_progress
- 2026-09-19T04:15:44Z claimed by dev-WD-dd81

## Links
- Parent: [[WD-1te5]]

## Comments
