---
id: WD-1s5s
title: "Local-only storage remediation packet"
status: closed
priority: 1
type: task
labels: [storage, evidence, operator-decision, accepted]
parent: WD-3nod
created_at: 2026-09-30T17:56:34Z
created_by: speed
updated_at: 2026-09-30T19:53:26Z
content_hash: "sha256:3e474b26985324e4eb7d742ed6bfdf8d6b617702b820001ac99e195c1e2af658"
follows: [WD-he8i, WD-qthq, WD-23rs, WD-p587]
assignee: dev-WD-1s5s
closed_at: 2026-09-30T19:29:46Z
close_reason: "Accepted: independently verified exact PR head and CI, scoped five-file diff, immutable source hashes, deterministic local-only outputs, typed fail-closed negative behavior, focused tests and local gates, protected-file parity, and separate future-authorization boundaries."
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

- WD-bw0h may reuse four exact hash-authorized H3/Qwen assets only. Its authorized no-download manifest total is `53,594,702,510` bytes.
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
- scripts/build_storage_remediation_packet.py -> `build_packet(input_path: Path, output_dir: Path) -> dict`
  spec: validate the typed local input snapshot, fail closed on drift/ambiguity, deterministically emit `local-plan.json`, and return a JSON-serializable packet with recorded facts and projected arithmetic clearly labeled.
- scripts/build_storage_remediation_packet.py -> `write_operator_request(packet: dict, output_path: Path) -> None`
  spec: render `operator-authorization-request.md` from the validated packet, state both distinct future approvals, and include no executable host command.
- datasets/runs/maestro-parity/storage-remediation-prep/inputs.json -> `wangp-dspy.storage-remediation-input/v1`
  schema: embeds source story/head/path/hash, both model manifests, superseded candidate sizes, recorded disk snapshot, offload root, 50-GiB floor, and `snapshot_only=true`.
- datasets/runs/maestro-parity/storage-remediation-prep/local-plan.json -> `wangp-dspy.storage-remediation-plan/v1`
  schema: exact candidate bytes/unknown hashes, projected free-space arithmetic, separate H3 and LTX requirements, no-live-state declaration, and authorization-required boundary.
- datasets/runs/maestro-parity/storage-remediation-prep/operator-authorization-request.md -> human-readable non-executable authorization request

CONSUMES:
- WD-bw0h: datasets/runs/maestro-parity/clean-generated/model-assets.json -> exact four-asset `wangp-dspy.model-assets/v1` manifest
  source: read asset id, destination, `size_bytes`, `sha256`, and license; reject duplicates, zero/negative sizes, malformed hashes, or any total other than `53,594,702,510`.
- WD-bw0h: datasets/runs/maestro-parity/clean-generated/failed-retry/failure.json -> typed `STORAGE_PREPARATION_FAILED` boundary
  source: diagnostic.code == `STORAGE_PREPARATION_FAILED`, diagnostic.detail == `cannot create offload root`, generated_artifact == false, substitution_attempted == false.
- WD-28ac: datasets/runs/maestro-parity/ltx-dependency-terminalization/model-assets.json -> exact five-asset `wangp-dspy.model-assets/v1` manifest
  source: preserve all five asset identities, destinations, sizes, SHA-256 values, and licenses; required total is exactly `23,701,298,279`.
- WD-28ac: datasets/runs/maestro-parity/ltx-dependency-terminalization/preflight-boundary.json -> recorded host-state boundary
  source: `model_download_bytes_actual == 0`, `queue_admission == blocked_before_admission`, destination free bytes `17,865,703,424`, and the explicit not-a-hardware-verdict boundary.
- WD-28ac: datasets/runs/maestro-parity/ltx-dependency-terminalization/host-storage-diagnosis/remote/filesystems.txt -> recorded `df` snapshot
  source: destination and `/mnt/bulk-hdd` free-byte fields; do not treat them as current observations.
