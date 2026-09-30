---
id: WD-he8i
title: "Maestro parity current index reconciliation"
status: closed
priority: 1
type: task
labels: [evidence, index, qc, delivered, accepted]
parent: WD-3nod
created_at: 2026-09-30T15:33:52Z
created_by: speed
updated_at: 2026-09-30T17:13:38Z
content_hash: "sha256:c9822ea25807483136e5221535ab809f33557a39fcf13f75ff2e3b99fabbf94e"
assignee: dev-WD-he8i
follows: [WD-qthq, WD-23rs]
closed_at: 2026-09-30T17:13:37Z
close_reason: "Accepted: exact head ec9abf4a38afa5249acffeaac2d639353fbfc864 has passing CI, exact 208-row matrix parity and boundary preservation, focused validator/test coverage, and clean standing gates."
---

## Description
## Context

At merged main `5a94eb491c524816334e23e1b2894acc3b772819`, the authoritative capability matrices and the accepted WD-qthq editor bundle have advanced, but the consolidated parity index remains the historical WD-fay0 snapshot from base `82f6c38570a818dd8dbd3e70baebd037459661b3`.

Current authoritative matrix census is 208 cells:

- 89 `host_run_verified`
- 7 `dependency_blocked`
- 110 terminal unsupported/fail-closed variants
- 2 not applicable
- 0 `planned`

The current stale index still claims 120 planned matrix cells and lists `docs/editor.md` Authorized host export/media as planned. Its own validator fails:

```text
FAIL: index rows diverge from source capability matrices
```

This creates a completion-audit hazard: an operator following `datasets/runs/maestro-parity/WD-fay0/evidence-index.md` would incorrectly believe the accepted and merged WD-qthq editor host run is still missing.

## USER INTENT

Observable outcome: running the consolidated index validator at merged main returns PASS, and the rendered index accurately tells the operator that only seven LTX dependency cells and the separately gated first-run generated artifact remain incomplete.

## OUT OF SCOPE

- Any SSH or host-3090 contact.
- Model downloads, storage moves, renders, queue admission, or generation.
- WD-bw0h or WD-28ac boundary changes.
- Modifying accepted media, native logs, provenance bytes, capability bundles, or protected engine files.
- New capability claims or GUI work.

## DIFF BUDGET

About 4 files and under 500 authored/evidence changed LOC.

## Boundary Map
PRODUCES:
- datasets/runs/maestro-parity/WD-fay0/evidence-index.json -> current consolidated row/cell inventory at merged main, preserving lane bundle provenance and recording exact remaining boundaries
- datasets/runs/maestro-parity/WD-fay0/evidence-index.md -> human-readable current index matching the JSON inventory
- datasets/runs/maestro-parity/WD-fay0/validate_index.py -> deterministic validator that fails on matrix/index drift, stale editor state, missing bundle hashes, or wrong remaining-scope totals
- tests/test_current_parity_index.py -> regression coverage proving current matrix/index agreement and editor/first-run dispositions

