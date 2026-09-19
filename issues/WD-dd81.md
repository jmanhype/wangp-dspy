---
id: WD-dd81
title: "Define the thin Talker-Reasoner bridge contract"
status: closed
priority: 1
type: task
parent: WD-1te5
created_at: 2026-09-19T04:14:14Z
created_by: speed
updated_at: 2026-09-19T20:44:00Z
content_hash: "sha256:6a79f1ec5f305984058a21f16939854bd70f277528bc62b1b49270c887ebc31c"
assignee: dev-WD-dd81
labels: [accepted]
closed_at: 2026-09-19T20:44:00Z
close_reason: "Accepted: independently re-read and AST-verified all four cited source seams on current main; the 299-line docs-only delivery stays in budget, preserves PersonaPlex/Moshi and Voxtral capability facts, adds the fifth-session target audio bus and staged adaptation, defaults to privacy-safe hash-bearing events, and keeps run_bundle as the sole release-quality path. Exact primary-interpreter pipeline test passed 11/11; independent contract validation passed 24/24; git diff checks and scoped pvg verify passed."
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
   delivery did not disturb the existing pipeline contract. If the story
   worktree lacks `.venv`, use the exact primary-repo interpreter
   `/Users/Shared/HermesWorkspace/wangp-dspy/.venv/bin/pytest` from the story
   worktree and record that substitution; do not create another environment.

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

## Context (Embedded)

### Operator-selected research inputs

- Fifth operator-provided synthesis: “The Whole System: PersonaPlex + Jev +
  Slow Reasoner + Memory.” It adds the target audio-bus architecture, async
  slow-reasoner requirement, clean-TTS-first response policy, safety/policy
  preflight, observability metrics, and staged Redis/Postgres/Mem0-or-Cognee
  rollout. This repo’s first slice must adapt that architecture to governed
  film actions rather than import every service immediately.
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
9. **Fifth-session target architecture.** Represent the full audio-bus system
   (PersonaPlex, Voxtral Realtime, Jev, slow reasoner, hot state, durable event
   log, semantic memory, response renderer, policy/observability) as the target,
   then define the repo-local staged adaptation. Explain that source label
   `needs_tools` maps to the first-slice `film_request` route, that slow
   reasoner work must be asynchronous, and that clean TTS/response rendering is
   safer than PersonaPlex context injection initially. Include a policy preflight
   and confirmation boundary even though the initial route enum remains three
   labels. Do not enable Redis, Postgres, Mem0, Cognee, Zep, or Letta in the
   first slice; enumerate them as later measured stages.

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
9. The exact primary-repo interpreter command
   `/Users/Shared/HermesWorkspace/wangp-dspy/.venv/bin/pytest -q tests/test_pipeline.py`
   passes from the story worktree, proving the docs-only delivery did not
   disturb the existing pipeline contract. Use this exact interpreter because
   story worktrees do not provision `.venv`; do not create a substitute
   environment.

## Testing Requirements

- Unit: not applicable to a docs-only story; do not add placeholder tests.
- Integration: run the exact primary-repo interpreter command above from the
  story worktree and paste the summary.
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


## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-19.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## Implementation Evidence

Commands run:

```bash
cd /Users/Shared/HermesWorkspace/wangp-dspy/.claude/worktrees/dev-WD-dd81
pvg issues show WD-dd81 --json
git merge main --no-edit
git add docs/specs/talker-reasoner-bridge.md docs/plans/talker-reasoner-bridge.md
git diff --cached --check
/Users/Shared/HermesWorkspace/wangp-dspy/.venv/bin/pytest -q tests/test_pipeline.py
python3 /Users/speed/Documents/Codex/2026-09-18/yes-paivot-pvg-is-designed-for/work/validate_wd_dd81.py
pvg verify docs/specs/talker-reasoner-bridge.md docs/plans/talker-reasoner-bridge.md
git commit -m 'docs: define thin Talker-Reasoner bridge'
git diff --check
```

Material state:

