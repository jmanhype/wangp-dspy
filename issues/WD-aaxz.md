---
id: WD-aaxz
title: "Fix stale 'planned' claim in the video capability matrix preamble"
status: in_progress
priority: 3
type: bug
labels: [parity, docs]
parent: WD-3nod
created_at: 2026-10-05T05:41:51Z
created_by: speed
updated_at: 2026-10-05T05:42:03Z
content_hash: "sha256:366f4f4ee1f5f956db03c0aaaa226d96c2a1525d298535390f5700a2550cf7d8"
assignee: dev-WD-aaxz
follows: [WD-cuzw]
---

## Description
## Description

`docs/video-capabilities.md` opens its "Capability matrix" section with the sentence
"Every family/operation row is `planned`." That sentence contradicts the 99-cell table
immediately beneath it and the merged parity evidence index
(`datasets/runs/maestro-parity/WD-fay0/evidence-index.json`), which records zero `planned`
rows: 89 `host_run_verified`, 110 `terminal_unsupported_or_fail_closed`,
7 `dependency_blocked`, 2 `not_applicable`. A reader (or any automated audit keyed on the
word `planned`) is misled into concluding the entire video lane is unrendered.

The same section closes with the vestigial clause "Likewise, `planned` does not claim Wangp
has rendered the pair", which now refers to a state that no cell carries.

This is a documentation-accuracy defect only. No machine-checked invariant depends on the
sentence: `tests/test_current_parity_index.py` parses the matrix cells, not this prose.

## Acceptance Criteria

1. The capability-matrix preamble states the true rule: each cell carries its current
   terminal disposition from the parity index; `host_run_verified` requires a separately
   authorized run bundle (command, repository commit, model/LoRA provenance, queue attempt,
   output hashes, ffprobe metadata, QC result, assembly/recipe linkage); an unrendered cell
   is recorded as a typed fail-closed boundary (`unsupported`) or a missing-dependency
   boundary (`dependency_blocked`).
2. The vestigial `planned` clause in the same section is corrected to reference the states
   the cells actually carry.
3. No capability table cell, evidence link, hash, or count changes.
4. `uv run --frozen --extra dev pytest -q tests/test_current_parity_index.py` exits 0.
5. `pvg lint --backlog` reports 0 errors.

## Notes

Evidence: `docs/video-capabilities.md` (preamble), and the index census asserted by
`tests/test_current_parity_index.py`. One finding, one PR.

## Acceptance Criteria


## Design


## Notes


## History
- 2026-10-05T05:42:03Z status: open -> in_progress
- 2026-10-05T05:42:03Z auto-follows: linked to predecessor WD-cuzw
- 2026-10-05T05:42:03Z claimed by dev-WD-aaxz

## Links
- Parent: [[WD-3nod]]
- Follows: [[WD-cuzw]]

## Comments
