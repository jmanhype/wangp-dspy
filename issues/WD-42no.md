---
id: WD-42no
title: "E2e: execute exactly one approved LF004 governed render"
status: in_progress
priority: 0
type: task
labels: [e2e, capstone]
parent: WD-h73w
created_at: 2026-09-20T19:48:19Z
created_by: speed
updated_at: 2026-09-21T00:59:30Z
content_hash: "sha256:461eb551904e104d21d79bce8ba70e947704e5f1e85e99c448cda5f2ef9e497e"
blocked_by: [WD-rb1f, WD-rj6e]
was_blocked_by: [WD-z46c, WD-ssdt]
assignee: dev-WD-42no
follows: [WD-z46c]
---

## Description

## Description
## USER INTENT
After explicitly approving the LF004 no-GPU plan, the operator wants exactly one governed real render that produces and stores a reviewable keeper-or-reject film artifact.

## Context (Embedded)
This story must not start until the planning story is accepted and the operator explicitly approves the exact plan hash. It uses the existing governed queue, preflight, provenance, vision/Whisper/SyncNet gates, retry policy, and assembly path. Governed retries belong to the one execution; a second independent production run does not.

## OUT OF SCOPE
- Running before explicit approval of the exact plan hash.
- A second independent render run.
- Changing pipeline behavior, gates, risk boundaries, or retry semantics.
- Claiming creative acceptance without an explicit operator verdict.

## DIFF BUDGET
- Runtime artifacts and evidence only unless an execution script is indispensable; under 200 changed LOC.

## Boundary Map
PRODUCES:
- one governed LF004 execution with queue/provenance records
- one reviewable assembled film and contact-sheet/probe review artifacts
- final mechanical gate evidence and operator-review-pending record

CONSUMES:
- accepted LF004 content plan and run ledger
  schema: wangp-dspy.content-plan/v1 plus canonical run ledger
- scripts/run_film.py -> run_film(...)
  spec: run_film(script_file, plates_dir, characters, ..., dry_run: bool = False) -> run result
- existing governed queue, render host, QC, AV, and provenance subsystems
  source: accepted Wangp governed production pipeline modules and remote host policy

## Story Contract
The user can inspect exactly one governed LF004 render whose final film, probes, review visuals, and provenance are stored and hash-identified.

1. Execution begins only after the exact approved plan hash is recorded in nd.
2. Exactly one governed production execution is started; its identifier and every governed retry are recorded.
3. Host and pipeline preflight pass before model/render work.
4. Every emitted cut passes identity vision, mouth-box, Whisper pre/post, and SyncNet gates under current accepted policy.
5. Assembly completes and final media hash, duration, resolution, frame count, and audio properties are recorded.
6. A human-reviewable contact sheet and/or first-frame packet is emitted beside probe evidence.
7. Provenance ties brief, plan, inputs, queue records, settings, retries, QC, assembly, repository state, and final hash together.
8. The story records `operator_review_pending`; no creative acceptance is claimed automatically.
9. No unrelated source behavior changes.

## Testing Requirements
- Exact governed commands required by the accepted LF004 plan.
- All runtime-declared targeted QC/provenance tests.
- `ffprobe` final-media validation.
- Contact-sheet/probe generation and hash recording.
- `git diff --check`

## MANDATORY SKILLS
- pvg

## nd_contract
status: new

### evidence
- Operator limited this goal to exactly one Wangp real render.

### proof
- [ ] Story #1: Exact plan approval precedes execution.
- [ ] Story #2: One execution and all retries are accounted for.
- [ ] Story #3: Preflight passes.
- [ ] Story #4: All declared cut gates pass.
- [ ] Story #5: Final media properties and hash are recorded.
- [ ] Story #6: Review visuals are available.
- [ ] Story #7: End-to-end provenance is complete.
- [ ] Story #8: Operator review remains pending.
- [ ] Story #9: No unrelated behavior changes.

## Acceptance Criteria


## Design


## Notes
## Operator Recovery Approval

Approved UTC: 2026-09-21T00:54:03Z
Operator response: approve
Approved canonical plan SHA-256: 620f2ba44beb7d0bc920772c136aa0ce6f76df89acd286647c23e5a7c8015eb8
Approved candidate brief SHA-256: 67202d3597affeab4e5edcf15a1acef2f5e88ed00950ce17ff3012f5bb0472cd
Candidate brief: datasets/content_briefs/lf004-operator-dogfood-56f/brief.json (to be committed into the repository by the recovery delivery)
Policy: 4 x 56 frames @24fps, guide_duration_s == shot_duration_s == 2.333 s (the accepted WD-rij6 per-cut policy)
Authorization: exactly one governed LF004 recovery execution through the accepted Wangp pipeline. This approval does not authorize a second independent run, gate or retry-policy changes, live-hook changes, or unrelated work.

## nd_contract
status: in_progress

