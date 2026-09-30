---
id: WD-qthq
title: "Editor authorized host export media"
status: closed
priority: 1
type: task
labels: [editor, evidence, external-integration, operator-decision, delivered, accepted]
parent: WD-3nod
created_at: 2026-09-29T08:43:01Z
created_by: speed
updated_at: 2026-09-30T14:59:48Z
content_hash: "sha256:69a629658d5973fbe605f05c356daa99d12893a934c23c05e5610f4c2745a30c"
follows: [WD-23rs, WD-p587, WD-32hk]
assignee: dev-WD-qthq
closed_at: 2026-09-30T14:59:48Z
close_reason: "Accepted: independently verified exact PR head 284c7f16259cab5c85a017f06bad1f29934e04ed CI, scoped diff, exact immutable source/project identities, one CPU-only editor_export queue job, real media/hash/metadata/visual/objective evidence, canonical checker, docs transition, and standing gates."
---

## Description
## Context

The strict Maestro completion audit found one unowned non-matrix row:

- `docs/editor.md` line 19 — **Authorized host export/media**
- Current disposition: `planned`
- Blocker: no authorized host run bundle with command, provenance, queue attempts, output hashes, QC evidence, and reviewer linkage.

WD-gc09 accepted the no-GPU editor project/export implementation only. Its deterministic JSON export and local queue submission are useful prerequisites, but they explicitly made no media claim. This story owns the missing authorized host media execution and must not inherit WD-gc09 as generation evidence.

## Immutable local reference

The host execution consumes two existing committed sources:

| Role | Repository path | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| video | `datasets/runs/provenance/lf002-vibevoice-film-20260917/cut1.mp4` | 1,421,376 | `b53e5d37457f61db8c1bfa31d11d8d873139bf0aabddf97e0efa245de4d702a3` |
| audio | `datasets/runs/provenance/lf002-vibevoice-audition-20260916/audio/orin.wav` | 102,444 | `f3d66cac4458d0d33870ff6dc97df75eff95d57b154180dd303be4f955c91857` |

A local reference project with two ordered video clips (`0–2 s`, `2–4 s`) and one audio clip (`0–4 s`) was generated from those exact bytes through the real `ProjectStore` and `export_project` APIs. Measured identities:

- Project file SHA-256: `e3ac1c1b973fc2e398b083d4e22eee98ed973cf0b8f09ca338c1d9848d35341e`
- Export file SHA-256: `ef2786b17d71c45a4931d4de88e03b129e040930bd63ad22185ad65df2fa9f12`
- Export `project_sha256`: `66dcc7acbca38fbeece2bbe478621f61bf9ac5dd166219b335f5c9a5242bed27`
- Director request SHA-256: `765eda5c737982c9fb9f2f72c8ad0a10a8cc205ca518a7aa25e8ff992dd82d46`
- Assembly continuity digest: `2d13c6c05ee59f9d63807bf36de1c1eb600fd5e00e3679bfb4fcaf78b55887c2`

## USER INTENT

Observable outcome: after explicit authorization, the operator can run one governed editor host-export command and it returns a checker-valid real media bundle while preserving every immutable source byte.

## Operator authorization status

**NOT AUTHORIZED.** No operator approval exists for host `3090` execution, source transfer, queue execution, or editor media export. Until verbatim approval is recorded, all work must remain local and fail closed before SSH.

Authorization must explicitly approve:

- host `3090`;
- transfer and execution of only the two source bytes above;
- exactly one `kind=editor_export` job through the governed queue;
- CPU-only FFmpeg assembly on the render host is allowed for this row, with `gpu_work=false`;
- zero model downloads, provider spend, training, GUI work, unrelated host mutation, or protected-engine semantic change.

## OUT OF SCOPE

- WD-bw0h clean-machine H3 retry; separate story and authorization.
- WD-28ac LTX dependency downloads; separate story and authorization.
- Any editor GUI/browser surface.
- New model inference, model download, provider API, or training.
- Changes to protected engine files.
- Relabelling WD-gc09's deterministic JSON export as media.

## DIFF BUDGET

About 7 files and under 700 authored changed LOC, excluding copied source media and generated output.

