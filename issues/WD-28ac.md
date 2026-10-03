---
id: WD-28ac
title: "LTX dependency terminalization batch"
status: in_progress
priority: 1
type: task
labels: [video, evidence, external-integration, operator-decision]
parent: WD-3nod
created_at: 2026-09-29T07:05:33Z
created_by: speed
updated_at: 2026-10-03T20:01:14Z
content_hash: "sha256:fb29aa81f6f5ff4112e13f3a98e561c0419d94f8c023b68eb077e8af03be68c2"
blocks: [WD-fay0]
follows: [WD-23rs, WD-p587, WD-1s5s, WD-cuzw, WD-he8i]
was_blocked_by: [WD-1s5s, WD-cuzw]
assignee: dev-WD-28ac
---

## Description
## Context

Seven video capability cells remain non-terminal `dependency_blocked` after the accepted WD-m7xw and WD-osfm runs:

- LTX-2.5: outpaint, repaint, recast, upscale
- LTX-2.3: outpaint, recast, upscale

These are exact missing-asset boundaries, not hardware-infeasibility verdicts and not inherited successes from each row's verified operations. The goal requires every affected cell to end at either checker-valid `host_run_verified` or an operator-approved terminal boundary.

HEAD-only metadata collection downloaded zero model bytes. The required unique assets are:

| Asset | Destination | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| `ltx-2.3-22b-ic-lora-ingredients-0.9.safetensors` | `/home/straughter/Wan2GP/ckpts/ltx-2.3-22b-ic-lora-ingredients-0.9.safetensors` | 1,308,778,338 | `4647f4f18c87208f949b6f473d49af679ddd87532b40718480e5153852f1f1ba` |
| `ltx-2.3-22b-ic-lora-outpaint.safetensors` | `/home/straughter/Wan2GP/ckpts/ltx-2.3-22b-ic-lora-outpaint.safetensors` | 1,308,756,416 | `76df7c1ccbe8d657e38f38e8defbc0755a8d57b1a2b34fcad1f6376f4ce289f0` |
| `ltx-2.3-22b-ic-lora-in-outpainting-0.9.safetensors` | `/home/straughter/Wan2GP/ckpts/ltx-2.3-22b-ic-lora-in-outpainting-0.9.safetensors` | 1,308,778,338 | `748bca2d539cf2776abe801da96f06d6f31eec64f2354dea0f4b336292d3b837` |
| `ltx-2.5-22b-ic-lora-pixel-spatial-upscaler-x2-1.0.safetensors` | `/home/straughter/Wan2GP/ckpts/ltx-2.5-22b-ic-lora-pixel-spatial-upscaler-x2-1.0.safetensors` | 327,322,640 | `229e549af18993e1670ad5dac7d2d8d03bb558ae446ac4ee23f8ba1263783996` |
| `ltx-2.3-22b-dev_diffusion_model_quanto_int8.safetensors` | `/home/straughter/Wan2GP/ckpts/ltx-2.3-22b-dev_diffusion_model_quanto_int8.safetensors` | 19,447,662,547 | `f27d0effb85903172d976f1929dc0b3a204944ff014574eaab51cdc5e54f0f22` |

Total unique download volume: **23,701,298,279 bytes**. The batch is below the prior 60 GB ceiling but still requires explicit model-download and GPU-host authorization.

## USER INTENT

The operator wants the remaining LTX rows to have truthful terminal outcomes rather than ambiguous dependency blocks. Observable outcome: after authorization, the operator can run the canonical checker and receive an explicit pass/fail result for each of the seven affected cell bundles.

## Operator authorization status

**NOT AUTHORIZED.** No verbatim operator approval for this batch is present. Until recorded, this story must remain deferred and no worker may contact host `3090`, download any asset, mutate storage, or run a generation.

Authorization must explicitly approve:

- all five assets and exactly 23,701,298,279 download bytes;
- host `3090` and the governed Wan2GP execution path;
- only the seven named operations;
- no training, provider spend, unrelated mutation, threshold change, or protected-engine semantic change;
- reversible storage handling and deletion prohibition.

## OUT OF SCOPE

- WD-bw0h clean-machine H3 retry; it has a separate consumed-authorization boundary.
- LTX blend; it already has an accepted typed backend boundary.
- Any already verified LTX operation, existing media, native log, or provenance record.
- Any model or operation not named above.
- Training, registry publication, GUI work, or protected-engine changes.

## DIFF BUDGET

About 5 files and under 500 authored/evidence LOC, excluding native logs and media bytes.

## Boundary Map
PRODUCES:
- datasets/runs/maestro-parity/ltx-dependency-terminalization/model-assets.json -> exact five-asset `wangp-dspy.model-assets/v1` manifest with source, destination, size, SHA-256, license, and authorization linkage
- datasets/runs/maestro-parity/ltx-dependency-terminalization/ -> seven-operation download, host-run, media/gate, boundary, checker, and matrix-transition evidence
- docs/video-capabilities.md -> terminal updates for exactly the seven named dependency-blocked cells
- tests/test_ltx_dependency_manifest.py -> manifest totals, hashes, cell ownership, and fail-closed drift/authorization tests

CONSUMES:
- WD-m7xw: datasets/runs/maestro-parity/WD-m7xw/dependency-boundaries.md -> exact four LTX-2.5 missing-asset boundaries
  source: operation, native exit/stage, absent asset identity, and zero-output evidence; do not inherit successful-operation evidence.
- WD-osfm: datasets/runs/maestro-parity/WD-osfm/boundary-evidence.json -> exact three LTX-2.3 missing-asset boundaries
  source: records[].operation, dependency, dependency_source, failing_stage, log, and boundary fields.
- WD-23rs: scripts/verify_maestro_parity.py -> verify_bundle(bundle: Path) -> VerificationReport; verify_checker_receipt(...) -> VerificationReport
  source: canonical pass/fail and warning-ownership semantics; no second checker standard.
- WD-23rs: docs/maestro-parity-evidence-contract.md -> `wangp-dspy.maestro-parity-evidence/v1`
  source: authorization, provenance, native-log, output, gate, and reviewer requirements.

## Story Acceptance Criteria
1. [State] Before any network or host action, the live tracker records verbatim operator approval for all five assets, exactly 23,701,298,279 bytes, host `3090`, and the seven named operations; absent or partial approval fails closed.
2. [State] Each declared file is downloaded exactly once to its declared destination, then passes exact size and SHA-256 verification; the download report records zero undeclared bytes and no substitution from unrelated assets.
3. [State] Host preflight verifies SSH, disk headroom, GPU state, Wan2GP/tree identity, existing accepted LTX assets, and configured QC before any queue admission.
4. [State] Each of the seven named operations runs once through the governed queue/adapter path with exact argv, durable state, native logs, exit state, and either a real nonempty output or a typed terminal boundary; no operation inherits another cell's evidence.
5. [State] Every successful output is hash-bound, ffprobe-probed, visually represented, objectively gated, checker-validated, and independently reviewed; genuine runtime failures become exact operator-reviewed terminal boundaries rather than being relabelled as hardware infeasibility.
6. [State] Exactly the seven named `dependency_blocked` cells change in `docs/video-capabilities.md`; all other cells and rows remain byte-for-byte semantically unchanged.
7. [State] Focused manifest/checker tests, the undeselected full suite, `pvg lint --backlog`, `wgp release verify` with `release=ready` and `tag_created=false`, protected-file parity, `git diff --check`, and exact-head CI pass.

## Testing Requirements
- Integration tests are mandatory with no mocked network, host, model, queue, generation, media, or checker behavior.
- Add real fail-closed tests for absent authorization, partial asset approval, wrong hash/size, undeclared download bytes, and manifest drift.
- Run the canonical checker on every produced success or terminal-boundary bundle.
- Run focused tests, the undeselected full suite with parsed JUnit, lint, release verification, protected parity, diff check, and exact-head CI.

