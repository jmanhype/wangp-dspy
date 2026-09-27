---
id: WD-7fvx
title: "Director no-download source-pairing rework"
status: closed
priority: 1
type: task
labels: [capability, evidence, director, external-integration, delivered, accepted]
parent: WD-3nod
created_at: 2026-09-26T20:53:44Z
created_by: speed
updated_at: 2026-09-27T00:13:32Z
content_hash: "sha256:cc6aa663d6258306777b3fb2432d887ca13805f9861c02ce0bb1c9a351dc23d0"
blocked_by: [WD-dmf2, WD-cpow]
follows: [WD-5k28, WD-m7xw, WD-43tj, WD-9ymi]
assignee: dev-WD-7fvx
closed_at: 2026-09-27T00:13:32Z
close_reason: "Accepted: docs-only 982e9d6d closes DOCS_STALE while preserving the verified no-download source-pairing evidence and protected boundaries."
---

## Description
## USER INTENT
The director lane needs a no-download source-selection rework that fixes the media-specific clip-1 failures without rewriting history, weakening a gate, or consuming another download. The operator needs either a checker-valid reworked director bundle or a fail-closed stop that leaves the matrix honest.

The rework emits a checker-valid bundle or a typed blocker; it never mutates the failed baseline.

## Embedded Evidence And Diagnosis
The immutable failed baseline is the accepted WD-dmf2 bundle. Its raw QC record contains:

- Screenplay clip 1 Whisper score `0.556` against pass bar `0.6`; the utterance was approximately 5.2 seconds of speech, but the produced clip cut speech to 3.5 seconds.
- Audio clip 1 SyncNet confidence `0.594741` against pass bar `1.0`; the selected speech-bearing video was paired with instrumental audio rather than its matching speech audio.
- Screenplay clip 1 SyncNet confidence `0.468897` against pass bar `1.0`; the visual was a static zoompan and therefore was not valid speech-motion evidence.
- Screenplay clip 2 Whisper `1.000` and SyncNet `1.10503` prove the existing thresholds are reachable; threshold weakening is prohibited and unnecessary.

The primary synchronized speech pair is the existing WD-cpow pair, already copied byte-identically into WD-dmf2:

- Speech guide: `datasets/runs/maestro-parity/WD-cpow/outputs/wd_cpow_vibevoice_raw.prepared.wav`, SHA-256 `e371ebe7ee1ce9964657b4f34f61d32fbff2a5345bdb90add6c3e7dba1ee2175`, measured duration `2.333333 s`, 24 kHz mono.
- Matching speech video: `datasets/runs/maestro-parity/WD-cpow/outputs/wd_cpow_vibevoice_revoice.mp4`, SHA-256 `1cdac314c38142e15af22e1122a3df8177a5e2027b9a7fcde5807e13c8c407d3`, 704x576 at 24 fps; video and audio both measure `2.333333/2.333 s`.

The instrumental `wd_rous_ace_generate.wav` (SHA-256 `6ee782ec4f8ea86fa531669ee1c762d7a5d9685ab7e08bf6dd74d84abf3868a9`) may be used only for an explicitly non-speech instrumental target. It must never be paired with a speech video for Whisper or SyncNet evidence.

Required local model identities are unchanged from WD-dmf2 and must be rehashed before any run:

- Whisper small: `9ecf779972d90ba49c06d968637d720dd632c55bbf19d441fb42bf17a411e794`
- Qwen vision text model: `3445102e9cde5d562508642c100a2f5ac3368a5a3f748442811d7a95daee3bec`
- Qwen vision projector: `add205b7bfdb3f71f6da36b0a82aa20928dd829a920878c602628cdfbebc5288`
- SyncNet v2: `961e8696f888fce4f3f3a6c3d5b3267cf5b343100b238e79b2659bff2c605442`

## REQUIRED OPERATOR INPUTS — NOT YET PROVIDED
This story authorizes nothing. Before execution the operator must supply verbatim scope, timestamp, approver, exact host and command boundary, rights boundary, stop/failure boundary, model identities above, and explicit approval for no-download rework execution. A run is blocked if any required input is absent; missing authorization is neither infeasibility nor success.

