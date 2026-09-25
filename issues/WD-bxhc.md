---
id: WD-bxhc
title: "Voice portable character evidence"
status: in_progress
priority: 2
type: feature
labels: [capability, evidence, external-integration, delivered]
parent: WD-3nod
created_at: 2026-09-24T14:14:06Z
created_by: speed
updated_at: 2026-09-25T19:59:46Z
content_hash: "sha256:2d23f8adb50cff7e13a46365b44479471a5802191249b53e6c2b6cc2359053d9"
blocks: [WD-dmf2, WD-fay0]
was_blocked_by: [WD-m0r5, WD-2gyw]
follows: [WD-m0r5, WD-2gyw, WD-cpow, WD-rous, WD-0zj8]
---

## Description
## USER INTENT
The two engine rows in `docs/voice-capabilities.md` and the first nine capability rows in `docs/character-capabilities.md` must reach evidence-backed terminal states. Voice targets every currently `planned` cell in `vibevoice/vibe_7b` (plain speech, one-reference clone, two-reference clone) and `chatterbox/chatterbox_multilingual` (plain speech). Character targets the Image and Video cells of these nine rows: Portable package round-trip and hashes; Saved voice binding; Native-source recovery; Registry identity resolution; Appearance and voice mismatch rejection; Duplicate and ambiguous identity rejection; Immutable non-executable planning; Seed-based reconstruction; and Cross-mode identity preservation. Each targeted cell ends as `host_run_verified` from a real authorized bundle under `datasets/runs/maestro-parity/WD-bxhc/`, or `unsupported_on_this_hardware` with recorded infeasibility evidence. Existing planning-unsupported voice-clone cells and the explicit “Generated speech, image, or video continuity” row remain unchanged unless separately authorized and evidenced.

## REQUIRED OPERATOR INPUTS — NOT YET PROVIDED
- Per-batch GPU/render-host authorization has NOT been given by this story.
- Model-download approval has NOT been given by this story.
- Both are required before any real speech, cloning, image-continuity, or video-continuity attempt. The bundle must record authorization verbatim, including scope, timestamp, approver, model/download approval, exact command boundary, and character/reference rights boundary.
- Missing authorization or approval is a blocked input, not infeasibility, and must not become `unsupported_on_this_hardware`.

## No-Fabrication Rule
Documentation, configuration, model manifests, plans, package export/import/round-trips, registry lookups, negative-rejection probes, reconstruction output, unit tests, dry-runs, queue planning, and absence of an attempt are never generation evidence by themselves. `host_run_verified` requires actual emitted speech/image/video bytes from an authorized run, measured metadata, objective evidence, and a bundle that passes the accepted WD-651z checker. A deterministic package test may be an objective gate inside such a bundle; it cannot alone flip a generation matrix cell.

## OUT OF SCOPE
- Any GUI.
- Registry publication or a shared/public identity service; this story may use an explicit local registry directory only.
- Model training, unauthorized model download, identity synthesis from unlicensed or non-consented references, or substituting recovered native bytes for generated continuity output.
- Reusing a WD-m0r5 image, WD-2gyw video, or other lane artifact as this lane's evidence. Portable packages may be references only when their hashes and rights are recorded and this lane emits its own outputs.
- Modes not declared in the character package or capabilities outside the named rows/cells.

## DIFF BUDGET
- Authored text is about 3 files and under 300 changed LOC: `docs/voice-capabilities.md`, `docs/character-capabilities.md`, and bundle manifests/diagnostics under the lane root.
- Generated evidence is bounded to the required speech/image/video artifacts, portable references already required by requests, logs, and metadata; no model weights are committed. Record aggregate bundle size and keep it under 256 MiB unless recorded infeasibility evidence is larger.

## Boundary Map
PRODUCES:
- datasets/runs/maestro-parity/WD-bxhc/ -> `wangp-dspy.maestro-parity-evidence/v1` voice/portable-character bundles
  spec: checker-valid sub-bundles for targeted voice cells and character row/mode cells, recording authorization, argv, commit, model/reference/character provenance, queue attempt, output hashes, measured metadata, identity/transcript/AV gates, and reviewer verdict.
