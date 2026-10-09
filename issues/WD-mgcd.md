---
id: WD-mgcd
title: "Preflight H3 PyAV media-write compatibility"
status: closed
priority: 0
type: task
labels: [bug, evidence, qc, accepted]
parent: WD-3nod
created_at: 2026-10-09T14:30:58Z
created_by: speed
updated_at: 2026-10-09T16:13:52Z
content_hash: "sha256:a40e0f6698fba9bef834fbaa1527d3db12bcd7f95ba88ef0fabd1c4b0588a57d"
assignee: dev-WD-mgcd
follows: [WD-dhcc, WD-5yg9]
closed_at: 2026-10-09T16:13:51Z
close_reason: "Accepted: exact-head CI, focused behavioral proof, diagnostic hash, fail-closed ordering, queue exclusion, and required release/QC gates satisfy WD-mgcd."
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
Commands run:
- `/Users/Shared/HermesWorkspace/wangp-dspy/.venv/bin/python -m pytest -q tests/test_clean_generated_proof.py --junitxml=/tmp/WD-mgcd-focused-final.xml`
- `/Users/Shared/HermesWorkspace/wangp-dspy/.venv/bin/python -m pytest -q tests/test_clean_generated_proof.py -k media_write`
- `pvg verify scripts/record_clean_generated_proof.py tests/test_clean_generated_proof.py --format=text --include-tests`
- `/Users/Shared/HermesWorkspace/wangp-dspy/.venv/bin/wgp release verify`
- `pvg lint --backlog`
- `git diff --exit-code origin/main -- services/jobs/queue.py services/director/renderers/policy.py services/director/wiring.py services/jobs/preflight.py scripts/run_film.py`
- `git diff --check`
- GitHub Actions exact-head CI run `37950722805` (`uv run --frozen --extra dev pytest -q` and `uv build`)
## PM Decision
ACCEPTED [2026-10-09]: Evidence reviewed and meets the bar.

## nd_contract
status: accepted

### evidence
- Exact head, PR ref, worktree, diagnostic SHA-256, ordering, static gates, focused-test proof, and exact-head CI run 37950722805 were reviewed.
- AC #1 through AC #7 are verified from delivered evidence and read-only checks.

### proof
- [x] AC #1: diagnostic bytes and SHA-256 match.
- [x] AC #2: preflight precedes relocation, models, wrapper, render, and queue.
- [x] AC #3: all failure paths are typed and exclude queue admission.
- [x] AC #4: success evidence records versions, output, hashes, stdout, stderr, and log hash.
- [x] AC #5: focused tests cover success, exception, nonzero, missing, empty, hash mismatch, and ordering.
- [x] AC #6: delivered scope contains no prohibited action or protected-file change.
- [x] AC #7: focused tests, CI, lint, verifier, release, protected parity, whitespace, and diff evidence pass.


## Implementation Evidence

Summary: WD-mgcd now returns a typed fail-closed PyAV media-write verdict before model checks, storage relocation, queue database creation, queue admission, or H3 render dispatch. A real no-model probe records exact Python/torch/torchvision/PyAV versions and hashes a one-frame video write. This prevents another one-shot H3 authorization from being consumed by the known incompatible torchvision/PyAV path.

Commit SHA: 510d2234826a4c283648da4c1be646e29932fd37
PR: https://github.com/jmanhype/wangp-dspy/pull/238

Changed files:
- `scripts/record_clean_generated_proof.py`
- `tests/test_clean_generated_proof.py`
- `datasets/runs/maestro-parity/WD-mgcd/README.md`
- `datasets/runs/maestro-parity/WD-mgcd/pyav-probe.txt`

Preflight contract:
- Runs immediately after fresh remote-root validation and before storage relocation/model checks/offline-wrapper/render/queue.
- Captures Python, torch, torchvision, and PyAV versions.
- Performs one no-model `torchvision.io.write_video` probe.
- Requires fresh local and remote outputs, positive size, and exact SHA-256.
- Records stdout/stderr, output size/hash/path, log path/hash.
- Fails typed `MEDIA_WRITE_PREFLIGHT_FAILED` on exception, nonzero exit, missing/empty output, malformed versions, or hash mismatch.
- No queue database is created on failure.

