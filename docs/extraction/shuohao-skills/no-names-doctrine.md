# No-Names-in-Image-Prompts Doctrine — extraction from shuohao-skills

Source: github.com/eternityspring/shuohao-skills (clone at /tmp/shuohao-skills), Apache-2.0, © 2026 烁皓 (eternityspring). Extracted 2026-08-27 for WD-4k56 follow-up (parent WD-j9nx).

## Mechanism (our terms)

**The rule:** character names, aliases, author names, and work titles are absolutely forbidden in image prompts (character `image.prompt` / `image.promptLocal` / `image.sheet`, scene prompts, prop prompts, storyboard-image prompts, and H3 shot descriptions). Reason: image models are heavily biased toward names they recognize — they will draw *their memory of* that character, not yours. And it is gated: `prompt-no-names` is a validate gate across novel-art and novel-storyboard; with `--cast` it also catches **aliases**; dialogue `<d>` blocks are the only exempt zone (storyboard-pass.md:17).

**The doctrine's two halves.** Rule 3 (profile-pass.md:28) bans the name; rule 4 (profile-pass.md:30-44) is "the other half of rule 3": once you cannot name the person, identity must be carried by explicit description — ethnicity/era/region **must** be inferred from the source text and written concretely into the prompt, otherwise the image model defaults to a contemporary Western white person ("民国的老船夫会出成一个穿工装的美国老头"). The specificity table (East Asian Han features / early 20th century Republican-era China / coarse indigo cotton tunic, southern Chinese river town — not "an old man", not "historical", not "traditional clothing") is the operational form.

**Key subtleties:**
- Identity cues come from the SOURCE, not the report language: "报告出成日文不代表人物是日本人——`lang` 管的是谁来读，不是故事发生在哪" (profile-pass.md:42).
- In storyboard prompts, use generic identity phrases ("an old ferryman", "a young woman in a plain qipao"); names appear only inside `<d>` dialogue tags (storyboard-pass.md:17).
- The name-ban generalizes to any proper noun the model might "know": scene/prop prompts also ban author and work names (scene-pass.md:23, prop-pass.md:31) — "图像模型会把它认识的东西画进去".
- Enforcement is deterministic string matching against the cast list; missing `--cast` skips loudly rather than silently (CHANGELOG novel-art 1.0.0 entry, gate list).

## File:line references (into /tmp/shuohao-skills)

- `skills/novel-characters/references/profile-pass.md:28` — rule 3, the core prohibition
- `:30-44` — rule 4, the descriptive complement; specificity table :36-40; source-not-lang :42; inferred content marked in persona but NEVER in the prompt ("`(inferred)` 混进去会被画进画面", :44)
- `skills/novel-art/references/scene-pass.md:23` — scene prompts: never character/author/work names
- `skills/novel-art/references/prop-pass.md:31` — prop prompts: same ban, one line
- `skills/novel-storyboard/references/storyboard-pass.md:17` — generic identity in shot prompts; names only in `<d>`
- `CHANGELOG.md:579-627` (novel-outline 1.0.0 gate list) and `CHANGELOG.md:534-577` (novel-art 1.0.0: "不含角色名（`--cast` 才查，不给就明说跳过）")
- `CHANGELOG.md:400-458` (novel-storyboard 1.0.0: 16 gates include "不含角色名（别名也拦，台词块除外）")

## Verbatim key excerpts

```text
// profile-pass.md:28
**`image.prompt` / `image.promptLocal` / `image.sheet` 里绝对不许出现角色名、别名、作者名、作品名。**
图像模型对这些偏见极重，会画成它记忆里的角色而不是你的角色。描述这个人，不要叫他的名字。
// profile-pass.md:32
名字不能写，那这个人长什么样、是哪儿的人，就只能靠描述交代。**不写死，图像模型默认画当代西方白人**
// profile-pass.md:44
推断出来的内容按第 1 条标注……**提示词里不标注**——那是给机器读的，`(inferred)` 混进去会被画进画面。
// storyboard-pass.md:17
**提示词禁角色名。** 分镜图和 H3 描述都用通用身份（an old ferryman、a young woman in a plain qipao），人名只许出现在 `<d>` 台词里。
```

## RECOMMENDATION vs SGFLIX bible pipeline / wangp-dspy / X-content

**ADOPT**
- Directly for wangp-dspy / H3 / FLUX3 prompt generation: our multi-ref shots reference character sheets by IMAGE, so names in the text prompt are pure poison — the model may drag in a celebrity/public figure it associates with the name. Add a no-proper-nouns gate (against the entity registry, aliases included) to any prompt QA step. This is cheap, deterministic, and matches the observed failure mode.
- The "second half": for invented SGFLIX characters, identity markers (ethnicity/era/region-equivalent world markers) must be explicit canon in the character bible, not left to the model's Western-default prior. Our kaiju/Ektachrome worlds default to "generic American city" without it.
- Never let provenance markers (`(inferred)` or our QC tags) leak into generation prompts.

**ADAPT**
- Alias catching: build the ban list from the SGFLIX entity registry (names + aliases + handles). For X-content: profile names/handles of real people must NEVER enter image prompts either — same doctrine, stronger reason (likeness leakage).

**PASS**
- Nothing to pass; this is the most portable rule in the repo.