- (existing): wangp/doctor.py -> `REMOTE_MINIMUM_FREE_GB: float = 50.0`
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
- scripts/build_storage_remediation_packet.py -> `build_packet(input_path: Path, output_dir: Path) -> dict`
  spec: validate the typed local input snapshot, fail closed on drift/ambiguity, deterministically emit `local-plan.json`, and return a JSON-serializable packet with recorded facts and projected arithmetic clearly labeled.
- scripts/build_storage_remediation_packet.py -> `write_operator_request(packet: dict, output_path: Path) -> None`
  spec: render `operator-authorization-request.md` from the validated packet, state both distinct future approvals, and include no executable host command.
- datasets/runs/maestro-parity/storage-remediation-prep/inputs.json -> `wangp-dspy.storage-remediation-input/v1`
  schema: embeds source story/head/path/hash, both model manifests, superseded candidate sizes, recorded disk snapshot, offload root, 50-GiB floor, and `snapshot_only=true`.
- datasets/runs/maestro-parity/storage-remediation-prep/local-plan.json -> `wangp-dspy.storage-remediation-plan/v1`
  schema: exact candidate bytes/unknown hashes, projected free-space arithmetic, separate H3 and LTX requirements, no-live-state declaration, and authorization-required boundary.
- datasets/runs/maestro-parity/storage-remediation-prep/operator-authorization-request.md -> human-readable non-executable authorization request

CONSUMES:
- WD-bw0h: datasets/runs/maestro-parity/clean-generated/model-assets.json -> exact four-asset `wangp-dspy.model-assets/v1` manifest
  source: read asset id, destination, `size_bytes`, `sha256`, and license; reject duplicates, zero/negative sizes, malformed hashes, or any total other than `53,594,932,510`.
- WD-bw0h: datasets/runs/maestro-parity/clean-generated/failed-retry/failure.json -> typed `STORAGE_PREPARATION_FAILED` boundary
  source: diagnostic.code == `STORAGE_PREPARATION_FAILED`, diagnostic.detail == `cannot create offload root`, generated_artifact == false, substitution_attempted == false.
- WD-28ac: datasets/runs/maestro-parity/ltx-dependency-terminalization/model-assets.json -> exact five-asset `wangp-dspy.model-assets/v1` manifest
  source: preserve all five asset identities, destinations, sizes, SHA-256 values, and licenses; required total is exactly `23,701,298,279`.
- WD-28ac: datasets/runs/maestro-parity/ltx-dependency-terminalization/preflight-boundary.json -> recorded host-state boundary
  source: `model_download_bytes_actual == 0`, `queue_admission == blocked_before_admission`, destination free bytes `17,865,703,424`, and the explicit not-a-hardware-verdict boundary.
- WD-28ac: datasets/runs/maestro-parity/ltx-dependency-terminalization/host-storage-diagnosis/remote/filesystems.txt -> recorded `df` snapshot
  source: destination and `/mnt/bulk-hdd` free-byte fields; do not treat them as current observations.
- (existing): wangp/doctor.py -> `REMOTE_MINIMUM_FREE_GB: float = 50.0`
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
BLOCKED: WD-1s5s acceptance is internally inconsistent. The story-required source blob story/WD-bw0h@2dfe36863e29eef02af0ea330d13d331bafdc00e:datasets/runs/maestro-parity/clean-generated/model-assets.json has verified SHA-256 25078447afda2306e86a424a7c554fba5ae40f3838fcfcdddced6e9391b90fa0 and its four recorded sizes sum to 53594702510 bytes, but AC 1/2 requires that exact source hash and an exact manifest total of 53594932510 bytes (a 230000-byte discrepancy). Preserving the immutable source makes the required total impossible; altering an asset size would falsify the hash-identified snapshot. Sr PM must adjudicate the authoritative total/source before implementation can proceed. DISCOVERED_BUG: title=WD-bw0h manifest sum contradicts WD-1s5s required total; context=Hash-verified four-asset source manifest sums to 53594702510, not 53594932510; affected_files=datasets/runs/maestro-parity/clean-generated/model-assets.json, WD-1s5s story; discovered_during=WD-1s5s.