## Delivery Requirements
- Record verbatim authorization, exact command and argv, commit/tree identity, asset hashes and bytes, host/storage state, queue state, native logs, output hashes/metadata/gates, bundle sizes, PR, CI, and AC table.
- Include `LEARNINGS:`.
- If download, preflight, generation, or checking fails, stop and record the typed boundary; never substitute an existing output.

## MANDATORY SKILLS
- pvg
- tool-systematic-debugging

## nd_contract
status: new

### evidence
- Current matrix audit at main `2c20caa1`: exactly seven `dependency_blocked` cells remain in the two LTX rows.
- WD-m7xw and WD-osfm record the exact absent assets and fail-closed offline behavior.
- HEAD-only metadata measured five unique assets totaling 23,701,298,279 bytes with the SHA-256 values above; zero model bytes were downloaded.

### proof
- [ ] Pending explicit operator authorization, exact download verification, governed seven-operation run, terminal matrix transition, checker proof, and standing gates.

## Acceptance Criteria


## Design


## Notes
Observable outcome: after authorization and execution, the operator can run the canonical checker on each of the seven affected cell bundles and it returns an explicit pass/fail result with exact provenance or boundary evidence.
## JEV Gate #7 Final Native Terminal Boundary (NOT DELIVERED)

### Gate #7
- Live Jev Gate #7: mode=live, model=jev-latest, decision=CONTINUE, confidence 0.80, constraint risk 0.37, missing-evidence score 1.16, no veto.
- Declared snapshot SHA-256: ed82d6d2fbb2cf7f9745a55625ec8850d2cb1ff9c70514634ce9698b85f9091c.
- Declared trace SHA-256: 21709889328392ed0e33a76ccadd16eeb284fd45278ea36b94a6161b4a9bf7b7.
- No-secret Gate #7 artifacts persisted under jev-gates/2026-10-03/ with raw API-key scan PASS, 0 matches.
- Pre-host authorization/runner head: e2f07a3c76486f53bf4e78ebecb57655de2e969f; exact-head CI run 37146983354 / job 111272864985 passed in 16m03s.
- Local Gate #7 runner/reviewer layer:
  - scripts/run_ltx_final_operations.py uses the real services.jobs.JobQueue, exact staged settings hashes, exact argv, native logs, GPU/source/disk snapshots, one-attempt semantics, and stop-on-first-terminal-failure.
  - scripts/review_ltx_operations.py provides independent local-Qwen review evidence.
  - phase-b-preparation/final-operation-plan.json binds seven operations, /usr/bin/python3, execution-tree source roots, assets, references, queue IDs, and native argv.

### Fresh Host Prefflight and Judge Readiness
- Evidence: final-native-operations/preflight/host-state.json.
- Host/user: straughter-Z690-Steel-Legend / straughter.
- Root free bytes: 23564808192.
- GPU: RTX 3090, 139 MiB used, 23978 MiB free, no compute apps.
- WD-m7xw tree: faea82d15bf10b3479c42c0ea430892aae975870, status ?? ckpts.
- WD-osfm tree: 4c93b64a47b5b0a915f2abec2ce754be98227150, status ?? ckpts.
- Models: 5/5 exact size and SHA-256.
- References: 7/7 exact SHA-256.
- Judge initially unreachable and absent.
- Judge readiness: judge_ctl start exited 0 ("judge up after 20s"); health HTTP 200 with exact body {"status":"ok"} on first poll; healthy PID 1780109 used 7752 MiB; stop exited 0 ("judge stopped: 0 remaining"); post-stop health unreachable and GPU idle.
- Exact deployment hashes and dry run are recorded in final-native-operations/deploy-hashes.txt and host-dry-run.txt. Dry run: 7 operations, 0 queue admissions, 0 native attempts; /usr/bin/python3 had torch CUDA/diffusers/safetensors/pydantic and all planned run paths were absent.

### Terminal Boundary
- First and only admitted operation: LTX-2.5 / outpaint / ltx25-outpaint.
- Planned job: wd-28ac-ltx25-outpaint-attempt-1.
- Durable JobQueue ID: job-1791055869374-3f043ee9.
- Exact argv is recorded in terminal-boundary/boundary.json and ltx25-outpaint.operation-record.json.
- Staged settings SHA-256: 76183330b7898eb95ac94236083eaa3092fabbcb01696fd7a930d4113afb8e83.
- Runner typed boundary: NATIVE_NO_OUTPUT.
- Diagnostic typed boundary: NATIVE_IMPORT_MMGP_MISSING.
- Exact native error: ModuleNotFoundError: No module named 'mmgp'.
- Native exit: 1. Output count: 0.
- Native log: 227 bytes, SHA-256 cf605c152543c2b9472ad6cfc6a208530cf6128906173c018df2d64dea49bada.
- Durable queue after boundary: failed=1, pending=0, active=0. No later job was submitted.
- Not attempted: ltx25-repaint, ltx25-recast, ltx25-upscale, ltx23-outpaint, ltx23-recast, ltx23-upscale.
- Read-only runtime diagnosis found mmgp absent from /usr/bin/python3 and no mmgp candidate in the WD-m7xw/WD-osfm run/vendor paths; no historical Wan2GP venv interpreter remained.
- This is not a hardware verdict and not a model-capability verdict. No retry, substitution, dependency installation, model mutation, reference mutation, deletion, or matrix transition occurred.

### Terminal Postflight
- Evidence: final-native-operations/terminal-boundary/postflight.json.
- Models: 5/5 unchanged.
- References: 7/7 unchanged.
- Execution trees: both unchanged at exact commit/status.
- GPU: 139 MiB used, 23978 MiB free, zero compute apps.
- Native/runner processes: zero.
- Judge: unreachable, zero processes.
- Generated native outputs: zero.
- docs/video-capabilities.md remains byte-identical to origin/main.

### Local Evidence Gates and CI
- Focused terminal-boundary tests: /Users/Shared/HermesWorkspace/wangp-dspy/.venv/bin/python -m pytest tests/test_ltx_final_terminal_boundary.py tests/test_ltx_final_operations_runner.py tests/test_ltx_jev_gate7.py -q => 8 passed.
- pvg verify terminal boundary/native log/tests --include-tests => VERIFY: PASSED.
- pvg lint --backlog => scanned 156 issues; 0 errors, 0 review findings.
- Protected-file parity => PASS.
- Matrix-document parity => PASS.
- git diff --check => PASS.
- wgp release verify => version=0.1.0, release=ready, tag=v0.1.0, tag_created=false.
- Boundary evidence head: b304b6e736bb3734038573fec8c4e42641f51249.
- Exact-head CI: run 37148447846 / job 111277101180 => success in 21m19s, https://github.com/jmanhype/wangp-dspy/actions/runs/37148447846.
- PR 217 remains OPEN and MERGEABLE.

### Boundary Decision
- WD-28ac is NOT delivered.
- No canonical success checker was applicable because there is no successful output bundle.
- A distinct operator/Jev decision must supply or authorize a compatible Wan2GP Python runtime containing mmgp before any retry. The failed settings/log/queue evidence must remain unchanged.

## nd_contract
status: in_progress

### evidence
- Gate #7 final native attempt stopped at a CI-green, typed runtime boundary at b304b6e736bb3734038573fec8c4e42641f51249.

### proof
- [x] Gate #7 evidence, final plan, real queue runner, reviewer seam, fresh preflight, judge readiness, exact first-attempt evidence, and terminal postflight are committed.
- [x] The first operation stopped the queue with one durable failed job, no pending work, no retry, no substitution, and no artifact mutation.
- [ ] NOT DELIVERED: compatible Wan2GP runtime and a distinct retry decision remain required.


## JEV Gate #6 QC Readiness Complete (NOT DELIVERED)

