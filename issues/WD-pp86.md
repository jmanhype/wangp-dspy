---
id: WD-pp86
title: "Stage no-install H3 PyAV media-write compatibility"
status: closed
priority: 0
type: task
labels: [bug, evidence, qc, integration, accepted]
parent: WD-3nod
created_at: 2026-10-09T16:17:23Z
created_by: speed
updated_at: 2026-10-09T17:47:58Z
content_hash: "sha256:29748fffcd3814bae42d23a0ae1fd3ae10c42aba65b3d12d08825521a2dcf636"
follows: [WD-mgcd, WD-dhcc, WD-5yg9]
assignee: dev-WD-pp86
closed_at: 2026-10-09T17:47:56Z
close_reason: "Accepted: exact head, raw and generated proof hashes, focused test and exact-head CI evidence, fail-closed boundaries, and all seven ACs verified."
led_to: [WD-82q2]
---

## Description
## Context (Embedded)

- Base stack: accepted PR 238 head `510d2234826a4c283648da4c1be646e29932fd37` (WD-mgcd).
- WD-bw0h retry4 completed H3 denoising but failed media write because torchvision `0.20.1+cu121` passes legacy string `"NONE"` to PyAV `16.1.0`, whose `VideoFrame.pict_type` setter now requires an integer/enum.
- WD-mgcd now fails this incompatibility closed before queue/render. That protects one-shot authorizations but does not repair the write path.
- A read-only temporary-host proof has already demonstrated a no-install compatibility shim. When a directory containing a `sitecustomize.py` patch precedes the authorized offline PYTHONPATH, the exact `torchvision.io.video` writer is replaced by a same-source copy with `frame.pict_type = 0`; both `torchvision.io.video.write_video` and `torchvision.io.write_video` refer to the patched function, and a 2-frame 8x8 synthetic tensor writes a nonempty 1,555-byte MP4.
- Successful shim proof: `/tmp/h3_pyav_compat_success.txt`, SHA-256 `a356597b5a4954a3b9c0fa291604f6d6b523040f36e4ff92f651b5da3f08fafe`.

## USER INTENT

The next authorized H3 clean-machine attempt returns a successful media-write preflight and should pass the no-model media-write preflight and preserve WanGP's completed video instead of losing a successful 20-step denoising run at the final encoder call, without installing packages or mutating the shared Wan2GP checkout.

## OUT OF SCOPE

- Any GPU render/H3 retry/model access: requires a new operator authorization after this repair merges.
- Package installation, downgrade, provider spend, training, deletion, threshold change, or protected-engine change.
- Mutating `/home/straughter/Wan2GP` or its source files.
- Changing LTX behavior or unrelated lanes.

## DIFF BUDGET

- About 4 files and under 400 authored/evidence LOC.
- Expected surfaces: clean-generated recorder, focused tests, and durable PyAV compatibility proof.

## Boundary Map

PRODUCES:
- scripts/record_clean_generated_proof.py -> pyav_compat_sitecustomize() -> str
  spec: deterministic, no-install Python source that patches only the exact legacy torchvision writer when the known `frame.pict_type = "NONE"` source is present; otherwise raises/records a typed compatibility boundary.
- scripts/record_clean_generated_proof.py -> stage_pyav_compat(host, proof, config) -> dict[str, Any]
  event: stages the exact shim in the fresh authorized remote root and prepends its directory to the offline wrapper PYTHONPATH before media-write preflight.
- datasets/runs/maestro-parity/WD-pp86/pyav-compat-success.txt -> exact successful temporary-host proof
  source: preserve the raw proof bytes and SHA-256 `a356597b5a4954a3b9c0fa291604f6d6b523040f36e4ff92f651b5da3f08fafe`.

CONSUMES:
- WD-mgcd: scripts/record_clean_generated_proof.py -> media_write_preflight(host, proof, config) -> dict[str, Any]
  source: no-model synthetic write gate that must run after compatibility staging and must pass before queue admission.
- WD-bw0h: datasets/runs/maestro-parity/clean-generated/failed-isolated-retry4-20261009/host-logs/render.log -> observed PyAV failure
  source: completed 20/20 denoise followed by `TypeError: an integer is required` and queue count 0/1.

## Story Acceptance Criteria

