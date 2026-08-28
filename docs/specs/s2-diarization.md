# SPEC — S2: speaker diarization for multi-speaker <d> attribution

Status: DRAFT → APPROVED (flip at sign-off; a plan may only be written
against an APPROVED spec) · Story: WD-j9nx child (S2, film lane) · Author: sol-max (orchestrator) · Date: 2026-08-28

Format source: `docs/specs/TEMPLATE.md`; extraction lineage:
shuohao-skills spec-driven-evolution.md (spec = why, plan = how).

## Goal

The repo CONSUMES out-of-repo speaker-diarization output: a versioned
JSON timeline schema (per-speaker segments with start/end/speaker id),
a deterministic validator that rejects malformed timelines with typed
errors, and a deterministic converter that turns a validated timeline
into `<d>Name</d>` speaker-attribution blocks compatible with the G5
prompt contract (S1) — so S3's `<d>` speaker gate has a real upstream
data source. Diarization EXECUTION stays out of the repo entirely.

**Success invariant.** A valid diarization JSON validates and converts
to `<d>Name</d>` blocks with zero ambiguity (deterministic: same input
bytes → same output bytes); every malformed input class in the plan's
failure table fails with a typed error naming the rule; and
`grep -rn "faster_whisper\|pyannote" --include="*.py"` over repo code
paths returns ZERO hits (binding constraint, mechanically checkable).

## Layout & scope

- NEW `predict/diarization.py` — the in-repo surface:
  - `DIARIZATION_SCHEMA_VERSION = 1`
  - `DiarizationError(ValueError)` — typed rejection base
  - `validate_diarization(doc: dict) -> None` — schema validator
    (pure function, no I/O)
  - `diarization_to_speaker_blocks(doc: dict) -> list[SpeakerBlock]`
    — deterministic conversion to attribution blocks
  - `SpeakerBlock` frozen dataclass: `start`, `end`, `speaker`,
    `text_hint` (optional transcript fragment, passthrough only)
- NEW `scripts/check_diarization.py` — CLI surface:
  `python scripts/check_diarization.py <file.json>` → exit 0 + summary
  on valid, exit 1 + typed error line on invalid; `--convert` flag
  prints the converted `<d>Name</d>` block listing.
