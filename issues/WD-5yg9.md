---
id: WD-5yg9
title: "Preflight H3 PyAV media-write compatibility"
status: open
priority: 0
type: task
labels: [bug, evidence, qc]
parent: WD-3nod
created_at: 2026-10-09T14:30:00Z
created_by: speed
updated_at: 2026-10-09T14:30:00Z
content_hash: "sha256:d82d80b2064537f1c10bef2f12607fd71000a6d3c324381bf8a7aa8a680b5657"
blocks: [WD-bw0h, WD-fay0]
---

## Description
## Context (Embedded)
- WD-bw0h retry4 consumed its v3 one-shot authorization at main `37a5d19a50b58be381e793cd10ba9f4bb5bd1fb0`.
- The prior settings-staging defect was cleared: WanGP loaded the remote `settings.json`.
- H3 completed 20/20 denoising steps, then `torchvision.io.write_video` failed because PyAV 16.1.0 requires an integer/enum for `VideoFrame.pict_type` while torchvision 0.20.1 passes the legacy string `"NONE"`.
- Exact host probe: torch 2.5.1+cu121, torchvision 0.20.1+cu121, av 16.1.0; string assignment and tiny torchvision write fail with `TypeError: an integer is required`; enum assignment succeeds.
- Durable failed-run bundle/PR: `datasets/runs/maestro-parity/clean-generated/failed-isolated-retry4-20261009/` and PR 237.

## USER INTENT
Future clean-machine H3 attempts must reject an incompatible PyAV media-write path before loading models or spending a one-shot render authorization, rather than completing denoising and losing the artifact at write time.

## OUT OF SCOPE
- Replaying retry4 or running another H3 render.
- Installing/downgrading packages, mutating Wan2GP, model access, provider spend, training, threshold change, or protected-engine changes.
- Changing LTX work or other capability lanes.

## DIFF BUDGET
- About 3 files and under 250 changed LOC.
- Expected surfaces: clean-generated recorder, focused tests, and durable diagnostic evidence.

## Boundary Map
PRODUCES:
- scripts/record_clean_generated_proof.py -> media_write_preflight(host, proof, config) -> dict[str, Any]
  spec: stage an exact tiny synthetic-frame probe script through RenderHost, run it with the authorized offline runtime, require a nonempty MP4, hash the probe artifact/log, and return typed `MEDIA_WRITE_PREFLIGHT_FAILED` on any exception or empty output before queue admission/render.
- tests/test_clean_generated_proof.py -> real local/unit integration coverage using a fake host for ordered staging and typed failure; no model/render.

CONSUMES:
- WD-bw0h retry4 evidence -> host-logs/render.log and queue/final.json -> exact observed PyAV failure.
- Existing recorder `push(...) -> str`, `probe(...)`, and offline wrapper contract.

## Acceptance Criteria
1. [State] A durable diagnostic record captures the exact host versions and tiny-write failure from retry4 evidence or a read-only probe.
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


## History
- 2026-10-09T14:30:07Z dep_added: blocks WD-bw0h
- 2026-10-09T14:30:08Z dep_added: blocks WD-fay0

## Links
- Parent: [[WD-3nod]]
- Blocks: [[WD-bw0h]], [[WD-fay0]]

## Comments
