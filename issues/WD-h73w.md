---
id: WD-h73w
title: "Dogfood one real content brief through governed film"
status: closed
priority: 0
type: epic
labels: [e2e, accepted]
created_at: 2026-09-20T19:46:39Z
created_by: speed
updated_at: 2026-09-23T20:48:29Z
content_hash: "sha256:9a9fb453453fd6c583110116ca6f691542db522d8c0d22ccd01df558e1f84599"
closed_at: 2026-09-21T04:42:48Z
close_reason: "All child stories are closed and accepted; mechanical capstone complete, operator creative verdict remains pending."
---

## Description
## USER INTENT
The operator wants to prove the accepted Content Brief Gateway and governed film pipeline as one real production loop, not merely as separate green components.

## Epic Outcomes
- One real repository-owned brief becomes a validated no-GPU run plan.
- The operator explicitly approves that exact plan before any real render.
- Exactly one governed render execution produces a reviewable, hash-identified film through the declared gates.
- Brief, plan, ledger, render, QC, provenance, review artifacts, and operator verdict remain reproducible.

## OUT OF SCOPE
- GPU, queue, host, model, or render work in the planning story.
- More than one independent governed render execution.
- Router, Jev, Gauntlet, or Talker-Reasoner changes.
- Reinterpreting an old LF003 artifact as the new dogfood render.

## nd_contract
status: new

### evidence
- Operator selected one real content-brief-to-film dogfood as the next Wangp phase on 2026-09-20.

### proof
- [ ] Pending planning and render story acceptance.

## Acceptance Criteria


## Design


## Notes


## History
- 2026-09-21T04:42:48Z status: open -> closed

## Links


## Comments

### 2026-09-23T20:48:29Z speed
Completion-gate evidence at merged head 1f86aaa2d799bdf151376fc6e71fcf88fd2fc44e (main checkout): (1) full suite tests=1999 errors=0 failures=0 skipped=1 via parsed JUnit counters; (2) pvg verify --check-e2e PASSED, 1 e2e file (tests/e2e/test_production_stability.py); (3) wgp release verify -> release=ready, tag_created=false; (4) pvg lint --backlog 0 errors / 0 review findings over 112 issues; (5) pvg nd list --status open -> none; (6) protected engine files unchanged vs 1a7f4e5. The gate also caught and closed defect WD-pn6h (canonical path leak) before declaring the epic complete.
