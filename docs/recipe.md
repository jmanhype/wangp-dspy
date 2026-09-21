# Render recipes

A **render recipe** is a small versioned manifest (`wangp-dspy.render-recipe/v2`)
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
| `run_id` | The run identity. A different run cannot verify against this recipe. |
| `repository_version` | The repository `VERSION` at the time the recipe was written. |
| `plan` | The canonical plan hash (the identity the operator approves) and the raw plan hash, read from `inputs.plan_sha256` or from the path-keyed form older runs used. |
| `brief` | The semantic brief hash and the raw brief file hash. |
| `assembled_media` | The hash the run recorded **and** the hash of the file present in this bundle, recomputed at verify time. |
| `cuts` | Per-cut recorded video hash plus the hash of the cut file present in this bundle, recomputed at verify time. |
| `cut_gate_thresholds` | The pass bars **per cut** (Whisper pre/post, vision, SyncNet confidence/offset and model hash), so a change confined to a later cut is still visible. |
| `recorded_settings_hashes` | The per-file hashes the run recorded for its model settings. |
| `retry_policy` | The retry ceiling in force (`DEFAULT_MAX_ATTEMPTS`, per-cut attempts). |
| `queue_database` | The queue database digest the run recorded, plus the hash of the file present now. |

`context.configuration` (the host configuration resolved on **this** machine,
with the source of each value) is recorded for information only and is never
compared — it is not evidence the run produced, so it can never manufacture
drift.

Anything the run did not record cannot be pinned. Where a field is absent
(for example a renderer checkpoint hash the run never wrote down or a media hash
the run omitted), it appears as `null` and verification reports it as `missing`
rather than treating absence as agreement.

Verification **re-reads the world**: referenced artifacts are re-hashed from
their current bytes rather than compared against a copy of the hash already
stored in the manifest. Appending a byte to `assembled.mp4`, editing a recorded
input, or swapping in a different run all change the observed values and are
reported as drift. When provenance records an absolute path from the worktree
that produced it, the file of the same name inside the bundle under review is
the artifact that gets hashed.

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
- **The verifying machine.** Host configuration is context, not evidence; it is
  recorded and never compared.
- **Operator acceptance.** A recipe records `creative_acceptance` state only as
  far as the run's provenance does; it never asserts a creative verdict.
