# Chain Controller — H3 Last-Frame Chaining

Continuous multi-shot episodes from director-emitted shots: each shot's
LAST FRAME becomes the next shot's FIRST FRAME via H3's trained
continuation task, with a Chain Plan JSON carrying per-clip audio
timing and resume-safe state.

Pure config/plan layer — no GPU, no rendering, no ffmpeg.

## Ported technique (ecosystem ground truth)

Logic ported (no ComfyUI dependency) from two ComfyUI packs:

1. **joeygambino/MiniMax-H3-Multishot-Workflow**
   (https://huggingface.co/joeygambino — MiniMax-H3-Multishot-Workflow)
   - Each shot's last frame seeds the next shot's first frame.
   - The duplicated boundary frame is TRIMMED downstream (TODO here).
   - Reference plates stand DOWN after shot 1 — continuity is carried
     by chaining, not re-anchored.
   - A post-chain color/texture normalize pass counters drift (TODO).

2. **RwGrid/ComfyUI-MiniMaxH3-Contex-Loop** — `H3_CHAIN_FORMAT_GUIDE`
   (https://github.com/RwGrid/ComfyUI-MiniMaxH3-Contex-Loop)
   - Chain Plan JSON: `global_prompt` prefix pins wardrobe/identity
     across scenes ("Throughout every scene S1 wears ...") + per-clip
     cards `{prompt, seed, steps, audio start/duration, speaker
     attribution, resume-safe state (clip index, completed flag)}`.
   - Frame math @24fps: clip 1 delivers full frames (124/243/362 for
     5/10/15s); later clips deliver 22 fewer — the context overlap
     consumed by chaining.

## Our frame grid

This repo's durations live on the 17k+5 frame grid @24fps
(5/22/39/56/73/... frames — see `services/director/renderers/policy.py`).
The controller accepts any on-grid duration per clip; clip 1 keeps its
full frame count, later clips are emitted with `OVERLAP_FRAMES` fewer
frames (default 22). Effective length 22f clips cannot be chained with
the default overlap (22-22=0) — use 39f+ for chained tails.

**OPEN: overlap constant verification.** The 22-frame default comes from
the upstream guide. It has NOT been verified against the 3090's Wan2GP
multishot implementation (no `models/minimax_h3/multishot.py` is
vendored here, and Wan2GP is out of scope to modify). It is
configurable (`overlap_frames=` on `build_chain_plan`) pending a live
chained-render measurement on the 3090.

## API

```python
from services.chain.controller import build_chain_plan, emit_render_manifest

plan = build_chain_plan(
    script_lines=[{"speaker": "Ada", "text": "..."}, ...],
    characters=[{"name": "Ada", "sn_tag": "S1", "description": "..."}],
    durations_s=[2.333, 2.333, 2.333],   # on 17k+5 grid @24fps
    audio_paths=["a0.wav", "a1.wav", "a2.wav"],  # optional
)
manifest = emit_render_manifest(plan)
```

`ChainPlan` (`services/chain/plan.py`) validates:
- SN tags stable across clips (S1 is always the same character; clip
  speaker SNs must exist in the roster)
- audio `start_s` cumulative and aligned to total episode duration;
  `padded_duration_s` equals clip duration (apad)
- frames on-grid (clip 1 full; later clips = grid − overlap)
- chaining refs present for every clip after the first and pointing at
  the previous clip's actual last frame (`{clip_index, frame: 0-based}`)
- resume-safe `status` per clip (pending|in_progress|completed|failed)

Render-order manifest:
- Shot 1: the proven 3-image-ref recipe (two-shot anchor + character
  plates, 20 steps, spectrum cache, 480x832, force_fps 24, audio apad,
  programmatic SN speaker template).
- Shots 2+: first-frame continuation configs — `image_start` = previous
  shot's last frame, `image_refs: null` (plates stand down).

## Honest scope — what is stubbed

- **Seam trim** (dropping the duplicated boundary frame) and **post-chain
  color/texture normalization** are downstream video-processing TODOs;
  the plan only emits the fields a downstream processor needs
  (`previous_clip_end_frame`, overlap metadata).
- Shot-1 recipe config is a minimal inline builder. When
  `renderers/h3_recipe.py` (feat/h3-production-recipe) merges, replace
  it with a reference to that module.
- Overlap constant unverified against the 3090 Wan2GP multishot
  semantics (see above).

## Tests

`tests/test_chain_plan.py`, `tests/test_chain_controller.py`.
