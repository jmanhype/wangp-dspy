---
id: WD-rij6
title: "LF003 full-gate four-cut chain-depth probe"
status: closed
priority: 0
type: feature
parent: WD-j9nx
created_at: 2026-09-19T13:07:14Z
created_by: speed
updated_at: 2026-09-19T20:28:48Z
content_hash: "sha256:b80916f9bd464d0fbfc4cc59b4447b8f88479d96c764a88c3be795f2d2f6d573"
follows: [WD-ice0, WD-clms, WD-sf9i, WD-8l2f, WD-2p52, WD-v66o]
was_blocked_by: [WD-sf9i, WD-8l2f, WD-2p52]
assignee: dev-WD-rij6
labels: [accepted]
closed_at: 2026-09-19T20:28:47Z
close_reason: "Accepted: independently reran targeted LF003/vision/executor tests, full 1,526-test suite, manifest/content-hash checks, queue/ledger inspection, ffprobe, contact-sheet review, and staged-secret scan. Four fresh cuts passed all gates; two governed rejections are preserved; assembly is repository-owned and explicitly operator_review_pending."
---

## Description
## Context (Embedded)

This is the operator-authorized next film-lane story after acceptance of the
LF003 “Borrowed Sunrise” two-cut candidate.

### Accepted entry artifact

- Repository baseline for this story: `35201a11bb1839fd5ba83739eed690227aabe199`.
- Run ID: `lf003-two-cut-vibevoice-rhostrong-20260918`.
- Premise: `lf-003`.
- Assembled artifact:
  `datasets/runs/pull/lf003-two-cut-vibevoice-rhostrong-20260918/assembled.mp4`.
- Assembled SHA-256:
  `1c1184fbcf504ffbc4657926e13d20c6dd039e41dcf54bfe6e61919032b21ad`.
- Acceptance bundle SHA-256:
  `df9012a3dcd2819d73ccacc9f7dbf9754c4a298a58869079424b46c611bdb361`.
- Source run records:
  - planned record SHA-256:
    `4c08dfe429499fc38bd20d0e9796b4d4d9ae06c4cd417bc1748b3b8c3969e502`
  - needs-review record SHA-256:
    `92180c776a820a58a3f725aa9e92308aba84f67c4dd1c1585853ba2537cbe996`
- Operator authorization: on 2026-09-19 the operator replied
  `i agree to everything you may continue on all fronts` after viewing the
  candidate. Treat this as acceptance of the two-cut entry artifact and
  authorization for the four-cut probe.

### Why this story exists

The original six-cut contract remains unmet. Historical depth-five evidence
predates the corrected native conditioning path. The current two-cut LF003 run
is the first mechanically eligible full-gate candidate under the current stack.
The next safe increment is exactly four cuts—not six and not latent carry yet.

## USER INTENT

Prove whether the current native-H3, VibeVoice, full-gate pipeline can preserve
identity, composition, speaker attribution, and audiovisual sync through cut 4
without changing premise, cast, style, duration policy, or QC thresholds.

## Goal

Produce a fresh, clean-checkout, no-prefix, one-queue, one-ledger four-cut
LF003 run through the repository-owned acceptance path, then submit the final
assembled artifact for operator review.

## Fixed inputs and constraints

1. Start from a clean checkout at a recorded commit. Do not use
   `completed_prefix`.
2. Use one durable job database and one append-only run ledger for all four
   cuts.
3. Keep fixed:
   - premise `lf-003`;
   - Tess and Rho cast/plates;
   - current style anchor;
   - native H3 audio carrier;
   - 56-frame/grid-aligned duration policy;
   - repository-owned VibeVoice supply;
   - current Ref2VA model and continuation profile.
4. Chain each cut from the predecessor’s decoded final frame through the
   existing repository seam.
5. Every cut must pass:
   - pre- and post-render Whisper at the production bar;
   - identity/composition vision;
   - three-frame mouth-box consensus;
   - blocking SyncNet audiovisual alignment;
   - conditioning and provenance checks.
6. Preserve every rejected attempt with its gate evidence. Do not weaken a
   threshold and do not reuse a deterministic replay as a new attempt.
7. Assemble all four gated cuts with repository-owned ffmpeg assembly.
8. Record the final artifact, every cut, every chain frame, bundle, jobs
   database, ledger, QC evidence, and repository identity with SHA-256 hashes.