### evidence
- Operator approval of canonical plan hash 620f2ba4... recorded from the operator's literal response "approve" at 2026-09-21T00:54:03Z.
- Guard-rejected approved plan 70280fdc... documented above; corrected candidate replay-verified twice.

### proof
- [x] Explicit operator approval of the corrected plan hash is recorded.
- [x] Unauthorized render dispatch prevented before approval.
- [ ] One governed recovery execution passing every declared gate with a reviewable artifact and committed provenance.

## Dispatch Hold — Do Not Respawn Or Release (dispatcher, 2026-09-21)

WD-42no is intentionally parked `in_progress` under claim `dev-WD-42no` pending an
operator decision. The execution loop reports this story as `stalled` and recommends
`pvg loop recover` followed by respawn or release. **Do not do that for WD-42no.**

- Respawning or releasing would let a developer start a governed render that is not
  authorized. The operator authorized exactly one LF004 execution, and that execution
  is complete: it failed closed at cut 2 after the three-attempt policy.
- The approved plan hash `70280fdcd6fb7f54bc4f7027e03de54e4897178dd41adcf92ef31bd347d7bd86`
  can no longer even be regenerated: the merged guard rejects its brief (exit 1, typed
  mismatch error, zero artifacts). See finding 85 and WD-ssdt.
- Any further render requires explicit operator approval of a corrected plan hash
  recorded verbatim in this story. The replay-verified candidate is
  `620f2ba44beb7d0bc920772c136aa0ce6f76df89acd286647c23e5a7c8015eb8`
  (brief `sha256:67202d3597affeab4e5edcf15a1acef2f5e88ed00950ce17ff3012f5bb0472cd`),
  still awaiting approval.
- `pvg loop recover` may prune the `dev-WD-42no` worktree. The LF004 provenance and its
  14 reconciliation scripts are preserved with a per-file hash manifest at
  `/Users/Shared/HermesWorkspace/lf004-provenance-preserved-20260921/MANIFEST.json`
  (`sha256:1b3865666017f3195e36b166a03c5966325e57fc9c1e47d6e322296c6ba73c50`, 48/48 verified)
  and must be committed into the repository by the delivery.

## nd_contract
status: in_progress

### evidence
- Dispatch hold recorded with the reasoning, the blocking approval, and the preservation location.
- Operator approval for `620f2ba4...` remains outstanding; no approval text exists in this story.

### proof
- [x] Unauthorized render dispatch is prevented by an explicit recorded hold.
- [ ] Operator approval of a corrected plan hash recorded in this story.
- [ ] One governed recovery execution passing every declared gate with a reviewable artifact.

## Provenance Durability Finding + Preservation (dispatcher, 2026-09-21)

The LF004 execution provenance was **not in git**. Measured in the `dev-WD-42no` worktree:

```text
git ls-files datasets/runs/provenance/lf004-operator-dogfood-20260920 | wc -l   -> 0
find      datasets/runs/provenance/lf004-operator-dogfood-20260920 -type f | wc -l -> 47
```

All 47 files existed only as untracked worktree files, including the 14 reconciliation
scripts the approved execution depended on (`reconcile_audio_policy_and_continue.sh`,
`fix_manifest_indexes_and_continue.sh`, `reconcile_runtime_fields_and_continue.sh`,
`reconcile_whisper_map_and_continue.sh`, `clarify_speaker_and_continue.sh`,
`run_lf004_once.sh`, `stage_assets_and_retry_once.sh`, `finalize_lf004.py`, and the
seed-905 re-judge). The loop had already flagged this worktree for recovery, so the
accepted evidence trail and the recovery execution inputs were one cleanup away from
being lost.

Preserved and hash-verified outside the worktree:

- Location: `/Users/Shared/HermesWorkspace/lf004-provenance-preserved-20260921/`
- Contents: the 47 provenance files, the 56-frame candidate brief, and finding 85.
- Manifest: `MANIFEST.json` — 48 entries, per-file sha256 + size.
- `MANIFEST.json` sha256: `1b3865666017f3195e36b166a03c5966325e57fc9c1e47d6e322296c6ba73c50`
- Integrity re-check: 48 verified, 0 mismatches (`INTEGRITY_OK`).

Recommendation: the WD-42no delivery must commit this provenance into the repository so
the evidence trail and recovery inputs are version-controlled rather than depending on a
single worktree directory.

## nd_contract
status: in_progress

### evidence
- Durability measurement: 0 tracked / 47 on-disk provenance files for the approved LF004 execution.
- Preservation copy with per-file sha256 manifest `1b386566...`; 48/48 hashes verified.
- Corrected candidate plan `620f2ba4...` (replay-verified) recorded in the previous note block.
- Guard rejection of the approved brief on main `4b99b3a`: exit 1, typed mismatch error, zero artifacts.

### proof
- [x] Accept-ed evidence trail and recovery inputs preserved and hash-verified.
- [x] Corrected plan candidate produced for operator approval.
- [ ] Operator approval of `620f2ba44beb7d0bc920772c136aa0ce6f76df89acd286647c23e5a7c8015eb8` (or an alternative).
- [ ] Provenance committed into the repository as part of the delivery.
- [ ] One governed recovery execution passing every declared gate with a reviewable artifact.

