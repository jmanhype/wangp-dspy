# SPEC — S3: <d> speaker gate (attribution REQUIRED) + G3 run_pipeline wiring

Status: APPROVED (operator sign-off 2026-08-28, recorded in PR description) · Story: WD-j9nx child (S3, film lane) · Author: sol-max (orchestrator) · Date: 2026-08-28

Format source: `docs/specs/TEMPLATE.md`; extraction lineage:
shuohao-skills spec-driven-evolution.md (spec = why, plan = how).

## Goal

The `<d>` speaker contract stops being optional groundwork and becomes a
REQUIRED gate on dialogue-bearing briefs: any render brief whose text
contains speech content MUST carry explicit speaker attribution in
`<d>SPEAKER_NN</d>` form (the shape S2's converter emits per
predict/diarization.py) or an explicit silence marker — bare quoted
dialogue with no attribution is a typed rejection. Silence is explicit,
never implied. In parallel, the carried nit from S1 review lands:
G3 (QC consumes artifact, not spec) is wired into `run_pipeline`'s QC
call path so the pipeline cannot silently degrade to a spec-based
verdict when the rendered file is missing.

**Success invariant.** A brief containing dialogue text without
`<d>Name</d>` attribution or an explicit silence marker is rejected at
the entry points with a typed error naming the rule (S3-G5a), while a
brief with proper `<d>SPEAKER_NN</d>` attribution or explicit silence
passes unchanged; AND `run_pipeline` raises a typed G3 error (not a
silent text-only critique, not a ValueError from a missing-file check)
when a render produces no readable video file — both mechanically
checkable by exercising the entry points directly.

## Layout & scope

- MODIFY `host/wangp_adapter.py`:
  - `_g5_check(text)` gains the dialogue-attribution rule (S3-G5a):
    detect dialogue-bearing text (quoted speech spans) and require
    either a `<d>Name</d>` token in the same field or an explicit
    silence marker. Existing malformed-marker rejection (bracketed /
    parenthesized labels) stays as-is.
  - New module-level constant for the explicit-silence marker
    (single authority; documented in the module docstring).
  - `run_pipeline._checked_video` replaced/augmented: a missing or
    unreadable rendered file now raises a typed **G3** error naming
    the gate ("QC consumes artifact, not spec") instead of the current
    generic message — the gate identity is structural, matching how
    G1/G4/G5/G6 already name themselves at their firing sites.
- NEW `tests/test_speaker_gate.py` — TDD RED-first: every failure class
  (bare dialogue, bracketed label, attributed pass, silence pass,
  mixed-field cases, G3 pipeline firing) gets its own test.
- MODIFY `tests/test_entry_point_gates.py` — update the G6 tests that
  depend on cwd absence of MASTER_LOCK.md to be hermetic (monkeypatch
  the env var + tmp_path chdir) so the suite is green regardless of
  stray files at repo root (found during S3 baseline: a leftover
  MASTER_LOCK.md from the S2.5 vertical slice made two G6 tests fail
  in this checkout).
- NEW `docs/specs/s3-speaker-gate.md` + `docs/plans/s3-speaker-gate.md`
  (this pair; #9 templates again).

**Non-goals.**
- Speaker NAME assignment (SPEAKER_00 → character names) — S4's
  editorial step; the gate accepts whatever label S2's converter
  emitted, it does not interpret it.
- Diarization execution — still out-of-repo (binding constraint
  unchanged: faster-whisper/pyannote grep stays zero).
- The whisper gate on assembled audio — S4 (assembly-time concern,
  different call site).
- Ref2VA guide-alignment changes — G2 untouched.
- Changing what `qc.run()` itself does — G3 here is about the
  PIPELINE refusing to feed QC a non-artifact; the critic's internals
  are out of scope.

## The attribution rule (S3-G5a)

Detection (per brief field checked by G5 — subject, motion, camera,
style, audio_direction):

1. **Dialogue-bearing** = the field contains a double-quoted span
   (`"..."`) with at least one word inside. Quoted spans are the
   pipeline's established way of marking speech (H3 prompt contract:
   dialogue blocks are punctuation-exact; our briefs quote lines).
2. If dialogue-bearing, the field MUST contain one of:
   - a `<d>Name</d>` token (any nonempty Name — S2 emits
     `<d>SPEAKER_NN</d>`; character names are equally valid), OR
   - the explicit silence marker (module constant, e.g.
     `[silence]` — chosen over prose "no dialogue" because it is
     unambiguous, greppable, and cannot collide with natural language).
