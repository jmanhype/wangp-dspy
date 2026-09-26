---
id: WD-fay0
title: "E2e: verified Maestro parity evidence"
status: closed
priority: 1
type: feature
labels: [capstone, e2e, evidence, accepted]
parent: WD-3nod
created_at: 2026-09-24T14:14:09Z
created_by: speed
updated_at: 2026-09-26T01:18:10Z
content_hash: "sha256:3e510e6ff01ddf0b926b80d31bec810132fd1a44f2678c5c48bdf27b81f3e789"
was_blocked_by: [WD-651z, WD-m0r5, WD-e4r7, WD-0zj8, WD-rous, WD-cpow, WD-2gyw, WD-r81u, WD-bxhc, WD-dmf2, WD-r4n8]
assignee: dev-WD-fay0
follows: [WD-651z, WD-m0r5, WD-e4r7, WD-0zj8, WD-rous, WD-cpow, WD-2gyw, WD-r81u, WD-bxhc, WD-dmf2]
closed_at: 2026-09-26T01:18:10Z
close_reason: "Accepted as a DELIVERED DISPOSITION INDEX only, not programme completion. Independently verified head/diff, lane checker outcomes, 208-cell disposition totals, no cross-lane edits, honest AC assessment, 61 fail-closed tests, and standing gates. Remaining scope: 120 matrix cells planned, 6 await operator consent, WD-dmf2 director gates fail structurally, and WD-0zj8 clean-machine generated-artifact half remains blocked."
led_to: [WD-r4n8, WD-i7qs]
blocked_by: [WD-i7qs, WD-r4n8, WD-14ej]
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


## nd_contract
status: accepted

### evidence
- PM closeout applied via pvg story accept on 2026-09-25.

### proof
- [x] Story closed after accepted label was applied.


## nd_contract
status: delivered

### evidence
- Authoritative delivery record: commit 1dbdd7977560c74a31a05986413b5671880b8031 is pushed to origin/story/WD-fay0; evidence-index.md/.json, gate-transcript.md, and validate_index.py are committed. The detailed Implementation Evidence block above remains part of this contract.

### proof
- [x] AC #1: NOT MET — 120 planned and 6 consent-pending cells remain.
- [x] AC #2: NOT MET — WD-0zj8 and WD-dmf2 checker exits are 1.
- [x] AC #3: NOT MET — clean-machine generated-artifact half is blocked on operator host/model inputs.
- [x] AC #4: MET — lint 0/0; full suite 2085/0/0/1; release ready/tag false; story-base protected parity and diff-check pass; accepted WD-e4r7 is the sole older-base exception.
- [x] AC #5: NOT MET — coverage validates, but the referenced bundle set does not pass and operator dispositions remain absent.

## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-25.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## Implementation Evidence

### Scope and artifacts
- Consolidated row/cell index: `datasets/runs/maestro-parity/WD-fay0/evidence-index.md`.
- Machine-readable index: `datasets/runs/maestro-parity/WD-fay0/evidence-index.json`.
- Exact checker/gate transcript: `datasets/runs/maestro-parity/WD-fay0/gate-transcript.md`.
- Mechanical validator: `datasets/runs/maestro-parity/WD-fay0/validate_index.py`.
- Bundle size: 212 KiB, four files, under the 16 MiB ceiling. No lane media, model weights, credentials, or disposable checkout was copied. No render host was contacted.

### Lane checker results
- WD-m0r5 image: exit 0, PASS.
- WD-rous music: exit 0, PASS.
- WD-cpow SFX/audio-post: exit 0, PASS.
- WD-2gyw video subset: exit 0, PASS.
- WD-r81u finishing: exit 0, PASS.
- WD-bxhc voice/character: exit 0, PASS.
- WD-dmf2 director: exit 1 at PM-recorded accepted commit `741a8bb27c4bec3be38667b090a03bedb00e3010`; failures are objective gates 21, 23, 24, 26, 27 and pending reviewer. The bundle is absent from capstone base `82f6c38` and was inspected only in a disposable detached worktree.
- WD-0zj8 clean install: exit 1 because no canonical `evidence.json` exists. The accepted artifact is the no-GPU plan/typed-refusal half only.

### Row inventory
- Parsed all state-bearing columns in image, music, SFX, video, finishing, voice, character, and director matrices: 208 cells.
- Totals: 46 `host_run_verified`, 34 unsupported (including typed/lane boundaries and measured hardware boundaries), 120 planned, 6 `evidence_complete_pending_review`, and 2 not applicable.
- The six undelivered video family groups remain TaoMate, H3 outpaint, LTX-2.5, LTX-2.3, SCAIL-2, and Wan-2gp. Four logical voice/character rows—six Image/Video or clone state cells—remain pending cloning-reuse consent.
- Explicit non-matrix editor/first-run inventory: 7 verified-local, 1 unsupported, 2 planned.
- Every planned entry has a recorded blocker in the index. No verdict was upgraded, downgraded, copied, or relabelled by WD-fay0.