## nd_contract
status: accepted

### evidence
- PM closeout applied via pvg story accept on 2026-09-30.

### proof
- [x] Story closed after accepted label was applied.


## nd_contract
status: delivered

### evidence
- Commit SHA: 77225696c693dc167915ad52d56ec08a7c29db97
- PR: https://github.com/jmanhike/wangp-dspy/pull/220
- Exact-head CI SUCCESS.
- Focused 16 PASS; full 2162 PASS / 1 boundary-preserving pre-existing 3090 skip; pvg verify, backlog lint, release/no-tag, protected parity, and diff checks PASS.

### proof
- [x] AC 1 through AC 8 verified in the Implementation Evidence blocks above.

## Implementation Evidence
Summary: WD-1s5s local-only storage remediation packet delivered; see the preceding full evidence block for all commands, hashes, gates, AC table, and LEARNINGS.
Commands run: focused pytest 16 PASS; undeselected full pytest 2162 PASS / 1 boundary-preserving pre-existing 3090 skip; pvg verify PASS; pvg lint --backlog PASS; wgp release verify ready=true tag_created=false; protected parity and diff checks PASS; exact-head CI PASS.
### CI/Test Results
- PR: https://github.com/jmanhike/wangp-dspy/pull/220
- CI: https://github.com/jmanhike/wangp-dspy/actions/runs/36762786094/job/110049309036
- Exact-head CI conclusion: SUCCESS
SHA: 77225696c693dc167915ad52d56ec08a7c29db97

## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-30.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## Implementation Evidence (DELIVERED)

Summary: Implemented the local-only WD-1s5s storage-remediation packet using the Sr-PM-corrected, hash-verified WD-bw0h total of 53594702510 bytes; generated deterministic local-plan and operator authorization-request artifacts; preserved stale/snapshot-only labeling, unknown candidate hashes, separate future approvals, and the no-host-action boundary.

Commands run:
- `pvg nd sync` -> up to date at `95287905`; story reread with `pvg issues show WD-1s5s --json`.
- `python -m py_compile scripts/build_storage_remediation_packet.py tests/test_storage_remediation_packet.py` -> PASS.
- `python scripts/build_storage_remediation_packet.py` -> `STORAGE_REMEDIATION_PACKET_READY outputs=2 authorization_required=true commands_emitted=0`.
- `/Users/Shared/HermesWorkspace/wangp-dspy/.venv/bin/pytest tests/test_storage_remediation_packet.py -q` -> 16 passed.
- `/Users/Shared/HermesWorkspace/wangp-dspy/.venv/bin/pytest -q -rs` -> 2162 passed, 1 skipped; collection: 2163 tests. The sole skip is the pre-existing `tests/test_jobs_integration_3090.py:20` gate requiring `WANGP_3090=1`; enabling it would violate this story's LOCAL ONLY/no-host-3090 boundary.
- `/Users/Shared/HermesWorkspace/wangp-dspy/.venv/bin/pytest --collect-only | tail -n 1` -> `2163 tests collected`.
- `pvg verify scripts/build_storage_remediation_packet.py tests/test_storage_remediation_packet.py datasets/runs/maestro-parity/storage-remediation-prep/inputs.json datasets/runs/maestro-parity/storage-remediation-prep/local-plan.json datasets/runs/maestro-parity/storage-remediation-prep/operator-authorization-request.md --format=text` -> `VERIFY: PASSED (2 files scanned, 0 issues)`.
- `pvg lint --backlog` -> scanned 155 issues, 0 errors, 0 review findings.
- `/Users/Shared/HermesWorkspace/wangp-dspy/.venv/bin/wgp release verify --json` -> all 4 checks pass; `ready=true`; `tag=v0.1.0`; `tag_created=false`.
- Protected parity: `git diff --exit-code b5169fec6885660f2c5806864d03d99b8db6fecc..HEAD -- services/jobs/queue.py services/director/renderers/policy.py services/director/wiring.py services/jobs/preflight.py scripts/run_film.py` -> PASS/no diff.
- Whitespace/tree: `git diff --check` and `git diff --check b5169fec6885660f2c5806864d03d99b8db6fecc..HEAD` -> PASS; final tree clean.
- `git commit -m 'feat(WD-1s5s): local storage remediation packet'` -> commit `77225696c693dc167915ad52d56ec08a7c29db97`.
- `git push -u origin story/WD-1s5s` -> pushed exact commit.
- PR: https://github.com/jmanhike/wangp-dspy/pull/220
- Exact-head CI: https://github.com/jmanhike/wangp-dspy/actions/runs/36762786094/job/110049309036 -> `test` conclusion SUCCESS at PR head `77225696c693dc167915ad52d56ec08a7c29db97` after 15m1s.

