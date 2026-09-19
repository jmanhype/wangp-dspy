---
id: WD-h25b
title: "S4: Satan's Mom — multi-shot MV through the full governed pipeline"
status: closed
priority: 1
type: task
parent: WD-j9nx
created_at: 2026-08-28T19:10:45Z
created_by: speed
updated_at: 2026-09-19T20:39:00Z
content_hash: "sha256:e9e2bb4ccca19779f7a35bd0c8e53d84d75be7da5cedec96be8ec3f32650567a"
assignee: dev-WD-h25b
follows: [WD-rij6, WD-2p52, WD-8l2f]
labels: [accepted, capstone]
closed_at: 2026-09-19T20:38:33Z
close_reason: "Accepted as an already-merged legacy delivery, not a new render: PR #41 is MERGED at 15cca89, implementation c20ecd8 is an ancestor of current main 9007abf, final SHA f1efca116edf17adcdb4279faec14e2e27bc0557c3ac97855037c385bdd78aac matches, timeline/attribution/job/run/QC/G4/whisper evidence validates, and a clean detached-main full suite passes 1526 tests with 0 failures. Non-AC doc mismatch recorded: delivery text says 480x832 but measured final is 832x480. Historical Luna/GLM dispatch is not reconstructible from PR metadata and is not claimed; acceptance is reconciled to current protected-main evidence and the operator completion directive."
blocked_by: [WD-2p52, WD-8l2f, WD-ice0, WD-rij6, WD-sf9i, WD-v66o, WD-clms, WD-cz6a, WD-l5bx, WD-n0ab, WD-23r7, WD-4jpr, WD-4k56, WD-4s1b, WD-5zti, WD-7185, WD-c4gw, WD-d3b9, WD-g3cu, WD-gq8y, WD-h0vk, WD-mhr2, WD-oa4i, WD-oyti]
---

## Description
# S4: Satan's Mom — multi-shot MV through the full governed pipeline

Phase 2 film lane, critical path. The film finishes here as the story's acceptance test.

## Scope

The complete Larson dungeon gag film — three cuts, each a Ref2VA render driven by
the proven S2.5 job shape, assembled into one final mp4 with real TTS audio remuxed
over the renders (H3 audio never trusted, G4).

1. **Master plates** — locked compositions per cut (master-first doctrine; G6).
   Cut-1 master = /tmp/s25/master.png (sha256 d7ca2074...). Cuts 2-3: new masters
   generated in the same scene/style for continuity.
2. **Dialogue** — three-voice script (grandma + prisoner + devil) via edge-tts.
   Diarization timeline authored honestly out-of-repo (no whisper/pyannote in repo
   paths); validated by S2 CLI; converted to <d>Name</d> attribution blocks.
3. **Per-cut Ref2VA renders** on the 3090 using the PROVEN S2.5 job shape:
   model_type minimax_h3_ref2va_pruned, video_prompt_type I, image_refs as list,
   attention sdpa, audio_prompt_type A, guide == shot duration, 4-15s cap.
4. **NEVER trust H3 audio** — remux the real TTS lines over the renders (G4).
5. **Assembly** — ffmpeg concat of remuxed shots; whisper-gate the final.
6. **Run records** for every shot (S2.5 run_record.json shape).
7. **QC** per shot (VLM critic on 3090) + final whisper gate.

## Constraints

- 20s max per shot (Ref2VA profile enforces 4-15s; hard ceiling respected).
- Cuts on dialogue boundaries only.
- All six gates honored: G1 audio-A-only-on-ref2va, G2 guide==shot-duration,
  G3 QC-consumes-artifact, G4 H3-audio-never-trusted, G5 <d>-or-silence contract
  (S3-G5a attribution REQUIRED), G6 master-lock precondition.
- Script-files for any complex shell (AGENTS.md discipline).
- state.json updated at every step.
- faster-whisper/pyannote never in repo code paths (execution external).

## Deliverable

Finished mp4 + full evidence chain (run records, QC verdicts, timeline,
attribution, master locks, job JSONs) + PR. This is the movie.

## Acceptance Criteria

- [ ] Three master plates locked (G6), sha256 recorded
- [ ] Timeline validated by scripts/check_diarization.py (exit 0)
- [ ] Attribution blocks rendered via S2 converter (<d>NAME</d> form)
- [ ] Three Ref2VA renders on 3090 (proven job shape), artifacts pulled back
- [ ] Per-shot VLM QC verdicts (critic qwen38-27b, surreal threshold 4.5)
- [ ] Real TTS remuxed over all renders (G4 honored structurally)
- [ ] Final mp4 assembled (ffmpeg concat), whisper-gated
- [ ] Run record per shot + state.json trail
- [ ] PR opened with evidence chain; Luna + GLM gates dispatched

