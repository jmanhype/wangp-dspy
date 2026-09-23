# First-run platform readiness

`wgp first-run` is a local, typed front door. It profiles the machine, reports
what a full run would need, checks LLM runtime configuration, reads recorded
OOM evidence, and renders a host-access preview. It does not download a model,
contact a provider, execute `nvidia-smi`, mutate a gate, or contact SSH.

## Hardware and advisory profile

Run `wgp first-run profile` for the local snapshot or pass
`--inventory <inventory.json>` to evaluate an operator-recorded inventory.
The inventory schema is `wangp-dspy.platform-inventory/v1` and records the
platform, CPU core counts, RAM, disk capacity/free space, and zero or more
accelerators. A `null` field is reported as unknown rather than inferred.

The recommendation is advisory and never generation evidence:

- `planning-only-external-render`: no accelerator is reported, or no reported
  accelerator has at least 24 GiB VRAM.
- `local-candidate-24gb`: an accelerator reports at least 24 GiB VRAM and the
  recorded volume has at least 100 GiB free. The status remains
  `advisory-unverified`.

Local collection checks only whether `nvidia-smi` is present on `PATH`; it
never executes it. The standard library does not expose a portable CPU model,
live memory availability, or accelerator VRAM, so those fields remain explicit
unknowns unless supplied in a recorded inventory. Add `--json` for the machine
shape; every response carries `verified_generation=false`.

## Download status and explicit resume

`wgp first-run download --manifest <manifest> --state <state>` reads a typed
manifest with each asset's source URL, SHA-256, exact size, licence, and
absolute destination. It reports `absent`, `partial`, `checksum_mismatch`,
`unreadable`, `paused`, or `complete` from the real local bytes and durable
state file. Opening this command starts no transfer.

`--pause <id>` records one durable pause. `--resume <id>` records the explicit
resume request, then exits `2` with `DOWNLOAD_REQUIRES_OPERATOR` and the exact
`curl --fail --location --continue-at - --output <destination> <source-url>`
command to review. Wangp never executes that command. The operator must verify
the recorded SHA-256 and licence before the asset can be considered complete.

## Bundled-local or external LLM runtime

`wgp first-run runtime --config <config>` resolves configuration only. The
`local-then-external` strategy selects a bundled-local model only when its
recorded bytes exist and hash-match. Otherwise it selects the recorded external
provider only when its named API-key environment variable is nonempty. Missing
credentials fail closed with `LLM_CREDENTIAL_MISSING`; the credential value is
never copied into output. Both runtimes report `provider_contact=false`.

## Recorded OOM recovery

`wgp first-run recovery --record <record>` accepts a
`wangp-dspy.oom-recovery/v1` record containing the actual stderr marker, run
and evidence IDs, the original model/style/render settings, current bounded
calibration, and original command. It detects OOM evidence and returns the next
bounded calibration step (`512p`, then minimum frames), or fails closed with
`OOM_NOT_DETECTED` for unrelated failures.

The result is guidance only. It preserves model and style, changes no gate,
and makes no automatic render change. The original command is shown for
separate operator authorization.

## Remote host preview

`wgp first-run remote` resolves only the existing explicit `[host]`
configuration or host environment variables. It prints
`ssh -o BatchMode=yes <target> true`, reports whether every required value is
present, and exits `3` before constructing SSH when configuration is
incomplete. A complete preview also reports `host_contact=false`; probing or
rendering requires a separately authorized command.

## Exit contract

- `0`: local typed preflight completed.
- `2`: malformed input, invalid provenance, missing credential, non-OOM record,
  or an explicit download action that requires the operator.
- `3`: render-host configuration is incomplete.

No command in this surface is a verified generation claim. A generation claim
requires a separately authorized run bundle with command, repository commit,
asset provenance, queue record, exit status, output hashes, and gate evidence.