### Gate #5 / #6 Evidence
- Gate #5: live jev-latest, GATHER_EVIDENCE, gather confidence 0.72, constraint risk 0.26, missing-evidence score 1.36, declared snapshot 91c2df7d23ec3d8a142d4419199b6326823c6e4b2047fb5789da3f6db000e9bd, declared trace d4d38261c79a38381ffa4832e637cc0f3e61bd23cf36455a657a2f07ae4330fb.
- Gate #6: live jev-latest, CONTINUE, confidence 0.98, constraint risk 0.20, missing-evidence score 1.09, declared snapshot f9509a57f4311c4a595e591551fe2f3fd4e55e25bf0862ee107fb263d9340aae, declared trace f6ffafda422883b9f5cb5149bb3e9384c167b034ec5d4cae9e994659c6e10726.
- No-secret artifacts persisted under jev-gates/2026-10-03/, including gate-5-6-evidence.json, both snapshots/decisions/traces, and wd28ac-fresh-readonly-probe-5.txt.
- Raw API-key pattern scan passed with 0 matches. No API key was read, received, logged, or passed to the worker.
- Authorization head before host action: a2d33a3e3aa71325daac1675e50e28d721cc65a9. Exact-head CI run 37142944825 / job 111260961046 passed in 23m31s.

### QC Readiness Execution
- Evidence: qc-readiness/report.json; remote exit 0.
- Pre-start:
  - Host/user: straughter-Z690-Steel-Legend / straughter.
  - Health http://127.0.0.1:8000/health: unreachable (connection refused).
  - GPU: RTX 3090, 144 MiB used, 23972 MiB free, no compute apps.
  - Judge processes: zero.
  - Root free bytes: 23369863168.
- Start command: /home/straughter/marathon/bin/judge_ctl.sh start => exit 0, stdout "judge up after 20s".
- Health:
  - HTTP 200.
  - Exact body: {"status":"ok"}.
  - Reached on poll attempt 1.
- Healthy state:
  - GPU: RTX 3090, 7901 MiB used, 16215 MiB free, utilization 0.
  - Compute process: pid 1495102, /home/straughter/llama.cpp/build/bin/llama-server, 7752 MiB.
  - Judge pgrep matched the governed llama-server command on port 8000.
  - Root free bytes: 23368744960.
- Stop:
  - /home/straughter/marathon/bin/judge_ctl.sh stop => exit 0.
  - stdout "judge stopped: 0 remaining".
  - Stop verified: true.
  - Health post-stop: unreachable (connection refused).
  - Judge processes: zero.
  - GPU apps: zero.
  - GPU post-stop: RTX 3090, 144 MiB used, 23972 MiB free.
- Protected state:
  - All five model finals hashed before and after: unchanged.
  - All six accepted references hashed before and after: unchanged.
- Hard boundary remained zero for native operations, queue admissions, renders, retrievals, network/model GETs, model/reference mutations, unrelated process actions, protected-file edits, and matrix transitions.

### Local Verification and CI
- Focused QC/Gate/auth tests: /Users/Shared/HermesWorkspace/wangp-dspy/.venv/bin/python -m pytest tests/test_ltx_qc_readiness.py tests/test_ltx_jev_gate6.py tests/test_ltx_dependency_manifest.py -q => 20 passed.
- pvg verify qc readiness report/tests/authorization --include-tests => VERIFY: PASSED.
- pvg lint --backlog => scanned 156 issues; 0 errors, 0 review findings.
- Protected-file parity versus origin/main => PASS.
- docs/video-capabilities.md parity versus origin/main => PASS.
- git diff --check => PASS.
- wgp release verify => version=0.1.0, release=ready, tag=v0.1.0, tag_created=false.
- Evidence commit: 985e49a69f0bb70f41a8d2a4ebdc500366978b9a.
- Exact-head CI: run 37144596220 / job 111265823742 => success in 22m43s, https://github.com/jmanhype/wangp-dspy/actions/runs/37144596220.
- PR 217 remains OPEN and MERGEABLE.

### Boundary
- WD-28ac is NOT delivered. QC readiness proves reversible local judge startup/health/shutdown only; the seven native operations still require a separate Jev operations gate.

## nd_contract
status: in_progress

### evidence
- QC readiness is committed and exact-head CI verified at 985e49a69f0bb70f41a8d2a4ebdc500366978b9a.

### proof
- [x] Gate #5/#6 no-secret evidence and QC-only authorization are persisted and bound.
- [x] Existing judge_ctl starts to governed port 8000 health, produces exact healthy GPU/process/disk evidence, and stops cleanly with zero remaining processes.
- [x] All five models and six references remained unchanged.
- [ ] NOT DELIVERED: seven native operations and matrix terminalization remain gated.


## JEV Gate #4 Local Phase B Preparation (NOT DELIVERED)

### Gate #3 / #4 Evidence
- Gate #3: live jev-latest, GATHER_EVIDENCE, selected gather confidence 0.46, choice confidence 0.33, constraint risk 0.48, missing-evidence score 1.85, declared snapshot d1d7b81948f1d7f8e5fa93e8a48782f7d76e04b2b633121d4d17a5dbd46658fa, declared trace bc71e063fbbcb6751d1424daa06009f6e519b5f50edbdff00e2bb341c087c00e.
- Gate #4: live jev-latest, CONTINUE, confidence 0.78, constraint risk 0.26, missing-evidence score 2.18, declared snapshot 38e9b171448464138e18ba6b4987d43c48a1f65df9f3bfc3da628418b2c58500, declared trace 1636e28fb5dbc9945c9fbe98df51500b560c5e9b06792d9798bad4823d283b9d.
- No-secret artifacts persisted in jev-gates/2026-10-03/: gate-3-4-evidence.json, wd28ac-jev-snapshot-3.json, wd28ac-jev-decision-3.json, wd28ac-jev-trace-3.jsonl, wd28ac-jev-snapshot-4.json, wd28ac-jev-decision-4.json, and wd28ac-jev-trace-4.jsonl.
- Raw API-key pattern scan: PASS, 0 matches. No API key was read, received, or passed to the worker.

### Local Operation-Preparation Layer
- Authorization now binds Gate #4 to local_phase_b_preparation_only with host_execution_authorized=false.
- Added scripts/prepare_ltx_operations.py and datasets/runs/maestro-parity/ltx-dependency-terminalization/phase-b-preparation/operation-plan.json.
- Exact operation mapping covers only:
  - LTX-2.5 outpaint/repaint/recast/upscale
  - LTX-2.3 outpaint/recast/upscale
- Every operation maps exact row, missing asset, accepted reference(s), hash-bound native settings template, staged settings path, native argv, log path, durable queue/job/retry identifiers, and planned_not_admitted state.
- Native patterns derive from accepted WD-m7xw/WD-osfm evidence; LTX-2.3 upscale uses the accepted no-profile upscale argv shape and other operations use profile 3 + SDPA.
- Typed local preflight checks Gate #4 authorization, healthy QC, disk, idle GPU, both accepted execution trees, all five verified model files, and all six accepted references. The committed plan is intentionally preflight_ready=false solely because QC health was not contacted/proven in local-only preparation.
- Evidence expectations require exact output hash, ffprobe JSON, contact-sheet and first-frame visuals, objective gates, canonical checker PASS, and independent reviewer approval.
- Attempt policy is max_attempts=1, retry=never, no evidence inheritance, terminal failure typed as native boundary, and stop_queue_on_first_terminal_failure.
- Exact seven-row matrix transition validator accepts only dependency_blocked -> host_run_verified or operator_approved_terminal_boundary for the seven owned cells; no unowned row/cell may change.
- docs/video-capabilities.md remains byte-identical to origin/main; no capability claim or matrix transition was made.