## Boundary Map
PRODUCES:
- datasets/runs/maestro-parity/editor-host-export/project/lf002-editor-media.wgp-editor.json -> canonical deterministic project with the exact two-source/two-video/one-audio reference above
- datasets/runs/maestro-parity/editor-host-export/export.json -> canonical deterministic `wangp-dspy.editor-export/v1` reference
- datasets/runs/maestro-parity/editor-host-export/operator-authorization.template.json -> fail-closed `not_authorized` template binding exact source and project hashes
- scripts/run_editor_host_export.py -> prepare_reference(root: Path) -> Path; verify_authorization(record: Mapping[str, object]) -> None; authorized command contract and fail-closed host runner
- datasets/runs/maestro-parity/editor-host-export/ -> complete queue, source transfer, native FFmpeg log, output, hash, ffprobe, objective-gate, checker, and reviewer evidence
- tests/test_editor_host_export.py -> real-process local reference/authorization/drift tests and recorded host replay coverage
- docs/editor.md -> terminal update for exactly the Authorized host export/media row

CONSUMES:
- WD-gc09: services/editor/project_store.py -> ProjectStore.create(path: str | Path, project: EditorProject) -> ProjectStore; import_source(source: str | Path, kind: TrackKind, asset_id: str) -> SourceAsset; verify_sources(project: EditorProject | None = None) -> list[SourceAsset]
  source: construct and verify the exact non-destructive project; source bytes must remain unchanged.
- WD-gc09: services/editor/assembly_exporter.py -> export_project(store: ProjectStore, project: EditorProject | None = None) -> dict[str, object]; write_export(payload: Mapping[str, object], destination: str | Path) -> Path; enqueue_export(payload: Mapping[str, object], export_path: str | Path, database: str | Path) -> str
  source: emit the deterministic export and submit one real pending `kind=editor_export` queue record.
- WD-gc09: services/jobs/queue.py -> JobQueue.submit(*, plan_ref: str, clips: Sequence[dict]) -> str
  source: queue admission must use the existing real JobQueue; no second queue semantics.
- WD-r81u: datasets/runs/maestro-parity/WD-r81u/ -> accepted FFmpeg host-run provenance, queue, ffprobe, and objective-gate pattern
  source: follow the accepted host FFmpeg evidence pattern; do not weaken gates.
- WD-23rs: scripts/verify_maestro_parity.py -> verify_bundle(bundle: Path) -> VerificationReport
  source: final media evidence must pass the canonical fail-closed checker.

## Story Acceptance Criteria
1. [State] A local reference command constructs the exact project/export from the two declared source bytes and reproduces the four declared project/export/request/continuity hashes; imported source bytes remain unchanged.
2. [Unwanted] With authorization absent, partial, ambiguous, host-mismatched, or source-hash-mismatched, the runner exits nonzero before SSH/workspace transfer and records a typed authorization/input failure.
3. [State] After verbatim operator authorization, host `3090` preflight verifies SSH, workspace isolation, FFmpeg availability, disk headroom, and both exact source hashes before queue admission; no model byte is downloaded.
4. [State] Exactly one pending `kind=editor_export` job is admitted through the real `JobQueue`, then claimed/executed once with exact native argv and logs; CPU-only FFmpeg assembly is permitted and `gpu_work=false` is recorded.
5. [State] The authorized run emits one real nonempty media artifact that concatenates the two declared video segments in order and carries the declared audio; the artifact is retrieved, hashed, ffprobe-probed, visually represented, and passes objective duration/order/audio/media gates.
6. [State] Source and project files are byte-identical before and after host execution; queue attempt state, host workspace identity, native logs, output hash/metadata, checker result, and reviewer verdict are recorded in the bundle.
7. [State] `docs/editor.md` changes only the Authorized host export/media row from planned to an evidence-backed terminal disposition linked to the bundle.
8. [State] Focused editor-host-export tests, the undeselected full suite, `pvg lint --backlog`, `wgp release verify` with `release=ready` and `tag_created=false`, protected-file parity, `git diff --check`, and exact-head CI pass.

## Testing Requirements
- Integration tests are mandatory with no mocked ProjectStore, export, queue, FFmpeg, hash, ffprobe, or checker behavior.
- Local tests must cover exact reference construction, source immutability, absent/partial/tampered authorization, host mismatch, wrong source hash, and export/queue drift.
- Authorized host coverage may use a recorded real-process replay only if it proves exact native argv, queue transitions, source/output hashes, media metadata, gates, and checker result; no synthetic media substitution.
- Run focused tests, undeselected full suite with parsed JUnit, canonical checker, backlog lint, release verification, protected parity, diff check, and exact-head CI.

