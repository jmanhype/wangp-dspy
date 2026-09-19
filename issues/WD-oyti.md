---
id: WD-oyti
title: "Provenance tiers: canon-citation vs (inferred) marker on identity/bible claims"
status: closed
priority: 2
type: task
parent: WD-j9nx
created_at: 2026-08-28T00:33:41Z
created_by: speed
updated_at: 2026-08-28T00:50:32Z
content_hash: "sha256:f0f461b61bb0dfef523ea58855b2f70c26c2a213667d09112a9a5fd2532a3673"
closed_at: 2026-08-28T00:50:32Z
blocks: [WD-h25b]
---

## Description
## Description

Implement the inferred-marker convention from docs/extraction/shuohao-skills/inferred-marker-convention.md (GLM-ruled ADOPT, 7/7, zero overrides). Identity/bible claims in RenderBrief carry provenance: a canon citation OR exactly one (inferred) marker. The (inferred) marker NEVER enters any prompt field — it is stripped at the brief_to_prompt seam. Decision-vs-fact audit trails stay separate in the entity registry schema.

## Acceptance Criteria

1. **Provenance gate (pure, zero-model):** every identity/bible claim carries either a canon citation or exactly one `(inferred)` marker; unmarked middle items and double-marked items are rejected with a typed violation. Gate lives in gates/ alongside language_gate.py / no_names_gate.py patterns (loud skip, typed violations).
2. **Marker never reaches a prompt:** host/wangp_adapter.py brief_to_prompt() output is asserted marker-free; a marker present at that seam = typed rejection. This is the handoff-to-prompt stripping point per the extraction's prescription.
3. **Specific-neutral fallback rule** documented + gated where applicable.
4. **Decision vs fact separation** in datasets/entity-registry.json + docs/entity-registry.md schema (from/mergeNote for decisions, cited facts for canon).
5. **TDD RED→GREEN:** tests cloned from tests/test_language_gate.py + test_no_names_gate.py templates (incl. CLI exit-code smoke 0/1/2, seed-registry load, typed brief rejection, loud-skip caplog). Full suite green in .venv (Python 3.12), zero-model.

## Design

- Enforcement point: RenderBrief.__post_init__ rejection chain in predict/prompt_director.py (identity_lock is ENGINE_BOUND); LM path re-raises gate rejections (WD-c4gw fold-in) so provenance rejection surfaces on the GEPA path for free.
- Stripping seam: brief_to_prompt() renders brief sections verbatim into settings.json script — strip markers there, assert marker-free output.
- Registry schema home: datasets/entity-registry.json + docs/entity-registry.md.

## Notes

- Seam-violation note for follow-up ticket: run_pipeline._checked_video uses os.path.isfile directly (local-namespace assumption) — inconsistent with the RenderHost seam; SshHost renders return local-mirror paths so it works today, but it is a latent seam violation. Candidate follow-up under this epic.

## History

- 2026-08-27: story created by sol-max under WD-j9nx, resume of #6 cycle (scoping complete in prior session; design source read in full; implementation surface mapped).

## Acceptance Criteria


## Design


## Notes


## History
- 2026-08-28T00:50:32Z status: open -> closed
- 2026-09-19T20:39:23Z dep_added: blocks WD-h25b

## Links
- Parent: [[WD-j9nx]]
- Blocks: [[WD-h25b]]

## Comments

### 2026-08-28T00:50:32Z speed
ADOPT #6 DELIVERED: PR #33 merged (GLM ADOPT verdict — handoff seam verified single-choke-point with planted-marker test catching unstripped fields; RED genuine via base-checkout module-absence; 390 passed). Nits for follow-up: wire check_specific_neutral into brief path, remove unused _split_claims.