## OUT OF SCOPE
- Editing, deleting, regenerating, or appending inside `datasets/runs/maestro-parity/WD-dmf2/`; it is immutable baseline evidence.
- Any model download, dependency change, provider account, training, publication, GUI, extra capability row/cell, rights bypass, or threshold change.
- Replacing a failed speech gate with an instrumental/non-applicable disposition, static zoompan, trimmed transcript, fixture, or prose explanation.
- Changing `services/jobs/queue.py`, `services/director/renderers/policy.py`, `services/director/wiring.py`, `services/jobs/preflight.py`, or `scripts/run_film.py`.

## DIFF BUDGET
- About 2 authored files and under 250 changed LOC: `docs/director-capabilities.md` plus manifests, scripts, logs, measurements, and evidence under `datasets/runs/maestro-parity/WD-7fvx/`.
- Keep the aggregate new bundle under 2 GiB unless an authorized failure log is larger. Do not copy model weights or mutate WD-dmf2.

## Boundary Map
PRODUCES:
- datasets/runs/maestro-parity/WD-7fvx/ -> checker-valid no-download director rework bundle
  spec: immutable baseline hash, authorization, zero-download preflight, model hashes, source-pair derivation, new request/plan/output hashes, queue attempts, raw Whisper/vision/mouth-box/SyncNet evidence, mechanically derived gates, checker result, and reviewer decision.
- docs/director-capabilities.md -> evidence-backed director-row updates
  event: update only cells supported by this bundle, cite the exact record, and leave every failed or unauthorized cell unchanged.

CONSUMES:
- WD-dmf2: datasets/runs/maestro-parity/WD-dmf2/ -> immutable failed baseline, raw QC, planned-produced map, model identities, and gate derivation
  source: copy inputs by hash into a new namespace; never mutate the predecessor bundle.
- WD-cpow: datasets/runs/maestro-parity/WD-cpow/ -> synchronized speech audio/video pair and measured stream metadata
  source: use SHA-256 `e371ebe7...` and `1cdac314...` as the primary speech pair; do not pair the speech video with instrumental audio.
- WD-651z: docs/maestro-parity-evidence-contract.md -> `wangp-dspy.maestro-parity-evidence/v1`
  source: canonical authorization, provenance, hash, disposition, gate, and reviewer fields; do not duplicate or weaken it.
- WD-651z: scripts/verify_maestro_parity.py -> `verify_bundle(bundle: Path) -> VerificationReport`
  event: invoke the accepted checker and require exit 0 before any `host_run_verified` transition.

## Story Acceptance Criteria
1. [State] Before execution, the bundle records verbatim operator authorization and proves the WD-dmf2 bundle is immutable by recording its base commit/content identity and a clean before/after parity check for `datasets/runs/maestro-parity/WD-dmf2/`; all new bytes are written only under this story's namespace.
2. [Unwanted] A no-download preflight proves zero planned and actual network/model-download bytes, rejects any absent or hash-mismatched model listed above before queue admission, and records no dependency, provider, or model-fetch mutation.
3. [State] The speech source plan preserves the complete measured utterance: the selected speech guide and speech video have matching identities/durations, and the produced speech window is at least the measured full-utterance duration; the 5.2-second-to-3.5-second cut cannot recur.
4. [State] Audio-mode evidence uses the WD-cpow synchronized speech pair as the primary source; instrumental audio is used only for a declared non-speech target and never with a speech video.
5. [State] Screenplay clip-1 evidence uses motion-bearing speech video; a static zoompan visual is rejected as incapable of supporting the speech SyncNet gate.
6. [State] Every applicable reworked clip records raw pre/post Whisper, identity-vision action/speaker scores, three-frame mouth-box consensus, and multicrop SyncNet evidence. The unchanged bars are Whisper `>=0.6`, identity action/speaker `>=0.7`, mouth center spread `<=0.03` normalized on each axis, SyncNet confidence `>=1.0`, and absolute offset `<=10` frames at 25 fps.
7. [Unwanted] Objective-gate values are mechanically derived from the raw QC evidence rather than hardcoded; any failed, inapplicable, unauthorized, missing, or reviewer-pending gate leaves the affected row/cell unchanged and the checker fail-closed.
8. [State] A successful delivery has checker exit `0`, every applicable objective gate `pass`, and an explicit approved reviewer decision; `docs/director-capabilities.md` changes only mechanically from the bundle and cites the exact new evidence record.
9. [Unwanted] No threshold, queue, preflight, renderer, wiring, or protected engine semantic changes; no WD-dmf2 mutation; no fabricated score, approval, hardware verdict, or inherited WD-cpow/WD-dmf2 output claimed as this story's output.

