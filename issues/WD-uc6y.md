---
id: WD-uc6y
title: "Production stability: installable, zero-config, documented"
status: open
priority: 1
type: epic
created_at: 2026-09-21T13:53:24Z
created_by: speed
updated_at: 2026-09-21T13:53:24Z
content_hash: "sha256:904c5ce47bbe5e277e770e49d0fbec6cfb72b1966e0f25e87b00676e63de1293"
---

## Description
## USER INTENT
The operator wants Wangp to feel stable like the upstream Maestro product: a stranger can install it, understand prerequisites, plan without a GPU, diagnose the host, recover from failure, and reproduce a render without learning internal script paths. The strong governed engine must remain intact.

## Epic Outcomes
- A fresh repository consumer can go from clone to a canonical no-GPU content plan through one documented, tested path.
- A stable `wgp` CLI exposes validation, planning, queue status, review, diagnostics, and doctor preflight without duplicating gateway or runner behavior.
- Host and Wan2GP root values come from explicit configuration or safe local detection; no operator-specific SSH target is a hidden runtime default.
- Common infrastructure and gate failures present typed, concrete remediations instead of Python tracebacks and dead-letter mystery.
- A render is represented by a pinned recipe/model manifest and a no-GPU reproduction check tied to repository version discipline.

## Measured Gap at main 3094b14
- `README.md` is 317 bytes and contains no install, prerequisite, quickstart, or troubleshooting path.
- `LICENSE`, `VERSION`, `CHANGELOG.md`, `CONTRIBUTING.md`, and `THIRD_PARTY_NOTICES.md` do not exist at the repository root.
- The committed 56-frame brief and plates are a viable no-GPU fixture. In a clean detached worktree at `3094b14`, `scripts/run_content_brief.py` emitted four clips with `gpu_work: false`, `queue_submitted: false`, and planned duration `9.332` seconds. The same command in the current dirty checkout fails because repository identity refuses to hash an opaque untracked embedded worktree; documentation must explain that fail-closed behavior.
- Active source under `host`, `services`, `scripts`, `predict`, and `qc` contains 20 exact `"3090"` or `/home/straughter/Wan2GP` default literals. `scripts/run_jobs.py:531-534` and `scripts/run_v3_native_control.py:61-64` directly construct the production SSH host with those values.
- `pyproject.toml` declares no console script. Operators must know internal script names and flags rather than stable verbs.
- Existing durable queue records contain `failure_class`, `failure_detail`, and immutable attempt history, but no user-facing diagnostic maps those facts to the next safe command.

## OUT OF SCOPE
- Any change to Whisper, vision, mouth-box, SyncNet, QC, retry, renderer, provenance, or gate semantics: this epic exposes and configures the accepted engine without weakening it; lands never without separate authorization.
- GPU execution, remote host mutation, model inference, or paid/external API dependence: every story must be verifiable with local no-GPU integration tests.
- Pinokio/installer parity and a graphical UI: deferred until this epic makes the repository contract stable and documented.
- Reinterpreting historical evidence or modifying accepted render artifacts: stories may read committed evidence but must not rewrite it.

## MANDATORY SKILLS
- pvg

## Epic Gate
1. Every child story is accepted with real no-mock integration evidence.
2. The final end-to-end story proves the documented stranger path, stable CLI, unconfigured-host behavior, diagnostics, and recipe verification in one clean checkout.
3. Protected engine behavior remains unchanged: no QC/AV/retry/renderer threshold or decision changes.

## nd_contract
status: new

### evidence
- Created 2026-09-21 from operator intent and measured repository gaps at main 3094b14.

### proof
- [ ] Pending acceptance of all child stories and the epic end-to-end gate.


## Acceptance Criteria


## Design


## Notes


## History


## Links


## Comments
