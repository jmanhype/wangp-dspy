# H3 Prompt Field Contract — extraction from shuohao-skills

Source: github.com/eternityspring/shuohao-skills (clone at /tmp/shuohao-skills), Apache-2.0, © 2026 烁皓 (eternityspring). Methodology itself internalized from the MiniMax-H3 official prompting guide (I2VA / multi-image alignment mode). Extracted 2026-08-27 for WD-4k56.

## Mechanism (our terms)

The h3Prompt for each segment is a *derived* artifact: its structural skeleton is computed from the cut list (seconds per shot), and the quality gate audits the prompt **verbatim** against that computation. Anything the model was supposed to copy — alignment line, cut timestamps, dialogue text — is string-matched exactly; only prose fields are free.

Contract elements:

1. **Alignment first line, derived.** `Picture k (from Shot k) aligns with the X.XX-second mark` — the timestamps are the cumulative sum of preceding cut seconds (`cutStarts`), formatted `00:0X.XXX`. Gate fails if the prompt's first line does not start with the computed string.
2. **Three ordered fields.** `integrated_multimodal_description:` → `overall_soundscape:` → `non_diegetic_music:` (each `[Shot k]` on its own line, opening with its cut time). Gate checks field presence AND order via indexOf monotonicity.
3. **Dialogue blocks are punctuation-exact.** Each claimed script beat of kind `line` must appear as `<d>[lang] text</d>` with the text regex-escaped verbatim ("一个标点都不许动").
4. **Camera vocabulary is closed.** 20 official H3 camera terms; each cut's term must appear *inside its own `[Shot k]` slice* of the prompt — not just anywhere.
5. **Name ban in English mode.** Character names from outline/cast must not appear in the prompt body (models bias on English-context names); identity is anchored by the reference images instead.
6. **Soundscape is an action instruction.** What you write in `overall_soundscape` gets performed ("铜铃在撞击时炸响" → the video enacts the collision) — so it must be updated in lockstep with visual actions.
7. **Off-screen voice phrasing.** V.O. uses the official clause `says in an off-screen voiceover … while their lips remain completely closed` (zh: 以画外音说（唇形完全闭合）).
8. **Language split.** Default `promptLang:'en'`: full English except dialogue/lyrics/visible text (verbatim originals). `zh` mode swaps skeleton tokens; gates pick the token table by promptLang.

## File:line references

- `skills/novel-storyboard/references/h3-prompt.md:1-51` — the full contract doc (internalized official guide)
  - `:13-24` structure block; `:26` zh token table; `:32-33` camera rules; `:37-40` speaker/dialogue/V.O. rules; `:44-45` soundscape-as-action; `:48-51` keyframe anchoring
- `skills/novel-storyboard/scripts/novel-storyboard.mjs:469-497` — h3 structure + language gates
  - `:472-474` first-line verbatim audit (`h3AlignmentLine(cuts, promptLang)`)
  - `:476-478` field presence + order
  - `:482-485` per-cut timestamp marks must equal cumulative seconds
  - `:488-497` language purity (CJK outside `<d>`) + name ban
- `:499` `h3CutSlices` — prompt sliced per shot so camera terms are audited per-slice
- `:569-577` — dialogue-fit + verbatim `<d>` regex audit

## Verbatim key excerpts

```text
# h3-prompt.md:14
How the reference pictures align with the target video — Picture 1 (from Shot 1)
aligns with the 0.00-second mark of the target video; Picture 2 (from Shot 2)
aligns with the 3.00-second mark of the target video; ….
```

```js
// novel-storyboard.mjs:483-484 — timestamp marks must equal cumulative cut seconds
const mark = tk.cutMark(k, h3CutTime(starts[k - 1]));
if (h3.indexOf(mark, idx[0]) < 0) bad.h3s.push(`${sid} 缺「${mark}」——切点时刻必须等于前面分镜秒数的累计`);
```

## RECOMMENDATION: ADAPT (merge into wangp-h3-multishot)

Rationale: we already generate H3 multishot prompts (wangp-h3-multishot skill), but we do not machine-audit the alignment line, per-shot camera placement, or `<d>` verbatim dialogue against the cut grid. The auditable contract (items 1-4) is directly adoptable as post-generation gates on our shot lists; the language/name policies (5,8) should be evaluated against our pipeline (we sometimes want names in zh prompts). Soundscape-as-action and lip-closed V.O. phrasing fold into our prompt templates. Per story AC (c), this document is the reference doc to merge into the wangp-h3-multishot skill area — placement decision is the reviewer's.

Attribution: eternityspring (烁皓), Apache-2.0; underlying methodology from the MiniMax-H3 official prompting guide.
