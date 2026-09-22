---
id: WD-gc09
title: "Non-destructive multi-track editing surface for governed generation"
status: open
priority: 2
type: feature
labels: [capability, capstone]
parent: WD-t741
created_at: 2026-09-22T20:24:45Z
created_by: speed
updated_at: 2026-09-22T20:26:48Z
content_hash: "sha256:b9bb9c729a8b64d15fb51f0174ab18dcd848a99c070e437c729fbac183d35c58"
blocked_by: [WD-eq1i, WD-fasw, WD-8ioj]
---

## Description
## USER INTENT
Observable outcome: a non-destructive multi-track editor can import governed artifacts, arrange video/audio/image/text tracks, revise edits without overwriting sources, and emit a deterministic assembly/render plan through the director and queue.

## Context (Embedded)
- The governed repository path is plan -> durable queue -> host render -> QC gates -> assembly -> provenance/recipe; `wgp` is the stable CLI and GPU execution is never implied by planning.
- This is a product surface over immutable source assets and governed jobs, not a second renderer or QC bypass.
- Non-destructive means edits are serialized decisions with source hashes; source files and accepted evidence remain unchanged.
- The editor consumes director output but must also permit manual arrangement and review checkpoints.

## OUT OF SCOPE
- In-place source editing, hidden generation, direct GPU dispatch, or assembly that bypasses existing QC/provenance.
- A proprietary project format without export/reconstruction evidence.

## DIFF BUDGET
Roughly 12 files, under 1,000 authored changed LOC, excluding generated media and GUI dependencies.

## Boundary Map
PRODUCES:
- wangp/editor_project.py -> typed multi-track project model with clips, transitions, text, audio, images, review marks, and source hashes
- services/editor/project_store.py -> portable save/load, migration checks, source verification, and non-destructive history
- services/editor/assembly_exporter.py -> deterministic project-to-assembly/director request translation
- editor/ -> minimal maintainable UI or equivalent CLI/TUI surface that exercises the same project service; a browser/GUI choice must be documented and testable without GPU
- wangp/editor_cli.py -> headless project validation/export commands so UI is never the only correctness path
- docs/editor.md -> track model, non-destructive guarantees, export semantics, and review/queue path
- tests/test_editor_project.py -> real-process project/export coverage; no mocks
- datasets/runs/maestro-parity/WD-gc09/ -> authorized rendered export bundle

CONSUMES:
CONSUMES:
- services/director/composition.py -> purpose
  spec: accepted director request/review model
- predict/assembler.py -> purpose
  spec: existing assembly path
- services/jobs/queue.py -> purpose
  spec: durable queue record and attempt transitions
- services/jobs/preflight.py -> purpose
  spec: typed missing source/project failures
- predict/v3_recipe.py -> purpose
  spec: immutable reconstruction/provenance contract
- wangp/diagnostics.py -> purpose
  spec: actionable headless/UI diagnostics
- wangp/cli.py -> purpose
  spec: stable verb registration and exit-code contract


## Required Outcomes
### no-GPU verifiable now
- Real tests create/save/reopen a multi-track project in a clean temporary directory, import committed media, move/trim/reorder clips and text, and prove every source hash and prior decision remains recoverable.
- Export emits the same deterministic director/assembly JSON across repeated export and after project round-trip; missing/mutated source files fail typed.
- Undo/redo or equivalent history records a real edit sequence and never rewrites imported source bytes.
- The headless validation/export verb runs in CI without a display, GPU, network, or generation claim.

### requires an authorized host render
- One separately authorized export/render through the governed director/queue path produces a real finished artifact from a non-destructive project, with all mandatory gates and assembly provenance.
- The run bundle includes project hash, source hashes, export request, queue attempts, command, model provenance, output hashes, and QC/review evidence.

