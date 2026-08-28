---
id: WD-j9nx
title: "DSPy-native video-gen pipeline"
status: open
priority: 2
type: epic
created_at: 2026-08-22T04:04:21Z
created_by: speed
updated_at: 2026-08-28T01:37:05Z
content_hash: "sha256:2fe1ec80920dcf461c3f43e655d858b512e97230a0cb4e3026c3e12eb34b6790"
---

## Description
## Acceptance Criteria (operator-view, 2026-08-24)

The epic is DONE when all of the following hold:

1. **One call, one artifact chain.** A single pipeline invocation
   (`Pipeline.forward(intent)`) carries an intent through
   briefs -> profile -> assemble -> render -> QC without any manual
   glue between stages, producing: the rendered video, a typed QC
   verdict, and a replayable evidence trail for the run.
2. **Typed failure at every boundary.** Each stage transition fails
   loudly with a typed error naming the stage — no silent no-ops
   (the WD-yyj9 class of bug is structurally excluded).
3. **Proven on the real GPU.** At least one full e2e run on the 3090
   through the PIPELINE (not the adapter alone) that ends in a
   keeper-trackable verdict (WD-mhr2).
4. **The pipeline is optimizable.** metrics/ + train/val datasets
   exist; a recorded baseline (LabeledFewShot) and at least one GEPA
   compile exist with side-by-side comparison — improvement OR a
   documented plateau with evidence (WD-txt9).
5. **Repo structure matches the research-agreed layout**:
   signatures/ (contracts), predict/, evaluate/, host/, datasets/,
   metrics/, training/, compiled/ — capability folders + app-repo
   artifacts.
6. **Every child story closed with its own evidence** (green tests,
   merged PR, real-run artifacts where GPU-bound) — no paper-only
   closures.

NOT in scope (explicitly): autonomous publishing, UI, fine-tuning
model weights (BootstrapFinetune is a later lever if prompt-only
plateaus).

## Acceptance Criteria


## Design


## Notes


## History


## Links


## Comments

### 2026-08-28T00:33:49Z speed
2026-08-27 sol-max: seam-violation note (candidate follow-up ticket): run_pipeline._checked_video uses os.path.isfile directly — local-namespace assumption, inconsistent with the RenderHost seam. SshHost renders return local-mirror paths so it works today, but a non-local render host without a mirror would break silently. Filed as candidate follow-up under this epic; logged during #6 provenance-tiers scoping.

### 2026-08-28T00:54:40Z speed
2026-08-28 sol-max: shuohao ADOPT cycle (extraction cdccd7d/#26) — remaining queue: #7 WD-rty2 (QC failure triage gate/rule/example + ledger, dispatched to deepseek-fixer, branch feat/wd-rty2-qc-triage off 9d0eb2f), #8 decision-record changelog (docs/CHANGELOG.md decision-record format per changelog-design-rationale.md RECOMMENDATION; backfill merged ADOPT stories #27-#33 with measured evidence + rejected alternatives), #9 spec/plan pair standard (spec-driven-evolution.md ADOPT: docs/specs/ + docs/plans/ template, 'Expected:' line discipline, mandatory recovery section). Standing automerge order from operator; gates per tier (docs = PR-only lane, Luna+GLM after stable head).

### 2026-08-28T01:37:05Z speed
2026-08-28 sol-max: OPERATOR MASTER SEQUENCE — canonical roadmap (supersedes prior queue comments; the loop survives on board state).

PHASE 1 (current): finish the adoption loop.
- #7 QC triage: DONE — PR #34 merged 2026-08-28T01:36Z (GLM PASS, 406/406 green), WD-rty2 closed.
- #8 decision-record changelog: as scoped (docs-tier, PR-only lane) — docs/CHANGELOG.md decision-record format per changelog-design-rationale.md RECOMMENDATION; backfill merged ADOPT stories #27–#33 with measured evidence + rejected alternatives.
- #9 spec/plan pair: as scoped (docs/specs/ + docs/plans/ templates, 'Expected:' line discipline, mandatory recovery section).
- Also phase 1: WD-r8n9 triage (scanner DANGEROUS verdicts on own fixtures — determine real vs scanner false-positive; file fix or close accordingly) and WD-n0ab close-out (fresh-session live plugin verification of knowledge_capture, then close).

PHASE 2: the film lane, S1–S8 in dependency order, same governed cycle each (story_create -> implementer -> ground-truth verify -> GLM review -> automerge per standing order). BINDING deep-dive constraints:
- Maestro = non-commercial license: ADAPT-TO-IDEA ONLY — never vendor Maestro code; use its file:line refs as specs, implement clean.
- aesthetic predictor: AGPL trap in v2.5 — use the v2/CLIP-L/14 LAION line (0.85GB, license-clean) or clean-room.
- faster-whisper/pyannote never in repo code paths.
- S1 WanGPJobConfig + Ref2VA profile (job schema absorbing scattered asserts: force_fps, >=96 frames, 17k+5 snap, flat JSON; Ref2VA Strategy leaf: image_refs, audio_prompt_type 'A', guide-alignment validation, 4-15s cap; six guaranteed-invocation gates from operator ruling: audio 'A' hard-reject at submit, guide==shot-duration validation, QC consumes artifact not spec, H3-audio-never-trusted gate, <d>-or-silence prompt contract, master-lock precondition).
- S2 diarization (MIT-clean upstream pattern), S3 <d> speaker gate, S4 Satan's Mom MV (critical path — the film finishes here as the story's acceptance test, S5 aesthetic anchor (parallel-safe), S6 GEPA metric blend, S7 caption signature (S6+S7 gated on S4's banked renders), S8 OOM retry + calibration (anytime).

PHASE 3 (AFTER all of S1-S8 complete): the GEPA run — last because duration is unknown. Run GEPA on the 30-example dataset against baseline 0.0, full validation-set scoring, side-by-side held-out outputs, artifact load/hash/readback verification per original WD-oa4i gates (d). No GPU render during optimization.

Standing rules unchanged: automerge on GLM PASS + no new failures + scope-match; stop on double-BLOCK/provider death/operator interrupt; every story board-carried; post-merge plugin resync for paivot-hermes changes.
EOF
)
