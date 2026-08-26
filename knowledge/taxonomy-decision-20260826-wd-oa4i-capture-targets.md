---
type: decision_record
domain: tooling-governance
status: active
run_id: run-wd-yyj9-t0
created_utc: "2026-08-26T15:30:00Z"
related: "[[capture-20260825T015512Z-2a260e79-3051-4853-888c-9a51cb3fcf65]]"
story_id: WD-oa4i
---

# Taxonomy decision: capture-note targets and the governed delete/move surface (P3 envelope)

**Story:** WD-oa4i | **Run:** run-wd-yyj9-t0 | **Recorded:** 2026-08-26 by sol-max

## Decision
Two distinct note families are in play, and they must not be conflated:

1. **Governed captures** — notes written by the paivot executor via
   run_knowledge_capture (sha256 evidence chain, role=developer). These live
   in `.vault/knowledge/` (repo-tracked) for wangp-dspy work orders, e.g. the
   Option A amendment record capture-20260826T140925Z-05a49b36.
2. **Vault knowledge notes** — free-form doctrine/capture notes in the nd-vault
   `knowledge/` folder (`.git/paivot/nd-vault/knowledge/`), managed with vlt.
   The two-step analog doctrine note (capture-20260825T015512Z-2a260e79) is this
   family; it was misrouted to `.trash/` and restored to `knowledge/` on
   2026-08-26 via `vlt move` + `vlt files` verification.

## P3 envelope (governed write surface)
- Writes to either family go through the governed path only: vlt for
  nd-vault notes, executor-owned run_knowledge_capture for .vault captures.
  No raw shell writes into either tree.
- Every write is verified post-hoc: `vlt files <folder>` listing (or readback
  marker) before the step is reported done. Silent no-ops are typed failures
  (WD-yyj9 precedent, fix 4b86d92).
- Trash is a staging area, not a destination: anything moved to `.trash/`
  must have a recorded reason or be restored.

## Known hazard (draft bug report follows in comments)
vlt delete-by-title resolves against BOTH extension-less and .md variants of
the same title; when both exist, the wrong sibling can be trashed. This bit us
on the stub-capture cleanup today. Filed as a paivot-hermes ticket after this
note lands.