3. Neither present → typed rejection naming S3-G5a, quoting the
   offending field and the first bare quoted span found.

Silence semantics: a field with the silence marker and no quoted
speech is VALID (explicit silence); a field with quoted speech AND the
silence marker but NO `<d>` token is REJECTED (contradiction — you
cannot claim silence while quoting a line).

Interaction with existing G5: the malformed-marker regex
(`[John]`/`(Mary)`) fires FIRST and wins on overlap — a bracketed
label is never re-diagnosed as "missing attribution".

Why quoted-span detection (vs. keyword lists like "says"/"whispers"):
keyword lists are open-ended and miss paraphrases; quotes are the
closed, machine-checkable signal we already use for verbatim dialogue
in the H3 prompt contract (h3-prompt-contract.md item 3). False
positives (quoting a title card) are acceptable: the fix is trivial
(reword or add the marker) and the cost of a false negative (unattributed
dialogue painted into a render) is exactly what S3 exists to prevent.

## G3 wiring into run_pipeline

Current state (carried nit from S1 review): `run_pipeline`'s
`_checked_video` refuses QC on a missing file, but the error message
is generic ("refusing to run QC on a missing file") — the gate is
there structurally but not NAMED, so a reader cannot tell G3 fired
without reading the adapter source. Fix: the raised error carries the
gate identity `G3 artifact-not-spec` and states the invariant (QC
input is the rendered file; a valid spec never substitutes for the
artifact). Both call sites (first QC call and REVISE retry) go through
the same helper, so one change covers both.

This does NOT change `qc_artifact()` (the standalone G3 entry point
from S1) — it stays as the direct-fire surface; `run_pipeline` simply
stops being the one gate site that fires anonymously.

## Binding constraints (carried from epic)

- faster-whisper / pyannote: never in repo code paths (grep check
  unchanged, part of verification).
- Local-only inference; nothing adds endpoints.
- PR-only flow, explicit staging, no force-push (repo standing rules).
- Suite baseline: 480 passed at b5b086d (main after #39 merge); the
  final count must be >= 480 + new tests, all green.

## History strategy

In-place edit on a feature branch (standing PR-only flow); no history
rewrite. Two independent concerns (speaker gate, G3 naming) land as
separate commits with separate RED→GREEN trails so the PR diff is
reviewable per concern.

## Cleanup & sequencing

Nothing removed. Sequence: (1) hermetic G6 test fix (baseline hygiene —
must be green before adding new tests so failures are attributable);
(2) S3-G5a RED→GREEN; (3) G3 run_pipeline naming RED→GREEN; (4) docs
pair last. At every commit the suite is green.

## Commit & GitHub flow

- Branch: `feat/wd-j9nx-s3-speaker-gate` off main @ b5b086d.
- PR-only; never direct to main; no force-push.
- Explicit file staging only (`git add <path>`); never `git add .`.
- Standing automerge order applies after gates clear.

## Verification

```bash
$ .venv/bin/python -m pytest tests/ -q
# Expected: full suite green, count >= 480 (baseline at b5b086d)

$ .venv/bin/python -m pytest tests/test_speaker_gate.py -q
# Expected: all passed; covers bare-dialogue rejection, attributed
# acceptance, explicit-silence acceptance, contradiction rejection,
# malformed-marker precedence, G3 pipeline firing (typed, named).

$ .venv/bin/python scripts/check_diarization.py <valid-fixture.json> --convert
# Expected: exit 0; rendered <d>SPEAKER_NN</d> lines accepted by the
# new gate (bridge check: S2 output -> S3 input, end-to-end shape).

$ grep -rn "faster_whisper\|pyannote" --include="*.py" predict/ host/ scripts/ tests/
# Expected: ZERO matches (binding constraint)
```

Full-suite gate: `.venv/bin/python -m pytest tests/` tail line pasted
into the PR description.

## Failure & recovery

- Recoverable: everything — work lives on a feature branch; mid-step
  failure = stop, leave the branch, report. Main untouched.
- NEVER touched during recovery: the shared checkout's uncommitted
  paivot tooling files (.gitignore, .paivot/config.yaml), AGENTS.md,
  MASTER_LOCK.md (operator artifacts), and any other agent's WIP.
- Stop-the-world vs retry: operator (via sol-max dispatch); standing
  stop conditions: double-BLOCK, provider death, operator interrupt.
