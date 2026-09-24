---
id: WD-cpow
title: "SFX audio-post evidence"
status: open
priority: 2
type: feature
labels: [capability, evidence, external-integration]
parent: WD-3nod
created_at: 2026-09-24T14:14:06Z
created_by: speed
updated_at: 2026-09-24T15:35:51Z
content_hash: "sha256:a81371371e1bc499b1b3b2771a6261cb33c19e8735447350dbd0e7f7cafebc2f"
blocks: [WD-fay0]
---

## Description
## USER INTENT
The three engine/mode rows in `docs/sfx-capabilities.md` — `stable_audio/sound_effect`, `vibevoice/revoice`, and `deepfilternet/refinement` — must reach evidence-backed terminal states. Every currently `planned` diagonal cell (Sound effect, Revoice, and Refinement respectively) ends as either `host_run_verified` from a real authorized bundle under `datasets/runs/maestro-parity/WD-cpow/`, or `unsupported_on_this_hardware` with recorded infeasibility evidence. Pre-existing planning-unsupported off-diagonal cells remain unchanged; they are not hardware verdicts.

## REQUIRED OPERATOR INPUTS — NOT YET PROVIDED
- Per-batch GPU/render-host authorization has NOT been given by this story.
- Model-download approval has NOT been given by this story.
- Both are required before any real sound-effect, revoice, or refinement run. The bundle must record the authorization verbatim, including scope, timestamp, approver, model/download approval, exact command boundary, and source/target rights.
- Missing authorization or approval is a blocked input, not infeasibility, and must not be converted to `unsupported_on_this_hardware`.

## No-Fabrication Rule
Documentation, configuration, model manifests, normalized settings, plans, unit tests, dry-runs, queue planning, reconstruction output, absence of an attempt, and prose such as “audio preserved” or “video preserved” are never generation or preservation evidence. `host_run_verified` requires actual emitted bytes from an authorized run plus recorded hashes and measured metadata. Preservation claims require matching recorded source/reference/output artifact or stream hashes, not narrative.

## OUT OF SCOPE
- Any GUI.
- Registry publication.
- New visual transformation, video generation, cropping, scaling, retiming, or re-encoding beyond the immutable source contract.
- Model training or any download beyond separately recorded approval.
- Capabilities outside the three named rows or reuse of another lane's output as this lane's evidence.

## DIFF BUDGET
- Authored text is about 2 files and under 250 changed LOC: `docs/sfx-capabilities.md` plus bundle manifests/diagnostics under the lane root.
- Generated evidence is bounded to one required artifact per planned cell plus source/reference material, logs, and metadata; no model weights are committed. Record aggregate bundle size and keep it under 128 MiB unless recorded infeasibility evidence is larger.

## Boundary Map
PRODUCES:
- datasets/runs/maestro-parity/WD-cpow/ -> `wangp-dspy.maestro-parity-evidence/v1` SFX/audio-post bundles
  spec: one checker-valid sub-bundle per planned cell, with authorization, argv, commit, model/source/target provenance, queue attempt, hashes, measured media metadata, preservation gates, and reviewer verdict.
- docs/sfx-capabilities.md -> evidence-backed terminal matrix rows
  event: update exactly the three named rows from bundle contents, cite each bundle record, and preserve planning-unsupported off-diagonal boundaries.

CONSUMES:
- WD-651z: docs/maestro-parity-evidence-contract.md -> `wangp-dspy.maestro-parity-evidence/v1`
  source: sole canonical bundle field/hash/verdict contract; this lane must not duplicate or weaken it.
- WD-651z: scripts/verify_maestro_parity.py -> `verify_bundle(bundle: Path) -> VerificationReport`
  event: the accepted checker must exit zero for every bundle used to set `host_run_verified`.
- (existing): docs/sfx-capabilities.md -> current three-row matrix and immutable source contract
  source: exact engine/cell identities, 48 kHz WAV target, MP4 outputs, and held-fixed video requirement.
- (operator): explicit per-batch GPU authorization and model-download approval -> verbatim authorization record
  source: future operator input; not supplied by story creation.

