---
id: WD-l5bx
title: "S1: WanGPJobConfig schema + Ref2VA render profile (film lane opener)"
status: in_progress
priority: 1
type: task
labels: [film-lane, phase-2]
parent: WD-j9nx
created_at: 2026-08-28T02:38:46Z
created_by: speed
updated_at: 2026-08-28T04:08:49Z
content_hash: "sha256:04fca4669197fb0519e1d4ec1a1313b155a8469415783a7894bc2b1a0f9171df"
assignee: dev-WD-l5bx
follows: [WD-g3cu]
---

## Description
# S1 — WanGPJobConfig schema + Ref2VA render profile (film lane opener)

Phase 2 film-lane story, first in the S1–S8 dependency sequence. This is a
CODE story (not docs-tier): it lands the job-config surface and the six
guaranteed-invocation gates on the render path, TDD RED-first.

## Spec (dogfooding the #9 spec/plan templates — first real use)

Per `docs/spec-plans.md`, this story ships as a spec+plan pair:
- `docs/specs/s1-wangp-jobconfig-ref2va.md` — pure decision document
  (goal + success invariant, layout, scope incl. explicit non-goals,
  history strategy, verification commands, failure & recovery section).
- `docs/plans/s1-wangp-jobconfig-ref2va.md` — executable decomposition
  (agentic-worker header, Goal/Architecture/Spec-pointer block, Global
  Constraints, File Map, Tasks→Steps with "Expected:" lines per step).

The spec/plan pair IS part of the deliverable set — this story dogfoods
the NEW #9 templates (WD-g3cu, PR #36) for their first real use. If the
templates prove unusable or missing a section the story needs, that gap
is recorded in the plan's Notes and surfaced to the operator (template
fix = separate follow-up story, not folded into S1).

### Deliverable 1 — WanGPJobConfig dataclass + validator

A single typed config object that absorbs EVERY scattered adapter assert
currently living inline across the render adapters. The known inventory
(measure against current main before coding; the list below is the floor,
not necessarily the ceiling — any other scattered fps/frame/JSON asserts
found during scoping get absorbed too):

1. `force_fps: str` — force_fps must be a string (adapter today asserts
   type at call time).
2. **fps >= 96 frame floor** — jobs below the 96-frame minimum are
   rejected at submit, not deep in the adapter.
3. **17k+5 frame-grid snap** — frame counts snap to the 17k+5 grid; the
   snap math lives in ONE place (validator), not re-derived per adapter.
4. **Flat JSON** — job payloads serialize to flat JSON (no nested
   structures); the validator enforces flatness.
5. **`\n---\n` separator** — multi-shot prompt blocks are joined with
   the literal `\n---\n` separator; one constant, one validator check.

Surface: CLI-visible (a `--job-config` / validation entry point on the
existing CLI surface) plus importable validator API. Every existing
adapter that carries one of these asserts delegates to the shared
validator instead of re-asserting (old asserts removed, not duplicated).

### Deliverable 2 — Ref2VA as Strategy-profile second implementation

Ref2VA becomes the SECOND concrete implementation of the existing render
Strategy interface (H3 remains the first). Contract:

- `image_refs` — accepts reference image paths; validated present +
  readable at submit.
- `audio_prompt_type 'A'` — Ref2VA audio mode is type 'A'; the config
  field is typed so anything else fails at construction/validation.
- **guide-alignment validation** — the guide (reference video) duration
  must align with the shot; misalignment is a typed rejection.
- **4–15s cap** — shot duration outside [4s, 15s] is rejected at submit.
- `<Picture N>` / `<Audio N>` tokens — the prompt contract uses numbered
  Picture/Audio token references; validator checks token numbering is
  contiguous and every referenced index has a corresponding ref.

### Deliverable 3 — THE SIX GUARANTEED-INVOCATION GATES (operator ruling)

These six gates MUST fire on the render path and MUST be unskippable —
tests prove each gate fires when its condition is violated AND that no
code path can bypass them (gate invocation is structural, e.g. inside the
submit/render entry points themselves, not optional pre-checks callers
may omit). "Guaranteed invocation" means: the gate code executes on every
render-path invocation by construction; the test suite contains a
test per gate proving the violation case is rejected with a typed error
naming the gate.

1. **Audio 'A' hard-reject at submit** — a job whose audio_prompt_type is
   'A' is hard-rejected AT SUBMIT (before any render work is scheduled).
   Note the interaction with Deliverable 2: Ref2VA *uses* 'A' internally
   as its own mode — the gate rejects 'A' arriving from the generic
   H3-style submit path where 'A' is not a supported audio mode; the
   Ref2VA profile is the sanctioned carrier of 'A'. The spec must state
   this boundary explicitly and the tests must cover both sides (generic
   submit + 'A' → reject; Ref2VA profile + 'A' → accepted).
2. **guide == shot-duration validation** — wherever a guide/reference
   video is supplied, its duration must equal the shot duration exactly;
   mismatch → typed rejection naming both durations.
3. **QC consumes artifact, not spec** — QC stage reads the rendered
   artifact file (hash/readback), never the spec/prompt text. Test:
   corrupt/stub the artifact while keeping the spec valid → QC must fail;
   valid artifact + mutated spec text → QC verdict unchanged.
4. **H3-audio-never-trusted gate** — H3-generated audio output is NEVER
   trusted as final: any pipeline path that would pass H3 audio through
   without the audio-critic/QC pass is structurally blocked (typed
   refusal), regardless of flags.
5. **`<d>`-or-silence prompt contract** — speaker tokens in prompts must
   be either a named `<d>`-form speaker token or explicit silence; free
   form / malformed speaker markers are rejected at validation. (This is
   the groundwork gate for S3's full speaker gate; S1 implements the
   contract check only.)
