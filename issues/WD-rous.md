---
id: WD-rous
title: "Music generation evidence"
status: in_progress
priority: 2
type: feature
labels: [capability, evidence, external-integration]
parent: WD-3nod
created_at: 2026-09-24T14:14:05Z
created_by: speed
updated_at: 2026-09-25T03:35:35Z
content_hash: "sha256:0fc02b6b424d15408b44b7b30176f351ebf926f8b28f2515fb9c2c8576604041"
blocks: [WD-dmf2, WD-fay0]
assignee: dev-WD-rous
follows: [WD-e4r7]
---

## Description
## USER INTENT
The two model-slot rows in `docs/music-capabilities.md` — `ace_step` and `stable_audio` — must reach evidence-backed terminal states. Every currently `planned` matrix cell in those rows (`ace_step` Generate, `ace_step` Style adapt, and `stable_audio` Generate) ends as either `host_run_verified` from a real authorized bundle under `datasets/runs/maestro-parity/WD-rous/`, or `unsupported_on_this_hardware` with recorded infeasibility evidence. The pre-existing `stable_audio` Style-adapt planning-unsupported boundary remains untouched unless separately authorized and evidenced; it must not be relabelled as a hardware verdict by this lane.

## REQUIRED OPERATOR INPUTS — NOT YET PROVIDED
- Per-batch GPU/render-host authorization has NOT been given by this story.
- Model-download approval has NOT been given by this story.
- Both are required before any real music generation or authorized style-adaptation attempt. The bundle must record the operator authorization text verbatim, including scope, timestamp, approver, model/download approval, exact command boundary, and style-reference rights boundary.
- Missing authorization or download approval is a blocked input, not infeasibility, and must never become `unsupported_on_this_hardware`.

## No-Fabrication Rule
Documentation, configuration, normalized settings, model manifests, plans, unit tests, dry-runs, queue planning, ABC notation, compiled scores, chord-planning output, reconstruction output, and absence of an attempt are never generation evidence. `host_run_verified` requires actual emitted audio bytes from an authorized run. `unsupported_on_this_hardware` requires recorded measured evidence, not assertion.

## OUT OF SCOPE
- Any music-style LoRA training run, including any run above the approved download threshold; this story authorizes no training and no threshold overrun. Future training needs separate operator authorization and a separate story.
- Any GUI.
- Registry publication.
- Capabilities outside the two named model-slot rows or reuse of another lane's output as this lane's evidence.

## DIFF BUDGET
- Authored text is about 2 files and under 250 changed LOC: `docs/music-capabilities.md` plus bundle manifests/diagnostics under the lane root.
- Generated evidence is bounded to required audio artifacts, A/B/reference material already required by the request, logs, and metadata; no model weights are committed. Record aggregate bundle size and keep it under 128 MiB unless recorded infeasibility evidence is larger.

## Boundary Map
PRODUCES:
- datasets/runs/maestro-parity/WD-rous/ -> `wangp-dspy.maestro-parity-evidence/v1` music evidence bundles
  spec: one checker-valid sub-bundle per currently planned cell, with authorization, exact argv, commit, model/reference rights, queue attempt, output hashes, measured audio metadata, objective gates, and reviewer verdict.
- docs/music-capabilities.md -> evidence-backed terminal matrix rows
  event: update exactly the `ace_step` and `stable_audio` rows from bundle contents, cite each bundle record, and preserve the distinct planning-unsupported boundary.

CONSUMES:
- WD-651z: docs/maestro-parity-evidence-contract.md -> `wangp-dspy.maestro-parity-evidence/v1`
  source: sole canonical bundle field/hash/verdict contract; this lane must not duplicate or weaken it.
- WD-651z: scripts/verify_maestro_parity.py -> `verify_bundle(bundle: Path) -> VerificationReport`
  event: the accepted checker must exit zero for every bundle used to set `host_run_verified`.
- (existing): docs/music-capabilities.md -> current two-row music matrix and 48 kHz stereo target
  source: exact row/cell identities, style-reference rights requirements, and pre-existing unsupported boundary.
- (operator): explicit per-batch GPU authorization and model-download approval -> verbatim authorization record
  source: future operator input; not supplied by story creation.