CONSUMES:
- (existing): docs/*capabilities.md -> authoritative 208-cell capability matrices
  source: parse exact source line, row identity, cell, documented state, and evidence/boundary link; do not invent or inherit adjacent-cell evidence.
- WD-qthq: datasets/runs/maestro-parity/editor-host-export/host-run/evidence.json -> accepted editor host-run bundle
  source: canonical operator authorization, queue job, output hash/metadata, objective gates, and reviewer verdict.
- WD-23rs: datasets/runs/maestro-parity/checker-lane-receipts/evidence.json -> current canonical checker receipt
  source: exact representative lane outcomes and warning ownership.
- WD-bw0h: datasets/runs/maestro-parity/clean-generated/failed-retry/boundary.md -> current first-run storage boundary
  source: first-run remains incomplete; no generated artifact claim is permitted.
- WD-28ac: datasets/runs/maestro-parity/ltx-dependency-terminalization/preflight-boundary.json -> exact seven-cell storage boundary
  source: all seven cells remain dependency_blocked; no operation verdict is inherited.

## Story Acceptance Criteria
1. [State] The consolidated JSON and Markdown indexes are regenerated against merged main `5a94eb491c524816334e23e1b2894acc3b772819` and exactly match all 208 authoritative matrix cells by document, source line, row, cell, documented state, and evidence/boundary link.
2. [State] The matrix inventory records zero `planned` cells, exactly seven `dependency_blocked` cells, exactly 89 `host_run_verified` cells, and the correct terminal unsupported/fail-closed and not-applicable totals.
3. [State] The non-matrix editor inventory marks Authorized host export/media as host-run verified and links the accepted WD-qthq bundle; the first-run generated row remains incomplete and links the WD-bw0h storage boundary.
4. [State] The index records the current remaining boundaries without converting WD-bw0h or WD-28ac into hardware verdicts and without claiming either blocked batch complete.
5. [State] Existing accepted evidence bundle bytes and hashes remain unchanged; only index/navigation metadata and validation coverage change.
6. [State] `python3 datasets/runs/maestro-parity/WD-fay0/validate_index.py` exits 0 at merged main and fails on a deliberate matrix/index drift fixture.
7. [State] Focused index tests, the undeselected full suite, `pvg lint --backlog`, `wgp release verify` with `release=ready` and `tag_created=false`, protected-file parity, `git diff --check`, and exact-head CI pass.

## Testing Requirements
- Integration tests are mandatory and must use the real repository documents and bundles; no mocks of document parsing, hashing, checker behavior, or index validation.
- Add negative coverage for matrix drift, stale editor planned state, wrong remaining LTX count, and a missing verified evidence link.
- Run the consolidated validator, focused tests, undeselected full suite with parsed JUnit, backlog lint, release verification, protected parity, diff check, and exact-head CI.

## Delivery Requirements
- Record exact commands, commit SHA, PR, CI, parsed JUnit counters, index totals, bundle hashes, and AC table.
- Include `LEARNINGS:`.
- This is a local evidence-navigation repair only; no host/model action is authorized.

## MANDATORY SKILLS
- pvg
- tool-systematic-debugging

## nd_contract
status: new

### evidence
- Current audit at main `5a94eb49`: consolidated validator fails because the historical index diverges from authoritative matrices.
- Merged docs contain zero planned matrix cells, seven dependency_blocked cells, and an accepted WD-qthq editor host-run bundle.
- Historical WD-fay0 index still reports 120 planned cells and editor host export planned.

### proof
- [ ] Pending regenerated current index, validator, tests, exact-head CI, and standing gates.

## Acceptance Criteria


## Design


## Notes
## Implementation Evidence
Commands run:
- `python3 datasets/runs/maestro-parity/WD-fay0/validate_index.py` => PASS: 208 rows; 89 host_run_verified; 7 dependency_blocked; 110 terminal unsupported/fail-closed; 2 not_applicable; 39 evidence files hash-verified.
- `uv run --frozen --extra dev pytest -q tests/test_current_parity_index.py --junitxml=/tmp/WD-he8i-focused-clean.junit.xml` => PASS: tests=9 failures=0 errors=0 skipped=0.
- `uv run --frozen --extra dev pytest -q -ra --junitxml=/tmp/WD-he8i-full-clean.junit.xml` => PASS: tests=2147 failures=0 errors=0 skipped=1 (pre-existing WANGP_3090 gate; no host contact).
- `pvg verify <4 changed paths> --format=text --include-tests` => PASS, 0 issues.
- `pvg lint --backlog` => PASS, 154 scanned, 0 errors, 0 review findings.
- `uv run --frozen --extra dev wgp release verify --json` => PASS, release=ready, tag_created=false.
- `git diff --exit-code 5a94eb491c524816334e23e1b2894acc3b772819 -- <5 protected engine files>` => PASS exit 0.
- `git diff --check` => PASS exit 0.
- Focused validator/test coverage command => validator+new-test coverage 78% (266 statements, 58 missed); full-project coverage is not claimed.
Summary:
The current consolidated JSON/Markdown index now exactly binds the authoritative 208-cell matrix and 39 linked evidence files. WD-qthq editor Authorized host export/media is host-run verified, WD-bw0h first-run generated media remains incomplete, and exactly seven WD-28ac LTX cells remain dependency-blocked. Deterministic drift tests, the undeselected full suite, local standing gates, protected/evidence byte parity, and exact-head CI all pass. No host/model/storage/render/queue action or new capability claim occurred.
SHA:
`ec9abf4a38afa5249acffeaac2d639353fbfc864` on `story/WD-he8i`; PR https://github.com/jmanhype/wangp-dspy/pull/219; exact-head CI attempt 2 SUCCESS https://github.com/jmanhype/wangp-dspy/actions/runs/36742380020.

The full command list, parsed JUnit, hashes, PR/CI details, boundary identities, AC table, observations, and initial transient timeout/dirty-tree explanations are in the preceding detailed evidence block.

LEARNINGS:
- Deterministic delivery-note checks require exact heading/prefix shapes (`## Implementation Evidence`, `Commands run:`, `Summary:`, `SHA:`) and an authoritative final contract; this append repairs that shape without changing code or artifacts.

## nd_contract
status: delivered

### evidence
- Commit `ec9abf4a38afa5249acffeaac2d639353fbfc864`; PR 219; exact-head CI attempt 2 success.
- Validator PASS; focused 9/9; full suite 2147 tests, 0 failures, 0 errors, 1 pre-existing host-gated skip.
- pvg verify, pvg lint, release, protected parity, evidence-byte parity, whitespace, and exact-head CI pass.

### proof
- [x] AC #1: exact 208-cell current matrix/index agreement.
- [x] AC #2: 89/7/110/2 totals and zero planned.
- [x] AC #3: WD-qthq editor verified; WD-bw0h first-run incomplete.
- [x] AC #4: exact seven-cell WD-28ac boundary preserved without hardware/complete verdicts.
- [x] AC #5: accepted evidence bytes unchanged.
- [x] AC #6: current validator passes and drift fixtures fail.
- [x] AC #7: focused/full/local gates and exact-head CI pass.

## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-30.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## Implementation Evidence (DELIVERED)

PROOF:

### CI/Test Results
- Commands run:
  - `python3 datasets/runs/maestro-parity/WD-fay0/validate_index.py`
  - `uv run --frozen --extra dev pytest -q tests/test_current_parity_index.py --junitxml=/tmp/WD-he8i-focused-clean.junit.xml`
  - `uv run --frozen --extra dev pytest -q -ra --junitxml=/tmp/WD-he8i-full-clean.junit.xml`
  - `uv run --frozen --extra dev python -m compileall -q datasets/runs/maestro-parity/WD-fay0/validate_index.py tests/test_current_parity_index.py`
  - `uv run --frozen --extra dev --with pytest-cov pytest -q tests/test_current_parity_index.py --cov=. --cov-report=` followed by `coverage report --include='datasets/runs/maestro-parity/WD-fay0/validate_index.py,tests/test_current_parity_index.py'`
  - `pvg verify datasets/runs/maestro-parity/WD-fay0/evidence-index.json datasets/runs/maestro-parity/WD-fay0/evidence-index.md datasets/runs/maestro-parity/WD-fay0/validate_index.py tests/test_current_parity_index.py --format=text --include-tests`
  - `pvg lint --backlog`
  - `uv run --frozen --extra dev wgp release verify --json`
  - `git diff --exit-code 5a94eb491c524816334e23e1b2894acc3b772819 -- services/jobs/queue.py services/director/renderers/policy.py services/director/wiring.py services/jobs/preflight.py scripts/run_film.py`
  - `git diff --check`
- Summary: validator PASS; focused tests 9/9 PASS; undeselected full suite PASS; compileall PASS; pvg verify PASS; backlog lint PASS; release PASS; protected parity PASS; whitespace PASS; exact-head CI PASS.
- Consolidated validator output: `{"hashed_matrix_evidence_files":39,"ltx_dependency_cells":7,"matrix_rows":208,"matrix_totals":{"dependency_blocked":7,"host_run_verified":89,"not_applicable":2,"terminal_unsupported_or_fail_closed":110},"non_matrix_rows":3,"result":"PASS"}`
- Focused JUnit: tests=9, failures=0, errors=0, skipped=0, time=0.109s.
- Full JUnit: tests=2147, failures=0, errors=0, skipped=1, time=788.883s. The sole skip is the pre-existing live-host gate `tests/test_jobs_integration_3090.py:20` requiring `WANGP_3090=1`; no SSH/host contact occurred.
- Coverage (validator plus new focused test only): 266 statements, 58 missed, 78%. This is focused coverage, not a full-project coverage claim.
- pvg verify: `VERIFY: PASSED (2 files scanned, 0 issues)`.
- pvg lint: `scanned 154 issues; 0 errors, 0 review findings`.
- Release: version 0.1.0; version/changelog/recipe_schema/tree checks all pass; `release=ready`; `tag_created=false`.
- Protected parity: exit 0 against base `5a94eb491c524816334e23e1b2894acc3b772819`.
- Matrix evidence-byte parity: `git diff --exit-code 5a94eb491c524816334e23e1b2894acc3b772819 -- <39 manifest paths>` exited 0 with no changed paths.
- Exact changed paths: `datasets/runs/maestro-parity/WD-fay0/evidence-index.json`, `datasets/runs/maestro-parity/WD-fay0/evidence-index.md`, `datasets/runs/maestro-parity/WD-fay0/validate_index.py`, and `tests/test_current_parity_index.py`.

### Commit / PR / CI
- Branch: `story/WD-he8i`
- SHA: `ec9abf4a38afa5249acffeaac2d639353fbfc864`
- Commit: `fix(WD-he8i): reconcile current parity index`
- PR: https://github.com/jmanhype/wangp-dspy/pull/219
- PR state/merge status at delivery: OPEN / CLEAN; PR head is exactly `ec9abf4a38afa5249acffeaac2d639353fbfc864`.
- Exact-head CI attempt 2: SUCCESS in 18m53s; all checkout/setup/ffmpeg/test/build/post steps passed. Run: https://github.com/jmanhype/wangp-dspy/actions/runs/36742380020 (job https://github.com/jmanhype/wangp-dspy/actions/runs/36742380020/job/109992851722)
- CI attempt 1 was canceled by the repository's 30-minute job timeout while pytest was still progressing at 80%, with no assertion/test failure in the log. Same-head attempt 2 passed. No workflow or code change was made for that transient runner timing variance.

### Hashes and boundary identities
- Matrix identity SHA-256: `137529223a941dd8a95bebbcb37acf2b149b5cfa3513afed0b6a81bdb01489a2`.
- WD-qthq editor evidence SHA-256: `7a292c0befd1bbbe59db3f9d0f8879f1ed17e3141f9ff07a06126803353b7d17`.
- WD-23rs checker receipt SHA-256: `2d935d24db35116c9acf7677943d93204cd79826276a3390141cadb667f3c3c4`.
- WD-bw0h first-run boundary ref/hash: `story/WD-bw0h@2dfe36863e29eef02af0ea330d13d331bafdc00e`; SHA-256 `b78f5936a227782e4c3b7866e041cd9bbcc3d60d7ed4b9ebe5418e14e3d78d5f`.
- WD-28ac LTX boundary ref/hash: `story/WD-28ac@fced67e1293dc2dbbdf3f29c8b615f6357012ab6`; SHA-256 `6c881c9df3cd2a5d4ce85ee8fe5327e6631ac77cf2a2ca88c3b4579be4f05d53`.
- Generated current index JSON SHA-256: `6e68a58af209805fba08554fff8dfeadb23f111fa2138c960a285843d907e8c7`.
- Generated current index Markdown SHA-256: `71fe3d27b070ae22d243b9bf85745dc66f8e9387fdb471c5de36ae06a149308a`.
- Validator SHA-256: `bcc1882d648eb2bf78576deed82bb61b2d8469a65744f46b8fa25a39024828ba`.
- New focused test SHA-256: `1a88401cccd2dd8b7377b2f22279a571ea31cf4b618c33f7a238941efc0daa69`.

### AC Verification
| AC # | Requirement | Code Location | Test Location | Status |
|---|---|---|---|---|
| 1 | JSON/Markdown exactly match all 208 authoritative document/line/row/cell/state/link cells | `evidence-index.json`; `validate_index.py:127-209` | `tests/test_current_parity_index.py:43-63` | PASS |
| 2 | Totals are 89 verified, 7 dependency-blocked, 110 terminal variants, 2 N/A, zero planned | `validate_index.py:26-49,211-235` | `tests/test_current_parity_index.py:43-63` | PASS |
| 3 | Editor host export/media is WD-qthq host-run verified; first-run generated remains incomplete | `validate_index.py:51-109,238-260`; `evidence-index.json` | `tests/test_current_parity_index.py:87-114` | PASS |
| 4 | Current WD-bw0h and exact seven-cell WD-28ac boundaries remain non-hardware, non-complete boundaries | `validate_index.py:51-109,237-244` | `tests/test_current_parity_index.py:65-114` | PASS |
| 5 | Accepted evidence bytes/hashes remain unchanged; only index/navigation metadata and validation coverage change | `evidence-index.json` 39-file manifest; delivery byte-parity command above | `tests/test_current_parity_index.py:116-125` | PASS |
| 6 | Validator passes current tree and fails matrix/index drift | `validate_index.py:192-308,398-416` | `tests/test_current_parity_index.py:127-195` | PASS |
| 7 | Focused/full/lint/release/protected/diff/CI gates pass at exact head | Commands and results above | Full suite, PR CI, and local gate receipts above | PASS |

### Boundary honored
- No SSH/host-3090 contact, model download, storage mutation, render, queue admission, protected-engine edit, WD-bw0h/WD-28ac evidence mutation, or new capability claim occurred.
- No acceptance, close, or merge occurred.

### OBSERVATIONS (unrelated)
- `pvg notes search` initially reported configured vault `Claude` unavailable (`Available: Obsidian Vault, Brand OS (AI Video Factory), vault, .vault, nd-vault`). Story context came from the live tracker and repository evidence; no global vault configuration was changed.
- The first full-suite invocation had two release tests fail only because the four implementation files were intentionally uncommitted; after commit-first discipline, the clean-tree full suite passed. An initial path-valued `pytest --cov` invocation produced module-not-imported/no-data warnings and was corrected to `--cov=.` plus include filtering; the final coverage run produced 78% with no warnings.

LEARNINGS:
- The stale index was not just a count problem: evidence-link equality, a fixed matrix identity hash, and byte manifests are needed so coordinated or silent document/index drift fails closed.
- The two active operator boundaries live on distinct story refs rather than merged main; recording exact ref/path/hash identities preserves their bytes without copying or mutating their bundles.
- Release-aware tests require commit-first execution on this repository; a clean full-suite rerun is necessary after a scoped evidence commit.
- GitHub CI can exceed its 30-minute timeout solely from runner variance. The failed attempt log reached 80% with no error; same-head rerun passed in 18m53s.

## nd_contract
status: delivered

### evidence
- Commit `ec9abf4a38afa5249acffeaac2d639353fbfc864`; PR 219; exact-head CI attempt 2 success.
- Validator PASS over 208 rows and required totals; focused 9/9; full JUnit 2147/0/0 with one pre-existing host-gated skip.
- pvg verify, pvg lint, release, protected parity, matrix evidence-byte parity, whitespace, and exact-head CI all pass.

### proof
- [x] AC #1: current 208-cell matrix/index identity, source lines, rows, cells, states, and links match exactly.
- [x] AC #2: current counts are 89/7/110/2 with zero planned.
- [x] AC #3: WD-qthq editor host run is verified; WD-bw0h first-run generated remains incomplete.
- [x] AC #4: WD-bw0h and exactly seven WD-28ac LTX cells remain explicit boundaries, not hardware/complete verdicts.
- [x] AC #5: accepted matrix evidence bytes remain unchanged.
- [x] AC #6: validator passes current tree and negative drift fixtures fail.
- [x] AC #7: focused/full/local standing gates and exact-head CI pass.

## nd_contract
status: in_progress

### evidence
- Claim verified via live tracker: WD-he8i assigned to dev-WD-he8i at required base 5a94eb491c524816334e23e1b2894acc3b772819.
- Reproduced stale validator: python3 datasets/runs/maestro-parity/WD-fay0/validate_index.py => exit 1, index rows diverge from source capability matrices.
- Root cause: historical index maps 208 current cells to 120 planned/46 verified, while authoritative docs parse to 89 host_run_verified, 7 dependency_blocked, 110 terminal variants, and 2 not-applicable; old validator omits evidence-link comparison and current non-matrix boundary validation.

### proof
- [ ] Pending regenerated index, deterministic validator, negative/real tests, full gates, commit/PR/exact-head CI.

## History
- 2026-09-30T15:33:53Z dep_added: blocks WD-t0il
- 2026-09-30T15:34:08Z dep_added: blocks WD-fay0
- 2026-09-30T15:34:39Z status: open -> in_progress
- 2026-09-30T15:34:39Z auto-follows: linked to predecessor WD-qthq
- 2026-09-30T15:34:39Z claimed by dev-WD-he8i
- 2026-09-30T17:05:54Z status: in_progress -> in_progress
- 2026-09-30T17:05:54Z auto-follows: linked to predecessor WD-23rs
- 2026-09-30T17:13:37Z status: in_progress -> closed
- 2026-09-30T17:13:38Z dep_removed: no_longer_blocks WD-t0il
- 2026-09-30T17:13:38Z dep_removed: no_longer_blocks WD-fay0

## Links
- Parent: [[WD-3nod]]
- Follows: [[WD-qthq]], [[WD-23rs]]

## Comments

### 2026-09-30T17:08:41Z speed
DELIVERED CONTRACT REPAIR (append-only): SHA: ec9abf4a38afa5249acffeaac2d639353fbfc864; branch story/WD-he8i; PR https://github.com/jmanhype/wangp-dspy/pull/219; exact-head CI attempt 2 success https://github.com/jmanhype/wangp-dspy/actions/runs/36742380020.

## nd_contract
status: delivered

### evidence
- Commit ec9abf4a38afa5249acffeaac2d639353fbfc864; validator PASS 208 rows 89/7/110/2; focused 9/9; full JUnit tests=2147 failures=0 errors=0 skipped=1; pvg verify/lint/release/protected/evidence-byte/whitespace gates pass; PR CI success.

### proof
- [x] AC #1 exact current 208-cell matrix/index agreement.
- [x] AC #2 totals 89 host_run_verified, 7 dependency_blocked, 110 terminal, 2 not_applicable, zero planned.
- [x] AC #3 WD-qthq editor verified and WD-bw0h first-run incomplete.
- [x] AC #4 exactly seven WD-28ac LTX boundary cells remain non-hardware/non-complete.
- [x] AC #5 accepted evidence bytes unchanged.
- [x] AC #6 current validator passes and negative drift fixtures fail.
- [x] AC #7 focused/full/local standing gates and exact-head CI pass.