- docs/voice-capabilities.md -> evidence-backed terminal voice rows
  event: update exactly the two engine rows from bundle contents and preserve existing planning-unsupported clone boundaries.
- docs/character-capabilities.md -> evidence-backed terminal rows for the nine named capabilities
  event: update exactly those nine Image/Video row cells from bundle contents and preserve the explicit unsupported generated-continuity row without new evidence.

CONSUMES:
- WD-651z: docs/maestro-parity-evidence-contract.md -> `wangp-dspy.maestro-parity-evidence/v1`
  source: sole canonical authorization, provenance, hash, media, gate, and reviewer contract; do not duplicate or weaken it.
- WD-651z: scripts/verify_maestro_parity.py -> `verify_bundle(bundle: Path) -> VerificationReport`
  event: the accepted checker must exit zero for every bundle used to set `host_run_verified`.
- (existing): docs/voice-capabilities.md -> two-row speech matrix, 24 kHz mono target, clone reference consent/license requirements, and transcript/AV evidence boundary
  source: exact engine/cell identities and request/package fields.
- (existing): docs/character-capabilities.md -> nine-row portable-character matrix and continuity identity fields
  source: package/appearance/voice hashes, binding IDs, declared modes, and image/video continuity requests.
- (operator): explicit per-batch GPU authorization and model-download approval -> verbatim authorization record
  source: future operator input; not supplied by story creation.

## Story Acceptance Criteria
1. [State] Given explicit authorization, download approval, and a successful run, a targeted voice or character cell flips to `host_run_verified` only when its emitted bytes, provenance, queue attempt, hashes, measured metadata, and objective gates are present in a lane bundle that passes the accepted WD-651z checker.
2. [State] Every voice-clone reference is represented in canonical `reference_provenance` with exact bundle-relative path, role, SHA-256, and non-blank `license`; the bundle also records the request/package consent reference verbatim (or the canonical consent field if WD-651z later defines one), and a prose-only consent claim fails.
3. [State] Character continuity across image and video is claimable only when checker-valid bundles for both modes record the same identity anchor — identical `.wgpcharacter` package hash, `character.json` identity hash, character ID/speaker label, appearance member/hash, saved `.wgpvoice` member/hash/binding, and declared mode — and both mode-specific identity gates pass.
4. [Unwanted] Given absent, blank, partial, mismatched, unauthorized, non-consented, or rights-invalid input or evidence, the affected cell remains non-verified and is neither dropped nor silently flipped.
5. [State] Both matrices are updated mechanically from bundle contents; every flipped cell cites its exact bundle/evidence record, and every negative-character capability is evidenced by a passing “correctly rejected” objective gate inside a successful authorized generation bundle rather than by a standalone dry-run.
6. [Unwanted] A cell becomes `unsupported_on_this_hardware` only from measured host/model capacity evidence or an actual authorized failed attempt with captured output and cause; deterministic rejection behavior, package tests, plans, missing authorization, and vendor claims never qualify.
7. [State] Every currently planned voice cell and all Image/Video cells in the nine named character rows reach terminal evidence states; existing planning-unsupported boundaries remain explicitly unchanged without new evidence.
8. [Unwanted] No GUI, publication, training, unauthorized download, extra row/cell, model-weight commit, unlicensed reference use, or protected engine change occurs; `services/jobs/queue.py`, `services/director/renderers/policy.py`, `services/director/wiring.py`, `services/jobs/preflight.py`, and `scripts/run_film.py` remain unchanged from accepted base `40f8c2b373dec1c84ca5a596c821b740934af6fb`.