- Story worktree: `/Users/Shared/HermesWorkspace/wangp-dspy/.claude/worktrees/dev-WD-dd81`
- Base/current protected main before docs commit: `9007abf`
- Delivery commit: `5458a25`
- Files: `docs/specs/talker-reasoner-bridge.md` and `docs/plans/talker-reasoner-bridge.md`
- Total changed lines: 299, within the under-300 budget.
- Spec SHA-256: `f776ff529f333fc4f8efdb17339efbf2dc01107bf43bff235597aa63a7b06583`
- Plan SHA-256: `f61b6ba0d2ed55693218cefb5c20843dbeaf5257fcd9cf9220c7a4af9763d415`
- The preserved draft was repaired to include the fifth-session target audio bus, `needs_tools -> film_request`, asynchronous reasoner behavior, clean TTS first, policy confirmation, and deferred Redis/Postgres/Mem0/Cognee/Zep/Letta stages.
- Independent AST validation confirmed all four current source seams: `Pipeline.forward`, `run_bundle`, `SshHost.run_argv/push_file/fetch_file`, and `VibeVoiceBackend.generate`.
- Broad word scan found only the policy word “credentials”; precise secret-value regex scan found zero hits.

### CI/Test Results

```text
git diff --cached --check: PASS (exit 0, no output)
/Users/Shared/HermesWorkspace/wangp-dspy/.venv/bin/pytest -q tests/test_pipeline.py:
...........                                                              [100%]
11 passed

Independent contract validation: PASS (24/24 checks)
pvg verify docs/specs/talker-reasoner-bridge.md docs/plans/talker-reasoner-bridge.md:
VERIFY: PASSED (0 files scanned, 0 issues)
post-commit git diff --check: PASS
```

Summary: the docs-only boundary contract is complete on a clean story branch fast-forwarded to current main. It defines exactly three first-slice routes, separates talker/transcription/call-emission/execution/routing/memory capabilities, maps the full fifth-session audio-bus architecture to staged repo-local work, and makes `run_bundle()` the sole release-quality film execution path. Raw prompt/audio bytes are transient only; persisted events carry hashes and repository identity by default.

Commit SHA: 5458a25

### AC Verification

| AC | Result | Evidence |
|---|---|---|
| 1. Self-contained spec exists | PASS | 273-line spec plus 26-line plan fragment; total 299 lines |
| 2. Four API seams copied and mapped | PASS | Story-normalized signatures copied; current-source AST signatures independently verified |
| 3. Capability facts correct | PASS | PersonaPlex/Moshi marked no native tool protocol; Voxtral Small and Realtime roles separated |
| 4. First slice thin | PASS | Three routes, fixed small action surface, no durable platform, no unconsented network |
| 5. Versioned hash event contract | PASS | `talker-reasoner-event/v1`; input/action/tool/artifact hashes, latency, rejection, repository identity |
| 6. Rollout/kill criteria and follow-up map | PASS | Measurable table plus nine dependency-ordered follow-up stories |
| 7. Ref2VA gates preserved | PASS | `run_bundle()` explicitly sole release path; no QC bypass or seam change |
| 8. diff check | PASS | `git diff --cached --check` and post-commit `git diff --check` exit 0 |
| 9. pipeline contract test | PASS | Exact primary interpreter command from story worktree: 11 passed |

## nd_contract
status: delivered

### evidence
- Delivery commit SHA: `5458a25`.
- Spec SHA-256: `f776ff529f333fc4f8efdb17339efbf2dc01107bf43bff235597aa63a7b06583`.
- Plan SHA-256: `f61b6ba0d2ed55693218cefb5c20843dbeaf5257fcd9cf9220c7a4af9763d415`.
- Independent validation and test outputs above.

### proof
- [x] AC #1: Spec and plan exist and are self-contained.
- [x] AC #2: Four source seams copied and consumer-mapped.
- [x] AC #3: Capability matrix preserves verified model facts.
- [x] AC #4: First implementation explicitly thin.
- [x] AC #5: Hash-bearing privacy-safe event contract defined.
- [x] AC #6: Rollout/kill gates and dependency map defined.
- [x] AC #7: Existing Ref2VA governance and `run_bundle()` boundary preserved.
- [x] AC #8: Diff check passed.
- [x] AC #9: Exact pipeline test command passed with 11 tests.


## History
- 2026-09-19T04:15:44Z status: open -> in_progress
- 2026-09-19T04:15:44Z claimed by dev-WD-dd81
- 2026-09-19T04:41:21Z status: in_progress -> open
- 2026-09-19T04:41:21Z released by speed
- 2026-09-19T20:40:14Z status: open -> in_progress
- 2026-09-19T20:40:14Z claimed by dev-WD-dd81
- 2026-09-19T20:43:44Z status: in_progress -> in_progress
- 2026-09-19T20:44:00Z status: in_progress -> closed

## Links
- Parent: [[WD-1te5]]

## Comments