## Recovery Preflight Evidence (dispatcher, 2026-09-21)

### 1. The merged guard rejects the approved LF004 brief

Run against the committed brief through the no-GPU gateway on main `4b99b3a`:

```text
$ ./.venv/bin/python scripts/run_content_brief.py \
    --brief datasets/content_briefs/lf004-operator-dogfood/brief.json \
    --plates datasets/content_briefs/lf004-operator-dogfood/plates \
    --output <scratch>/plan.json --run-dir <scratch>/run
predict.content_brief.ContentBriefError: audio duration mismatch for turn 1:
  guide=.../lf003-vibevoice-audition-20260917/audio/tess.prepared.wav
  declared_s=4.458333333333333 measured_s=2.333333
EXIT=1   artifacts_written=0
```

The approved plan hash `70280fdc...` can no longer be regenerated from its brief; the
defect is caught in the planning stage before any GPU work.

### 2. Corrected candidate plan (duration-corrected, 56 frames per cut)

Same dialogue, characters, plates, and repository-owned guides; only `durations_s`
changed to the Content Brief Gateway default `56/24` s per turn, which reproduces the
accepted LF003 per-cut policy (WD-rij6: 56 frames/cut, 224 frames, 9.333333 s total).

- Candidate brief: `.claude/worktrees/dev-WD-42no/datasets/content_briefs/lf004-operator-dogfood-56f/brief.json` (uncommitted candidate artifact)
- `candidate_brief_hash`: `sha256:67202d3597affeab4e5edcf15a1acef2f5e88ed00950ce17ff3012f5bb0472cd`
- `canonical_plan_sha256`: `620f2ba44beb7d0bc920772c136aa0ce6f76df89acd286647c23e5a7c8015eb8`
- Replay: gateway run twice into separate temp dirs, canonical hashes identical (`620f2ba4...`).
- Clips: 4 x `frames=56`, `audio_length_frames=56`, `guide_duration_s=shot_duration_s=2.333`, `keeper_window_s=[0.0, 2.3333333333333335]`.
- Summary: `{"clip_count": 4, "planned_duration_s": 9.332, "dry_run": true, "gpu_work": false, "queue_submitted": false}`.
- Guard outcome: the candidate passes the new preflight (measured guide 2.333333 matches declared 2.333333 within 1e-6).

Reproduce with the same command as above plus `--brief <candidate brief>` and the same
`--plates` directory; then compute the canonical hash with the `canonical_sha` algorithm
already defined in `datasets/content_briefs/lf004-operator-dogfood/run/verify.py`.

### 3. Approval required (single explicit decision)

Approve canonical plan hash `620f2ba44beb7d0bc920772c136aa0ce6f76df89acd286647c23e5a7c8015eb8`
(candidate brief `sha256:67202d35...`) for exactly one governed recovery execution under
WD-h73w using the accepted 56-frame-per-cut policy, or direct an alternative
(regenerate longer guides and keep 4.458 s turns).

### 4. Required deliverables for the recovery execution

- Commit the corrected brief + plan into the repository and record brief/plan/run-ledger hashes.
- Provide a corrected verification script; the existing `datasets/content_briefs/lf004-operator-dogfood/run/verify.py` hard-asserts 107 frames and `planned_duration_s == 17.832`, which is specific to the defective plan.
- Execute exactly one governed render through the accepted pipeline with the three-attempt policy, all declared gates, and preserved review artifacts.

## nd_contract
status: in_progress

### evidence
- Guard rejection of the approved brief: exit 1 with the typed mismatch error and zero artifacts on main `4b99b3a`.
- Corrected candidate plan `620f2ba4...` replay-verified twice; 4 x 56 frames matching the accepted WD-rij6 policy.
- Root cause and corrective actions recorded at `docs/findings/85-lf004-guide-duration-mismatch.md` (dev-WD-42no worktree) and in WD-ssdt (delivered, accepted, merged).

### proof
- [x] Fail closed at cut 2 rather than relaxing gates.
- [x] Root cause identified and the guard that prevents recurrence is merged with green CI.
- [x] Corrected plan candidate produced, replay-verified, and hash-recorded.
- [ ] Operator approval of `620f2ba4...` (or an alternative) before any further render.
- [ ] One governed recovery execution passing every declared gate with a reviewable artifact.

## Root Cause: Declared Clip Duration vs Guide Audio Length

Cut-2's dead-letter is explained by a plan-input defect, not by seed luck alone.

| Item | Value | Source |
| --- | --- | --- |
| brief `durations_s` | `4.458333` per turn (107 frames @24fps) | `datasets/content_briefs/lf004-operator-dogfood/brief.json` |
| actual guide audio, all four turns | `2.333333` s (56 frames @24fps) | `ffprobe` on the four `audio_paths` guides |
| Content Brief Gateway default | `56.0/24.0` = 2.333 s | `predict/content_brief.py` (`DEFAULT_DURATION_S`) |
| LF003 accepted per-cut policy | 56 frames/cut; assembly 224 frames / 9.333 s | WD-rij6 |

