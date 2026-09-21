# Render recipes

A **render recipe** is a small versioned manifest (`wangp-dspy.render-recipe/v1`)
that pins the logical inputs of one finished run, plus a verifier that reports
where a run has drifted from the recipe that describes it.

## Why

Two questions come up whenever a generated film is shared or revisited:

1. *What produced this artifact?*
2. *Is the artifact in front of me still the one that recipe describes?*

A recipe answers both without re-running anything and without a GPU.

## What a recipe pins

| Field group | Contents |
| --- | --- |
| `repository_version` | The repository `VERSION` at the time the recipe was written. |
| `plan` | The canonical plan hash (the identity the operator approves) and the raw plan file hash. |
| `brief` | The semantic brief hash and the raw brief file hash. |
| `configuration` | The resolved `host.target`, `host.wgp_root`, `host.pull_root`, and `host.wgp_python`, each with the source that supplied it. Values are redacted like every other `wgp` output. |
| `model_and_settings_hashes` | The per-file hashes the run recorded for its model settings. |
| `retry_policy` | The retry ceiling in force (`DEFAULT_MAX_ATTEMPTS`, per-cut attempts). |
| `gate_thresholds` | The declared pass bars and model identity recovered from the run's per-cut evidence (Whisper pre/post, vision, SyncNet confidence/offset, SyncNet model hash). |
| `media` | The assembled film hash and the per-cut video hashes. |
| `queue_database_sha256` | The durable queue database the run used. |

Anything the run did not record cannot be pinned. Where a field is absent
(for example a renderer checkpoint hash the run never wrote down), it appears as
`null` and verification reports it as `missing` rather than inventing a value.

## Write and verify

```bash
uv run --frozen --extra dev wgp recipe write \
  --run datasets/runs/pull/lf004-operator-dogfood-56f-recovery-20260921 \
  --out /tmp/recipe.json

uv run --frozen --extra dev wgp recipe verify \
  --recipe /tmp/recipe.json \
  --run datasets/runs/pull/lf004-operator-dogfood-56f-recovery-20260921
```

`write` prints the recipe path, its sha256, and the number of pinned fields.
`verify` prints one line per drifted field:

```text
drift field=pinned.plan.canonical_sha256 status=changed expected='620f2ba4…' observed='0000…'
drift=1 verified=false
```

Exit codes follow the CLI contract: `0` when nothing drifted, `2` when drift,
a missing recipe, or a malformed/tampered manifest is reported, `4` for an
unexpected internal error.

Both verbs are local and read-only. They make no host call, add no files to the
run bundle, and never mutate a queue.

## What a recipe does not promise

- **Byte-identical pixels.** A generative render is lossy. The same recipe can
  produce different pixels when re-rendered with a different seed, model build,
  or host environment. The recipe pins the *logical* recipe, not the bits.
- **Anything the run did not record.** An unrecorded input is reported as
  missing instead of being silently assumed equal.
- **Operator acceptance.** A recipe records `creative_acceptance` state only as
  far as the run's provenance does; it never asserts a creative verdict.