## Delivery Requirements
- Record verbatim operator authorization, exact command/argv, repository commit/tree identity, source/project/export hashes, host/workspace identity, queue state, native log, output hash and metadata, bundle size, PR, CI, and AC table.
- Include `LEARNINGS:`.
- If authorization, preflight, queue execution, FFmpeg, retrieval, or checking fails, stop and record the typed boundary; never substitute existing media.

## MANDATORY SKILLS
- pvg
- tool-systematic-debugging

## nd_contract
status: new

### evidence
- Current strict audit at main `2c20caa1`: editor Authorized host export/media remains planned; WD-gc09 is no-GPU only.
- Exact two-source reference and hashes above were generated locally with the real ProjectStore/export APIs; no SSH, model, download, or host execution occurred.

### proof
- [ ] Pending explicit authorization, fail-closed runner, exact governed queue execution, real editor media bundle, checker proof, matrix transition, and standing gates.

## Acceptance Criteria


## Design


## Notes


## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-30.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## Implementation Evidence

Summary: Delivered the operator-authorized editor host-export media path. One governed `kind=editor_export` queue job ran on host `3090`, CPU-only FFmpeg produced a real nonempty four-second ordered video/audio artifact, both immutable source identities remained unchanged, all eight objective gates passed, the canonical Maestro parity checker exited zero, and the single editor row now links to the host-run evidence.

Commands run:
- `uv run --frozen --extra dev pytest -q tests/test_editor_host_export.py tests/test_runtime_host_wiring.py --junitxml=/tmp/wd-qthq-delivery-focused.xml`
- `python3 scripts/verify_maestro_parity.py datasets/runs/maestro-parity/editor-host-export/host-run`
- `pvg verify scripts/run_editor_host_export.py tests/test_editor_host_export.py datasets/runs/maestro-parity/editor-host-export/operator-authorization.template.json --include-tests --format=text`
- `pvg lint --backlog`
- `uv run --frozen --extra dev wgp release verify --json`
- `git diff --exit-code origin/main -- services/jobs/queue.py services/director/renderers/policy.py services/director/wiring.py services/jobs/preflight.py scripts/run_film.py`
- `git diff --check`
- GitHub exact-head CI at PR #218 head `284c7f16259cab5c85a017f06bad1f29934e04ed`.

SHA: `284c7f16259cab5c85a017f06bad1f29934e04ed` on `story/WD-qthq`; PR https://github.com/jmanhype/wangp-dspy/pull/218

### CI/Test Results
- Focused editor/runtime host-wiring JUnit: `tests=14 errors=0 failures=0 skipped=0`.
- Exact-head CI run `36724918128`: `test` success at the same head, 24m56s, https://github.com/jmanhype/wangp-dspy/actions/runs/36724918128.
- Canonical checker: `PASS wangp-dspy.maestro-parity-evidence/v1 datasets/runs/maestro-parity/editor-host-export/host-run owned_warnings=0`.
- `pvg verify`: PASSED, 2 files, 0 issues.
- `pvg lint --backlog`: 153 scanned, 0 errors, 0 review findings.
- Release verification: `ready=true`, `tag_created=false`.
- Protected-file parity: exit 0.
- `git diff --check`: pass.
- Host queue: `job-1790730445881-aa610b52`, attempt 1, final `done`, exit `succeeded`.
- Output: `outputs/editor-export.mp4`, 515764 bytes, SHA-256 `4f7c955ebbf68daa98eed4c117cb879db8dfc6744924d6f1e7ad1e1de8c8725e`.
- FFprobe: 704x576, 24 fps, 4.0 s, AAC 24 kHz mono.
- Objective gates: 8/8 pass, including first-half SSIM `0.989087`, second-half SSIM `0.991025`, audio-head correlation `0.9995817278979054`, and audio-padding RMSE `0.000001645215474140844`.
- Canonical evidence bundle: `datasets/runs/maestro-parity/editor-host-export/host-run/evidence.json`.
- Boundary history: two local wrapper defects and two post-preflight local transport defects are recorded under `boundary-attempts/`; they did not execute a second queue job or FFmpeg operation.

