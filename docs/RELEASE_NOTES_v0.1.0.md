# Wangp 0.1.0

Wangp is a governed short-film generation engine. It validates typed content briefs, cast plates, and turn audio; creates deterministic no-GPU render plans; submits production cuts to a durable queue; renders only through an authorized host; applies transcript, identity-vision, mouth-box, and SyncNet gates; assembles accepted cuts; and preserves hashes and provenance for review.

The complete v0.1.0 surface starts with one-command installation from Git source (`sh install.sh`). `wgp content` turns a brief plus plates into a reviewed no-GPU plan; when an explicitly configured host is available, its truthful submission path queues the planned cuts without executing a render. `wgp doctor --capabilities` reports local tools, resources, model-manifest status, and the generation capabilities that are not implemented yet. Rendering remains host-authorized, and recipes retain their logical—not byte-identical—identity contract.

## No-GPU guarantee

The local lane supports `wgp doctor`, typed brief validation, and deterministic planning without model inference, SSH, queue submission, GPU work, or an API key. The committed LF004 quickstart plans four cuts in `9.332` seconds with `gpu_work=false` and `queue_submitted=false`.

## Install and limits

Version 0.1.0 installs from source with [`docs/install.md`](install.md). Actual rendering still requires a configured, authorized render host with the Wan2GP environment and required models; installation does not provision one. The tool install also does not carry Git metadata or repository evidence: recipe and release operations need a clean checkout. Wangp does not publish or administer third-party model licences.

A versioned recipe is a logical identity check, not a promise of byte-identical pixels. It pins run, repository, brief, plan, gate, model/settings, retry, and media hashes and re-hashes the artifacts being verified. Generative rendering remains lossy, so equality means the pinned evidence and artifacts are unchanged—not that a new render would reproduce every byte.

## Verify a recipe

From a clean checkout, pin and verify the governed LF004 run:

```bash
uv run --frozen --extra dev wgp recipe write --run datasets/runs/pull/lf004-operator-dogfood-56f-recovery-20260921 --out /tmp/recipe.json
uv run --frozen --extra dev wgp recipe verify --recipe /tmp/recipe.json --run datasets/runs/pull/lf004-operator-dogfood-56f-recovery-20260921
```

`recipe verify` exits 0 when every pinned field matches and 2 when it reports `changed`, `missing`, or `added` drift.