## Testing Requirements
- Real integration MANDATORY with no mocks: authorized no-download host execution, exact command tails, source and output hashes, queue admission/exit, raw media metadata, all QC inputs/outputs, checker transcript, and matrix-transition proof.
- Verify all copied source hashes before and after execution, including the synchronized pair and any WD-dmf2 input reused.
- Mechanically compare raw QC fields to each objective gate; do not substitute a derived summary for raw evidence.
- Run `pvg lint --backlog`; `uv run --frozen --extra dev pytest -q --junitxml=/tmp/WD-7fvx-full.xml` with parsed JUnit `errors=0` and `failures=0`; `uv run --frozen --extra dev wgp release verify` with `release=ready` and `tag_created=false`; protected-file parity against the recorded base; `git diff --check`; and the WD-651z checker.

## Delivery Requirements
- Paste authorization, base identity, zero-download/model preflight, source-pair table, commands, queue transitions, hashes, metadata, raw gate tables, derivation rule, checker result, reviewer decision, lint/JUnit/release/parity outputs, bundle size, and final matrix delta.
- If authorization, rights, a hash-matched model, a synchronized source, or a required gate input is absent, stop and record that exact blocker without flipping a cell.

## MANDATORY SKILLS
- pvg

## nd_contract
status: new

### evidence
- Authored on 2026-09-26 from immutable WD-dmf2 raw QC, the synchronized WD-cpow pair, current WD-fay0/WD-t0il scope records, and the operator-supplied scout diagnosis embedded above.

### proof
- [ ] Pending explicit operator authorization and no-download rework execution.

## Acceptance Criteria


## Design


## Notes
## PM Decision
ACCEPTED [2026-09-26]: The prior DOCS_STALE gap is closed at docs-only commit 982e9d6d.

The delta from 45d4c7f3 is exactly one documentation line. The corrected sentence accurately states that WD-7fvx exercised authorized SSH/RTX 3090 execution, preexisting hash-verified local models, queue admission/retry, and QC/AV, while it made no model/dependency/provider mutation or download, performed no training or paid-provider work, and changed no threshold or protected queue/preflight/renderer/wiring/engine semantics.

Fresh PM checks: targeted director suite 34/34 PASS; checker PASS with owned_warnings=0; pvg verify PASS; release verify PASS release=ready tag_created=false; git diff --check PASS; protected-file parity PASS. The prior full-suite receipt remains valid for the unchanged implementation/evidence tree: 2108 tests, 0 errors, 0 failures, 1 skipped. Independent hash audit reconfirmed WD-dmf2 parity, WD-cpow source identities, both output hashes, 26/26 objective gates, and the 200-file/5920-KiB bundle. A concurrent unrelated WD-obkn backlog-lint path error remains outside WD-7fvx and does not alter this docs-only delta.

## nd_contract
status: accepted

### evidence
- Corrected docs-only commit 982e9d6d09cbaddad51b7074411564923a65671a.
- docs/director-capabilities.md:37,43 and the unchanged WD-7fvx evidence bundle.
- Fresh targeted/checker/pvg/release/diff/protected checks plus the scoped full-suite receipt.

### proof
- [x] AC #1 through AC #9 verified, including the corrected AC #8 documentation boundary.

## nd_contract
status: delivered

### evidence
- Corrected docs-only commit 982e9d6d and rerun gates: targeted director 34/34 PASS, checker exit 0/owned_warnings=0, pvg verify PASS, git diff --check PASS, protected parity PASS. Existing full-suite receipt remains scoped to the one-line docs-only delta from 45d4c7f3 to 982e9d6d.