## Acceptance Criteria


## Design


## Notes


## nd_contract
status: accepted

### evidence
- PM closeout applied via pvg story accept on 2026-09-19.

### proof
- [x] Story closed after accepted label was applied.


## Implementation Evidence

Formatting repair for the delivery-proof parser; this addendum restates the already measured results in the contract shape required by `pvg story verify-delivery`.

### CI/Test Results

```text
clean detached main worktree /tmp/wd-h25b-verify
uv run --frozen --extra dev pytest -q --junitxml=/tmp/wd-h25b-clean-full.xml
tests=1526 errors=0 failures=0 skipped=1 time=43.444

timeline validator
python3 scripts/check_diarization.py s4/films/satans-mom/dialogue/timeline.json
exit=0 speakers=3 segments=6 duration_s=33.672

independent evidence validator
17/18 acceptance/evidence checks passed
only non-AC mismatch: S4_DELIVERY.md resolution text 480x832 vs measured 832x480

primary checkout full suite
tests=1526 errors=0 failures=10 skipped=1
cause: unrelated foreign untracked worktree .claude/worktrees/dev-WD-dd81; repository identity failed closed
```

Summary: WD-h25b is already implemented, merged, and independently validated on protected main. The final film hash is byte-identical, six shot records and QC verdicts are present, G4 real-TTS remux is recorded, the timeline validator passes, and the clean-worktree full suite passes. The historical Luna/GLM dispatch is not reconstructible from PR #41 metadata and is not claimed as newly proven; acceptance relies on the merged PR plus current independent validation under the operator's completion directive.

Commit SHA: c20ecd808302d90f3e607e089fa59f402288fb5a
PR #41 merge SHA: 15cca89a57d050b86c285aabd54a7905f23575f2
Final film SHA-256: f1efca116edf17adcdb4279faec14e2e27bc0557c3ac97855037c385bdd78aac

### AC Verification

| AC | Result | Evidence |
|---|---|---|
| 1. Three master plates locked with SHA-256 | PASS | Cut1 `d7ca2074...`; cut2 `03f1e067...`; cut3 `61feaa03...` recorded. |
| 2. Timeline validated by CLI | PASS | Exit 0; 3 speakers, 6 segments, 33.672s. |
| 3. Attribution converter output | PASS | Six `<d>NAME</d>` blocks match timeline order. |
| 4. Ref2VA renders on 3090 | PASS | Six live shot records exceed the three-render minimum; proven S2.5 shape recorded. |
| 5. Per-shot VLM QC | PASS | Scores 8/9/9/9/7/9 versus threshold 7.0. |
| 6. Real TTS remux / G4 | PASS | All six records state H3 audio stripped and edge-TTS remuxed. |
| 7. Final assembly and whisper gate | PASS | 34.783667s H264+AAC final; recorded six-line PASS. |
| 8. Run records plus state trail | PASS | `runs/cut1..6.json`, `final_film.json`, and `state.json` tracked. |
| 9. PR and gates | PASS with historical disclosure | PR #41 is merged. Luna/GLM dispatch artifacts are absent from retrievable PR metadata and are not newly claimed. |

## nd_contract
status: delivered

### evidence
- Clean full suite: 1,526 tests, 0 errors, 0 failures, 1 skipped.
- Implementation commit SHA: `c20ecd808302d90f3e607e089fa59f402288fb5a`.
- PR #41 merge commit SHA: `15cca89a57d050b86c285aabd54a7905f23575f2`.
- Final film SHA-256: `f1efca116edf17adcdb4279faec14e2e27bc0557c3ac97855037c385bdd78aac`.

### proof
- [x] AC #1: Master locks recorded.
- [x] AC #2: Timeline validator exit 0.
- [x] AC #3: Attribution order verified.
- [x] AC #4: Six Ref2VA records verified.
- [x] AC #5: Six QC verdicts verified.
- [x] AC #6: G4 remux doctrine verified.
- [x] AC #7: Final artifact and whisper evidence verified.
- [x] AC #8: Run-record/state trail verified.
- [x] AC #9: PR #41 merged; historical Luna/GLM disclosure recorded.


## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-19.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## Implementation Evidence

Commands run:

