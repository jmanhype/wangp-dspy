# BUILD ORDER — wangp-dspy repo-owned film path
# Status: 2026-09-07, post gap-audit. Owner: operator. Executors: Codex (PRs), Hermes (creative/validation).
# Rule: one finding = one PR. Acceptance test at bottom. No side scripts —
# any bridge script written during execution is itself a new finding.

## Finding 0 — checkout identity/preflight  [BLOCKS ALL]
- Sync to /Users/Shared/HermesWorkspace/wangp-dspy, origin/main @ 1138c2a
- Preflight records repo root + commit SHA in every run ledger
- Reclassify audit #3 as checkout false positive; #7 as external-asset
  availability (3090 dialogue wavs — fixture contract covers tests)

## Render blockers (nothing renders until 0-6 land)
1. #4  — 48-frame/2-second continuation profile (96f floor + grid policy)
2. #14 — shared Ref2Va model-type constant (kill ref2va_lip_sync mismatch)
3. #5  — ContinuationExtras wired + resolved last-frame artifacts
          (verify post-sync; file exists at predict/continuation_lane.py —
           keep only if present-but-unwired)
4. #6  — Pipeline emits per-job render requests (valid terminal states,
          per-cut jobs)
5. #13 — executor production seam through render_for_job() only
          (adjacent to #6, separate PR)

## Evidence layer (gates around the working seam)
6. #8  — audio prep/normalization (>=2s, trim-to-cut, +9dB, single-speaker,
          RMS checks — fail closed)
7. #9  — Whisper pre/post transcript gates, evidence persisted
          (adjacent to #8, separate PR)
8. #16 — Picture-N/speaker prompt binding (typed builder + assertions)
9. #10 — speaker-ID manifest (versioned schema, turn mapping)

## Assembly + data layer
10. #15 — chain advancement (last-frame extraction) + media assembler
11. #1/#2/#12 — premise index, DirectorRun orchestrator, dataset-run
           emission (append-only, content-addressed)

## Blocking QC layer
12. #11 — integrated vision judge (right mouth / right action per cut);
           mandatory before a ledger verdict can be emitted

## ACCEPTANCE TEST (binary, operator-ratified; amended 2026-09-07):
> Fresh clone at a recorded SHA; repo-only execution; six ~2.33-second
> grid-aligned (56-frame, 5+17x3) cuts; render_for_job(); pre/post
> Whisper gates; dialogue WAVs padded ~0.33s silence tail via repo
> audio-prep; chained last frames; assembled output; complete run ledger.
> (Amendment: original "six 2-second cuts" wording replaced — H3's latent
> grid cannot produce exactly 48 frames; 45f/1.875s artifacts are REJECTED,
> not waived. Ratified by operator 2026-09-07 with #28.)

Any `ref2va` ledger verdict also requires persisted visual-judge evidence;
`vision_judge: None` is a hard QC failure, not an acceptable placeholder.