## Story Acceptance Criteria
1. [State] Given explicit authorization, download approval, and a successful run, a planned SFX/audio-post cell flips to `host_run_verified` only when its emitted WAV or MP4 bytes, provenance, queue attempt, hashes, measured metadata, and objective gates are present in a lane bundle that passes the accepted WD-651z checker.
2. [Unwanted] Given absent, blank, partial, mismatched, or unauthorized input or evidence, the affected cell remains non-verified and is neither dropped nor silently flipped.
3. [State] `docs/sfx-capabilities.md` is updated mechanically from bundle contents, and every flipped cell cites the exact bundle/evidence record from which its verdict came.
4. [State] Every successful bundle records SHA-256 for all source, reference, target-voice, and output artifacts; measured stream layout/duration; model identity/source/hash or immutable version and license; objective-gate inputs/threshold/measured value; and reviewer approval while satisfying the complete canonical contract.
5. [Unwanted] Any audio-preservation or held-fixed-video claim without recorded before/after artifact or stream hashes and a passing objective comparison fails; prose, filenames, settings, and planned `video_bytes_changed=false` values never verify it.
6. [State] All three planned diagonal cells reach terminal evidence states; infeasible cells use recorded measured evidence, and planning-unsupported off-diagonal cells remain explicitly unchanged without new evidence.
7. [Unwanted] No GUI, registry publication, training, unauthorized download, extra row/cell, model-weight commit, visual mutation, or protected engine change occurs; `services/jobs/queue.py`, `services/director/renderers/policy.py`, `services/director/wiring.py`, `services/jobs/preflight.py`, and `scripts/run_film.py` remain unchanged from accepted base `40f8c2b373dec1c84ca5a596c821b740934af6fb`.

## Testing Requirements
- Before generation, record verbatim authorization/download approval and verify exact argv, commit, model identities/licenses, source hashes, target-voice rights, requested controls, seeds, and output targets.
- For sound-effect output, measure and record WAV format, channels, sample rate, and duration. For MP4 revoice/refinement, measure and record video/audio stream properties and perform the declared before/after preservation comparison from recorded hashes.
- Invoke the accepted WD-651z checker on every complete bundle and require exit zero before any verified update. For infeasibility, retain measured capacity/requirements or exact authorized failed-attempt output plus a fail-closed checker result and separate infeasibility evidence.
- Parse the final matrix and prove all three row identities, planned-cell transitions, preservation citations, no dropped cells, and unchanged off-diagonal unsupported boundaries.
- Standing gates: targeted SFX/evidence tests if implementation adds them; `uv run --frozen --extra dev pytest -q --junitxml=/tmp/WD-cpow-full.xml` with parsed `errors=0`/`failures=0`; `uv run --frozen --extra dev wgp release verify` reporting `release=ready`/`tag_created=false`; and `git diff --exit-code 40f8c2b373dec1c84ca5a596c821b740934af6fb -- services/jobs/queue.py services/director/renderers/policy.py services/director/wiring.py services/jobs/preflight.py scripts/run_film.py`.
- Also run `git diff --check`, record aggregate bundle size, and record every matrix and preservation-gate transition.

## Delivery Requirements
- Paste authorization provenance without inventing approval, exact command tails, measured stream metadata, before/after hashes, checker output, parsed JUnit counters, release fields, protected-file parity, aggregate bundle size, and the final three-row matrix table.
- If required operator input remains absent, report the lane as blocked on that input; do not substitute plans, dry-runs, reconstruction output, preservation prose, or unsupported assertions for generation evidence.

## MANDATORY SKILLS
- pvg

## nd_contract
status: new

### evidence
- Authored on 2026-09-24 from the three engine/mode rows in `docs/sfx-capabilities.md`; operator GPU/download approvals remain outstanding.

### proof
- [ ] Pending implementation and explicit operator authorization.

## Acceptance Criteria


## Design


## Notes
## MANDATORY SKILLS
- pvg

Observable outcome: an explicitly authorized future run emits hashed SFX/audio-post artifacts and measured metadata under datasets/runs/maestro-parity/WD-cpow/; no GPU batch is authorized by this story and no audio result is claimed without that bundle.

## History
- 2026-09-24T14:14:08Z dep_added: blocks WD-651z
- 2026-09-24T14:14:10Z dep_added: blocks WD-fay0
- 2026-09-24T14:39:54Z dep_removed: no_longer_blocks WD-651z

## Links
- Parent: [[WD-3nod]]
- Blocks: [[WD-fay0]]

## Comments