Consequences measured on disk:

- Every 107-frame clip carries ~2.125 s of speech time with no guide content; the renderer fills it, observed as the intended line spoken twice (seed 904 `7351334145399bd4`, seed 905 `93075b7b7633289b`, both post-Whisper 0.167) or as double-exposure motion (seed 906 `cb1293c6e987f6a5`, vision `action_match` 0.1).
- `plan.json` sets `guide_duration_s := shot_duration_s` (4.458) instead of the guide's measured 2.333 s, so `services/director/renderers/policy.py::check_guide_duration()` compares two plan-declared values and passes trivially; the real audio file length is never inspected.
- `keeper_window_s` / `audio_policy.remux_window` are `[0.0, 4.458333]` although the master is 2.333 s long.
- Cut 1 also required two retries before passing, i.e. every LF004 cut hit the same mismatch.

Nothing was relaxed: no gate, no retry policy, no artifact. No fourth render was started.

## nd_contract
status: in_progress

### evidence
- Root cause recorded above with measured hashes/durations; write-up at `docs/findings/85-lf004-guide-duration-mismatch.md` in the `dev-WD-42no` worktree.
- Cut 1 `done`; cut 2 `dead_letter` after three `qc_gate` failures; cuts 3/4 `pending` behind cut 2.
- Approved plan hash `70280fdcd6fb7f54bc4f7027e03de54e4897178dd41adcf92ef31bd347d7bd86` is the only hash approved so far.

### proof
- [x] Fail closed at cut 2 rather than relaxing Whisper/vision/retry gates.
- [x] Root cause identified from disk evidence (guide length vs declared duration).
- [ ] Operator decision required before any further render: approve a corrected plan hash (gateway default 56/24 s per turn, matching the LF003-accepted policy) for one governed recovery execution, or authorize re-seeding the current 107-frame plan.
- [ ] Corrected render passes every declared gate and yields the reviewable artifact.

## Fail-Closed LF004 Boundary Evidence

The approved execution did not proceed to cuts 3/4. Cut 2 exhausted the accepted three-attempt QC retry policy and is durable-queue dead-lettered:

- Seed 904 raw SHA-256 `7351334145399bd4b26454760e97869da412e3015d441ea31516365c4ad3b397`: post-Whisper score 0.167; transcript included hallucinated preceding dialogue.
- Seed 905 raw SHA-256 `93075b7b7633289b2f956fb23d4fe40061650c140aff9f6af2195daa6b7d65ff`: post-Whisper score 0.167; intended line repeated.
- Seed 906 raw SHA-256 `cb1293c6e987f6a5224b3649c27392b9f75cbec769b4a1ed1ad1f944c64e71de`: Whisper pre/post passed (post score 1.0), but identity/action vision rejected ghosting/double-exposure artifacts (`action_match=0.1`, `speaker_attribution=0.1`).
- Queue states: cut 1 `done`; cut 2 `dead_letter` after 3 `qc_gate` failures; cuts 3/4 remain `pending` behind cut 2.
- Contact sheets and hashes: `datasets/runs/provenance/lf004-operator-dogfood-20260920/cut2-deadletter-review/`.
- Independent seed-905 visual re-judge passed identity/action but observed the speaker mouth closed; it is not a substitute because post-Whisper and AV gates remain failed.

No gate was relaxed and no fourth render was started. Continuing with seed 907 would exceed the current approved retry policy and needs a new explicit operator-approved recovery story.

## nd_contract
status: in_progress

### evidence
- Durable queue and attempt failure records above; dead-letter review artifacts on disk.

### proof
- [x] Fail closed at cut 2 rather than relaxing Whisper/vision/retry gates.
- [ ] Operator decision required before any additional render or recovery story.

## Operator Render Approval

Approved UTC: 2026-09-20T20:47:21Z
Operator response: yes
Exact canonical plan SHA-256: 70280fdcd6fb7f54bc4f7027e03de54e4897178dd41adcf92ef31bd347d7bd86
Authorization: exactly one governed LF004 production execution through the accepted Wangp pipeline. This approval does not authorize a second independent run, live-hook changes, or unrelated work.

## History
- 2026-09-20T19:48:19Z dep_added: blocked_by WD-z46c
- 2026-09-20T19:48:47Z dep_added: blocked_by WD-rb1f
- 2026-09-20T19:48:47Z dep_added: blocked_by WD-rj6e
- 2026-09-20T20:14:46Z dep_removed: was_blocked_by WD-z46c
- 2026-09-20T20:47:21Z status: open -> in_progress
- 2026-09-20T20:47:21Z auto-follows: linked to predecessor WD-z46c
- 2026-09-20T20:47:21Z claimed by dev-WD-42no
- 2026-09-20T23:53:58Z dep_added: blocked_by WD-ssdt
- 2026-09-21T00:25:02Z dep_removed: was_blocked_by WD-ssdt