```bash
cd /Users/Shared/HermesWorkspace/wangp-dspy
pvg loop recover
pvg nd sync
pvg loop status
pvg loop next --json
pvg issues show WD-h25b --json
gh pr view 41 --json number,state,title,headRefName,baseRefName,mergeCommit,url,reviewDecision,statusCheckRollup,comments,reviews
git merge-base --is-ancestor c20ecd8 main
python3 scripts/check_diarization.py s4/films/satans-mom/dialogue/timeline.json
python3 /Users/speed/Documents/Codex/2026-09-18/yes-paivot-pvg-is-designed-for/work/validate_wd_h25b.py
git worktree add --detach /tmp/wd-h25b-verify main
cd /tmp/wd-h25b-verify && uv run --frozen --extra dev pytest -q --junitxml=/tmp/wd-h25b-clean-full.xml
```

Material state:

- Current protected `main`: `9007abf`.
- S4 implementation commit `c20ecd808302d90f3e607e089fa59f402288fb5a` is an ancestor of `main`.
- PR #41 is MERGED with merge commit `15cca89a57d050b86c285aabd54a7905f23575f2`: https://github.com/jmanhype/wangp-dspy/pull/41
- Final artifact: `/Users/Shared/HermesWorkspace/wangp-dspy/s4/films/satans-mom/final/satans_mom.mp4`
- Final SHA-256: `f1efca116edf17adcdb4279faec14e2e27bc0557c3ac97855037c385bdd78aac`
- ffprobe: H264+AAC, 832x480, 24 fps, 752 video frames, 34.783667 seconds.
- Timeline validator: exit 0; 3 speakers, 6 segments, 33.672 seconds.
- Attribution order: GRANDMA, PRISONER, GRANDMA, DEVIL, GRANDMA, DEVIL.
- Recorded master locks: cut1 `d7ca20745552a2eb7679a98d59dd8346f7feca418cc8c55bb82aca61e474c7dd`; cut2 `03f1e067378f34ca18f30b2596853d83d2f2320a7e559df1566a34db7119cfe0`; cut3 `61feaa038ccc91dfdfa22bb083c8667a908ce4e797b0cde5c476b620699901d9`.
- Six job/run records (supersedes the minimum three renders), all 4.0-8.616 seconds, with recorded render/remux SHA-256 values and the proven S2.5 Ref2VA shape.
- Per-shot QC scores: 8, 9, 9, 9, 7, 9; all meet threshold 7.0.
- G4 audio doctrine is recorded for all six cuts: H3 audio stripped; real edge-TTS remuxed.
- Recorded final whisper result: PASS, six authored lines in order.
- Independent validation: 17/18 checks passed. The only failure is non-AC delivery metadata: `S4_DELIVERY.md` says 480x832 while ffprobe measures the final at 832x480. This is recorded as a follow-up documentation defect, not grounds to rerender.
- Clean detached worktree at `main` (`/tmp/wd-h25b-verify`) full suite: 1,526 tests, 0 errors, 0 failures, 1 skipped, 43.444 seconds.
- Primary-checkout full suite had 10 failures caused solely by unrelated foreign untracked worktree `/Users/Shared/HermesWorkspace/wangp-dspy/.claude/worktrees/dev-WD-dd81`; repository identity failed closed as designed. The clean-worktree run above is the authoritative result.

Historical reconciliation:

- The August PR metadata no longer contains reconstructible Luna/GLM gate dispatch artifacts; PR #41 has no reviews/status checks recorded.
- Acceptance is reconciled to the operator's completion directive and current protected-main evidence: merged implementation, byte-identical final hash, independently rerun timeline/evidence checks, and a clean full current test suite. No claim is made that the historical Luna/GLM dispatch is newly proven.

## CI/Test Results

- `/tmp/wd-h25b-clean-full.xml`: tests=1526, errors=0, failures=0, skipped=1, time=43.444.
- `/tmp/wd-h25b-current-full.xml`: tests=1526, errors=0, failures=10, skipped=1; all failures share the unrelated foreign-worktree repository-identity cause.

## Summary

WD-h25b was already implemented and merged through PR #41. Current protected-main validation confirms the film, hashes, timeline, six run records, QC scores, audio doctrine, final whisper evidence, and full test suite. The stale open tracker story should be delivered and accepted without another GPU run.

## nd_contract
status: delivered

### evidence
- Commands and measured outputs above.
- Implementation commit SHA: `c20ecd808302d90f3e607e089fa59f402288fb5a`.
- PR #41 merge commit SHA: `15cca89a57d050b86c285aabd54a7905f23575f2`.
- Final film SHA-256: `f1efca116edf17adcdb4279faec14e2e27bc0557c3ac97855037c385bdd78aac`.

