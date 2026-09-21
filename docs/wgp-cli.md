# `wgp` command reference

`wgp` is the stable operator surface over the existing planning, queue, preflight,
and provenance seams. It adds no renderer, QC, retry, or queue-transition behavior.

## Stable verbs

```bash
uv run wgp --help
uv run wgp doctor
uv run wgp brief validate datasets/content_briefs/lf004-operator-dogfood-56f/brief.json
uv run wgp plan --brief datasets/content_briefs/lf004-operator-dogfood-56f/brief.json --plates datasets/content_briefs/lf004-operator-dogfood/plates --out "${TMPDIR:-/tmp}/wangp-cli/plan.json"
uv run wgp status --db datasets/lf004-operator-dogfood-56f-recovery-20260921.jobs.db
uv run wgp review datasets/runs/pull/lf004-operator-dogfood-56f-recovery-20260921
```

These are reference examples, not the README's tested quickstart block. Planning
writes its run ledger beside `plan.json` under `run/`. It performs no SSH, queue
submission, model inference, or GPU work.

## Doctor safety

By default, `doctor` checks Python, `uv`, required imports, `ffprobe`, `ffmpeg`,
SQLite, the optional supplied model manifest, host configuration, and local disk.
It reports a missing host configuration as **skipped**, not failed: no-GPU planning
remains ready. The `host_configuration` detail names each resolved key and its provenance
(`environment`, `user_config`, `repository_config`, or `detection`); missing values are reported as
`unconfigured`. See [configuration.md](configuration.md) for precedence, safe local detection, and
copy-pasteable configuration examples.

`--models` accepts either a JSON list or `{"models":[...]}`. Local and remote files are
declared explicitly: `local_path` is verified in the workstation namespace and
`remote_path` is verified in the Wan2GP host namespace. Both require a 64-character
hexadecimal `sha256`. Relative `remote_path` values are resolved beneath the configured
Wan2GP root; absolute remote paths are passed unchanged. The legacy `path` field is
accepted as `local_path`. A failed local check names every missing, unreadable, or
digest-mismatched path.
`--db` performs a read-only SQLite reachability check.

`doctor --probe-host --models MANIFEST` is the only mode that contacts a configured
host. The manifest must contain at least one `remote_path`; otherwise doctor fails
without contacting the host. It calls the existing preflight seam and reports exactly
these check kinds:
`ssh_reachable`, `model_files`, `disk_headroom`, `gpu_state`, and `qc_available`.
Remote model hashes are checked at their Wan2GP-relative or absolute remote paths, and
the render volume must retain at least **50 GB** free.
The host is complete only when `host.target`, `host.wgp_root`, and `host.pull_root` all resolve;
`WANGP_SSH_TARGET`, `WANGP_WGP_ROOT`, `WANGP_PULL_ROOT`, and `WANGP_WGP_PYTHON` override their
file values. Without `--probe-host`, doctor makes no SSH or hosted-service call. Every failed or
skipped check has one concrete remediation line.
Failed model, SSH, and disk checks also carry a structured diagnostic with a
stable code, observed measurement, cause, safe command, and evidence reference.
Human output prints the diagnostic block; JSON places serialized diagnostics in
the top-level `diagnostics` array.

## Status and review

`status --db DB` (or `status --run RUN_DIR`) uses the existing `JobQueue` read APIs
and never advances state or retry eligibility. It reports state counts, selected
jobs, attempts, failure classes, and details.
Failed and dead-letter jobs receive a read-only diagnostic that preserves the
queue/attempt values, distinguishes gate and retry outcomes, and names the exact
review/reopen or eligible-retry command.

`review --db DB [--job ID]` reports durable clips, failure summaries, immutable
attempt history, and referenced evidence paths. `review RUN` points at
`assembled.mp4`, `probe.json`, `review/*.contact_sheet.jpg`, and
`final-provenance.json`; it verifies every recorded path-plus-SHA-256 pair using
content-derived fields only. A hash mismatch is an input/integrity failure.
Gate and provenance failures use this same diagnostic vocabulary and JSON shape;
review exits `2` after printing or serializing them.

## JSON and exit codes

`doctor`, `brief validate`, `plan`, `status`, and `review` support `--json`. JSON is
canonical (sorted keys and compact separators), contains no timestamps or process
IDs, and never dumps the environment.

| Code | Meaning |
| --- | --- |
| `0` | success |
| `2` | usage, input, configuration, or evidence-integrity error |
| `3` | one or more doctor checks failed |
| `4` | unexpected internal error |

Usage errors from argparse also use the conventional code `2`. Human failures print
one actionable line rather than a Python traceback.