### Verification
- Branch/head: story/WD-28ac at d0a05c447f0e170946a470ffb5638594e94299da.
- Focused real-process/local tests: /Users/Shared/HermesWorkspace/wangp-dspy/.venv/bin/python -m pytest tests/test_ltx_phase_b_preparation.py tests/test_ltx_dependency_manifest.py tests/test_ltx_jev_gate2.py tests/test_ltx_jev_phase_a.py tests/test_ltx_download_runner.py -q => 36 passed.
- Undeselected full suite at clean head: /Users/Shared/HermesWorkspace/wangp-dspy/.venv/bin/python -m pytest -q -ra --junitxml=/private/tmp/WD-28ac-phase-b-full-20261003.junit.xml => JUnit tests=2221 failures=0 errors=0 skipped=1 time=1849.075s. Sole skip is the pre-existing WANGP_3090 live-host gate; the variable was not set.
- pvg verify explicit changed evidence/test paths --include-tests => VERIFY: PASSED (3 files scanned, 0 issues).
- pvg lint --backlog => scanned 156 issues; 0 errors, 0 review findings.
- wgp release verify => version=0.1.0, all checks pass, release=ready, tag=v0.1.0, tag_created=false.
- Protected-file parity versus origin/main => PASS.
- docs/video-capabilities.md parity versus origin/main => PASS.
- Credential scan across 68 WD-28ac JSON/JSONL/text/Markdown evidence files => PASS, 0 matches.
- git diff --check => PASS.
- Exact-head CI: run 37140480001 / job 111253711605 at d0a05c447f0e170946a470ffb5638594e94299da => success in 23m35s, https://github.com/jmanhype/wangp-dspy/actions/runs/37140480001.
- PR 217 remains OPEN and MERGEABLE.

### Boundary
- No SSH/host-3090 contact, QC start/contact, network/model GET, queue admission, render, retrieval, model/file mutation, protected-file edit, capability claim, delivery, acceptance, or merge occurred.
- Host execution remains blocked pending a separate live Jev host-execution gate.

## nd_contract
status: in_progress

### evidence
- Local Phase B preparation is committed and CI-green at d0a05c447f0e170946a470ffb5638594e94299da.

### proof
- [x] Gate #3/#4 no-secret evidence is persisted and authorization-bound.
- [x] Seven-operation planner/preflight/evidence/matrix layer exists with focused real-process coverage and negative paths.
- [x] Full suite, pvg verify, lint, release readiness, protected parity, matrix-doc parity, credential scan, diff check, and exact-head CI pass.
- [ ] NOT DELIVERED: host QC/operations require a separate Jev execution gate.


## JEV Gate #2 Phase A Downloads Complete (NOT DELIVERED)

### Gate Evidence and Authorization
- Live Jev Gate #2: mode=live, model=jev-latest, decision=CONTINUE, confidence=0.96, constraint risk=0.21, missing-evidence score=1.25, no veto.
- Declared snapshot SHA-256: 1e7d3349996543e8cf1ae9d3f66711be26ab73fa1d8b49d866fafb2ec13cbdf2.
- Declared canonical trace SHA-256: 2f15b2d5bc2746d9354810b3ad5302635cad66ba97ae4c1af472b4336dc835dd.
- No-secret artifacts persisted under jev-gates/2026-10-03/:
  - gate-evidence.json
  - wd28ac-jev-snapshot-2.json
  - wd28ac-jev-decision-2.json
  - wd28ac-jev-trace-2.jsonl
  - wd28ac-fresh-readonly-probe.txt
- Raw API-key pattern scan passed with 0 matches. No key was read, received, logged, or passed to this worker.
- Authorization commit and exact-head CI before host action: e279ece57acfac372310fe2ea451d71921e32fe3, CI run 37135687840 / job 111239640985, success in 23m25s.

### Fresh Read-Only Preflight
- Evidence: host-preflight-phase-a/host-state.json.
- Host/user: straughter-Z690-Steel-Legend / straughter.
- Root free bytes: 44644319232.
- GPU: RTX 3090, 139 MiB used, 23978 MiB free, no compute apps.
- WD-m7xw tree: faea82d15bf10b3479c42c0ea430892aae975870, status ?? ckpts.
- WD-osfm tree: 4c93b64a47b5b0a915f2abec2ce754be98227150, status ?? ckpts.
- Existing ingredients and outpaint finals matched exact size and SHA-256.
- All three remaining final and partial paths were absent.
- QC was not contacted.

### Downloads
- CI-green repaired runner was deployed to a new dated phase-A directory; prior artifacts were not overwritten.
- Three dry-run plans passed with zero network requests.
- Each asset used exactly one declared curl invocation; url_effective and num_redirects came from that same invocation.
- Exact results:
  - ltx-2.3-22b-ic-lora-in-outpainting-0.9.safetensors: 1308778338 bytes, SHA-256 73dd0841c0d4f0eb26fb1f017781b841b2752021944ac5ecefe57917f6dae6b5, promoted.
  - ltx-2.5-22b-ic-lora-pixel-spatial-upscaler-x2-1.0.safetensors: 327322640 bytes, SHA-256 984851b769ea2bcb4c9e0a239a7676239e42c6a6001ddc69943b41ff0b283c1d, promoted.
  - ltx-2.3-22b-dev_diffusion_model_quanto_int8.safetensors: 19447662547 bytes, SHA-256 5fc8d83656cdabf93b79bfb8799ee1c84c8270c59a49caccd4f8d1a27c77f6ec, promoted.
- Aggregate accounting: curl_invocations=3, declared_request_count=3, undeclared_request_count=0, url_effective_probe_request_count=0, redirect_count=3, network_request_count=6.
- Evidence: phase-a-downloads/download-summary.json plus three sanitized per-asset reports.
- Signed effective-URL queries were removed from Git copies; each sanitized report records the remote raw report size and SHA-256.

### Read-Only Postflight
- Evidence: host-preflight-phase-a/phase-a-postflight.json.
- All five declared finals exist with exact sizes and file SHA-256 values.
- All five WD-28ac partial paths are absent.
- GPU remains idle with no compute apps; no curl process remains.
- Postflight root free bytes: 23522594816.
- No QC contact, queue admission, render, output retrieval, matrix transition, protected-file change, deletion, or unrelated mutation occurred.

### Verification and CI
- Pre-host focused auth/gate/runner tests: 33 passed.
- Post-download focused Gate 2/Phase A/runner/manifest/boundary tests: 28 passed.
- pvg verify explicit changed evidence/test paths --include-tests => PASSED.
- pvg lint --backlog => scanned 156 issues, 0 errors, 0 review findings.
- Protected-file parity versus origin/main => PASS.
- git diff --check => PASS.
- Evidence commit: 66e0f08a31a39fc142549416710c0e043967c263.
- Exact-head CI: run 37138219380 / job 111247023089 => success in 22m36s, https://github.com/jmanhype/wangp-dspy/actions/runs/37138219380.
- PR 217 remains open and mergeable.

### Boundary
- Phase A stopped exactly as required. Jev Gate #3 and a separate QC/operations decision are still required.
- WD-28ac is NOT delivered.

## nd_contract
status: in_progress

### evidence
- JEV Gate #2 Phase A downloads and exact verification are complete and CI-green at 66e0f08a31a39fc142549416710c0e043967c263.

### proof
- [x] Gate #2 no-secret evidence and exact authorization are committed.
- [x] Exactly three remaining assets were downloaded, verified, and atomically promoted with clean accounting.
- [x] All five finals and partial absences are postflight-verified.
- [ ] NOT DELIVERED: QC/operations remain blocked pending Jev Gate #3.


## Local Curl Accounting Repair (NOT DELIVERED)

### Basis
- Corrected-retry boundary remains authoritative in datasets/runs/maestro-parity/ltx-dependency-terminalization/corrected-retry-boundary.json.
- Existing verified state is preserved unchanged from that boundary snapshot:
  - ingredients final: size 1308778338, SHA-256 515e4e139001ac6282357a5b35372e42e98b3affd5fcc886a52242abeed19559, promoted with 0 network requests;
  - outpaint final: size 1308756416, SHA-256 32c5d3e0649aa4e89b192319f3c79460dfd2319d2859ca11fa6f88e983a81665, produced by exactly 1 declared curl invocation and 0 separate URL-effectiveness GETs;
  - three remaining assets were not requested.