## Links
- Parent: [[WD-h73w]]
- Blocked by: [[WD-rb1f]], [[WD-rj6e]]
- Was blocked by: [[WD-z46c]], [[WD-ssdt]]
- Follows: [[WD-z46c]]

## Comments

## USER INTENT
After explicitly approving the LF004 no-GPU plan, the operator wants exactly one governed real render that produces and stores a reviewable keeper-or-reject film artifact.

## Context (Embedded)
This story must not start until the planning story is accepted and the operator explicitly approves the exact plan hash. It uses the existing governed queue, preflight, provenance, vision/Whisper/SyncNet gates, retry policy, and assembly path. Governed retries belong to the one execution; a second independent production run does not.

## OUT OF SCOPE
- Running before explicit approval of the exact plan hash.
- A second independent render run.
- Changing pipeline behavior, gates, risk boundaries, or retry semantics.
- Claiming creative acceptance without an explicit operator verdict.

## DIFF BUDGET
- Runtime artifacts and evidence only unless an execution script is indispensable; under 200 changed LOC.

## Boundary Map
PRODUCES:
- one governed LF004 execution with queue/provenance records
- one reviewable assembled film and contact-sheet/probe review artifacts
- final mechanical gate evidence and operator-review-pending record

CONSUMES:
- accepted LF004 content plan and run ledger
  schema: wangp-dspy.content-plan/v1 plus canonical run ledger
- scripts/run_film.py -> run_film(...)
  spec: run_film(script_file, plates_dir, characters, ..., dry_run: bool = False) -> run result
- existing governed queue, render host, QC, AV, and provenance subsystems
  source: accepted Wangp governed production pipeline modules and remote host policy

## Story Contract
The user can inspect exactly one governed LF004 render whose final film, probes, review visuals, and provenance are stored and hash-identified.

1. Execution begins only after the exact approved plan hash is recorded in nd.
2. Exactly one governed production execution is started; its identifier and every governed retry are recorded.
3. Host and pipeline preflight pass before model/render work.
4. Every emitted cut passes identity vision, mouth-box, Whisper pre/post, and SyncNet gates under current accepted policy.
5. Assembly completes and final media hash, duration, resolution, frame count, and audio properties are recorded.
6. A human-reviewable contact sheet and/or first-frame packet is emitted beside probe evidence.
7. Provenance ties brief, plan, inputs, queue records, settings, retries, QC, assembly, repository state, and final hash together.
8. The story records `operator_review_pending`; no creative acceptance is claimed automatically.
9. No unrelated source behavior changes.

## Testing Requirements
- Exact governed commands required by the accepted LF004 plan.
- All runtime-declared targeted QC/provenance tests.
- `ffprobe` final-media validation.
- Contact-sheet/probe generation and hash recording.
- `git diff --check`

## MANDATORY SKILLS
- pvg

## nd_contract
status: new

### evidence
- Operator limited this goal to exactly one Wangp real render.

### proof
- [ ] Story #1: Exact plan approval precedes execution.
- [ ] Story #2: One execution and all retries are accounted for.
- [ ] Story #3: Preflight passes.
- [ ] Story #4: All declared cut gates pass.
- [ ] Story #5: Final media properties and hash are recorded.
- [ ] Story #6: Review visuals are available.
- [ ] Story #7: End-to-end provenance is complete.
- [ ] Story #8: Operator review remains pending.
- [ ] Story #9: No unrelated behavior changes.

## Acceptance Criteria


## Design


## Notes
## Operator Recovery Approval

Approved UTC: 2026-09-21T00:54:03Z
Operator response: approve
Approved canonical plan SHA-256: 620f2ba44beb7d0bc920772c136aa0ce6f76df89acd286647c23e5a7c8015eb8
Approved candidate brief SHA-256: 67202d3597affeab4e5edcf15a1acef2f5e88ed00950ce17ff3012f5bb0472cd
Candidate brief: datasets/content_briefs/lf004-operator-dogfood-56f/brief.json (to be committed into the repository by the recovery delivery)
Policy: 4 x 56 frames @24fps, guide_duration_s == shot_duration_s == 2.333 s (the accepted WD-rij6 per-cut policy)
Authorization: exactly one governed LF004 recovery execution through the accepted Wangp pipeline. This approval does not authorize a second independent run, gate or retry-policy changes, live-hook changes, or unrelated work.

## nd_contract
status: in_progress

### evidence
- Operator approval of canonical plan hash 620f2ba4... recorded from the operator's literal response "approve" at 2026-09-21T00:54:03Z.
- Guard-rejected approved plan 70280fdc... documented above; corrected candidate replay-verified twice.

### proof
- [x] Explicit operator approval of the corrected plan hash is recorded.
- [x] Unauthorized render dispatch prevented before approval.
- [ ] One governed recovery execution passing every declared gate with a reviewable artifact and committed provenance.

