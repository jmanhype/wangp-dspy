---
id: WD-4jpr
title: "ADOPT: no-proper-nouns gate against entity registry"
status: closed
priority: 2
type: task
parent: WD-j9nx
created_at: 2026-08-27T16:29:10Z
created_by: speed
updated_at: 2026-08-27T16:32:02Z
content_hash: "sha256:98de42f8b6f4b4ce9f7542a2e393d1e3a36178c11dbbbb9366b87eed627a7555"
assignee: speed
follows: [WD-4k56]
closed_at: 2026-08-27T16:32:02Z
led_to: [WD-gq8y, WD-4s1b]
---

## Description
# ADOPT: no-proper-nouns gate against entity registry  Implements the no-names doctrine (docs/extraction/shuohao-skills/no-names-doctrine.md, GLM ADOPT verdict) as a deterministic gate: image/render prompts must never contain registry proper nouns (memorized-entity bias — image models draw their memory of a named entity, not ours).  ## Components  1. **Pure no-names check function + entity registry schema + seed registry.** Deterministic matcher over an entity registry (names + aliases). Word-boundary matching, case-insensitive, alias-aware. Registry is a documented schema with a seeded initial set (SGFLIX characters/aliases/handles from canon). 2. **Gate wired into PromptDirector brief validation** alongside the existing meta-hint guard (`_reject_meta_hints` in predict/prompt_director.py), plus a standalone CLI `scripts/check_names.py` for pre-submission checks on arbitrary prompt text/files. 3. **Strict TDD, zero-model.** No LLM calls anywhere in the gate or its tests.  ## Acceptance criteria  - (a) Deterministic matcher passes TDD suite: exact match, case variants, alias hits, word-boundary behavior, and false-positive cases (e.g., name appearing inside a longer word, common-word collisions) all covered by tests. - (b) Briefs containing registry names are rejected with a typed failure using the same pattern as the meta-hint guard (ValueError raised during RenderBrief validation, caught by the existing rejection path in PromptDirector.forward). - (c) CLI works on arbitrary text (stdin/args) and files; non-zero exit + clear report on violations, zero exit when clean. - (d) Registry schema documented + seeded (schema doc + seed data file checked in). - (e) Full test suite green + implementation captured (PR trail, evidence).  ## Notes  - Doctrine source: docs/extraction/shuohao-skills/no-names-doctrine.md (ADOPT section). - The "second half" (explicit identity description to counter Western-default prior) is out of scope for this story — gate only. - Typed-failure pattern reference: predict/prompt_director.py `_reject_meta_hints` + RenderBrief.__post_init__ wiring. 

## Acceptance Criteria


## Design


## Notes
Dispatch (2026-08-27, sol-max): Qwen implements — already briefed and running.

Brief: implement the no-names doctrine (docs/extraction/shuohao-skills/no-names-doctrine.md, GLM ADOPT verdict) as a deterministic gate. Components: (1) pure no-names check function + entity registry schema + seed registry; (2) gate wired into PromptDirector brief validation alongside the meta-hint guard (_reject_meta_hints in predict/prompt_director.py), plus standalone CLI scripts/check_names.py for pre-submission checks on any prompt text/files; (3) strict TDD, zero-model.

Acceptance criteria: (a) deterministic matcher passes TDD suite (exact/case/alias/word-boundary + false-positive cases); (b) briefs containing registry names rejected with typed failure (same pattern as meta-hint guard); (c) CLI works on arbitrary text/files; (d) registry schema documented + seeded; (e) full suite green + implementation captured.

Note: story created via paivot_story story_create (WD-4jpr); AC section patch not_wired at create time — AC text is embedded in Description above and restated here.

## History
- 2026-08-27T16:29:34Z status: open -> in_progress
- 2026-08-27T16:29:34Z auto-follows: linked to predecessor WD-4k56
- 2026-08-27T16:29:34Z claimed by speed
- 2026-08-27T16:32:02Z status: in_progress -> closed

## Links
- Parent: [[WD-j9nx]]
- Follows: [[WD-4k56]]
- Led to: [[WD-gq8y]], [[WD-4s1b]]

## Comments

### 2026-08-27T16:30:09Z speed
Dispatch: Qwen implements — already briefed and running (see Notes). AC (a)-(e) restated in dispatch note.

### 2026-08-27T16:32:01Z speed
ADOPT #1 DELIVERED: PR #27 merged 7971612 (GLM review PASS all 6 items). Gate + CLI + registry schema live. Future-work noted: wire registry into LM forward() optimization path. PM accept pending.
