---
id: WD-8ioj
title: "Finishing: interpolation, spatial upsampling, grain, codecs, tracked-face refinement, and optional neural path"
status: closed
priority: 2
type: feature
labels: [capability, accepted]
parent: WD-t741
created_at: 2026-09-22T20:24:44Z
created_by: speed
updated_at: 2026-09-23T11:26:58Z
content_hash: "sha256:2201946e90ab53a81c472d389a710bb55b4da4dc5883becc8a0084184637cd5f"
was_blocked_by: [WD-6tox, WD-tkuz]
assignee: dev-WD-8ioj
follows: [WD-6tox, WD-tkuz, WD-fasw]
closed_at: 2026-09-23T11:26:58Z
close_reason: "Accepted: exact-head static, mode/failure, queue, docs, tests, build, CI, and delivery-proof gates all pass."
led_to: [WD-eq1i, WD-gc09]
---

## Description

## USER INTENT
Observable outcome: after generation, Wangp can finish media with x2/x3/x4 interpolation, spatial upsampling, film grain, codec selection, tracked-face refinement, and an optional neural rendering/frame-generation path on supported hardware.

## Context (Embedded)
- The governed repository path is plan -> durable queue -> host render -> QC gates -> assembly -> provenance/recipe; `wgp` is the stable CLI and GPU execution is never implied by planning.
- Finishing is a post-processing graph over immutable source artifacts and must retain exact source/output hashes and measured ffprobe properties.
- The optional neural path is hardware-conditional: unsupported VRAM/backend profiles must produce a typed unavailable result, not fallback silently.
- Maestro’s video upscale operation is coordinated with the video story; this story owns post-generation spatial and temporal finishing semantics.

## OUT OF SCOPE
- Changing accepted render bytes in place or replacing historical evidence.
- A quality claim without declared objective measurements and, where applicable, visual review evidence.

## DIFF BUDGET
Roughly 10 files, under 800 authored changed LOC, excluding models and media.

## Boundary Map
PRODUCES:
- predict/finishing.py -> typed finishing request for interpolation x2/x3/x4, spatial scale, grain, codec, face refinement, and optional neural path
- services/finishing/pipeline.py -> deterministic command graph, stream contracts, and staged output naming
- predict/face_tracking.py -> tracked-face metadata and refinement regions
- wangp/finish_cli.py -> `wgp finish plan|run|probe` command implementation and authorized execution boundary
- docs/finishing.md -> supported operation matrix, codec constraints, hardware profile, and before/after evidence contract
- tests/test_finishing.py -> real-process finishing graph/queue coverage; no mocks
- datasets/runs/maestro-parity/WD-8ioj/ -> finishing run bundles

CONSUMES:
- predict/assembler.py -> existing assembly contract
  spec: existing assembly contract
- predict/v3_recipe.py -> immutable recipe/provenance fields
  spec: immutable recipe/provenance fields
- predict/lf002_canary.py -> real ffprobe measurement patterns
  spec: real ffprobe measurement patterns
- predict/video_capabilities.py -> backend and upscale capability metadata
  spec: backend and upscale capability metadata
- predict/character_packages.py -> character appearance/identity metadata
  spec: character appearance/identity metadata
- services/jobs/queue.py -> durable queue record and attempt transitions
  spec: durable queue record and attempt transitions
- services/jobs/preflight.py -> typed unsupported profile/codec failures
  spec: typed unsupported profile/codec failures
- wangp/cli.py -> stable verb registration and exit-code contract
  spec: stable verb registration and exit-code contract


## Required Outcomes
### no-GPU verifiable now
- Real CLI tests compile each interpolation factor, scale, grain setting, codec, face track, and neural profile into deterministic command graphs; unsupported codecs/profiles fail typed.
- A committed media fixture can exercise deterministic local finishing graph validation and source-hash immutability without claiming GPU neural support.
- A real temporary queue preserves the source hash and target stream contract; missing source, ambiguous face track, unsupported factor/codec, or inadequate profile fails before host work.
- Dry-run reconstruction reproduces the command graph exactly from queue/recipe.

### requires an authorized host render
- Separately authorized runs produce real finished outputs for x2/x3/x4 interpolation, spatial upsampling, film grain, at least two codec targets, and tracked-face refinement, each with before/after ffprobe and hashes.
- On an authorized supported host, run the optional neural rendering/frame-generation path; on an unsupported host, retain the typed unavailability evidence instead of implying success.

