---
type: decision_record
domain: tooling-governance
status: active
run_id: run-wd-yyj9-t0
created_utc: "2026-08-26T15:30:00Z"
related: "[[capture-20260825T015512Z-2a260e79-3051-4853-888c-9a51cb3fcf65]]"
story_id: WD-oa4i
---

# Taxonomy decision: ONE canonical project knowledge vault with typed subfolders (supersedes the flat-knowledge convention and the two-family note)

**Supersession 2 (2026-08-26, operator ruling):** the FLAT convention — all capture notes in bare `knowledge/` — is retired. Canonical structure is now `knowledge/` WITH typed subfolders:

    knowledge/conventions/   dataset authoring + working conventions (doctrine notes)
    knowledge/debug/         debugging notes, failure post-mortems
    knowledge/decisions/     decision records, work orders, amendments
    knowledge/patterns/      reusable patterns (loader behavior, TDD recipes)
    knowledge/skills/        procedural know-how
    knowledge/uat/           acceptance/gate checklists (Luna artifacts)

New captures are filed by type AT WRITE TIME into the matching subfolder; retroactive reclassification goes through `vlt move` (wikilink-aware). All nine pre-existing flat notes were reclassified on 2026-08-26 per this mapping (see the reclassification capture in decisions/).

**Story:** WD-oa4i | **Run:** run-wd-yyj9-t0 | **Recorded:** 2026-08-26 by sol-max
**Supersession:** This note replaces its own earlier revision, which documented
"two capture families" as convention. The operator ruled (2026-08-26): there is
ONE canonical project knowledge vault. The two-family framing is retired.

## Decision — single canonical root
The canonical project knowledge vault for wangp-dspy is:

    .git/paivot/nd-vault/knowledge/   (vault name: `nd-vault`)

It is the live nd board vault: gitignored-but-synced (persisted on the
`nd/backlog` branch via pvg/nd), holds the majority of captures, and is what
the nd board + vlt registry already point at. All project-scope capture notes
belong here.

## Existing notes reclassified (2026-08-26)
| note | destination |
|---|---|
| taxonomy-decision-20260826-wd-oa4i-capture-targets (this note) | decisions/ |
| capture-20260826T140925Z-05a49b36 (Option A amendment) | decisions/ |
| capture-20260826T135954Z-wd-oa4i-step1-curation | decisions/ |
| capture-20260826T135515Z-e84a2f91 (work order) | decisions/ |
| capture-20260826T135954Z-wd-oa4i-step1-loader | patterns/ |
| capture-20260826T135954Z-wd-oa4i-step1-intents-v2 | conventions/ |
| capture-20260826T135515Z-1d808578 (intents authoring) | conventions/ |
| capture-20260825T015512Z-2a260e79 (two-step analog doctrine) | conventions/ |
| capture-20260826T140500Z-luna-wdoa4i-gates | uat/ |

Moved via `vlt move` (wikilink-aware); verified with `vlt files --tree` and `vlt unresolved` (0 broken links).

## Root `.vault` must NOT be recreated
- `<project-root>/.vault/knowledge/` is NOT a capture destination. It was a
  fork created by the P1 default in `driver/vault_capture.py`
  (`PROJECT_KNOWLEDGE_SCOPE = ".vault/knowledge"`; zero-config default
  `vault_arg = <project_root>/.vault`).
- If any code path recreates root `.vault/knowledge/` or writes a capture into
  it, that is a BUG to report — not a convention to accommodate. Detection:
  `ls <project>/.vault/knowledge` non-empty, or a capture note with a
  `run_knowledge_capture` frontmatter envelope landing outside
  `.git/paivot/nd-vault/knowledge/`.
- The three forked captures (capture-20260826T135515Z x2,
  capture-20260826T140925Z) were moved out of root `.vault/knowledge/` into
  this vault's `knowledge/` on 2026-08-26 and verified with `vlt files`.
  Note: `vlt move` refuses cross-vault sources ("path escapes vault boundary"),
  so the physical move was a filesystem mv between the two registered vaults,
  followed by `vlt files folder="knowledge"` verification in the target vault.
  Cross-vault moves are themselves a gap worth filing (no governed surface).

## Code path that recreated root `.vault` (for the bug report)
Precise chain, all in paivot-hermes unless noted:
1. **Repo bootstrap (wangp-dspy commit cf81408, 2026-08-21):** committed
   `.vault/.gitignore` — root `.vault/` became part of the repo layout from day one.
2. **`.vault/.nd-shared.yaml` (wangp-dspy commit 6f9f4cb, 2026-08-21):**
   `mode: git_common_dir, path: paivot/nd-vault` — this correctly redirects the
   ND BACKLOG to `.git/paivot/nd-vault`, but only for backlog ops. It does
   nothing for the capture write path.
3. **`driver/vault_capture.py` → `run_knowledge_capture` (paivot-hermes, S2
   slice; PR #76/#77 lineage):** project scope resolves the vault as
   `project_knowledge_vault or os.path.abspath(os.path.join(project_root,
   ".vault"))` (lines ~302/318) and writes via `vlt create` to
   `knowledge/<title>.md` relative to that root (line ~322). wangp-dspy has NO
   `project_knowledge_vault` override configured (its `.paivot/config.yaml`
   sets only backlog=vault:.vault and notes=vault:nd-vault for pvg, which the
   capture bridge does not read), so every project-scope capture landed in
   root `.vault/knowledge/` — recreating/filling the fork even though the nd
   board lives elsewhere.
4. The retroactive captures of 2026-08-26 (commit 3155933) went through exactly
   this bridge ("executor-owned run_knowledge_capture bridge (vlt-only write,
   sha256 evidence, role=developer)" per the commit message).

Fix direction (operator call): route project-scope captures at
`<project>/.git/paivot/nd-vault` (honor an explicit `project_knowledge_vault`
config value pointing at the shared worktree vault) and make the zero-config
default fail loud when the resolved vault is not the live nd board vault — or
at minimum refuse when `.vault/.nd-shared.yaml` says the board lives elsewhere.

## P3 envelope (governed write surface) — unchanged
- Writes go through the governed path only: vlt for nd-vault notes,
  executor-owned run_knowledge_capture for captures. No raw shell writes into
  either tree.
- Every write is verified post-hoc: `vlt files <folder>` listing (or readback
  marker) before the step is reported done. Silent no-ops are typed failures
  (WD-yyj9 precedent, fix 4b86d92).
- Trash is a staging area, not a destination: anything moved to `.trash/`
  must have a recorded reason or be restored.

## Known hazard (ticket filed)
vlt delete-by-title resolves against BOTH extension-less and .md variants of
the same title; when both exist, the wrong sibling can be trashed. Filed as a
paivot-hermes ticket (see issues/ in the paivot-hermes repo vault, prefix PH).