## Dispatch Hold — Do Not Respawn Or Release (dispatcher, 2026-09-21)

WD-42no is intentionally parked `in_progress` under claim `dev-WD-42no` pending an
operator decision. The execution loop reports this story as `stalled` and recommends
`pvg loop recover` followed by respawn or release. **Do not do that for WD-42no.**

- Respawning or releasing would let a developer start a governed render that is not
  authorized. The operator authorized exactly one LF004 execution, and that execution
  is complete: it failed closed at cut 2 after the three-attempt policy.
- The approved plan hash `70280fdcd6fb7f54bc4f7027e03de54e4897178dd41adcf92ef31bd347d7bd86`
  can no longer even be regenerated: the merged guard rejects its brief (exit 1, typed
  mismatch error, zero artifacts). See finding 85 and WD-ssdt.
- Any further render requires explicit operator approval of a corrected plan hash
  recorded verbatim in this story. The replay-verified candidate is
  `620f2ba44beb7d0bc920772c136aa0ce6f76df89acd286647c23e5a7c8015eb8`
  (brief `sha256:67202d3597affeab4e5edcf15a1acef2f5e88ed00950ce17ff3012f5bb0472cd`),
  still awaiting approval.
- `pvg loop recover` may prune the `dev-WD-42no` worktree. The LF004 provenance and its
  14 reconciliation scripts are preserved with a per-file hash manifest at
  `/Users/Shared/HermesWorkspace/lf004-provenance-preserved-20260921/MANIFEST.json`
  (`sha256:1b3865666017f3195e36b166a03c5966325e57fc9c1e47d6e322296c6ba73c50`, 48/48 verified)
  and must be committed into the repository by the delivery.

## nd_contract
status: in_progress

### evidence
- Dispatch hold recorded with the reasoning, the blocking approval, and the preservation location.
- Operator approval for `620f2ba4...` remains outstanding; no approval text exists in this story.

### proof
- [x] Unauthorized render dispatch is prevented by an explicit recorded hold.
- [ ] Operator approval of a corrected plan hash recorded in this story.
- [ ] One governed recovery execution passing every declared gate with a reviewable artifact.

## Provenance Durability Finding + Preservation (dispatcher, 2026-09-21)

The LF004 execution provenance was **not in git**. Measured in the `dev-WD-42no` worktree:

```text
git ls-files datasets/runs/provenance/lf004-operator-dogfood-20260920 | wc -l   -> 0
find      datasets/runs/provenance/lf004-operator-dogfood-20260920 -type f | wc -l -> 47
```

All 47 files existed only as untracked worktree files, including the 14 reconciliation
scripts the approved execution depended on (`reconcile_audio_policy_and_continue.sh`,
`fix_manifest_indexes_and_continue.sh`, `reconcile_runtime_fields_and_continue.sh`,
`reconcile_whisper_map_and_continue.sh`, `clarify_speaker_and_continue.sh`,
`run_lf004_once.sh`, `stage_assets_and_retry_once.sh`, `finalize_lf004.py`, and the
seed-905 re-judge). The loop had already flagged this worktree for recovery, so the
accepted evidence trail and the recovery execution inputs were one cleanup away from
being lost.

Preserved and hash-verified outside the worktree:

- Location: `/Users/Shared/HermesWorkspace/lf004-provenance-preserved-20260921/`
- Contents: the 47 provenance files, the 56-frame candidate brief, and finding 85.
- Manifest: `MANIFEST.json` — 48 entries, per-file sha256 + size.
- `MANIFEST.json` sha256: `1b3865666017f3195e36b166a03c5966325e57fc9c1e47d6e322296c6ba73c50`
- Integrity re-check: 48 verified, 0 mismatches (`INTEGRITY_OK`).

Recommendation: the WD-42no delivery must commit this provenance into the repository so
the evidence trail and recovery inputs are version-controlled rather than depending on a
single worktree directory.

## nd_contract
status: in_progress

### evidence
- Durability measurement: 0 tracked / 47 on-disk provenance files for the approved LF004 execution.
- Preservation copy with per-file sha256 manifest `1b386566...`; 48/48 hashes verified.
- Corrected candidate plan `620f2ba4...` (replay-verified) recorded in the previous note block.
- Guard rejection of the approved brief on main `4b99b3a`: exit 1, typed mismatch error, zero artifacts.

### proof
- [x] Accept-ed evidence trail and recovery inputs preserved and hash-verified.
- [x] Corrected plan candidate produced for operator approval.
- [ ] Operator approval of `620f2ba44beb7d0bc920772c136aa0ce6f76df89acd286647c23e5a7c8015eb8` (or an alternative).
- [ ] Provenance committed into the repository as part of the delivery.
- [ ] One governed recovery execution passing every declared gate with a reviewable artifact.

## Recovery Preflight Evidence (dispatcher, 2026-09-21)

### 1. The merged guard rejects the approved LF004 brief

Run against the committed brief through the no-GPU gateway on main `4b99b3a`:

```text
$ ./.venv/bin/python scripts/run_content_brief.py \
    --brief datasets/content_briefs/lf004-operator-dogfood/brief.json \
    --plates datasets/content_briefs/lf004-operator-dogfood/plates \
    --output <scratch>/plan.json --run-dir <scratch>/run
predict.content_brief.ContentBriefError: audio duration mismatch for turn 1:
  guide=.../lf003-vibevoice-audition-20260917/audio/tess.prepared.wav
  declared_s=4.458333333333333 measured_s=2.333333
EXIT=1   artifacts_written=0
```

The approved plan hash `70280fdc...` can no longer be regenerated from its brief; the
defect is caught in the planning stage before any GPU work.

### 2. Corrected candidate plan (duration-corrected, 56 frames per cut)

Same dialogue, characters, plates, and repository-owned guides; only `durations_s`
changed to the Content Brief Gateway default `56/24` s per turn, which reproduces the
accepted LF003 per-cut policy (WD-rij6: 56 frames/cut, 224 frames, 9.333333 s total).

- Candidate brief: `.claude/worktrees/dev-WD-42no/datasets/content_briefs/lf004-operator-dogfood-56f/brief.json` (uncommitted candidate artifact)
- `candidate_brief_hash`: `sha256:67202d3597affeab4e5edcf15a1acef2f5e88ed00950ce17ff3012f5bb0472cd`
- `canonical_plan_sha256`: `620f2ba44beb7d0bc920772c136aa0ce6f76df89acd286647c23e5a7c8015eb8`
- Replay: gateway run twice into separate temp dirs, canonical hashes identical (`620f2ba4...`).
- Clips: 4 x `frames=56`, `audio_length_frames=56`, `guide_duration_s=shot_duration_s=2.333`, `keeper_window_s=[0.0, 2.3333333333333335]`.
- Summary: `{"clip_count": 4, "planned_duration_s": 9.332, "dry_run": true, "gpu_work": false, "queue_submitted": false}`.
- Guard outcome: the candidate passes the new preflight (measured guide 2.333333 matches declared 2.333333 within 1e-6).

Reproduce with the same command as above plus `--brief <candidate brief>` and the same
`--plates` directory; then compute the canonical hash with the `canonical_sha` algorithm
already defined in `datasets/content_briefs/lf004-operator-dogfood/run/verify.py`.

### 3. Approval required (single explicit decision)

Approve canonical plan hash `620f2ba44beb7d0bc920772c136aa0ce6f76df89acd286647c23e5a7c8015eb8`
(candidate brief `sha256:67202d35...`) for exactly one governed recovery execution under
WD-h73w using the accepted 56-frame-per-cut policy, or direct an alternative
(regenerate longer guides and keep 4.458 s turns).

### 4. Required deliverables for the recovery execution

- Commit the corrected brief + plan into the repository and record brief/plan/run-ledger hashes.
- Provide a corrected verification script; the existing `run/verify.py` hard-asserts 107 frames and `planned_duration_s == 17.832`, which is specific to the defective plan.
- Execute exactly one governed render through the accepted pipeline with the three-attempt policy, all declared gates, and preserved review artifacts.

## nd_contract
status: in_progress

### evidence
- Guard rejection of the approved brief: exit 1 with the typed mismatch error and zero artifacts on main `4b99b3a`.
- Corrected candidate plan `620f2ba4...` replay-verified twice; 4 x 56 frames matching the accepted WD-rij6 policy.
- Root cause and corrective actions recorded at `docs/findings/85-lf004-guide-duration-mismatch.md` (dev-WD-42no worktree) and in WD-ssdt (delivered, accepted, merged).

### proof
- [x] Fail closed at cut 2 rather than relaxing gates.
- [x] Root cause identified and the guard that prevents recurrence is merged with green CI.
- [x] Corrected plan candidate produced, replay-verified, and hash-recorded.
- [ ] Operator approval of `620f2ba4...` (or an alternative) before any further render.
- [ ] One governed recovery execution passing every declared gate with a reviewable artifact.

## Root Cause: Declared Clip Duration vs Guide Audio Length

Cut-2's dead-letter is explained by a plan-input defect, not by seed luck alone.

| Item | Value | Source |
| --- | --- | --- |
| brief `durations_s` | `4.458333` per turn (107 frames @24fps) | `datasets/content_briefs/lf004-operator-dogfood/brief.json` |
| actual guide audio, all four turns | `2.333333` s (56 frames @24fps) | `ffprobe` on the four `audio_paths` guides |
| Content Brief Gateway default | `56.0/24.0` = 2.333 s | `predict/content_brief.py` (`DEFAULT_DURATION_S`) |
| LF003 accepted per-cut policy | 56 frames/cut; assembly 224 frames / 9.333 s | WD-rij6 |

Consequences measured on disk:

