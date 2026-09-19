---
id: WD-j9nx
title: "DSPy-native video-gen pipeline"
status: closed
priority: 2
type: epic
created_at: 2026-08-22T04:04:21Z
created_by: speed
updated_at: 2026-09-19T20:39:43Z
content_hash: "sha256:f140042034c649de829239b19f6a74390a358c3f9b763fabaefc78bf15cf7549"
closed_at: 2026-09-19T20:39:43Z
close_reason: "Completion gate passed: all 32 child stories closed; WD-h25b is the accepted capstone with merged PR #41, byte-identical final artifact, independent evidence validation, and clean full-suite result; scoped backlog lint and RTM checks both PASSED."
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
- 2026-09-19T20:39:43Z status: open -> closed

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

### 2026-08-28T01:37:20Z speed
2026-08-28 sol-max: CORRECTION to the master-sequence comment above — the S4 line was mangled by shell heredoc quoting (the "S5 aesthetic anchor..." text got absorbed into the S4 bullet). Authoritative Phase 2 list, verbatim from operator:

PHASE 2 (film lane, dependency order, same governed cycle each):
- S1 WanGPJobConfig + Ref2VA profile (job schema absorbing scattered asserts: force_fps, >=96 frames, 17k+5 snap, flat JSON; Ref2VA Strategy leaf: image_refs, audio_prompt_type 'A', guide-alignment validation, 4-15s cap; six guaranteed-invocation gates: audio 'A' hard-reject at submit, guide==shot-duration validation, QC consumes artifact not spec, H3-audio-never-trusted gate, <d>-or-silence prompt contract, master-lock precondition).
- S2 diarization (MIT-clean upstream pattern)
- S3 <d> speaker gate
- S4 Satan's Mom MV (critical path — the film finishes here as the story's acceptance test
- S5 aesthetic anchor (parallel-safe)
- S6 GEPA metric blend
- S7 caption signature (S6+S7 gated on S4's banked renders)
- S8 OOM retry + calibration (anytime)

BINDING constraints unchanged: Maestro ADAPT-TO-IDEA ONLY (non-commercial license — never vendor code, use file:line refs as specs); aesthetic predictor = v2/CLIP-L/14 LAION line (0.85GB, license-clean) or clean-room (AGPL trap in v2.5); faster-whisper/pyannote never in repo code paths.
EOF
)

### 2026-08-28T01:38:40Z speed
2026-08-28 sol-max: Phase 1 board state — #8 filed as WD-23r7 (decision-record CHANGELOG, docs-tier), #9 filed as WD-g3cu (spec/plan pair standard, docs-tier). Both parented to WD-j9nx. Dispatch order per standing automerge sequence: #8 first, then #9; WD-r8n9 triage and WD-n0ab close-out run in parallel with the docs lane.

