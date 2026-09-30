---
id: WD-1s5s
title: "Local-only storage remediation packet"
status: open
priority: 1
type: task
labels: [storage, evidence, operator-decision]
parent: WD-3nod
created_at: 2026-09-30T17:56:34Z
created_by: speed
updated_at: 2026-09-30T17:56:34Z
content_hash: "sha256:09866b33e53f15f1690534e649abeadad762c083078c3dc450071dad235a90f1"
---

## Description
## Context (Embedded)

This story is authorized only to create a local, repository-backed preparation packet. It must not resume the deferred WD-bw0h or WD-28ac host operations and must not consume their future operator authorization.

Operator input at `2026-09-30T17:55:42Z`: `Authorize`. It is interpreted against the immediately prior proposed next step: create a local-only Paivot storage-remediation preparation story and artifacts, without SSH, host mutation, model-byte movement, download, queue admission, or protected-engine changes. A separate, explicit approval remains required before either host batch resumes.

Authoritative repository at creation time is `main@b5169fec6885660f2c5806864d03d99b8db6fecc`. Paivot is in sync and current exact live tracker state is:

- WD-bw0h: deferred, no assignee; one prior retry stopped at `STORAGE_PREPARATION_FAILED` / `cannot create offload root`.
- WD-28ac: deferred, no assignee; a prior preflight recorded insufficient room for exactly `23,701,298,279` bytes of missing LTX assets.
- WD-qthq and WD-he8i: accepted/closed. The 208-row current parity index passes and reports zero `planned` cells; it does not claim that either deferred host lane is complete.

Immutable evidence inputs to embed (these are snapshots, not proof that host state is currently unchanged):

| Story | Branch/head | Path | SHA-256 |
| --- | --- | --- | --- |
| WD-bw0h | `story/WD-bw0h@2dfe36863e29eef02af0ea330d13d331bafdc00e` | `datasets/runs/maestro-parity/clean-generated/model-assets.json` | `25078447afda2306e86a424a7c554fba5ae40f3838fcfcdddced6e9391b90fa0` |
| WD-bw0h | same head | `datasets/runs/maestro-parity/clean-generated/failed-retry/failure.json` | `7d8320174c0d621cd32b4013acaddb81e92fc72a9d2af3eeabed76f5d987a6d5` |
| WD-bw0h | same head | `datasets/runs/maestro-parity/clean-generated/failed-retry/boundary.md` | `b78f5936a227782e4c3b7866e041cd9bbcc3d60d7ed4b9ebe5418e14e3d78d5f` |
| WD-28ac | `story/WD-28ac@fced67e1293dc2dbbdf3f29c8b615f6357012ab6` | `datasets/runs/maestro-parity/ltx-dependency-terminalization/model-assets.json` | `89f3b52bab6ff7f0ac028d5225798dd612ecdcdd10a1087f6e299474fb1b34a4` |
| WD-28ac | same head | `datasets/runs/maestro-parity/ltx-dependency-terminalization/preflight-boundary.json` | `6c881c9df3cd2a5d4ce85ee8fe5327e6631ac77cf2a2ca88c3b4579be4f05d53` |
| WD-28ac | same head | `datasets/runs/maestro-parity/ltx-dependency-terminalization/host-storage-diagnosis/remote/filesystems.txt` | `fe48f4f09634a511ae43a20211ca78bef83d415b38817303926aeac623817e9e` |

Required packet facts:

- WD-bw0h may reuse four exact hash-authorized H3/Qwen assets only. Its authorized no-download manifest total is `53,594,932,510` bytes.
- Two superseded H3 checkpoints are recorded candidates for future reversible offload only. Their recorded sizes are `22,144,108,396` and `22,144,108,397` bytes, total `44,288,216,793` bytes. No SHA-256 is known from the accepted snapshots, so this packet must not invent one; future work must measure and verify before any move.
- Recorded destination-filesystem free space at the WD-28ac snapshot was `17,865,703,424` bytes. Recorded `/mnt/bulk-hdd` free space was `317,216,575,488` bytes.
- The proposed offload root is `/mnt/bulk-hdd/straughter/model-offload/wangp-3090/`. Recorded arithmetic, not a live prediction, says moving both superseded candidates would recover `44,288,216,793` bytes and project `62,153,920,217` bytes free if and only if the snapshot still matches. That is above the conservative 50-GiB doctor floor (`53,687,091,200` bytes) and above the exact `23,701,298,279`-byte LTX manifest, but no result may be represented as live host state.
- The missing LTX set is exactly five assets totaling `23,701,298,279` bytes; all five SHA-256 values are embedded in the WD-28ac manifest snapshot.

