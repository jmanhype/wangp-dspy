---
id: WD-mgcd
title: "Preflight H3 PyAV media-write compatibility"
status: in_progress
priority: 0
type: task
labels: [bug, evidence, qc, delivered]
parent: WD-3nod
created_at: 2026-10-09T14:30:58Z
created_by: speed
updated_at: 2026-10-09T16:06:43Z
content_hash: "sha256:e045a82d74182ae835e435ac2e60178aac030431034828b6bfd52cfda583573e"
blocks: [WD-bw0h, WD-fay0]
assignee: dev-WD-mgcd
follows: [WD-dhcc, WD-5yg9]
---

## Description
## Context (Embedded)
- WD-bw0h retry4 consumed its v3 one-shot authorization at main `37a5d19a50b58be381e793cd10ba9f4bb5bd1fb0`.
- The prior settings-staging defect was cleared: WanGP loaded the remote `settings.json`.
- H3 completed 20/20 denoising steps, then `torchvision.io.write_video` failed because PyAV 16.1.0 requires an integer/enum for `VideoFrame.pict_type` while torchvision 0.20.1 passes legacy string `"NONE"`.
- Exact host probe: torch 2.5.1+cu121, torchvision 0.20.1+cu121, av 16.1.0; string assignment and tiny torchvision write fail with `TypeError: an integer is required`; enum assignment succeeds.
- Durable failed-run bundle: `datasets/runs/maestro-parity/clean-generated/failed-isolated-retry4-20261009/`.

## USER INTENT
Future clean-machine H3 attempts return a fail-closed media-write verdict and reject an incompatible PyAV media-write path before model loading or queue admission, preventing a one-shot render from completing denoising and losing the artifact at write time.

## OUT OF SCOPE
- Replaying retry4 or running another H3 render.
- Installing/downgrading packages, mutating Wan2GP, model access, provider spend, training, threshold change, or protected-engine changes.
- Changing LTX work or unrelated capability lanes.

## DIFF BUDGET
- About 3 files and under 250 changed LOC.
- Expected surfaces: clean-generated recorder, focused tests, and durable diagnostic evidence.

## Boundary Map
PRODUCES:
- scripts/record_clean_generated_proof.py -> media_write_preflight(host, proof, config) -> dict[str, Any]
  spec: stage a tiny synthetic-frame probe through RenderHost, run it with the authorized offline runtime, require a nonempty MP4, hash artifact/log, and return typed `MEDIA_WRITE_PREFLIGHT_FAILED` before queue admission/render on failure.
- tests/test_clean_generated_proof.py -> real local/fake-host integration coverage
  spec: verify ordered staging and typed failure; no model/render.

CONSUMES:
- WD-bw0h: datasets/runs/maestro-parity/clean-generated/failed-isolated-retry4-20261009/host-logs/render.log -> exact native PyAV failure
  source: file contains completed 20/20 denoising, `TypeError: an integer is required`, and queue count 0/1.
- WD-bw0h: datasets/runs/maestro-parity/clean-generated/failed-isolated-retry4-20261009/queue/final.json -> queue failure contract
  fields: state="failed", one allocated attempt, render_attempted=true, failure_detail contains task count 0/1.
## Story Acceptance Criteria
1. [State] A durable diagnostic record captures exact host versions and tiny-write failure from retry4 evidence or a read-only probe.
2. [State] Clean-generated execution performs a tiny synthetic media-write compatibility check with the authorized offline runtime before queue admission or native render.
3. [Unwanted] Any exception, nonzero exit, absent/empty probe output, or hash mismatch stops with typed `MEDIA_WRITE_PREFLIGHT_FAILED`; no queue job is admitted.
4. [State] Success path records probe path, size, SHA-256, stdout/stderr, and exact runtime versions.
5. [State] Real tests cover success, exception, nonzero exit, missing/empty output, and execution order before queue submission.
6. [Unwanted] No host render/retry, model access/download, package install, provider spend, deletion, protected-file change, or threshold change occurs.
7. [State] Focused tests, backlog lint 0 errors, verifier, release verify, protected parity, whitespace, and exact-head CI pass.

## Testing Requirements
- Unit/fake-host integration tests: mandatory, no mocks of hash/file bytes.
- Commands: focused recorder test; `pvg lint --backlog`; `pvg verify`; `wgp release verify`; `git diff --check`; exact-head CI.

## MANDATORY SKILLS
- pvg
- tool-systematic-debugging

## nd_contract
status: new

### evidence
- Created after retry4 failed at the media-write seam after full denoising.

### proof
- [ ] Pending implementation.

## Acceptance Criteria


## Design


## Notes
### Read-only PyAV diagnostic (orchestrator, 2026-10-09)

On host 3094/3090 runtime, the exact offline PYTHONPATH reports Python 3.12.3, torch 2.5.1+cu121, torchvision 0.20.1+cu121, and PyAV 16.1.0. A direct tiny probe reproduced the retry4 failure without a model render: assigning `VideoFrame.pict_type="NONE"` raises `TypeError: an integer is required`; enum assignment succeeds; `torchvision.io.write_video` on one 8x8 frame fails with the same TypeError. This confirms a media-write dependency incompatibility after successful H3 denoising, not a model or settings-staging failure.

## History
- 2026-10-09T14:31:07Z dep_added: blocks WD-bw0h
- 2026-10-09T14:31:08Z dep_added: blocks WD-fay0
- 2026-10-09T14:31:21Z status: open -> in_progress
- 2026-10-09T14:31:21Z auto-follows: linked to predecessor WD-dhcc
- 2026-10-09T14:31:21Z claimed by dev-WD-mgcd
- 2026-10-09T16:06:42Z status: in_progress -> in_progress
- 2026-10-09T16:06:42Z auto-follows: linked to predecessor WD-5yg9

## Links
- Parent: [[WD-3nod]]
- Blocks: [[WD-bw0h]], [[WD-fay0]]
- Follows: [[WD-dhcc]], [[WD-5yg9]]

## Comments