9. If cut 3 or cut 4 fails continuity, create a separate numbered finding using
   those exact artifacts. Do not infer that latent carry is required from the
   older pre-correction runs.

## OUT OF SCOPE

- Six-cut acceptance: this story only probes depth four.
- Latent save/load or first-frame-preservation implementation: only a separate
  finding may be filed if current-gate artifacts justify it.
- Changing the accepted two-cut artifact or its history.
- Changing cast, premise, style, model, duration policy, Whisper/vision/SyncNet
  thresholds, or assembly environment.
- Direct `wgp` calls or side scripts that bypass `run_bundle()`,
  `render_for_job()`, repository staging, QC, or ledger emission.

## DIFF BUDGET

- Expected: run assets/evidence and at most small bundle/fixture adjustments.
- Source-code changes are not intended. If a production gap blocks the governed
  path, stop and file a separate finding rather than expanding this story.

## Boundary Map

PRODUCES:
- `datasets/runs/provenance/lf003-four-cut-fullgate-YYYYMMDD/manifest.json`
  -> complete content-addressed run manifest
- `datasets/lf003-four-cut-fullgate-YYYYMMDD.jobs.db` -> durable four-job queue
- `datasets/lf003-four-cut-fullgate-YYYYMMDD.runs.jsonl` -> append-only ledger
- `datasets/runs/pull/lf003-four-cut-fullgate-YYYYMMDD/assembled.mp4`
  -> operator-review candidate
- per-cut raw/remux videos, chain frames, QC evidence, and hashes

CONSUMES:
- existing: `scripts/run_acceptance.py` -> `run_bundle(bundle_path: str | Path,
  *, db_path: str | Path | None = None, ledger_path: str | Path | None = None,
  output_path: str | Path | None = None, host=None, vision_judge=None) -> dict`
- existing: `host/wangp_adapter.py` -> `WanGPAdapter.render_for_job(job:
  Mapping, **kwargs)` repository render seam
- existing: `predict/vibevoice.py` -> repository-owned dialogue supply/provenance
- existing: LF003 premise, plates, style reference, and accepted Rho/Tess inputs

## Acceptance Criteria

1. Operator acceptance of the prior two-cut artifact is recorded in the new
   provenance directory with the exact artifact hash, source ledger hashes,
   verbatim authorization message, and UTC timestamp.
2. A clean-checkout run records repository commit and clean-tree identity before
   execution.
3. Four newly rendered cuts execute through the repository queue and
   `render_for_job()` with no completed-prefix reuse.
4. Each cut preserves its intended speaker and chains from the predecessor’s
   decoded final frame.
5. Each cut passes pre/post Whisper, identity/composition vision, mouth-box
   consensus, SyncNet, and provenance gates.
6. Every rejected attempt and gate reason is preserved and hashed.
7. The final four-cut assembly is produced through the repository-owned assembly
   path and has codec/probe metadata and SHA-256 recorded.
8. The final status is submitted as `mechanically_eligible_operator_review_pending`
   unless a gate fails; no operator acceptance is claimed automatically.
9. If continuity fails at cut 3 or 4, a separate finding is filed with exact
   artifacts and no speculative latent-carry implementation occurs in this story.
10. The run evidence is committed or staged as repo-owned artifacts, with no
    secrets, remote-only paths, or unhashable inputs.

## Testing Requirements

- Live GPU integration is mandatory: four fresh Ref2VA renders through the
  repository path.
- No model-free substitute may claim acceptance.
- Verify all artifact hashes after pullback.
- Run the applicable evidence-preservation tests targeting the new artifacts.
- Run `git diff --check`.

## Skills To Use

- `pvg` for story governance.
- `video-render-qc` for final artifact/probe/contact-sheet inspection.

## Delivery Requirements

- Paste exact acceptance/queue commands and summaries.
- Provide cut-by-cut gate table.
- Provide final hashes and probe metadata.
- Include an AC verification table.
- Update the authoritative `nd_contract` through the pvg delivery workflow.

## nd_contract
status: new

### evidence
- Prior two-cut artifact was displayed to the operator and authorized with
  “i agree to everything you may continue on all fronts” on 2026-09-19.

### proof
- [ ] Pending implementation

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

Commands run:

```bash
cd /Users/Shared/HermesWorkspace/wangp-dspy/.claude/worktrees/dev-WD-rij6
uv run --frozen --extra dev pytest -q tests/test_lf003_fourcut_retry_success.py tests/test_lf003_fourcut_gate_failure.py tests/test_lf003_fixture_manifest.py tests/test_av_sync_gate.py tests/test_lf003_fullgate_bundle.py tests/test_lf003_strict_vibevoice_bundle.py tests/test_lf003_vibevoice_bundle.py tests/test_lf003_rhostrong_film_evidence.py tests/test_vision_judge.py tests/test_local_qwen_vision_judge.py tests/test_ref2va_runtime.py tests/test_jobs_executor.py -rs
uv run --frozen --extra dev pytest -q --junitxml=/tmp/wd-rij6-full.xml
ffprobe -v error -show_format -show_streams -of json datasets/runs/pull/lf003-four-cut-fullgate-retry-20260919/assembled.mp4
git diff --check
git diff --cached --check
```

### CI/Test Results

```text
targeted LF003/vision/executor suite: 107 passed, 0 skipped
full suite JUnit: tests=1526 errors=0 failures=0 skipped=1
final manifest test: 5 passed
git diff checks: PASS
staged text secret scan: PASS (56 files)
```

Summary: the governed four-cut retry completed from clean commit 52654ff with no completed_prefix, one durable queue, one append-only ledger, and all four cuts freshly rendered through the repository path. Cut 2 required one governed SyncNet reseed and cut 4 required one governed post-Whisper reseed; both rejections remain preserved. All four final cuts passed pre/post Whisper, identity vision, three-frame mouth localization, and blocking SyncNet. Repository-owned assembly is 224 frames, 704x576, 24 fps, 9.333333 seconds, and status remains mechanically_eligible_operator_review_pending.

Commit SHA: 5989810

### AC Verification

| AC | Result | Evidence |
|---|---|---|
| 1. Prior operator acceptance and exact hashes recorded | PASS | Retry manifest references preserved operator acceptance. |
| 2. Clean-checkout identity before execution | PASS | `pre-execution-identity.json`, commit 52654ff, clean tree. |
| 3. Four fresh renders through queue/render_for_job, no prefix | PASS | Queue has four done jobs; bundle has no completed_prefix. |
| 4. Correct speakers and predecessor chaining | PASS | Tess/Rho/Tess/Rho; three chain frames hashed. |
| 5. Every cut passes all gates | PASS | Manifest and queue gate table. |
| 6. Every rejection preserved and hashed | PASS | Seed-906 cut2 SyncNet and seed-906 cut4 Whisper evidence committed. |
| 7. Repository-owned four-cut assembly | PASS | Assembled SHA 5a8676922d16c954d579c096c5eb9891ce33758ef1ebda27e98f03c632422063. |
| 8. Honest operator-review status | PASS | `mechanically_eligible_operator_review_pending`; verdict `not_requested`. |
| 9. Continuity failure handled separately | PASS | Prior Finding 84 preserved; successful current-gate retry did not infer latent carry. |
| 10. Evidence committed, hashable, no secrets | PASS | 80-file evidence commit 5989810; text secret scan PASS. |


## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-19.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## nd_contract
status: rejected

### evidence
- PM rejection applied via pvg story reject on 2026-09-19.

### proof
- [ ] Story requires another developer delivery before it can be accepted.


## Implementation Evidence

Commands run:

```bash
cd /Users/Shared/HermesWorkspace/wangp-dspy/.claude/worktrees/dev-WD-rij6
git diff --check
git diff --cached --check
/Users/Shared/HermesWorkspace/wangp-dspy/.venv/bin/python -m py_compile tests/test_lf003_fourcut_gate_failure.py
/Users/Shared/HermesWorkspace/wangp-dspy/.venv/bin/python -m pytest -q tests/test_lf003_fourcut_gate_failure.py tests/test_lf003_rhostrong_film_evidence.py tests/test_lf003_rhostrong_bundle.py tests/test_lf003_fullgate_bundle.py
/Users/Shared/HermesWorkspace/wangp-dspy/.venv/bin/python -m pytest -q tests/test_vibevoice.py
```

Independent coordinator results:

- Formatting checks: exit 0.
- Targeted evidence tests: 9/9 passed.
- VibeVoice suite: 67/67 passed.
- Confirmed no `assembled.mp4` exists for the failed four-cut run.
- Manifest status: `gate_failed_cut3`.
- Cut 3 failed because the vision result lacked three required `speaker_mouth_bboxes`; cut 4 remained pending.
- All 77 evidence/input/test files were committed for preservation on story branch `story/WD-rij6`.