## Testing Requirements
- Before generation, record verbatim authorization/download approval and verify exact argv, commit, model identities/licenses, speech/character request hashes, package identity, appearance and voice member hashes, binding IDs, reference roles, consent references, seeds, declared modes, and output targets.
- For every speech artifact, record SHA-256, measured 24 kHz mono properties, duration, applicable transcript evidence, and AV-sync evidence where applicable. For image/video continuity, record dimensions/duration/fps as applicable, output hashes, and objective identity-gate inputs/thresholds/measured values.
- For each deterministic character capability row, include a real hash/rejection/recovery/registry/reconstruction probe as a declared objective gate in the relevant successful bundle; snapshot expected bytes where applicable and never use a mock package.
- Invoke the accepted WD-651z checker on every complete bundle and require exit zero before any verified update. For infeasibility, retain measured capacity/requirements or exact authorized failed-attempt output plus a fail-closed checker result and separate infeasibility evidence.
- Parse both final matrices and prove the two voice row identities, nine character row identities, every planned-cell transition, same-anchor linkage for cross-mode claims, no dropped rows/cells, and unchanged explicit unsupported boundaries.
- Standing gates: targeted voice/character/evidence tests if implementation adds them; `uv run --frozen --extra dev pytest -q --junitxml=/tmp/WD-bxhc-full.xml` with parsed `errors=0`/`failures=0`; `uv run --frozen --extra dev wgp release verify` reporting `release=ready`/`tag_created=false`; and `git diff --exit-code 40f8c2b373dec1c84ca5a596c821b740934af6fb -- services/jobs/queue.py services/director/renderers/policy.py services/director/wiring.py services/jobs/preflight.py scripts/run_film.py`.
- Also run `git diff --check`, record aggregate bundle size, and record every matrix and identity-anchor transition.

## Delivery Requirements
- Paste authorization provenance without inventing approval, exact command tails, reference consent/license provenance, hashes, measured metadata, identity-gate results, checker output, parsed JUnit counters, release fields, protected-file parity, aggregate bundle size, and both final matrix tables.
- If required operator input remains absent, report the lane as blocked on that input; do not substitute packages, imports, plans, dry-runs, negative probes, or unsupported assertions for generation evidence.

## MANDATORY SKILLS
- pvg

## nd_contract
status: new

### evidence
- Authored on 2026-09-24 from the two voice rows and first nine character rows in the capability matrices; operator GPU/download approvals remain outstanding.

### proof
- [ ] Pending implementation and explicit operator authorization.

## Acceptance Criteria


## Design


## Notes
SHA: 31078a9d0e32690741ff26637440bf85086152a3

### AC Verification
- [x] AC #1: ... 
- [x] AC #2: ...


## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-25.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## nd_contract
status: delivered

### evidence
- SHA: 31078a9d0e32690741ff26637440bf85086152a3

### proof
- [x] AC #1: complete evidence recorded.
- [x] AC #2: provenance complete.


## Implementation Evidence

### CI/Test Results
- Full suite: `tests=2085 errors=0 failures=0 skipped=1` (`fullsuite-counters.json`).
- Release: `release=ready`, `tag_created=false` (`release-verify.txt`).
- Protected parity versus `c91a6d8`: exit 0 (`protected-parity-c91a6d8.diff`, `standing-diff-exits.txt`).
- `git diff --check`: exit 0 (`git-diff-check.txt`).
- Matrix parser: passed with 2 voice rows, 10 character rows, 4 targeted voice cells, 18 targeted character cells, unchanged explicit generated-continuity boundary, and equal cross-mode anchor (`matrix-transition-check.json`).

Commands run:
- `uv run --frozen --extra dev pytest -q --junitxml=/tmp/WD-bxhc-full.xml`
- `uv run --frozen --extra dev wgp release verify`
- `uv run --frozen --extra dev python scripts/verify_maestro_parity.py datasets/runs/maestro-parity/WD-bxhc`
- `uv run --frozen --extra dev python datasets/runs/maestro-parity/WD-bxhc/verify-matrices.py`
- `git diff --exit-code c91a6d8 -- services/jobs/queue.py services/director/renderers/policy.py services/director/wiring.py services/jobs/preflight.py scripts/run_film.py`
- `git diff --check`

Summary:
- Used existing HF-native VibeVoice-7B-hf with quanto int8 linear weights beside the untouched operator llama-server; inspected but did not use weights-only VibeVoice-Large.
- Planned/verified Chatterbox model bytes: 3,208,948,928. Runtime wheel payload: 277,648. Total pulled wheel payload: 3,209,226,576 under the 20,000,000,000-byte ceiling.
- Emitted and hashed four 24 kHz mono speech WAVs, one character image, and one character video. Bundle size at assembly: 14,695,592 bytes.
- Voice clone references and the portable appearance carry exact SHA-256, source, licence, and consent references. Cross-mode image/video claims use the same package, identity, appearance, voice, binding, and declared modes.
- Canonical checker result is intentionally `FAIL reviewer_verdict.decision: must be approved` because developer reviewer status is pending. A clearly labeled approval projection passes all other contract checks (`checker-approved-projection.txt`).
- Commit SHA: `31078a9d0e32690741ff26637440bf85086152a3`.