### proof
- [x] AC #8 documentation now accurately distinguishes exercised authorized host/queue/QC work from unchanged download, threshold, dependency/provider, and protected-engine boundaries.
- [x] AC #1 through AC #9 remain PASS.


## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-26.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## Implementation Evidence

### DOCS_STALE rework scope
- Reclaimed WD-7fvx after the PM rejection.
- Changed exactly one sentence in `docs/director-capabilities.md:43` (one-line diff, one insertion and one deletion).
- The corrected sentence now states that WD-7fvx exercised authorized SSH execution on the RTX 3090 host, preexisting hash-verified local models, durable queue admission/retry transitions, and QC/AV gates.
- It also states that WD-7fvx did not perform or change model/dependency/provider mutation or download, training, paid-provider work, thresholds, or protected queue/preflight/renderer/wiring/engine semantics.
- No media, GPU, SSH, model download, dependency mutation, provider mutation, or WD-obkn path was touched during this docs rework.

Commands run:
- `uv run --frozen --extra dev pytest -q tests/test_director_capabilities.py`
- `uv run --frozen python scripts/verify_maestro_parity.py datasets/runs/maestro-parity/WD-7fvx`
- `pvg verify docs/director-capabilities.md datasets/runs/maestro-parity/WD-7fvx/build_evidence.py datasets/runs/maestro-parity/WD-7fvx/host-scripts/wd_7fvx_run.py datasets/runs/maestro-parity/WD-7fvx/judge-start.sh datasets/runs/maestro-parity/WD-7fvx/judge-stop.sh datasets/runs/maestro-parity/WD-7fvx/standing-gates-final.md`
- `git diff --check`
- `git diff --exit-code 2b4714bf -- services/jobs/queue.py services/director/renderers/policy.py services/director/wiring.py services/jobs/preflight.py scripts/run_film.py`

Summary: targeted director PASS 34/34; checker PASS exit 0 with owned_warnings=0; pvg verify PASS 2 files/0 issues; git diff --check PASS; protected-file parity PASS exit 0. Existing full-suite receipt remains valid for this commit because `982e9d6d` changes only the stale one-line docs sentence relative to `45d4c7f3`; no code, media, model, dependency, provider, queue, preflight, renderer, wiring, engine, or evidence payload path changed. The retained clean-tree result is tests=2108, errors=0, failures=0, skipped=1.

Commit SHA: 982e9d6d

### AC Verification after DOCS_STALE rework
| AC | Result | Evidence |
|---|---|---|
| 1 | PASS | Existing authorization/immutability evidence unchanged |
| 2 | PASS | Existing zero-download/model-hash evidence unchanged |
| 3 | PASS | Existing full-utterance evidence unchanged |
| 4 | PASS | Existing synchronized source-pair evidence unchanged |
| 5 | PASS | Existing motion-frame evidence unchanged |
| 6 | PASS | Existing raw QC evidence unchanged |
| 7 | PASS | Existing 26 mechanical gates unchanged |
| 8 | PASS | Corrected `docs/director-capabilities.md:43`; checker, tests, pvg verify, and matrix evidence pass |
| 9 | PASS | Protected parity and no-mutation boundaries pass |

## nd_contract
status: delivered

### evidence
- Docs-only rework commit `982e9d6d`; targeted/checker/pvg/diff/protected gates rerun PASS; prior full-suite receipt explicitly scoped to the docs-only delta.

### proof
- [x] AC #1 through AC #9 PASS after correcting the stale authorization-boundary sentence.


## nd_contract
status: rejected

### evidence
- PM rejection applied via pvg story reject on 2026-09-26.

### proof
- [ ] Story requires another developer delivery before it can be accepted.


## Implementation Evidence

Commit SHA: 45d4c7f3

Commands run: see the preceding verifier-shaped addendum; all exact terminal receipts are retained in datasets/runs/maestro-parity/WD-7fvx/standing-gates-final.md.