### Better-than-Maestro proofs
- Checker fail-closed proof: targeted suite passed 61 tests with errors=0/failures=0/skipped=0, covering every canonical field/constraint violation, symlink, hash tampering, denied authorization, and non-mutating exact CLI failure.
- Clean-machine proof: no-GPU half verified from a disposable checkout: install succeeded, clips=4 plan emitted, `generated_artifact=false`, exit 3 with `HOST_CONFIGURATION_INCOMPLETE` and `MODEL_MANIFEST_REQUIRED`, no traceback. Generated half remains blocked on per-batch host authorization, model-download approval, and a complete authorized host/model manifest.

### CI/Test Results
Commands run:
- `python3 scripts/verify_maestro_parity.py datasets/runs/maestro-parity/<each lane>`
- `python3 datasets/runs/maestro-parity/WD-fay0/validate_index.py`
- `uv run --frozen --extra dev pytest -q tests/test_maestro_parity_evidence.py tests/test_readme_quickstart.py::test_clean_checkout_install_plan_then_typed_generation_refusal --junitxml=/tmp/WD-fay0-targeted.xml`
- `timeout 1800 uv run --frozen --extra dev pytest -q --junitxml=/tmp/WD-fay0-full.xml`
- `pvg lint --backlog`
- `uv run --frozen --extra dev wgp release verify`
- `git diff --exit-code 82f6c38570a818dd8dbd3e70baebd037459661b3 -- services/jobs/queue.py services/director/renderers/policy.py services/director/wiring.py services/jobs/preflight.py scripts/run_film.py`
- `git diff --check`

Summary: validator PASS (208 rows, 8 lanes, 6 passing bundles, 2 failing bundles); targeted proof PASS 61/0/0/0; clean-tree full suite PASS tests=2085 errors=0 failures=0 skipped=1; lint PASS 126 scanned, 0 errors, 0 review findings; release=ready/tag_created=false; story-base protected parity PASS; diff-check PASS. The only difference from `40f8c2b` is `services/jobs/preflight.py`, independently accepted by WD-e4r7 for fail-closed `nvidia-smi` CSV parsing. The first full-suite attempt had two failures caused solely by in-repo gate instrumentation dirtying the real-tree release checks; that transcript is retained and the clean-tree rerun above passed.

Commit SHA: 1dbdd7977560c74a31a05986413b5671880b8031
Branch: story/WD-fay0; pushed and byte-verified against origin.

## nd_contract
status: delivered

### evidence
- Artifacts, checker transcripts, row inventory, hashes, gate receipts, commit, and pushed branch are recorded above and in `datasets/runs/maestro-parity/WD-fay0/`.

### proof
- [x] AC #1 evaluated: NOT MET — 120 cells remain planned and 6 remain pending operator consent; no operator-approved terminal disposition exists.
- [x] AC #2 evaluated: NOT MET — WD-0zj8 and WD-dmf2 checker exits are non-zero; WD-dmf2 is also absent from capstone base.
- [x] AC #3 evaluated: NOT MET — WD-0zj8 has no generated artifact or canonical evidence bundle; required operator host/model inputs remain absent.
- [x] AC #4 evaluated: MET — lint, clean-tree full suite, release, story-base protected parity, and diff-check pass; the sole older-base preflight difference is the independently accepted WD-e4r7 exception.
- [x] AC #5 evaluated: NOT MET — coverage is complete and mechanically validated, but the referenced bundle set cannot pass while WD-0zj8/WD-dmf2 fail and unresolved planned entries lack operator disposition.

## nd_contract
status: in_progress

### evidence
- 2026-09-26 capstone execution started in story worktree at HEAD 82f6c38.

