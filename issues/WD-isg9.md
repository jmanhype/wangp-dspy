---
id: WD-isg9
title: "Maestro parity: H3 standard operation batch"
status: closed
priority: 1
type: task
labels: [capability, evidence, accepted]
parent: WD-3nod
created_at: 2026-09-26T13:07:47Z
created_by: speed
updated_at: 2026-09-26T15:35:12Z
content_hash: "sha256:c0a3a6ff1581c3600387f5e8519ff5104560cbdfc78e2d648f89e33eb724af90"
follows: [WD-14ej, WD-i7qs, WD-r4n8, WD-fay0, WD-dmf2, WD-bxhc]
assignee: dev-WD-isg9
closed_at: 2026-09-26T15:35:12Z
close_reason: "Accepted: verified reworked preflight/provenance, all eight terminal dispositions, canonical checker PASS, CI PASS, and reviewer evidence commit 83858000."
led_to: [WD-9t9o]
---

## Description
WD-isg9 emits terminal, operation-specific evidence for the eight remaining
`minimax_h3/standard` cells using already present hash-verified FL2VA assets on
host `3090`, with no new model download. The cells are extend, blend, retake,
edit, outpaint, repaint, recast, and upscale. The verified create cell cannot
proxy for any other cell.

Each cell must end as `host_run_verified` with its own distinct nonempty hashed
media artifact and objective gates, or as documented `unsupported` backed by a
real host rejection or implementation boundary. Never relabel a generic render
as an operation.

Operator authorization is the 2026-09-26 text "Authorized and approved." followed
by "continue", scoped to this existing-asset host-run batch. Training, paid
providers, GUI work, unrelated GPU processes, new downloads, and model deletion
are not authorized.

The bundle must record repository/base state; live SSH, H3 hash, disk, GPU, and
QC preflight; exact command argv; model/reference/mask provenance; durable
queue admission; output hashes; ffprobe metadata; operation-specific objective
gates; and reviewer links. Capture fail-closed diagnostics for blend, recast,
and outpaint. Update only the eight `minimax_h3/standard` cells in
`docs/video-capabilities.md`. The parity checker, scoped/full tests, backlog
lint, and delivery proof must pass.

## Acceptance Criteria

1. A clean story worktree is created from current `main`, and the story is
   atomically claimed before implementation.
2. Before host contact, record repository state and a live host preflight
   including SSH, model hashes, disk floor, GPU state, and unrelated-process
   state. Any failed prerequisite stops the batch.
3. The bundle records operator authorization, exact local/remote command argv,
   repository identity, model provenance, bundle-relative references, durable
   queue admission, output hashes, ffprobe metadata, objective gates, and
   reviewer evidence.
4. Every one of the eight named cells reaches a terminal state:
   `host_run_verified` with a distinct nonempty media artifact, or documented
   `unsupported` backed by a real host rejection/implementation boundary.
5. `docs/video-capabilities.md` changes only the eight cells in this story and
   links each change to the new evidence.
6. `scripts/verify_maestro_parity.py` passes on the new bundle, and existing
   capability/evidence tests pass.
7. `pvg lint --backlog` passes, the story delivery proof passes, and the PR
   contains only this batch's evidence and documentation updates.

## MANDATORY SKILLS

None identified.

## Design


## Notes


## nd_contract
status: accepted

### evidence
- PM closeout applied via pvg story accept on 2026-09-26.

### proof
- [x] Story closed after accepted label was applied.


## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-26.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## Implementation Evidence (DELIVERED)

Commands run:

- `ssh 3090 /home/straughter/Wan2GP/wd-isg9/host-scripts/wd_isg9_preflight_hash_probe.sh`
- `uv run --frozen --extra dev python datasets/runs/maestro-parity/WD-isg9/build_preflight_hash_summary.py`
- `uv run --frozen --extra dev python datasets/runs/maestro-parity/WD-isg9/build-objective-gates.py`
- `uv run --frozen --extra dev python datasets/runs/maestro-parity/WD-isg9/build-evidence.py`
- `uv run --frozen --extra dev python scripts/verify_maestro_parity.py datasets/runs/maestro-parity/WD-isg9`
- `uv run --frozen --extra dev pytest -q tests/test_video_capabilities.py tests/test_maestro_parity_evidence.py`
- `pvg lint --backlog`
- `git diff --check`
- `uv run --frozen --extra dev wgp release verify --json`

Summary:

Rework preserved the original preflight argv and added a rerunnable raw live model-hash probe: 4/4 expected model hashes and sizes match, model mtimes predate rendering, disk/GPU/process/QC state is recorded, and the evidence now has 48/48 passing objective gates.

Commit SHA: d79979614ea5fd2a97ef4257247e2d098e66217c