## Story Acceptance Criteria
1. [State] Given explicit authorization, download approval, and a successful run, a planned music cell flips to `host_run_verified` only when its emitted audio bytes, model/reference provenance, queue attempt, hashes, measured metadata, and objective gates are present in a lane bundle that passes the accepted WD-651z checker.
2. [Unwanted] Given absent, blank, partial, mismatched, or unauthorized input or evidence, the affected cell remains non-verified and is neither dropped nor silently flipped.
3. [State] `docs/music-capabilities.md` is updated mechanically from bundle contents, and every flipped cell cites the exact bundle/evidence record from which its verdict came.
4. [State] Every successful bundle records actual 48 kHz stereo audio metadata, exact duration, model identity/source/hash or immutable version, license, style-reference rights where applicable, output SHA-256, declared objective-gate inputs/threshold/measured value, and reviewer approval while satisfying the complete canonical contract.
5. [Unwanted] A cell becomes `unsupported_on_this_hardware` only from measured host capacity versus model/output requirements or an actual authorized failed attempt with captured command output and cause; vendor claims, plans, tests, dry-runs, ABC/chord output, and missing authorization never qualify.
6. [State] All currently planned cells in the `ace_step` and `stable_audio` rows reach terminal evidence states with none left `planned`; existing planning-unsupported cells remain explicitly unchanged unless a separately authorized bundle proves a different verdict.
7. [Unwanted] No training run, GUI, registry publication, extra row/cell, model-weight commit, or protected engine change occurs; `services/jobs/queue.py`, `services/director/renderers/policy.py`, `services/director/wiring.py`, `services/jobs/preflight.py`, and `scripts/run_film.py` remain unchanged from accepted base `40f8c2b373dec1c84ca5a596c821b740934af6fb`.

## Testing Requirements
- Before generation, record verbatim authorization/download approval and verify exact argv, commit, model identities, licenses, reference rights, seeds, target format, and requested duration.
- For every emitted audio artifact, record SHA-256 and measured ffprobe properties proving the required 48 kHz stereo target and duration; for style adaptation, retain hash-bound before/reference/output material and the declared audible A/B gate evidence.
- Invoke the accepted WD-651z checker on every complete bundle and require exit zero before any verified update. For infeasibility, retain measured capacity/requirements or the exact authorized failed attempt and a fail-closed checker result plus separate infeasibility evidence.
- Parse the final matrix and prove both named row identities, every planned-cell transition, every citation, no dropped cells, and no changed planning-unsupported boundary without evidence.
- Standing gates: targeted music/evidence tests if implementation adds them; `uv run --frozen --extra dev pytest -q --junitxml=/tmp/WD-rous-full.xml` with parsed `errors=0`/`failures=0`; `uv run --frozen --extra dev wgp release verify` reporting `release=ready`/`tag_created=false`; and `git diff --exit-code 40f8c2b373dec1c84ca5a596c821b740934af6fb -- services/jobs/queue.py services/director/renderers/policy.py services/director/wiring.py services/jobs/preflight.py scripts/run_film.py`.
- Also run `git diff --check`, record aggregate bundle size, and record every matrix transition.

## Delivery Requirements
- Paste authorization provenance without inventing approval, exact command tails, ffprobe metadata, hashes, gate results, checker output, parsed JUnit counters, release fields, protected-file parity, aggregate bundle size, and the final two-row matrix table.
- If required operator input remains absent, report the lane as blocked on that input; do not substitute plans, dry-runs, ABC/chord output, or unsupported assertions for generation evidence.

## MANDATORY SKILLS
- pvg

## nd_contract
status: new

### evidence
- Authored on 2026-09-24 from the two model-slot rows in `docs/music-capabilities.md`; operator GPU/download approvals remain outstanding.

### proof
- [ ] Pending implementation and explicit operator authorization.

## Acceptance Criteria


## Design


## Notes
## MANDATORY SKILLS
- pvg

Observable outcome: an explicitly authorized future run emits hashed music artifacts and measured audio metadata under datasets/runs/maestro-parity/WD-rous/; no GPU batch is authorized by this story and no music result is claimed without that bundle.

## History
- 2026-09-24T14:14:07Z dep_added: blocks WD-dmf2
- 2026-09-24T14:14:08Z dep_added: blocks WD-651z
- 2026-09-24T14:14:09Z dep_added: blocks WD-fay0
- 2026-09-24T14:39:53Z dep_removed: no_longer_blocks WD-651z
- 2026-09-25T03:35:35Z status: open -> in_progress
- 2026-09-25T03:35:35Z auto-follows: linked to predecessor WD-e4r7
- 2026-09-25T03:35:35Z claimed by dev-WD-rous

## Links
- Parent: [[WD-3nod]]
- Blocks: [[WD-dmf2]], [[WD-fay0]]
- Follows: [[WD-e4r7]]

## Comments