## Testing Requirements
- `uv run --frozen --extra dev pytest tests/test_editor_project.py -q` plus the UI/headless test selected by the implementation; real filesystem/CLI/subprocess only, no mocks.
- Use committed media and prove source bytes are unchanged after edits and exports.
- Authorized export evidence is reviewed through ffprobe, hashes, queue records, and recipe reconstruction; planning alone cannot be called rendering.

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

## USER INTENT
Observable outcome: a non-destructive multi-track editor can import governed artifacts, arrange video/audio/image/text tracks, revise edits without overwriting sources, and emit a deterministic assembly/render plan through the director and queue.

## Context (Embedded)
- The governed repository path is plan -> durable queue -> host render -> QC gates -> assembly -> provenance/recipe; `wgp` is the stable CLI and GPU execution is never implied by planning.
- This is a product surface over immutable source assets and governed jobs, not a second renderer or QC bypass.
- Non-destructive means edits are serialized decisions with source hashes; source files and accepted evidence remain unchanged.
- The editor consumes director output but must also permit manual arrangement and review checkpoints.

## OUT OF SCOPE
- In-place source editing, hidden generation, direct GPU dispatch, or assembly that bypasses existing QC/provenance.
- A proprietary project format without export/reconstruction evidence.

## DIFF BUDGET
Roughly 12 files, under 1,000 authored changed LOC, excluding generated media and GUI dependencies.

## Boundary Map
PRODUCES:
- wangp/editor_project.py -> typed multi-track project model with clips, transitions, text, audio, images, review marks, and source hashes
- services/editor/project_store.py -> portable save/load, migration checks, source verification, and non-destructive history
- services/editor/assembly_exporter.py -> deterministic project-to-assembly/director request translation
- editor/ -> minimal maintainable UI or equivalent CLI/TUI surface that exercises the same project service; a browser/GUI choice must be documented and testable without GPU
- wangp/cli.py -> headless project validation/export verbs so UI is never the only correctness path
- docs/editor.md -> track model, non-destructive guarantees, export semantics, and review/queue path
- datasets/runs/maestro-parity/<story-id>/ -> authorized rendered export bundle

CONSUMES:
- services/director/composition.py -> accepted director request/review model
- predict/assembler.py -> existing assembly path
- services/jobs/queue.py and services/jobs/preflight.py -> durable queue and typed preflight
- predict/v3_recipe.py -> immutable reconstruction/provenance contract
- wangp/diagnostics.py -> actionable UI/headless errors

## Required Outcomes
### no-GPU verifiable now
- Real tests create/save/reopen a multi-track project in a clean temporary directory, import committed media, move/trim/reorder clips and text, and prove every source hash and prior decision remains recoverable.
- Export emits the same deterministic director/assembly JSON across repeated export and after project round-trip; missing/mutated source files fail typed.
- Undo/redo or equivalent history records a real edit sequence and never rewrites imported source bytes.
- The headless validation/export verb runs in CI without a display, GPU, network, or generation claim.

### requires an authorized host render
- One separately authorized export/render through the governed director/queue path produces a real finished artifact from a non-destructive project, with all mandatory gates and assembly provenance.
- The run bundle includes project hash, source hashes, export request, queue attempts, command, model provenance, output hashes, and QC/review evidence.

## Testing Requirements
- `uv run --frozen --extra dev pytest tests/test_editor_project.py -q` plus the UI/headless test selected by the implementation; real filesystem/CLI/subprocess only, no mocks.
- Use committed media and prove source bytes are unchanged after edits and exports.
- Authorized export evidence is reviewed through ffprobe, hashes, queue records, and recipe reconstruction; planning alone cannot be called rendering.

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
- 2026-09-22T20:24:47Z dep_added: blocked_by WD-eq1i
- 2026-09-22T20:26:48Z dep_added: blocked_by WD-fasw
- 2026-09-22T20:26:48Z dep_added: blocked_by WD-8ioj

## Links
- Parent: [[WD-t741]]
- Blocked by: [[WD-eq1i]], [[WD-fasw]], [[WD-8ioj]]

## Comments