### CI/Test Results

```text
9 targeted evidence tests passed
67 VibeVoice tests passed
git diff --check: PASS
git diff --cached --check: PASS
```

Summary: the four-cut probe executed as a governed fail-closed experiment. Cuts 1–2 passed all gates; cut 3 passed pre/post Whisper but failed the required three-frame mouth-box evidence contract; cut 4 was not rendered and no four-cut assembly was produced. Finding 84 and all rejection evidence were preserved.

Commit SHA: 8db5339

### AC Verification

| AC | Result | Evidence |
|---|---|---|
| 1. Prior operator acceptance recorded | PASS | `operator-acceptance.json` and manifest. |
| 2. Clean-checkout identity | PASS | `pre-execution-identity.json`. |
| 3. Four fresh renders / no prefix | FAIL | Three rendered; cut 4 pending after cut 3 gate failure. |
| 4. Speaker and predecessor chaining | PARTIAL/FAIL | Cuts 1–3 chained; cut 4 not rendered. |
| 5. Every cut passes every gate | FAIL | Cut 3 lacks three mouth boxes; SyncNet not run. |
| 6. Preserve rejected attempts/evidence | PASS | Two infrastructure rejections and terminal gate failure preserved. |
| 7. Four-cut assembly | FAIL / correctly not attempted | No assembled artifact exists. |
| 8. Honest status/no automatic acceptance | PASS | `gate_failed_cut3`; operator verdict `not_requested`. |
| 9. Separate continuity finding if cut 3/4 fails | PASS | Finding 84 filed. |
| 10. Evidence staged/hashable/no secrets | PASS | 77 files committed and targeted evidence tests pass. |


## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-19.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## History
- 2026-09-19T13:07:35Z status: open -> in_progress
- 2026-09-19T13:07:35Z auto-follows: linked to predecessor WD-ice0
- 2026-09-19T13:07:35Z claimed by dev-WD-rij6
- 2026-09-19T14:57:39Z status: in_progress -> in_progress
- 2026-09-19T14:57:39Z auto-follows: linked to predecessor WD-clms
- 2026-09-19T14:59:28Z status: in_progress -> open
- 2026-09-19T14:59:28Z released by speed
- 2026-09-19T15:01:26Z dep_added: blocked_by WD-sf9i
- 2026-09-19T15:02:12Z status: open -> deferred
- 2026-09-19T15:35:08Z dep_removed: was_blocked_by WD-sf9i
- 2026-09-19T16:33:09Z dep_added: blocked_by WD-8l2f
- 2026-09-19T16:52:14Z dep_removed: was_blocked_by WD-8l2f
- 2026-09-19T16:58:55Z dep_added: blocked_by WD-2p52
- 2026-09-19T17:23:44Z dep_removed: was_blocked_by WD-2p52
- 2026-09-19T17:24:39Z status: deferred -> open
- 2026-09-19T17:24:53Z status: open -> in_progress
- 2026-09-19T17:24:53Z auto-follows: linked to predecessor WD-sf9i
- 2026-09-19T17:24:53Z auto-follows: linked to predecessor WD-8l2f
- 2026-09-19T17:24:53Z auto-follows: linked to predecessor WD-2p52
- 2026-09-19T17:24:53Z claimed by dev-WD-rij6
- 2026-09-19T20:27:58Z status: in_progress -> in_progress
- 2026-09-19T20:27:58Z auto-follows: linked to predecessor WD-v66o
- 2026-09-19T20:28:47Z status: in_progress -> closed

## Links
- Parent: [[WD-j9nx]]
- Was blocked by: [[WD-sf9i]], [[WD-8l2f]], [[WD-2p52]]
- Follows: [[WD-ice0]], [[WD-clms]], [[WD-sf9i]], [[WD-8l2f]], [[WD-2p52]], [[WD-v66o]]

## Comments

### 2026-09-19T14:59:28Z speed
EXPECTED: A governed four-cut run with all cuts passing full gates and a final assembled operator-review candidate. DELIVERED: A valid fail-closed probe and preserved evidence, but only cuts 1-2 passed; cut 3 lacked three speaker_mouth_bboxes, cut 4 was not rendered, and no four-cut assembly exists. GAP: WD-rij6 acceptance is not met. FIX: Keep story branch 8db5339 as authoritative failure evidence; handle Finding 84 in its own story before retrying depth four. Do not weaken gates or infer latent carry.
