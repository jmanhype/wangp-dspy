---
id: WD-pcen
title: "Image generation and editing with references, transparency, upscaling, and identity preservation"
status: in_progress
priority: 2
type: feature
labels: [capability]
parent: WD-t741
created_at: 2026-09-22T20:24:44Z
created_by: speed
updated_at: 2026-09-23T00:09:22Z
content_hash: "sha256:17810d9e1d42ad0676e045a8b6ed5b2b87cfaf8ec24d9754b9037a430a2c9702"
blocks: [WD-tkuz, WD-gc09]
assignee: dev-WD-pcen
follows: [WD-6tox]
---

## Description

## USER INTENT
Observable outcome: image generation and editing reach Maestro breadth—up to ten references, prompt enhancement, transparent PNG, upscale/outpaint, and an identity-preserving edit—while remaining typed, reproducible, and honestly gated.

## Context (Embedded)
- The governed repository path is plan -> durable queue -> host render -> QC gates -> assembly -> provenance/recipe; `wgp` is the stable CLI and GPU execution is never implied by planning.
- There is no first-class `wgp` image modality today; this story adds it as a governed peer of video rather than as an arbitrary script.
- Reference count, prompt-enhancement mode, transparency, output size, identity references, and edit region are immutable request fields.
- Image results can seed characters, video plates, and director composition, so hashes and licence metadata must remain attached.

## OUT OF SCOPE
- Quiet prompt rewriting by a remote provider, model download, or paid API without explicit configuration and per-run authorization.
- A face-swap or identity claim based only on visual inspection; identity preservation needs a declared objective gate and recorded evidence.

## DIFF BUDGET
Roughly 9 files, under 750 authored changed LOC, excluding weights and generated images.

## Boundary Map
PRODUCES:
- predict/image_capabilities.py -> typed `ImageCapabilityRequest` with mode, up to ten references, enhancement, transparency, upscale/outpaint, identity, and output constraints
- services/image/request_compiler.py -> deterministic job records, reference ordering/hashes, edit masks, and backend-specific normalization
- host/image_backends.py -> fail-closed image backend adapters and model-manifest checks
- wangp/image_cli.py -> `wgp image plan|edit|upscale|outpaint` command implementation and submit boundary
- docs/image-capabilities.md -> schema, reference/identity rules, transparency/PNG contract, and evidence matrix
- tests/test_image_capabilities.py -> real-process image request and queue coverage; no mocks
- datasets/runs/maestro-parity/WD-pcen/ -> authorized image run bundles

CONSUMES:
- predict/content_brief.py -> typed reference and asset validation patterns
  spec: typed reference and asset validation patterns
- services/jobs/queue.py -> durable queue record and attempt transitions
  spec: durable queue record and attempt transitions
- services/jobs/preflight.py -> typed missing model/reference failures
  spec: typed missing model/reference failures
- host/render_host.py -> explicit asset push/pull and remote execution boundary
  spec: explicit asset push/pull and remote execution boundary
- wangp/diagnostics.py -> typed actionable diagnostics and redaction
  spec: typed actionable diagnostics and redaction
- wangp/cli.py -> stable verb registration and exit-code contract
  spec: stable verb registration and exit-code contract


## Required Outcomes
### no-GPU verifiable now
- Real CLI tests validate generation and edit forms, exactly ten-reference acceptance, eleventh-reference rejection, prompt-enhancement modes, PNG transparency, output bounds, and identity-reference requirements.
- A real temporary queue records hashes and ordered references, while absent/mismatched assets, invalid masks, unsupported size, or missing model provenance fail typed before host contact.
- Dry-run reconstruction reproduces the exact image job and enhancement metadata from queue plus recipe; no image existence or quality is claimed.
- Documentation and matrix rows distinguish planned from host-verified image capabilities.

### requires an authorized host render
- Separately authorized host runs produce real artifacts for generation, ten-reference edit, transparent PNG, upscale, outpaint, and identity-preserving edit.
- Each bundle records operator authorization, model/reference provenance, command, commit, queue attempt, hashes, image metadata/dimensions/alpha mode, objective identity-gate result where applicable, and reviewer verdict.

## Testing Requirements
- `uv run --frozen --extra dev pytest tests/test_image_capabilities.py -q` with real CLI and filesystem processes and no mocks.
- Use actual reference files and actual temporary queue databases; corrupt or mismatch one real file to prove typed failure.
- Review authorized image bundles with file/identify or equivalent real metadata tooling and hash verification; do not generate during no-GPU tests.

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
- 2026-09-22T20:24:45Z dep_added: blocks WD-tkuz
- 2026-09-22T20:27:37Z dep_added: blocks WD-gc09
- 2026-09-23T00:09:22Z status: open -> in_progress
- 2026-09-23T00:09:22Z auto-follows: linked to predecessor WD-6tox
- 2026-09-23T00:09:22Z claimed by dev-WD-pcen

## Links
- Parent: [[WD-t741]]
- Blocks: [[WD-tkuz]], [[WD-gc09]]
- Follows: [[WD-6tox]]

## Comments