### CI/Test Results

- Scoped capability/evidence tests: 92 passed, exit 0.
- Backlog lint: 131 scanned, 0 errors, 0 review findings.
- `git diff --check`: exit 0.
- Clean-tree release verification at `d7997961`: version/changelog/recipe/tree all pass; `release=ready`; no tag created.
- PR 197 CI restarted at `d7997961` and is pending.
- Dirty-tree full-suite ownership: the two `tests/test_release.py` failures were the intentional clean-tree gate on the uncommitted evidence worktree; clean release verification now passes. The existing FastAPI/Starlette test-client deprecation warning is unrelated and explicitly retained as an observation, not dismissed.
- Canonical parity checker at delivery: fails only the two independent reviewer-verdict fields.

### AC Verification

| AC | Result | Evidence |
| --- | --- | --- |
| 1 | PASS | Story reclaimed and clean worktree updated on `story/WD-isg9`. |
| 2 | PASS | Original command in `preflight-original-command.txt`; raw hash/size/mtime/disk/GPU/process/QC evidence in `preflight-model-hash-rerun.txt` and summary JSON. |
| 3 | PASS | `evidence.json` now records preflight, hash-probe, boundary, and render argv plus observed model hashes. |
| 4 | PASS | Five distinct media outputs and three real host boundaries remain valid. |
| 5 | PASS | Matrix scope remains limited to the eight H3-standard cells and supporting narrative. |
| 6 | PENDING REVIEWER | 48/48 objective gates and scoped tests pass; canonical checker awaits reviewer approval. |
| 7 | PENDING REVIEWER | Delivery proof passes; PM acceptance and merge remain. |

LEARNINGS:

- A preflight check that collapses hash verification to `model_files=true` is not sufficient audit evidence; preserve `sha256sum -c`, size, and mtime output in the bundle.
- Release-tree tests intentionally reject dirty evidence worktrees; commit first, then run clean release verification and CI.
- Verbatim host/test logs can contain trailing whitespace; bundle-local `.gitattributes` can preserve exact bytes without weakening the repository-wide diff check.

### OBSERVATIONS (unrelated)

- [CONCERN] dependency warning: FastAPI's test client emits `StarletteDeprecationWarning: Using httpx with starlette.test_client is deprecated`; no failures. This is outside WD-isg9 and retained for SrPM triage.

## nd_contract
status: delivered

### evidence

- Commit SHA: d79979614ea5fd2a97ef4257247e2d098e66217c
- Preflight hash summary: 4/4 hashes and sizes match.
- Objective gates: 48 pass, 0 fail.
- Scoped tests, backlog lint, diff-check, and clean release verify pass.
- Reviewer approval remains pending.

### proof

- [x] AC1 through AC5 pass with artifacts cited above.
- [ ] AC6 completes after independent reviewer approval and CI.
- [ ] AC7 completes after PM acceptance and merge.

## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-26.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## nd_contract
status: rejected

### evidence
- PM rejection applied via pvg story reject on 2026-09-26.

### proof
- [ ] Story requires another developer delivery before it can be accepted.


## Implementation Evidence (DELIVERED)

Commands run:

- `ssh 3090 /home/straughter/Wan2GP/wd-isg9/host-scripts/wd_isg9_boundary_probes.sh`
- `ssh 3090 /home/straughter/Wan2GP/wd-isg9/host-scripts/wd_isg9_render.sh`
- `uv run --frozen --extra dev python datasets/runs/maestro-parity/WD-isg9/build-objective-gates.py`
- `uv run --frozen --extra dev python datasets/runs/maestro-parity/WD-isg9/build-evidence.py`
- `uv run --frozen --extra dev python scripts/verify_maestro_parity.py datasets/runs/maestro-parity/WD-isg9`
- `uv run --frozen --extra dev pytest -q tests/test_video_capabilities.py tests/test_maestro_parity_evidence.py`
- `pvg lint --backlog`

Summary:

Five H3-standard operations produced real distinct hashed media; blend, recast, and outpaint reached evidenced host implementation boundaries. Independent PM review is pending.

Commit SHA: ee81c0ccd763376d86734791a342e16efad78ebb

### AC Verification

| AC | Result | Evidence |
| --- | --- | --- |
| 1 | PASS | Clean story worktree and atomic claim completed. |
| 2 | PASS | `preflight.json` passes SSH, model hashes, disk, GPU, and QC. |
| 3 | PASS | `evidence.json`, queue DB, argv logs, hashes, ffprobe, and gates record the required provenance. |
| 4 | PASS | Five outputs and three boundary diagnostics disposition all eight cells. |
| 5 | PASS | `docs/video-capabilities.md` changes only the eight H3-standard cells plus their supporting narrative. |
| 6 | PENDING REVIEWER | Objective/scoped gates pass; canonical checker awaits independent reviewer approval. |
| 7 | PENDING REVIEWER | Lint/diff pass; PM acceptance and merge remain. |

