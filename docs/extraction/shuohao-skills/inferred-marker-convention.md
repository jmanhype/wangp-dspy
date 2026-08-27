# Inferred-Marker Provenance Convention — extraction from shuohao-skills

Source: github.com/eternityspring/shuohao-skills (clone at /tmp/shuohao-skills), Apache-2.0, © 2026 烁皓 (eternityspring). Extracted 2026-08-27 for WD-4k56 follow-up (parent WD-j9nx).

## Mechanism (our terms)

**The rule** (profile-pass.md rule 1): everything on a character card must be grounded in the observation record. Where the writer must fill a gap to make the设定 usable, the invented portion must (a) stay consistent with the source and (b) be **marked** with a single provenance marker — 「（推断）」 in Chinese reports, `(inferred)` in English reports, or the equivalent in whichever language. Exactly one marker per item, never both ("只用一种标记，不要中英都加").

**Three placement rules that make it a real contract rather than a habit:**

1. **Markers live in human fields only.** Inferred content is marked in `persona.appearance` / `persona.identity`; it must NEVER appear inside machine prompts — "(inferred) 混进去会被画进画面" (the marker would literally get painted into the image; profile-pass.md:44).
2. **Evidence can never be inferred.** `persona.evidence` accepts ONLY strings verbatim-copied from the provided quote block — no translation, no trimming, no merging two quotes, no substituting from observations. Empty block → empty array (profile-pass.md:26). This makes the provenance hierarchy explicit: verbatim evidence > marked inference > nothing. There is no unmarked middle ground.
3. **When inference fails, commit to specific-neutral.** If ethnicity/era/region can't be inferred, choose a neutral but CONCRETE setting — never leave it blank, never write a vague "亚洲人" (profile-pass.md:44). The system prefers a flagged-or-explicit decision over ambiguity in either direction.

**Surface-level rendering:** the report auto-highlights （推断） markers (report-style.md / CHANGELOG 1.0.0: "「（推断）」自动高亮、冷灰印张配铁锈红印记") — the marker is first-class UI, so a human reviewer can scan a card and instantly see which claims are load-bearing evidence vs. reconstruction.

**Related but distinct: the from/mergeNote chain.** Adaptation-level provenance (`characters[].from` ← who merged into whom, `mergeNote` stating why the lead group was chosen) records provenance of DECISIONS, while (推断) records provenance of FACTS. Two different audit trails that never mix.

## File:line references (into /tmp/shuohao-skills)

- `skills/novel-characters/references/profile-pass.md:24` — rule 1: grounding + marker requirement + one-marker-only
- `:26` — rule 2: evidence verbatim-only, never invented (the complement that makes the marker meaningful)
- `:42-44` — inference from source clues (人名用字、地名、称谓、器物、节令、货币、饮食); markers stay out of prompts; specific-neutral fallback
- `skills/novel-characters/references/report-style.md` — （推断） highlighting convention
- `CHANGELOG.md:802-826` (novel-characters 1.0.0) — "「（推断）」自动高亮" in report conventions; deterministic checks "逐字引文" listed among core validations
- `skills/novel-outline/references/outline-pass.md:15` — decision-level evidence (adaptation.keep carries verbatim source excerpts)

## Verbatim key excerpts

```text
// profile-pass.md:24
**一切基于观察记录。** 为了让设定可用而不得不补全的部分，要跟原文保持一致，并且**标注出来**——中文报告加「（推断）」，英文报告加 `(inferred)`……**只用一种标记，不要中英都加。**
// profile-pass.md:26
**`persona.evidence` 只能放「可引用原文」区块里的字符串，逐字照抄。** 不许翻译、不许裁剪、不许把两条合并……那个区块是空的就返回空数组。
// profile-pass.md:44
推断出来的内容按第 1 条标注在 `persona.appearance` / `persona.identity` 里；**提示词里不标注**——那是给机器读的，`(inferred)` 混进去会被画进画面。实在推不出来就定一个中性但具体的设定，不要留空、不要写成泛泛的「亚洲人」。
```

## RECOMMENDATION vs SGFLIX bible pipeline / wangp-dspy / X-content

**ADOPT**
- Two-tier provenance (verbatim evidence / marked inference) for the SGFLIX character bibles: every identity claim in an IDENTITY_LOCK bible should carry either a canon citation or an `(inferred)` marker, with the marker stripped at handoff-to-prompt time by rule (their "markers never enter prompts" rule is the operational safeguard — bake it into the handoff assembler).
- Specific-neutral fallback for unresolved bible fields: commit to concrete canon rather than leaving blanks that generation models fill with Western defaults.
- Decision-provenance vs fact-provenance as separate trails (mergeNote/from ↔ inferred) in the entity registry.

**ADAPT**
- Single-marker-per-item and report highlighting: adopt if/when bibles get a rendered review surface; until then the marker in the JSON alone suffices for wangp-dspy gates (a simple "no `(inferred)` substring in any prompt field" check is nearly free).

**PASS**
- Nothing — this convention is small, portable, and directly fixes a real gap in our pipeline (invented bible details currently indistinguishable from canon at generation time).
