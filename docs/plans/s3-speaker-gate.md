# PLAN — S3: <d> speaker gate (attribution REQUIRED) + G3 run_pipeline wiring

Spec: `docs/specs/s3-speaker-gate.md` (APPROVED at sign-off) · Story: WD-j9nx/S3 · Author: sol-max · Date: 2026-08-28

## Global constraints

- Suite green at every commit (baseline 480 passed @ b5b086d).
- Explicit staging only; never `git add .`.
- No faster-whisper/pyannote anywhere in repo code paths.
- RED before GREEN for every new behavior; the RED must fail for the
  RIGHT reason (assert on the typed error, not just "raises").

## File map

| Path | Task | Change |
|------|------|--------|
| tests/test_entry_point_gates.py | T1 | hermetic G6 tests (monkeypatch env + tmp_path) |
| host/wangp_adapter.py | T2 | S3-G5a attribution rule in `_g5_check` + silence constant |
| tests/test_speaker_gate.py | T2 | RED-first per failure class |
| host/wangp_adapter.py | T3 | G3 naming in `run_pipeline._checked_video` |
| tests/test_speaker_gate.py | T3 | G3 pipeline firing test (RED first) |
| docs/specs/s3-speaker-gate.md | T4 | spec pair (already drafted with this plan) |
| docs/plans/s3-speaker-gate.md | T4 | this file |

## Task 1 — Hermetic G6 tests (baseline hygiene)

Context: baseline run found `test_g6_typed_rejection` and
`test_g6_entry_point_fires` fail when a stray `MASTER_LOCK.md` exists
at repo root (leftover from the S2.5 vertical slice). The G6 check
reads cwd, so the tests must control cwd themselves.

- [x] **Step 1.1** — Rewrite both G6 tests to: monkeypatch
  `WANGP_MASTER_LOCK` to "" (delete if set), chdir into an empty
  `tmp_path` (no MASTER_LOCK.md possible), then assert the typed G6
  rejection. Add a third case: lock present via env var → no G6 fire
  (proves the monkeypatch actually controls the input).

```bash
$ .venv/bin/python -m pytest tests/test_entry_point_gates.py -q
```
Expected: all pass, WITH and WITHOUT a stray MASTER_LOCK.md at repo
root (verify both ways before committing).

Failure gate: if the third case (env-var lock honored) fails, stop —
the monkeypatch is not isolating correctly.

Commit: `fix(WD-j9nx/S3): hermetic G6 tests — cwd isolation via monkeypatch+tmp_path`

## Task 2 — S3-G5a: dialogue attribution REQUIRED

- [x] **Step 2.1** — RED: write `tests/test_speaker_gate.py` with these
  cases (all expected to FAIL against current code where noted):

  1. `test_bare_dialogue_rejected` — brief with subject containing
     `"hello there"` (quoted span, no `<d>`, no silence marker) →
     `WanGPError` matching `S3-G5a`. (RED today.)
  2. `test_attributed_dialogue_passes` — same quote plus
     `<d>SPEAKER_00</d>` in the field → no error. (GREEN today —
     regression guard.)
  3. `test_explicit_silence_passes` — field with the silence marker,
     no quoted speech → no error. (RED today — marker unknown.)
  4. `test_silence_with_quote_rejected` — silence marker AND quoted
     span, no `<d>` token → `S3-G5a` (contradiction). (RED today.)
  5. `test_malformed_marker_precedence` — `[John] says "hi"` → error
     names the malformed-marker rule (existing G5), NOT S3-G5a.
     (GREEN today — precedence guard.)
  6. `test_all_fields_checked` — bare quote in each of motion /
     camera / style / audio_direction individually → rejected.
     (RED today.)
  7. `test_s2_bridge_shape` — build a timeline doc, run
     `diarization_to_speaker_blocks` + `render_attribution`, embed the
     rendered tokens in a brief with quoted speech → accepted.
     (GREEN today — proves the S2→S3 shape bridge end-to-end.)

- [x] **Step 2.2** — Implement in `host/wangp_adapter.py`:
  - Module constant `SILENCE_MARKER = "[silence]"` (single authority;
    docstring explains the choice — unambiguous, greppable, no
    natural-language collision).
  - `_g5_check(text)` extension: after the existing malformed-marker
    regex (which keeps precedence), detect quoted spans
    (`re.search(r'"[^"\n]+?"', text)`); if found and the field has
    neither a `<d>...</d>` token nor the silence marker → raise
    `WanGPError("S3-G5a: ...")` quoting the field's offending span.
    If the silence marker is present AND a quoted span exists AND no
    `<d>` token → same typed rejection (contradiction clause).
  - Keep the function pure (no I/O); it already receives the field
    string. The field NAME is not available inside `_g5_check` today —
    pass it as an optional second arg (default "<text>") so the error
    can name the field; update the call sites in `submit()` and
    `build_settings()`.

```bash
$ .venv/bin/python -m pytest tests/test_speaker_gate.py -q
```
Expected: all 7 pass.

```bash
$ .venv/bin/python -m pytest tests/ -q
```
Expected: full suite green (480 + 7 = 487, or more if T1 added cases).

Failure gate: any pre-existing test that now trips S3-G5a means a
fixture contains bare quoted dialogue — fix the FIXTURE by adding
proper attribution (do NOT weaken the gate to make old fixtures pass;
that defeats the story).

Commit: `feat(WD-j9nx/S3): S3-G5a — dialogue attribution REQUIRED on briefs (<d>Name</d> or explicit silence)`

## Task 3 — G3 named in run_pipeline

- [x] **Step 3.1** — RED: add to `tests/test_speaker_gate.py`
  (or `tests/test_wangp_adapter.py` if it reads cleaner — decide at
  implementation time, note in PR):
  1. `test_run_pipeline_missing_video_raises_named_g3` — adapter with
     a runner whose result points at a nonexistent path; call
     `run_pipeline`; expect `WanGPError` matching `G3` AND
     `artifact-not-spec`. (RED today — message is generic.)
  2. `test_run_pipeline_revise_retry_missing_video_also_g3` — force a
     REVISE verdict then a missing file on retry → same named G3.
     (RED today.)

- [x] **Step 3.2** — Implement: rewrite `_checked_video`'s raised
  message to carry `G3 artifact-not-spec: QC consumes the rendered
  artifact, not the spec — {path!r} is not a readable file; a valid
  spec NEVER substitutes for the artifact`. One helper, both call
  sites covered. Do NOT touch `qc_artifact()`.

```bash
$ .venv/bin/python -m pytest tests/ -q
```
Expected: full suite green.

Commit: `feat(WD-j9nx/S3): G3 named at run_pipeline QC call path (carried nit from S1 review)`

## Task 4 — Docs pair

- [x] **Step 4.1** — Spec status DRAFT → APPROVED (operator sign-off
  recorded in PR description); plan checkboxes ticked as completed.

Commit: `docs(WD-j9nx/S3): spec/plan pair — speaker gate + G3 pipeline wiring`

## Final verification

```bash
$ .venv/bin/python -m pytest tests/ -q
# Expected: measured green count pasted verbatim into the PR
# description (>= 480 baseline + all new tests).

$ grep -rn "faster_whisper\|pyannote" --include="*.py" predict/ host/ scripts/ tests/
# Expected: ZERO matches.

$ .venv/bin/python scripts/check_diarization.py tests/fixtures/<valid>.json --convert
# Expected: exit 0 + <d>SPEAKER_NN</d> lines (bridge evidence).
```