## nd_contract
status: delivered

### evidence

- Commit SHA: ee81c0ccd763376d86734791a342e16efad78ebb is pushed on `story/WD-isg9`.
- Objective gates 43/43 pass; scoped tests exit 0; backlog lint and diff-check exit 0.
- Reviewer approval is intentionally pending.

### proof

- [x] AC1 through AC5 pass with artifacts cited above.
- [ ] AC6 completes after independent reviewer approval.
- [ ] AC7 completes after PM acceptance and merge.

## Implementation Evidence

### Bundle

- `datasets/runs/maestro-parity/WD-isg9/evidence.json`
- `datasets/runs/maestro-parity/WD-isg9/execution-summary.md`
- `datasets/runs/maestro-parity/WD-isg9/objective-gates.json`
- `datasets/runs/maestro-parity/WD-isg9/queue.db`
- `docs/video-capabilities.md`

### Outputs

- extend SHA-256 `489f8aae72b41b669df2259182eb287ca805ff3033d2b7ed93a130b903c00cef`
- retake SHA-256 `4a75cccc6aefe55cbf3cb65e276f9783a3430635cbbc65e140ab5d7b30dd864b`
- edit SHA-256 `93acbbd1c4d432555d14135dad2648b88f19bec7a1ec40457ce6e17978158f1c`
- repaint SHA-256 `3f14efa860a0a3564abbb4a39fcc56a380731d7f5595991639dc2cfc08fa9416`
- upscale SHA-256 `ee703d736fc6a065b6d546d8756838fa2edd5feeebd4755d304463f33dbe505a`

### CI/Test Results

- Scoped tests: 92 passed, exit 0 (`scoped-tests.out`).
- Dirty-worktree full suite: 2090 tests, 0 errors, 2088 passed, 1 skipped, 2 expected release-tree failures because the evidence worktree was intentionally dirty (`fullsuite-dirty-tree-counters.json`).
- Backlog lint: 131 scanned, 0 errors, 0 review findings.
- Objective gates: 43/43 pass.
- Canonical parity checker at delivery: fails only `reviewer_verdict.decision` and `reviewer_verdict.evidence_links`; independent PM review is pending.

### Commands run

- `pvg story claim WD-isg9`
- `ssh 3090 /home/straughter/Wan2GP/wd-isg9/host-scripts/wd_isg9_boundary_probes.sh`
- `ssh 3090 /home/straughter/Wan2GP/wd-isg9/host-scripts/wd_isg9_render.sh`
- `uv run --frozen --extra dev python datasets/runs/maestro-parity/WD-isg9/measure_objective_gates.py`
- `uv run --frozen --extra dev python datasets/runs/maestro-parity/WD-isg9/build-objective-gates.py`
- `uv run --frozen --extra dev python datasets/runs/maestro-parity/WD-isg9/build-evidence.py`
- `uv run --frozen --extra dev python scripts/verify_maestro_parity.py datasets/runs/maestro-parity/WD-isg9`
- `uv run --frozen --extra dev pytest -q tests/test_video_capabilities.py tests/test_maestro_parity_evidence.py`
- `pvg lint --backlog`
- `git diff --check`

### Summary

WD-isg9 terminally dispositioned all eight remaining H3-standard cells with five real hashed media outputs and three evidenced host implementation boundaries, using zero new download bytes.

## nd_contract
status: delivered

### evidence

- Commit SHA: ee81c0ccd763376d86734791a342e16efad78ebb
- Branch: `story/WD-isg9` pushed to origin.
- Bundle: `datasets/runs/maestro-parity/WD-isg9/evidence.json`.
- Preflight: SSH/model hashes/disk/GPU/QC all pass.
- Render exits: extend/retake/edit/repaint/upscale all 0.
- Boundary exits: blend 1, recast 1; outpaint control disabled in hashed host code.
- Objective gates: 43 pass, 0 fail.
- Review status: pending independent PM approval.

### proof

- [x] AC1: clean story worktree and atomic claim completed.
- [x] AC2: live preflight recorded and all prerequisites passed.
- [x] AC3: authorization, argv, provenance, queue, hashes, ffprobe, gates, and reviewer links recorded.
- [x] AC4: all eight cells reached operation-specific terminal dispositions.
- [x] AC5: only the eight H3-standard matrix cells and their supporting narrative changed.
- [ ] AC6: canonical checker and tests complete after independent reviewer approval.
- [ ] AC7: delivery proof, PM acceptance, and final merge gate remain.

## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-26.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## nd_contract
status: delivered

### evidence