6. **Master-lock precondition** — no lock record → no render brief. If
   the master-lock record for the project/run does not exist, brief
   generation refuses (typed). Render cannot start from an unlocked
   project.

### Binding constraints (operator rulings — non-negotiable)

- **Maestro = idea-only.** Maestro is under a non-commercial license.
  ADAPT-TO-IDEA ONLY: never vendor Maestro code into this repo. Use its
  file:line references as SPECS (cite them in the spec doc), then
  implement clean-room. Any Maestro-derived logic must be written fresh
  with the citation, not copied.
- **No faster-whisper / pyannote** anywhere in repo code paths (imports,
  requirements, vendored deps). Diarization work is S2's problem with
  MIT-clean upstream patterns; S1 must not pull them in.
- **Local-only inference.** No cloud inference endpoints introduced by
  this story; everything runs against local model/inference surfaces.

## Acceptance Criteria

1. **TDD RED-first:** each of the six gates lands RED (failing test
   proving the violation is currently unguarded or untyped) BEFORE its
   implementation goes GREEN. The PR trail shows red→green per gate.
2. **All six gates fire on the render path** — for each gate: (a) a test
   proving the violating input is rejected with a typed error naming the
   gate, and (b) a test proving the gate is invoked structurally (no
   bypass path exists — e.g. the gate sits inside the submit/render
   entry point itself, verified by exercising the entry point directly
   rather than calling the gate function separately).
3. **WanGPJobConfig absorbs the scattered asserts** — the five known
   rules (force_fps:str, fps>=96 floor, 17k+5 snap, flat JSON,
   `\n---\n` separator) are enforced by the shared validator; the old
   inline adapter asserts are REMOVED (grep proves zero remaining
   duplicates); CLI/validator surface is usable from the command line.
4. **Ref2VA Strategy profile complete** — image_refs validation,
   audio_prompt_type 'A' typing, guide-alignment validation, 4–15s cap,
   `<Picture N>`/`<Audio N>` token contiguity checks all tested.
5. **Full suite green** at branch head, no new failures vs main baseline
   (baseline measured at the pinned SHA before starting; count reported
   in the dispatch reply).
6. **Spec/plan pair shipped** per the #9 templates — both files present,
   spec has the mandatory failure & recovery section, plan steps carry
   "Expected:" lines; template gaps (if any) noted in plan Notes.
7. **Binding constraints hold** — no Maestro code vendored (citations
   only, file:line refs in spec doc), no faster-whisper/pyannote in any
   repo path, no cloud inference endpoints.
8. **PR-only, governed cycle:** isolated branch off main, PR opened,
   Luna acceptance + GLM security review dispatched after stable head,
   merge per standing automerge order (GLM PASS + no new failures +
   scope-match).

## Design notes

- Gate placement: the six gates live in the submit/render ENTRY POINTS
  (the choke points every render path passes through), not in individual
  adapters — that is what makes invocation guaranteed.
- The audio-'A' gate and the Ref2VA-'A' carrier interact; the spec must
  define the boundary in one sentence and the tests must pin both sides.
- Absorb-don't-duplicate: when moving an assert into the validator, the
  adapter-side copy is deleted in the same commit (single-commit
  move-per-rule keeps the diff auditable).
- This story is the film-lane OPENER: S2 (diarization) and S3 (<d>
  speaker gate) build on the config surface and gate structure landed
  here. Keep the gate registration mechanism extensible (a new gate in
  S3 should be a small addition, not a refactor).

## Acceptance Criteria


## Design


## Notes


## History
- 2026-08-28T02:41:15Z status: open -> in_progress
- 2026-08-28T02:41:16Z auto-follows: linked to predecessor WD-g3cu
- 2026-08-28T02:41:16Z claimed by dev-WD-l5bx

## Links
- Parent: [[WD-j9nx]]
- Follows: [[WD-g3cu]]

## Comments

### 2026-08-28T02:38:57Z speed
2026-08-28 sol-max: Phase 2 begins. S1 filed as WD-l5bx (P1, film-lane opener): WanGPJobConfig dataclass/validator absorbing the five scattered adapter asserts (force_fps:str, fps>=96 floor, 17k+5 frame-grid snap, flat JSON, \n---\n separator) + Ref2VA as Strategy-profile second implementation (image_refs, audio_prompt_type 'A', guide-alignment validation, 4-15s cap, <Picture N>/<Audio N> tokens) + the SIX guaranteed-invocation gates from the operator ruling (audio 'A' hard-reject at submit, guide==shot-duration, QC consumes artifact not spec, H3-audio-never-trusted, <d>-or-silence prompt contract, master-lock precondition). Binding constraints carried in the story body: Maestro = idea-only (file:line refs as specs, never vendor code), no faster-whisper/pyannote in repo paths, local-only inference. AC: TDD RED-first per gate, all six gates structurally unskippable on the render path, full suite green vs measured baseline, CLI/validator surface, spec/plan pair per the NEW #9 templates (first real dogfood of WD-g3cu PR #36). Dispatch: qwen-escalator (architectural — new config surface + trust-boundary gates). Standing automerge order applies.

### 2026-08-28T04:08:49Z speed
S1 DELIVERED: PR #37 merged (GLM re-review PASS after fix round; Luna mechanical PASS — zero duplicate enforcement sites verified per-rule, all six gates entry-point unskippable, 442 tests, RED trail genuine, clean-room confirmed). Nits logged: G3 run_pipeline wiring (S3 territory), render_profiles max(frames,96) constant import.
