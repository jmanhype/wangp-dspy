---
id: WD-he8i
title: "Maestro parity current index reconciliation"
status: in_progress
priority: 1
type: task
labels: [evidence, index, qc]
parent: WD-3nod
created_at: 2026-09-30T15:33:52Z
created_by: speed
updated_at: 2026-09-30T15:34:39Z
content_hash: "sha256:d235a964a6df3078547b9aefcabc21691186686fafcb68d976afb88314acc57d"
blocks: [WD-t0il, WD-fay0]
assignee: dev-WD-he8i
follows: [WD-qthq]
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


## History
- 2026-09-30T15:33:53Z dep_added: blocks WD-t0il
- 2026-09-30T15:34:08Z dep_added: blocks WD-fay0
- 2026-09-30T15:34:39Z status: open -> in_progress
- 2026-09-30T15:34:39Z auto-follows: linked to predecessor WD-qthq
- 2026-09-30T15:34:39Z claimed by dev-WD-he8i

## Links
- Parent: [[WD-3nod]]
- Blocks: [[WD-t0il]], [[WD-fay0]]
- Follows: [[WD-qthq]]

## Comments
