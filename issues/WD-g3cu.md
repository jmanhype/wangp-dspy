---
id: WD-g3cu
title: "#9 spec/plan pair standard: docs/specs/ + docs/plans/ templates"
status: open
priority: 2
type: task
labels: [docs, adopt-cycle]
parent: WD-j9nx
created_at: 2026-08-28T01:38:18Z
created_by: speed
updated_at: 2026-08-28T01:38:18Z
content_hash: "sha256:5db89ffa8ad617d9e9c9e4fbe9b14af3451ef52128f0a3895229ff5669cf7290"
---

## Description
# #9 — Spec/plan pair standard (ADOPT spec-driven-evolution)

## Description

ADOPT of the shuohao-skills spec → plan → implementation cycle (docs/extraction/shuohao-skills/spec-driven-evolution.md ADOPT; source: docs/superpowers/specs/2026-08-21-shot-recipes-repository-migration-design.md + plans/2026-08-21-shot-recipes-repository-migration.md). The notable property we adopt: **the plan is machine-executable by a fresh agent with zero conversation context** — every decision lives in the spec, every command and expected-output in the plan. Deliverables: (a) `docs/specs/TEMPLATE.md` — the pure decision document (goal + success invariant / layout / scope incl. explicit non-goals / history strategy / verification commands / failure & recovery; every non-obvious choice carries its reason inline); (b) `docs/plans/TEMPLATE.md` — the executable decomposition (agentic-worker header / one-line Goal / Architecture paragraph stating the key invariant / Tech Stack / pointer back to spec / Global Constraints / File Map before tasks / Tasks→Steps where each step = command block + an "Expected:" line stating the observable outcome, failure conditions gate progression); (c) `docs/spec-plans.md` — when to use which (spec+plan pair for risky multi-step/multi-repo operations or anything delegated to a fresh agent; plain story body for routine slices), the 'Expected:' line discipline, and the mandatory recovery section rule (every spec MUST state what happens on failure — never stash/reset user work, git history as safety net).

## Acceptance Criteria

1. `docs/specs/TEMPLATE.md` exists with all fixed sections from the extraction (goal+invariant, layout, scope+non-goals, history strategy, verification, failure & recovery) and inline-reason placeholders showing the convention.
2. `docs/plans/TEMPLATE.md` exists with: agentic-worker header, Goal/Architecture/Spec-pointer block, Global Constraints, File Map, Tasks→Steps with at least two worked example steps demonstrating the "Expected:" line discipline (observable outcome per step, stop-condition on failure).
3. `docs/spec-plans.md` states: the trigger condition (when a spec/plan pair is required vs a plain story), the 'Expected:' line rule, the mandatory recovery-section rule, and the relationship to the CHANGELOG decision-record format (spec = why, plan = how, changelog = what was learned).
4. Templates are immediately usable: a future Phase 2 film-lane story (S1+) can be filed against them without further authoring.
5. Docs-tier lane: PR-only, no code/test changes; full suite green at branch head (unchanged from main).

## Design

- Templates stay SHORT (each < ~100 lines): they are skeletons with conventions, not essays.
- The 'Expected:' line is the load-bearing discipline — it makes verification mechanical and lets a fresh agent self-check every step.
- Recovery section is MANDATORY in specs (extraction spec:97-105 pattern): old content stays in git history; user uncommitted work is never stash/reset/checkout'd away.
- This story pairs with #8: together they establish the docs corpus (decisions + process). No overlap — #8 = what was decided, #9 = how work gets decomposed.

## Acceptance Criteria


## Design


## Notes


## History


## Links
- Parent: [[WD-j9nx]]

## Comments
