---
id: WD-clms
title: "S2.5: thin vertical slice — one real e2e render through the full stack"
status: in_progress
priority: 1
type: task
labels: [film-lane, vertical-slice, e2e, gpu, discovery-ledger]
parent: WD-j9nx
created_at: 2026-08-28T06:39:20Z
created_by: speed
updated_at: 2026-08-28T13:42:02Z
content_hash: "sha256:e5e9bf61a179077b7f1fc9946c37053981234f2ea1758e17590f33f56e10e8f3"
assignee: batmanosama
follows: [WD-l5bx]
---

## Description
# S2.5: thin vertical slice — one real e2e render through the full stack

## Description

OPERATOR RULING (2026-08-28): insert the discovery engine's recommendation as
the next story. The vertical slice (S2.5) takes priority over S3: one REAL
end-to-end run before more schema layers.

**This closes the discovery-ledger loop**: this is the FIRST entry in
`knowledge/decisions/discovery-ledger.md` (cycle 001, 2026-08-28 ~05:30 CDT)
being acted on — its "Top recommendation (NEW): Thin vertical slice: one real
e2e run before S3" and its explicit anti-recommendation ("do NOT start S3's
speaker gate before the slice runs") are both honored by this story. Record
that closure in the ledger at delivery time.

Scope (verbatim from the discovery ledger's first entry): real audio file ->
out-of-repo diarization tool -> real timeline JSON -> S2 converter
(`predict/diarization.py`) -> S1 Ref2VA `WanGPJobConfig` -> G5 prompt assembly
-> ONE real render on the 3090 -> VLM QC verdict -> record artifacts against
the run-evidence contract.

**NO new schemas, NO new gates — glue + one render.** Every contract mismatch
found gets FILED (not fixed in-story unless it is a one-line fix).

### Chain to execute (each hop lands an artifact)

1. **Real audio file** — pick one real multi-speaker audio clip (existing
   asset or short recording; must be genuinely multi-speaker so the `<d>`
   attribution path is exercised, not trivially single-speaker).
2. **Out-of-repo diarization** — run an out-of-repo tool (faster-whisper /
   pyannote etc. OUTSIDE the repo code paths — binding rule: never in repo
   imports). Output: real timeline JSON conforming to the S2 schema v1.
3. **Validate + convert** — `scripts/check_diarization.py` (exit 0) then
   `--convert` -> `<d>Name</d>` speaker-attribution blocks.
4. **S1 job config** — build the Ref2VA `WanGPJobConfig` via
   `predict/job_config.py` (audio_prompt_type 'A', guide-alignment, 4-15s cap,
   force_fps, >=96 frames, 17k+5 snap); validate with `check_job_config.py`.
5. **G5 prompt assembly** — assemble the brief through the G5 prompt contract
   (`<d>`-or-silence shape); confirm the six S1 gates fire as designed.
6. **ONE real render on the 3090** — `ssh 3090`. Render discipline:
   - master-lock FIRST (G6 precondition),
   - never trust H3 audio (H3-audio-never-trusted gate),
   - GLM_API_KEY lives in the profile `.env` for the director if needed.
7. **VLM QC verdict** — run QC on the rendered ARTIFACT (not spec), record the
   typed verdict.
8. **Record artifacts** — land the full chain under `datasets/runs/` per the
   run-evidence contract (see existing run records, e.g.
   `datasets/runs/20260826-105551.json`: run_id, briefs, decisions, videos,
   evidence, qc). This run must additionally carry the timeline JSON +
   converted attribution + job config so the chain is replayable end-to-end.

### Out of scope (binding)

- No new schemas, no new gates, no new validator rules.
- No faster-whisper/pyannote imports anywhere in repo code paths.
- No cross-layer refactors; mismatches get filed as follow-up stories.
- S3 (`<d>` speaker gate) stays queued AFTER this story.

## Acceptance Criteria

- [ ] Full artifact chain lands under `datasets/runs/` for this run:
      timeline JSON -> converter output -> WanGPJobConfig -> assembled G5
      prompt -> render video path -> VLM QC verdict, all in one run record
      consistent with the run-evidence contract used by prior runs
- [ ] Every contract mismatch encountered is FILED as a story/comment (one-line
      fixes may be applied in-story but must still be noted); count of
      mismatches found + their disposition recorded in the PR description
- [ ] Epic WD-j9nx GPU-proven AC #3 receives its first real evidence: this run
      is cited as the first e2e-through-the-pipeline attempt on the 3090 with
      a keeper-trackable QC verdict (pass or fail — the EVIDENCE is the point)
- [ ] Render discipline proven in the run record: master-lock acquired before
      submit, H3-audio-never-trusted gate active, QC consumed the artifact
- [ ] Discovery-ledger loop closed: a note appended to
      `knowledge/decisions/discovery-ledger.md` marking cycle-001's top
      recommendation as ACTED ON (this story id + outcome)
- [ ] PR-only flow: branch off current main, explicit staging, no force-push,
      no self-merge; stable head reported to sol-max for Luna+GLM gating
- [ ] Suite green at final head (no regressions vs baseline at branch point)

## Notes

Estimate: ~1 day. Dispatch target: TBD by orchestrator after this filing —
render-heavy + judgment calls (real audio selection, 3090 access) suggest a
hands-on session rather than a pure deepseek-fixer routine; orchestrator to
rule at dispatch.

Carried from ledger cycle 001 priors: WD-cz6a needs evidence-verified closure
(S2 merged as #38 but story still open) — do that verification as part of this
story's pre-work since the slice consumes S2's converter directly.

Sequence after this story: S3 (`<d>` speaker gate) as previously queued, then
S4 (Satan's Mom MV, critical path).

## Acceptance Criteria


## Design


## Notes


## History
- 2026-08-28T13:42:02Z status: open -> in_progress
- 2026-08-28T13:42:02Z auto-follows: linked to predecessor WD-l5bx
- 2026-08-28T13:42:02Z claimed by batmanosama

## Links
- Parent: [[WD-j9nx]]
- Follows: [[WD-l5bx]]

## Comments

### 2026-08-28T06:39:32Z speed
2026-08-28 sol-max: FILED per operator ruling — discovery-ledger cycle 001 top recommendation acted on; S2.5 takes priority over S3 (S3 stays queued). Scope = glue + one real 3090 render, NO new schemas/gates; mismatches get filed not fixed in-story. AC: full chain under datasets/runs/, epic AC #3 first real GPU evidence, ledger loop closed at delivery. Pre-work note: verify WD-cz6a evidence closure (merged as #38, story still open) since the slice consumes S2's converter directly. Dispatch target TBD by orchestrator at dispatch time.
