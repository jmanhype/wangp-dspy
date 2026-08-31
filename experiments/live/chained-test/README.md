# Two-Shot Chained Proof — experiments/live/chained-test/

Goal: prove (or disprove) that last-frame chaining makes shot 2
CONTINUE rather than reset the scene, using WanGP's H3 multishot path.

## Investigation findings (2026-08-31)

- `models/minimax_h3/multishot.py::generate_multishot` already
  implements last-frame chaining internally: after each shot it keeps
  `prev_last_frame = decoded_video[:, -1:]` and passes it as the next
  shot's `image_start` to `pipeline.generate(...)`. Shot-1 can take an
  optional user `image_start`. For shots > 0 the seam frame is trimmed
  (`decoded_video[:, 1:]`) plus matching audio samples.
- `wgp.py::process_tasks_cli` (line ~8824) routes any task whose
  `params.script` is set to `generate_multishot`, mapping
  `width/height/frames_per_shot/num_inference_steps/seed/fps` from the
  validated params and honoring `output` for the final mp4 path
  (audio muxed via ffmpeg).
- CLI: `venv/bin/python wgp.py --process shot-config.json --profile 3
  --attention sdpa [--dry-run]`. The settings JSON must be a FLAT
  params dict (a dict file is wrapped whole as one task's params; the
  id/prompt/params manifest shape only works inside a LIST).
- 3090 checkout state: branch `rebase-onto-upstream`,
  `frames_minimum` already patched 107 -> 56
  (`36d7cc9 feat: unlock k<6 grid`).
- Bug found + fixed (3090 local, not committed upstream):
  `multishot.py` imported `FPS` from `pipeline`, which no longer
  exports it (upstream removed it during the rebase). Added
  `FPS = 24` local constant — import restored.
- venv: `venv/bin/python` (system python3 lacks mmgp). Use
  `venv/bin/python wgp.py ...`.

## Files

- `shot-config.json` — flat params: model_type `minimax_h3_fl2va`,
  script with 2 subject-mode shots (dungeon master, `<Subject 1>`
  definitions, retention_analysis, ambient actions, (S1) `<d>[en]`
  dialogue, overall_soundscape, non_diegetic_music: N/A), separated by
  `---`; 56 frames/shot (k=3 grid point), 832x480, seed 7, 20 steps.
- `run-chained-test.sh` — driver (tmux/nohup wrapper around wgp CLI).
- `verify_chained.py` — verification: per-shot 64x36 thirds motion
  metric (threshold 2.0), boundary frame extraction around the seam
  (frames 54-58), seam luma-jump vs in-shot motion ratio.
  Verdict: CONTINUES if seam jump <= 3x in-shot mean diff and shot 2
  motion alive; RESETS if seam jump > 3x; else INCONCLUSIVE.

## Run log

See RESULTS.md (populated after the render + verification).