- NEW `tests/test_diarization.py` — TDD RED-first per failure class.
- NEW `docs/specs/s2-diarization.md` + `docs/plans/s2-diarization.md`
  (this pair; dogfoods the #9 templates again).

**Non-goals.**
- Running diarization models — faster-whisper/pyannote NEVER appear in
  repo code paths (license + operator binding rule). Execution is an
  out-of-repo tool whose JSON output this story consumes. The repo
  ships NO runner script for them either; the external tool is
  operator-supplied (e.g. a standalone venv on the 3090).
- Transcript accuracy / ASR quality — text fragments are opaque
  passthrough; nothing in the repo scores or corrects them.
- Speaker NAME assignment from voice identity — the external tool
  emits speaker labels (SPEAKER_00…); mapping labels to character
  names is a downstream editorial step (S4's job), not this one.
- G3 run_pipeline wiring — carried nit from S1; lands in S3, not here.
- render_profiles constant import — carried nit, anytime, not here.

## The timeline schema (v1)

Top-level object, exactly these keys:

```json
{
  "schema_version": 1,
  "audio_sha256": "<64 hex chars — hash of the exact audio file the
                     diarization ran against; ties timeline to artifact>",
  "duration_sec": 123.45,
  "speakers": ["SPEAKER_00", "SPEAKER_01"],
  "segments": [
    {"start": 0.0, "end": 3.2, "speaker": "SPEAKER_00",
     "text": "optional transcript fragment"}
  ]
}
```

Validation rules (each a distinct typed rejection):
- R1 `schema_version` must be int == 1 (no floats, no strings).
- R2 `audio_sha256` must be 64 lowercase hex chars.
- R3 `duration_sec` must be a positive finite number.
- R4 `speakers` must be a non-empty list of unique non-empty strings.
- R5 `segments` must be a list; each segment: `start`/`end` numeric
  with 0 <= start < end <= duration_sec (+1e-6 float tolerance);
  `speaker` must be a member of `speakers`; `text` optional string.
- R6 segments must be sorted by `start` ascending (ties broken by
  `end`); overlapping segments of DIFFERENT speakers are rejected
  (overlap of same speaker also rejected — one contiguous run per
  speaker interval; merging is the external tool's job).
- Unknown top-level keys rejected (forward-compat discipline: a
  schema change must bump schema_version, not sneak keys in).

Conversion semantics (`diarization_to_speaker_blocks`):
- Input MUST already pass `validate_diarization` (converter re-validates
  defensively and raises the same typed errors — single authority).
- Each segment maps 1:1 to a `SpeakerBlock(start, end, speaker,
  text_hint=text-or-"")`. Order preserved (timeline order).
- Attribution rendering helper `render_attribution(blocks)` emits
  `<d>SPEAKER_00</d>`-form tokens — EXACTLY the shape G5 accepts
  (G5 rejects bracketed/parenthesized labels; `<d>Name</d>` is the
  sanctioned form). This is the bridge into S3.
- Determinism: no timestamps, no randomness, no dict-order leakage —
  same input bytes produce byte-identical output. Proven by test.

## Maestro spec references (clean-room sources)

Maestro `audio_analysis.py:675-780` is the IDEA-ONLY reference for
"diarize dialogue audio into per-speaker timelines convertible to
(S1)/(S2) attribution" (operator deep-dive). ADAPT-TO-IDEA ONLY:
Maestro is non-commercial licensed — its code is NEVER vendored; the
file:line ref exists so a reviewer can verify we adapted the idea
(versioned timeline + speaker segmentation + attribution conversion)
without copying any implementation. Our schema is our own design,
constrained by what S3's gate needs, not by Maestro's internal shape.

## Binding constraints (carried from epic)

- faster-whisper / pyannote: never in repo code paths — no imports,
  no requirements entries, no subprocess calls to their CLIs from repo
  code. The grep check above is part of verification.
- Local-only inference (epic-wide): nothing here adds endpoints.
- PR-only flow, explicit staging, no force-push (repo standing rules).

## History strategy

In-place edit on a feature branch (repo's standing PR-only flow); no
history rewrite. Purely additive story — no deletions, so no
move-per-rule sequencing needed (that was S1's refactor shape).

## Cleanup & sequencing

Nothing to remove. Sequencing inside the branch: schema+validator
RED→GREEN first, then converter RED→GREEN, then CLI last (CLI is a
thin wrapper; it tests the two functions above, never new logic).

## Commit & GitHub flow

- Branch: `feat/wd-s2-diarization` off main @ d10af46.
- PR-only; never direct to main; no force-push.
- Explicit file staging only (`git add <path>`); never `git add .`.

## Verification

```bash
$ .venv/bin/python -m pytest tests/ -q
# Expected: full suite green, count >= 442 (baseline 442 at d10af46)

$ .venv/bin/python -m pytest tests/test_diarization.py -q
# Expected: all passed; covers every rule R1-R6 (>=2 cases each:
# valid acceptance + typed rejection naming the rule) plus
# determinism (double-conversion byte-equality) and G5-shape
# compatibility of rendered tokens.

$ .venv/bin/python scripts/check_diarization.py <valid-fixture.json>
# Expected: exit 0, one-line summary (n speakers, n segments)

$ .venv/bin/python scripts/check_diarization.py <invalid-fixture.json>
# Expected: exit 1, stderr line naming the failing rule (R1..R6)

$ grep -rn "faster_whisper\|pyannote" --include="*.py" predict/ host/ scripts/ tests/
# Expected: ZERO matches (binding constraint)
```

Full-suite gate: `.venv/bin/python -m pytest tests/` tail line pasted
into the PR description.

## Failure & recovery

- Recoverable: everything — work lives on a feature branch; mid-step
  failure = stop, leave the branch, report. Main untouched.
- NEVER touched during recovery: the shared checkout's uncommitted
  paivot tooling files (.gitignore, .paivot/config.yaml) and any other
  agent's WIP.
- Stop-the-world vs retry: operator (via sol-max dispatch); standing
  stop conditions: double-BLOCK, provider death, operator interrupt.