Summary: all required commands passed; full suite 2108 tests, 0 errors, 0 failures, 1 skipped; checker exit 0; release=ready.

## nd_contract
status: delivered

### evidence
- Exact final evidence commit SHA supplied for structural verification.

### proof
- [x] AC #1 through AC #9 remain PASS.


## Implementation Evidence

Commands run:
- `pvg lint --backlog`
- `uv run --frozen --extra dev pytest -q tests/test_director_capabilities.py`
- clean-tree `/bin/bash`-precedence `uv run --frozen --extra dev pytest -q --junitxml=/tmp/WD-7fvx-full.xml`
- `uv run --frozen --extra dev wgp release verify`
- `uv run --frozen python scripts/verify_maestro_parity.py datasets/runs/maestro-parity/WD-7fvx`
- `pvg verify docs/director-capabilities.md datasets/runs/maestro-parity/WD-7fvx/build_evidence.py datasets/runs/maestro-parity/WD-7fvx/host-scripts/wd_7fvx_run.py datasets/runs/maestro-parity/WD-7fvx/judge-start.sh datasets/runs/maestro-parity/WD-7fvx/judge-stop.sh datasets/runs/maestro-parity/WD-7fvx/standing-gates-final.md`
- `git diff --check`

Summary: checker PASS exit 0 with owned_warnings=0; backlog lint PASS 139 scanned, 0 errors, 0 review findings; targeted PASS 34/34; full suite PASS tests=2108 errors=0 failures=0 skipped=1; release PASS release=ready tag_created=false; pvg verify PASS 0 issues; protected parity and diff-check PASS. All 9 story ACs PASS as detailed in the preceding Implementation Evidence (DELIVERED FOR REVIEW) block.

Commit SHA: test-producing `d71ca053245a508bec02f28b29f815d230aa6f37`; final evidence/pushed HEAD `45d4c7f3`.

Coverage: not instrumented and not claimed; evidence-only story with real no-mock host integration.

## nd_contract
status: delivered

### evidence
- The addendum preserves the exact commands, terminal summary, and commit SHA required by pvg delivery verification.

### proof
- [x] AC #1 through AC #9 remain PASS per the preceding AC table and bundle artifacts.


## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-26.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## Implementation Evidence (DELIVERED FOR REVIEW)

PROOF:

### Authorization, immutability, and scope
- Verbatim authorization is recorded in `operator-authorization.md` and `evidence.json.operator_authorization`: operator via /root dispatcher, timestamp `2026-09-26T20:31:00Z`, host `3090`, exact no-download scope/rights/stop boundary.
- Story base: `2b4714bf`. WD-dmf2 before/after recursive content identity is `32b443680a0dacde1103a87d3fa263d75744fa25614ec83d9a414a521020fd46` across 285 files (`baseline-parity-before.json`, `baseline-parity-after.json`); immutable.
- New evidence was written only under `datasets/runs/maestro-parity/WD-7fvx/` plus the mechanically derived two-cell matrix update in `docs/director-capabilities.md:37,43`.
- Bundle terminal size/count: 200 files, 5920 KiB (`bundle-file-count.txt`, `bundle-size-kib.txt`).

### No-download/model preflight and synchronized source pair
- Preflight matched all four required model hashes before queue admission: Whisper `9ecf7799…`, Qwen text `3445102e…`, Qwen projector `add205b7…`, SyncNet `961e8696…` (`host-preflight.json`, `model-hashes.txt`).
- Planned and actual model-download bytes are both 0; dependency/provider/model-fetch mutation lists are empty (`download-report.json`, `host-preflight.json`).
- Source pair recomputed identical before and after: prepared speech `e371ebe7ee1ce9964657b4f34f61d32fbff2a5345bdb90add6c3e7dba1ee2175` (2.333333 s, 24 kHz mono) and speech video `1cdac314c38142e15af22e1122a3df8177a5e2027b9a7fcde5807e13c8c407d3` (2.333333 s, 704x576, 24 fps) (`source-pair.json`, `host-final-state.json`).
- Instrumental `wd_rous_ace_generate.wav` was not copied or paired; `source-pair.json.instrumental_audio_used=false`.

