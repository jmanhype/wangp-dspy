---
id: WD-fay0
title: "E2e: verified Maestro parity evidence"
status: open
priority: 1
type: feature
labels: [capstone, e2e, evidence]
parent: WD-3nod
created_at: 2026-09-24T14:14:09Z
created_by: speed
updated_at: 2026-09-24T16:17:34Z
content_hash: "sha256:b14efe25f9207ee7ef7b81611e562bc262040fa426f7fa2be9b276ba43e7ccfb"
blocked_by: [WD-m0r5, WD-rous, WD-2gyw, WD-bxhc, WD-cpow, WD-r81u, WD-dmf2, WD-0zj8, WD-e4r7]
was_blocked_by: [WD-651z]
---

## Description
## USER INTENT
This capstone converts the Maestro-parity programme from a set of lane claims into one independently reviewable completion record. It must prove that no targeted capability remains merely planned and that every terminal disposition is backed by an exact bundle that can be retrieved and checked without trusting a summary.

Observed lane coverage is: video `WD-2gyw`; image `WD-m0r5`; music `WD-rous`; voice and character `WD-bxhc`; SFX/audio-post `WD-cpow`; finishing `WD-r81u`; director/editor composition `WD-dmf2`; and first-run clean-machine install `WD-0zj8`. The accepted `WD-651z` contract/checker is the common authority. The capstone does not create a second evidence standard or broaden any lane verdict.

Every targeted video, image, music, voice, character, SFX, finishing, and director/editor row/cell must end as `host_run_verified` from a real authorized bundle under that lane's `datasets/runs/maestro-parity/<STORY_ID>/` root, or as `unsupported_on_this_hardware` with recorded infeasibility evidence. The first-run proof must likewise be a real generated-install outcome, not a plan-only demonstration. No row, cell, bundle, failure, or operator disposition may be silently dropped.

## REQUIRED OPERATOR INPUTS — NOT YET PROVIDED
- This story gives no GPU, render-host, remote-host, or model-download authorization and cannot reuse lane authorization outside its verbatim recorded scope.
- Any additional lane rerun needed to close a gap remains blocked until the operator supplies exact per-batch scope, timestamp, approver, command boundary, host/model identity, download approval where applicable, and source/rights boundary.
- Final operator/reviewer approval of the consolidated disposition index has not been given. `unsupported_on_this_hardware` and `host_run_verified` both require an explicit approved disposition; missing input is blocked and is neither infeasibility nor success.

## No-Fabrication Rule
A consolidated index, lane summary, matrix edit, checker transcript, fixture, deterministic plan, dry-run, unit test, vendor claim, or absent attempt is not generation evidence. `host_run_verified` requires actual emitted bytes from an authorized lane run and a bundle that passes the accepted WD-651z checker. `unsupported_on_this_hardware` requires the originating lane's recorded authorized refusal/failed attempt or measurable requirement-versus-capacity proof. The capstone may link and re-run verification; it may not infer, upgrade, normalize, copy, or rewrite a lane verdict.

## OUT OF SCOPE
- Authorizing or performing generation, downloads, remote execution, training, publication, a tag, or a new provider account.
- Adding capability rows, weakening a gate, changing the canonical evidence contract/checker semantics, or replacing lane-specific provenance.
- Reusing one lane's artifact as another lane's evidence or copying lane media into the capstone bundle.
- Editing dependencies, title, priority, parent, or lane ownership; silently dropping an unresolved row/cell.
- Changing queue admission, renderer policy, preflight, wiring, or `scripts/run_film.py` semantics.

## DIFF BUDGET
- About 2 files and under 200 authored changed LOC, limited to the consolidated index/gate record under `datasets/runs/maestro-parity/WD-fay0/` and narrowly targeted verification tests if needed for index consistency.
- Lane bundles and matrices remain owned by their lane stories. Do not copy media or model weights into this bundle; record aggregate index size and keep it under 16 MiB.

## Boundary Map
PRODUCES:
- datasets/runs/maestro-parity/WD-fay0/ -> checker-validated consolidated parity evidence index
  spec: immutable row/bundle map covering every lane transition and infeasible disposition, with story ID, row/cell identity, exact relative bundle path and hash, disposition, operator/reviewer decision, checker command/result, and standing-gate result.
