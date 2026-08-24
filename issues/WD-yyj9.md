---
id: WD-yyj9
title: "publish: vlt create needs .md extension; write silently no-ops on extension-mismatched notes"
status: closed
priority: 1
type: task
labels: [bug]
created_at: 2026-08-23T18:09:31Z
created_by: speed
updated_at: 2026-08-24T13:42:20Z
content_hash: "sha256:4f555fa83239a404cf3ad17cfbcc454d3968628166fea4ec9af6b3ff90fa2453"
assignee: dev-WD-yyj9
closed_at: 2026-08-24T13:42:03Z
close_reason: "Fix verified live: commit 4b86d92 (.md normalization + fail-loud readback), 24/24 + 92/92 tests green, live vault probe PASS, 4 legacy notes renamed. Evidence in comments."
---

## Description
Live publish #2 findings: (1) vlt create path='Paivot Insights/<id>' created files WITHOUT .md — Obsidian won't index them, vlt read can't find them; create path must be 'Paivot Insights/<id>.md'. (2) write file='Paivot Insights/Index' on the extension-less note exits rc=0 'note not found' silently — publish reported success:true while the Index never updated (mtime 12:32 smoke vs 13:08 run). Fix: always create with .md; after write, verify the note is findable (vlt read or files listing re-check) or treat 'note not found' stderr as a typed failure. Cleanup: the 4 extension-less notes in Brand OS vault Paivot Insights/ need renaming (vlt move or delete+republish).

## Acceptance Criteria


## Design


## Notes


## History
- 2026-08-24T02:14:26Z status: open -> in_progress
- 2026-08-24T02:14:26Z claimed by dev-WD-yyj9
- 2026-08-24T13:42:03Z status: in_progress -> closed

## Links


## Comments

### 2026-08-24T13:42:20Z speed
Verified + closed by jmanhype session (2026-08-23 ~23:40 CDT). Evidence: (1) fix commit 4b86d92 'fail-loud system-scope capture (.md + readback)' — path always .md, post-write marker readback refuses silent no-op. (2) tests: test_insights_publish.py 24/24 pass (uv run pytest); vault capture/readback suite 92/92 pass. (3) Live end-to-end probe on Brand OS vault: create with .md -> read returns content+marker; probe note trashed after. (4) Cleanup clause done: 4 extension-less notes renamed to .md (13:47), folder archived 'Paivot Insights (archived 2026-08)'.
