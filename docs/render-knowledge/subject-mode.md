# Subject-Mode Prompt Format — `verified`

10-13x motion gain over prose prompts (measured with the 64x36
thirds-luma motion metric on controlled A/B renders, 2026-08-30/31).

Format:

- `<Subject N>` angle-bracket tag definitions derived from `<Picture 1>`
  (identity lock anchor).
- `retention_analysis` block (what must persist shot-to-shot).
- Per-subject ambient actions (idle motion so subjects never freeze).
- `(S1)` speaker binding with language-tagged `<d>[lang]` dialogue tags;
  non-speakers get explicit **lips-closed** clauses.
- `overall_soundscape`.
- `non_diegetic_music: N/A` (unless music is wanted).

Now **enforced in code** by `predict/subject_prompt.py` (PR #52, merged
as 7c0c883) — the prompt builder emits this structure directly.

## Evidence

- CONTROLLED-SEED-AB: subject-mode prompts measured 2.03-5.06
  motion/third vs 0.11-0.39 for equivalent prose prompts under the same
  seed/params.
- PR-52: `predict/subject_prompt.py` + tests
  (`tests/test_subject_prompt.py`,
  `tests/test_subject_prompt_fixture_fidelity.py`).