### proof
- [ ] Pending consolidated checker matrix, row disposition table, standing gates, commit, push, and delivery verification.

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
- 2026-09-25T02:28:58Z dep_removed: was_blocked_by WD-m0r5
- 2026-09-25T02:42:09Z dep_removed: was_blocked_by WD-e4r7
- 2026-09-25T04:33:19Z dep_removed: was_blocked_by WD-0zj8
- 2026-09-25T05:04:03Z dep_removed: was_blocked_by WD-rous
- 2026-09-25T06:24:28Z dep_removed: was_blocked_by WD-cpow
- 2026-09-25T18:11:21Z dep_removed: was_blocked_by WD-2gyw
- 2026-09-25T20:13:03Z dep_removed: was_blocked_by WD-r81u
- 2026-09-25T21:27:31Z dep_removed: was_blocked_by WD-bxhc
- 2026-09-26T00:07:41Z dep_removed: was_blocked_by WD-dmf2
- 2026-09-26T00:08:49Z status: open -> in_progress
- 2026-09-26T00:08:50Z auto-follows: linked to predecessor WD-651z
- 2026-09-26T00:08:50Z auto-follows: linked to predecessor WD-m0r5
- 2026-09-26T00:08:50Z auto-follows: linked to predecessor WD-e4r7
- 2026-09-26T00:08:50Z auto-follows: linked to predecessor WD-0zj8
- 2026-09-26T00:08:50Z auto-follows: linked to predecessor WD-rous
- 2026-09-26T00:08:50Z auto-follows: linked to predecessor WD-cpow
- 2026-09-26T00:08:50Z auto-follows: linked to predecessor WD-2gyw
- 2026-09-26T00:08:50Z auto-follows: linked to predecessor WD-r81u
- 2026-09-26T00:08:50Z auto-follows: linked to predecessor WD-bxhc
- 2026-09-26T00:08:50Z auto-follows: linked to predecessor WD-dmf2
- 2026-09-26T00:08:50Z claimed by dev-WD-fay0
- 2026-09-26T00:55:32Z status: in_progress -> in_progress
- 2026-09-26T01:18:10Z status: in_progress -> closed
- 2026-09-26T02:47:58Z dep_added: blocked_by WD-r4n8
- 2026-09-26T03:17:49Z dep_removed: was_blocked_by WD-r4n8
- 2026-09-26T04:30:28Z dep_added: blocked_by WD-i7qs
- 2026-09-26T04:30:28Z dep_added: blocked_by WD-r4n8
- 2026-09-26T04:32:52Z dep_added: blocked_by WD-14ej

## Links
- Parent: [[WD-3nod]]
- Blocked by: [[WD-i7qs]], [[WD-r4n8]], [[WD-14ej]]
- Was blocked by: [[WD-651z]], [[WD-m0r5]], [[WD-e4r7]], [[WD-0zj8]], [[WD-rous]], [[WD-cpow]], [[WD-2gyw]], [[WD-r81u]], [[WD-bxhc]], [[WD-dmf2]], [[WD-r4n8]]
- Follows: [[WD-651z]], [[WD-m0r5]], [[WD-e4r7]], [[WD-0zj8]], [[WD-rous]], [[WD-cpow]], [[WD-2gyw]], [[WD-r81u]], [[WD-bxhc]], [[WD-dmf2]]
- Led to: [[WD-r4n8]], [[WD-i7qs]]

## Comments

### 2026-09-26T00:57:06Z speed
## nd_contract
status: delivered

### evidence
- Commit 1dbdd7977560c74a31a05986413b5671880b8031 is pushed to origin/story/WD-fay0. Consolidated index, machine-readable inventory, gate transcript, and validator are committed under datasets/runs/maestro-parity/WD-fay0/.

### proof
- [x] AC #1: NOT MET — 120 planned and 6 consent-pending cells remain.
- [x] AC #2: NOT MET — WD-0zj8 and WD-dmf2 checker exits are 1.
- [x] AC #3: NOT MET — clean-machine generated-artifact half is blocked on operator host/model inputs.
- [x] AC #4: MET — lint 0/0; full suite 2085 tests, 0 errors, 0 failures, 1 skip; release ready/tag false; story-base protected parity and diff-check pass; accepted WD-e4r7 is the sole older-base exception.
- [x] AC #5: NOT MET — coverage validates, but referenced bundle set does not pass and operator dispositions remain absent.

### 2026-09-26T00:57:33Z speed
### AC Verification
| AC | Requirement | Evidence | Status |
|---|---|---|---|
| 1 | Zero targeted entries unresolved | evidence-index.md complete matrix | NOT MET: 120 planned plus 6 consent-pending cells |
| 2 | Every referenced lane bundle passes checker | gate-transcript.md checker sections | NOT MET: WD-0zj8 and WD-dmf2 exit 1 |
| 3 | Clean-machine generated artifact | WD-0zj8 blocked-record and targeted proof | NOT MET: no-GPU half only; operator host/model inputs absent |
| 4 | Standing gates | gate-transcript.md gate sections | MET: lint 0/0; suite 2085/0/0/1; release ready/tag false; base parity and diff-check pass; accepted WD-e4r7 exception |
| 5 | Complete mechanically valid index | validate_index.py output | NOT MET: coverage validates, but referenced set fails and dispositions remain unapproved |

## nd_contract
status: delivered

### evidence
- Commit 1dbdd7977560c74a31a05986413b5671880b8031 is pushed to origin/story/WD-fay0; evidence artifacts are committed.

### proof
- [x] All five WD-fay0 acceptance criteria are explicitly evaluated above; four substantive completion criteria are not met and one standing-gate criterion is met.