### AC Verification
| AC | Result | Evidence |
| --- | --- | --- |
| 1 exact local reference and immutable source hashes | PASS | canonical project/export identities reproduced; before/after source hashes equal in `host-run/run-summary.json` |
| 2 fail-closed authorization/input handling | PASS | `tests/test_editor_host_export.py`; typed boundary artifacts; focused 14/14 |
| 3 authorized host preflight and zero model downloads | PASS | `execute-preflight.log`, host facts in `run-summary.json`, `model_downloads=0` |
| 4 exactly one real governed queue job and CPU FFmpeg | PASS | queue DB and `queue_attempt` record one `editor_export` job, attempt 1, `gpu_work=false` |
| 5 real ordered media artifact and objective gates | PASS | hashed MP4, ffprobe, contact sheet, SSIM/audio gates, checker PASS |
| 6 source/project immutability and complete evidence | PASS | before/after hashes equal; queue, native logs, transfer/hash logs, metadata, gates, reviewer record present |
| 7 exact editor row terminal transition | PASS | `docs/editor.md` updates only Authorized host export/media to evidence-backed host run |
| 8 focused/full/standing gates | PASS | focused 14/14; exact-head full CI success; lint, release, protected parity, checker, and diff gates pass |

LEARNINGS:
- The remote root is operator-specific authorization data, not an active-runtime default; binding it in the authorization record preserves the no-host-defaults gate.
- SSH scripts must be staged to absolute remote paths and invoked without `-n` stdin redirection.
- Local wrapper failures before queue admission can be repaired without consuming the authorized operation; the successful run records exact continuity and all boundary attempts.

## Implementation Boundary (HOST PREFLIGHT — NOT DELIVERED)

- Command: `bash /tmp/wd_qthq_execute_once.sh`; exit `3`.
- Typed diagnostic: `EDITOR_HOST_PREFLIGHT_INVALID` — SSH preflight returned no workspace/runtime facts.
- Root cause evidence: the SSH wrapper used `-n`, which redirects stdin from `/dev/null`, while the preflight script was supplied on stdin to remote `/bin/sh -s`. The SSH process exited `0`, but stdout and stderr were empty and the preflight facts were absent.
- Authoritative artifacts: `datasets/runs/maestro-parity/editor-host-export/host-run/ssh-preflight.log` (SHA-256 `9d3e4287aa5673f4a7bc87fd79f0202f99eb9d73bc14cff87625dcfb22983717`) and `datasets/runs/maestro-parity/editor-host-export/host-boundary-20260929T193758Z.md`.
- Host effect: one SSH listener contact only. No remote preflight script execution, source/project/export transfer, workspace population, queue admission, FFmpeg execution, media retrieval, model download, GPU/provider work, or media substitution occurred.
- Stopped fail-closed without retry or delivery as required.

## nd_contract
status: in_progress

### evidence
- Exact local guard and source/project/export preflight passed at `04f5b7261db2d1e35596bc9761fc38734aafae89`.
- Authorized host attempt stopped at `EDITOR_HOST_PREFLIGHT_INVALID`; only `host-run/ssh-preflight.log` exists.

### proof
- [x] Verbatim authorization recorded as `Authorize`.
- [x] Exact local source/project/export identities verified.
- [x] Typed host boundary recorded without retry.
- [ ] Host preflight facts, transfer, one real editor_export queue execution, CPU-only FFmpeg media, evidence bundle, row transition, and standing gates remain incomplete.

## Implementation Boundary (NOT DELIVERED)

- Command: `bash /tmp/wd_qthq_execute_once.sh`
- Result: exit `1` at the local wrapper HEAD equality check, before the story runner was invoked.
- Typed boundary: `EDITOR_HOST_EXECUTION_GUARD_HEAD_MISMATCH`; observed HEAD `04f5b7261db2d1e35596bc9761fc38734aafae89`, incorrect expected full SHA `04f5b7262d4153c2e58fc4c8f930a6ad30e7bf5b`.
- Evidence: `datasets/runs/maestro-parity/editor-host-export/local-boundary-20260929.md`.
- No SSH contact, source transfer, workspace mutation, queue admission, FFmpeg execution, media retrieval, model download, GPU/provider work, or media substitution occurred. `host-run/` remained absent.
- Stopped fail-closed without retry or delivery as required.

