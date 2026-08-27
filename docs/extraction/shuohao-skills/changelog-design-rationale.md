# CHANGELOG as Design-Rationale History — extraction from shuohao-skills

Source: github.com/eternityspring/shuohao-skills (clone at /tmp/shuohao-skills), Apache-2.0, © 2026 烁皓 (eternityspring). Extracted 2026-08-27 for WD-4k56 follow-up (parent WD-j9nx).

## Mechanism (our terms)

The 827-line CHANGELOG.md is not a release log; it is a **decision-record corpus**. Each of its 27 entries (2026-08-06 → 08-21, repo lifespan 15 days, ~2 releases/day) documents: the observed failure (often verbatim from production or an external issue), the root-cause analysis, the chosen fix, the alternatives rejected AND WHY, and measured evidence for every threshold. Mined decision records, in our terms:

### A. Thresholds are measured, never guessed
- Voice-prompt 400-char cap: same character rewritten as 230-char param string vs 500-char prose — the compact form "明显更好"; threshold placed between good samples (218-245) and bad prose (490-514) (CHANGELOG:105, 1.10.0).
- Distinctness gate 75% Jaccard: samples pairwise max 39%, lazy variant 98% — "中间余量极大" (:136 profile-pass; CHANGELOG:216-251).
- Sheet deliberately NOT checked: real characters share ~63% of the fixed layout text — a gate there would false-positive; "误拦的门比没有门更糟——门的信用比数量重要" (:140; :355-356). This phrase (a false-blocking gate is worse than no gate; a gate's credibility matters more than its count) recurs at least 5× and is the repo's central gate-design axiom.

### B. Gate vs rule vs example — a three-tier escalation ladder for lessons
When a production failure appears, they decide explicitly which tier absorbs it (novel-script 1.1.1, CHANGELOG:384-398): (1) judgeable → hard rule in the pass doc (motion-in-cold-open); (2) semantic/ungateable → craft rule + reasoning, NO gate (keyword scans "两头漏" — leak both ways); (3) example-as-norm — the strongest soft constraint: fix the bundled sample so every instance demonstrates the rule ("样例即规范"). Position-checkable sub-cases DO get gates (hookBeat in first 3 beats). Same triage for voice: quoted-dialogue gets a gate (cleanly judgeable); metaphor/performance/branching do not (:103 — keyword scan would flag "说话时"/"低音区" which merely contain the characters 时/区).

### C. "说明给人读，认领给机器查" — declarations vs claims
Hooks had "descriptions" but no claim, so episodes drifted. Fix: `hookBeat: [scene, beat]` CLAIMS the hook's location; the gate checks the claim. General pattern: make every soft intention a machine-checkable claim field (:482-500, novel-script 1.1.0 — "衔接从此是门不是自觉").

### D. Fix the ambiguity, don't label it (see language-split-contract.md)
voice.promptLocal deleted because users copied the wrong button; "消除歧义优于解释歧义" (:147-189).

### E. Judgment/execution separation
Merge candidates: code proposes, model judges, code applies deterministically (:460-480). Selftest fixes: test the invariant, not the string ("测的是…这个不变量本身", :180-183).

### F. Skip loudly, never silently
Every optional-input gate prints an explicit SKIP reason; optional fields skip gates that then still count in the total ("跳过不等于少一道门", :71).

### G. Anti-eval-set discipline (novel-storyboard 1.3.0, :190-215)
Gate failures now APPEND to `.gates.jsonl` (run record + per-failure lines); `stats` answers: which gate fires most (fix the rule's wording), which never fires (dead gate or internalized), what failure details look like (ungated patterns discoverable only by human reading). They explicitly took only half of SkillOpt's "frozen trainable state" idea: evidence accumulation yes, automated doc-rewriting no — "没有评测集的自动改文档就是瞎改" (auto-editing docs without an eval set is blind editing).

### H. Structural decisions with stated tradeoffs
- Model writes JSON only; Markdown/report/asset-lists computed by scripts ("四件模型写、一件算出来", :631-633). Core claim: "checklist 交给模型自觉是靠不住的" — checklists delegated to model self-discipline are unreliable (the repo's founding thesis, novel-outline 1.0.0).
- Style presets swap WHOLE (render/surface/lighting/negative/tags), never mix; the two presets have near-OPPOSITE negatives ("realistic 绝不能禁 photorealistic，ghibli 必须禁", :694-722).
- Backward compat by design: new optional field → existing artifacts "一份都不会红", selftest asserts the skip behavior (:71).

## File:line references (into /tmp/shuohao-skills)

- `CHANGELOG.md:3-45` — report assembler entry (scope-prefix CSS, document-Proxy isolation; three pitfalls each with a selftest assertion)
- `:46-79` — props added to outline; refs gate extension; "存量大纲一份都不会红"
- `:147-189` — voice entry (D, A, B all in one entry)
- `:190-215` — gate-log/stats entry (G)
- `:216-251` — distinctness gate (A) + CRLF false-failure fix (E: reproduce→isolate→verify: "本地把样例转成 CRLF 复现了报告里的失败")
- `:271-363` — shot-recipes entry: completeness-as-gate (coverage domains linted; "『这个库覆盖全了运镜』从此是查出来的，不是谁说的"), when-NOT-to-use sections machine-checked, phrase-vs-word collision avoidance, "不装繁荣" (listing never-used cards rather than faking prosperity)
- `:384-398` — the three-tier ladder (B)
- `:400-458` — storyboard 1.0.0 (C applied to seconds/prompt reconciliation)
- `:482-500` — hookBeat claim-gate (C)
- `:579-627` — outline 1.0.0 founding thesis (H)
- `:694-722` — style preset opposition

## Verbatim key excerpts

```
<!-- excerpt lightly normalized: whitespace only -->text
// :389-391 (novel-script 1.1.1, tier ladder)
**门不动**：hookBeat 位置门照旧；「有没有运动」是语义判断，关键词扫描两头漏，误拦的门比没有门更糟——门的信用比数量重要
// :493-495 (novel-script 1.1.0)
**说明给人读，认领给机器查**，衔接从此是门不是自觉。
// :207-210 (novel-storyboard 1.3.0)
它最硬的纪律是「改动只有在验证分提高时才被接受」，那需要一套评测集……没有评测集的自动改文档就是瞎改
// :631-632 (novel-outline 1.0.0)
**核心主张：checklist 交给模型自觉是靠不住的**
```

## RECOMMENDATION vs SGFLIX bible pipeline / wangp-dspy / X-content

**ADOPT**
- The decision-record CHANGELOG format for wangp-dspy and the SGFLIX pipeline skills: every gate/threshold we add records the measured evidence (ours: 3090 QC pass rates, VLM reject rates) and the rejected alternative. Our skills currently state rules without provenance; this format turns each skill into its own design history.
- The gate-vs-rule-vs-example triage as the explicit rubric when a QC failure recurs in dogfood/VLM-curator loops: first ask "is this deterministically judgeable?" — if not, fix the sample/exemplar, don't build a keyword gate. (Our VLM QC gates risk exactly the 误拦 failure mode.)
- Claim-fields (hookBeat pattern) for DSPy pipeline outputs: soft narrative intents become `[scene, beat]` claims that a validator checks — directly strengthens our beat-grid/lyric-boundary discipline (cuts must land on phrase boundaries → claimable, checkable).
- Gate-fire logging (.gates.jsonl + stats) on wangp-dspy validators: which prompt rule fires most tells us which rule wording to rewrite.

**ADAPT**
- Eval-set discipline: we actually HAVE QC signal (modelscope VLM verdicts) — the "no eval set" caveat doesn't bind us as tightly; a small GEPA-style scored set could justify the auto-accept-if-score-improves half they rejected. Adapt with care.

**PASS**
- The specific incident history (Windows CRLF, Safari blob URLs, CSS scoping) — good reading, not portable obligations.