### Repair at bb0af2e12ffd9f8d867448ce4db49316c550d66e
- scripts/run_ltx_dependency_download.py now uses the curl 8.5.0 documented `%{num_redirects}` write-out, not unsupported `%{redirect_count}`.
- Non-integer/blank accounting fields raise typed `CURL_ACCOUNTING_OUTPUT_INVALID` before `os.replace`, preserving the partial and preventing promotion.
- An already-present exact verified final fails `DESTINATION_OR_PARTIAL_COLLISION` before curl invocation, move, or deletion.
- `url_effective` continues to come from the same declared curl write-out; the runner records `url_effective_probe_request_count=0` and rejects a second invocation of the same asset.
- Local summary: datasets/runs/maestro-parity/ltx-dependency-terminalization/accounting-repair-summary.json.

### Verification
- Focused tests: /Users/Shared/HermesWorkspace/wangp-dspy/.venv/bin/python -m pytest tests/test_ltx_download_runner.py tests/test_ltx_corrected_retry_boundary.py tests/test_ltx_dependency_manifest.py tests/test_ltx_metadata_audit.py tests/test_ltx_download_boundary.py -q => 32 passed.
- pvg verify scripts/run_ltx_dependency_download.py tests/test_ltx_download_runner.py datasets/runs/maestro-parity/ltx-dependency-terminalization/accounting-repair-summary.json --include-tests => VERIFY: PASSED.
- pvg lint --backlog => scanned 156 issues; 0 errors, 0 review findings.
- Protected-file parity versus origin/main => PASS for services/jobs/queue.py, services/director/renderers/policy.py, services/director/wiring.py, services/jobs/preflight.py, and scripts/run_film.py.
- git diff --check => PASS.
- PR 217 exact-head CI: run 37130251949 / job 111223772427 at bb0af2e12ffd9f8d867448ce4db49316c550d66e => success, 22m36s, https://github.com/jmanhype/wangp-dspy/actions/runs/37130251949.

### Boundary
- Local-only repair: no host 3090 contact, model/body request, URL-effectiveness request, final/partial movement or deletion, queue admission, render, protected-file change, delivery, acceptance, or merge.
- Host execution remains blocked pending a distinct operator decision; future retry must preserve the two verified finals and request only the three remaining declared assets.

## nd_contract
status: in_progress

### evidence
- Local curl accounting repair committed and exact-head CI verified at bb0af2e12ffd9f8d867448ce4db49316c550d66e.

### proof
- [x] Runner uses curl-documented num_redirects and fails safely on absent/non-integer accounting.
- [x] Exact verified-final resume, one-declared-request accounting, and no second URL-effectiveness/network request are regression-covered.
- [ ] NOT DELIVERED: corrected host retry remains blocked on a distinct operator decision.


## Local Metadata Repair (NOT DELIVERED)

### Metadata Evidence
- Source: METADATA-ONLY AUDIT RESULT recorded 2026-10-03T08:14:32Z; collection recorded 2026-10-03T08:11:12Z.
- Repository: DeepBeepMeep/LTX-2 at 6aa898aea1d968febdd834dc29e1dbef35340aeb (lastModified 2026-09-29T19:49:05.000Z).
- Preserved evidence: datasets/runs/maestro-parity/ltx-dependency-terminalization/metadata-audit/model.json and tree.json.
- Response SHA-256: model.json 33fb1cde721375e7b391aa2189b711965364ac0dfa403a48407ab0e8d1604505; tree.json 079d472c84a9fa68e29fab9a17896a079ea209f6c6bc8d3313a7601ee5e91baa.
- Summary: metadata-audit/summary.json binds all five path/size/lfs.oid/xetHash mappings and records total 23701298279 bytes.
- Correct mappings (actual file SHA-256=lfs.oid; XET is separate):
  - ingredients: 515e4e139001ac6282357a5b35372e42e98b3affd5fcc886a52242abeed19559 / xet 4647f4f18c87208f949b6f473d49af679ddd87532b40718480e5153852f1f1ba
  - outpaint: 32c5d3e0649aa4e89b192319f3c79460dfd2319d2859ca11fa6f88e983a81665 / xet 76df7c1ccbe8d657e38f38e8defbc0755a8d57b1a2b34fcad1f6376f4ce289f0
  - in/outpainting: 73dd0841c0d4f0eb26fb1f017781b841b2752021944ac5ecefe57917f6dae6b5 / xet 748bca2d539cf2776abe801da96f06d6f31eec64f2354dea0f4b336292d3b837
  - pixel upscaler: 984851b769ea2bcb4c9e0a239a7676239e42c6a6001ddc69943b41ff0b283c1d / xet 229e549af18993e1670ad5dac7d2d8d03bb558ae446ac4ee23f8ba1263783996
  - dev int8: 5fc8d83656cdabf93b79bfb8799ee1c84c8270c59a49caccd4f8d1a27c77f6ec / xet f27d0effb85903172d976f1929dc0b3a204944ff014574eaab51cdc5e54f0f22

### Repair
- model-assets.json now uses lfs.oid for sha256, a separate xet_hash field, source revision 6aa898aea1d968febdd834dc29e1dbef35340aeb, and corrected canonical digest 05c9e6ba1d69d4a75c20d83bcb41e381e64de2a310b8dcba05a84f66b62136d2.
- operator-authorization.json and the not-authorized template rebind that digest. The authorized record preserves the original approval, records the metadata correction, and explicitly sets retry_authorized=false.
- download-boundary.json now records that the ingredients partial matched the true file SHA-256 while the old expected value was XET; the 172109-byte undeclared URL-effectiveness GET remains a fail-closed boundary.
- scripts/run_ltx_dependency_download.py records url_effective from the same declared curl --write-out, never issues a second URL-effective GET, exhausts a one-declared-curl budget, and reports declared/undeclared/redirect/network request counts. Current authorization fails closed before network with RETRY_NOT_AUTHORIZED.
- predict/model_assets.py now models xet_hash separately from sha256 and binds optional source_revision.

### Exact-Head Verification
- Branch/commit: story/WD-28ac at 2e8229b804d38c8f083e3f399f8c4fade4a700af.
- Focused tests: /Users/Shared/HermesWorkspace/wangp-dspy/.venv/bin/python -m pytest tests/test_ltx_dependency_manifest.py tests/test_ltx_metadata_audit.py tests/test_ltx_download_boundary.py tests/test_ltx_download_runner.py -q => 26 passed.
- Undeselected full suite at the clean commit: /Users/Shared/HermesWorkspace/wangp-dspy/.venv/bin/python -m pytest -q -ra --junitxml=/private/tmp/WD-28ac-metadata-full-clean-20261003.junit.xml => JUnit tests=2201 failures=0 errors=0 skipped=1 time=879.658s. The sole skip is the pre-existing WANGP_3090 live-host gate; the variable was not set.
- A preliminary full-suite attempt while the repair was uncommitted had 3 failures: two clean-tree release checks and one transient PyPI uvicorn timeout. The install test passed on direct rerun and the entire suite passed after committing the exact clean head.
- pvg verify explicit changed files --include-tests => VERIFY: PASSED (6 files scanned, 0 issues).
- pvg lint --backlog => scanned 156 issues; 0 errors, 0 review findings.
- wgp release verify => version 0.1.0, all checks pass, release=ready, tag=v0.1.0, tag_created=false.
- Protected parity: git diff --exit-code origin/main -- services/jobs/queue.py services/director/renderers/policy.py services/director/wiring.py services/jobs/preflight.py scripts/run_film.py => PASS.
- git diff --check => PASS.
- PR 217 exact-head CI: run 37110988516 / job 111168697611 at commit 2e8229b804d38c8f083e3f399f8c4fade4a700af => success, 23m29s, https://github.com/jmanhype/wangp-dspy/actions/runs/37110988516.

### Boundary
- No host 3090 contact, model-body GET, preserved-partial promotion/move/delete, queue admission, render, protected-file change, delivery, acceptance, or merge occurred.
- Host execution remains blocked on a distinct operator retry decision covering the 172109 undeclared payload bytes and preserved-partial disposition.

