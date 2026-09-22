---
id: WD-eq1i
title: "Director and composition: prompt or audio to governed multi-clip film"
status: open
priority: 2
type: feature
labels: [capability]
parent: WD-t741
created_at: 2026-09-22T20:24:44Z
created_by: speed
updated_at: 2026-09-22T20:24:44Z
content_hash: "sha256:8e8ba68e51de3ae06c1bbf0ab8c5deb7174c5be7b5159ba12a9dc5b6d0d2b362"
blocked_by: [WD-6tox, WD-soa4, WD-6ml6, WD-tkuz]
blocks: [WD-gc09]
---

## Description
## USER INTENT
Observable outcome: one prompt or one audio track can become a governed multi-clip film plan and, only after separate authorization, a finished artifact; screenplay and music-video modes carry continuity, pacing, auto/manual review, and queue enhancement.

## Context (Embedded)
- The governed repository path is plan -> durable queue -> host render -> QC gates -> assembly -> provenance/recipe; `wgp` is the stable CLI and GPU execution is never implied by planning.
- Existing director services, content-brief planning, chain planning, assembler, and QC provide the governed substrate; this story exposes Maestro’s product-level composition modes without weakening review.
- Beat-aware music-video planning consumes measured audio beats rather than fabricated beat claims.
- Auto review is a policy over real gates and reviewer evidence; manual review remains available and must not be bypassed by a planner.

## OUT OF SCOPE
- A free-form prompt that silently calls an external LLM or paid provider; provider selection and authorization are explicit.
- Accepting continuity because the screenplay mentions a character; cross-clip state must be represented and checked.

## DIFF BUDGET
Roughly 11 files, under 900 authored changed LOC, excluding models and generated media.

## Boundary Map
PRODUCES:
- services/director/composition.py -> typed prompt/audio/screenplay/music-video composition requests and outputs
- services/director/continuity.py -> explicit character/appearance/voice/location state across scenes and clips
- services/director/pacing.py -> deterministic pacing and beat-to-clip/window mapping
- services/director/review_policy.py -> auto/manual gate policy and review checkpoints
- wangp/cli.py -> `wgp director plan|enhance|queue|review` no-GPU verbs and explicit submit boundary
- docs/director-composition.md -> prompt/audio/screenplay/music-video workflows, long-form limits, review modes, and evidence contract
- datasets/runs/maestro-parity/<story-id>/ -> authorized director run bundles

CONSUMES:
- services/director/ -> existing orchestration, premises, schema, run ledger/records, and wiring
- services/chain/plan.py and services/chain/keyframes.py -> existing multi-shot continuity planning seams
- predict/video_capabilities.py and predict/music_capabilities.py -> accepted video and music request contracts
- predict/character_packages.py and predict/voice_registry.py -> portable continuity and voice bindings
- services/jobs/queue.py and services/jobs/preflight.py -> durable queue and typed preflight
- predict/assembler.py and qc/ -> governed assembly and QC gates

## Required Outcomes
### no-GPU verifiable now
- Real CLI tests turn a fixed prompt, a committed audio track, and a fixed screenplay into deterministic multi-clip plans with explicit continuity state and per-clip prompts/overlaps.
- Beat-aware music-video planning reads real audio/beat evidence and maps every clip window; absent/corrupt beat evidence is a typed failure.
- Pacing and exact-timecode/window-count controls preserve total target duration up to the programme’s 60-minute contract, and auto/manual review checkpoints are explicit in JSON.
- Queue enhancement rewrites only intended fields with provenance and leaves the original request hash recoverable; a real temporary queue can reconstruct the full composition without generation.

### requires an authorized host render
- Separately authorized runs execute at least one prompt-to-film, one audio/music-video, and one screenplay path through video/music/speech as needed, including assembly and all mandatory QC gates.
- The run bundle records the composition source, review decisions, per-clip queue attempts, model provenance, output hashes, final duration, and recipe/reconstruction evidence.

## Testing Requirements
- `uv run --frozen --extra dev pytest tests/test_director_composition.py -q`, real CLI/files/audio/queue processes, no mocks.
- Use real committed audio and screenplay fixtures; assert one missing/corrupt continuity or beat input produces a typed preflight failure.
- Authorized director bundles must be reviewed with queue, QC, ffprobe, hash, and recipe evidence before capability rows become verified.

## MANDATORY SKILLS
- pvg

## Delivery Requirements
- Developer must use `pvg story deliver`, paste real command output, and provide an AC table plus hashes for every produced artifact and read-only input.
- A GPU-dependent claim may be made only from a recorded run bundle with command, repository commit, model/asset provenance, queue record, exit status, output hashes, QC/gate evidence, and operator authorization for that run. A plan, prompt, unit test, or intention is not generation evidence.
- No story may silently download a model, contact a host, use a paid provider, or claim a capability the matrix marks unverified.

## nd_contract
status: new

### evidence
- Created 2026-09-22 under epic WD-t741 from the Maestro v2.3.0 capability inventory.

### proof
- [ ] Pending implementation and independent PM acceptance.

## Acceptance Criteria


## Design


## Notes


## History
- 2026-09-22T20:24:46Z dep_added: blocked_by WD-6tox
- 2026-09-22T20:24:46Z dep_added: blocked_by WD-soa4
- 2026-09-22T20:24:47Z dep_added: blocked_by WD-6ml6
- 2026-09-22T20:24:47Z dep_added: blocked_by WD-tkuz
- 2026-09-22T20:24:47Z dep_added: blocks WD-gc09

## Links
- Parent: [[WD-t741]]
- Blocks: [[WD-gc09]]
- Blocked by: [[WD-6tox]], [[WD-soa4]], [[WD-6ml6]], [[WD-tkuz]]

## Comments
