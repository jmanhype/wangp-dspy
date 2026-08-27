# Character & Roster Method — extraction from shuohao-skills

Source: github.com/eternityspring/shuohao-skills (clone at /tmp/shuohao-skills), Apache-2.0, © 2026 烁皓 (eternityspring). Extracted 2026-08-27 for WD-4k56 follow-up (parent WD-j9nx).

Covers the two-pass character system: `roster-pass.md` (scan) + `profile-pass.md` (card), plus the cross-pass handoff design. Language-split and no-names rules are extracted separately (language-split-contract.md, no-names-doctrine.md); this doc covers the character methodology itself.

## Mechanism (our terms)

Two LLM traversals with a strict information firewall between them:

**Pass 1 — roster scan** (`roster-pass.md`): one traversal per text chunk over the raw novel. Output: minimal JSON entries `{name, aliases, note, quotes}`. The critical design fact: **the second pass never sees the source text** — everything downstream knows about a character is what pass 1 wrote in `note`. Hence the rule that note must be dense (appearance, speech manner, actions). This is a deliberate compaction contract: it bounds pass-2 context and makes the alias merge deterministic.

**Between passes — alias merge** (from CHANGELOG 2026-08-13, novel-characters 1.7.0): exact-match merge runs deterministically in code; residuals ("陆" ⊂ "陆行远" substring containment) are emitted as `mergeCandidates`; the MODEL reviews and writes `merges.json`; `merge --apply` lands it deterministically. "判断留给模型，落地回到脚本——谁擅长什么谁干什么" (judgment to the model, execution back to the script). Chunking grew 14k→40k chars purely because fewer chunks = fewer seams = fewer missed merges.

**Pass 2 — profile cards** (`profile-pass.md`): one card per merged character. Input block is fixed (Language, Character, aliases, other cast names, numbered observations, verbatim-quote block). Eight hard rules (see pass-methodology-outline.md §3 for the summary): observation-grounding with inferred markers; verbatim-only evidence; no names in image prompts; ethnicity/era/region inferred from source text into prompts; expressive-illustration prompt spec (semi-realistic painterly, realism-through-imperfection: pores, asymmetry, expression-muscle-aligned wrinkles; do NOT negative-prompt photorealistic); 16:9 three-zone character sheet with zoned lighting (left bust: directional key + AO for volume; right views: flat orthographic for cutout/measurement — "LIGHTING IN THE LEFT ZONE ONLY" vs "flat even orthographic"); voice.prompt as a static instrument spec ≤400 chars (banned: literary metaphor, performance direction, conditional branching, quoted dialogue; fixed parameter order: age/gender, timbre, pitch, support, dynamic range, volume, pace, inflection, accent, default emotion); intra-cast distinctness gate (pairwise word-Jaccard ≤75% on image+voice prompts; sheet deliberately exempt at ~63% baseline similarity).

**Key craft decisions in rule 5-6 worth naming:**
- "真实感来自不完美，不是细节量" — realism from imperfection, not detail count (asymmetry > more pores).
- The negative-prompt inversion: banning `photorealistic` while demanding realism is self-contradiction; ban the *fakeness* instead (waxy skin, symmetric face, dead eyes).
- Sheet proportions are the likeliest failure: "PROPORTIONS ARE CRITICAL", figures never stretched ("the detail studies give way, not the figures"), one face per sheet.
- Realism surfaces are character-skill-only: environment skill explicitly forbids importing skin pores into scenes (scene-pass.md:29).

## File:line references (into /tmp/shuohao-skills)

- `skills/novel-characters/references/roster-pass.md:7-12` — scan rules; :10 the firewall ("后一趟看不到原文"); :11 verbatim-quote rules (no translation, no stitching across narration)
- `skills/novel-characters/references/profile-pass.md:142-156` — the fixed input block (input contract)
- `:24-44` — rules 1-4 (grounding/evidence/names/ethnicity-era-region)
- `:46-55` — rule 5 prompt shape + negative-prompt inversion (:55)
- `:57-90` — rule 6 sheet layout, ASCII diagram :59-68, zoned lighting :78-82, proportions :84, one-face :88, required phrases :90
- `:92-132` — rule 7 voice (banned table :96-101, engine table :126-131, param template :109-118)
- `:134-140` — rule 8 distinctness gate + measured thresholds (:136)
- `CHANGELOG.md:460-480` — merge review / assemble / 40k chunking rationale
- `CHANGELOG.md:216-251` — issue #9 → distinctness gate; sheet deliberately un-gated (:136 profile-pass / changelog)
- `CHANGELOG.md:253-269` — PR #7 cross-character style consistency gate (normalize `image.style`, >1 value fails, names offenders)

## Verbatim key excerpts

```text
// roster-pass.md:10
`note` 要密集：长什么样、怎么说话、做了什么。**后一趟看不到原文，只看得到你写的 note**
// profile-pass.md:55
`negativePrompt` **不要写 `photorealistic` / `3d render`**——一边要真实感一边禁真实感是自相矛盾的。该禁的是「假」
// profile-pass.md:84
**比例是这个版面最容易崩的地方。** ……**绝不能为了塞下别的东西把人物拉伸或压扁**
// profile-pass.md:136
阈值是量出来的：自带样例四个角色两两最高 39%，而「只改年龄与衣服颜色」的雷同用例是 98%，中间余量极大。
// CHANGELOG.md:467-469
判断留给模型，落地回到脚本——谁擅长什么谁干什么
```

## RECOMMENDATION vs SGFLIX bible pipeline / wangp-dspy / X-content

**ADOPT**
- The scan→merge→card structure maps 1:1 onto SGFLIX character bibles: our IDENTITY_LOCK bibles ARE profile cards. Adopt (a) the dense-note compaction contract ("the next stage sees only your note") as the bible→handoff→generation firewall discipline — guarantees generation prompts are self-contained; (b) mergeCandidates pattern: code proposes, model judges, code applies — for entity-registry dedupe across multi-episode casts.
- Voice rule 7 wholesale for any TTS casting step in the music-video pipeline: static-instrument spec, compact param string, 4 banned categories, engine-compatibility table (directly matches our MiniMax/Suno/Qwen3-TTS reality).
- Pairwise distinctness across a batch of character prompts before burning generation budget on 3090.

**ADAPT**
- Zoned-lighting character sheet: we generate character refs via Ideogram4 + LoRA, not $imagegen; keep the three-zone layout and "one face per sheet" but our prompt style tokens replace their semi-realistic boilerplate.
- Ethnicity/era/region rule: SGFLIX worlds are invented, not adapted — the rule becomes "world-bible canon must state origin/era markers explicitly" rather than "infer from source."

**PASS**
- Two-pass scan of a long novel text — no long-form source in our loops.
- Report UI specifics (sprite-slice thumbnails, relationship graph) — no artifact for them to render in our stack.