1. [State] Preserve the exact successful shim proof with SHA-256 `a356597b5a4954a3b9c0fa291604f6d6b523040f36e4ff92f651b5da3f08fafe`.
2. [State] Implement a deterministic no-install compatibility shim that only rewrites the exact known legacy writer source from `frame.pict_type = "NONE"` to `frame.pict_type = 0`, updates both torchvision module attributes, and refuses unexpected/absent source rather than broadly monkeypatching.
3. [State] Stage the shim inside the fresh authorized remote work root and prepend that exact directory to the offline wrapper PYTHONPATH before running WD-mgcd media-write preflight.
4. [State] The no-model media-write preflight passes under the shim and records versions, stdout/stderr, output size/hash, and log hash before queue admission.
5. [Unwanted] If shim staging, PYTHONPATH ordering, patch application, or the synthetic write fails, stop typed before storage relocation, model checks, queue creation/admission, or render; no shared Wan2GP source mutation occurs.
6. [State] Real focused tests cover successful patch/write, unexpected writer source, failed `torchvision.io` alias patch, missing shim/path ordering, failed media write, and preflight ordering before queue.
7. [State] Focused tests, scoped verifier, backlog lint 0 errors, release verify, protected parity, whitespace, and exact-head CI pass.

## Testing Requirements

- Real unit/fake-host integration tests are mandatory; no mocks of filesystem bytes, source inspection, hash, or subprocess environment.
- A local fixture may emulate the exact legacy writer/PyAV behavior only when real torch/torchvision/PyAV are unavailable; it must be labeled fixture evidence and cannot be represented as host proof.
- Commands: focused clean-generated tests; `pvg verify`; `pvg lint --backlog`; `wgp release verify`; protected-file parity; `git diff --check`; exact-head CI.

## MANDATORY SKILLS

- pvg
- tool-systematic-debugging

## nd_contract
status: new

### evidence
- Created after PR 238 was accepted and the temporary no-install shim proof succeeded.

### proof
- [ ] Pending implementation.

## Acceptance Criteria


## Design


## Notes


## nd_contract
status: accepted

### evidence
- PM closeout applied via pvg story accept on 2026-10-09.

### proof
- [x] Story closed after accepted label was applied.


## Implementation Evidence

Summary: WD-pp86 stages a deterministic no-install PyAV compatibility shim in the exact authorized remote work root, prepends that directory to the offline runtime PYTHONPATH, and requires the no-model media-write preflight to pass before storage relocation, model checks, queue construction/admission, or H3 render. Shared Wan2GP source is not mutated.

Commit SHA: 8a03f9352dbde33ee1b372c40b233161eb10add9
PR: https://github.com/jmanhype/wangp-dspy/pull/239
Accepted implementation base: PR 238 head `510d2234826a4c283648da4c1be646e29932fd37`

Changed files:
- `scripts/record_clean_generated_proof.py`
- `tests/test_clean_generated_proof.py`
- `tests/test_clean_generated_pyav_compat.py`
- `datasets/runs/maestro-parity/WD-pp86/pyav-compat-success.txt`

Shim boundaries:
- Generated `sitecustomize.py` is 1,385 bytes with SHA-256 `9dfe8c270fc888acde082365a5d9d88208773679a4d5944940fdd8a97a4f0cb3`.
- It rejects any environment where its directory does not lead PYTHONPATH.
- It requires `torchvision.io.write_video` and `torchvision.io.video.write_video` to alias the same original writer.
- It requires exactly one whole-line legacy assignment `frame.pict_type = "NONE"`.
- It replaces only that assignment with integer `0`, patches both aliases, and exposes `PYAV_COMPAT_APPLIED=True`.
- Unexpected source, alias, or patch behavior exits code 78 rather than being swallowed.
- Staging verifies exact remote path and fetched byte hash.
- Offline wrapper verifies the staged shim hash before normal site startup and prepends its directory.
- Media-write script requires `PYAV_COMPAT_APPLIED` before importing dependencies or writing.
- Any staging, ordering, patch, media-write, or hash failure stops before storage/model/queue/render.

Raw successful temporary-host proof:
- Path: `datasets/runs/maestro-parity/WD-pp86/pyav-compat-success.txt`
- SHA-256: `a356597b5a4954a3b9c0fa291604f6d6b523040f36e4ff92f651b5da3f08fafe`
- Recorded `sitecustomize torchvision torchvision.io.video True`, patched first line number 1, and a 1,555-byte synthetic write. This is proof of the no-install shim on the temporary host; it is not an H3 render or generated clean-machine artifact.

### CI/Test Results