## nd_contract
status: in_progress

### evidence
- Local-only metadata repair committed and CI-verified at 2e8229b804d38c8f083e3f399f8c4fade4a700af.

### proof
- [x] All five LFS-OID/XET mappings are evidenced, separately modeled, authorization-bound, and regression-tested.
- [x] Downloader control eliminates the second URL-effectiveness GET and records exact request counts in tested reports.
- [ ] NOT DELIVERED: distinct operator retry/disposition decision remains required; no host execution is authorized.


## Authorized Execution Start

- Worktree: /Users/Shared/HermesWorkspace/wangp-dspy/.claude/worktrees/dev-WD-28ac
- HEAD: cd57dfc53d41fa73b94f7426c9c76e58360b20dc
- Authorization source: live tracker comment recorded at 2026-09-29T23:17:30Z, verbatim operator input "Authorize".
- Authorized scope: exactly five manifest assets totaling 23701298279 bytes, host 3090, governed Wan2GP path, and only LTX-2.5 outpaint/repaint/recast/upscale plus LTX-2.3 outpaint/recast/upscale.
- No unrelated model, training, provider spend, protected-engine semantic change, threshold change, merge, or acceptance is authorized.

## nd_contract
status: in_progress

### evidence
- Local artifacts committed at cd57dfc53d41fa73b94f7426c9c76e58360b20dc on story/WD-28ac:
  - datasets/runs/maestro-parity/ltx-dependency-terminalization/model-assets.json
  - datasets/runs/maestro-parity/ltx-dependency-terminalization/operator-authorization.template.json
  - tests/test_ltx_dependency_manifest.py
- Manifest contains exactly the five story assets, canonical schema, source/destination/size/SHA-256/license data, and total 23701298279 bytes. Its canonical-JSON SHA-256 linkage in the authorization template is 7f159b99bdd3a688763c5c3d4188f5672ecff9af8003d2c5f76ab783fa31ceb1.
- Authorization template remains status=not_authorized with operator_approval=null; no approval is claimed.
- Focused test: /Users/Shared/HermesWorkspace/wangp-dspy/.venv/bin/python -m pytest tests/test_ltx_dependency_manifest.py -q => 11 passed.
- Undeselected full suite with parsed JUnit: /Users/Shared/HermesWorkspace/wangp-dspy/.venv/bin/python -m pytest -q -ra --junitxml=/tmp/wd28ac_full.junit.xml => tests=2138 failures=0 errors=0 skipped=1 time=844.556s. The sole skip is the pre-existing live-host gate tests/test_jobs_integration_3090.py:20 requiring WANGP_3090=1; no host was contacted.
- pvg verify changed files --include-tests => VERIFY: PASSED (1 files scanned, 0 issues).
- pvg lint --backlog => scanned 152 issues; 0 errors, 0 review findings.
- wgp release verify => version/checks pass, release=ready, tag_created=false.
- Protected parity: git diff --exit-code origin/main -- services/jobs/queue.py services/director/renderers/policy.py services/director/wiring.py services/jobs/preflight.py scripts/run_film.py => exit 0. git diff --check => pass.
- PR: https://github.com/jmanhype/wangp-dspy/pull/217
- Exact-head CI at cd57dfc53d41fa73b94f7426c9c76e58360b20dc: https://github.com/jmanhype/wangp-dspy/actions/runs/36538874449 => success, CI/test 24m37s.
- Boundary honored: no SSH/3090 contact, model-byte download or HEAD request, Hugging Face curl, storage mutation, queue admission/render/retrieval, docs/video-capabilities.md change, or protected-engine edit.

### proof
- [x] Local manifest preparation and fail-closed JSON coverage exist at cd57dfc5 with passing focused, full-suite, lint, release, protected-parity, diff, and exact-head CI evidence.
- [ ] NOT DELIVERED: operator authorization for all five assets, exactly 23701298279 bytes, host 3090, and the seven operations remains absent; downloads, host work, matrix terminalization, acceptance, and merge remain blocked.

## nd_contract
status: in_progress

### evidence
- Local manifest-prep boundary active at worktree HEAD 2c20caa1 on story/WD-28ac.
- No host/3090 contact, model-byte download, HEAD request, Hugging Face curl, storage mutation, queue/render action, or capability-matrix edit will occur.
- Preparing only the exact five-asset model manifest, fail-closed JSON tests, and a not_authorized local authorization template.

### proof
- [ ] Pending local manifest/test artifact and exact-head CI; this remains not delivered while operator authorization is absent.

## History
- 2026-09-29T07:05:34Z dep_added: blocks WD-fay0
- 2026-09-29T07:05:34Z status: open -> deferred
- 2026-09-29T07:07:31Z status: deferred -> open
- 2026-09-29T07:07:37Z status: open -> in_progress
- 2026-09-29T07:07:37Z auto-follows: linked to predecessor WD-23rs
- 2026-09-29T07:07:37Z claimed by dev-WD-28ac
- 2026-09-29T08:16:37Z status: in_progress -> open
- 2026-09-29T08:16:37Z released by speed
- 2026-09-29T08:16:39Z status: open -> deferred
- 2026-09-29T23:17:51Z status: deferred -> open
- 2026-09-29T23:18:01Z status: open -> in_progress
- 2026-09-29T23:18:02Z auto-follows: linked to predecessor WD-p587
- 2026-09-29T23:18:02Z claimed by dev-WD-28ac
- 2026-09-30T14:49:05Z status: in_progress -> open
- 2026-09-30T14:49:05Z released by speed
- 2026-09-30T14:51:37Z status: open -> deferred
- 2026-09-30T17:56:46Z dep_added: blocked_by WD-1s5s
- 2026-09-30T19:29:46Z dep_removed: was_blocked_by WD-1s5s
- 2026-09-30T20:00:02Z dep_added: blocked_by WD-cuzw
- 2026-10-01T23:49:42Z dep_removed: was_blocked_by WD-cuzw
- 2026-10-03T06:57:56Z status: deferred -> open
- 2026-10-03T06:57:56Z status: open -> in_progress
- 2026-10-03T06:57:56Z auto-follows: linked to predecessor WD-1s5s
- 2026-10-03T06:57:56Z auto-follows: linked to predecessor WD-cuzw
- 2026-10-03T06:57:56Z claimed by dev-WD-28ac
- 2026-10-03T07:44:32Z status: in_progress -> open
- 2026-10-03T07:44:32Z released by speed
- 2026-10-03T08:11:11Z status: open -> in_progress
- 2026-10-03T08:11:11Z auto-follows: linked to predecessor WD-he8i
- 2026-10-03T08:11:11Z claimed by dev-WD-28ac

## Links
- Parent: [[WD-3nod]]
- Blocks: [[WD-fay0]]
- Was blocked by: [[WD-1s5s]], [[WD-cuzw]]
- Follows: [[WD-23rs]], [[WD-p587]], [[WD-1s5s]], [[WD-cuzw]], [[WD-he8i]]

## Comments

### 2026-09-29T08:16:39Z speed
Parked as operator-gated after local preparation. PR 217 head cd57dfc53d41fa73b94f7426c9c76e58360b20dc has exact-head CI success and the five-asset fail-closed manifest/tests, but no operator approval exists. No network/host/model action is authorized by this status change.

### 2026-09-29T23:17:30Z speed
OPERATOR AUTHORIZATION at 2026-09-29T23:17:30Z. Verbatim user input: Authorize. Interpreted scope from the immediately prior authorization request: WD-28ac five-asset LTX dependency batch, exactly 23,701,298,279 bytes, on host 3090, only the seven named LTX operations, with exact manifest hashes and no unrelated mutation.

### 2026-09-29T23:22:07Z speed
Dispatch note: operator authorization is recorded, but host-3090 execution is queued behind the WD-bw0h one-attempt clean-machine H3 run to prevent overlapping host/GPU mutations. Do not interpret the wait as lost approval.

