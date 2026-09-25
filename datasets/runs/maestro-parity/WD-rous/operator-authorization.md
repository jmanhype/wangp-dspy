# WD-rous operator authorization

## Verbatim authorization

1. `I agree`
   - Original scope: host batch 1; report the download-plan byte total and stop above a 20 GB download ceiling.
2. `you need to kill whatever that is that was holding up the GPU and get back to work so that we can finish and complete this`
3. `Unblock and cont`

The dispatcher scoped those approvals to this WD-rous music batch: download only the minimum Stable Audio Small Music / SAME-S / T5Gemma set, then run the real ACE-Step generate and style-adaptation operations and Stable Audio generate operation for operator research/evaluation. The operator-imposed download ceiling remains 20 GB. This lane's exact pending set is 2,356,908,559 bytes, below that ceiling. Actual bytes pulled will be recorded in `selected-download.log` and `evidence.json`.

Authorization recorded at 2026-09-25T03:42:53Z by the operator through the `/root` parent authorization. No training, GUI, registry publication, model-weight commit, or threshold overrun is authorized.

## Derived disk floor

- Host volume: `/dev/nvme0n1p4`, measured available bytes before download: 13,518,491,648 (13.52 decimal GB / 12.59 GiB).
- Authorized download set: 2,356,908,559 bytes (2.36 decimal GB).
- Render/output working-set allowance: 1.14 decimal GB (3 ten-second 48 kHz stereo WAV candidates plus temporary model state and logs).
- Post-download operator safety floor: 8.00 decimal GB.
- Pre-download admission `min_free_gb`: 8.00 + 2.36 + 1.14 = **11.50 GB**. Before the pull, 13.49 decimal GB was available, so the authorized download could finish above the 8.00 GB final safety floor. The attempt to apply this already-consumed download component again after the pull correctly failed at 11.12 decimal GB and is retained in `selected-doctor-preflight-pre-download-floor-11.5-failed.json`.
- Post-download render `min_free_gb`: 8.00 final safety + 1.14 render/output margin = **9.14 GB**. This is a separately derived remaining-requirement gate, not a silent reduction of the pre-download admission gate. Actual post-download availability is 11.12 decimal GB, and the lane would stop rather than render if it were below either 9.14 GB or the operator's 8 GB final safety floor.