## USER INTENT

Before granting another expensive or irreversible-looking host action, the operator needs one auditable packet that separates recorded facts from stale snapshots, identifies only the two superseded H3 candidates, computes whether their reversible offload could plausibly restore the 50-GiB preflight floor and fit the exact LTX manifest, and emits an explicit future authorization request. The packet is preparation only.

## OUT OF SCOPE

- SSH or any contact with host `3090`: this story has no way to validate current filesystem state; it records that limitation.
- Creating, repairing, moving, linking, copying, or deleting any host file or model byte.
- Model download, HEAD request, provider spend, training, rendering, queue admission, or generated evidence.
- Changing protected engine files: `services/jobs/queue.py`, `services/director/renderers/policy.py`, `services/director/wiring.py`, `services/jobs/preflight.py`, and `scripts/run_film.py`.
- Editing WD-bw0h or WD-28ac evidence, changing their deferred status, or treating this packet as a new host authorization.
- A generic storage-manager product surface. This is one fail-closed evidence packet for the two named deferred stories.

## DIFF BUDGET

- About 5-7 files and under 550 authored/evidence LOC. Expected outputs are one input snapshot, one local builder, focused tests, one generated JSON packet, and one generated operator request.

## Boundary Map

PRODUCES:
- `scripts/build_storage_remediation_packet.py` -> `build_packet(input_path: Path, output_dir: Path) -> dict`
  spec: validate the typed local input snapshot, fail closed on drift/ambiguity, deterministically emit `local-plan.json`, and return a JSON-serializable packet with recorded facts and projected arithmetic clearly labeled.
- `scripts/build_storage_remediation_packet.py` -> `write_operator_request(packet: dict, output_path: Path) -> None`
  spec: render `operator-authorization-request.md` from the validated packet, state both distinct future approvals, and include no executable host command.
- `datasets/runs/maestro-parity/storage-remediation-prep/inputs.json` -> `wangp-dspy.storage-remediation-input/v1`
  schema: embeds source story/head/path/hash, both model manifests, superseded candidate sizes, recorded disk snapshot, offload root, 50-GiB floor, and `snapshot_only=true`.
- `datasets/runs/maestro-parity/storage-remediation-prep/local-plan.json` -> `wangp-dspy.storage-remediation-plan/v1`
  schema: exact candidate bytes/unknown hashes, projected free-space arithmetic, separate H3 and LTX requirements, no-live-state declaration, and authorization-required boundary.
- `datasets/runs/maestro-parity/storage-remediation-prep/operator-authorization-request.md` -> human-readable non-executable authorization request

CONSUMES:
- WD-bw0h: `datasets/runs/maestro-parity/clean-generated/model-assets.json` -> exact four-asset `wangp-dspy.model-assets/v1` manifest
  source: read asset id, destination, `size_bytes`, `sha256`, and license; reject duplicates, zero/negative sizes, malformed hashes, or any total other than `53,594,932,510`.
- WD-bw0h: `datasets/runs/maestro-parity/clean-generated/failed-retry/failure.json` -> typed `STORAGE_PREPARATION_FAILED` boundary
  source: diagnostic.code == `STORAGE_PREPARATION_FAILED`, diagnostic.detail == `cannot create offload root`, generated_artifact == false, substitution_attempted == false.
- WD-28ac: `datasets/runs/maestro-parity/ltx-dependency-terminalization/model-assets.json` -> exact five-asset `wangp-dspy.model-assets/v1` manifest
  source: preserve all five asset identities, destinations, sizes, SHA-256 values, and licenses; required total is exactly `23,701,298,279`.
- WD-28ac: `datasets/runs/maestro-parity/ltx-dependency-terminalization/preflight-boundary.json` -> recorded host-state boundary
  source: `model_download_bytes_actual == 0`, `queue_admission == blocked_before_admission`, destination free bytes `17,865,703,424`, and the explicit not-a-hardware-verdict boundary.
