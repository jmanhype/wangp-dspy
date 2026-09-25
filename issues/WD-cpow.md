---
id: WD-cpow
title: "SFX audio-post evidence"
status: closed
priority: 2
type: feature
labels: [capability, evidence, external-integration, accepted]
parent: WD-3nod
created_at: 2026-09-24T14:14:06Z
created_by: speed
updated_at: 2026-09-25T06:24:28Z
content_hash: "sha256:4feeef607ff73a8b7ddbdd90185a192a6c24ead988cc2cf1ed0acf0593366261"
assignee: dev-WD-cpow
follows: [WD-rous, WD-0zj8]
closed_at: 2026-09-25T06:24:28Z
close_reason: "Approved after independent artifact hash, media packet-stream, gate, download-reuse, checker, and standing-gate verification at 10a5e92060041a0d7542ae46299730d6c639325f."
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


## nd_contract
status: accepted

### evidence
- PM closeout applied via pvg story accept on 2026-09-25.

### proof
- [x] Story closed after accepted label was applied.


## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-25.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## Implementation Evidence (DELIVERED)

PROOF:

### Host operation
- Authorized batch: `operator-authorization.md`; planned/actual network pull 8,677,764 bytes under the 20,000,000,000-byte ceiling.
- All 2,356,908,559 Stable Audio bytes were already present from WD-rous; incremental Stable Audio bytes were zero.
- Derived preflight floor: 8.16 GB = approximately 8 GB post-download floor + 0.009 GB download + 0.05 GB render working set + 0.10 GB margin. Host had 11,026,259,968 bytes before and 10,993,692,672 bytes after the pull.
- Outputs/hash evidence: `output-hashes.txt`, `audio-statistics.json`, `ffprobe-*.json`, and `video-stream-hash.*.txt`.
- Queue: `queue-record.json` plus `queue-complete.log`; state `done`, all three clips bound to artifacts.

### CI/Test Results
- Commands run:
  - `uv run --frozen --extra dev pytest -q tests/test_sfx_capabilities.py tests/test_maestro_parity_evidence.py --junitxml=/tmp/WD-cpow-targeted.xml`
  - `timeout 1800 uv run --frozen --extra dev pytest -q --junitxml=datasets/runs/maestro-parity/WD-cpow/fullsuite.xml`
  - `timeout 300 uv run --frozen --extra dev wgp release verify`
  - `git diff --exit-code 6f708d4 -- services/jobs/queue.py services/director/renderers/policy.py services/director/wiring.py services/jobs/preflight.py scripts/run_film.py`
  - `git diff --check`
- Targeted: 89 tests, 0 errors, 0 failures, 0 skipped.
- Full suite: 2,085 tests, 0 errors, 0 failures, 1 skipped; one pre-existing FastAPI/Starlette deprecation warning.
- Release: `release=ready`, `tag_created=false`.
- Protected-file parity versus branch base `6f708d4`: PASS.
- The story text also names `40f8c2b`; that older base predates accepted WD-e4r7 preflight changes already contained in `6f708d4`. This lane introduces no protected-file diff versus its actual branch base. Recorded in `standing-gates-final.txt`.

### Checker and matrix
- Checker: `FAIL reviewer_verdict.decision: must be approved`, exit 1. Every other canonical field group validates; reviewer verdict intentionally remains pending.
- Matrix: Stable Audio diagonal -> `unsupported_on_this_hardware` from measured 44.1 kHz output. VibeVoice revoice and DeepFilterNet refinement diagonals remain `planned` with complete hash-bound evidence pending human review. All six off-diagonal planning-unsupported boundaries remain unchanged.
- `matrix-parse.txt` passes 3 identities, 6 unchanged off-diagonal boundaries, one hardware-unsupported diagonal, and two pending diagonals.

### Commit
- Branch: `story/WD-cpow`
- SHA at delivery: `14dcf59` (full SHA recorded below after delivery command)

### pvg verify
- `VERIFY: PASSED (5 files scanned, 0 issues)`

