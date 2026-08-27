# Export Pack Spec — extraction from shuohao-skills

Source: github.com/eternityspring/shuohao-skills (clone at /tmp/shuohao-skills), Apache-2.0, © 2026 烁皓 (eternityspring). Extracted 2026-08-27 for WD-4k56.

## Mechanism (our terms)

`exportPack()` turns a validated storyboard into a *drop-in generation package*: one folder per segment, prompt file lying next to its images, plus a root manifest. Design points:

1. **Fixed layout per segment**: `<segId>/f1.png … fN.png` + `<segId>/prompt.md`. f1 is pinned to 0.00s (first frame / world reference); fN pinned to each cut's cumulative start.
2. **prompt.md is self-describing**: a header states which file is the first frame and which second each Picture pins to (`- Picture 2 = f2.png（钉 3.00 秒）`), then a `---` separator, then the h3Prompt **verbatim** — copy-paste the whole file into H3 and it works.
3. **Manifest per segment** at root: `{ segment, seconds, cuts, cutStarts, prompt, pictures, missing }`.
4. **Fail-honest image accounting**: `imageExists` is an injected predicate (default `() => false`); missing images are *listed in the manifest* and counted (`missingTotal`) rather than silently omitted or hard-failing the export.
5. **Pure function**: returns `{ files, manifest, missingTotal }` where files are `{path, content}` records; disk writes happen in the CLI layer only — the whole pack is unit-testable without touching the filesystem.

## File:line references

- `skills/novel-storyboard/scripts/novel-storyboard.mjs:760-800` — `exportPack()`
  - `:763-768` design comment: fixed production structure, pure function / CLI-layer disk writes
  - `:769` signature with injected `imageExists` predicate
  - `:778-783` prompt.md header construction (Picture→file→timestamp mapping + verbatim prompt below `---`)
  - `:784-795` manifest entry with `pictures`, `missing`, `cutStarts`
  - `:798-799` manifest.json emitted last; return value shape
- Consumer: `:1761` CLI calls it with `imageExists: (rel) => existsSync(resolve(rel))`

## Verbatim key excerpts

```js
// novel-storyboard.mjs:769, 785-786, 798-799
export function exportPack(board, script, { imageExists = () => false, dir = '.' } = {}) {
  ...
  const missing = pictures.filter((rel) => !imageExists(rel));
  missingTotal += missing.length;
  ...
  files.push({ path: `${prefix}manifest.json`, content: JSON.stringify(manifest, null, 2) + '\n' });
  return { files, manifest, missingTotal };
```

## RECOMMENDATION: ADAPT

Rationale: our wangp-h3-multishot packages are JSON blobs (shot list + prompt + paths) consumed by WanGP-side scripts; the shuohao pack is optimized for *human drag-and-drop into the H3 web UI* (prompt.md next to images, self-describing header). For machine consumption our JSON is fine; the two things worth adapting are (a) the **missing-image ledger in the manifest with a total** — we currently discover missing frames only at render time; (b) the **cutStarts echoed per manifest entry** so the render side can re-audit timestamps against the prompt contract independently. Full adoption (folder-per-segment + prompt.md) only pays off if we ever drive the H3 UI manually. Decision: reviewer.

Attribution: eternityspring (烁皓), shuohao-skills, Apache-2.0.