### 2026-09-30T14:49:05Z speed
BLOCKED: Authorized host-3090 preflight passed SSH, tree identity, 34 existing accepted LTX assets, GPU idle, and host QC probes, but the destination filesystem has 17865703424 bytes free versus 23701298279 required (shortfall 5835594855). The largest declared asset is 19447662547 bytes, 1581959123 bytes larger than all free space. All five target assets remain absent. Moving/removing an unrelated asset or redirecting the declared destination was not authorized, so zero model bytes were downloaded and zero operations were admitted. Evidence and local gates are committed at fced67e1293dc2dbbdf3f29c8b615f6357012ab6; exact-head CI run 36728749388 passed. Distinct reversible-storage authorization is required before retry.

### 2026-09-30T14:50:25Z speed
CORRECTION to the prior BLOCKED comment: the live integration test exercised the configured qc_available check kind, but it does not assert a healthy QC result and the status was not captured. The durable preflight evidence proves host Python, ffmpeg, and ffprobe executable probes; it does not claim QC health. The storage boundary and zero-download/zero-admission decision are unchanged.

### 2026-09-30T14:51:37Z speed
Parked on measured destination-storage boundary after authorized preflight. Root filesystem has 17,865,703,424 bytes free versus 23,701,298,279 declared bytes; largest asset exceeds free space alone. /mnt/bulk-hdd has headroom, but moving unrelated assets or redirecting declared destinations requires a distinct operator-approved reversible storage plan. No model bytes downloaded, queue admitted, operation attempted, matrix cell changed, or unrelated host mutation occurred. PR 217 head fced67e1293dc2dbbdf3f29b8b615f6357012ab6a has exact-head CI success.

### 2026-09-30T15:30:18Z speed
Proposed shared storage remediation requiring operator authorization: after the two superseded H3 checkpoints are hash-verified and reversibly moved to /mnt/bulk-hdd/straughter/model-offload/wangp-3090, root free space should rise by about 44.28GB, enough for the exact 23.70GB LTX manifest plus output/workspace margin. Re-run host preflight before any download; if either H3 checkpoint is absent, hashes differ, target creation fails, or post-move root free space remains insufficient, stop typed. No LTX retry is authorized by this proposal.

### 2026-09-30T19:53:26Z speed
WD-1s5s storage-remediation packet is accepted and merged at main 498a9cb4c994033064161cace2a98165c0a1dbb2. Its stale-space projection does not authorize the exact five-asset/23701298279-byte LTX batch; that download/host batch still requires explicit operator approval.

### 2026-10-02T00:22:32Z speed
WD-cuzw storage offload is accepted/merged at main b5b7e35b131de72e541bec508fcac19fced895f3. Recorded remote free is 48494047232 bytes, which exceeds the exact 23701298279-byte five-asset LTX manifest by 24792764953 bytes before download. This storage fact does not authorize downloads or host execution; WD-28ac remains deferred pending explicit model-download and GPU-host approval.

### 2026-10-02T00:27:01Z speed
Read-only execution-readiness audit at merged main b5b7e35b131de72e541bec508fcac19fced895f3: existing story/WD-28ac head and origin head remain fced67e1293dc2dbbdf3f29c8b615f6357012ab6; PR 217 remains OPEN with exact-head CI success at that older head. A local three-way merge-tree simulation against current main reported exit 0 and no conflict markers. The branch contains the exact five-asset model manifest, not-authorized operator template, and prior preflight boundary. GitHub currently reports PR mergeability UNKNOWN, so after operator approval the worker must merge/rebase current main and rerun exact-head CI before execution. No host contact, download, model access, queue action, or authorization change occurred.

### 2026-10-03T06:57:55Z speed
OPERATOR AUTHORIZATION at 2026-10-03T06:57:55Z. Verbatim user input: Authorized. Scope is the immediately preceding blocked-goal request: WD-28ac on host 3090, exactly five LTX assets totaling 23701298279 download bytes, only the seven named operations, governed queue/adapter execution, no training/provider spend/unrelated mutation/threshold change/protected-engine change, and reversible storage handling with deletion prohibition. Record this verbatim authorization in the story branch before any network or host action.

### 2026-10-03T07:44:02Z speed
BLOCKED: Authorized download failed closed at the first declared asset. Observed size 1308778338 matches, but SHA-256 515e4e139001ac6282357a5b35372e42e98b3affd5fcc886a52242abeed19559 does not match 4647f4f18c87208f949b6f473d49af679ddd87532b40718480e5153852f1f1ba. A downloader defect also issued an undeclared URL-effectiveness GET that timed out after 172109 payload bytes. The partial is preserved at /home/straughter/Wan2GP/ckpts/ltx-2.3-22b-ic-lora-ingredients-0.9.safetensors.WD-28ac.partial; no promotion, retry, deletion, queue admission, operation, output, or matrix change occurred. Distinct operator decisions are required for the source/hash discrepancy, undeclared bytes, and preserved partial before retry.

### 2026-10-03T07:44:31Z speed
BOUNDARY ARTIFACTS committed and pushed at 1672679ef6985ce16c5b87e409e5911b83e29c08 on story/WD-28ac. Focused tests: /Users/Shared/HermesWorkspace/wangp-dspy/.venv/bin/python -m pytest tests/test_ltx_dependency_manifest.py tests/test_ltx_download_boundary.py -q => 16 passed. Boundary evidence paths: 15 present, 0 missing. pvg verify changed boundary files --include-tests => PASSED. git diff --check => PASS. Protected-file parity versus origin/main => PASS. No retry, deletion, promotion, queue admission, operation, output, or matrix transition.

### 2026-10-03T08:05:29Z speed
Exact-head CI for boundary commit 1672679ef6985ce16c5b87e409e5911b83e29c08 passed: run 37107341722, job 111158348210, duration 20m14s, https://github.com/jmanhype/wangp-dspy/actions/runs/37107341722. PR 217 remains open and mergeable. Story is released/open pending distinct operator decisions on the source/hash discrepancy, 172109 undeclared bytes, and preserved partial; no retry is authorized.

### 2026-10-03T08:07:38Z speed
Read-only post-boundary audit: repository-wide local evidence search found no prior occurrence of observed SHA-256 515e4e139001ac6282357a5b35372e42e98b3affd5fcc886a52242abeed19559; it found only the declared expected SHA-256 4647f4f18c87208f949b6f473d49af679ddd87532b40718480e5153852f1f1ba. This does not resolve upstream state and does not authorize retry. Preserve the remote partial unchanged pending a distinct operator decision on metadata audit, hash discrepancy, 172109 undeclared payload bytes, and retry/disposition.

### 2026-10-03T08:14:32Z speed
METADATA-ONLY AUDIT RESULT at 2026-10-03T08:11:12Z: Hugging Face model DeepBeepMeep/LTX-2 current commit 6aa898aea1d968febdd834dc29e1dbef35340aeb, lastModified 2026-09-29T19:49:05Z. For every WD-28ac asset, sizes match exactly and the manifest value currently labeled sha256 equals metadata xetHash, not LFS oid/actual file SHA-256. Target ingredients entry: expected 4647f4f18c87208f949b6f473d49af679ddd87532b40718480e5153852f1f1ba is xetHash; observed remote partial 515e4e139001ac6282357a5b35372e42e98b3affd5fcc886a52242abeed19559 is lfs.oid and exact-size file SHA-256. Same pattern holds for all five declared assets. Metadata API responses: model.json SHA-256 33fb1cde721375e7b391aa2189b711965364ac0dfa403a48407ab0e8d1604505 and tree.json SHA-256 079d472c84a9fa68e29fab9a17896a079ea209f6c6bc8d3313a7601ee5e91baa. No model-body GET, host contact, retry, promotion, deletion, queue action, or render occurred. Live Jev delegation cannot run yet because TYPESAFE_API_KEY is absent from this shell and no .env credential file is present; dry-run would not be represented as Jev.