### AC Verification
| AC # | Requirement | Evidence Location | Status |
|---|---|---|---|
| 1 | checker-pass before host_run_verified | checker-result.txt; docs/sfx-capabilities.md | BLOCKED ON REVIEW for VibeVoice/DeepFilterNet; no premature promotion |
| 2 | absent/partial evidence stays non-verified | matrix-transition-check.json; docs/sfx-capabilities.md | PASS |
| 3 | mechanical row updates/citations | docs/sfx-capabilities.md; matrix-parse.txt | PASS |
| 4 | full provenance/hashes/metadata/reviewer approval | evidence.json; output-hashes.txt | PARTIAL: all objective evidence present; reviewer approval pending |
| 5 | hash-backed audio/video preservation | video-stream-hash.*.txt; objective-gates.json | PASS |
| 6 | all three diagonals terminal | docs/sfx-capabilities.md | PARTIAL: Stable terminal unsupported; two pending review |
| 7 | protected scope/files unchanged | standing-gates-final.txt; protected-parity-6f.txt | PASS versus 6f708d4; inherited 40f mismatch documented |

LEARNINGS:
- WD-rous made the entire Stable Audio set reusable, so this lane's actual pull was only the absent 8.68 MB DeepFilterNet runtime/model set.
- DeepFilterNet 0.5.6 needs a small torchaudio compatibility shim on the host's torchaudio 2.10 stack; the native script records this without downgrading shared ML packages.
- VibeVoice remote supplier deliberately writes into a unique hidden run namespace; post-generation mux must resolve that namespace rather than assume manifest-relative output paths.
- Holding video fixed is objectively provable with ffmpeg streamhash equality even when container bytes must change for replacement audio.

## nd_contract
status: delivered

### evidence
- Host artifacts, queue, hashes, metadata, authorization, download report, checker, tests, release gate, matrix evidence, and commits under `datasets/runs/maestro-parity/WD-cpow/`.
- Final worktree commit before delivery note: 14dcf59.

### proof
- [x] Real authorized Stable Audio attempt recorded and measured unsupported at 44.1 kHz.
- [x] Real VibeVoice revoice and DeepFilterNet refinement artifacts, hashes, metadata, queue state, and preservation gates recorded.
- [x] Targeted and full test counters recorded; release and branch-base protected-file gates pass.
- [ ] Human reviewer approval and canonical checker PASS remain pending by design.


## MANDATORY SKILLS
- pvg

Observable outcome: an explicitly authorized future run emits hashed SFX/audio-post artifacts and measured metadata under datasets/runs/maestro-parity/WD-cpow/; no GPU batch is authorized by this story and no audio result is claimed without that bundle.

## History
- 2026-09-24T14:14:08Z dep_added: blocks WD-651z
- 2026-09-24T14:14:10Z dep_added: blocks WD-fay0
- 2026-09-24T14:39:54Z dep_removed: no_longer_blocks WD-651z
- 2026-09-25T05:12:08Z status: open -> in_progress
- 2026-09-25T05:12:08Z auto-follows: linked to predecessor WD-rous
- 2026-09-25T05:12:08Z claimed by dev-WD-cpow
- 2026-09-25T05:51:23Z status: in_progress -> in_progress
- 2026-09-25T05:51:23Z auto-follows: linked to predecessor WD-0zj8
- 2026-09-25T06:24:28Z status: in_progress -> closed
- 2026-09-25T06:24:28Z dep_removed: no_longer_blocks WD-fay0

## Links
- Parent: [[WD-3nod]]
- Follows: [[WD-rous]], [[WD-0zj8]]

## Comments

### 2026-09-25T05:52:40Z speed
## Implementation Evidence (DELIVERED)

Summary: Real authorized host batch emitted one Stable Audio SFX attempt, one VibeVoice revoice MP4, and one DeepFilterNet refinement MP4 with hashes and measured metadata. Stable Audio is unsupported at 44.1 kHz; the other two diagonals remain pending human review. Full suite 2085/0 failures/0 errors; release ready/tag false.

Commands run:
- timeout 700 ssh -n -o BatchMode=yes -o ConnectTimeout=15 3090 timeout 620 bash /home/straughter/Wan2GP/wd_c_pow_stable_sfx.sh
- timeout 2400 datasets/runs/maestro-parity/WD-cpow/run-vibevoice-remote.sh
- timeout 360 ssh -n -o BatchMode=yes -o ConnectTimeout=15 3090 timeout 300 bash /home/straughter/Wan2GP/wd_c_pow_revoice_mux.sh
- timeout 900 ssh -n -o BatchMode=yes -o ConnectTimeout=15 3090 timeout 840 /home/straughter/Wan2GP/venv/bin/python /home/straughter/Wan2GP/wd_c_pow_refine.py
- uv run --frozen --extra dev pytest -q tests/test_sfx_capabilities.py tests/test_maestro_parity_evidence.py --junitxml=/tmp/WD-cpow-targeted.xml
- timeout 1800 uv run --frozen --extra dev pytest -q --junitxml=datasets/runs/maestro-parity/WD-cpow/fullsuite.xml
- timeout 300 uv run --frozen --extra dev wgp release verify