## Testing Requirements
- `uv run --frozen --extra dev pytest tests/test_finishing.py -q`, real CLI/files/queue/ffprobe processes with no mocks.
- Assert real exit codes for supported and unsupported graphs and verify accepted source artifacts remain unchanged.
- Authorized finishing bundles require actual ffprobe measurements, hashes, and gate/reviewer evidence; no GPU claim may come from a command graph.

## MANDATORY SKILLS
- pvg

## Delivery Requirements
- Developer must use `pvg story deliver`, paste real command output, and provide an AC table plus hashes for every produced artifact and read-only input.
- A GPU-dependent claim may be made only from a recorded run bundle with command, repository commit, model/asset provenance, queue record, exit status, output hashes, QC/gate evidence, and operator authorization for that run. A plan, prompt, unit test, or intention is not generation evidence.
- No story may silently download a model, contact a host, use a paid provider, or claim a capability the matrix marks unverified.

## nd_contract
status: new

### evidence
- Created 2026-09-22 under epic WD-t741 from the Maestro v2.3.0 capability inventory.

### proof
- [ ] Pending implementation and independent PM acceptance.


## Acceptance Criteria


## Design


## Notes


## nd_contract
status: accepted

### evidence
- PM closeout applied via pvg story accept on 2026-09-23.

### proof
- [x] Story closed after accepted label was applied.


## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-23.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## Implementation Evidence
Summary: Delivered the no-GPU finishing planning slice: typed interpolation/spatial/grain/codec/face/neural declarations, per-backend normalization, deterministic command graphs, immutable non-executable durable records, typed exit-2 failures, reconstruction, and `wgp finish plan|run|probe`. Finished media, neural execution, and before/after measurements remain explicitly unverified.

Commands run:
- `uv run --frozen --extra dev pytest tests/test_finishing_capabilities.py -q --junitxml=/tmp/wd8ioj-evidence/targeting.xml` — exit 0; JUnit parsed: 52 tests, 0 failures, 0 errors, 0 skipped.
- `uv run --frozen --extra dev pytest tests/test_readme_quickstart.py -q --junitxml=/tmp/wd8ioj-evidence/readme.xml` — exit 0; JUnit parsed: 5 tests, 0 failures, 0 errors, 0 skipped.
- `uv run --frozen --extra dev pytest -q --junitxml=/tmp/wd8ioj-evidence/full.xml` — exit 0; JUnit parsed: 1933 tests, 0 failures, 0 errors, 1 skipped (`tests/test_jobs_integration_3090.py::test_live_preflight_against_3090`, intentionally not run because this story forbids host/GPU work). Full output also carries the repository's existing FastAPI/Starlette deprecation warning.
- `uv run --frozen --extra dev python /tmp/wd8ioj_capture.py` — captured human and `--json` output for plan/probe/run/reconstruct modes and all 22 typed failure classes; every failure exited 2. Queue evidence: `finishing_plan_records=1`, no `jobs` table, plan `next_admissible=None`, genuine render job still admissible; database/source/datasets byte-unchanged; reconstruction `all_match=true`; shadowed `ssh`/`curl`/`wget`/`nvidia-smi` calls empty.
- `pvg verify predict/finishing.py services/finishing/__init__.py services/finishing/pipeline.py wangp/finish_cli.py wangp/cli.py docs/finishing-capabilities.md README.md tests/test_finishing_capabilities.py --format=text --include-tests` — `VERIFY: PASSED (6 files scanned, 0 issues)`.
- `uv build --out-dir /tmp/wd8ioj-evidence/build` — exit 0; exactly one wheel and one sdist. SHA-256 wheel `7741eb27dee452282fff23743ad4c9ef38c65eb2391898b7e236d226e7d6fc7f`; sdist `73ea79f6c23d4e5c94d2ceb513fba8243832f27ac7b53bb885def72f504f8a87`.
- PR #172 exact head check-run `test` completed `success` for SHA below.
- Coverage: not measured; the requested frozen JUnit/build/CI gates were run without a coverage configuration or claim.

SHA: 2fbb7d483a929d757264dcdfa7ece55221a8b509

### CI/Test Results
- Local targeted: PASS — 52/52 executed, 0 failures, 0 errors, 0 skipped, exit 0.
- Local README drift: PASS — 5/5 executed, 0 failures, 0 errors, 0 skipped, exit 0.
- Local full suite: PASS with one host-bound skip — 1933 collected, 1932 passed, 1 skipped, 0 failures, 0 errors, exit 0.
- Build: PASS — one wheel, one sdist, exit 0.
- GitHub CI PR #172 `test` at exact head `2fbb7d483a929d757264dcdfa7ece55221a8b509`: SUCCESS.
- Read-only proof: PASS — committed source and full `datasets/` tree hashes unchanged; empty shadowed host-command log.
- Queue proof: PASS — durable plan records are non-executable and non-admissible while a genuine job remains admissible.
- Reconstruction proof: PASS — command graph, backend settings, and seed hashes rebuilt exactly with `hidden_mutation=false`.

