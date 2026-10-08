# WD-bw0h authorized retry stopped at storage preparation

Recorded failure time: `2026-09-29T23:40:31Z`.

The exact operator approval was first corrected and locally verified:
`Authorize` at `2026-09-29T23:17:30Z`, with the governed one-attempt scope at
PR-215 head `6900884acd6baa3d978d30dd4aae92401b8f75e8`. The correction commit
and clean disposable clone resolved to `44c8d82dbfd4bebd7b337d9b60446b2357030613`
with an empty repository status.

Local preflight passed before the sole host attempt: required tools were present,
the four-asset manifest was semantically identical to the accepted manifest, the
workspace was absent, installer dry-run matched the isolated clone/sync/proof
path, 12 focused/generated tests passed, and `pvg verify` passed with 0 issues.

The single authorized command then reached host `3090` and completed an SSH disk
probe, but stopped with exit `4`, `STORAGE_PREPARATION_FAILED`, detail
`cannot create offload root`, while preparing
`/mnt/bulk-hdd/straughter/model-offload/wangp-3090`. No relocation script ran,
so no superseded checkpoint was copied, moved, unlinked, or deleted. The failure
occurred before model identity preflight, queue admission, offline wrapper setup,
rendering, retrieval, media gates, and the canonical checker.

Boundary result:

- Generated artifact: **false**
- Existing-artifact substitution: **false**
- Retry or second generation: **none**
- Model bytes downloaded/read/rendered: `0`
- Queue jobs admitted: `0`
- Provider spend/training: `false`
- Superseded model relocations/deletions: `0`
- Protected engine/threshold changes: `0`

The recorder does not retain the remote `mkdir -p` return code or stderr for this
first failed host action. Re-contacting the host to recover those values would
violate the one-attempt boundary, so the typed diagnostic and absent downstream
evidence are the authoritative stop record.
