---
id: WD-4jpr
title: "ADOPT: no-proper-nouns gate against entity registry"
status: in_progress
priority: 2
type: task
parent: WD-j9nx
created_at: 2026-08-27T16:29:10Z
created_by: speed
updated_at: 2026-08-27T16:29:34Z
content_hash: "sha256:ee24f3de58b7d93dd75440ca0d3bb5e4434c0832ac730c978c2c4a30a40ce348"
assignee: speed
follows: [WD-4k56]
---

## Description
# ADOPT: no-proper-nouns gate against entity registry  Implements the no-names doctrine (docs/extraction/shuohao-skills/no-names-doctrine.md, GLM ADOPT verdict) as a deterministic gate: image/render prompts must never contain registry proper nouns (memorized-entity bias — image models draw their memory of a named entity, not ours).  ## Components  1. **Pure no-names check function + entity registry schema + seed registry.** Deterministic matcher over an entity registry (names + aliases). Word-boundary matching, case-insensitive, alias-aware. Registry is a documented schema with a seeded initial set (SGFLIX characters/aliases/handles from canon). 2. **Gate wired into PromptDirector brief validation** alongside the existing meta-hint guard (`_reject_meta_hints` in predict/prompt_director.py), plus a standalone CLI `scripts/check_names.py` for pre-submission checks on arbitrary prompt text/files. 3. **Strict TDD, zero-model.** No LLM calls anywhere in the gate or its tests.  ## Acceptance criteria  - (a) Deterministic matcher passes TDD suite: exact match, case variants, alias hits, word-boundary behavior, and false-positive cases (e.g., name appearing inside a longer word, common-word collisions) all covered by tests. - (b) Briefs containing registry names are rejected with a typed failure using the same pattern as the meta-hint guard (ValueError raised during RenderBrief validation, caught by the existing rejection path in PromptDirector.forward). - (c) CLI works on arbitrary text (stdin/args) and files; non-zero exit + clear report on violations, zero exit when clean. - (d) Registry schema documented + seeded (schema doc + seed data file checked in). - (e) Full test suite green + implementation captured (PR trail, evidence).  ## Notes  - Doctrine source: docs/extraction/shuohao-skills/no-names-doctrine.md (ADOPT section). - The "second half" (explicit identity description to counter Western-default prior) is out of scope for this story — gate only. - Typed-failure pattern reference: predict/prompt_director.py `_reject_meta_hints` + RenderBrief.__post_init__ wiring. 

## Acceptance Criteria


## Design


## Notes


## History
- 2026-08-27T16:29:34Z status: open -> in_progress
- 2026-08-27T16:29:34Z auto-follows: linked to predecessor WD-4k56
- 2026-08-27T16:29:34Z claimed by speed

## Links
- Parent: [[WD-j9nx]]
- Follows: [[WD-4k56]]

## Comments
