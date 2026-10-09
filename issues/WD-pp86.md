---
id: WD-pp86
title: "Stage no-install H3 PyAV media-write compatibility"
status: in_progress
priority: 0
type: task
labels: [bug, evidence, qc, integration, delivered]
parent: WD-3nod
created_at: 2026-10-09T16:17:23Z
created_by: speed
updated_at: 2026-10-09T17:40:46Z
content_hash: "sha256:1b49af3b8c4c935d29bd83012b66188718c96dd36573aba3b0f127e459311f0e"
blocks: [WD-bw0h, WD-fay0]
follows: [WD-mgcd, WD-dhcc, WD-5yg9]
assignee: dev-WD-pp86
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

## Links
- Parent: [[WD-3nod]]
- Blocks: [[WD-bw0h]], [[WD-fay0]]
- Follows: [[WD-mgcd]], [[WD-dhcc]], [[WD-5yg9]]

## Comments