SHA:
- Branch: `story/WD-1s5s`
- Commit: `77225696c693dc167915ad52d56ec08a7c29db97`
- Base: `b5169fec6885660f2c5806864d03d99b8db6fecc`

### CI/Test Results
- Focused real-process builder/import tests: 16/16 PASS, no skips.
- Full undeselected suite: 2162 PASS, 1 pre-existing host-gated skip, 0 failures.
- Exact-head GitHub CI: PASS.
- All local standing gates: PASS.

### Artifact SHA-256
- `scripts/build_storage_remediation_packet.py`: `cce38a16a2b4238a69ff8a5a92a1004bd48ececa75d88631d04d8e8cd56be4a2`
- `tests/test_storage_remediation_packet.py`: `38c7e9eadb3398c443836d5fbc535d7fdae0c75818c5dbb2af71210df9e25063`
- `datasets/runs/maestro-parity/storage-remediation-prep/inputs.json`: `4f0e7fbd1de0f588a2cf6eefc8ea924b0deee7a2c15afa465af27411a6cf2647`
- `datasets/runs/maestro-parity/storage-remediation-prep/local-plan.json`: `c7744a4a3aa3a01916f465f4a9475c2619304888413226f698b11d636275e7ee`
- `datasets/runs/maestro-parity/storage-remediation-prep/operator-authorization-request.md`: `94b2eabcee423377c3e2ed2d1b12c4e72d33511a58b77ecde83c76363b3a47d2`
- Authored/evidence line count: 536 total (under 550). Packet directory contains exactly `inputs.json`, `local-plan.json`, and `operator-authorization-request.md`; no model/download/queue artifact was created.

### AC Verification
| AC | Requirement | Evidence | Status |
| --- | --- | --- | --- |
| 1 | Committed input embeds all six source identities/hashes, 4 H3 assets, 5 LTX assets, candidates, disk values, offload root, snapshot-only flag | `inputs.json`; focused plan/input assertions | PASS |
| 2 | Typed validation, exact corrected H3 total, LTX total, candidate/projection totals, deterministic stable JSON, no local checkout paths | Builder validation + deterministic focused tests; `local-plan.json` | PASS |
| 3 | Invalid/missing/duplicate/mismatched/zero/negative/ambiguous input fails typed before output mutation | 11 parameterized negative cases + missing-input/render-preservation tests | PASS |
| 4 | Unknown candidate hashes, stale/snapshot-only disk facts/projections, authorization-required, no commands | Plan assertions and command-safety test | PASS |
| 5 | Separate H3-offload/retry versus exact LTX batch approvals; fresh live verification; deletion forbidden | `operator-authorization-request.md` and focused assertions | PASS |
| 6 | No network/process/SSH/host/model/queue/protected/evidence transition side effects | Builder import-surface test; protected parity; artifact inventory; LOCAL ONLY execution | PASS |
| 7 | Real-process clean-directory success/determinism and all AC3/4/5 safety families | 16 focused tests | PASS |
| 8 | Focused/full tests, pvg verify, lint, release verify, protected parity, diff, exact-head CI | Commands and outputs above; PR #220 CI SUCCESS | PASS |

