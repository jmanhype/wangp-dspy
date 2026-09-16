# LF002 Archive of Rain — golden reproduction contract

## Status

The two-cut seed-905 native H3 candidate received the operator verdict
**“Perfect”** at `2026-09-16T15:32:19Z`. It is the second golden control after
Devil’s Grandma `v3_pair`.

This document describes artifact preservation and the fresh-clone render
contract. It does not claim that seed 905 is a universal seed for every future
premise.

## Pinned artifacts

Content-addressed copies live in `datasets/runs/provenance/lf002-golden-20260916/`.

| Artifact | SHA-256 |
|---|---|
| `cut1.mp4` | `64916cd42d40e0f81a51dd750d2134d194dd59c8318bf3d6f75fbc8649d97770` |
| `cut2.mp4` | `c3131c041a2b586e15ab19280a0ede64aa294b2e6bdc9f26fde0e353fbc29ceb` |
| `pair.mp4` | `ef4c3944ef728862119b065838ac1ec5f1e1452d1f8b4fdbb0d683f06272a527` |
| `chain_last_frame.png` | `1c1d86b0108c31a8318d428fcf626d3af6ffd0c0ba6269a8a69859eca6fb53de` |

Read-only verification:

```bash
./.venv/bin/python -m predict.lf002_canary \
  --cut1 datasets/runs/provenance/lf002-golden-20260916/cut1.mp4 \
  --cut2 datasets/runs/provenance/lf002-golden-20260916/cut2.mp4 \
  --pair datasets/runs/provenance/lf002-golden-20260916/pair.mp4 \
  --chain datasets/runs/provenance/lf002-golden-20260916/chain_last_frame.png \
  --report datasets/runs/provenance/lf002-golden-20260916/canary.json
```

## Required contract

```text
recipe: golden_v3
seed: 905
cuts: 2
frames: 56 per cut
profile: 2
attention: sdpa
audio carrier: native_h3
post-render audio replacement: forbidden
refs: exactly [seed/start, silent-character face]
chain: cut 1 decoded last frame -> cut 2 image_start
```

The committed fresh-clone bundle is:

```text
assets/lf002-two-cut-20260913/staging-two-cut-seed905-fresh-20260916.json
```

It intentionally has no `completed_prefix`; a release reproduction must render
both cuts and cannot adopt the prior operator-accepted artifact.

## Fresh-clone acceptance

Run from a clean checkout at the recorded merge SHA:

```bash
export WANGP_VISION_BACKEND=local
export WANGP_LOCAL_VISION_ENDPOINT=http://localhost:8000/v1/chat/completions
export WANGP_LOCAL_VISION_MODEL=q
export WANGP_WHISPER_LOCAL_FIRST=1
export WANGP_LF002_FFMPEG=/opt/homebrew/bin/ffmpeg
export WANGP_LF002_FFMPEG_EXPECTED=Lavf62.3.100
export WANGP_ASSET_MAP='assets/lf002-two-cut-20260913=/home/straughter/acceptance/lf002-two-cut-20260913'
export WANGP_SANCTIONED_DIRS='/home/straughter/acceptance/lf002-two-cut-20260913:/home/straughter/Wan2GP'

./.venv/bin/python -u scripts/run_acceptance.py \
  --bundle assets/lf002-two-cut-20260913/staging-two-cut-seed905-fresh-20260916.json \
  --db datasets/lf002-two-cut-seed905-fresh-20260916.jobs.db \
  --ledger datasets/lf002-two-cut-seed905-fresh-20260916.runs.jsonl \
  --output datasets/runs/pull/lf002-two-cut-seed905-fresh-20260916/assembled.mp4
```

The acceptance passes only if:

1. both jobs are freshly rendered through `render_for_job()`;
2. each raw/final artifact is byte-identical and native H3;
3. cut 1, cut 2, chain frame, and assembled pair match the pinned hashes above;
4. pre/post Whisper gates pass without repetition;
5. the vision gate passes;
6. the append-only ledger records a clean tree and full provenance;
7. the operator reviews the final assembled video.

The operator’s earlier “perfect” verdict transfers byte-for-byte only if all
pinned hashes match.

## Fresh-checkout verification — 2026-09-16

The fresh-checkout path reproduced all pinned LF002 hashes at commit
`3faaf9a87ef3c7c87769bb73a5e5579b05b830ef`:

- cut 1: `64916cd42d40e0f81a51dd750d2134d194dd59c8318bf3d6f75fbc8649d97770`
- cut 2: `c3131c041a2b586e15ab19280a0ede64aa294b2e6bdc9f26fde0e353fbc29ceb`
- chain: `1c1d86b0108c31a8318d428fcf626d3af6ffd0c0ba6269a8a69859eca6fb53de`
- pair: `ef4c3944ef728862119b065838ac1ec5f1e1452d1f8b4fdbb0d683f06272a527`

The operator reviewed the linked fresh-checkout assembled video and replied
verbatim: **“Perfect.”**

The first clean-tree attempt exposed Finding #60: a stale remote final artifact
occupied the mapped chain-source path. After hash verification and repair,
the corrected clean-tree retry reproduced the exact cut 2 and assembled pair.
The successful final ledger used `completed_prefix` for the already-verified
fresh cut 1; it was therefore a fresh-checkout reproduction, but not one
uninterrupted no-prefix two-render ledger. That stricter bookkeeping run is
still available if required.

Machine-readable evidence:
`datasets/runs/provenance/lf002-golden-20260916/fresh-clone-verification.json`.
