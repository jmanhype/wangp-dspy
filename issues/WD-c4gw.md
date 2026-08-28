---
id: WD-c4gw
title: "ADOPT: two-class language split for DSPy signatures (human-review vs engine-bound fields)"
status: in_progress
priority: 2
type: task
labels: [adopt, architecture, language-split]
parent: WD-j9nx
created_at: 2026-08-27T19:37:43Z
created_by: speed
updated_at: 2026-08-28T00:23:56Z
content_hash: "sha256:2cf06ac750001baf89352e6e4d86b9ea68c6f62fcaec51703117ed0fc3a7631b"
assignee: speed
follows: [WD-7185]
---

## Description
ADOPT #5 from shuohao-skills extraction (docs/extraction/shuohao-skills/language-split-contract.md, ADOPT verdict per GLM review capture-20260827T153308Z).

Two-class field split as a schema rule for every wangp-dspy DSPy output signature:
- Human-review fields follow the workflow language (report lang).
- Engine-bound prompt fields are LOCKED ENGLISH — image/video models and TTS engines eat English most stably ("机器字段不跟随 lang——图像模型和 TTS 引擎吃英文最稳", profile-pass.md:16). The report language decides who reads, never what the engines eat.
- Evidence/quotes are a third implicit class: NEVER translated, verbatim source language preserved ("引文永远保持原文语言——它是证据，翻译了就不是证据了", profile-pass.md:26).

Our surface: signatures/ (RenderBriefSignature in predict/prompt_director.py, ProfileSelectorSignature in signatures/profile.py, RenderQCSignature in signatures/qc.py) — all fields currently unclassified free-form str with no language contract. Plus a deterministic language-class validator gate in gates/, same pattern as no-names (gates/no_names_gate.py) and common-actions (gates/common_actions.py): bidirectional check like theirs ("设定英文混进中文…都拦").

Fold-in (operator decision 2026-08-27, FOLD IN): the no-proper-nouns registry pass-through into the LM forward() optimization path — GLM's future-work flag from WD-4jpr (PR #27): "wire registry into LM forward() optimization path". Ground truth on the gap: PromptDirector.forward takes no registry; Pipeline.forward calls self.director(intent=intent) with no registry pass-through, so the no-names gate only fires when someone hand-builds RenderBrief(registry=...) — the LM-generated brief path (the actual production + GEPA path) bypasses the gate entirely. Fold it in here since this story touches the same signature/wiring surface: entity registry flows through Pipeline -> PromptDirector.forward -> RenderBrief construction, so the gate is live on the LM path.

Design constraints (from the extraction doc, apply deliberately):
- "Eliminate ambiguity over explaining it": when a downstream consumer can copy the wrong field, DELETE the redundant field rather than relabel it.
- Never name a multilingual field after one language (no promptZh mistakes in our schemas).
- promptLocal concept: ADAPT — SGFLIX bibles are reviewed in English by default, so keep the omission rule (don't emit duplicates) and skip the field entirely.
- PASS (out of scope): full trilingual UI machinery (I18N tables, ui-template) — our artifacts are English-primary.

Acceptance criteria:
(a) Field-class contract explicit on all three signatures: each output field classified human-review vs engine-bound (evidence-class where applicable), documented in the signature docstrings AND enforced deterministically — zero-model, no LLM calls in the gate or its tests.
(b) Deterministic language-class validator in gates/ (same typed-failure pattern as _reject_registry_names / _reject_risky_actions: ValueError during validation, caught by existing rejection paths): engine-bound fields containing non-ASCII/non-English text fail LOUDLY; human-review fields accept any language; evidence/quote fields reject translation (verbatim-source check where source is available). Bidirectional: English leaking into a lang-scoped human field is also flagged.
(c) Registry pass-through wired: Pipeline accepts an entity registry (load via gates.load_registry) and threads it to PromptDirector.forward so LM-generated RenderBriefs carry registry=... and the no-names gate fires on the LM path; missing registry = LOUD skip (warning), never silent — same doctrine as the existing gate. Backward compatible: no registry arg = current behavior.
(d) TDD suite: RED first, then GREEN — each classification fires on a positive sample; word-boundary/case behavior pinned; false-positive cases covered (legitimate proper nouns in human-review fields do NOT fire the engine lock); empty/whitespace input handled distinctly (typed, loud skip when optional inputs absent — never silent); all deterministic, zero-model.
(e) Full test suite green in repo uv venv + implementation captured (PR trail, evidence). Docs updated in the same slice (docstring contract + docs/ note citing the extraction doc with file:line refs).

## Acceptance Criteria


## Design


## Notes


## History
- 2026-08-27T19:37:58Z status: open -> in_progress
- 2026-08-27T19:37:58Z auto-follows: linked to predecessor WD-7185
- 2026-08-27T19:37:58Z claimed by speed

## Links
- Parent: [[WD-j9nx]]
- Follows: [[WD-7185]]

## Comments

### 2026-08-28T00:23:56Z speed
ADOPT #5 DELIVERED: PR #32 merged (GLM SHIP — all 5 PASS; fold-in traced line-by-line: Pipeline->director->_parse_brief->_reject_registry_names fires on the LM path; RED commit verified by checkout; 355 tests). Follow-ups: asymmetric human-review check, brand-token allowlist.
