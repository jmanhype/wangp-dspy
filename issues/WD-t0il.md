---
id: WD-t0il
title: "Gate: remaining Maestro-parity scope (120 planned cells) pending operator authorization"
status: open
priority: 1
type: task
labels: [capability, evidence, gate]
parent: WD-3nod
created_at: 2026-09-26T05:37:46Z
created_by: speed
updated_at: 2026-09-26T05:37:46Z
content_hash: "sha256:129f7a6ef9e80c187ab56d1cb4fc4131f6ece51612fb5639a80a741470894ef8"
blocks: [WD-fay0]
---

## Description
## Purpose

This story exists so the programme record cannot claim completion it has not
earned. `pvg` closes an epic automatically when its last child closes, which
twice produced a false "Maestro parity: generation evidence — accepted" state
while 120 matrix cells remained `planned`. This story is the epic's standing gate:
it stays open (blocked) until the remaining cells reach terminal, evidence-backed
states, so the epic stays open and the loop reports a real escalation instead of
"epic_complete".

This is a tracking gate, not dispatchable engineering work. It must not be worked,
claimed, or closed by an agent. Only the operator closing the underlying scope
retires it.

## Remaining scope (authoritative count from the capstone index)

208 cells: 46 verified, 34 unsupported, 120 planned, 6 pending consent, 2 not
applicable. The 120 planned cells sit in eight state-bearing capability matrices.

- **video, 90 cells.** Every cell carries the same recorded blocker verbatim: the
  representative operation was verified and the remaining operations "need a new
  operator-approved per-family/per-operation batch". Unlocked by: per-batch
  GPU-host authorization.
- **director, 25 cells.** All blocked by `WD-dmf2`'s three structural gate
  failures: Whisper screenplay clip 1 `0.556 < 0.6`, SyncNet audio clip 1
  `0.594741 < 1.0`, SyncNet screenplay clip 1 `0.468897 < 1.0`. Unlocked by: a
  rework-versus-structural-disposition decision.
- **finishing, 4 cells.** `ffmpeg` Film grain is honestly `planned` because the
  corrected size/persistence graph (WD-r4n8) is unmeasured and needs a host run;
  `neural_frame_gen` has three cells with no named host implementation, which the
  record states is "absence, not hardware infeasibility" and therefore needs a
  scope decision.
- **voice/character, 6 cells.** Clone and cross-mode identity rows are
  `evidence_complete_pending_review`; the reference consent chain is unapproved.
  Unlocked by: cloning-reuse consent.
- **video `ltx/2.3`.** A 29.5 GB generic FP8 checkpoint mismatches the WanGP
  manifest. Unlocked by: download approval.
- **video `ltx/2.5`.** Root-caused and fixed on the WanGP fork branch
  `story/WD-i7qs` @ `faea82d1` (declared in `WD-i7qs`, dispatched and accepted).
  Unlocked by: deploying that branch to the render host and authorizing the run.

Also outstanding for criterion (b): the clean-machine one-command install that
emits a real generated artifact (blocked on host authorization plus a complete
model manifest), and a checker-demonstrated bundle for the `director` lane, which
depends on the director decision above.

## Host prerequisites (already cleared, tool-verified)

`wgp doctor --probe-host` against `3090`: `ssh_reachable` PASS, `model_files` PASS
with a real verified hash, `disk_headroom` PASS at 60G free against the 50G floor,
`gpu_state` idle with 24 GB free. The binding constraint is operator authorization,
not the machine.

## MANDATORY SKILLS
None identified.

## nd_contract
status: blocked

### evidence
- Capstone disposition index (WD-fay0) and the reopened epic comment on WD-3nod.
- Preflight probe output recorded in the WD-3nod epic comment.

### proof
- [ ] Zero rows remain `planned` without an operator-approved disposition
- [ ] Criterion (b) clean-machine generated-artifact demonstration completed
- [ ] Criterion (b) checker demonstrated on a director-lane bundle

## Acceptance Criteria


## Design


## Notes


## History
- 2026-09-26T05:37:53Z dep_added: blocks WD-fay0

## Links
- Parent: [[WD-3nod]]
- Blocks: [[WD-fay0]]

## Comments
