---
id: WD-yyj9
title: "publish: vlt create needs .md extension; write silently no-ops on extension-mismatched notes"
status: open
priority: 1
type: task
labels: [bug]
created_at: 2026-08-23T18:09:31Z
created_by: speed
updated_at: 2026-08-23T18:09:31Z
content_hash: "sha256:57e10a24f9f19506ef78bf9e8cb698c9933926e425ef88f86c6737d93adf6213"
---

## Description
Live publish #2 findings: (1) vlt create path='Paivot Insights/<id>' created files WITHOUT .md — Obsidian won't index them, vlt read can't find them; create path must be 'Paivot Insights/<id>.md'. (2) write file='Paivot Insights/Index' on the extension-less note exits rc=0 'note not found' silently — publish reported success:true while the Index never updated (mtime 12:32 smoke vs 13:08 run). Fix: always create with .md; after write, verify the note is findable (vlt read or files listing re-check) or treat 'note not found' stderr as a typed failure. Cleanup: the 4 extension-less notes in Brand OS vault Paivot Insights/ need renaming (vlt move or delete+republish).

## Acceptance Criteria


## Design


## Notes


## History


## Links


## Comments
