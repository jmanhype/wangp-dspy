# Language-Split Field Contract — extraction from shuohao-skills

Source: github.com/eternityspring/shuohao-skills (clone at /tmp/shuohao-skills), Apache-2.0, © 2026 烁皓 (eternityspring). Extracted 2026-08-27 for WD-4k56 follow-up (parent WD-j9nx).

## Mechanism (our terms)

Every artifact has a report language `lang` (default zh, user-settable, --lang flag > JSON top-level `lang` > default; invalid lang errors loudly, never silently falls back). Fields split into exactly two classes:

| Class | Fields | Language |
| --- | --- | --- |
| Human-readable | oneLiner, persona.*, voice.timbre/pitch/pace/accent/emotion/referenceHint, image.style, image.promptLocal | follows `lang` |
| Machine-facing | image.prompt, image.negativePrompt, image.tags, image.sheet, voice.prompt | **always English** |

Rationale: "机器字段不跟随 `lang`——图像模型和 TTS 引擎吃英文最稳" (profile-pass.md:16). The report language decides *who reads*, never *what the engines eat*.

**Evidence is a third, implicit class: never translated.** `persona.evidence` must be verbatim strings from the provided quote block, source language preserved: "引文永远保持原文语言，不跟随 `lang`——它是证据，翻译了就不是证据了" (profile-pass.md:26). Same rule in roster-pass quotes and in storyboard `<d>` blocks (dialogue stays in its original language inside otherwise-English H3 prompts; CHANGELOG novel-storyboard 1.0.0: "台词/歌词/画面文字按官方规定保留原文").

**promptLocal is a one-way translation, omitted when redundant:** it is the local-language rendering of the English image prompt for human review; when `lang` is `en` it MUST be omitted (otherwise it duplicates the English verbatim) — profile-pass.md:18.

**The deliberate exception: voice has NO promptLocal** (profile-pass.md:20). Reasoning: the six voice fields (timbre/pitch/pace/accent/emotion/referenceHint) are already mandatory local-language fields — a human reviews those six faster than prose; adding a translation would create a second copy button that users will feed into the TTS engine — "生产里真踩过" (actually hit in production). CHANGELOG 1.10.0 expands: the report originally rendered promptLocal (Chinese) first with the label "音色提示词" and the real English prompt second with an "EN" suffix; Chinese users copied the first one and fed prose to TTS. Fix: **delete the field** — "消除歧义优于解释歧义" (eliminating ambiguity beats explaining it — they did NOT choose "label it more clearly").

**Interface vs data vs prompt are three separate switches:** report UI language (--lang), artifact content language, and storyboard `promptLang` (H3 prompt language, zh mode even allows names) are independent (CHANGELOG 双语化 entry; storyboard 1.0.0 entry). Gate i18n is display-time only: gate labels map id→English with thresholds computed by the gate itself and substituted into placeholders; failure details and data content stay in their original language.

**Naming history matters:** `image.promptZh`/`voice.promptZh` were renamed to `promptLocal` in 1.1.0 because "多语言下 `Zh` 这个名字不成立" — a hard lesson: never name a field after one language if the design is multilingual.

## File:line references (into /tmp/shuohao-skills)

- `skills/novel-characters/references/profile-pass.md:7-20` — the field-class table (:11-14), machine-fields-always-English (:16), promptLocal omission rule (:18), deliberate no-voice-promptLocal (:20)
- `:26` — evidence never translated
- `skills/novel-characters/references/roster-pass.md:11` — quotes stay source-language, no stitching
- `CHANGELOG.md:147-189` — 1.10.0 voice.promptLocal deletion, "消除歧义优于解释歧义", wrong-copy incident (:153-160)
- `CHANGELOG.md:746-768` — 1.2.0 multilingual design; promptZh→promptLocal rename (:794); "半吊子报告" validation (no `ui` + unsupported lang = error, :760-762 area)
- `CHANGELOG.md:364-382` — report i18n across five skills; --lang/promptLang independence (:380)
- `skills/novel-storyboard/SKILL.md` + `CHANGELOG.md:440-458` — promptLang zh mode, language gates bidirectional ("设定英文混进中文…都拦")

## Verbatim key excerpts

```text
// profile-pass.md:13-14
| **给人读的** | `oneLiner`、`persona.*` … | **`lang` 指定的语言** |
| **喂给机器的** | `image.prompt`、`image.negativePrompt` … `voice.prompt` | **永远英文** |
// profile-pass.md:20
**`voice` 没有 `promptLocal`，这是有意的。**……再给一段中文译文只会多出一个长得一样的复制按钮，用户会把它喂进 TTS 引擎——**生产里真踩过**。
// profile-pass.md:26
**注意：引文永远保持原文语言，不跟随 `lang`**——它是证据，翻译了就不是证据了。
// CHANGELOG.md:163
**消除歧义优于解释歧义**——这次没有选择「把标签写清楚提醒用户别点错」
```

## RECOMMENDATION vs SGFLIX bible pipeline / wangp-dspy / X-content

**ADOPT**
- The two-class field split as a schema rule for every wangp-dspy DSPy output signature: human-review fields follow the workflow language; engine-bound prompt fields are locked English; evidence/quotes are immutable originals. Our DSPy pipelines already half-do this implicitly; making it an explicit field-class contract (and gating it bidirectionally like theirs) kills a whole class of mixed-language prompt bugs.
- "Eliminate ambiguity over explaining it": when a downstream consumer can copy the wrong field, DELETE the redundant field rather than relabel it. Applicable to our QC report → copy-paste-into-WanGP path.
- Never name multilingual fields after one language (no `promptZh` mistakes in our schemas).

**ADAPT**
- promptLocal concept: for SGFLIX bibles reviewed in English by default, the local-language rendering is usually unnecessary; keep the omission rule (don't emit duplicates) and skip the field entirely.

**PASS**
- Full trilingual UI machinery (I18N tables, ui-template) — our artifacts are English-primary; not worth the surface.
