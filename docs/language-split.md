# Language-split field contract (WD-c4gw)

Adopted from shuohao-skills (docs/extraction/shuohao-skills/
language-split-contract.md — the extraction doc is the design source
of truth; verbatim doctrine: profile-pass.md:16 "机器字段不跟随
lang——图像模型和 TTS 引擎吃英文最稳"; :26 evidence-never-translated;
CHANGELOG:440-458 bidirectional gates "设定英文混进中文…都拦").

## Field classes (gates/language_gate.py FIELD_CLASSES)

| Signature | Field | Class |
|---|---|---|
| RenderBrief | subject, motion, camera, style, audio_direction, negatives, identity_lock | ENGINE_BOUND (LOCKED ENGLISH) |
| ProfileSelector | decision | ENGINE_BOUND |
| RenderQC | critique | ENGINE_BOUND |
| RenderQC | notes | HUMAN_REVIEW (workflow language) |

RenderBrief sections are engine-bound because they feed the WanGP
render prompt verbatim — they are prompt fragments, not review prose.
EVIDENCE class exists in the gate (verbatim source, never translated,
verbatim-match check, loud typed skip without a source) for future
quote-carrying fields.

## Gate semantics

- ENGINE_BOUND: non-ASCII word runs → typed ValueError via the
  RenderBrief rejection path (alongside meta-hints/no-names/actions).
- HUMAN_REVIEW: any language; when a workflow lang is scoped (zh),
  English mixing is flagged (bidirectional, like theirs).
- EVIDENCE: verbatim comparison against source; differs → violation
  ("翻译了就不是证据了"); no source → LOUD typed skip.

## Design constraints applied deliberately

- **Eliminate ambiguity over explaining it** (CHANGELOG:162): no
  duplicate copyable fields were introduced; nothing to relabel.
- **Never name a multilingual field after one language**
  (promptZh→promptLocal lesson, CHANGELOG:794): pinned by test.
- **promptLocal = ADAPT/omit**: SGFLIX bibles are English-primary;
  the field is skipped entirely, omission rule kept (no duplicates).
- **Trilingual UI machinery = PASS**: out of scope.

## Registry fold-in (operator decision 2026-08-27)

Pipeline(registry=...) → director.forward(intent=..., registry=...)
→ RenderBrief(registry=...) → no-names gate fires ON THE LM PATH
(the production + GEPA path previously bypassed it entirely).
Missing registry = LOUD skip (warning), never silent; no registry
arg = previous behavior (backward compatible). Gate-rejection
ValueErrors now surface through the WD-txt9 fallback (rejections
are re-raised; only genuine LM/parse failures fall back).