### 2026-08-28T01:40:03Z speed
2026-08-28 sol-max: Phase 1 dispatch — (1) deepseek-fixer on WD-23r7 (#8 decision-record CHANGELOG, primary checkout, branch feat/wd-23r7-decision-changelog off main @ 0db8996); (2) Luna live verification of knowledge_capture in a fresh session for WD-n0ab close-out; (3) WD-r8n9 triage: scanner DANGEROUS verdicts on own test fixtures — root cause already filed upstream (NousResearch/hermes-agent#93927: plugin_guard.EXCLUDED_DIRS lacks tests/, single-critical→dangerous with no override), so the determination is SCANNER FALSE-POSITIVE on legitimate destructive-string test fixtures (tests/test_driver_ops.py:236, test_vault_s5_evolve.py:226). Disposition pending operator call on fix location: (a) upstream hermes-agent fix (preferred — scanner logic lives there), (b) local quarantine of scanner-bait fixtures into a dedicated file with recognized header. Awaiting operator ruling before filing/closing.

### 2026-08-28T02:47:13Z speed
2026-08-28 sol-max: Phase 1 close-out + Phase 2 dispatch. (1) WD-r8n9 triage COMPLETE (full measured verdicts + recommendation in its own comments): SCANNER FALSE-POSITIVE class — all 4 criticals are deliberate test fixtures (destructive-string quoting guard, decoy secret, traversal-refusal tests), zero runtime exposure; root cause pinned upstream NousResearch/hermes-agent#93927 (EXCLUDED_DIRS lacks tests/, single-critical->dangerous, no override). RECOMMENDATION to operator: (a) UPSTREAM FIX [preferred] — a tests/-tier exclusion moves this repo dangerous->caution (force-installable, human-confirmable); (b) NO local interim — recommend against any local ignore/allowlist (would mask future real regressions in our own driver code; violates gate-credibility axiom); one-time confirmation flow after upstream lands is the right interim; (c) rejected: quarantining bait fixtures (scanner still scores the file, degrades test locality without fixing the gap). Awaiting operator call on disposition. (2) PHASE 2 BEGINS: S1 filed as WD-l5bx (P1, film-lane opener) — WanGPJobConfig validator absorbing the 5 scattered asserts + Ref2VA Strategy profile + six guaranteed-invocation gates (audio 'A' hard-reject at submit, guide==shot-duration, QC-consumes-artifact, H3-audio-never-trusted, <d>-or-silence contract, master-lock precondition); binding constraints in body (Maestro idea-only / file:line refs, no faster-whisper/pyannote, local-only inference); AC includes TDD RED-first per gate + spec/plan pair dogfooding the NEW #9 templates (first real use of PR #36). Dispatched to qwen-escalator (architectural: new config surface + trust-boundary gates), primary checkout, branch feat/wd-l5bx-wangp-jobconfig-ref2va off main @ ed6420a, baseline 406 tests. Standing automerge order applies; Luna+GLM parallel after verified stable head. S2-S8 follow per epic sequence once S1 merges.

### 2026-08-28T04:17:11Z speed
2026-08-28 sol-max: S1 MERGED — PR #37 -> d10af46, WD-l5bx closed. Double-PASS: GLM re-review PASS after fix round; Luna mechanical PASS (per-rule grep verification: zero duplicate enforcement sites, all six gates proven entry-point unskippable, 442 tests, RED genuine, clean-room vs Maestro). Film lane foundation LIVE: WanGPJobConfig single authority, Ref2VA Strategy profile, six operator-ruled gates structurally unskippable at submit/render.

S2 FILED + DISPATCHED: WD-cz6a "S2: speaker diarization for multi-speaker <d> attribution" (parent WD-j9nx, P1). Scope per deep-dive: repo CONSUMES out-of-repo diarization JSON — schema v1 + deterministic validator (rules R1-R6, typed per-rule rejections) + conversion to <d>Name</d> attribution blocks feeding S3's gate + CLI surface. BINDING honored: no faster-whisper/pyannote in repo code paths (execution external, MIT-clean upstream pattern); Maestro audio_analysis.py:675-780 IDEA-ONLY (never vendor). Spec/plan pair authored by orchestrator per #9 templates (docs/specs/s2-diarization.md + docs/plans/s2-diarization.md, in working tree for the implementer). Dispatched to deepseek-fixer (routine measured-first against fully specified plan), primary checkout, branch feat/wd-s2-diarization off main @ d10af46 (baseline 442). AC: validator TDD / deterministic conversion / suite >= 442 green / CLI+validator surface / binding grep zero. After verified stable head: Luna+GLM parallel -> standing automerge. Then S3 (<d> speaker gate; G3 run_pipeline wiring lands there per carried nit), S4 (Satan's Mom MV, critical path) per sequence. Carried nits: render_profiles constant import anytime.

### 2026-08-28T18:28:34Z speed
S3 DELIVERED: PR #40 merged (GLM PASS all 5 — RED trail reproduced empirically, hermetic fix verified as isolation-not-evasion, suite failures proven pre-existing). Speaker attribution now REQUIRED; G3 wired. Film lane: S1-S3 + S2.5 all merged. S4 (the film) next.
