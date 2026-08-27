# Pass Methodology — extraction from shuohao-skills

Source: github.com/eternityspring/shuohao-skills (clone at /tmp/shuohao-skills), Apache-2.0, © 2026 烁皓 (eternityspring). Extracted 2026-08-27 for WD-4k56 follow-up (parent WD-j9nx).

Covers the seven craft docs (`references/*-pass.md`) not taken by WD-4k56 (which took gate-array / H3-contract / export-pack / assembler).

## Mechanism (our terms)

Each pipeline stage ships a **pass doc**: a short prompt-shaped instruction file that defines ONE LLM traversal of the artifact, with (a) hard rules that map 1:1 to deterministic gates, (b) craft/"feel" rules explicitly marked as un-gateable, and (c) a fixed input block (seed + upstream artifacts + sibling-batch names). The pass docs are the prompt-layer half of the gate-array pattern: every gate in the .mjs has a matching numbered rule in the pass doc, and every rule the author decided NOT to gate says why ("误拦的门比没有门更糟" — a gate that false-positives is worse than no gate).

### 1. outline-pass — adaptation economics (outline-pass.md, 36 lines)

The order IS the method (line 5: "顺序就是方法"):

1. **Cut lines** (砍线): short-drama fits one main plotline + at most one subplot. Every cut goes into `adaptation.cut` **with a why**. If `adaptMode` is not faithful and you cut nothing, validate blocks (L7).
2. **Merge by function** (合人): characters with duplicate function merge into one face; merges recorded in `characters[].from` ←. Then tiering: lead 1–5, named support ≤10, functional ≤10. Functional characters "占脸不占名" — name is a label ("急诊医生"), no arc. Anonymous background people don't enter the table (L8).
3. **Cap scenes**: 4 + ⌈episodes/10⌉ clamped 5–15 (6 eps→5, 60 eps→10). Explicitly a relaxed AI-era budget: scenes are generated, extra sets buy visual variety. Once-only source scenes must be cut or given a `reusePlan` (L9).
4. **Space payoffs** (排爽点): place major beats first, fill minors between. Hard rules: adjacent gap ≤3 eps, no vacuum at start/end, earliest major not in the final ep. Beat `type` follows genre (L10).
5. **Select props LAST** — deliberately after payoffs: the test for a narrative prop is "which payoff does it carry"; until payoffs are fixed you can't tell prop from set dressing. Cap 8, each needs `function` + `beatIds`. One-question test (L13): "它坏了、丢了、被换掉，剧情会不会塌" — if the plot doesn't collapse, it's scenery, not a prop.

Decision sentences: `adaptation.cutNote` ("this means: the story ends at…") and `mergeNote` (why the lead group was chosen — who has a complete arc) — these two sentences headline the report's "key decisions" block shown to the user for sign-off (L17).

**Two-round skeleton validation** (L19-26): round 1 "fast version" fills all four blocks, passes `validate --stage beats`, stops, and goes to the USER for sign-off — which lines cut / which people merged / where the majors land are the three things that invalidate everything downstream. Round 2 refines after feedback and re-validates. Rationale (L26): the fast round is cheap — an error costs one skeleton, not 60 episode synopses.

Every key keep/cut decision carries `evidence` (verbatim source excerpt, L15).

### 2. roster-pass — scan pass (roster-pass.md, 29 lines)

First traversal over raw text: extract every character, JSON only. Rules: alias/title/formal-name merge into one entry (`name` = most-used form); descriptive labels for unnamed individuals; **don't invent characters** — places/orgs/animals don't count unless they act like one; `note` must be dense because **the next pass can't see the source text, only your note** (L10); `quotes` are verbatim, source-language, never translated, never stitching dialogue interrupted by narration (L11).

### 3. profile-pass — card pass (profile-pass.md, 157 lines; the richest doc)

