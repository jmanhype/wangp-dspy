---
id: WD-43tj
title: "Maestro parity: TaoMate host boundary"
status: closed
priority: 1
type: task
labels: [capability, evidence, accepted]
parent: WD-3nod
created_at: 2026-09-26T18:42:51Z
created_by: speed
updated_at: 2026-09-26T19:18:11Z
content_hash: "sha256:28b7547ce3aa6bb0640e60cebe9b049984f73f1c5625b4d856dc528b92c341e1"
assignee: dev-WD-43tj
follows: [WD-9ymi, WD-f0vk]
closed_at: 2026-09-26T19:18:10Z
close_reason: "Accepted: verified live TaoMate boundary evidence, planner-only match classification, hashes, docs scope, delivery proof, CI, and clean release readiness."
---

## Description
WD-TAOMATE terminally dispositions all nine `minimax_h3/taomate_three_step` cells without a GPU render or model download. TaoMate is a named WanGP/Maestro preset, not a generic three-inference-step prompt; a generic H3 render cannot proxy for it.

Each cell must become `unsupported` only from live read-only host search evidence showing no TaoMate implementation, handler, preset, model identity, or settings path in the checked-out Wan2GP and Maestro trees. The story must preserve the existing accepted WD-2gyw search evidence, add current command/hash evidence, and update only the nine TaoMate cells in `docs/video-capabilities.md`.

Operator authorization is the 2026-09-26 text "Authorized and approved." followed by "continue", scoped to read-only host inventory. No GPU, inference, download, training, host mutation, paid provider, or accepted-artifact mutation is authorized.

## Acceptance Criteria
- [ ] A live read-only search of the checked-out Wan2GP and Maestro trees finds zero TaoMate implementation, handler, preset, settings, or model-identity matches and records the exact command, exit status, timestamp, and host.
- [ ] The boundary record preserves and cites the accepted WD-2gyw TaoMate search evidence without mutating it.
- [ ] All nine `minimax_h3/taomate_three_step` cells become `unsupported` with links to the new boundary evidence; no generic H3 render is relabelled.
- [ ] `docs/video-capabilities.md` changes only the TaoMate row and the supporting disposition narrative.
- [ ] Scoped capability/evidence tests, `pvg lint --backlog`, `git diff --check`, and clean release verification pass.
- [ ] Delivery evidence records that no GPU, inference, download, training, host mutation, paid provider, or accepted-artifact mutation occurred.

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


## PM Decision
ACCEPTED [2026-09-26]: Evidence reviewed and meets the boundary-only bar.

## nd_contract
status: accepted

### evidence
- Verified live host-search evidence, nested planner-only match classification, current and prior evidence hashes, nine-cell docs dispositions, and docs-only scope.
- Verified delivery proof 9/9; scoped-test output has 110 passing dots and exit 0; lint artifact has 0 errors; git diff --check is clean.
- Independently reran offline clean release verification at f19fa500697712f72edac09d54eb0d5b5daa3a34: all 4 checks pass, release=true, no tag.
- PR 200 test check passed at head f19fa500 in 21m20s.

### proof
- [x] AC1 through AC6 verified from artifacts, independent hash/release checks, and CI evidence.

## Implementation Evidence

Commands run:

- `ssh 3090 /tmp/wd_43tj_boundary_probe.sh`
- `shasum -a 256 datasets/runs/maestro-parity/WD-43tj/taomate-live-boundary.txt datasets/runs/maestro-parity/WD-43tj/taomate-boundary.md datasets/runs/maestro-parity/WD-43tj/boundary-evidence.json datasets/runs/maestro-parity/WD-2gyw/taomate-search-evidence.md`
- `uv run --frozen --extra dev pytest -q tests/test_video_capabilities.py tests/test_maestro_parity_evidence.py`
- `pvg lint --backlog`
- `git diff --check`
- `uv run --frozen --extra dev wgp release verify --json`

Summary:

WD-43tj records a live host implementation boundary for all nine TaoMate cells. Active host implementation surfaces and Maestro contain zero TaoMate matches; the only broad-tree matches are the typed planner enum in a nested Wangp repository copy, which is hashed and excluded as non-runtime context.

Commit SHA: f19fa500697712f72edac09d54eb0d5b5daa3a34

### CI/Test Results

- Scoped capability/evidence tests: 110 passed, exit 0.
- Backlog lint: 135 scanned, 0 errors, 0 review-blocking errors; one nonblocking vertical-slice review note for a boundary-only story.
- `git diff --check`: exit 0.
- Clean release verification at `f19fa500`: all four checks pass; `release=ready`; no tag created.
- PR CI is pending.

### AC Verification

| AC | Result | Evidence |
| --- | --- | --- |
| 1 | PASS | `taomate-live-boundary.txt` records timestamp, host, exact search, host exit 1, filename exit 0, and tree identities. |
| 2 | PASS | `boundary-evidence.json` cites accepted WD-2gyw evidence and records its hash in `evidence-hashes.txt`. |
| 3 | PASS | All nine TaoMate matrix cells are unsupported and link to `taomate-boundary.md`. |
| 4 | PASS | `docs/video-capabilities.md` changes only the TaoMate row and supporting narrative. |
| 5 | PASS | Scoped tests, lint, diff-check, and clean release verification pass. |
| 6 | PASS | Boundary evidence records zero downloads and no GPU/inference/host mutation. |

LEARNINGS:

- Broad host-tree searches can hit nested Wangp repository copies; implementation-boundary searches must target active runtime surfaces and explicitly classify downstream planner-only matches.
- A named preset cannot be inferred from a prompt that merely describes its mechanics.

## nd_contract
status: delivered

### evidence

- Commit SHA: f19fa500697712f72edac09d54eb0d5b5daa3a34
- Live host implementation search exit 1 with zero runtime matches.
- Filename search match count zero.
- Nested planner-only context match SHA-256 `3111b78ad110493a9ba8d5c26ed1fdee0a8183f432cedd37be986495cd65d04b`.
- Scoped tests 110/110; lint 0 errors; diff-check clean; clean release ready.

### proof

- [x] AC1 through AC6 pass with artifacts cited above.

## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-26.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## History
- 2026-09-26T18:43:28Z dep_added: blocks WD-fay0
- 2026-09-26T18:43:33Z status: open -> in_progress
- 2026-09-26T18:43:33Z auto-follows: linked to predecessor WD-9ymi
- 2026-09-26T18:43:33Z claimed by dev-WD-43tj
- 2026-09-26T18:48:46Z status: in_progress -> in_progress
- 2026-09-26T18:48:46Z auto-follows: linked to predecessor WD-f0vk
- 2026-09-26T19:18:11Z status: in_progress -> closed
- 2026-09-26T19:18:11Z dep_removed: no_longer_blocks WD-fay0

## Links
- Parent: [[WD-3nod]]
- Follows: [[WD-9ymi]], [[WD-f0vk]]

## Comments