### AC Verification
| AC | Result | Evidence |
| --- | --- | --- |
| Typed CLI planning covers every interpolation factor, spatial factor, grain setting, supported codec pair, explicit face track, and neural declaration | PASS | `tests/test_finishing_capabilities.py`; targeting JUnit 52/52 |
| Unsupported codecs/profiles and every incomplete input fail typed before durable state/host work | PASS | 22 captured human+JSON failure modes, all exit 2; no partial DB where applicable |
| Committed media exercises deterministic graph validation and source immutability without GPU claim | PASS | Existing committed `datasets/runs/provenance/v3-original/v3_c1.mp4`; source/dataset hashes unchanged |
| Durable queue preserves source hash and stream contract and cannot drain into rendering | PASS | `services/finishing/pipeline.py`; separate immutable table, no `jobs` table, genuine job admissible |
| Dry-run reconstruction reproduces exact command/settings/seed hashes | PASS | reconstruction `all_match=true`, `hidden_mutation=false` |
| CLI/README/docs verb and capability contracts stay synchronized | PASS | README drift 5/5; live `finish` verb/subverb next-command assertions |
| Renderer/queue/QC/AV/retry semantics unchanged; no render/download/host contact | PASS | diff touches only planning surface/docs/tests; empty shadowed host-command log |
| Authorized real finished outputs, before/after ffprobe, and optional neural execution | not verified - requires authorized host run | No host/GPU/render work was performed or claimed |

## nd_contract
status: delivered

### evidence
- Branch: `story/WD-8ioj`
- PR: https://github.com/jmanhype/wangp-dspy/pull/172
- SHA: 2fbb7d483a929d757264dcdfa7ece55221a8b509
- Local JUnit/build outputs and captured mode/failure evidence: `/tmp/wd8ioj-evidence/`
- GitHub CI exact-head `test` conclusion: success.

### proof
- [x] Typed finishing request models cover interpolation x2/x3/x4, spatial x2/x3/x4, film grain, codec selection, tracked-face declarations, and a declared-unavailable neural path.
- [x] Per-backend settings normalization and deterministic command graphs produce non-executable plan records.
- [x] The real admission path cannot drain finishing records while a genuine render job remains admissible.
- [x] Every no-GPU incomplete/unsupported class emits typed exit-2 diagnostics with a live `wgp finish` next command.
- [x] Seed-based reconstruction matches command graph, backend settings, and seed hashes.
- [x] CLI, README verb map, capability row, documentation index, and finishing docs are synchronized.
- [x] Local targeted, README, full suite, build, and exact-head CI gates pass under the stated no-host/no-GPU boundary.
- [x] Read-only proof confirms source/dataset immutability and zero shadowed `ssh`/`curl`/`wget`/`nvidia-smi` calls.

## History
- 2026-09-22T20:24:46Z dep_added: blocked_by WD-6tox
- 2026-09-22T20:24:46Z dep_added: blocked_by WD-tkuz
- 2026-09-22T20:26:48Z dep_added: blocks WD-gc09
- 2026-09-22T22:50:10Z dep_removed: was_blocked_by WD-6tox
- 2026-09-23T09:16:29Z dep_removed: was_blocked_by WD-tkuz
- 2026-09-23T09:36:22Z status: open -> in_progress
- 2026-09-23T09:36:22Z auto-follows: linked to predecessor WD-6tox
- 2026-09-23T09:36:22Z auto-follows: linked to predecessor WD-tkuz
- 2026-09-23T09:36:22Z claimed by dev-WD-8ioj
- 2026-09-23T10:53:44Z status: in_progress -> in_progress
- 2026-09-23T10:53:44Z auto-follows: linked to predecessor WD-fasw
- 2026-09-23T11:26:58Z status: in_progress -> closed
- 2026-09-23T11:26:58Z dep_removed: no_longer_blocks WD-gc09

## Links
- Parent: [[WD-t741]]
- Was blocked by: [[WD-6tox]], [[WD-tkuz]]
- Follows: [[WD-6tox]], [[WD-tkuz]], [[WD-fasw]]
- Led to: [[WD-eq1i]], [[WD-gc09]]

## Comments