Branch story/WD-cpow at SHA 14dcf59d7fd7a95aee6a093500eee1e160840326.

## nd_contract
status: delivered

### evidence
- Branch story/WD-cpow at SHA 14dcf59d7fd7a95aee6a093500eee1e160840326.
- Bundle datasets/runs/maestro-parity/WD-cpow/evidence.json; full suite tests=2085 errors=0 failures=0 skipped=1; release ready/tag false; checker sole pending-reviewer failure.
- Stable 44.1 kHz attempt measured unsupported; VibeVoice and DeepFilterNet outputs complete but pending review.

### proof
- [x] AC #1: No successful row is promoted without checker PASS and reviewer approval.
- [x] AC #2: Partial/pending evidence remains non-verified.
- [x] AC #3: Matrix transitions and citations parse from bundle contents.
- [x] AC #4: Required provenance, rights, metadata, hashes, duration, and gates are recorded; reviewer remains pending.
- [x] AC #5: Video preservation uses matching recorded packet-stream hashes.
- [x] AC #6: Stable diagonal is terminal unsupported; two diagonals correctly remain pending review.
- [x] AC #7: No training/GUI/registry/weight commit; protected parity exits zero versus supplied branch base 6f708d4; inherited 40f mismatch documented.


### 2026-09-25T05:52:57Z speed
## Implementation Evidence

Summary: WD-cpow produced one real authorized Stable Audio SFX attempt, one VibeVoice revoice MP4, and one DeepFilterNet refinement MP4 with provenance, queue state, hashes, measured metadata, and preservation gates. Stable Audio is measured unsupported at 44.1 kHz; VibeVoice and DeepFilterNet remain pending reviewer approval. Full suite tests=2085 errors=0 failures=0 skipped=1; release=ready tag_created=false; protected parity versus 6f708d4 and diff check PASS.

Commands run:
- timeout 700 ssh -n -o BatchMode=yes -o ConnectTimeout=15 3090 timeout 620 bash /home/straughter/Wan2GP/wd_c_pow_stable_sfx.sh
- timeout 2400 datasets/runs/maestro-parity/WD-cpow/run-vibevoice-remote.sh
- timeout 360 ssh -n -o BatchMode=yes -o ConnectTimeout=15 3090 timeout 300 bash /home/straughter/Wan2GP/wd_c_pow_revoice_mux.sh
- timeout 900 ssh -n -o BatchMode=yes -o ConnectTimeout=15 3090 timeout 840 /home/straughter/Wan2GP/venv/bin/python /home/straughter/Wan2GP/wd_c_pow_refine.py
- timeout 1800 uv run --frozen --extra dev pytest -q --junitxml=datasets/runs/maestro-parity/WD-cpow/fullsuite.xml
- timeout 300 uv run --frozen --extra dev wgp release verify

SHA: 14dcf59d7fd7a95aee6a093500eee1e160840326

## nd_contract
status: delivered

### evidence
- Branch story/WD-cpow at SHA 14dcf59d7fd7a95aee6a093500eee1e160840326.
- Bundle datasets/runs/maestro-parity/WD-cpow/evidence.json; full suite tests=2085 errors=0 failures=0 skipped=1; release ready/tag false; checker sole pending-reviewer failure.
- Stable 44.1 kHz attempt measured unsupported; VibeVoice and DeepFilterNet outputs complete but pending review.

### proof
- [x] AC #1: No successful row is promoted without checker PASS and reviewer approval.
- [x] AC #2: Partial/pending evidence remains non-verified.
- [x] AC #3: Matrix transitions and citations parse from bundle contents.
- [x] AC #4: Required provenance, rights, metadata, hashes, duration, and gates are recorded; reviewer remains pending.
- [x] AC #5: Video preservation uses matching recorded packet-stream hashes.
- [x] AC #6: Stable diagonal is terminal unsupported; two diagonals correctly remain pending review.
- [x] AC #7: No training/GUI/registry/weight commit; protected parity exits zero versus supplied branch base 6f708d4; inherited 40f mismatch documented.

