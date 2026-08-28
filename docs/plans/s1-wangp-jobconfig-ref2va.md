# PLAN — S1: WanGPJobConfig schema + Ref2VA render profile

> **For agentic workers:** REQUIRED SUB-SKILL: Hermes delegate_task or
> kanban lane. Steps use checkbox syntax. Machine-executable with ZERO
> conversation context: decisions live in the spec
> (docs/specs/s1-wangp-jobconfig-ref2va.md); commands/expected outputs
> here. Judgment call not answered here? STOP and report.

**Goal.** One authoritative WanGPJobConfig schema/validator absorbing
the five scattered adapter rules + a Ref2VA Strategy profile + six
entry-point-structural gates.

**Architecture.** Land each rule's authority (predict/job_config.py)
and delete the adapter-side copy in the SAME commit — at every commit
exactly one enforcement site exists. Gates land in the render/submit
entry points of the adapter so callers cannot skip them.

**Tech Stack.** Python 3.12, `.venv/bin/python` (repo uv venv),
pytest. No new dependencies (binding: no whisper/pyannote, local-only).

**Spec.** `docs/specs/s1-wangp-jobconfig-ref2va.md`.

## Global Constraints

- Absolute paths: /Users/Shared/HermesWorkspace/wangp-dspy.
- Staging ban: `git add <path>` per file; never `git add .`.
- Sequencing safety: adapter inline rule deleted ONLY after its
  authority's tests are green in the same commit. Gates G1-G6 are
  RED-first: failing test committed before implementation.
- Tier boundary: code+tests+these two docs only; no template edits.
- Shared-checkout hazard: confirm `git branch --show-current` before
  every commit; never commit on main.

## File Map

| File | Action | Task |
|------|--------|------|
| `docs/specs/s1-wangp-jobconfig-ref2va.md` | create | 0 |
| `docs/plans/s1-wangp-jobconfig-ref2va.md` | create | 0 |
| `tests/test_job_config.py` | create | 1 |
| `predict/job_config.py` | create | 1 |
| `host/wangp_adapter.py` | modify (delegations, same-commit deletions) | 1-2 |
| `tests/test_render_profiles.py` | create | 2 |
| `predict/render_profiles.py` | create | 2 |
| `scripts/check_job_config.py` | create | 3 |
| `tests/test_entry_point_gates.py` | create (RED per gate) | 4-9 |

## Tasks

### Task 1 — WanGPJobConfig authority (move-per-rule)
- [ ] **Step 1.1** — RED: tests/test_job_config.py covering the five
  rules against the NEW API (they fail: module absent). Commit.
- [ ] **Step 1.2** — GREEN: predict/job_config.py (dataclass +
  validate_job_config + normalize_frame_count moved); adapter's five
  inline copies deleted same commit; adapter delegates.
  Expected: test_job_config green; full suite green (>=406);
  `grep -n "normalize_frame_count\|H3_FRAMES_MIN" host/wangp_adapter.py`
  shows import-only. Failure gate: any pre-existing test red → stop.

### Task 2 — Render profiles (Strategy)
- [ ] **Step 2.1** — RED: tests/test_render_profiles.py — H3 shape
  unchanged; Ref2VA: image_refs present+readable, audio 'A' typed,
  guide==shot duration, 4-15s cap, token contiguity. Commit.
- [ ] **Step 2.2** — GREEN: predict/render_profiles.py; adapter uses
  profile.build_settings(). Expected: profiles green, suite green.

### Task 3 — CLI surface
- [ ] **Step 3.1** — scripts/check_job_config.py (0/1/2 exits) +
  tests. Expected: CLI validates a JSON job file, exit codes pinned.

### Tasks 4-9 — Gates G1..G6 (RED-first, one commit pair each)
- [ ] **Step N.1 RED** — failing entry-point test in
  tests/test_entry_point_gates.py (two tests: typed rejection naming
  the gate; entry point exercised directly). Commit.
- [ ] **Step N.2 GREEN** — gate implemented IN the entry point.
  Expected: gate tests green; suite green; entry-point test does NOT
  call the gate function directly.
  Failure gate: if implementing a gate requires touching a file not
  on the File Map → STOP and report.

## Notes

- Template gap (surfaced, not fixed here per dispatch): the spec
  TEMPLATE's "History strategy" section presumes repo/file-move
  stories; for gate/refactor work it reduces to one sentence (as
  written). No blocker.
