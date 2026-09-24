---
id: WD-m0r5
title: "Image generation evidence"
status: open
priority: 1
type: feature
labels: [capability, evidence, external-integration, walking-skeleton]
parent: WD-3nod
created_at: 2026-09-24T14:14:05Z
created_by: speed
updated_at: 2026-09-24T14:39:53Z
content_hash: "sha256:3da86211290d4a52361eb42d53e9458b69a6e63deeceed4060e367fed9ef6a18"
blocks: [WD-bxhc, WD-651z, WD-0zj8, WD-fay0]
---

## Description
## USER INTENT
The four currently `planned` family/preset rows in `docs/image-capabilities.md` — `qwen_image/qwen-standard`, `qwen_image/qwen-professional`, `flux_kontext/flux-standard`, and `flux_kontext/flux-kontext` — must reach an evidence-backed terminal state. Every currently `planned` capability cell in those four rows ends as either `host_run_verified` from a real authorized bundle under `datasets/runs/maestro-parity/WD-m0r5/`, or `unsupported_on_this_hardware` with recorded infeasibility evidence. No row or cell may be dropped or silently marked verified.

## REQUIRED OPERATOR INPUTS — NOT YET PROVIDED
- Per-batch GPU authorization has NOT been given by this story.
- Model-download approval has NOT been given by this story.
- Both are required inputs before any real generation attempt. The lane bundle must record the operator authorization text verbatim, including its scope, timestamp, model/download approval, and exact command boundary.
- Missing authorization is not infeasibility and must not be converted into `unsupported_on_this_hardware`; the lane remains blocked on operator input rather than fabricating a terminal verdict.

## No-Fabrication Rule
Vendor documentation, configuration, normalized settings, plans, unit tests, dry-runs, queue planning, and absence of an attempt are never generation evidence. `host_run_verified` requires actual emitted image bytes from an authorized run. `unsupported_on_this_hardware` requires recorded evidence, not assertion.

## OUT OF SCOPE
- Any GUI.
- Capabilities beyond Maestro's documented image list or beyond the four named family/preset rows.
- Registry publication.
- Any training run.
- Reusing output from another lane as this lane's evidence.

## DIFF BUDGET
- Authored text is about 2 files and under 250 changed LOC: `docs/image-capabilities.md` plus bundle manifests/diagnostics under the lane root.
- Generated evidence is bounded to the required image artifacts, logs, and metadata for the four rows; no model weights are committed. Record aggregate bundle size, and keep it under 128 MiB unless the recorded infeasibility evidence itself is larger.

## Boundary Map
PRODUCES:
- datasets/runs/maestro-parity/WD-m0r5/ -> `wangp-dspy.maestro-parity-evidence/v1` image evidence bundles
  spec: one checker-valid sub-bundle per family/preset row (and per planned operation where applicable), with authorization, exact command, commit, provenance, queue attempt, output hashes, metadata, gates, and verdict.
- docs/image-capabilities.md -> evidence-backed terminal matrix rows
  event: update exactly the four named rows from bundle contents, citing the bundle path and preserving every already unsupported boundary rather than inventing capability.

CONSUMES:
- WD-651z: docs/maestro-parity-evidence-contract.md -> canonical required bundle fields
  source: the checker contract is authoritative; this lane must not duplicate or weaken it.
- WD-651z: scripts/verify_maestro_parity.py -> `verify_bundle(bundle: Path) -> VerificationReport`
  event: the implemented checker must pass this lane's complete bundle before any `host_run_verified` update.
- (existing): docs/image-capabilities.md -> current four-row image matrix
  source: row/cell identity and existing unsupported boundaries.
- (operator): explicit per-batch GPU authorization and model-download approval -> verbatim authorization record
  source: future operator input; not supplied by story creation.