### Real queue, outputs, and QC
- Final durable queue: `wangp-JobQueue-WD-7fvx`, job `job-1790457887200-3571e01c`, retry `attempt-8`, admission admitted, exit `done` (`queue-record.json`, `queue-final-state.json`).
- New director request hashes: audio `58f392037cd1d47c176d42ee8819c9172ddf539dae221c443e2f443a95e6ad99`; screenplay `eff6d93feaec455cd568595f8e9a8a9f2cd0a1f56ca8eda9beee8df341f4e50d`. Plan DBs and immutable plan queue/review records are retained under `planning/`.
- Newly composed audio and screenplay outputs are `960x768`, 24 fps, 56 frames, `2.333333` s, SHA-256 `c9b9dbc6038e6cc7a3403c05372cb6ed25d1d586ec6eceecc57615e608a7050b`. The paths are mode-specific and the bytes differ from both WD-cpow source `1cdac314…` and all WD-dmf2 outputs; deterministic reuse of the same synchronized pair yields identical reworked bytes across the two mode paths.
- Raw pre/post Whisper for both modes: intended `This is the last rain we have.`, transcript exact, score `1.0`, bar `0.6`.
- Raw identity action/speaker for both: `0.95/0.9`, bar `0.7`. Raw three-frame mouth center spreads: `0.016` x and `0.029` y, bar `<=0.03` each.
- Multicrop SyncNet for both: crop confidences `0.758436`, `1.126480`, `1.702520`; aggregate `1.126480 >= 1.0`, offset `10 <= 10` frames at 25 fps. Source motion proof has 3 unique frame hashes, so static zoompan is rejected.
- PID-scoped Qwen judge start/stop receipts are retained (`judge-start.*`, `judge-stop.*`); no broad operator service mutation.
- Reviewer decision is explicitly approved only for these two cells in `reviewer-record.md` and `evidence.json.reviewer_verdict`; no human PM acceptance or creative keeper claim is made.

### Mechanical gates, checker, and matrix
- `build_evidence.py` mechanically derived `objective-gates.json`: 26/26 gates `pass`; no failed value was converted to pass.
- Final checker command `uv run --frozen python scripts/verify_maestro_parity.py datasets/runs/maestro-parity/WD-7fvx` exited 0: `PASS wangp-dspy.maestro-parity-evidence/v1 ... owned_warnings=0` (`checker-final.txt`).
- Matrix parser (`matrix-transition-check.json`): 10 row identities before/after match; exactly one changed row, `Auto/manual review checkpoints`; Prompt stays planned, Audio/music-video and Screenplay become `host_run_verified (WD-7fvx)`, generation evidence stays none, and the generated-media row is unchanged.

### CI/Test Results
- Commands run:
  - `pvg lint --backlog`
  - `uv run --frozen --extra dev pytest -q tests/test_director_capabilities.py`
  - clean-tree `/bin/bash`-precedence run of `uv run --frozen --extra dev pytest -q --junitxml=/tmp/WD-7fvx-full.xml`
  - `uv run --frozen --extra dev wgp release verify`
  - `uv run --frozen python scripts/verify_maestro_parity.py datasets/runs/maestro-parity/WD-7fvx`
  - `pvg verify <authored subset>`
  - `git diff --check`
- Summary: backlog lint PASS 139 scanned / 0 errors / 0 review findings; targeted PASS 34/34; full suite PASS `tests=2108, errors=0, failures=0, skipped=1`; release PASS `release=ready`, `tag_created=false`; checker PASS 0 warnings; pvg verify PASS 2 files / 0 issues; diff-check PASS.
- Coverage: not instrumented/claimed. This is an evidence-only story with no production package path change; real integration behavior is covered by the 2108-test suite plus the no-mock host/QC bundle.
- The first full-suite attempts are owned in `standing-gates-final.md`: Homebrew Bash 5.2.37 reproduced a heredoc deadlock, and writing suite receipts inside the bundle made release tree checks dirty. The terminal clean-tree `/bin/bash`-precedence run and exact-test probe are retained. One FastAPI/Starlette deprecation warning is also reported, not suppressed.