- WD-28ac: `datasets/runs/maestro-parity/ltx-dependency-terminalization/host-storage-diagnosis/remote/filesystems.txt` -> recorded `df` snapshot
  source: destination and `/mnt/bulk-hdd` free-byte fields; do not treat them as current observations.
- (existing): `wangp/doctor.py` -> `REMOTE_MINIMUM_FREE_GB: float = 50.0`
  source: use the conservative 50-GiB byte floor (`53,687,091,200`) for projected readiness, while preserving the source constant in the input snapshot.

## Story Acceptance Criteria

1. [State] The committed input snapshot embeds every source story/head/path/hash above, exactly four WD-bw0h assets, exactly five WD-28ac assets, the two superseded candidate sizes, both recorded disk free-space values, the named offload root, and `snapshot_only=true`.
2. [State] `build_packet` validates schema, required fields, source hashes, unique asset IDs/destinations, 64-character lowercase hexadecimal model hashes, exact manifest totals, exact candidate total `44,288,216,793`, and exact projected free space `62,153,920,217`; it writes deterministic JSON with stable key order and no absolute local checkout paths.
3. [Unwanted] Invalid, missing, duplicated, mismatched, zero-byte, negative-size, or ambiguous input exits nonzero with a typed `STORAGE_REMEDIATION_INPUT_INVALID` diagnostic before any output file is created or replaced.
4. [State] The generated plan marks superseded candidate SHA-256 values as unknown/requires-live-verification, marks all disk facts and projections stale/snapshot-only, marks both future actions authorization-required, and never emits a shell/SSH/download/move command.
5. [State] The operator request separates (a) reversible offload of exactly the two superseded H3 checkpoints and then a possible WD-bw0h retry from (b) the separate exact five-asset/23,701,298,279-byte WD-28ac download batch; it explicitly requires fresh live size/hash/disk verification and forbids deletion.
6. [Unwanted] The builder and tests perform no network, subprocess, SSH, socket, host mutation, model-byte access, queue admission, protected-engine edit, WD-bw0h/WD-28ac evidence edit, or story status transition.
7. [State] Real-process focused tests run the builder from a clean temporary output directory, verify success output and deterministic rerun, and cover each typed failure family from AC 3 plus the AC 4/5 safety invariants.
8. [State] Focused tests, the undeselected full suite, `pvg verify` on the builder/tests/input/output, `pvg lint --backlog`, `wgp release verify` with `release=ready` and `tag_created=false`, protected-file parity, `git diff --check`, and exact-head CI pass.

## Testing Requirements

- Unit: typed validation, exact totals, source-hash references, deterministic serialization, stale/projection labeling, and output safety invariants.
- Integration: MANDATORY, no mocks. Invoke the real builder as a subprocess or import its real entry point against real temporary files, then read the generated bytes; do not fake filesystem failures or patch network/subprocess calls.
- Negative paths: missing input/schema field, wrong WD-bw0h total, wrong WD-28ac total, duplicate destination, malformed model hash, negative size, candidate-size drift, and existing output that must remain untouched after validation failure.
- Commands: include focused pytest, undeselected full pytest, `pvg verify`, backlog lint, release verify, protected parity, diff check, and exact-head CI.
- No test may skip when a required local fixture is absent; absence is an expected typed failure.

## MANDATORY SKILLS

- pvg
- tool-systematic-debugging

## Delivery Requirements

- Include `## Implementation Evidence`, `Summary:`, `Commands run:`, `SHA:`, `### CI/Test Results`, `### AC Verification`, and `LEARNINGS:`.
- Record generated-file SHA-256 values and prove the builder created no local model/download/queue artifact.
- Deliver through `pvg story deliver`; do not self-accept.

## nd_contract
status: new

### evidence
- Created from operator local-only authorization at `2026-09-30T17:55:42Z`, merged main `b5169fec6885660f2c5806864d03d99b8db6fecc`, and the six hash-identified WD-bw0h/WD-28ac snapshots above.

### proof
- [ ] Pending local packet implementation, typed negative-path tests, standing gates, and exact-head CI.

## Acceptance Criteria


## Design


## Notes


## History


## Links
- Parent: [[WD-3nod]]

## Comments