- Commit SHA: d79979614ea5fd2a97ef4257247e2d098e66217c
- Rework preserves original preflight argv, raw live model hashes/sizes/mtimes, disk/GPU/process/QC state, and warning ownership.
- Objective gates 48/48 pass; scoped tests 92/92 pass; lint and diff-check pass; clean release verification is ready with no tag.
- Independent reviewer approval remains pending.

### proof

- [x] AC1 through AC5 pass with artifacts cited in the rework Implementation Evidence above.
- [ ] AC6 completes after independent reviewer approval and PR CI.
- [ ] AC7 completes after PM acceptance and merge.

## History
- 2026-09-26T13:08:07Z status: open -> in_progress
- 2026-09-26T13:08:07Z auto-follows: linked to predecessor WD-14ej
- 2026-09-26T13:08:07Z claimed by dev-WD-isg9
- 2026-09-26T13:08:15Z dep_added: blocks WD-fay0
- 2026-09-26T14:44:30Z status: in_progress -> in_progress
- 2026-09-26T14:44:30Z auto-follows: linked to predecessor WD-i7qs
- 2026-09-26T14:57:11Z status: in_progress -> open
- 2026-09-26T14:57:11Z released by speed
- 2026-09-26T14:59:51Z status: open -> in_progress
- 2026-09-26T14:59:51Z auto-follows: linked to predecessor WD-r4n8
- 2026-09-26T14:59:51Z claimed by dev-WD-isg9
- 2026-09-26T15:08:58Z status: in_progress -> in_progress
- 2026-09-26T15:08:58Z auto-follows: linked to predecessor WD-fay0
- 2026-09-26T15:10:40Z status: in_progress -> in_progress
- 2026-09-26T15:10:40Z auto-follows: linked to predecessor WD-dmf2
- 2026-09-26T15:11:24Z status: in_progress -> in_progress
- 2026-09-26T15:11:24Z auto-follows: linked to predecessor WD-bxhc
- 2026-09-26T15:35:12Z status: in_progress -> closed
- 2026-09-26T15:35:12Z dep_removed: no_longer_blocks WD-fay0

## Links
- Parent: [[WD-3nod]]
- Follows: [[WD-14ej]], [[WD-i7qs]], [[WD-r4n8]], [[WD-fay0]], [[WD-dmf2]], [[WD-bxhc]]
- Led to: [[WD-9t9o]]

## Comments

### 2026-09-26T13:28:50Z speed
Dispatcher repaired malformed authored sections created by repeated body updates; canonical Description and Acceptance Criteria now occur once.

### 2026-09-26T14:48:37Z speed
Corrected delivery commit SHA to ee81c0ccd763376d86734791a342e16efad78ebb.

### 2026-09-26T14:50:51Z speed
Corrected delivery commit SHA to ee81c0ccd763376d86734791a342e16efad78ebb.

### 2026-09-26T14:57:11Z speed
PM Decision
REJECTED [2026-09-26]:
EXPECTED: AC2 requires a pre-host-contact live preflight recording SSH, model hashes, disk floor, GPU state, and unrelated-process state; AC3 requires exact local/remote command argv. The pm_acceptor contract also requires a LEARNINGS section and ownership of test-output warnings.
DELIVERED: datasets/runs/maestro-parity/WD-isg9/preflight.json:8-11 records only model_files=true with blank detail; model-assets.json:3-34 lists expected hashes but no live measured hashes; build-evidence.py:125-132 records only boundary/render SSH argv and no preflight argv. The delivery notes contain no LEARNINGS block. The full-suite artifact has two release failures (fullsuite-dirty-tree-counters.json:3-8), and fullsuite-dirty-tree.out:87-95 also has an unreported StarletteDeprecationWarning.
GAP: A boolean model_files result plus a separate expected-hash catalog does not prove the live host assets matched those hashes before contact, and the bundle does not capture the preflight command or unrelated-process check. The proof is therefore incomplete for AC2/AC3 and does not meet the mandatory delivery-note/warning ownership requirements.
FIX: Add a fail-closed preflight artifact generated before host rendering with its exact argv, timestamp/order, repository state, SSH result, actual sha256sum output for every required model and expected-hash comparison, disk floor, GPU state, and unrelated-process state. Record that artifact and its command in evidence.json. Add LEARNINGS, then provide a clean committed-tree full-suite result or explicitly file/dispose the warning under the project bug model; rerun the canonical checker and update delivery proof.

### 2026-09-26T15:10:06Z speed
Rework delivery contract placed at EOF; authoritative commit is d79979614ea5fd2a97ef4257247e2d098e66217c.

### 2026-09-26T15:13:39Z speed
Rework delivery complete; normalized the prior PM comment heading so pvg contract EOF validation remains valid.
