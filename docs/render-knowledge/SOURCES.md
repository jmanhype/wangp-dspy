# Render Knowledge — SOURCES

Citation index for every finding in this directory. Format modeled on
[phileiny/h3-storyboard-skill](https://github.com/phileiny/h3-storyboard-skill)
(MIT) — each finding file carries a status marker
(`verified` / `partially-verified` / `inferred` / `open`) and an
Evidence section with concrete citations.

## Internal (our own controlled tests, 2026-08-30/31)

| Tag | Source | Used by |
|---|---|---|
| CONTROLLED-SEED-AB | Controlled seed A/B renders, 2026-08-30/31: identical prompt+params, varied seed; 64x36 luma-diff per third measured on outputs | freeze.md, motion-gate.md |
| RENDER-LOGS-0830 | WanGP render logs, 3090, 2026-08-30 (frames/step-times, frame-grid acceptance) | frame-grid.md, rebase-speed.md |
| USER-OBS-CHAINING | User observation of per-cut same-master render behavior (scene resets every cut) | chaining-gap.md |
| PR-52 | wangp-dspy PR #52 `feat(predict): subject-mode Ref2VA prompt builder` (merged as 7c0c883); `predict/subject_prompt.py` | subject-mode.md |

## External

| Tag | Source | License | Used by |
|---|---|---|---|
| PHILEINY | github.com/phileiny/h3-storyboard-skill — findings on beat density, dialogue tags, tail collapse, phrasing leaks, silent characters, PSNR verification | MIT | phileiny-findings.md |
| COMFYUI-H3 | ComfyUI MiniMax H3 docs (MiniMaxH3AddGuide node: valid clip lengths 5/22/39/…) | as cited | frame-grid.md |
| WANGP-H3-SKILL | Hermes skill `wangp-h3-multishot` (Ref2VA mechanics: audio_prompt_type=A, audio refs 2-15s, 4-15s render range, up to 9 image refs, synthesized audio, `<d>` tags) | internal skill | ref2va-mechanics.md |
| WANGP-UPSTREAM | Wan2GP upstream main (rebase target; deepy optimizations) | upstream repo license | rebase-speed.md |

## Verification-status legend

- `verified` — reproduced by our own controlled test with measured evidence.
- `partially-verified` — parts measured by us, parts adopted from external sources.
- `inferred` — reasonable inference, not directly measured.
- `open` — known gap, fix path identified but NOT implemented.
