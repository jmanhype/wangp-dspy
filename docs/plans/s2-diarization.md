# PLAN — S2: speaker diarization for multi-speaker <d> attribution

> **For agentic workers:** REQUIRED SUB-SKILL: Hermes delegate_task or
> kanban lane. Steps use checkbox syntax. Machine-executable with ZERO
> conversation context: decisions live in the spec
> (docs/specs/s2-diarization.md); commands/expected outputs here.
> Judgment call not answered here? STOP and report.

**Goal.** In-repo CONSUMPTION surface for out-of-repo diarization
output: versioned JSON timeline schema + deterministic validator +
conversion to `<d>Name</d>` speaker-attribution blocks feeding S3's
`<d>` speaker gate. Execution stays external (binding).

**Architecture.** Validator is a pure function over a dict; converter
re-validates then maps 1:1 preserving order; CLI wraps both without
new logic. Determinism is an invariant, proven by test (double-run
byte-equality), not assumed.

**Tech Stack.** Python 3.12, `/Users/Shared/HermesWorkspace/wangp-dspy/.venv/bin/python`,
pytest. NO new dependencies (binding: no faster-whisper/pyannote,
local-only, nothing added to requirements).

**Spec.** `docs/specs/s2-diarization.md`.

## Global Constraints

- Absolute paths only: /Users/Shared/HermesWorkspace/wangp-dspy.
- Repo: jmanhype/paivot-hermes sibling = wangp-dspy (private), PR-only.
- Staging ban: explicit `git add <path>` per file; **never `git add .`**.
- Sequencing safety: TDD RED-first — each failing test committed
  before its implementation; full suite green at every commit.
- Tier boundary: code + tests + these two docs only. No template
  edits, no requirements changes, no adapter/pipeline changes (G3
  wiring is S3's scope — do NOT touch host/wangp_adapter.py or
  run_pipeline).
- Binding grep gate must stay clean at EVERY commit:
  `grep -rn "faster_whisper\|pyannote" --include="*.py" predict/ host/ scripts/ tests/` → zero matches.

## File Map

| File | Action | Task |
|---|---|---|
| `predict/diarization.py` | CREATE | T1–T4 |
| `tests/test_diarization.py` | CREATE | T1–T4 |
| `scripts/check_diarization.py` | CREATE | T5 |
| `tests/fixtures/diarization_valid.json` | CREATE | T5 |
| `tests/fixtures/diarization_invalid_r5.json` | CREATE | T5 |
| `docs/specs/s2-diarization.md` | CREATE | T0 |
| `docs/plans/s2-diarization.md` | CREATE | T0 |

A task touching a file not on this map is out of scope — stop and report.

## Tasks

### T0 — Branch + spec/plan pair (already authored by orchestrator)

- [ ] `git checkout main && git pull` → confirm HEAD == d10af46.
- [ ] `git checkout -b feat/wd-s2-diarization`
- [ ] Commit the two doc files (they exist in the working tree):
      `git add docs/specs/s2-diarization.md docs/plans/s2-diarization.md`
      → commit `docs(WD-j9nx/S2): spec+plan pair for diarization consumption`.
- Expected: `git log --oneline -1` shows the docs commit; branch off d10af46.

### T1 — Schema constants + validator skeleton (RED→GREEN)

- [ ] RED: write `tests/test_diarization.py` covering R1–R4 first:
      - valid minimal doc passes (no exception)
      - R1: schema_version float / string / 2 → DiarizationError naming R1
      - R2: sha wrong length / uppercase hex / non-hex → names R2
      - R3: duration_sec zero / negative / NaN / inf → names R3
      - R4: speakers empty list / duplicate entries / non-string entry → names R4
      Run: `.venv/bin/python -m pytest tests/test_diarization.py -q`
      Expected: FAIL (module missing / functions undefined) — genuine RED.
- [ ] GREEN: create `predict/diarization.py` with `DIARIZATION_SCHEMA_VERSION`,
      `DiarizationError`, `validate_diarization` implementing R1–R4 (+ unknown-key
      rejection from R6-discipline). Each error message MUST name the rule id
      (e.g. `"R2: audio_sha256 must be 64 lowercase hex chars"`).
      Run same command. Expected: all T1 tests pass.
- [ ] Full suite: `.venv/bin/python -m pytest tests/ -q` → green, count >= 442.
- [ ] Commit: `feat(WD-j9nx/S2): diarization schema v1 + validator R1-R4 (TDD)`.

### T2 — Segment rules R5/R6 (RED→GREEN)

- [ ] RED: extend `tests/test_diarization.py`:
      - R5: start==end / start>end / end>duration / negative start /
        speaker not in speakers list / text as non-string → names R5
      - R6: unsorted segments → names R6; overlapping different-speaker
        segments → names R6; overlapping same-speaker segments → names R6
      - tolerance: end == duration + 1e-7 accepted (float tolerance)
      - unknown top-level key → rejected (names the discipline rule)
      Expected: FAIL against current impl.
