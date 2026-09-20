# S4 — Satan's Mom: the finished film (evidence chain)

Deliverable for task t_e8138ca0 / story WD-h25b. The complete Larson dungeon
gag film through the full governed pipeline, plus its evidence chain.

## The movie

`films/satans-mom/final/satans_mom.mp4` — 34.78s, 6 dialogue shots across 3
master-plate compositions, 832x480 @ 24fps. sha256 in `runs/final_film.json`.

## Pipeline (all six gates)

| step | gate | result |
|---|---|---|
| script + edge-tts (3 voices) | G3 authored-honest timeline | 6 segments, 33.672s, check_diarization.py OK |
| master plates (locked) | master-first doctrine | cut1 = locked S2.5 plate; cut2/cut3 regenerated, VLM-verified |
| jobs via adapter.submit | G1 jobconfig schema + G2 Ref2VAProfile | PROVEN S2.5 shape: minimax_h3_ref2va_pruned, video_prompt_type I, image_refs list, attention sdpa, audio_prompt_type A, guide==shot duration |
| renders on 3090 | sequential driver w/ GPU-free preflight | 6/6 cuts, seeds 43-48 |
| remux | G4 never trust H3 audio | H3 audio stripped; real TTS lines muxed (-shortest) |
| per-shot QC | G5 comedy >= 7.0 | qwen38-27b VLM: 8/9/9/9/7/9 — all PASS |
| assembly + whisper | G6 final gate | faster-whisper small: all 6 lines verbatim in order — PASS |

## Evidence

- `films/satans-mom/runs/cut{1..6}.json` — per-shot run records: live sha256 of
  render/remux/master/guide, settings shas from the 3090, QC verdicts, gate map.
- `films/satans-mom/runs/final_film.json` — final film hash, whisper transcript,
  disclosures (frame quantization trims, CPU-offloaded VLM, flaky ssh under load).
- `films/satans-mom/qc/whisper_final.json` — raw whisper gate output.
- `films/satans-mom/state.json` — step-by-step state with timestamps.
- `films/satans-mom/dialogue/provenance.json` + `PROVENANCE.md` — R0 key discipline.

## What is NOT committed (by size, kept on disk at s4/films/satans-mom/)

renders/, remux/, qc/*_fs.mp4 faststart copies, dialogue mp3/wav intermediates,
masters pngs — ~45MB of media. The committed tree carries the final film, all
JSON/text evidence, and the scripts that reproduce every step.

## Scripts (reproducible steps)

- `scripts/build_jobs.py` — G1/G2 job construction through adapter.submit
- `scripts/remux_tts.py` — G4 remux (idempotent)
- `scripts/qc_assemble.py` — G5 QC leg + concat assembly
- `scripts/write_run_records.py` — run-record/evidence writer
- `scripts/render_driver_v2.sh` — sequential 3090 render driver (OOM fix)