## Story Acceptance Criteria
1. [State] Given explicit operator authorization, model/download approval, and a real successful run, an image cell flips to `host_run_verified` only when its emitted bytes, provenance, and metadata are present in a lane bundle that passes the WD-651z checker.
2. [Unwanted] Given absent, blank, partial, or mismatched authorization or evidence, the affected cell remains non-verified; it is neither dropped nor silently flipped to verified.
3. [State] `docs/image-capabilities.md` is mechanically updated from bundle contents, and every flipped cell names or links to the exact bundle/evidence record from which its verdict came.
4. [State] Each successful row bundle contains all four summary field groups — authorization/command/commit; model/reference/queue provenance; output hash/media metadata/objective gates; and reviewer verdict — while complying with the complete canonical contract rather than this abbreviated grouping.
5. [Unwanted] A cell becomes `unsupported_on_this_hardware` only with recorded infeasibility evidence: measured host capacity versus model/output requirements, or an actual authorized failed attempt with captured command output and failure cause; vendor claims, plans, tests, and dry-runs do not qualify.
6. [State] All four named family/preset rows reach a terminal evidence state with no `planned` cell left in those rows; already unsupported cells remain unsupported unless real evidence supports a different explicit verdict.
7. [Unwanted] No GUI, registry publication, training run, extra capability row, or protected engine change occurs; `services/jobs/queue.py`, `services/director/renderers/policy.py`, `services/director/wiring.py`, `services/jobs/preflight.py`, and `scripts/run_film.py` remain unchanged from accepted base `40f8c2b373dec1c84ca5a596c821b740934af6fb`.

## Testing Requirements
- Before generation, record the operator authorization and model/download approval verbatim and verify the exact planned command/commit/model/reference inputs.
- For every emitted image, record SHA-256, dimensions, alpha mode where applicable, objective gate inputs/results, and reviewer verdict; invoke the WD-651z checker on the lane bundle and require exit zero before any `host_run_verified` update.
- For every infeasible cell, record the measured host/model constraint or exact authorized failed-attempt output; run the checker in its unsupported-evidence mode if the contract defines one, otherwise record a fail-closed checker result plus the separate infeasibility evidence.
- Matrix consistency is mandatory: parse the final document and prove every one of the four row identities has only evidence-backed terminal values, no dropped rows/cells, and links to matching bundle records.
- Standing gates: targeted image/evidence tests if implementation adds them; `uv run --frozen --extra dev pytest -q --junitxml=/tmp/WD-m0r5-full.xml` with parsed `errors=0`/`failures=0`; `uv run --frozen --extra dev wgp release verify` reporting `release=ready`/`tag_created=false`; and `git diff --exit-code 40f8c2b373dec1c84ca5a596c821b740934af6fb -- services/jobs/queue.py services/director/renderers/policy.py services/director/wiring.py services/jobs/preflight.py scripts/run_film.py`.
- Also run `git diff --check`, record aggregate bundle size, and record every matrix row/cell transition.

## Delivery Requirements
- Paste authorization provenance without inventing approval, exact command output tails, bundle hashes/metadata, checker output, parsed JUnit counters, release fields, protected-file parity, and the final four-row matrix table.
- If operator input remains absent, report the lane as blocked on that input; do not substitute plans, dry-runs, or unsupported assertions for generation evidence.

## nd_contract
status: new

### evidence
- Authored on 2026-09-24 from the four planned rows in `docs/image-capabilities.md:60-63`; operator GPU/download approvals remain outstanding.

### proof
- [ ] Pending implementation and explicit operator authorization.

## Acceptance Criteria


## Design


## Notes
## MANDATORY SKILLS
- pvg

Observable outcome: an explicitly authorized run emits hashed image artifacts and metadata under datasets/runs/maestro-parity/WD-m0r5/; without that authorization and bundle, no generation result is claimed.

## History
- 2026-09-24T14:14:06Z dep_added: blocks WD-bxhc
- 2026-09-24T14:14:08Z dep_added: blocks WD-651z
- 2026-09-24T14:14:09Z dep_added: blocks WD-0zj8
- 2026-09-24T14:14:09Z dep_added: blocks WD-fay0

## Links
- Parent: [[WD-3nod]]
- Blocks: [[WD-bxhc]], [[WD-651z]], [[WD-0zj8]], [[WD-fay0]]

## Comments
