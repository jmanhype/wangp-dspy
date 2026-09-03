# Director Run — the first live film runbook (2026-09-03)

The record of the director's first-ever live run: clip 1 approved
("looks good"), full film delivered. Seven wiring-boundary defects
were patched ad-hoc on the 3090 box mid-run; ALL of them are now
landed at source on `feat/director-convergence` with regression tests
(`tests/test_director_convergence.py`). This page is the clean-clone
runbook.

## First-run command (verbatim)

On the 3090, from the repo checkout:

```
WANGP_SSH_TARGET=localhost \
.venv/bin/python scripts/run_film.py \
    --script s4/films/satans-mom/script.txt \
    --plates s4/films/satans-mom/plates/ \
    --characters \
    "Grandma:S1:a weathered woman with silver braids, seated left" \
    "Seth:S2:a lean man with soot-streaked cheeks, standing right" \
    --whisper-map s4/films/satans-mom/qc/whisper_map.json \
    --db s4/films/satans-mom/run/jobs.db
```

Pre-flight sanity (no GPU, no host calls — the acceptance gate the CI
runs too):

```
.venv/bin/python scripts/run_film.py --script <script> --plates <dir> \
    --characters ... --dry-run
```

## Environment variables

| Var | Default | Meaning |
|---|---|---|
| `WANGP_SSH_TARGET` | `3090` | SSH target for the render host. Set `localhost` when running ON the box (skips the ssh hop). |
| `WANGP_QC_URL` | `http://localhost:8000/health` | Preflight QC healthz probe URL. |
| `WANGP_SANCTIONED_DIRS` | keepers/Wan2GP outputs/qc_media | `:`-separated sanctioned asset roots for ref2va containment. |
| `WANGP_STALENESS_S` | `600` | Stale-active job heartbeat timeout. |
| `WANGP_LOAD_STALL_S` | `300` | Load-progress watchdog before first Denoising line. |

When `WANGP_SSH_TARGET=localhost`, run_film wires the
`localhost_pre_render` hook (DEFAULT-ON): the phased VRAM dance the
box scripts performed — QC stack up for preflight, killed again
before the render leg so the render gets the VRAM. Pass
`pre_render=` explicitly to override; `pre_render=None` from the API
means "use the default", pass a no-op lambda to force-disable.

## Plates dir layout

```
plates/
  anchor.png        # two-shot composition anchor (re-anchor every 3 cuts)
  Grandma.png       # identity plate, one per character
  Seth.png
```

Run dir layout (created by run_film):

```
<run>/              # parent of jobs.db
  jobs.db           # durable queue (one chained job per clip)
  audio/clipNNNN.wav  # materialized silence guides (plan time)
  render/clipNNNN/    # renders + chain_last_frame.png extractions
```

## The seven boundaries

Each of these failed the live run exactly once; each fix was
live-verified on the box before landing here.

1. **`kind` literal routing.** `plan_to_clips` emitted the product
   mode enum value (`REF2VA_IDENTITY_AUDIO`) as `kind`, but
   `job_lane()` only recognizes the literal `ref2va_render` — every
   job silently fell to the fl2va lane. Clips now emit
   `kind="ref2va_render"`; the enum stays as `mode`.

2. **Audio guides are materialized at plan time.** The plan referenced
   `audio/clipNNNN.wav` paths that did not exist — the ref2va runtime
   fails closed on missing guides. `plan_to_clips` now writes ffmpeg
   silence (`anullsrc`, 24 kHz mono pcm_s16le) of `duration_s` into
   `<run>/audio/clipNNNN.wav` with ABSOLUTE paths, and fills
   `audio_provenance{source_master, vocal_stem, whisper_map,
   keeper_window_s}` so `AudioGuideProvenance` constructs cleanly.

3. **Duration trio alongside frames.** The runtime reads durations,
   not frame counts. Clips now emit `shot_duration_s` +
   `guide_duration_s` (both `round(frames/24, 3)`) +
   `audio_length_frames` next to `frames`.

4. **G5 exempts `<d>[Language]` tags.** The official H3 dialogue
   format `<d>[English] ...</d>` tripped the malformed-marker scan.
   `_g5_check` strips `<d>\s*\[[A-Za-z]+\]` BEFORE the bad-marker
   regex: `[English]` passes, `[John]` still rejects.

5. **`_Ref2VABrief` full attr set.** The duck-typed brief only carried
   four attrs; the G5 loop and `brief_to_prompt` touch all seven and
   crashed at render time. It now defaults `audio_direction=""`,
   `identity_lock=""`, `negatives=""`.

6. **Chain auto-advance in `drain_once`.** When a chain job completes,
   the dependent job's `image_refs[0]`
   `chain://clipNNNN/last_frame` placeholder is materialized from the
   completed job's mp4 (the proven `ffmpeg -sseof -0.1` extraction,
   same r2i machinery) BEFORE the next pick. The director executor
   renders through `adapter.render_for_job` (the hardened per-job
   seam), never the legacy brief-based `render()`.

7. **On-host execution.** `WANGP_SSH_TARGET` overrides the SSH target
   (default unchanged); `localhost` additionally turns on the
   QC-up-for-preflight / kill-for-render pre_render hook
   (`scripts/run_jobs.localhost_pre_render`).

## Acceptance gate

`tests/test_director_convergence.py::TestDryRunGoldenAcceptance` runs
`run_film --dry-run` on a 2-line fixture and asserts every emitted
clip passes `job_lane` (→ ref2va), constructs
`AudioGuideProvenance`, carries the duration trio, and builds a brief
→ prompt without hand-fixing. It fails on every pre-fix defect —
first-try on a clean clone is now the tested contract.
