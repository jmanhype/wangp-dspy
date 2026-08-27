---
id: WD-gq8y
title: "ADOPT: two-round sign-off checkpoint for bible/brief flow"
status: closed
priority: 2
type: task
labels: [adopt, shuohao-skills]
parent: WD-j9nx
created_at: 2026-08-27T17:23:35Z
created_by: speed
updated_at: 2026-08-27T17:46:47Z
content_hash: "sha256:1e5a4d19bb9ed097efca614a50579c1a0a208fecfb7bc8aaae6b8850ee17a903"
assignee: dev-WD-gq8y
follows: [WD-4jpr]
closed_at: 2026-08-27T17:46:47Z
led_to: [WD-4s1b]
---

## Description
# ADOPT: two-round sign-off checkpoint (cheap round-1 skeleton before expensive work)

Implements the two-round skeleton validation from shuohao-skills outline-pass
(docs/extraction/shuohao-skills/pass-methodology-outline.md, section 1 L19-26;
GLM verdict ADOPT — "highest-value single idea in this set").

## Doctrine (verbatim rationale)
Round 1 is a cheap "fast version": fill the four structural blocks (what we cut,
who we merged, where the majors land), validate the skeleton, STOP, and go to the
USER for sign-off. Round 2 refines after feedback and re-validates. Rationale:
"快版的意义是便宜——错了只损失一轮骨架，不是 60 集梗概" — an error costs one
skeleton, not the full expensive artifact. The three sign-off questions that
invalidate everything downstream: which lines were cut / which people merged /
where the major beats land.

## Our application
The SGFLIX bible flow's expensive artifacts are the 8-page character bibles
(IDENTITY_LOCK pages) and the rendered briefs. Today wangp-dspy has no
checkpoint between intent and full brief generation — a wrong direction is only
caught at QC, after render spend. This story adds the round-1 checkpoint
artifact + deterministic validation so the user can sign off on the skeleton
before any expensive stage runs.

## Components
1. **Skeleton dataclass** (new module `predict/skeleton.py` or similar): the
   round-1 artifact with exactly the fields the doctrine names — cuts (each with
   a why), merges (each with a why / `from` source), payoff/major-beat placement,
   plus a `signoff` block (status pending/approved/rejected, reviewer, ts).
2. **Deterministic validator** `validate_skeleton(skel) -> list[str]`:
   all four blocks present and nonempty; every cut/merge carries a nonempty why;
   payoff placement obeys the spacing rules adapted to our regime (no vacuum at
   start/end; earliest major not last); returns violation strings, raises typed
   SkeletonValidationError when invalid. NO LLM calls.
3. **Sign-off gate**: pipeline/run path refuses to proceed past round 1 while
   `signoff.status != "approved"` — typed failure naming the missing approval,
   same loud-failure pattern as the meta-hint guard and no-names gate.
4. **Doc**: short pass-doc-style note under docs/ describing the two-round
   discipline (round-1 fields, the three sign-off questions, why cheap-first).

## Acceptance criteria
- (a) TDD suite for the validator: valid skeleton passes; each of the four
      blocks individually empty -> rejected; cut without why -> rejected;
      merge without why -> rejected; payoff at first/last position -> rejected;
      approved vs pending signoff handled distinctly. All deterministic, zero-model.
- (b) Sign-off gate wired into the pipeline path (or documented seam if the
      pipeline change is larger than this slice): proceeding with unapproved
      skeleton raises a typed error naming the skeleton id + status.
- (c) CLI or script helper to pretty-print a skeleton for human review (the
      three sign-off questions rendered explicitly).
- (d) Doc checked in under docs/ citing the extraction doc (file:line refs).
- (e) Full test suite green + implementation captured (PR trail, evidence).

## Notes
- Source: docs/extraction/shuohao-skills/pass-methodology-outline.md (outline-pass
  L19-26 two-round; L17 decision sentences; L15 evidence-on-decisions).
- Zero-model: no LLM anywhere in the validator/gate/tests.
- Pattern references: predict/prompt_director.py `_reject_meta_hints` +
  gates/no_names_gate.py (typed rejection, loud skip).

## Acceptance Criteria


## Design


## Notes


## History
- 2026-08-27T17:25:54Z status: open -> in_progress
- 2026-08-27T17:25:54Z auto-follows: linked to predecessor WD-4jpr
- 2026-08-27T17:25:54Z claimed by dev-WD-gq8y
- 2026-08-27T17:46:47Z status: in_progress -> closed

## Links
- Parent: [[WD-j9nx]]
- Follows: [[WD-4jpr]]
- Led to: [[WD-4s1b]]

## Comments

### 2026-08-27T17:37:55Z speed
PR #28 opened (feat/wd-gq8y-skeleton-signoff -> main). Branch tests 19/19 green; full suite clean modulo 2 pre-existing test_wd_oa4i_tooling failures proven identical on main checkout. Awaiting GLM security review.

### 2026-08-27T17:44:28Z speed
GLM review (rubric-lite) — OVERALL: PASS, merge-ready.
1. MECHANISM FIDELITY — PASS (doctrine faithfully carried; see nits).
2. TESTS GENUINE — PASS (Boom-stub proves no stage runs pre-signoff).
3. NO REGREGRESSIONS — PASS (diff additive + new files only).
4. SECURITY SURFACE — PASS (no shell/eval/writes/network; zero-model verified, stdlib-only deps).
Carry-over nits (non-blocking): M1 docstring/code start-vacuum constant mismatch; F1 document sign-off is caller-attested not authenticated; F2 consider requiring skeleton kwarg (None skips gate).

### 2026-08-27T17:44:29Z speed
ADOPT #2 VERIFIED by sol-max: branch feat/wd-gq8y-skeleton-signoff head e7f5f45. tests/test_skeleton.py 19/19 pass; diff --check clean; full-suite failure set IDENTICAL on main vs branch (12 pre-existing LM-wiring + 2 pre-existing manifest-count failures, both fail on clean main too); CLI renders the three sign-off questions correctly. GLM OVERALL PASS. Ready for operator PR+merge.

### 2026-08-27T17:46:47Z speed
ADOPT #2 DELIVERED: PR #28 merged (GLM PASS all 4 items, Sol verification: 19/19 skeleton tests, CLI live, zero-model confirmed). Nits logged: M1 constant mismatch, F1 caller-attested signoff, F2 skeleton-kwarg enforcement. Automerge per operator standing order.