Rules 1–8: observation-only + inferred-marking (rule 1); evidence verbatim-only (rule 2); no-names-in-prompts (rule 3, → no-names-doctrine.md); ethnicity/era/region must be inferred from source and written explicitly into prompts (rule 4, the "other half" of rule 3: if you can't name him, you must describe him — otherwise image models default to "contemporary Western white person"); single expressive-illustration prompt spec (rule 5); 16:9 three-zone character sheet layout with zoned lighting (rule 6); voice.prompt as static instrument description with 4 banned categories and a 400-char compact-parameter-string shape (rule 7, engine-compatibility table included); intra-cast distinctness now gated at 75% pairwise word-Jaccard (rule 8, threshold measured: samples max 39%, lazy-rewrite case 98%).

### 4. script-pass — episode writing (script-pass.md, 48 lines)

8 hard rules: duration budget before everything (4.5 chars/sec dialogue, 2.5 s/action-beat, ±15%); single line ≤35 chars; speaker-voice fidelity ("盖着名字也认得出是谁在说话"); **action beats = common actions only** — the AI-video lifeline rule: video models only act what they've seen millions of times (boarding, sitting, handing, nodding = safe; pole-blocks-crate physics, micro-expressions, inch-scale displacements = will break); every scene ≥1 action beat; hook is beat 1 **in motion** (cold open: ✗ static close-up of suitcase ✗ running through fog holding suitcase ✓); last beat must be a cliff; every claimed payoff must have continuous beats enacting it ("爆点是演出来的，不是梗概里说说").

**Single-point-edit discipline** (L24-27): after changing one beat, re-read three (±1 beat) checking continuous state — position / prop-in-hand / who's-present — "改的时候空间状态不在你脑子里——连读是把状态找回来的唯一办法". Also: change picture → change scene-scape (storyboard soundscape) in the same edit.

Failure-pattern table (L37-48): radio-drama, literary-disease (precision action prose), dead-opening frame, spatial jump, padding, speech-making, omniscience, flat ending.

### 5. scene-pass / prop-pass / sheet (novel-art)

- scene-pass: scenes are **environment assets generated dozens of times that must look identical**, not locations. Summary = design intent not floor plan; anchors must be "可画、可认、可核对" (paintable, recognizable, checkable — "陈旧的氛围" is an adjective, not an anchor); lighting states derived backwards from episodes, not a default day/night set; prompts always English, always empty scene; styles taken whole, never mixed; prefer `variantOf` over a new scene ("每多一个独立环境就多一份一致性维护"); environment realism comes from **worn materials** (chipped paint, patina), NOT the character skill's skin-surface tricks.
- prop-pass: selection BEFORE filling — three simultaneous conditions (has close-up, recurs across episodes, carries plot), 3–8 props; three-tier table (narrative prop / set dressing / one-shot hand prop) routes each object; anchors survive close-up; state variants derive from plot arc; **scale must be written into the prompt** (handheld/tabletop/furniture scale — "AI 把手持道具画成家具尺寸是高频事故", gated); white background, no people, no hands (hands = most common contamination, gated).
- sheet.md: L-shaped detail-border layout for environment/prop sheets; "one space per sheet, THE SPACE MUST BE IDENTICAL ACROSS ALL PANELS"; variant scenes image from the **mother scene's generated image as reference** + "keep the structure, materials and wear identical to the reference image".

### 6. storyboard-pass — segmentation then cutting (storyboard-pass.md, 51 lines)

Segment = one generation call, ≤15 s, never crosses scenes; cut = 2–5 s (hard gate), aim 3 s; storyboard image per cut, primary pinned at 0.00 s. Rules: claim intervals are the foundation (continuous, non-overlapping, complete); **seconds are an order, not an estimate** — changing cut seconds must sync `h3Prompt` alignment text, validate does verbatim reconciliation; dialogue must fit its cut (4.4 s line → 5 s cut); framing phrases in the image prompt, camera-move vocabulary (H3 official words) in its own [Shot k] section; no character names in prompts (generic identity "an old ferryman"). Feel rules (ungated): 3-second rhythm, shot/reverse-shot for dialogue, entrance trio (moving subject → wide establishing → key insert), reaction shots are free acting, action-matches-action cuts, last cut of each segment keeps a hook, camera restraint. Reference-image discipline: always mount scene sheet + every on-screen character sheet + prop sheet; **when prompt and reference conflict, the model obeys the reference** — so the prompt should specify composition, current position state, and pose, delegating looks/materials to the sheets.

## File:line references (into /tmp/shuohao-skills)

- `skills/novel-outline/references/outline-pass.md` — full file (36 lines); scene cap L9, payoff spacing L10, props-after-payoffs L11-13, evidence L15, decision notes L17, two-round L19-26
- `skills/novel-characters/references/roster-pass.md` — L7-12 rules, L10 "后一趟看不到原文", L11 verbatim quotes
- `skills/novel-characters/references/profile-pass.md` — L24 rule 1, L26 rule 2, L28 rule 3, L30-44 rule 4, L46-55 rule 5, L57-90 rule 6 (sheet layout + zoned lighting), L92-132 rule 7 (voice), L134-140 rule 8 (distinctness gate)
- `skills/novel-script/references/script-pass.md` — L7 duration budget, L10-18 common-actions table, L20 motion-hook, L24-27 edit discipline, L37-48 failure table
- `skills/novel-art/references/scene-pass.md` — L5-13 asset framing, L19 anchors, L23 empty-scene English, L27 variantOf, L29 worn materials
- `skills/novel-art/references/prop-pass.md` — L7-15 selection, L25 scale gate, L27 no-hands
- `skills/novel-art/references/sheet.md` — L24 nothing-invented, L35 one space per sheet, L51 variant-from-mother-image
- `skills/novel-storyboard/references/storyboard-pass.md` — L7-9 segmentation, L13 claims, L14 seconds-are-an-order, L17 no names, L38 prompt-vs-reference conflict

## Verbatim key excerpts

```text
// outline-pass.md:11
**排在爽点之后不是随便排的**——叙事道具的判据是「它托起哪个爽点」
// outline-pass.md:13
一件东西该不该进这张表，问一句就够了：它坏了、丢了、被换掉，剧情会不会塌。
// outline-pass.md:26
快版的意义是便宜——错了只损失一轮骨架，不是 60 集梗概。
// roster-pass.md:10
**后一趟看不到原文，只看得到你写的 note**，所以细节必须落在 note 里。
// script-pass.md:11
**常见动作是 AI 生成的生命线**——这条戏最终是视频模型演的，它只会演它见过千万次的动作
// script-pass.md:26
改一拍，连读三拍。……写作时空间状态在你脑子里，改的时候它不在——连读是把状态找回来的唯一办法。
// storyboard-pass.md:38
提示词与参考图冲突时，模型听参考图的——所以提示词专心写构图、**此刻的位置状态**……长相材质交给参考图。
```

## RECOMMENDATION vs SGFLIX bible pipeline / wangp-dspy / X-content

**ADOPT**
- Two-round skeleton sign-off for the SGFLIX bible pipeline: our character bibles (8-page, IDENTITY_LOCK) are the expensive artifact — a cheap round-1 "cut/merge/payoff" skeleton that the user signs off before any bible pages are written directly prevents "narrative>perfection" wasted batches. Highest-value single idea in this set.
- Cut-with-reasons + merge-by-function as explicit fields (`cut`+why, `from` ←, `cutNote`/`mergeNote`) in any adaptation/repurposing layer.
- Props-after-payoffs ordering + the plot-collapse test, for prop sheets feeding multi-ref generation.
- "Common actions only" rule + the action-judgment table, verbatim into wangp-dspy shot/H3-prompt generation — this is the single best anti-mush rule for WanGP H3 we've seen stated formally, and it matches our 3090 production experience.
- Change-one-reread-three edit discipline in any DSPy/dogfood prompt that post-edits shot lists (position/prop-in-hand/present-cast as continuous state).

**ADAPT**
- Scene cap formula 4+⌈eps/10⌉ clamped 5–15: adapt the *idea* (asset budget scales with episode count, explicitly relaxed for AI) rather than the numbers — SGFLIX shorts are 20 s capped with far fewer scenes.
- Pairwise-distinctness rule 8: adopt the gate concept for our character prompt batches, but our prompts embed LoRA/style tokens; re-measure the threshold on our own corpus before setting it.
- 3-second-cut rhythm: our 20 s cap and music-video beat grids already dictate cut points; adopt as default feel only when the beat grid is silent.

**PASS**
- Episode-count machinery (60-ep volumes, chapter chunking, hookWindow) — wrong regime for us.
- Two-pass character scan (roster→profile) for X-content: our X work has no long source text to scan.