### Commit
- Test-producing implementation commit: `d71ca053245a508bec02f28b29f815d230aa6f37`
- Final evidence/pushed HEAD: `45d4c7f3` on `story/WD-7fvx`
- Both commits are pushed to `origin/story/WD-7fvx`.

### AC Verification
| AC | Requirement | Evidence | Status |
|---|---|---|---|
| 1 | Authorization, immutable WD-dmf2 identity, namespace-only new evidence | operator-authorization.md; baseline-parity-before/after.json | PASS |
| 2 | Zero downloads, all model hashes, no dependency/provider/fetch mutation | host-preflight.json; download-report.json | PASS |
| 3 | Complete synchronized utterance preserved | source-pair.json; director-qc-evidence.json (2.333333 s / 56 frames) | PASS |
| 4 | Audio mode uses matching WD-cpow speech pair; no instrumental pairing | source-pair.json; hash-ledger.json | PASS |
| 5 | Screenplay uses motion-bearing speech video, rejects zoompan | director-qc-evidence.json; review/*/frame-hashes.json | PASS |
| 6 | Raw pre/post Whisper, identity, three-frame mouth, multicrop SyncNet at unchanged bars | director-qc-evidence.json; qc/*-target.json | PASS |
| 7 | Objective values mechanically derived and fail closed | build_evidence.py; objective-gates.json | PASS |
| 8 | Checker exit 0, all applicable gates pass, explicit reviewer approval, mechanical matrix citation | checker-final.txt; reviewer-record.md; matrix-transition-check.json; docs/director-capabilities.md | PASS |
| 9 | No threshold/queue/preflight/renderer/wiring/engine semantic change, no baseline mutation/fabrication | protected-parity-2b4714bf.*; baseline parity; objective-gates.json | PASS |

LEARNINGS:
- Pairing the speech video with its exact prepared audio removes both predecessor audio/screen clip-1 source failures without changing any bar.
- A visually assessable action prompt is necessary for the still-frame identity judge; dialogue semantics belong to Whisper/SyncNet, not action vision.
- Normalized mouth consensus and SyncNet respond differently to camera stabilization. The final 960x768 two-axis follow preserved all 56 frames and passed both.
- Homebrew Bash 5.2.37 can deadlock this repository's LF004 heredoc test; `/bin/bash` precedence is a non-mutating run environment workaround, with the exact probe retained.
- Full-suite receipts must stay outside the repository until the run terminates or release tree checks correctly fail on their own dirt.

### DISCOVERED_BUG (one block per bug; details in standing-gates-final.md)
- Homebrew Bash 5.2.37 heredoc deadlock in `tests/test_lf004_recovery_tooling.py`.
- FastAPI testclient emits a Starlette/httpx deprecation warning.

## nd_contract
status: delivered

### evidence
- Implementation commit `d71ca053245a508bec02f28b29f815d230aa6f37`; final evidence commit `45d4c7f3`; checker exit 0; full suite 2108/0 errors/0 failures; release ready; bundle and matrix evidence under `datasets/runs/maestro-parity/WD-7fvx/`.

### proof
- [x] AC #1: authorization and immutable baseline proven.
- [x] AC #2: zero-download/model preflight and no mutation proven.
- [x] AC #3: full synchronized utterance preserved.
- [x] AC #4: matching speech pair used; instrumental excluded.
- [x] AC #5: motion-bearing speech visual proven.
- [x] AC #6: all raw gates and unchanged bars recorded.
- [x] AC #7: 26 mechanical gates derived and pass.
- [x] AC #8: checker, reviewer, and exact two-cell matrix transition recorded.
- [x] AC #9: protected semantics, baseline immutability, and no fabrication verified.


## History
- 2026-09-26T20:53:45Z dep_added: blocks WD-fay0
- 2026-09-26T20:53:46Z dep_added: blocked_by WD-dmf2
- 2026-09-26T20:53:46Z dep_added: blocked_by WD-cpow
- 2026-09-26T20:57:47Z status: open -> in_progress
- 2026-09-26T20:57:48Z auto-follows: linked to predecessor WD-5k28
- 2026-09-26T20:57:48Z claimed by dev-WD-7fvx
- 2026-09-26T23:47:34Z status: in_progress -> in_progress
- 2026-09-26T23:47:34Z auto-follows: linked to predecessor WD-m7xw
- 2026-09-26T23:58:04Z status: in_progress -> open
- 2026-09-26T23:58:04Z released by speed
- 2026-09-27T00:01:24Z status: open -> in_progress
- 2026-09-27T00:01:24Z auto-follows: linked to predecessor WD-43tj
- 2026-09-27T00:01:24Z claimed by dev-WD-7fvx
- 2026-09-27T00:05:33Z status: in_progress -> in_progress
- 2026-09-27T00:05:33Z auto-follows: linked to predecessor WD-9ymi
- 2026-09-27T00:13:32Z status: in_progress -> closed
- 2026-09-27T00:13:32Z dep_removed: no_longer_blocks WD-fay0

## Links
- Parent: [[WD-3nod]]
- Blocked by: [[WD-dmf2]], [[WD-cpow]]
- Follows: [[WD-5k28]], [[WD-m7xw]], [[WD-43tj]], [[WD-9ymi]]

## Comments

### 2026-09-26T23:58:06Z speed
## PM Decision
REJECTED [2026-09-26]:
EXPECTED: AC #8 requires docs/director-capabilities.md to change only mechanically from the WD-7fvx bundle and accurately describe the authorized run boundary.
DELIVERED: docs/director-capabilities.md:37 correctly marks only Audio/music-video and Screenplay review checkpoints as host_run_verified (WD-7fvx), but docs/director-capabilities.md:43 still ends with: "No GPU, SSH, model download, paid provider, renderer admission, retry, QC/AV, or gate semantic is exercised or changed by this planning slice." The delivered bundle contradicts that stale sentence: evidence.json records the SSH host command; host-preflight.json records the RTX 3090/local Qwen judge; queue-record.json records admitted attempt-8; queue-final-state.json records retry/done; and director-qc-evidence.json records Whisper, identity, mouth-box, and SyncNet QC.
GAP: DOCS_STALE: the inherited planning-only sentence was not updated after promoting two cells from an authorized host/QC bundle. It falsely says GPU, SSH, queue admission/retry, and QC/AV were not exercised, so the final matrix narrative is not mechanically true to WD-7fvx and fails AC #8.
FIX: Update only the stale authorization-boundary sentence to accurately distinguish what WD-7fvx exercised (authorized SSH/3090 execution, preexisting local models, queue admission/retry, and QC/AV) from what it did not do or change (model/dependency/provider mutation or download, thresholds, and protected queue/preflight/renderer/wiring/engine semantics). Then rerun the relevant standing gates from the new final head, including targeted director tests, the maestro-parity checker, pvg verify, git diff --check, and protected-file parity; supply the corrected commit SHA and outputs.

## nd_contract
status: rejected

### evidence
- docs/director-capabilities.md:37,43 versus evidence.json, host-preflight.json, queue-record.json, queue-final-state.json, and director-qc-evidence.json.
- Independently verified checker PASS, 26/26 objective gates, source/output hashes, WD-dmf2 parity, protected-file parity, and delivery-proof shape before finding the stale docs claim.

### proof
- [ ] AC #8: documentation is not mechanically accurate at the final authorization-boundary sentence.

### 2026-09-27T00:07:24Z speed
## nd_contract
status: delivered

### evidence
- Corrected docs-only commit `982e9d6d` is pushed. Rerun gates: targeted director 34/34 PASS; checker exit 0 with owned_warnings=0; pvg verify PASS; git diff --check PASS; protected parity PASS. The existing full-suite receipt remains scoped to the one-line docs-only delta from `45d4c7f3` to `982e9d6d`.

### proof
- [x] AC #8 documentation now accurately distinguishes exercised authorized SSH/3090 execution, preexisting local models, queue admission/retry, and QC/AV from unchanged download, threshold, dependency/provider, and protected-engine boundaries.
- [x] AC #1 through AC #9 remain PASS.

