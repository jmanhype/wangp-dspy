# Gate-Array Pattern — extraction from shuohao-skills

Source: github.com/eternityspring/shuohao-skills (clone at /tmp/shuohao-skills), Apache-2.0, © 2026 烁皓 (eternityspring). Extracted 2026-08-27 for WD-4k56 (parent WD-j9nx).

## Mechanism (our terms)

A single pure function `gateReport(board, ctx)` computes ALL quality checks at once and returns a flat array of gate objects:

```js
{ id, label, ok, detail }
```

- `id` — stable machine key (`'coverage'`, `'h3-structure'`, `'shot-recipe'`, …)
- `label` — human sentence including the computed threshold (e.g. `每段 0 < 总秒数 ≤ 10`)
- `ok` — boolean, never throws
- `detail` — either the joined failure list (`bad.coverage.join('；')`) or an explicit SKIP reason string

Key design decisions, in our terms:

1. **One source of truth.** validate, the HTML report, the CLI log, and the gate-log all call the same `gateReport()`. No check exists anywhere else. Consequence: a gate can never disagree with the report, and adding a gate upgrades every consumer for free.
2. **Collect-then-report.** All checks first *accumulate* failures into a `bad` map keyed by gate id; the `add(...)` calls at the end turn buckets into gate objects. This keeps "what is checked" (loop bodies) separate from "what is reported" (final add block).
3. **Optional inputs skip loudly, not silently.** Missing `script.json` → `detail = '未提供 script.json，本门跳过（视为通过）'` with `ok: true`. The pass is visible in the report, not an invisible default.
4. **Deterministic, zero-model.** Every gate is string/number logic over the artifact JSON — no LLM calls, so the whole battery runs in the selftest for free and cannot flake.
5. **Id-keyed i18n at display time only.** Gate logic and Chinese diagnostics never move; English UI maps `id → label` and numbers from the Chinese label are substituted into `{0}/{1}` placeholders at render (GATE_LABELS_EN, novel-storyboard.mjs:827-863).

## File:line references (into /tmp/shuohao-skills)

- `skills/novel-storyboard/scripts/novel-storyboard.mjs:419-676` — `gateReport()` (17 gates)
- `:421` — the `add(id, label, ok, detail)` helper that defines the object shape
- `:426-430` — the `bad` failure-bucket map
- `:431-433` — optional recipe library mounted via ctx; whole gate skips if absent
- `:646-649` — explicit SKIP / NO_RECIPE detail strings
- `:651-673` — the final `add()` block: every gate declared with its label + joined detail
- `:682-710` — `validateStoryboard()` (schema-level checks, separate from quality gates)
- `:722` — validate reuses `gateReport` output; `:1110`, `:1701`, `:1728` — report/CLI reuse it
- `skills/novel-storyboard/scripts/selftest.mjs` — every gate has a break-case test ("证明它真的会拦，不是一个永远为真的假测试")

## Verbatim key excerpts

```js
// novel-storyboard.mjs:419-421
export function gateReport(board, ctx = {}) {
  const gates = [];
  const add = (id, label, ok, detail = '') => gates.push({ id, label, ok, detail });
```

```js
// novel-storyboard.mjs:651 — one declared gate
add('coverage', '剧本节拍被恰好一次、按顺序、连续认领（分镜级）',
    bad.coverage.length === 0, script ? bad.coverage.join('；') : SKIP_SCRIPT);
```

```js
// novel-storyboard.mjs:646 — loud skip
const SKIP_SCRIPT = '未提供 script.json，本门跳过（视为通过）';
```

## RECOMMENDATION: ADOPT

Rationale: wangp-dspy already runs Luna G1-G7 dataset gates and SGFLIX bible gates, but they live as ad-hoc checks scattered across scripts; unifying them as `{id,label,ok,detail}` arrays gives us (a) one report renderer, (b) free selftest break-cases per gate, (c) explicit skip semantics for optional inputs (exactly our "fail-honest" doctrine). Cost is low: the pattern is ~30 lines of convention, not a framework. Draft skill prepared at /tmp/gate-array-skill (SKILL.md + scripts/gate-array.mjs + scripts/selftest.mjs). Final adopt/adapt/pass call: reviewer.

Attribution: pattern extracted from shuohao-skills by eternityspring (烁皓), Apache-2.0. NOTICE file present in repo root.
