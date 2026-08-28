
### 2026-08-27T23:15:00Z luna-tester (VALIDATOR)
Luna VALIDATOR pass on PR #37 @ 903fee7 (new head, above 46b5443). READ ONLY.

**Item 1 — Grep-proof (5 rules, single authority): PASS**
Each rule has exactly ONE enforcement site in predict/job_config.py:
- Rule 1 (force_fps:str): job_config.py:120 (isinstance check) — adapter only passes str(FORCE_FPS), no re-check.
- Rule 2 (>=96 floor): job_config.py:130 (SHOT_LENGTH_FLOOR_FRAMES) — the inline try/except in build_settings at 46b5443 is DELETED at 903fee7; profile_selector's floor is a documented distinct selection-time layer (re-exports the same constant, adds no independent bound).
- Rule 3 (17k+5 snap): job_config.py:47 normalize_frame_count (sole def); applied in __post_init__ (line 81). Adapter imports it, never re-derives. math.ceil appears exactly once in non-test code.
- Rule 4 (flat JSON): job_config.py:106-110 (to_settings_doc walk) — sole nested-value rejection. Ref2VA rides extra=... with flat=False scoping (documented review ruling).
- Rule 5 (\n---\n separator): job_config.py:26 SCRIPT_SEPARATOR (sole literal def); adapter + render_profiles import it; identity pinned by test_separator_single_constant.
Zero duplicate enforcement sites in adapter or elsewhere. The claimed blocker fix is confirmed real.

**Item 2 — Entry-point unskippability (6 gates): PASS (with note)**
tests/test_entry_point_gates.py exercises the REAL entry points, never gate functions in isolation:
- G1: a.submit(..., audio_prompt_type="A") → WanGPError "G1" (both sides: generic reject + Ref2VA carrier accepted via test_render_profiles).
- G2: a.submit(profile="ref2va", guide_duration_s=7.33, shot_duration_s=8.0) → "G2" naming both durations.
- G3: a.qc_artifact(missing.mp4, spec_text="valid") → "G3"; valid artifact + mutated spec → verdict unchanged ("artifact-verdict").
- G4: a.submit(trust_h3_audio=True) → "G4"; a.trust_h3_audio(brief) → "G4" regardless of flags.
- G5: a.submit(_brief("[John] looks up")) → "G5"; ALSO enforced at build_settings/render over all 5 fields (review fold-in, test_g5_rejected_at_render_entry_point).
- G6: a.generate_brief("a kaiju video") with no lock → "G6".
NOTE (non-blocking): G3/G4 also have thin standalone entry methods (qc_artifact/trust_h3_audio) that are themselves the entry points — structurally fine, but G3 does not yet sit inside run_pipeline's QC call path (run_pipeline uses qc_factory directly). Acceptable for S1 scope per board AC (gate fires on the named entry point); flag for S3 wiring.

**Item 3 — Spec compliance vs board AC: PASS**
- AC1 TDD RED-first: 3 genuine RED commits (3c7b534 task1 collection-fail — module absent at RED time; 11e375f task2; 863cc47 tasks4-9, 12 tests) each followed by GREEN. Trail visible in branch history.
- AC2 six gates structural: see Item 2.
- AC3 five rules absorbed + CLI: see Item 1 + CLI verified live (exit 0 valid / 1 sub-floor / 2 missing file).
- AC4 Ref2VA complete: image_refs present+readable, audio 'A' typed, guide==shot exact (names both), 4-15s cap, token contiguity — all tested in test_render_profiles.py.
- AC5 full suite green: 442 passed, 0 failed (baseline 406 → +36, matches commit message 438→442 after review round).
- AC6 spec/plan pair: both files present; spec has Failure and recovery section (line 125); plan has 4 "Expected:" lines + Notes section with template gap noted.
- AC7 binding constraints: zero faster-whisper/pyannote matches; cloud endpoints (api.z.ai) pre-existing on main, NOT introduced by this PR; Maestro cited as spec only.
- AC8 PR-only governed cycle: isolated branch off main, PR open, Luna acceptance = this pass.

**Item 4 — Full suite in repo .venv: PASS**
.venv/bin/python -m pytest tests/ → 442 passed, 1 warning (pre-existing starlette deprecation), 11.46s. Exit 0.

**Item 5 — Ref2VA spot-check vs requirements: PASS**
- image_refs carrier: required, present + readable (os.path.isfile) at submit; rides to_settings_doc(extra=...) as sanctioned non-scalar extension.
- audio A typed: Ref2VA REQUIRES 'A' (rejects anything else); H3/generic path REJECTS 'A' — boundary stated in one sentence in both spec and code, both sides tested.
- 4-15s cap: REF2VA_MIN_SHOT_S=4.0 / MAX=15.0, enforced with typed rejection; 3.5 and 15.5 both rejected in tests.
- Token contiguity: Picture/Audio N regex; indices must be contiguous from 1 and within ref count; Picture 2 with 1 ref rejected; Picture 1 plus Audio 1 accepted.
Minor (non-blocking): frames_per_shot=max(frames, 96) at render_profiles.py:136 hardcodes the 96 literal instead of importing SHOT_LENGTH_FLOOR_FRAMES — cosmetic duplication of the constant's VALUE (not its enforcement); enforcement still flows through WanGPJobConfig construction. Worth a one-line nit for the author.

**RECOMMENDATION: PASS** — all five mechanical items pass on the NEW head 903fee7. The 46b5443 blocker (duplicate enforcement in build_settings) is genuinely fixed. No regressions. Two non-blocking nits for relay: (1) Ref2VA max(frames, 96) literal could import the constant; (2) G3 not yet wired into run_pipeline's QC path (S3 territory).
