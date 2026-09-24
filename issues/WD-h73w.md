---
id: WD-h73w
title: "Dogfood one real content brief through governed film"
status: closed
priority: 0
type: epic
labels: [e2e, accepted]
created_at: 2026-09-20T19:46:39Z
created_by: speed
updated_at: 2026-09-24T01:03:06Z
content_hash: "sha256:f33da834efdb9a19a111aa9328fa93d5861fd7c7e359f3ffb8b0a7b33e0d3fb4"
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
### Render-count scope disposition (milestone review, 2026-09-23)

WD-h73w's OUT OF SCOPE said, "More than one independent governed render execution," but two real starts occurred with `dry_run: false`: `datasets/runs/provenance/lf004-operator-dogfood-20260920/execution.log` records 4 cuts at 107 frames, and `datasets/runs/provenance/lf004-operator-dogfood-56f-recovery-20260921/execution.log` records 4 cuts at 56 frames. WD-42no records both exact operator approvals—the original 107-frame plan (`70280fdcd6fb7f54bc4f7027e03de54e4897178dd41adcf92ef31bd347d7bd86`, approved 2026-09-20T20:47:21Z) and the corrected 56-frame plan (`620f2ba44beb7d0bc920772c136aa0ce6f76df89acd286647c23e5a7c8015eb8`, approved 2026-09-21T00:54:03Z)—so the second start was operator-authorized. The literal epic sentence was nevertheless exceeded with operator authorization, and the epic text was not amended. This note records that discrepancy; it does not resolve it. The operator's explicit confirmation is still needed for the scope-history mismatch.

## History
- 2026-09-21T04:42:48Z status: open -> closed

## Links


## Comments

### 2026-09-23T20:48:29Z speed
Completion-gate evidence at merged head 1f86aaa2d799bdf151376fc6e71fcf88fd2fc44e (main checkout): (1) full suite tests=1999 errors=0 failures=0 skipped=1 via parsed JUnit counters; (2) pvg verify --check-e2e PASSED, 1 e2e file (tests/e2e/test_production_stability.py); (3) wgp release verify -> release=ready, tag_created=false; (4) pvg lint --backlog 0 errors / 0 review findings over 112 issues; (5) pvg nd list --status open -> none; (6) protected engine files unchanged vs 1a7f4e5. The gate also caught and closed defect WD-pn6h (canonical path leak) before declaring the epic complete.

### 2026-09-24T01:03:06Z speed
Completion-gate evidence at merged head 40f8c2b373dec1c84ca5a596c821b740934af6fb (operator main checkout, ignored live acceptance file present): (1) full suite tests=2012 errors=0 failures=0 skipped=1 via parsed JUnit counters; (2) pvg verify --check-e2e PASSED (1 e2e file); (3) wgp release verify -> release=ready, tag_created=false; (4) pvg lint --backlog 0 errors / 0 review findings over 114 issues; (5) pvg nd list --status open -> none (114 issues, 114 closed); (6) protected engine files unchanged vs 1a7f4e5. The gate itself caught and closed three defects before this head: WD-pn6h (canonical path leak), WD-td89 (durable operator verdict + launcher reconciliation), WD-mjzt (acceptance source resolution crossing the output root; rejected once for a symlink escape and reworked). Merged PRs: #178 rf1a, #179 v6xp, #180 pn6h, #176 7zrq, #181 td89, #182 mjzt.