- datasets/runs/maestro-parity/WD-fay0/ -> capstone gate transcript
  event: preserve exact checker/install/lint/test/release/protected-file command identities and output tails so every index verdict can be independently replayed.

CONSUMES:
- WD-651z: docs/maestro-parity-evidence-contract.md -> canonical `wangp-dspy.maestro-parity-evidence/v1` semantics
  source: accepted field, hash, authorization, gate, and reviewer authority; do not duplicate or weaken it.
- WD-651z: scripts/verify_maestro_parity.py -> `verify_bundle(bundle: Path) -> VerificationReport`
  event: invoke the accepted checker on every bundle named by the index and require its observed pass/fail result.
- WD-2gyw: datasets/runs/maestro-parity/WD-2gyw/ -> video lane evidence bundles and dispositions
  source: only accepted lane outcomes and their exact recorded matrices/artifacts.
- WD-m0r5: datasets/runs/maestro-parity/WD-m0r5/ -> image lane evidence bundles and dispositions
  source: only accepted lane outcomes and their exact recorded matrices/artifacts.
- WD-rous: datasets/runs/maestro-parity/WD-rous/ -> music lane evidence bundles and dispositions
  source: only accepted lane outcomes and their exact recorded matrices/artifacts.
- WD-bxhc: datasets/runs/maestro-parity/WD-bxhc/ -> voice and character lane evidence bundles and dispositions
  source: only accepted lane outcomes and their exact recorded matrices/artifacts.
- WD-cpow: datasets/runs/maestro-parity/WD-cpow/ -> SFX/audio-post lane evidence bundles and dispositions
  source: only accepted lane outcomes and their exact recorded matrices/artifacts.
- WD-r81u: datasets/runs/maestro-parity/WD-r81u/ -> finishing lane evidence bundles and dispositions
  source: only accepted lane outcomes and their exact recorded matrices/artifacts.
- WD-dmf2: datasets/runs/maestro-parity/WD-dmf2/ -> director/editor lane evidence bundles and dispositions
  source: only accepted lane outcomes and their exact recorded matrices/artifacts.
- WD-0zj8: datasets/runs/maestro-parity/WD-0zj8/ -> first-run clean-machine install bundle and disposition
  source: only the accepted install outcome and its exact recorded artifact/provenance.
- (existing): docs/video-capabilities.md, docs/image-capabilities.md, docs/music-capabilities.md, docs/voice-capabilities.md, docs/character-capabilities.md, docs/sfx-capabilities.md, docs/finishing-capabilities.md, docs/director-capabilities.md, docs/install.md, and README.md -> final row/cell and first-run claims
  source: exact identities and public claims that the index must account for.
- (operator): explicit final disposition approval and any still-missing lane authorization -> verbatim approval/blocked records
  source: future operator input; not supplied by story creation.

## Story Acceptance Criteria
1. [State] Given the accepted final lane matrices and the programme's original targeted row/cell inventory, when the capstone compares video, image, music, voice, character, SFX, finishing, director/editor, and first-run claims, then zero targeted entries remain `planned` or unresolved: each retained entry maps to exactly one operator-approved `host_run_verified` bundle or `unsupported_on_this_hardware` infeasibility record, while any dropped, blank, duplicated, unauthorized, or missing entry fails.
2. [State] Given every lane bundle referenced by the consolidated index, when the accepted WD-651z checker is invoked on each bundle, then every invocation exits zero with `PASS`, including at least one real authorized generation bundle demonstrated for every generation lane; any missing bundle, skipped lane, fixture substitution, non-zero checker result, or unsupported disposition represented as generation evidence fails.
3. [State] Given the accepted WD-0zj8 command and the exact operator inputs recorded by that lane, when the documented command runs from a pristine disposable environment with isolated `HOME` and temporary checkout/cache directories, then it installs without hand configuration and emits actual generated artifact bytes with a checker-passing bundle; a plan, refusal, fixture, or pre-existing checkout is not capstone completion.
4. [State] Given the merged capstone head, when the standing gates run, then `pvg lint --backlog` reports 0 errors and 0 review findings, the full suite emits parsed JUnit `errors=0` and `failures=0`, `wgp release verify` reports `release=ready` and `tag_created=false`, and the protected engine files are unchanged from `40f8c2b373dec1c84ca5a596c821b740934af6fb` unless an independently accepted story required and recorded an exception.
5. [State] Given all lane outcomes and gate transcripts, when the consolidated evidence index is generated, then it accounts for every lane bundle and every flipped or infeasible row/cell with exact relative paths, hashes, disposition, authorization/reviewer status, and checker result, and checker validation of the referenced bundle set succeeds with no stale, missing, duplicate, or unapproved entry.

