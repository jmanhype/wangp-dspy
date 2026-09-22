---
id: WD-tkuz
title: "Portable characters and continuity across image and video generation"
status: open
priority: 2
type: feature
labels: [capability]
parent: WD-t741
created_at: 2026-09-22T20:24:44Z
created_by: speed
updated_at: 2026-09-22T20:24:44Z
content_hash: "sha256:2691f16010462c5093807261536111a09ea8be646f6eaa3b570bb16225358cfd"
blocked_by: [WD-pcen, WD-6ml6, WD-6tox]
blocks: [WD-8ioj, WD-eq1i]
---

## Description
## USER INTENT
Observable outcome: reusable character definitions carry appearance and voice, share as portable files, recover native-resolution views, bind to saved voices, and are reused consistently by both image and video modes.

## Context (Embedded)
- The governed repository path is plan -> durable queue -> host render -> QC gates -> assembly -> provenance/recipe; `wgp` is the stable CLI and GPU execution is never implied by planning.
- Typed briefs and speaker manifests already identify characters, and the entity registry records deterministic identity constraints; this story creates the reusable portable product object and generation bindings.
- Native-resolution recovery must preserve original bytes/provenance and must not upscale or silently substitute a rendered thumbnail as native.
- Continuity is evidence-based: identity gates and cross-mode hashes/state links, not a claim embedded in a prompt.

## OUT OF SCOPE
- Creating a real-person deepfake or a named public character without recorded authorization and licence review.
- Hiding character voice consent or appearance licence metadata inside a host-only model directory.

## DIFF BUDGET
Roughly 9 files, under 700 authored changed LOC, excluding character assets and generated media.

## Boundary Map
PRODUCES:
- predict/character_packages.py -> portable typed schema for identity, appearance assets, native-source links, voice binding, constraints, and version
- services/characters/package_service.py -> import/export, hash verification, native-view recovery, and compatibility checks
- predict/image_capabilities.py and predict/video_capabilities.py integration points -> explicit character-reference binding for both modes
- wangp/cli.py -> `wgp character create|show|export|import|recover|bind-voice` no-GPU verbs
- docs/character-packages.md -> portable format, consent/licence fields, native-resolution semantics, and cross-mode usage
- datasets/runs/maestro-parity/<story-id>/ -> authorized cross-mode character continuity bundles

CONSUMES:
- predict/content_brief.py and predict/speaker_manifest.py -> existing character/speaker contracts
- predict/voice_registry.py -> saved portable voice package
- docs/entity-registry.md and qc identity/vision paths -> existing identity-governance concepts
- predict/image_capabilities.py and predict/video_capabilities.py -> image/video request compilation
- services/jobs/queue.py and services/jobs/preflight.py -> durable queue and typed failures

## Required Outcomes
### no-GPU verifiable now
- Real CLI round-trip creates a character package, exports it to a portable archive/file, imports it in a clean temporary directory, verifies all asset hashes, and fails typed on tampering or missing native source.
- Native-resolution recovery resolves and hashes the recorded source view without transcoding; if the source is unavailable it emits an actionable missing-asset diagnostic rather than substituting a derivative.
- Character binding to a saved voice is represented in image/video dry-run plans with explicit package and voice hashes; duplicate IDs, incompatible modes, and absent bindings fail typed.
- No identity-preservation capability is marked verified before authorized image and video runs.

### requires an authorized host render
- Separately authorized runs reuse the same portable character in image generation/edit and video create/extend operations, with bound saved voice where speech is involved.
- Bundles include character package/voice hashes, native sources, model provenance, commands, output hashes, identity-gate evidence, and reviewer decisions.

## Testing Requirements
- `uv run --frozen --extra dev pytest tests/test_character_packages.py -q`, real archive/file/CLI/queue processes with no mocks.
- Deliberately alter one real package byte and prove import fails with the exact hash mismatch.
- Authorized cross-mode artifacts are reviewed through their recorded identity gates; no identity claim may be prompt-only.

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
- 2026-09-22T20:24:45Z dep_added: blocked_by WD-pcen
- 2026-09-22T20:24:45Z dep_added: blocked_by WD-6ml6
- 2026-09-22T20:24:45Z dep_added: blocked_by WD-6tox
- 2026-09-22T20:24:46Z dep_added: blocks WD-8ioj
- 2026-09-22T20:24:47Z dep_added: blocks WD-eq1i

## Links
- Parent: [[WD-t741]]
- Blocks: [[WD-8ioj]], [[WD-eq1i]]
- Blocked by: [[WD-pcen]], [[WD-6ml6]], [[WD-6tox]]

## Comments