Diagnostic:
- Path: `datasets/runs/maestro-parity/WD-mgcd/pyav-probe.txt`
- SHA-256: `ede7669366e852393373d801027e342dac0a3dcaa42bbad5083dc7a9281a6e8e`
- Observed Python 3.12.3, torch 2.5.1+cu121, torchvision 0.20.1+cu121, PyAV 16.1.0; legacy string assignment and tiny write fail; integer enum assignment succeeds.

### CI/Test Results

- Focused changed test file: 50 tests, 0 failures, 0 errors, 0 skipped.
- Media-write selection: 9 passed, 41 deselected.
- Exact-head GitHub CI run `37950722805`: SUCCESS at `510d2234826a4c283648da4c1be646e29932fd37`; full test suite and distributable build passed in 20m12s.
- `pvg verify ... --format=text --include-tests`: PASSED, 0 issues.
- `wgp release verify`: release=ready, tag_created=false.
- `pvg lint --backlog`: 0 errors, 1 non-blocking story-wording review finding.
- Protected-file parity versus `origin/main`: PASS.
- `git diff --check`: PASS.
- Independent adversarial review: `REVIEW_RESULT: APPROVED`.

Invalid local evidence disclosure:
- A attempted full local suite using the main checkout interpreter in this worktree mixed checkout contexts, produced failures, and timed out. It is discarded as invalid evidence, not counted as a pass or product failure. Exact-head CI is the authoritative full-suite result.

LEARNINGS:
- Do not reuse a main checkout virtualenv as a full-suite environment for a separate worktree; import/package context can differ and produce invalid failures.
- A successful model denoise is not a generated-artifact proof; the media encoder must be preflighted before consuming a one-shot authorization.
- Version probes alone are insufficient. The exact `torchvision.io.write_video` path must be exercised with a no-model synthetic frame.
- Preflight ordering is part of the safety contract: it must precede storage relocation, model loading, queue database creation, admission, and render.

### AC Verification

| AC | Result | Evidence |
|---|---|---|
| 1 | PASS | Raw diagnostic preserved at exact SHA-256 `ede7669366e852393373d801027e342dac0a3dcaa42bbad5083dc7a9281a6e8e`. |
| 2 | PASS | `media_write_preflight` runs before storage/model/queue/render. |
| 3 | PASS | Exception/nonzero/missing/empty/hash mismatch all yield `MEDIA_WRITE_PREFLIGHT_FAILED` with no queue DB. |
| 4 | PASS | Versions, stdout/stderr, output size/hash/path, and log hash recorded. |
| 5 | PASS | Nine media-write tests cover success and all required failure/order paths. |
| 6 | PASS | No host render/retry, model access/download, install, spend, deletion, protected-file change, or threshold change occurred. |
| 7 | PASS | Focused tests, exact-head CI, verifier, release, lint, protected parity, and diff checks pass. |

## nd_contract
status: delivered

### evidence
- PR head `510d2234826a4c283648da4c1be646e29932fd37`.
- PR: https://github.com/jmanhype/wangp-dspy/pull/238
- Exact-head CI run `37950722805`: SUCCESS.
- Focused tests: 50/50 pass.
- Independent review: APPROVED.

### proof
- [x] AC #1: Exact diagnostic preserved.
- [x] AC #2: Media-write preflight runs before queue/render.
- [x] AC #3: Typed failure prevents queue admission.
- [x] AC #4: Successful probe evidence fields recorded.
- [x] AC #5: Real success/failure/order tests pass.
- [x] AC #6: No prohibited action occurred.
- [x] AC #7: Local deterministic gates and exact-head CI pass.

## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-10-09.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## History
- 2026-10-09T14:31:07Z dep_added: blocks WD-bw0h
- 2026-10-09T14:31:08Z dep_added: blocks WD-fay0
- 2026-10-09T14:31:21Z status: open -> in_progress
- 2026-10-09T14:31:21Z auto-follows: linked to predecessor WD-dhcc
- 2026-10-09T14:31:21Z claimed by dev-WD-mgcd
- 2026-10-09T16:06:42Z status: in_progress -> in_progress
- 2026-10-09T16:06:42Z auto-follows: linked to predecessor WD-5yg9
- 2026-10-09T16:13:51Z status: in_progress -> closed
- 2026-10-09T16:13:51Z dep_removed: no_longer_blocks WD-bw0h
- 2026-10-09T16:13:52Z dep_removed: no_longer_blocks WD-fay0

## Links
- Parent: [[WD-3nod]]
- Follows: [[WD-dhcc]], [[WD-5yg9]]

## Comments