- Combined focused tests: 61 tests, 0 failures, 0 errors, 0 skipped.
- `pvg verify scripts/record_clean_generated_proof.py tests/test_clean_generated_proof.py tests/test_clean_generated_pyav_compat.py --format=text --include-tests`: PASSED, 3 files, 0 issues.
- `wgp release verify`: release=ready, tag_created=false.
- `pvg lint --backlog`: 163 scanned, 0 errors, 0 review findings.
- Protected-file/host-adapter parity versus accepted base and `origin/main`: PASS.
- `git diff --check`: PASS.
- Independent adversarial review: `REVIEW_RESULT: APPROVED`.
- Exact-head GitHub CI run `37964950342`: SUCCESS at `8a03f9352dbde33ee1b372c40b233161eb10add9`; full test suite and distributable build passed.

Commands run:
- `/Users/Shared/HermesWorkspace/wangp-dspy/.venv/bin/python -m pytest -q tests/test_clean_generated_proof.py tests/test_clean_generated_pyav_compat.py --junitxml=/tmp/WD-pp86-independent.xml`
- `pvg verify scripts/record_clean_generated_proof.py tests/test_clean_generated_proof.py tests/test_clean_generated_pyav_compat.py --format=text --include-tests`
- `/Users/Shared/HermesWorkspace/wangp-dspy/.venv/bin/wgp release verify`
- `pvg lint --backlog`
- `git diff --exit-code 510d2234826a4c283648da4c1be646e29932fd37 -- services/jobs/queue.py services/director/renderers/policy.py services/director/wiring.py services/jobs/preflight.py scripts/run_film.py host/wangp_adapter.py host/render_host.py`
- `git diff --check`
- GitHub Actions exact-head CI run `37964950342`

LEARNINGS:
- The compatibility layer must be narrowly source-bound; broad monkeypatching would turn a version workaround into an unsafe runtime fork.
- Startup failure cannot rely on an ordinary Python exception because sitecustomize exceptions are swallowed; explicit exit code 78 is required.
- Both `torchvision.io.video.write_video` and `torchvision.io.write_video` must be patched and checked because callers import different aliases.
- A successful no-model synthetic write is required before consuming another one-shot H3 authorization; it is necessary but not sufficient for a generated-artifact claim.

### AC Verification

| AC | Result | Evidence |
|---|---|---|
| 1 | PASS | Raw proof preserved at exact required SHA-256. |
| 2 | PASS | Exact whole-line source replacement and both alias checks implemented. |
| 3 | PASS | Shim staged at exact authorized root and prepended to offline PYTHONPATH. |
| 4 | PASS | No-model media-write preflight verifies patch application, versions, output hash/size, and log hash. |
| 5 | PASS | Staging/order/patch/media failures stop typed before storage/model/queue/render; Wan2GP unchanged. |
| 6 | PASS | Real subprocess fixtures cover success, source drift, alias failure, missing/changed shim, write failure, path order, and queue exclusion. |
| 7 | PASS | Focused tests, verifier, lint, release, protected parity, whitespace, and exact-head CI pass. |

## nd_contract
status: delivered

### evidence
- PR head `8a03f9352dbde33ee1b372c40b233161eb10add9`.
- PR: https://github.com/jmanhype/wangp-dspy/pull/239
- Exact-head CI run `37964950342`: SUCCESS.
- Combined focused tests: 61/61 pass.
- Independent review: APPROVED.

### proof
- [x] AC #1: Raw proof preserved exactly.
- [x] AC #2: Exact source-bound compatibility function implemented.
- [x] AC #3: Authorized-root staging and PYTHONPATH ordering implemented.
- [x] AC #4: No-model media-write preflight passes under shim in fixture and recorded host proof.
- [x] AC #5: Failures stop before storage/model/queue/render; no shared Wan2GP mutation.
- [x] AC #6: Real subprocess positive/negative/order tests pass.
- [x] AC #7: All local deterministic gates and exact-head CI pass.

## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-10-09.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## History
- 2026-10-09T16:17:52Z dep_added: blocks WD-bw0h
- 2026-10-09T16:17:53Z dep_added: blocks WD-fay0
- 2026-10-09T16:18:44Z status: open -> in_progress
- 2026-10-09T16:18:44Z auto-follows: linked to predecessor WD-dhcc
- 2026-10-09T16:18:44Z claimed by dev-WD-pp86
- 2026-10-09T17:40:42Z status: in_progress -> in_progress
- 2026-10-09T17:40:43Z auto-follows: linked to predecessor WD-5yg9
- 2026-10-09T17:47:56Z status: in_progress -> closed
- 2026-10-09T17:47:56Z dep_removed: no_longer_blocks WD-bw0h
- 2026-10-09T17:47:57Z dep_removed: no_longer_blocks WD-fay0

## Links
- Parent: [[WD-3nod]]
- Follows: [[WD-mgcd]], [[WD-dhcc]], [[WD-5yg9]]
- Led to: [[WD-82q2]]

## Comments