## Testing Requirements
- Verify all observed blockers are accepted before execution; do not restore or remove dependency edges. Record the direct and transitive edge list actually observed at execution.
- Build a machine-readable before/after inventory from the lane stories and final matrices; prove zero targeted `planned` entries remain, no entry was dropped, and each disposition resolves to exactly one accepted lane record.
- Run the accepted WD-651z checker separately on every bundle referenced by the index; retain command argv, exit status, output, and bundle hash. At least one real bundle per generation lane must pass.
- Re-run or cite the accepted WD-0zj8 clean-machine command from a disposable environment; prove isolated state, resolved commit, no manual configuration, actual artifact hash/metadata, and checker pass.
- Validate the index mechanically: exact lane/row/bundle coverage, relative contained paths, no duplicate or stale reference, disposition consistency with lane evidence, and explicit reviewer/operator status.
- Standing gates: `pvg lint --backlog` with 0 errors and 0 review findings; `uv run --frozen --extra dev pytest -q --junitxml=/tmp/WD-fay0-full.xml` with parsed `errors=0`/`failures=0`; `uv run --frozen --extra dev wgp release verify` with `release=ready`/`tag_created=false`; and protected-file parity against `40f8c2b373dec1c84ca5a596c821b740934af6fb` unless an accepted exception is recorded.
- Also run `git diff --check`, record index/bundle hashes and aggregate sizes, and record that no lane media, model weight, credential, or disposable checkout was copied or committed.

## Delivery Requirements
- Paste the observed dependency/acceptance list, before/after row inventory, complete lane-to-bundle checker table, clean-machine command and artifact proof, index tree/hash, operator disposition status, lint output, parsed JUnit counters, release fields, protected-file parity, and `git diff --check`.
- If any required lane input or final disposition approval remains absent, deliver the exact typed blocker and stop; do not convert it into infeasibility, success, or a reduced capstone claim.

## MANDATORY SKILLS
- pvg

## nd_contract
status: new

### evidence
- Authored on 2026-09-24 from the accepted WD-651z checker/contract, WD-0zj8 install proof, and the WD-2gyw/WD-m0r5 lane templates plus the other observed lane bodies; no GPU/download authorization or final operator disposition exists yet.

### proof
- [ ] Pending all lane outcomes, explicit operator disposition approval, checker/install evidence, and standing gates.

## Acceptance Criteria


## Design


## Notes
## MANDATORY SKILLS
- pvg

Observable outcome: the capstone returns a consolidated parity-evidence index and gate verdicts under datasets/runs/maestro-parity/WD-fay0/ so a reviewer can retrieve every required artifact and failure reason without relabeling missing evidence as success.

## History
- 2026-09-24T14:14:09Z dep_added: blocked_by WD-m0r5
- 2026-09-24T14:14:09Z dep_added: blocked_by WD-rous
- 2026-09-24T14:14:09Z dep_added: blocked_by WD-2gyw
- 2026-09-24T14:14:10Z dep_added: blocked_by WD-bxhc
- 2026-09-24T14:14:10Z dep_added: blocked_by WD-cpow
- 2026-09-24T14:14:10Z dep_added: blocked_by WD-r81u
- 2026-09-24T14:14:10Z dep_added: blocked_by WD-dmf2
- 2026-09-24T14:14:10Z dep_added: blocked_by WD-651z
- 2026-09-24T14:14:10Z dep_added: blocked_by WD-0zj8
- 2026-09-24T16:02:51Z dep_removed: was_blocked_by WD-651z
- 2026-09-24T21:11:26Z dep_added: blocked_by WD-e4r7

## Links
- Parent: [[WD-3nod]]
- Blocked by: [[WD-m0r5]], [[WD-rous]], [[WD-2gyw]], [[WD-bxhc]], [[WD-cpow]], [[WD-r81u]], [[WD-dmf2]], [[WD-0zj8]], [[WD-e4r7]]
- Was blocked by: [[WD-651z]]

## Comments
