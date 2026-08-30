# SPEC — S2: Ref2VA audio_guide data plane (provenance + audio policy + QC fields)

Status: DRAFT → APPROVED (flip at sign-off) · Story: WD-a1d9 · Author: sol-max (orchestrator) · Date: 2026-08-30

Format source: `docs/specs/TEMPLATE.md` (same lineage as S1/WD-l5bx).

## Goal

Give Ref2VA a real audio data plane. Today `Ref2VAProfile.build_settings`
accepts `audio_prompt_type='A'` but no audio asset actually flows: there is
no audio_guide, no provenance, no audio policy on the output, and no
audio-aware QC schema. This slice adds all four as typed, validated,
tested structures — code and tests only, NO remote GPU render (mini has
~4.4 GiB free; binding constraint).

**Success invariant.** Every audio-bearing Ref2VA job that passes
validation carries: (1) `audio_prompt_type='A'` plus a readable
`audio_guide` path, (2) full provenance (master / vocal stem / Whisper
map / keeper window), (3) an explicit H3 audio discard/remux policy, and
(4) a QC schema with Qwen2-Audio-7B critic fields and
mouth/audio/visual fields — and the generic H3 GEPA A/B harness is
byte-for-byte untouched (proven by test + grep).

## Layout & scope

- NEW `predict/audio_dataplane.py`:
  - `AudioGuideProvenance` frozen dataclass: `source_master` (path),
    `vocal_stem` (path), `whisper_map` (path), `keeper_window_s`
    (start, end) — all required, typed `AudioDataPlaneError` on
    missing/unreadable paths, end > start, window within [0, master
    duration not checkable offline → check >= 0 only, documented].
  - `AudioPolicy` frozen dataclass: `discard_rendered_audio: bool =
    True` (H3/Ref2VA generated audio is NEVER trusted — G4 tie-in),
    `remux_source: str` = one of {"source_master", "vocal_stem"},
    `remux_window` = keeper window. Renders as a dict into the settings
    doc.
  - `Ref2VAAudioQC` schema (dataclass / dict contract): critic
    fields `critic_model="Qwen2-Audio-7B"`, `critic_version`,
    plus score fields `mouth_sync`, `audio_fidelity`,
    `visual_motion_match`, `audio_artifacts` (0-10 floats, None =
    not yet judged) and free-text `notes`. A `to_dict()` that round-trips.
- MODIFY `predict/render_profiles.py` — `Ref2VAProfile.build_settings`
  gains required kwargs `audio_guide: str` (path readable at submit,
  same treatment as image_refs), `audio_provenance:
  AudioGuideProvenance` (validated), `audio_policy: AudioPolicy`
  (default constructed: discard=True, remux_source="source_master").
  The settings doc `extra` gains `audio_guide`, `audio_provenance`
  (as dict), `audio_policy` (as dict), and `audio_qc` initialized
  from `Ref2VAAudioQC.empty()`. H3Profile and the generic path are
  NOT modified beyond import surface.

  **Qwen design review ruling (2026-08-30, required finding —
  resolved):** rule 4 (flat JSON) is scoped to the GENERIC/H3 lane;
  the Ref2VA lane carries nested dict payloads under `extra` as an
  EXPLICIT, documented, TESTED exemption (option c), extending the
  S1 precedent where `image_refs` (a list) was already a sanctioned
  Ref2VA-only non-scalar extension. The exemption is typed: a test
  asserts (1) `to_settings_doc(flat=True)` still rejects nested
  values on the generic path, and (2) Ref2VA output is exempt only
  via `flat=False`. Any future doc-hash caching MUST exclude `extra`
  keys (noted for the manifest/QC slice). `vocal_stem` is REQUIRED:
  the Ref2VA lane is lip-sync-only; instrumental-only guides are out
  of scope (auditable assumption, per review).
- NEW tests `tests/test_audio_dataplane.py` (RED-first):
  - provenance: rejects missing file / missing stem / missing whisper
    map / end<=start window / negative start (each typed
    `AudioDataPlaneError`, message names the field).
  - policy: discard default True; remux_source enum rejection.
  - QC: to_dict round-trip; critic_model default "Qwen2-Audio-7B";
    None scores allowed (pre-judgment state).
- EXTEND `tests/test_render_profiles.py`:
  - Ref2VA happy path now requires audio_guide (existing tests
    UPDATED, minimal-diff — existing assertions preserved).
  - audio_guide unreadable → typed ProfileError.
  - missing audio_provenance → typed ProfileError naming it.
  - settings doc extra contains audio_guide + provenance dict +
    policy dict + audio_qc dict.
  - H3 harness preservation: `H3Profile.build_settings` output for a
    fixed brief fixture is IDENTICAL before/after (snapshot test using
    a checked-in expected dict, and a test asserting no
    `audio_dataplane` keys leak into H3 output).
- Grep gate test: `test_h3_harness_untouched` asserts
  `evaluate/` and `training/` source contains no `ref2va|audio_guide`
  additions (guards the GEPA A/B harness).

## Non-goals

- Actual remux execution (ffmpeg) — policy is data, execution is a
  later slice with the render driver.
- Running Qwen2-Audio-7B — schema fields only.
- GPU/render smoke — explicitly out (4.4 GiB free).
- Speaker gate / diarization (S3 lane).

## Commit & GitHub flow

Branch `feat/wd-a1d9-ref2va-audio-dataplane` off current worktree
branch; PR-only; explicit file staging; RED-first commit trail
(tests-RED then GREEN per module).

## Verification

```bash
$ .venv/bin/python -m pytest tests/ -q
# Expected: all green, count >= existing baseline (measure first; paste tail in PR)
$ .venv/bin/python -m pytest tests/test_audio_dataplane.py tests/test_render_profiles.py -q
# Expected: all pass, new tests >= 15
```

## Failure & recovery

Feature branch; mid-step failure = stop, leave branch, report. Never
touch the dirty main checkout or other agents' WIP.
