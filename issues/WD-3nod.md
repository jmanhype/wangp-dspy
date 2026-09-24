---
id: WD-3nod
title: "Maestro parity: generation evidence"
status: open
priority: 1
type: epic
labels: [capability, evidence]
created_at: 2026-09-24T14:14:05Z
created_by: speed
updated_at: 2026-09-24T16:33:45Z
content_hash: "sha256:47df1afd91d2a4cbfe9984fa293b62c9c4fb701d0fd33181fca351038313b8a1"
---

## Description
Temporary creation body; authoritative body is installed immediately after ID assignment.

## Acceptance Criteria


## Design


## Notes


## History


## Links


## Comments

### 2026-09-24T16:33:45Z speed
Programme status at 8f0b225: WD-651z (fail-closed parity evidence checker + canonical bundle contract) delivered, independently accepted, and merged. All 10 child stories now have authoritative bodies. Remaining scope is entirely host-gated: 45 capability rows still read 'planned' and no bundle exists under datasets/runs/maestro-parity/ because the operator's per-batch GPU-host authorization and model-download approval have not been given. The no-GPU install half of the 'better than Maestro' proof already exists and is tested in a clean worktree (tests/test_readme_quickstart.py).
