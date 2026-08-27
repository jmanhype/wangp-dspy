# Report Assembler (scoped merge of stage reports) — extraction from shuohao-skills

Source: github.com/eternityspring/shuohao-skills (clone at /tmp/shuohao-skills), Apache-2.0, © 2026 烁皓 (eternityspring). Extracted 2026-08-27 for WD-4k56.

## Mechanism (our terms)

`scripts/report.mjs` merges five per-stage HTML reports (outline/characters/art/script/storyboard) into one single-page app with left-nav panes — **without importing any skill code**. It shells out to each skill's `render --html` and assembles the outputs. Stated benefits (report.mjs:6-10): skills stay untouched and independently runnable; loading logic lives once per skill; renderer changes propagate automatically.

Three collision classes, each solved non-invasively:

1. **CSS collisions** — `scopeCss(css, scope)`: hand-rolled brace-matching parser prefixes every selector with the pane id. Special cases: `:root/html/body` → replaced by the scope itself (custom properties land on the pane); `@keyframes/@font-face/...` kept whole; `@media/@supports/...` recursed; comma groups prefixed per-branch. Comments stripped first (a comment's comma can split a selector — measured bug).
2. **JS collisions** — `scopeJs(js, paneId, prefix)`: each report's script is wrapped in an IIFE whose `document` is a Proxy: `querySelector(All)` restricted to the pane root; `getElementById` auto-prepends the id prefix (so script id-strings need zero edits); everything else passes through bound. IIFE also isolates top-level `const` collisions across the five scripts.
3. **Image paths + id anchors** — `rebaseAssets` rewrites `src/data-img/url(...)` relative to the merged file's location (data:/absolute untouched; inline `url()` covered because character-report thumbnails hide there); `scopeHtml` prefixes `id=` and the attributes that reference ids (`href="#…"`, `data-pane`, `aria-controls`, `for`).

Purity: `splitDoc`/`scopeCss`/`scopeHtml`/`rebaseAssets`/`scopeJs`/`makePane` are pure string functions — the selftest feeds HTML strings directly, no subprocess needed. Zero dependencies; regex-based split is justified because all reports share one fixed document shape.

## File:line references

- `scripts/report.mjs:1-24` — header: "组装器，不是第六个 skill"; the three collision classes
- `:47-103` — `PANES` table: id, skill, CLI flag, demo `dir`, labels, upstream `needs` (assembler auto-wires upstream artifacts to each render call)
- `:115-135` — `splitDoc(html)`; `:118-125` isJs filter keeps `<script type="application/json">` data blocks in the body (they're export-button data, not code — extracting them as JS throws `Unexpected token ':'`)
- `:151-205` — `scopeCss(css, scope)` with brace-matching `readBlock`
- `:221-228` — `scopeHtml` id-prefix + reference rewrite
- `:237-249` — `rebaseAssets` (attr + url() dual path)
- `:266-284` — `scopeJs` Proxy wrapper
- `:294-` — `makePane(html, {id, fromDir, outDir})` pure composition

## Verbatim key excerpts

```js
// report.mjs:271-279 — the document proxy
var document=new Proxy(__doc,{get:function(t,k){
  if(k==='querySelector')return function(s){return __root.querySelector(s);};
  if(k==='querySelectorAll')return function(s){return __root.querySelectorAll(s);};
  if(k==='getElementById')return function(id){
    return __root.querySelector('#'+(window.CSS&&CSS.escape?CSS.escape(prefix+id):prefix+id));};
  var v=t[k]; return typeof v==='function'?v.bind(t):v;
}});
```

```js
// report.mjs:193-196 — page selectors become the scope itself
if (/^(:root|html|body)$/.test(s)) return scope;
```

## RECOMMENDATION: PASS (record, revisit on demand)

Rationale: elegant, but it solves a problem we don't currently have — we have no fleet of standalone HTML stage reports to merge (our QC artifacts are JSON/markdown consumed by the SGFLIX QC gate and VLM curators). The *ideas* worth keeping in the notebook: (1) "assembler, not a sixth skill" — never import the things you compose, shell out to their canonical entry point so consumers never drift; (2) the measured-before-fixing discipline (counted 57 shared classnames, 13 conflicting, 9 duplicate ids, zero `#id` selectors — then chose regex over a parser). If SGFLIX ever ships multiple per-stage HTML reports (bibles, QC, render logs), revisit as ADAPT. Decision: reviewer.

Attribution: eternityspring (烁皓), shuohao-skills, Apache-2.0.
