# Common-actions gate — anti-mush rule for shot/action text

Adopted from the shuohao-skills script-pass common-actions rule:
`docs/extraction/shuohao-skills/pass-methodology-outline.md`
**section 4** (script-pass **L10-18** — the common-actions table) and
`docs/extraction/shuohao-skills/RUBRIC-methodology-extraction.md`
**A4.2**.

Doctrine (verbatim judgment test): **"is this action common in
real-life video?"** Video models only act what they've seen millions
of times — walking, sitting, handing, nodding are safe; **precise
physics interaction, micro-expression direction, and inch-scale
displacement will break** into mush.

## Registry schema (`datasets/common-actions.json`)

```
{
  "safe":  ["walking", "sitting", ...],          # documentation-only
  "risky": [
    {"id": "physics-pole-blocks",
     "pattern": "(pole|beam|plank|rod) blocks",  # regex body
     "category": "physics",                      # see below
     "rationale": "... citing the doctrine ..."}
  ]
}
```

- `category` ∈ `physics | micro_expression | fine_displacement`.
- `pattern` is matched word-boundary anchored, case-insensitive
  (same `_compile` style as gates/no_names_gate.py).
- Every entry carries a `rationale` citing the doctrine.

## Measure-then-threshold stance

The seed RISKY set starts SMALL (9 patterns, 3 per category — the
examples named in the story). **Each future addition must cite the
observed 3090 mush case** (the failing render) in its rationale —
the list grows from evidence, not from imagination.

## False-positive philosophy

**The gate only rejects known-bad patterns; SAFE-list presence is
NOT required** — a shot may use any common action not in the seed
list. This mirrors the no-names gate's exact-match-only stance: **a
mis-blocking gate is worse than no gate.** Word-boundary anchoring
prevents risky substrings inside safe words from firing.

## Wiring

`RenderBrief.__post_init__` → `_reject_risky_actions` (alongside
`_reject_meta_hints` / `_reject_registry_names`): a risky pattern in
any brief section raises `ValueError`, caught by
`PromptDirector.forward`'s existing rejection path. The gate is
**ALWAYS ACTIVE** — patterns are bundled with the repo
(`datasets/common-actions.json`), unlike the no-names registry which
is per-production context and skips loudly when absent. No disable
knob exists; adding one requires an explicit documented decision.

## CLI

`python scripts/check_common_actions.py <file-or-text>` — per-hit
report with category + pattern id; exit 0 clean / 1 violations /
2 usage error (incl. empty-text loud skip).