## nd_contract
status: in_progress

### evidence
- Pre-execution authorization/reference checks passed at clean pushed head `04f5b7261db2d1e35596bc9761fc38734aafae89`.
- Authorized execution wrapper failed before runner invocation due the typed local HEAD guard mismatch above.

### proof
- [x] Verbatim authorization recorded as `Authorize`.
- [x] Local source/project/export hashes verified.
- [ ] Authorized host preflight, transfer, one real editor_export queue execution, CPU-only FFmpeg media, evidence bundle, row transition, and standing gates remain incomplete.

## Implementation Evidence (LOCAL PREPARATION ONLY — NOT DELIVERED)

PROOF:
- Commit: `e55588f57fd46ca43e144a57662a09eafad1668a` on `story/WD-qthq`; pushed to origin.
- PR: https://github.com/jmanhype/wangp-dspy/pull/218
- PR head verified: `e55588f57fd46ca43e144a57662a09eafad1668a`; CI `test` passed in 22m56s at https://github.com/jmanhype/wangp-dspy/actions/runs/36551766900/job/109351377903
- Added the immutable two-source project workspace and canonical export. SHA-256: project file `e3ac1c1b973fc2e398b083d4e22eee98ed973cf0b8f09ca338c1d9848d35341e`; export `ef2786b17d71c45a4931d4de88e03b129e040930bd63ad22185ad65df2fa9f12`; project identity `66dcc7acbca38fbeece2bbe478621f61bf9ac5dd166219b335f5c9a5242bed27`; director request `765eda5c737982c9fb9f2f72c8ad0a10a8cc205ca518a7aa25e8ff992dd82d46`; continuity `2d13c6c05ee59f9d63807bf36de1c1eb600fd5e00e3679bfb4fcaf78b55887c2`.
- Added `operator-authorization.template.json` with status `not_authorized`, host `3090`, exactly one `kind=editor_export` job, `gpu_work=false`, `model_downloads=0`, and exact source/project/export bindings.
- Added `scripts/run_editor_host_export.py`: typed local prepare/verify, exact hash verification through real `ProjectStore`/`export_project`, strict authorization validation, argv-only authorized command representation, and fail-closed execution refusal. No SSH execution is wired.
- Focused command: `uv run --frozen --extra dev pytest tests/test_editor_host_export.py -q` — 7 passed, 0 failed.
- Full undeselected command: `uv run --frozen --extra dev pytest -q --junitxml=/tmp/wd-qthq-junit.xml` — parsed JUnit: 2134 tests, 0 failures, 0 errors, 1 existing `WANGP_3090`-gated live-host skip (`tests.test_jobs_integration_3090.test_live_preflight_against_3090`); no deselection.
- `pvg verify scripts/run_editor_host_export.py tests/test_editor_host_export.py datasets/runs/maestro-parity/editor-host-export/operator-authorization.template.json --include-tests` — PASSED, 0 issues.
- `pvg lint --backlog` — 153 issues scanned, 0 errors, 0 review findings.
- `uv run --frozen --extra dev wgp release verify --json` — all checks pass, `ready=true`, `tag_created=false`.
- Protected parity: `git diff --exit-code origin/main -- services/jobs/queue.py services/director/renderers/policy.py services/director/wiring.py services/jobs/preflight.py scripts/run_film.py` — exit 0, no output.
- `git diff --check` — clean.

BOUNDARY — NOT DELIVERED:
- No SSH or host-3090 contact, workspace transfer, model download/HEAD request, provider spend, media generation, GUI work, or protected-engine edit occurred.
- Queue execution was not run; tests admit one pending `kind=editor_export` job only in a local disposable SQLite database and leave it pending.
- `docs/editor.md` is unchanged; Authorized host export/media remains unclaimed.
- Authorization is still absent. This is local export preparation only and must not be treated as delivery or media evidence.

LEARNINGS:
- The exact project name was `LF002 authorized editor media export`; the dispatcher-supplied local generator removed ambiguity and reproduced all five declared identities.
- Active Python scripts must not hardcode quoted operator host aliases. Reading host `3090` from the committed not-authorized template satisfies both story binding and the existing no-host-defaults runtime gate.
- The intentionally gated live 3090 integration test is the sole full-suite skip when host contact is forbidden; it must remain skipped rather than violating authorization.

