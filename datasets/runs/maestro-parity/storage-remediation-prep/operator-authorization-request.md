# Operator authorization request: local storage remediation packet

This WD-1s5s packet is preparation only. It records stale snapshots, performs no host contact, and grants no authority. Two future actions require separate, explicit operator approvals.

## Decision A: reversible H3 offload, then a possible WD-bw0h retry

- Reversibly offload exactly the two superseded H3 checkpoints listed below; no other model asset is in this scope.
- Candidate SHA-256 values are unknown. Measure and record each identity and size before any relocation, then preserve a reversible recovery path.
- Fresh live verification must confirm candidate identity, size, destination free space, and bulk-HDD free space. Deletion is forbidden.
- A possible WD-bw0h retry requires its own approval after the storage precondition is verified; this section does not authorize that retry.

| Candidate | Recorded bytes | SHA-256 |
| --- | ---: | --- |
| superseded-h3-checkpoint-1 | 22144108396 | unknown; live verification required |
| superseded-h3-checkpoint-2 | 22144108397 | unknown; live verification required |

## Decision B: exact WD-28ac LTX batch

- Approve or reject the separate batch of exactly five LTX assets totaling 23701298279 bytes.
- Before any transfer, verify every asset identity and hash, every destination, and current destination disk headroom. Substitution is forbidden.

## Recorded arithmetic, not live state

The stale destination snapshot records 17865703424 bytes free. Reversible offload of both candidates would recover 44288216793 bytes and project 62153920217 bytes free only if that snapshot still matches. That number is above the 53687091200-byte doctor floor and above the exact LTX manifest, but it is not a live observation or outcome prediction.

No host command is included. This request authorizes neither action and forbids deletion, model substitution, queue admission, and any unapproved host contact.
