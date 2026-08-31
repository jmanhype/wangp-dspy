# Phileiny Findings (external, MIT) — `partially-verified`

Adopted from [phileiny/h3-storyboard-skill](https://github.com/phileiny/h3-storyboard-skill)
(MIT). Tag: PHILEINY. We adopt their methodology; the specific numeric
claims below are theirs, not re-measured by us unless noted.

- **Beat density ceiling**: 9 beats/shot fails; 1 beat works.
- **`<d>` dialogue tags reallocate screen time** to dialogue shots.
- **Tail collapse**: motion dies 1.2-1.7s before shot end.
- **"Nothing changes" phrasing leaks** into the render — avoid
  negation-style motion descriptions.
- **Silent characters use body, not face** — give non-speakers body
  action clauses.
- **PSNR verification methodology** for prompt/format A-B comparisons.

## Evidence

- PHILEINY repo (MIT) — see SOURCES.md.

## Overlap with our verified findings

- Silent-character body action ↔ our lips-closed + ambient-action
  clauses in subject-mode.md (we verified the motion gain).
- Tail collapse is compatible with our freeze measurements (freeze.md)
  but was not separately measured.