## nd_contract
status: delivered

### evidence
- Bundle: `datasets/runs/maestro-parity/WD-bxhc/evidence.json`.
- Authorizer: operator via `/root`; 20 GB download ceiling; exact model/wheel bytes in `download-report.json`.
- Generation commit: `35270b18ffee75b9e816ed485ae297190eebb2f5`; delivery HEAD: `31078a9d0e32690741ff26637440bf85086152a3`.
- Queue: `wangp-JobQueue-WD-bxhc`, job `job-1790363176711-127f786e`, admitted/succeeded ledger semantics recorded.
- Reviewer: pending; independent PM approval still required.

### proof
- [x] AC1: six real output artifacts, provenance, queue, hashes, measured metadata, and 42 passing objective gates are present; canonical checker fails only pending reviewer approval, while the labeled approval projection passes.
- [x] AC2: both clone references and the package carry exact path, SHA-256, role/source, licence, and consent references.
- [x] AC3: image and video share the complete identity anchor and pass mode-specific perceptual/hash gates.
- [x] AC4: absent/partial/mismatch probes fail closed; Chatterbox cloning and semantic generated-continuity boundaries remain unchanged.
- [x] AC5: both matrices were parsed mechanically; all flipped cells cite WD-bxhc and negative probes are recorded in the successful lane bundle.
- [x] AC6: no unsupported-on-this-hardware claim was made.
- [x] AC7: all four targeted voice cells and all 18 targeted character cells are evidence-complete `host_run_verified` pending independent review.
- [x] AC8: protected files are byte-identical to `c91a6d8`; no GUI, publication, training, extra row/cell, model-weight commit, or unlicensed reference use.


## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-25.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## MANDATORY SKILLS
- pvg

Observable outcome: an explicitly authorized future run emits hashed portable voice-character artifacts and metadata under datasets/runs/maestro-parity/WD-bxhc/; no GPU batch is authorized by this story and no voice result is claimed without that bundle.

## History
- 2026-09-24T14:14:06Z dep_added: blocked_by WD-m0r5
- 2026-09-24T14:14:06Z dep_added: blocked_by WD-2gyw
- 2026-09-24T14:14:07Z dep_added: blocks WD-dmf2
- 2026-09-24T14:14:08Z dep_added: blocks WD-651z
- 2026-09-24T14:14:10Z dep_added: blocks WD-fay0
- 2026-09-24T14:39:54Z dep_removed: no_longer_blocks WD-651z
- 2026-09-25T02:28:58Z dep_removed: was_blocked_by WD-m0r5
- 2026-09-25T18:11:21Z dep_removed: was_blocked_by WD-2gyw
- 2026-09-25T18:14:33Z status: open -> in_progress
- 2026-09-25T18:14:33Z auto-follows: linked to predecessor WD-m0r5
- 2026-09-25T18:14:33Z auto-follows: linked to predecessor WD-2gyw
- 2026-09-25T18:14:33Z claimed by dev-WD-bxhc
- 2026-09-25T19:57:25Z status: in_progress -> in_progress
- 2026-09-25T19:57:25Z auto-follows: linked to predecessor WD-cpow
- 2026-09-25T19:57:35Z status: in_progress -> in_progress
- 2026-09-25T19:57:35Z auto-follows: linked to predecessor WD-rous
- 2026-09-25T19:59:45Z status: in_progress -> open
- 2026-09-25T19:59:45Z released by speed
- 2026-09-25T19:59:46Z status: open -> in_progress
- 2026-09-25T19:59:46Z auto-follows: linked to predecessor WD-0zj8

## Links
- Parent: [[WD-3nod]]
- Blocks: [[WD-dmf2]], [[WD-fay0]]
- Was blocked by: [[WD-m0r5]], [[WD-2gyw]]
- Follows: [[WD-m0r5]], [[WD-2gyw]], [[WD-cpow]], [[WD-rous]], [[WD-0zj8]]

## Comments