LEARNINGS:
- The original 230000-byte story-total mismatch was a source/story inconsistency, not a builder defect; the Sr PM correction to the hash-verified manifest sum made the packet implementable without changing source identities.
- Release readiness tests require a clean tree, so the story must be committed before the full suite's real-repository checks; the first uncommitted run failed only those clean-tree checks and the post-commit rerun passed.
- The sole full-suite skip is a live 3090 integration gate and must remain disabled under this story's explicit LOCAL ONLY boundary.

## nd_contract
status: delivered

### evidence
- Commit `77225696c693dc167915ad52d56ec08a7c29db97`; PR https://github.com/jmanhike/wangp-dspy/pull/220
- Exact-head CI SUCCESS: https://github.com/jmanhike/wangp-dspy/actions/runs/36762786094/job/110049309036
- Focused 16 PASS; full 2162 PASS/1 boundary-preserving pre-existing skip; pvg verify PASS; backlog lint PASS; release ready/no tag; protected parity and diff checks PASS.

### proof
- [x] AC 1: Complete committed typed input snapshot.
- [x] AC 2: Fail-closed validation, corrected exact totals, deterministic local plan.
- [x] AC 3: Typed invalid-input behavior before output mutation.
- [x] AC 4: Unknown hashes, stale-only labels, authorization boundaries, no commands.
- [x] AC 5: Separate future H3 and LTX authorization request with live verification and no deletion.
- [x] AC 6: Local-only builder/tests and unchanged protected/evidence boundaries.
- [x] AC 7: Real-process focused success, determinism, negative, and safety tests.
- [x] AC 8: Full local gates, exact-head PR CI, and delivery checks.

## History
- 2026-09-30T17:56:46Z dep_added: blocks WD-bw0h
- 2026-09-30T17:56:46Z dep_added: blocks WD-28ac
- 2026-09-30T17:57:13Z dep_added: blocks WD-fay0
- 2026-09-30T17:57:39Z status: open -> in_progress
- 2026-09-30T17:57:39Z auto-follows: linked to predecessor WD-he8i
- 2026-09-30T17:57:39Z claimed by dev-WD-1s5s
- 2026-09-30T18:09:31Z status: in_progress -> blocked
- 2026-09-30T18:10:50Z released by speed
- 2026-09-30T18:10:50Z status: blocked -> in_progress
- 2026-09-30T18:10:50Z auto-follows: linked to predecessor WD-qthq
- 2026-09-30T18:10:50Z claimed by dev-WD-1s5s
- 2026-09-30T19:18:30Z status: in_progress -> in_progress
- 2026-09-30T19:18:30Z auto-follows: linked to predecessor WD-23rs
- 2026-09-30T19:19:11Z status: in_progress -> in_progress
- 2026-09-30T19:19:11Z auto-follows: linked to predecessor WD-p587
- 2026-09-30T19:29:46Z status: in_progress -> closed
- 2026-09-30T19:29:46Z dep_removed: no_longer_blocks WD-bw0h
- 2026-09-30T19:29:46Z dep_removed: no_longer_blocks WD-28ac
- 2026-09-30T19:29:46Z dep_removed: no_longer_blocks WD-fay0

## Links
- Parent: [[WD-3nod]]
- Follows: [[WD-he8i]], [[WD-qthq]], [[WD-23rs]], [[WD-p587]]

## Comments

### 2026-09-30T18:10:49Z speed
SR_PM REPAIR: the hash-verified WD-bw0h manifest is authoritative. Its four recorded sizes sum to 53594702510 bytes, not 53594932510; the story total was corrected by 230000 bytes. No source snapshot or model identity was altered.

### 2026-09-30T19:53:26Z speed
Merged squash-PR closeout: PR 220 merged as main 498a9cb4c994033064161cace2a98165c0a1dbb2. Exact-head PR CI run 36762786094 and main CI run 36766286618 both completed successfully. Merged-head focused tests 16/16, pvg verify, backlog lint, release ready/tag false, protected parity, and diff checks passed. No host action occurred.
