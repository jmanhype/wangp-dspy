# Content surface and capability report

`wgp content` is the product-facing way to inspect a committed content brief and
plate set. It reuses the existing typed validator and deterministic no-GPU
planner, then reports the content facts without exposing the planner's internal
progress paths:

```bash
uv run --frozen --extra dev wgp content \
  --brief datasets/content_briefs/lf004-operator-dogfood-56f/brief.json \
  --plates datasets/content_briefs/lf004-operator-dogfood/plates \
  --out "${TMPDIR:-/tmp}/wangp-content/plan.json"
```

Add `--json` for the stable `wangp-dspy.content-request/v1` object. The output
names the clip count, unique speaker roster, planned duration, resolved host
requirement, and the governed queue-worker command. Both forms explicitly report
`gpu_work=false` and `queue_submitted=false`.

`--out` is optional. When supplied, it is the canonical
`wangp-dspy.content-plan/v1` path and its sibling `run/` contains the equivalent
script and ledger. When omitted, planning uses temporary storage only.

## Submission boundary

`--submit` first resolves the render host configuration. If any required key is
missing, `wgp content` exits `3` with one typed diagnostic naming the exact
`host.*` keys, their `WANGP_*` variables, and `wgp doctor --capabilities` as
the next command. It writes no plan and submits nothing.

With a complete configuration, `--submit` prints the exact governed
queue-worker command for the generated run directory. It deliberately does not
execute that command or start a render: this product surface has not replaced
the operator-controlled queue worker. The summary therefore remains
`queue_submitted=false`.

## First-run capabilities

```bash
uv run --frozen --extra dev wgp doctor --capabilities
uv run --frozen --extra dev wgp doctor --capabilities --json
```

The report is read-only and local. It records platform, Python, ffmpeg/ffprobe
availability, physical RAM and approximate available RAM, repository-volume
free space, resolved host-key state (without host values or paths), accelerator
visibility, model-manifest status, and per-entry verification state.

Accelerator reporting checks whether `nvidia-smi` is visible on `PATH`; it never
executes it. A machine without that executable is reported as **no local
accelerator**, not as GPU-ready. A manifest entry names its local verification
state and whether operator-supplied bytes are still required. Wangp never
downloads a model.

## Not implemented

The report and content surface never imply support for:

- image generation;
- music generation;
- speech/voice cloning;
- sound effects;
- upscaling;
- face refinement;
- video editing;
- a GUI.

The implemented product surface is no-GPU content planning and host-backed
rendering through the governed queue after explicit operator configuration and
queue execution.