## nd_contract
status: in_progress

### evidence
- Commit `e55588f57fd46ca43e144a57662a09eafad1668a`; PR #218; exact-head CI passed.
- Local preparation and fail-closed tests verified; no authorized host execution attempted.

### proof
- [x] Authorization-free local reference/export/template/runner/tests prepared.
- [ ] Verbatim operator authorization recorded.
- [ ] Host preflight, transfer, exactly one executed governed queue job, media output, checker/review evidence, and `docs/editor.md` terminal disposition completed.


## History
- 2026-09-29T08:43:02Z dep_added: blocks WD-fay0
- 2026-09-29T08:43:02Z status: open -> deferred
- 2026-09-29T08:44:05Z status: deferred -> open
- 2026-09-29T08:44:11Z status: open -> in_progress
- 2026-09-29T08:44:11Z auto-follows: linked to predecessor WD-23rs
- 2026-09-29T08:44:11Z claimed by dev-WD-qthq
- 2026-09-29T10:17:13Z status: in_progress -> open
- 2026-09-29T10:17:13Z released by speed
- 2026-09-29T10:17:15Z status: open -> deferred
- 2026-09-29T23:18:03Z status: deferred -> open
- 2026-09-29T23:18:11Z status: open -> in_progress
- 2026-09-29T23:18:11Z auto-follows: linked to predecessor WD-p587
- 2026-09-29T23:18:11Z claimed by dev-WD-qthq
- 2026-09-30T14:49:16Z status: in_progress -> in_progress
- 2026-09-30T14:49:16Z auto-follows: linked to predecessor WD-32hk
- 2026-09-30T14:59:48Z status: in_progress -> closed
- 2026-09-30T14:59:48Z dep_removed: no_longer_blocks WD-fay0

## Links
- Parent: [[WD-3nod]]
- Follows: [[WD-23rs]], [[WD-p587]], [[WD-32hk]]

## Comments

### 2026-09-29T10:17:15Z speed
Parked as operator-gated after local preparation. PR 218 head e55588f57fd46ca43e144a57662a09eafad1668a has exact-head CI success and fail-closed editor project/export/authorization tests, but no operator approval exists. No network/host/model action is authorized by this status change.

### 2026-09-29T23:17:31Z speed
OPERATOR AUTHORIZATION at 2026-09-29T23:17:30Z. Verbatim user input: Authorize. Interpreted scope from the immediately prior authorization request: WD-qthq editor host export on host 3090, using only its two existing hash-verified sources and one CPU-only FFmpeg editor_export job.

### 2026-09-29T23:22:09Z speed
Dispatch note: operator authorization is recorded, but host-3090 execution is queued behind the WD-bw0h one-attempt clean-machine H3 run to prevent overlapping host/workspace mutations. Do not interpret the wait as lost approval.

### 2026-09-30T14:50:42Z speed
## Authoritative Delivery Contract

Commit SHA: 284c7f16259cab5c85a017f06bad1f29934e04ed

## nd_contract
status: delivered

### evidence
- PR #218 head and exact-head CI run 36724918128 both resolve to 284c7f16259cab5c85a017f06bad1f29934e04ed.
- One authorized editor_export queue job completed on host 3090 with CPU-only FFmpeg and zero model downloads.
- Real output outputs/editor-export.mp4 has SHA-256 4f7c955ebbf68daa98eed4c117cb879db8dfc6744924d6f1e7ad1e1de8c8725e.
- Canonical checker passed with zero warnings; focused tests were 14/14; lint, release, protected parity, and diff gates passed.

### proof
- [x] AC #1: exact local reference and immutable source identities verified.
- [x] AC #2: authorization/input failures fail closed before SSH.
- [x] AC #3: authorized host preflight passed with zero model downloads.
- [x] AC #4: exactly one real governed editor_export queue job ran with CPU-only FFmpeg.
- [x] AC #5: real ordered video/audio artifact passed all eight objective gates.
- [x] AC #6: source/project immutability and complete provenance/queue/log evidence recorded.
- [x] AC #7: only the editor host-export row transitioned to evidence-backed host run.
- [x] AC #8: focused tests, exact-head full CI, lint, release, protected parity, checker, and diff gates passed.