### 2026-10-03T09:15:15Z speed
OPERATOR JEV-DELEGATION POLICY recorded after metadata repair. Operator asked that Jev decide future authorization/checkpoint actions to reduce latency. Live Jev is currently unavailable because TYPESAFE_API_KEY is absent; the offline gate is deterministic but uncalibrated and must not be misrepresented as Jev. When a live key is configured, Jev may authorize only an exact operator-predeclared reversible batch/scope, with recorded probabilities and fail-closed policy. Jev cannot broaden scope, approve deletion/credentials/spend/irreversible action, or authorize an undeclared model/body request. The current retry remains unauthorized pending live Jev or an explicit operator decision covering the 172109-byte undeclared boundary, preserved-partial disposition, corrected manifest, four remaining declared downloads, and seven operations.

### 2026-10-03T13:11:01Z speed
OPERATOR CORRECTED-RETRY AUTHORIZATION at 2026-10-03T13:11:01Z. Verbatim user input: Yes. This approves the immediately preceding corrected WD-28ac retry only: preserve/record the prior 172109-byte undeclared URL-effectiveness GET as a boundary; verify and promote the already-preserved exact-LFS-SHA first partial; request/download only the remaining four declared assets using one declared curl invocation per asset; verify exact sizes and file SHA-256 values; run only the seven named governed operations; and retain all prior prohibitions—no deletion, training, provider spend, unrelated mutation, threshold change, protected-engine change, undeclared model/body request, or WD-bw0h H3 retry. Authorization must be committed to the story record and exact-head CI must pass before host contact.

### 2026-10-03T15:58:22Z speed
LIVE JEV GATE #1 at 2026-10-03T15:55Z: mode=live, model=jev-latest, snapshot sha256 d3b08b65433d4d4de510846f459d82b51192c9d52086336b61c5987ca28a7e52, decision=gather_evidence, policy_reason=choice confidence 0.40 below 0.50, missing_evidence_score=1.75. A fresh read-only host probe then verified exact ingredients/outpaint finals and hashes, three remaining assets/partials absent, execution tree commits/status unchanged, GPU idle, free bytes 44718174208, and QC ports 8000/8420 unreachable. No host mutation or model request occurred.

### 2026-10-03T15:58:52Z speed
LIVE JEV GATE #2 at 2026-10-03T16:00Z: mode=live, model=jev-latest, snapshot sha256 1e7d3349996543e8cf1ae9d3f66711be26ab73fa1d8b49d866fafb2ec13cbdf2, decision=CONTINUE, continue confidence=0.96, constraint risk=0.21, missing evidence score=1.25, triggered_rules=no_veto_triggered. Exact delegated scope is PHASE A DOWNLOADS ONLY: reverify current state, issue exactly one declared curl invocation for each of the three absent assets, verify exact size/file SHA-256, and stop before QC start, queue admission, render, or matrix transition. The raw API key remains only in the local 0600 orchestrator secret file and was not passed to any worker.

### 2026-10-03T17:14:25Z speed
LIVE JEV GATE #3 at 2026-10-03T17:15Z: mode=live, model=jev-latest, snapshot sha256 d1d7b81948f1d7f8e5fa93e8a48782f7d76e04b2b633121d4d17a5dbd46658fa, decision=GATHER_EVIDENCE, selected gather confidence=0.46/choice confidence=0.33, constraint risk=0.48, missing evidence score=1.85. No QC start, queue admission, native attempt, render, or matrix transition occurred. Next evidence will inspect prior accepted QC startup and seven-operation patterns plus current local operation-preparation coverage.

### 2026-10-03T17:15:32Z speed
LIVE JEV GATE #4 at 2026-10-03T17:25Z: mode=live, model=jev-latest, snapshot sha256 38e9b171448464138e18ba6b4987d43c48a1f65df9f3bfc3da628418b2c58500, decision=CONTINUE, confidence=0.78, constraint risk=0.26, missing evidence score=2.18, triggered_rules=no_veto_triggered. Scope is LOCAL PHASE B PREPARATION ONLY: implement a fail-closed operation plan/runner and evidence tests from accepted WD-m7xw/WD-osfm patterns, then run local gates and exact-head CI. No host contact, QC contact, queue admission, render, download, retrieval, protected-file change, or capability claim. Raw API key remains only in local 0600 orchestrator storage and is not passed to the worker.

### 2026-10-03T18:01:21Z speed
LIVE JEV GATE #5 at 2026-10-03T18:20Z: mode=live, model=jev-latest, snapshot sha256 91c2df7d23ec3d8a142d4419199b6326823c6e4b2047fb5789da3f6db000e9bd, decision=GATHER_EVIDENCE, gather confidence=0.72, constraint risk=0.26, missing evidence score=1.36. No QC start, queue admission, native attempt, render, model request, or matrix transition occurred. Required evidence: current QC/disk/GPU/tree/model/reference/process state after local Phase B preparation.

### 2026-10-03T18:03:01Z speed
LIVE JEV GATE #6 at 2026-10-03T18:05Z: mode=live, model=jev-latest, snapshot sha256 f9509a57f4311c4a595e591551fe2f3fd4e55e25bf0862ee107fb263d9340aae, decision=CONTINUE, confidence=0.98, constraint risk=0.20, missing evidence score=1.09, triggered_rules=no_veto_triggered. Scope is QC READINESS ONLY: commit/persist gate evidence and CI it, then start the existing governed judge_ctl, verify port 8000 health and GPU/process state, and stop it cleanly after recording evidence. No native operation, queue admission, render, download, model mutation, protected-file change, or matrix transition.

### 2026-10-03T18:57:54Z speed
LIVE JEV GATE #7 at 2026-10-03T18:45Z: mode=live, model=jev-latest, snapshot sha256 ed82d6d2fbb2cf7f9745a55625ec8850d2cb1ff9c70514634ce9698b85f9091c, decision=CONTINUE, confidence=0.80, constraint risk=0.37, missing evidence score=1.16, triggered_rules=no_veto_triggered. Scope is FINAL NATIVE OPERATIONS: persist gate evidence and CI it, prepare/deploy exact operation scripts, fresh preflight, start the verified governed judge as needed, execute each of the seven planned operations at most once through the governed queue/adapter path, stop on first terminal failure with no retry, collect complete output/gate/checker/review evidence, stop judge, preserve models/references, and transition exactly seven owned cells. No download, model substitution, deletion, training, provider spend, unrelated mutation, protected-engine change, or WD-bw0h H3 retry.

### 2026-10-03T20:00:19Z speed
LIVE JEV GATE #8 at 2026-10-03T20:20Z: mode=live, model=jev-latest, snapshot sha256 8f82c488faabec1fc224011b331ddaa31921be27ec5fe95ab403ac0a90312d27, decision=CONTINUE, confidence=0.67, constraint risk=0.10, missing evidence score=2.70, triggered_rules=no_veto_triggered. Scope is READ-ONLY RUNTIME INVENTORY ONLY: bounded search for existing mmgp package/runtime candidates in accepted Wan2GP paths, user site-packages, pip/uv caches, likely venvs, and authorized bulk offload root. No install/download/copy/move/delete, no retry, no QC, no queue/render, no protected-file change.

### 2026-10-03T20:01:14Z speed
Jev Gate #8 read-only runtime inventory result at 2026-10-03T20:00:23Z: historical /home/straughter/Wan2GP/venv and its python/mmgp paths are absent; WD-m7xw/WD-osfm worktrees have no venv; bounded accepted roots, user site-packages, pip/uv caches, and authorized bulk offload root yielded zero mmgp directories/dist-info/wheels/archives; /usr/bin/python3 and python3.12 both fail mmgp import. Root free 23548354560 bytes and bulk free 317216575488 bytes. No install/download/copy/move/delete, retry, QC, queue/render, or protected-file change occurred. Next boundary is exact mmgp 3.7.14 metadata audit.