- [ ] GREEN: implement R5/R6 in `validate_diarization` (overlap check via
      sorted walk; 1e-6 tolerance constant named `FLOAT_TOL`).
      Expected: all pass.
- [ ] Full suite green. Commit: `feat(WD-j9nx/S2): segment validation R5-R6 (TDD)`.

### T3 — Converter + determinism + G5-shape bridge (RED→GREEN)

- [ ] RED: extend tests:
      - `diarization_to_speaker_blocks` on valid doc → one SpeakerBlock per
        segment, order preserved, fields exact
      - converter on INVALID doc raises the SAME typed DiarizationError
        (defensive re-validation, single authority)
      - `render_attribution(blocks)` emits tokens matching regex
        `^<d>[^<>]+</d>$` for every block (G5-compatible shape; G5 rejects
        bracketed/parenthesized labels — assert our output contains none)
      - DETERMINISM: convert the same doc twice → identical lists; render
        twice → byte-identical strings
      Expected: FAIL (functions undefined).
- [ ] GREEN: implement `SpeakerBlock` (frozen dataclass: start, end, speaker,
      text_hint), `diarization_to_speaker_blocks`, `render_attribution`.
      No timestamps/randomness/dict-order leakage anywhere.
      Expected: all pass.
- [ ] Full suite green. Commit: `feat(WD-j9nx/S2): speaker-block conversion + attribution rendering (TDD)`.

### T4 — Edge cases hardening

- [ ] Add tests: empty segments list (valid — zero dialogue), large doc
      (1000 segments, performance sanity < 1s), unicode speaker ids,
      text fragments with embedded `<d>`-like substrings (passthrough,
      never parsed).
- [ ] Fix any revealed bugs. Full suite green.
- [ ] Commit: `test(WD-j9nx/S2): edge cases — empty/large/unicode/passthrough`.

### T5 — CLI surface (thin wrapper, no new logic)

- [ ] Create `tests/fixtures/diarization_valid.json` (2 speakers, 4 segments,
      realistic times) and `tests/fixtures/diarization_invalid_r5.json`
      (one segment with end > duration).
- [ ] Create `scripts/check_diarization.py`:
      `python scripts/check_diarization.py FILE [--convert]`
      - valid → stdout summary line (`OK: 2 speakers, 4 segments, 123.45s`), exit 0
      - invalid → stderr line with the typed rule error, exit 1
      - `--convert` on valid → prints rendered attribution lines after summary
      - missing file / bad JSON → exit 1 with clear message (not a traceback)
- [ ] Test the CLI via subprocess in `tests/test_diarization.py` (or a small
      `tests/test_check_diarization_cli.py` if it keeps imports clean — your
      call, but NO new file outside the File Map unless you amend the plan
      comment on the story first): assert exit codes + output lines.
- [ ] Manual verification (paste into PR description):
      ```
      $ .venv/bin/python scripts/check_diarization.py tests/fixtures/diarization_valid.json
      OK: 2 speakers, 4 segments, ...   (exit 0)
      $ .venv/bin/python scripts/check_diarization.py tests/fixtures/diarization_invalid_r5.json
      R5: ...                            (exit 1)
      ```
- [ ] Full suite green. Commit: `feat(WD-j9nx/S2): CLI validator surface + fixtures`.

### T6 — Final gates + PR

- [ ] `.venv/bin/python -m pytest tests/ -q` → record tail line (count >= 442).
- [ ] Binding grep: `grep -rn "faster_whisper\|pyannote" --include="*.py" predict/ host/ scripts/ tests/` → zero matches. Record result.
- [ ] `git diff --check` clean; `git status` shows only File-Map files.
- [ ] Push branch, open PR with: tail-line suite count, grep result, manual
      CLI output, spec/plan links. Title:
      `feat(WD-j9nx/S2): diarization timeline schema + validator + <d> attribution conversion`.
- [ ] Report stable head SHA to sol-max (orchestrator) — do NOT merge;
      Luna + GLM parallel gating follows, then standing automerge.

## Acceptance criteria (mirror of story AC)

1. Timeline schema validator — TDD, every rule R1–R6 has acceptance +
   typed-rejection tests naming the rule.
2. Conversion to speaker-attribution blocks — deterministic (proven by
   double-run byte-equality), G5-compatible token shape.
3. Suite green — full suite >= 442 at final head.
4. CLI/validator surface — exit-code contract verified manually AND by test.
5. Binding constraint — zero faster-whisper/pyannote hits in repo code paths.

## Failure & recovery

Mid-task failure: stop, leave the branch as-is, report to sol-max with
the failing command + output. Main is untouched; the branch is safe to
resume. Never force-push; never stage outside the File Map.