- Every 107-frame clip carries ~2.125 s of speech time with no guide content; the renderer fills it, observed as the intended line spoken twice (seed 904 `7351334145399bd4`, seed 905 `93075b7b7633289b`, both post-Whisper 0.167) or as double-exposure motion (seed 906 `cb1293c6e987f6a5`, vision `action_match` 0.1).
- `plan.json` sets `guide_duration_s := shot_duration_s` (4.458) instead of the guide's measured 2.333 s, so `services/director/renderers/policy.py::check_guide_duration()` compares two plan-declared values and passes trivially; the real audio file length is never inspected.
- `keeper_window_s` / `audio_policy.remux_window` are `[0.0, 4.458333]` although the master is 2.333 s long.
- Cut 1 also required two retries before passing, i.e. every LF004 cut hit the same mismatch.

Nothing was relaxed: no gate, no retry policy, no artifact. No fourth render was started.

## nd_contract
status: in_progress

### evidence
- Root cause recorded above with measured hashes/durations; write-up at `docs/findings/85-lf004-guide-duration-mismatch.md` in the `dev-WD-42no` worktree.
- Cut 1 `done`; cut 2 `dead_letter` after three `qc_gate` failures; cuts 3/4 `pending` behind cut 2.
- Approved plan hash `70280fdcd6fb7f54bc4f7027e03de54e4897178dd41adcf92ef31bd347d7bd86` is the only hash approved so far.

### proof
- [x] Fail closed at cut 2 rather than relaxing Whisper/vision/retry gates.
- [x] Root cause identified from disk evidence (guide length vs declared duration).
- [ ] Operator decision required before any further render: approve a corrected plan hash (gateway default 56/24 s per turn, matching the LF003-accepted policy) for one governed recovery execution, or authorize re-seeding the current 107-frame plan.
- [ ] Corrected render passes every declared gate and yields the reviewable artifact.

## Fail-Closed LF004 Boundary Evidence

The approved execution did not proceed to cuts 3/4. Cut 2 exhausted the accepted three-attempt QC retry policy and is durable-queue dead-lettered:

- Seed 904 raw SHA-256 `7351334145399bd4b26454760e97869da412e3015d441ea31516365c4ad3b397`: post-Whisper score 0.167; transcript included hallucinated preceding dialogue.
- Seed 905 raw SHA-256 `93075b7b7633289b2f956fb23d4fe40061650c140aff9f6af2195daa6b7d65ff`: post-Whisper score 0.167; intended line repeated.
- Seed 906 raw SHA-256 `cb1293c6e987f6a5224b3649c27392b9f75cbec769b4a1ed1ad1f944c64e71de`: Whisper pre/post passed (post score 1.0), but identity/action vision rejected ghosting/double-exposure artifacts (`action_match=0.1`, `speaker_attribution=0.1`).
- Queue states: cut 1 `done`; cut 2 `dead_letter` after 3 `qc_gate` failures; cuts 3/4 remain `pending` behind cut 2.
- Contact sheets and hashes: `datasets/runs/provenance/lf004-operator-dogfood-20260920/cut2-deadletter-review/`.
- Independent seed-905 visual re-judge passed identity/action but observed the speaker mouth closed; it is not a substitute because post-Whisper and AV gates remain failed.

No gate was relaxed and no fourth render was started. Continuing with seed 907 would exceed the current approved retry policy and needs a new explicit operator-approved recovery story.

## nd_contract
status: in_progress

### evidence
- Durable queue and attempt failure records above; dead-letter review artifacts on disk.

### proof
- [x] Fail closed at cut 2 rather than relaxing Whisper/vision/retry gates.
- [ ] Operator decision required before any additional render or recovery story.

## Operator Render Approval

Approved UTC: 2026-09-20T20:47:21Z
Operator response: yes
Exact canonical plan SHA-256: 70280fdcd6fb7f54bc4f7027e03de54e4897178dd41adcf92ef31bd347d7bd86
Authorization: exactly one governed LF004 production execution through the accepted Wangp pipeline. This approval does not authorize a second independent run, live-hook changes, or unrelated work.

## History
- 2026-09-20T19:48:19Z dep_added: blocked_by WD-z46c
- 2026-09-20T19:48:47Z dep_added: blocked_by WD-rb1f
- 2026-09-20T19:48:47Z dep_added: blocked_by WD-rj6e
- 2026-09-20T20:14:46Z dep_removed: was_blocked_by WD-z46c
- 2026-09-20T20:47:21Z status: open -> in_progress
- 2026-09-20T20:47:21Z auto-follows: linked to predecessor WD-z46c
- 2026-09-20T20:47:21Z claimed by dev-WD-42no
- 2026-09-20T23:53:58Z dep_added: blocked_by WD-ssdt
- 2026-09-21T00:25:02Z dep_removed: was_blocked_by WD-ssdt

## Links
- Parent: [[WD-h73w]]
- Blocked by: [[WD-rb1f]], [[WD-rj6e]]
- Was blocked by: [[WD-z46c]], [[WD-ssdt]]
- Follows: [[WD-z46c]]

## Comments
