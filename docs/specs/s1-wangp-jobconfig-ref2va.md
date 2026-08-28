# SPEC — S1: WanGPJobConfig schema + Ref2VA render profile (film lane opener)

Status: DRAFT → APPROVED (flip at sign-off) · Story: WD-l5bx · Author: qwen-escalator · Date: 2026-08-28

Format source: `docs/specs/TEMPLATE.md`; extraction lineage:
shuohao-skills spec-driven-evolution.md (spec = why, plan = how).

## Goal

A single authoritative WanGPJobConfig schema + validator absorbs every
scattered adapter assert (frame floor, 5+17k grid snap, force_fps
string typing, flat-JSON enforcement, multi-shot separator), and a
second render profile (Ref2VA) joins H3 behind one profile Strategy
surface — with six operator-ruled gates structurally wired into the
submit/render ENTRY POINTS so invocation is not optional.

**Success invariant.** Every frame/fps/separator rule has exactly one
authority (grep-provable: zero duplicate enforcement sites), and each
of the six gates fires by exercising the entry point directly with a
typed error naming the gate.

## Layout & scope

- NEW `predict/job_config.py` — WanGPJobConfig frozen dataclass +
  `validate_job_config()` importable API + the five absorbed rules +
  `normalize_frame_count` moved here (single authority).
- NEW `predict/render_profiles.py` — RenderProfile Strategy base,
  H3Profile (extracted from the adapter's H3-specific settings
  shaping), Ref2VAProfile (image_refs, audio_prompt_type 'A',
  guide-alignment, 4-15s cap, `<Picture N>`/`<Audio N>` token
  contiguity).
- MODIFY `host/wangp_adapter.py` — adapter delegates rule checks to
  job_config (its inline copies DELETED in the same commits); the six
  gates land in the submit/render entry points.
- NEW `scripts/check_job_config.py` — CLI validator surface.
- NEW `docs/specs/` + `docs/plans/` pair (this document + plan).
- Tests: `tests/test_job_config.py`, `tests/test_render_profiles.py`,
  `tests/test_entry_point_gates.py` (RED-first per gate).

**Non-goals.**
- Diarization/speaker ID — S2's problem (no faster-whisper/pyannote
  anywhere, operator binding constraint).
- QC quality calibration — G3 wires QC to consume the artifact; the
  critique stack itself is untouched.
- Maestro code vendoring — ADAPT-TO-IDEA only; Maestro file:line
  refs below are SPECS, implemented clean-room (non-commercial
  license, operator binding constraint).
- Cloud inference — nothing in this story adds endpoints
  (local-only binding constraint).

## Maestro spec references (clean-room sources)

- Maestro `wgp.py` settings shaping (force_fps string typing because
  wgp's `get_computed_fps` len()s the field; flat settings JSON) —
  behavior observed in our own pinned-vlt probes and prior WD-u4rv/
  WD-izly pins, which already encode the measured contract.
- Ref2VA lip-sync job shape: image_refs + audio_prompt_type 'A' +
  guide-alignment — matches the sgflix-music-video skill contract
  (audio_prompt_type 'A' REQUIRED; guide slice = exact shot length).
  Cited as spec intent; no Maestro code copied.

## The six gates (operator ruling — guaranteed invocation)

Placed in the submit/render ENTRY POINTS, not optional pre-checks:

- G1 audio-'A' hard-reject at submit: the GENERIC (H3-style) submit
  path rejects audio_prompt_type='A' before any render work. Boundary
  in one sentence: Ref2VA is the only sanctioned carrier of 'A'
  audio-prompt jobs; the generic path refuses them so H3 never
  receives an audio-prompt job it cannot honor.
- G2 guide==shot-duration exact match (Ref2VA): typed rejection
  naming BOTH durations.
- G3 QC consumes artifact, not spec: QC input is the rendered file
  (path/hash readback); a valid spec never substitutes for the
  artifact.
- G4 H3-audio-never-trusted: any path passing H3-generated audio
  through without the audio-critic/QC pass is refused, typed,
  regardless of flags.
- G5 `<d>`-or-silence prompt contract: speaker tokens in script text
  are `<d>Name</d>`-form or explicit silence; malformed markers
  rejected at validation (groundwork for S3).
- G6 master-lock precondition: no lock record → brief generation
  refuses, typed; render cannot start from an unlocked project.

## History strategy

In-place edit on a feature branch (the repo's standing PR-only flow);
no history rewrite; the plan's commit sequence gives per-gate
red→green trail. Reason: single-repo additive refactor — clean
snapshot/rebase buys nothing and risks the shared checkout.

## Cleanup & sequencing

Adapter-side rule copies are deleted in the SAME commit that lands
the corresponding job_config authority (move-per-rule), so at every
commit the rule has exactly one enforcement site. Order: force_fps
typing → frame floor → grid snap → flat-JSON → separator → profiles
→ gates G1..G6. Safety condition for each deletion: the new
authority's tests green before the adapter copy dies.

## Commit & GitHub flow

- Branch: `feat/wd-l5bx-wangp-jobconfig-ref2va` off main @ ed6420a.
- PR-only; never direct to main; no force-push.
- Explicit file staging only (`git add <path>`), never `git add .`.

## Verification

```bash
$ .venv/bin/python -m pytest tests/ -q
# Expected: full suite green, count >= 406 (baseline 406 at ed6420a)

$ grep -n "H3_FRAMES_MIN\|normalize_frame_count\|force_fps.*str\|SHOT_LENGTH_FLOOR" host/wangp_adapter.py
# Expected: only imports/delegations to predict.job_config — no
# inline rule enforcement remains

$ .venv/bin/python -m pytest tests/test_entry_point_gates.py -q
# Expected: 12+ passed (2 per gate: typed rejection + entry-point
# invocation)
```

Full-suite gate: `.venv/bin/python -m pytest tests/ -q` must report
the measured green count; tail line pasted into the PR description.

## Failure & recovery

- Recoverable: everything — the work lives on a feature branch;
  mid-step failure = stop, leave the branch, report. Old behavior
  remains on main untouched.
- NEVER touched during recovery: the shared checkout's uncommitted
  paivot tooling files (.gitignore, .paivot/config.yaml) and any
  other agent's WIP.
- Stop-the-world vs retry: operator (via sol-max dispatch); standing
  stop conditions: double-BLOCK, provider death, operator interrupt.