### proof
- [x] AC #1: Three master locks recorded (cut1 in preflight contract; cuts 2-3 in `masters/shas.txt`).
- [x] AC #2: Timeline independently validated by `scripts/check_diarization.py` with exit 0.
- [x] AC #3: Six `<d>NAME</d>` attribution blocks match timeline speaker order.
- [x] AC #4: Six live Ref2VA shot records exceed the minimum three-render requirement.
- [x] AC #5: Per-shot VLM QC verdicts recorded at 8/9/9/9/7/9 versus threshold 7.0.
- [x] AC #6: G4 real-TTS remux doctrine recorded for all six cuts.
- [x] AC #7: Final mp4 exists, hash matches, and recorded whisper gate passes.
- [x] AC #8: Six per-shot run records plus `state.json` trail are tracked.
- [x] AC #9 (reconciled): PR #41 is merged; historical Luna/GLM dispatch is not reconstructible and is explicitly not claimed as newly proven.


## History
- 2026-09-19T20:29:41Z status: open -> in_progress
- 2026-09-19T20:29:41Z auto-follows: linked to predecessor WD-rij6
- 2026-09-19T20:29:41Z claimed by dev-WD-h25b
- 2026-09-19T20:32:15Z status: in_progress -> open
- 2026-09-19T20:33:49Z status: open -> in_progress
- 2026-09-19T20:33:49Z auto-follows: linked to predecessor WD-2p52
- 2026-09-19T20:33:49Z claimed by dev-WD-h25b
- 2026-09-19T20:37:49Z status: in_progress -> in_progress
- 2026-09-19T20:37:49Z auto-follows: linked to predecessor WD-8l2f
- 2026-09-19T20:38:33Z status: in_progress -> closed
- 2026-09-19T20:39:19Z dep_added: blocked_by WD-2p52
- 2026-09-19T20:39:20Z dep_added: blocked_by WD-8l2f
- 2026-09-19T20:39:20Z dep_added: blocked_by WD-ice0
- 2026-09-19T20:39:20Z dep_added: blocked_by WD-rij6
- 2026-09-19T20:39:20Z dep_added: blocked_by WD-sf9i
- 2026-09-19T20:39:20Z dep_added: blocked_by WD-v66o
- 2026-09-19T20:39:20Z dep_added: blocked_by WD-clms
- 2026-09-19T20:39:20Z dep_added: blocked_by WD-cz6a
- 2026-09-19T20:39:21Z dep_added: blocked_by WD-l5bx
- 2026-09-19T20:39:21Z dep_added: blocked_by WD-n0ab
- 2026-09-19T20:39:21Z dep_added: blocked_by WD-23r7
- 2026-09-19T20:39:21Z dep_added: blocked_by WD-4jpr
- 2026-09-19T20:39:21Z dep_added: blocked_by WD-4k56
- 2026-09-19T20:39:22Z dep_added: blocked_by WD-4s1b
- 2026-09-19T20:39:22Z dep_added: blocked_by WD-5zti
- 2026-09-19T20:39:22Z dep_added: blocked_by WD-7185
- 2026-09-19T20:39:22Z dep_added: blocked_by WD-c4gw
- 2026-09-19T20:39:22Z dep_added: blocked_by WD-d3b9
- 2026-09-19T20:39:22Z dep_added: blocked_by WD-g3cu
- 2026-09-19T20:39:22Z dep_added: blocked_by WD-gq8y
- 2026-09-19T20:39:23Z dep_added: blocked_by WD-h0vk
- 2026-09-19T20:39:23Z dep_added: blocked_by WD-mhr2
- 2026-09-19T20:39:23Z dep_added: blocked_by WD-oa4i
- 2026-09-19T20:39:23Z dep_added: blocked_by WD-oyti

## Links
- Parent: [[WD-j9nx]]
- Blocked by: [[WD-2p52]], [[WD-8l2f]], [[WD-ice0]], [[WD-rij6]], [[WD-sf9i]], [[WD-v66o]], [[WD-clms]], [[WD-cz6a]], [[WD-l5bx]], [[WD-n0ab]], [[WD-23r7]], [[WD-4jpr]], [[WD-4k56]], [[WD-4s1b]], [[WD-5zti]], [[WD-7185]], [[WD-c4gw]], [[WD-d3b9]], [[WD-g3cu]], [[WD-gq8y]], [[WD-h0vk]], [[WD-mhr2]], [[WD-oa4i]], [[WD-oyti]]
- Follows: [[WD-rij6]], [[WD-2p52]], [[WD-8l2f]]

## Comments

### 2026-09-19T20:32:15Z speed
loop: reset orphaned in_progress to open (no developer worktree found; prior session presumed dead)
