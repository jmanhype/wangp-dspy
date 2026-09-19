---
id: WD-h25b
title: "S4: Satan's Mom — multi-shot MV through the full governed pipeline"
status: open
priority: 1
type: task
parent: WD-j9nx
created_at: 2026-08-28T19:10:45Z
created_by: speed
updated_at: 2026-08-28T19:10:45Z
content_hash: "sha256:73075fe944397ae817c487b459d5ef4b505b8504bf7e8d386705e8cafa134f0e"
---

## Description
# S4: Satan's Mom — multi-shot MV through the full governed pipeline

Phase 2 film lane, critical path. The film finishes here as the story's acceptance test.

## Scope

The complete Larson dungeon gag film — three cuts, each a Ref2VA render driven by
the proven S2.5 job shape, assembled into one final mp4 with real TTS audio remuxed
over the renders (H3 audio never trusted, G4).

1. **Master plates** — locked compositions per cut (master-first doctrine; G6).
   Cut-1 master = /tmp/s25/master.png (sha256 d7ca2074...). Cuts 2-3: new masters
   generated in the same scene/style for continuity.
2. **Dialogue** — three-voice script (grandma + prisoner + devil) via edge-tts.
   Diarization timeline authored honestly out-of-repo (no whisper/pyannote in repo
   paths); validated by S2 CLI; converted to <d>Name</d> attribution blocks.
3. **Per-cut Ref2VA renders** on the 3090 using the PROVEN S2.5 job shape:
   model_type minimax_h3_ref2va_pruned, video_prompt_type I, image_refs as list,
   attention sdpa, audio_prompt_type A, guide == shot duration, 4-15s cap.
4. **NEVER trust H3 audio** — remux the real TTS lines over the renders (G4).
5. **Assembly** — ffmpeg concat of remuxed shots; whisper-gate the final.
6. **Run records** for every shot (S2.5 run_record.json shape).
7. **QC** per shot (VLM critic on 3090) + final whisper gate.

## Constraints

- 20s max per shot (Ref2VA profile enforces 4-15s; hard ceiling respected).
- Cuts on dialogue boundaries only.
- All six gates honored: G1 audio-A-only-on-ref2va, G2 guide==shot-duration,
  G3 QC-consumes-artifact, G4 H3-audio-never-trusted, G5 <d>-or-silence contract
  (S3-G5a attribution REQUIRED), G6 master-lock precondition.
- Script-files for any complex shell (AGENTS.md discipline).
- state.json updated at every step.
- faster-whisper/pyannote never in repo code paths (execution external).

## Deliverable

Finished mp4 + full evidence chain (run records, QC verdicts, timeline,
attribution, master locks, job JSONs) + PR. This is the movie.

## Acceptance Criteria

- [ ] Three master plates locked (G6), sha256 recorded
- [ ] Timeline validated by scripts/check_diarization.py (exit 0)
- [ ] Attribution blocks rendered via S2 converter (<d>NAME</d> form)
- [ ] Three Ref2VA renders on 3090 (proven job shape), artifacts pulled back
- [ ] Per-shot VLM QC verdicts (critic qwen38-27b, surreal threshold 4.5)
- [ ] Real TTS remuxed over all renders (G4 honored structurally)
- [ ] Final mp4 assembled (ffmpeg concat), whisper-gated
- [ ] Run record per shot + state.json trail
- [ ] PR opened with evidence chain; Luna + GLM gates dispatched

## Acceptance Criteria


## Design


## Notes


## History


## Links
- Parent: [[WD-j9nx]]

## Comments
