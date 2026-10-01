---
id: WD-cuzw
title: "Authorized reversible H3 checkpoint offload"
status: in_progress
priority: 1
type: task
labels: [storage, evidence, external-integration, operator-decision]
parent: WD-3nod
created_at: 2026-09-30T19:59:48Z
created_by: speed
updated_at: 2026-10-01T19:01:02Z
content_hash: "sha256:9dbe903cd565fef8acbdc1688f308f9cb69bc829eceb85dd547de6e901aa9159"
blocks: [WD-fay0, WD-bw0h, WD-28ac]
follows: [WD-1s5s, WD-he8i, WD-qthq, WD-23rs, WD-p587]
assignee: dev-WD-cuzw
---

## Description
## Context (Embedded)

Operator authorization is now explicit for one narrowly bounded storage action. Verbatim input at `2026-09-30T19:57:10Z`:

> Approved authorized

This is the approval for the immediately preceding question: **reversible offload of exactly the two superseded H3 checkpoints on host `3090`, with live size/SHA verification, a reversible recovery path, and no deletion.** It does **not** authorize a new WD-bw0h H3 generation retry, WD-28ac LTX download, model access for inference, provider spend, or queue admission.

Current authoritative base is `main@498a9cb4c994033064161cace2a98165c0a1dbb2`. `WD-1s5s` is accepted/merged and supplies the local-only packet; its stale disk numbers must not be reused as live facts.

Exact authorized candidates:

| ID | Source | Recorded bytes | Destination |
| --- | --- | ---: | --- |
| superseded-h3-checkpoint-1 | `/home/straughter/Wan2GP/ckpts/MiniMax-H3-FL2VA-pruned_int8_convrot.safetensors` | 22,144,108,396 | `/mnt/bulk-hdd/straughter/model-offload/wangp-3090/MiniMax-H3-FL2VA-pruned_int8_convrot.safetensors` |
| superseded-h3-checkpoint-2 | `/home/straughter/Wan2GP/ckpts/MiniMax-H3-Ref2VA-pruned_int8_convrot.safetensors` | 22,144,108,397 | `/mnt/bulk-hdd/straughter/model-offload/wangp-3090/MiniMax-H3-Ref2VA-pruned_int8_convrot.safetensors` |

Exact combined recovery: `44,288,216,793` bytes. Their SHA-256 values are intentionally unknown in the accepted packet; this story must measure them live and prove before/after identity without inventing a prior value.

The offload root is exactly `/mnt/bulk-hdd/straughter/model-offload/wangp-3090/`. It may be created or verified with ordinary user permissions only. Do not use `sudo`, an alternate root, or a broader cleanup. If ordinary creation/verification fails, stop with a typed boundary.

The previous WD-bw0h attempt stopped at `STORAGE_PREPARATION_FAILED` / `cannot create offload root`; preserve that history and do not overwrite WD-bw0h evidence.

### Preflight-retry adjudication

Read-only host validation does not consume the one mutation attempt. The recorded `2026-09-30T21:08:21Z` boundary `H3_ROOT_CONTAINMENT_INVALID` proved that staging, `push_file`, `run_argv`, root creation, and both moves were not reached. Preserve those three files immutably under a dated `boundary-attempts/` directory, repair the local mount-probe and repository-branch evidence defects, then one fresh read-only preflight is allowed under the same operator approval. The mutation budget remains exactly one and begins only after a complete passing preflight. A second preflight boundary after this adjudication requires a fresh dispatcher/operator decision.

### Final mount-namespace adjudication

The second zero-mutation boundary recorded the exact expected host namespace: `/mnt/bulk-hdd` appears once as `systemd-1`/`autofs` and once as `/dev/sda4`/`ext4`. For exactly this shape, preflight must retain both rows as evidence, select the unique non-autofs `ext4` block mount, and continue only when the resolved offload root remains contained beneath `/mnt/bulk-hdd`. Any other duplicated/ambiguous mount shape still fails closed. This permits one final read-only preflight retry; the mutation budget remains exactly one and a third preflight failure stops for operator review.

## USER INTENT

The completed command returns a typed PASS result only after it stores immutable before/after evidence and emits a reversible two-file restoration mapping; otherwise it returns a typed failure boundary.

Free enough space on the authorized host so later, separately approved H3 or LTX work can be preflighted honestly, while preserving every model byte and a deterministic way to restore the two superseded files to their original paths. Observable outcome: the operator can inspect one host-run bundle and see live before/after hashes, sizes, free bytes, exact move outcomes, and a restoration mapping for both files.

## OUT OF SCOPE

- WD-bw0h H3 retry or generated artifact: requires a separate approval after this storage precondition succeeds.
- WD-28ac five-asset/23,701,298,279-byte LTX download or host run: still unauthorized.
- Model download, HEAD request, inference, GPU work, provider API, training, or queue admission.
- Moving, copying, linking, rewriting, or deleting any file other than the two exact source candidates above.
- `sudo`, privileged escalation, permissions repair, alternate offload roots, filesystem cleanup, or deletion of partial/destination files.
- Protected engine changes to `services/jobs/queue.py`, `services/director/renderers/policy.py`, `services/director/wiring.py`, `services/jobs/preflight.py`, or `scripts/run_film.py`.
- Rewriting accepted WD-bw0h, WD-28ac, or WD-1s5s evidence.

## DIFF BUDGET

- About 5-8 files and under 700 authored/evidence LOC: an authorization record, fail-closed host runner, focused tests, and one immutable host-run evidence bundle.

## Boundary Map

PRODUCES:
- datasets/runs/maestro-parity/h3-offload/operator-authorization.json -> `wangp-dspy.h3-offload-authorization/v1`
  schema: binds verbatim approval, host `3090`, the two exact source/destination identities, ordinary-user offload root, no-deletion boundary, and zero downstream job authority.
- scripts/run_h3_offload.py -> preflight(root: Path, record: Mapping[str, object], host: SshHostLike) -> dict
  spec: read-only host preflight validates target identity, source existence/type/size/hash, destination-root mount containment, free space, collisions, and records all facts without mutation.
- scripts/run_h3_offload.py -> execute(root: Path, record: Mapping[str, object], host: SshHostLike) -> dict
  spec: after preflight, stage one sh script through RenderHost/SshHost, execute exactly one authorized offload attempt, hash/verify each moved file, and automatically reverse partial progress on failure before returning a typed result.
- datasets/runs/maestro-parity/h3-offload/host-run/ -> immutable evidence bundle
  event: authorization, repository commit/tree, exact commands/staged-script identities, host facts, before/after hashes/sizes/free bytes, move outcomes, rollback state if applicable, and recovery mapping.
- tests/test_h3_offload.py -> real-process local regressions
  event: authorization parsing, fail-closed preflight/move script generation, command/path containment, rollback behavior, evidence invariants, and no network/model/queue action in local tests.

CONSUMES:
- WD-1s5s: datasets/runs/maestro-parity/storage-remediation-prep/inputs.json -> `wangp-dspy.storage-remediation-input/v1`
  source: superseded candidate IDs/sizes, offload root, doctor floor, stale disk snapshots, and no-deletion boundary; live values must be re-measured.
- WD-1s5s: datasets/runs/maestro-parity/storage-remediation-prep/local-plan.json -> `wangp-dspy.storage-remediation-plan/v1`
  source: projection and `snapshot_only=true`; the projection may not be treated as a live result.
- (existing): host/render_host.py -> `SshHost.__init__(*, target: str, wgp_root: str, pull_root: str, sp: Callable = _sp, port: Optional[int] = None, asset_map: Optional[dict] = None)`
  source: use its `run_probe(argv, timeout=30) -> (rc, stdout, stderr)`, `push_file(local, remote) -> str`, and `run_argv(cmd, *, cwd, timeout) -> result` seams rather than ad-hoc inline SSH strings.
- (existing): wangp/doctor.py -> `REMOTE_MINIMUM_FREE_GB: float = 50.0`
  source: report whether the post-offload root filesystem reaches the current 50-GiB doctor floor, but do not modify the constant.

## Story Acceptance Criteria

1. [State] Before mutation, a read-only preflight on host `3090` proves both exact source paths are regular non-symlink files, have the exact recorded sizes, obtains each live SHA-256, verifies `/mnt/bulk-hdd` is the containing mounted filesystem, verifies or safely creates the exact ordinary-user offload root, and verifies enough live bulk-HDD free space for the combined `44,288,216,793` bytes plus at least 1 GiB margin.
2. [Unwanted] Preflight fails closed with a typed diagnostic and zero host mutation if host identity, source path/type/size, root containment, write permission, destination collision, free space, or script identity is absent, ambiguous, mismatched, symlinked, or outside the authorized set. A zero-mutation preflight boundary must record the actual branch/commit and prove staging/mutation was not reached; it does not consume the mutation budget.
3. [State] The sole mutation attempt moves exactly the two candidates with no-clobber semantics to their exact destination paths, performs no `rm`, truncate, rewrite, download, hard-link, symlink, privileged command, or unrelated filesystem action, and records source-absent/destination-present outcomes.
4. [State] For each candidate, post-move byte size equals the recorded size and post-move SHA-256 equals the live pre-move SHA-256; the evidence records both hashes and a reversible source-to-destination recovery mapping.
5. [State] If any step fails after the first move, the same authorized attempt automatically reverses already-moved files to their exact original paths, verifies size/hash, records rollback evidence, and leaves no partial offload claim; a rollback failure is a typed critical boundary and must not be retried automatically.
6. [State] Post-offlight records live root and bulk-HDD free bytes, states whether the root filesystem reaches the 53,687,091,200-byte doctor floor, and clearly labels this storage result as neither a generation result nor a hardware-verdict/capability promotion.
7. [Unwanted] No WD-bw0h retry, WD-28ac download/inference, model download/read for inference, GPU work, provider spend, queue job, protected-engine edit, unrelated host mutation, deletion, or accepted-story evidence overwrite occurs.
8. [State] Focused real-process tests, the undeselected full suite, `pvg verify` on the runner/tests/authorization, `pvg lint --backlog`, `wgp release verify` with `release=ready` and `tag_created=false`, protected-file parity, `git diff --check`, and exact-head CI pass.

## Testing Requirements

- Unit: authorization validation, exact candidate set/totals, remote script syntax/path containment, typed preflight failures, no-clobber move semantics, rollback ordering, and evidence invariants.
- Integration: MANDATORY with no mocked host operation for the authorized run. Use the real `SshHost` path against host `3090` and a real staged script; do not patch SSH, hashing, move, filesystem, or evidence behavior.
- Negative paths: wrong host, wrong size, absent source, symlink source, destination exists, insufficient bulk space, offload root outside `/mnt/bulk-hdd`, unauthorized third path, and partial-move rollback.
- Local tests must not contact the host; the sole live integration is the one authorized execution.
- Commands: focused pytest, undeselected full pytest, pvg verify, backlog lint, release verification, protected parity, diff check, and exact-head CI.

## MANDATORY SKILLS

- pvg
- tool-systematic-debugging

## Delivery Requirements

- Record verbatim authorization, exact repository commit, clean tree identity, host/user/filesystem identities, before/after hashes/sizes/free bytes, staged script SHA-256, move timing/outcome, rollback state, evidence file hashes, PR, and CI.
- Include `## Implementation Evidence`, `Summary:`, `Commands run:`, `SHA:`, `### CI/Test Results`, `### AC Verification`, and `LEARNINGS:`.
- Preserve every zero-mutation preflight boundary under `boundary-attempts/`. After the recorded 21:08 preflight defect only, repair locally and retry read-only preflight once; after a passing preflight, execute the sole mutation attempt. Any later preflight or execution failure stops for a fresh decision; never substitute an artifact.
- Deliver through `pvg story deliver`; do not self-accept.

## nd_contract
status: new

### evidence
- Created from verbatim operator approval `Approved authorized` at `2026-09-30T19:57:10Z`, merged main `498a9cb4c994033064161cace2a98165c0a1dbb2`, accepted WD-1s5s packet, and the exact two-candidate reversible-offload boundary above.

### proof
- [ ] Pending live preflight, sole reversible offload execution, post-move hash/size/free verification, evidence bundle, tests, standing gates, and exact-head CI.

## Context (Embedded)

Operator authorization is now explicit for one narrowly bounded storage action. Verbatim input at `2026-09-30T19:57:10Z`:

> Approved authorized

This is the approval for the immediately preceding question: **reversible offload of exactly the two superseded H3 checkpoints on host `3090`, with live size/SHA verification, a reversible recovery path, and no deletion.** It does **not** authorize a new WD-bw0h H3 generation retry, WD-28ac LTX download, model access for inference, provider spend, or queue admission.

Current authoritative base is `main@498a9cb4c994033064161cace2a98165c0a1dbb2`. `WD-1s5s` is accepted/merged and supplies the local-only packet; its stale disk numbers must not be reused as live facts.

Exact authorized candidates:

| ID | Source | Recorded bytes | Destination |
| --- | --- | ---: | --- |
| superseded-h3-checkpoint-1 | `/home/straughter/Wan2GP/ckpts/MiniMax-H3-FL2VA-pruned_int8_convrot.safetensors` | 22,144,108,396 | `/mnt/bulk-hdd/straughter/model-offload/wangp-3090/MiniMax-H3-FL2VA-pruned_int8_convrot.safetensors` |
| superseded-h3-checkpoint-2 | `/home/straughter/Wan2GP/ckpts/MiniMax-H3-Ref2VA-pruned_int8_convrot.safetensors` | 22,144,108,397 | `/mnt/bulk-hdd/straughter/model-offload/wangp-3090/MiniMax-H3-Ref2VA-pruned_int8_convrot.safetensors` |

Exact combined recovery: `44,288,216,793` bytes. Their SHA-256 values are intentionally unknown in the accepted packet; this story must measure them live and prove before/after identity without inventing a prior value.

The offload root is exactly `/mnt/bulk-hdd/straughter/model-offload/wangp-3090/`. It may be created or verified with ordinary user permissions only. Do not use `sudo`, an alternate root, or a broader cleanup. If ordinary creation/verification fails, stop with a typed boundary.

The previous WD-bw0h attempt stopped at `STORAGE_PREPARATION_FAILED` / `cannot create offload root`; preserve that history and do not overwrite WD-bw0h evidence.

### Preflight-retry adjudication

Read-only host validation does not consume the one mutation attempt. The recorded `2026-09-30T21:08:21Z` boundary `H3_ROOT_CONTAINMENT_INVALID` proved that staging, `push_file`, `run_argv`, root creation, and both moves were not reached. Preserve those three files immutably under a dated `boundary-attempts/` directory, repair the local mount-probe and repository-branch evidence defects, then one fresh read-only preflight is allowed under the same operator approval. The mutation budget remains exactly one and begins only after a complete passing preflight. A second preflight boundary after this adjudication requires a fresh dispatcher/operator decision.

## USER INTENT

The completed command returns a typed PASS result only after it stores immutable before/after evidence and emits a reversible two-file restoration mapping; otherwise it returns a typed failure boundary.

Free enough space on the authorized host so later, separately approved H3 or LTX work can be preflighted honestly, while preserving every model byte and a deterministic way to restore the two superseded files to their original paths. Observable outcome: the operator can inspect one host-run bundle and see live before/after hashes, sizes, free bytes, exact move outcomes, and a restoration mapping for both files.

## OUT OF SCOPE

- WD-bw0h H3 retry or generated artifact: requires a separate approval after this storage precondition succeeds.
- WD-28ac five-asset/23,701,298,279-byte LTX download or host run: still unauthorized.
- Model download, HEAD request, inference, GPU work, provider API, training, or queue admission.
- Moving, copying, linking, rewriting, or deleting any file other than the two exact source candidates above.
- `sudo`, privileged escalation, permissions repair, alternate offload roots, filesystem cleanup, or deletion of partial/destination files.
- Protected engine changes to `services/jobs/queue.py`, `services/director/renderers/policy.py`, `services/director/wiring.py`, `services/jobs/preflight.py`, or `scripts/run_film.py`.
- Rewriting accepted WD-bw0h, WD-28ac, or WD-1s5s evidence.

## DIFF BUDGET

- About 5-8 files and under 700 authored/evidence LOC: an authorization record, fail-closed host runner, focused tests, and one immutable host-run evidence bundle.

## Boundary Map

PRODUCES:
- datasets/runs/maestro-parity/h3-offload/operator-authorization.json -> `wangp-dspy.h3-offload-authorization/v1`
  schema: binds verbatim approval, host `3090`, the two exact source/destination identities, ordinary-user offload root, no-deletion boundary, and zero downstream job authority.
- scripts/run_h3_offload.py -> preflight(root: Path, record: Mapping[str, object], host: SshHostLike) -> dict
  spec: read-only host preflight validates target identity, source existence/type/size/hash, destination-root mount containment, free space, collisions, and records all facts without mutation.
- scripts/run_h3_offload.py -> execute(root: Path, record: Mapping[str, object], host: SshHostLike) -> dict
  spec: after preflight, stage one sh script through RenderHost/SshHost, execute exactly one authorized offload attempt, hash/verify each moved file, and automatically reverse partial progress on failure before returning a typed result.
- datasets/runs/maestro-parity/h3-offload/host-run/ -> immutable evidence bundle
  event: authorization, repository commit/tree, exact commands/staged-script identities, host facts, before/after hashes/sizes/free bytes, move outcomes, rollback state if applicable, and recovery mapping.
- tests/test_h3_offload.py -> real-process local regressions
  event: authorization parsing, fail-closed preflight/move script generation, command/path containment, rollback behavior, evidence invariants, and no network/model/queue action in local tests.

CONSUMES:
- WD-1s5s: datasets/runs/maestro-parity/storage-remediation-prep/inputs.json -> `wangp-dspy.storage-remediation-input/v1`
  source: superseded candidate IDs/sizes, offload root, doctor floor, stale disk snapshots, and no-deletion boundary; live values must be re-measured.
- WD-1s5s: datasets/runs/maestro-parity/storage-remediation-prep/local-plan.json -> `wangp-dspy.storage-remediation-plan/v1`
  source: projection and `snapshot_only=true`; the projection may not be treated as a live result.
- (existing): host/render_host.py -> `SshHost.__init__(*, target: str, wgp_root: str, pull_root: str, sp: Callable = _sp, port: Optional[int] = None, asset_map: Optional[dict] = None)`
  source: use its `run_probe(argv, timeout=30) -> (rc, stdout, stderr)`, `push_file(local, remote) -> str`, and `run_argv(cmd, *, cwd, timeout) -> result` seams rather than ad-hoc inline SSH strings.
- (existing): wangp/doctor.py -> `REMOTE_MINIMUM_FREE_GB: float = 50.0`
  source: report whether the post-offload root filesystem reaches the current 50-GiB doctor floor, but do not modify the constant.

## Story Acceptance Criteria

1. [State] Before mutation, a read-only preflight on host `3090` proves both exact source paths are regular non-symlink files, have the exact recorded sizes, obtains each live SHA-256, verifies `/mnt/bulk-hdd` is the containing mounted filesystem, verifies or safely creates the exact ordinary-user offload root, and verifies enough live bulk-HDD free space for the combined `44,288,216,793` bytes plus at least 1 GiB margin.
2. [Unwanted] Preflight fails closed with a typed diagnostic and zero host mutation if host identity, source path/type/size, root containment, write permission, destination collision, free space, or script identity is absent, ambiguous, mismatched, symlinked, or outside the authorized set. A zero-mutation preflight boundary must record the actual branch/commit and prove staging/mutation was not reached; it does not consume the mutation budget.
3. [State] The sole mutation attempt moves exactly the two candidates with no-clobber semantics to their exact destination paths, performs no `rm`, truncate, rewrite, download, hard-link, symlink, privileged command, or unrelated filesystem action, and records source-absent/destination-present outcomes.
4. [State] For each candidate, post-move byte size equals the recorded size and post-move SHA-256 equals the live pre-move SHA-256; the evidence records both hashes and a reversible source-to-destination recovery mapping.
5. [State] If any step fails after the first move, the same authorized attempt automatically reverses already-moved files to their exact original paths, verifies size/hash, records rollback evidence, and leaves no partial offload claim; a rollback failure is a typed critical boundary and must not be retried automatically.
6. [State] Post-offlight records live root and bulk-HDD free bytes, states whether the root filesystem reaches the 53,687,091,200-byte doctor floor, and clearly labels this storage result as neither a generation result nor a hardware-verdict/capability promotion.
7. [Unwanted] No WD-bw0h retry, WD-28ac download/inference, model download/read for inference, GPU work, provider spend, queue job, protected-engine edit, unrelated host mutation, deletion, or accepted-story evidence overwrite occurs.
8. [State] Focused real-process tests, the undeselected full suite, `pvg verify` on the runner/tests/authorization, `pvg lint --backlog`, `wgp release verify` with `release=ready` and `tag_created=false`, protected-file parity, `git diff --check`, and exact-head CI pass.

## Testing Requirements

- Unit: authorization validation, exact candidate set/totals, remote script syntax/path containment, typed preflight failures, no-clobber move semantics, rollback ordering, and evidence invariants.
- Integration: MANDATORY with no mocked host operation for the authorized run. Use the real `SshHost` path against host `3090` and a real staged script; do not patch SSH, hashing, move, filesystem, or evidence behavior.
- Negative paths: wrong host, wrong size, absent source, symlink source, destination exists, insufficient bulk space, offload root outside `/mnt/bulk-hdd`, unauthorized third path, and partial-move rollback.
- Local tests must not contact the host; the sole live integration is the one authorized execution.
- Commands: focused pytest, undeselected full pytest, pvg verify, backlog lint, release verification, protected parity, diff check, and exact-head CI.

## MANDATORY SKILLS

- pvg
- tool-systematic-debugging

## Delivery Requirements

- Record verbatim authorization, exact repository commit, clean tree identity, host/user/filesystem identities, before/after hashes/sizes/free bytes, staged script SHA-256, move timing/outcome, rollback state, evidence file hashes, PR, and CI.
- Include `## Implementation Evidence`, `Summary:`, `Commands run:`, `SHA:`, `### CI/Test Results`, `### AC Verification`, and `LEARNINGS:`.
- Preserve every zero-mutation preflight boundary under `boundary-attempts/`. After the recorded 21:08 preflight defect only, repair locally and retry read-only preflight once; after a passing preflight, execute the sole mutation attempt. Any later preflight or execution failure stops for a fresh decision; never substitute an artifact.
- Deliver through `pvg story deliver`; do not self-accept.

## nd_contract
status: new

### evidence
- Created from verbatim operator approval `Approved authorized` at `2026-09-30T19:57:10Z`, merged main `498a9cb4c994033064161cace2a98165c0a1dbb2`, accepted WD-1s5s packet, and the exact two-candidate reversible-offload boundary above.

### proof
- [ ] Pending live preflight, sole reversible offload execution, post-move hash/size/free verification, evidence bundle, tests, standing gates, and exact-head CI.

## Context (Embedded)

Operator authorization is now explicit for one narrowly bounded storage action. Verbatim input at `2026-09-30T19:57:10Z`:

> Approved authorized

This is the approval for the immediately preceding question: **reversible offload of exactly the two superseded H3 checkpoints on host `3090`, with live size/SHA verification, a reversible recovery path, and no deletion.** It does **not** authorize a new WD-bw0h H3 generation retry, WD-28ac LTX download, model access for inference, provider spend, or queue admission.

Current authoritative base is `main@498a9cb4c994033064161cace2a98165c0a1dbb2`. `WD-1s5s` is accepted/merged and supplies the local-only packet; its stale disk numbers must not be reused as live facts.

Exact authorized candidates:

| ID | Source | Recorded bytes | Destination |
| --- | --- | ---: | --- |
| superseded-h3-checkpoint-1 | `/home/straughter/Wan2GP/ckpts/MiniMax-H3-FL2VA-pruned_int8_convrot.safetensors` | 22,144,108,396 | `/mnt/bulk-hdd/straughter/model-offload/wangp-3090/MiniMax-H3-FL2VA-pruned_int8_convrot.safetensors` |
| superseded-h3-checkpoint-2 | `/home/straughter/Wan2GP/ckpts/MiniMax-H3-Ref2VA-pruned_int8_convrot.safetensors` | 22,144,108,397 | `/mnt/bulk-hdd/straughter/model-offload/wangp-3090/MiniMax-H3-Ref2VA-pruned_int8_convrot.safetensors` |

Exact combined recovery: `44,288,216,793` bytes. Their SHA-256 values are intentionally unknown in the accepted packet; this story must measure them live and prove before/after identity without inventing a prior value.

The offload root is exactly `/mnt/bulk-hdd/straughter/model-offload/wangp-3090/`. It may be created or verified with ordinary user permissions only. Do not use `sudo`, an alternate root, or a broader cleanup. If ordinary creation/verification fails, stop with a typed boundary.

The previous WD-bw0h attempt stopped at `STORAGE_PREPARATION_FAILED` / `cannot create offload root`; preserve that history and do not overwrite WD-bw0h evidence.

## USER INTENT

The completed command returns a typed PASS result only after it stores immutable before/after evidence and emits a reversible two-file restoration mapping; otherwise it returns a typed failure boundary.

Free enough space on the authorized host so later, separately approved H3 or LTX work can be preflighted honestly, while preserving every model byte and a deterministic way to restore the two superseded files to their original paths. Observable outcome: the operator can inspect one host-run bundle and see live before/after hashes, sizes, free bytes, exact move outcomes, and a restoration mapping for both files.

## OUT OF SCOPE

- WD-bw0h H3 retry or generated artifact: requires a separate approval after this storage precondition succeeds.
- WD-28ac five-asset/23,701,298,279-byte LTX download or host run: still unauthorized.
- Model download, HEAD request, inference, GPU work, provider API, training, or queue admission.
- Moving, copying, linking, rewriting, or deleting any file other than the two exact source candidates above.
- `sudo`, privileged escalation, permissions repair, alternate offload roots, filesystem cleanup, or deletion of partial/destination files.
- Protected engine changes to `services/jobs/queue.py`, `services/director/renderers/policy.py`, `services/director/wiring.py`, `services/jobs/preflight.py`, or `scripts/run_film.py`.
- Rewriting accepted WD-bw0h, WD-28ac, or WD-1s5s evidence.

## DIFF BUDGET

- About 5-8 files and under 700 authored/evidence LOC: an authorization record, fail-closed host runner, focused tests, and one immutable host-run evidence bundle.

## Boundary Map

PRODUCES:
- datasets/runs/maestro-parity/h3-offload/operator-authorization.json -> `wangp-dspy.h3-offload-authorization/v1`
  schema: binds verbatim approval, host `3090`, the two exact source/destination identities, ordinary-user offload root, no-deletion boundary, and zero downstream job authority.
- scripts/run_h3_offload.py -> preflight(root: Path, record: Mapping[str, object], host: SshHostLike) -> dict
  spec: read-only host preflight validates target identity, source existence/type/size/hash, destination-root mount containment, free space, collisions, and records all facts without mutation.
- scripts/run_h3_offload.py -> execute(root: Path, record: Mapping[str, object], host: SshHostLike) -> dict
  spec: after preflight, stage one sh script through RenderHost/SshHost, execute exactly one authorized offload attempt, hash/verify each moved file, and automatically reverse partial progress on failure before returning a typed result.
- datasets/runs/maestro-parity/h3-offload/host-run/ -> immutable evidence bundle
  event: authorization, repository commit/tree, exact commands/staged-script identities, host facts, before/after hashes/sizes/free bytes, move outcomes, rollback state if applicable, and recovery mapping.
- tests/test_h3_offload.py -> real-process local regressions
  event: authorization parsing, fail-closed preflight/move script generation, command/path containment, rollback behavior, evidence invariants, and no network/model/queue action in local tests.

CONSUMES:
- WD-1s5s: datasets/runs/maestro-parity/storage-remediation-prep/inputs.json -> `wangp-dspy.storage-remediation-input/v1`
  source: superseded candidate IDs/sizes, offload root, doctor floor, stale disk snapshots, and no-deletion boundary; live values must be re-measured.
- WD-1s5s: datasets/runs/maestro-parity/storage-remediation-prep/local-plan.json -> `wangp-dspy.storage-remediation-plan/v1`
  source: projection and `snapshot_only=true`; the projection may not be treated as a live result.
- (existing): host/render_host.py -> `SshHost.__init__(*, target: str, wgp_root: str, pull_root: str, sp: Callable = _sp, port: Optional[int] = None, asset_map: Optional[dict] = None)`
  source: use its `run_probe(argv, timeout=30) -> (rc, stdout, stderr)`, `push_file(local, remote) -> str`, and `run_argv(cmd, *, cwd, timeout) -> result` seams rather than ad-hoc inline SSH strings.
- (existing): wangp/doctor.py -> `REMOTE_MINIMUM_FREE_GB: float = 50.0`
  source: report whether the post-offload root filesystem reaches the current 50-GiB doctor floor, but do not modify the constant.

## Story Acceptance Criteria

1. [State] Before mutation, a read-only preflight on host `3090` proves both exact source paths are regular non-symlink files, have the exact recorded sizes, obtains each live SHA-256, verifies `/mnt/bulk-hdd` is the containing mounted filesystem, verifies or safely creates the exact ordinary-user offload root, and verifies enough live bulk-HDD free space for the combined `44,288,216,793` bytes plus at least 1 GiB margin.
2. [Unwanted] Preflight fails closed with a typed diagnostic and zero host mutation if host identity, source path/type/size, root containment, write permission, destination collision, free space, or script identity is absent, ambiguous, mismatched, symlinked, or outside the authorized set.
3. [State] The sole mutation attempt moves exactly the two candidates with no-clobber semantics to their exact destination paths, performs no `rm`, truncate, rewrite, download, hard-link, symlink, privileged command, or unrelated filesystem action, and records source-absent/destination-present outcomes.
4. [State] For each candidate, post-move byte size equals the recorded size and post-move SHA-256 equals the live pre-move SHA-256; the evidence records both hashes and a reversible source-to-destination recovery mapping.
5. [State] If any step fails after the first move, the same authorized attempt automatically reverses already-moved files to their exact original paths, verifies size/hash, records rollback evidence, and leaves no partial offload claim; a rollback failure is a typed critical boundary and must not be retried automatically.
6. [State] Post-offlight records live root and bulk-HDD free bytes, states whether the root filesystem reaches the 53,687,091,200-byte doctor floor, and clearly labels this storage result as neither a generation result nor a hardware-verdict/capability promotion.
7. [Unwanted] No WD-bw0h retry, WD-28ac download/inference, model download/read for inference, GPU work, provider spend, queue job, protected-engine edit, unrelated host mutation, deletion, or accepted-story evidence overwrite occurs.
8. [State] Focused real-process tests, the undeselected full suite, `pvg verify` on the runner/tests/authorization, `pvg lint --backlog`, `wgp release verify` with `release=ready` and `tag_created=false`, protected-file parity, `git diff --check`, and exact-head CI pass.

## Testing Requirements

- Unit: authorization validation, exact candidate set/totals, remote script syntax/path containment, typed preflight failures, no-clobber move semantics, rollback ordering, and evidence invariants.
- Integration: MANDATORY with no mocked host operation for the authorized run. Use the real `SshHost` path against host `3090` and a real staged script; do not patch SSH, hashing, move, filesystem, or evidence behavior.
- Negative paths: wrong host, wrong size, absent source, symlink source, destination exists, insufficient bulk space, offload root outside `/mnt/bulk-hdd`, unauthorized third path, and partial-move rollback.
- Local tests must not contact the host; the sole live integration is the one authorized execution.
- Commands: focused pytest, undeselected full pytest, pvg verify, backlog lint, release verification, protected parity, diff check, and exact-head CI.

## MANDATORY SKILLS

- pvg
- tool-systematic-debugging

## Delivery Requirements

- Record verbatim authorization, exact repository commit, clean tree identity, host/user/filesystem identities, before/after hashes/sizes/free bytes, staged script SHA-256, move timing/outcome, rollback state, evidence file hashes, PR, and CI.
- Include `## Implementation Evidence`, `Summary:`, `Commands run:`, `SHA:`, `### CI/Test Results`, `### AC Verification`, and `LEARNINGS:`.
- If preflight or execution fails, stop after recording the typed boundary and any automatic rollback; do not retry or substitute an artifact.
- Deliver through `pvg story deliver`; do not self-accept.

## nd_contract
status: new

### evidence
- Created from verbatim operator approval `Approved authorized` at `2026-09-30T19:57:10Z`, merged main `498a9cb4c994033064161cace2a98165c0a1dbb2`, accepted WD-1s5s packet, and the exact two-candidate reversible-offload boundary above.

### proof
- [ ] Pending live preflight, sole reversible offload execution, post-move hash/size/free verification, evidence bundle, tests, standing gates, and exact-head CI.

## Context (Embedded)

Operator authorization is now explicit for one narrowly bounded storage action. Verbatim input at `2026-09-30T19:57:10Z`:

> Approved authorized

This is the approval for the immediately preceding question: **reversible offload of exactly the two superseded H3 checkpoints on host `3090`, with live size/SHA verification, a reversible recovery path, and no deletion.** It does **not** authorize a new WD-bw0h H3 generation retry, WD-28ac LTX download, model access for inference, provider spend, or queue admission.

Current authoritative base is `main@498a9cb4c994033064161cace2a98165c0a1dbb2`. `WD-1s5s` is accepted/merged and supplies the local-only packet; its stale disk numbers must not be reused as live facts.

Exact authorized candidates:

| ID | Source | Recorded bytes | Destination |
| --- | --- | ---: | --- |
| superseded-h3-checkpoint-1 | `/home/straughter/Wan2GP/ckpts/MiniMax-H3-FL2VA-pruned_int8_convrot.safetensors` | 22,144,108,396 | `/mnt/bulk-hdd/straughter/model-offload/wangp-3090/MiniMax-H3-FL2VA-pruned_int8_convrot.safetensors` |
| superseded-h3-checkpoint-2 | `/home/straughter/Wan2GP/ckpts/MiniMax-H3-Ref2VA-pruned_int8_convrot.safetensors` | 22,144,108,397 | `/mnt/bulk-hdd/straughter/model-offload/wangp-3090/MiniMax-H3-Ref2VA-pruned_int8_convrot.safetensors` |

Exact combined recovery: `44,288,216,793` bytes. Their SHA-256 values are intentionally unknown in the accepted packet; this story must measure them live and prove before/after identity without inventing a prior value.

The offload root is exactly `/mnt/bulk-hdd/straughter/model-offload/wangp-3090/`. It may be created or verified with ordinary user permissions only. Do not use `sudo`, an alternate root, or a broader cleanup. If ordinary creation/verification fails, stop with a typed boundary.

The previous WD-bw0h attempt stopped at `STORAGE_PREPARATION_FAILED` / `cannot create offload root`; preserve that history and do not overwrite WD-bw0h evidence.

## USER INTENT

Free enough space on the authorized host so later, separately approved H3 or LTX work can be preflighted honestly, while preserving every model byte and a deterministic way to restore the two superseded files to their original paths. Observable outcome: the operator can inspect one host-run bundle and see live before/after hashes, sizes, free bytes, exact move outcomes, and a restoration mapping for both files.

## OUT OF SCOPE

- WD-bw0h H3 retry or generated artifact: requires a separate approval after this storage precondition succeeds.
- WD-28ac five-asset/23,701,298,279-byte LTX download or host run: still unauthorized.
- Model download, HEAD request, inference, GPU work, provider API, training, or queue admission.
- Moving, copying, linking, rewriting, or deleting any file other than the two exact source candidates above.
- `sudo`, privileged escalation, permissions repair, alternate offload roots, filesystem cleanup, or deletion of partial/destination files.
- Protected engine changes to `services/jobs/queue.py`, `services/director/renderers/policy.py`, `services/director/wiring.py`, `services/jobs/preflight.py`, or `scripts/run_film.py`.
- Rewriting accepted WD-bw0h, WD-28ac, or WD-1s5s evidence.

## DIFF BUDGET

- About 5-8 files and under 700 authored/evidence LOC: an authorization record, fail-closed host runner, focused tests, and one immutable host-run evidence bundle.

## Boundary Map

PRODUCES:
- datasets/runs/maestro-parity/h3-offload/operator-authorization.json -> `wangp-dspy.h3-offload-authorization/v1`
  schema: binds verbatim approval, host `3090`, the two exact source/destination identities, ordinary-user offload root, no-deletion boundary, and zero downstream job authority.
- scripts/run_h3_offload.py -> preflight(root: Path, record: Mapping[str, object], host: SshHostLike) -> dict
  spec: read-only host preflight validates target identity, source existence/type/size/hash, destination-root mount containment, free space, collisions, and records all facts without mutation.
- scripts/run_h3_offload.py -> execute(root: Path, record: Mapping[str, object], host: SshHostLike) -> dict
  spec: after preflight, stage one sh script through RenderHost/SshHost, execute exactly one authorized offload attempt, hash/verify each moved file, and automatically reverse partial progress on failure before returning a typed result.
- datasets/runs/maestro-parity/h3-offload/host-run/ -> immutable evidence bundle
  event: authorization, repository commit/tree, exact commands/staged-script identities, host facts, before/after hashes/sizes/free bytes, move outcomes, rollback state if applicable, and recovery mapping.
- tests/test_h3_offload.py -> real-process local regressions
  event: authorization parsing, fail-closed preflight/move script generation, command/path containment, rollback behavior, evidence invariants, and no network/model/queue action in local tests.

CONSUMES:
- WD-1s5s: datasets/runs/maestro-parity/storage-remediation-prep/inputs.json -> `wangp-dspy.storage-remediation-input/v1`
  source: superseded candidate IDs/sizes, offload root, doctor floor, stale disk snapshots, and no-deletion boundary; live values must be re-measured.
- WD-1s5s: datasets/runs/maestro-parity/storage-remediation-prep/local-plan.json -> `wangp-dspy.storage-remediation-plan/v1`
  source: projection and `snapshot_only=true`; the projection may not be treated as a live result.
- (existing): host/render_host.py -> `SshHost.__init__(*, target: str, wgp_root: str, pull_root: str, sp: Callable = _sp, port: Optional[int] = None, asset_map: Optional[dict] = None)`
  source: use its `run_probe(argv, timeout=30) -> (rc, stdout, stderr)`, `push_file(local, remote) -> str`, and `run_argv(cmd, *, cwd, timeout) -> result` seams rather than ad-hoc inline SSH strings.
- (existing): wangp/doctor.py -> `REMOTE_MINIMUM_FREE_GB: float = 50.0`
  source: report whether the post-offload root filesystem reaches the current 50-GiB doctor floor, but do not modify the constant.

## Story Acceptance Criteria

1. [State] Before mutation, a read-only preflight on host `3090` proves both exact source paths are regular non-symlink files, have the exact recorded sizes, obtains each live SHA-256, verifies `/mnt/bulk-hdd` is the containing mounted filesystem, verifies or safely creates the exact ordinary-user offload root, and verifies enough live bulk-HDD free space for the combined `44,288,216,793` bytes plus at least 1 GiB margin.
2. [Unwanted] Preflight fails closed with a typed diagnostic and zero host mutation if host identity, source path/type/size, root containment, write permission, destination collision, free space, or script identity is absent, ambiguous, mismatched, symlinked, or outside the authorized set.
3. [State] The sole mutation attempt moves exactly the two candidates with no-clobber semantics to their exact destination paths, performs no `rm`, truncate, rewrite, download, hard-link, symlink, privileged command, or unrelated filesystem action, and records source-absent/destination-present outcomes.
4. [State] For each candidate, post-move byte size equals the recorded size and post-move SHA-256 equals the live pre-move SHA-256; the evidence records both hashes and a reversible source-to-destination recovery mapping.
5. [State] If any step fails after the first move, the same authorized attempt automatically reverses already-moved files to their exact original paths, verifies size/hash, records rollback evidence, and leaves no partial offload claim; a rollback failure is a typed critical boundary and must not be retried automatically.
6. [State] Post-offlight records live root and bulk-HDD free bytes, states whether the root filesystem reaches the 53,687,091,200-byte doctor floor, and clearly labels this storage result as neither a generation result nor a hardware-verdict/capability promotion.
7. [Unwanted] No WD-bw0h retry, WD-28ac download/inference, model download/read for inference, GPU work, provider spend, queue job, protected-engine edit, unrelated host mutation, deletion, or accepted-story evidence overwrite occurs.
8. [State] Focused real-process tests, the undeselected full suite, `pvg verify` on the runner/tests/authorization, `pvg lint --backlog`, `wgp release verify` with `release=ready` and `tag_created=false`, protected-file parity, `git diff --check`, and exact-head CI pass.

## Testing Requirements

- Unit: authorization validation, exact candidate set/totals, remote script syntax/path containment, typed preflight failures, no-clobber move semantics, rollback ordering, and evidence invariants.
- Integration: MANDATORY with no mocked host operation for the authorized run. Use the real `SshHost` path against host `3090` and a real staged script; do not patch SSH, hashing, move, filesystem, or evidence behavior.
- Negative paths: wrong host, wrong size, absent source, symlink source, destination exists, insufficient bulk space, offload root outside `/mnt/bulk-hdd`, unauthorized third path, and partial-move rollback.
- Local tests must not contact the host; the sole live integration is the one authorized execution.
- Commands: focused pytest, undeselected full pytest, pvg verify, backlog lint, release verification, protected parity, diff check, and exact-head CI.

## MANDATORY SKILLS

- pvg
- tool-systematic-debugging

## Delivery Requirements

- Record verbatim authorization, exact repository commit, clean tree identity, host/user/filesystem identities, before/after hashes/sizes/free bytes, staged script SHA-256, move timing/outcome, rollback state, evidence file hashes, PR, and CI.
- Include `## Implementation Evidence`, `Summary:`, `Commands run:`, `SHA:`, `### CI/Test Results`, `### AC Verification`, and `LEARNINGS:`.
- If preflight or execution fails, stop after recording the typed boundary and any automatic rollback; do not retry or substitute an artifact.
- Deliver through `pvg story deliver`; do not self-accept.

## nd_contract
status: new

### evidence
- Created from verbatim operator approval `Approved authorized` at `2026-09-30T19:57:10Z`, merged main `498a9cb4c994033064161cace2a98165c0a1dbb2`, accepted WD-1s5s packet, and the exact two-candidate reversible-offload boundary above.

### proof
- [ ] Pending live preflight, sole reversible offload execution, post-move hash/size/free verification, evidence bundle, tests, standing gates, and exact-head CI.

## Context (Embedded)

Operator authorization is now explicit for one narrowly bounded storage action. Verbatim input at `2026-09-30T19:57:10Z`:

> Approved authorized

This is the approval for the immediately preceding question: **reversible offload of exactly the two superseded H3 checkpoints on host `3090`, with live size/SHA verification, a reversible recovery path, and no deletion.** It does **not** authorize a new WD-bw0h H3 generation retry, WD-28ac LTX download, model access for inference, provider spend, or queue admission.

Current authoritative base is `main@498a9cb4c994033064161cace2a98165c0a1dbb2`. `WD-1s5s` is accepted/merged and supplies the local-only packet; its stale disk numbers must not be reused as live facts.

Exact authorized candidates:

| ID | Source | Recorded bytes | Destination |
| --- | --- | ---: | --- |
| superseded-h3-checkpoint-1 | `/home/straughter/Wan2GP/ckpts/MiniMax-H3-FL2VA-pruned_int8_convrot.safetensors` | 22,144,108,396 | `/mnt/bulk-hdd/straughter/model-offload/wangp-3090/MiniMax-H3-FL2VA-pruned_int8_convrot.safetensors` |
| superseded-h3-checkpoint-2 | `/home/straughter/Wan2GP/ckpts/MiniMax-H3-Ref2VA-pruned_int8_convrot.safetensors` | 22,144,108,397 | `/mnt/bulk-hdd/straughter/model-offload/wangp-3090/MiniMax-H3-Ref2VA-pruned_int8_convrot.safetensors` |

Exact combined recovery: `44,288,216,793` bytes. Their SHA-256 values are intentionally unknown in the accepted packet; this story must measure them live and prove before/after identity without inventing a prior value.

The offload root is exactly `/mnt/bulk-hdd/straughter/model-offload/wangp-3090/`. It may be created or verified with ordinary user permissions only. Do not use `sudo`, an alternate root, or a broader cleanup. If ordinary creation/verification fails, stop with a typed boundary.

The previous WD-bw0h attempt stopped at `STORAGE_PREPARATION_FAILED` / `cannot create offload root`; preserve that history and do not overwrite WD-bw0h evidence.

## USER INTENT

Free enough space on the authorized host so later, separately approved H3 or LTX work can be preflighted honestly, while preserving every model byte and a deterministic way to restore the two superseded files to their original paths.

## OUT OF SCOPE

- WD-bw0h H3 retry or generated artifact: requires a separate approval after this storage precondition succeeds.
- WD-28ac five-asset/23,701,298,279-byte LTX download or host run: still unauthorized.
- Model download, HEAD request, inference, GPU work, provider API, training, or queue admission.
- Moving, copying, linking, rewriting, or deleting any file other than the two exact source candidates above.
- `sudo`, privileged escalation, permissions repair, alternate offload roots, filesystem cleanup, or deletion of partial/destination files.
- Protected engine changes to `services/jobs/queue.py`, `services/director/renderers/policy.py`, `services/director/wiring.py`, `services/jobs/preflight.py`, or `scripts/run_film.py`.
- Rewriting accepted WD-bw0h, WD-28ac, or WD-1s5s evidence.

## DIFF BUDGET

- About 5-8 files and under 700 authored/evidence LOC: an authorization record, fail-closed host runner, focused tests, and one immutable host-run evidence bundle.

## Boundary Map

PRODUCES:
- datasets/runs/maestro-parity/h3-offload/operator-authorization.json -> `wangp-dspy.h3-offload-authorization/v1`
  schema: binds verbatim approval, host `3090`, the two exact source/destination identities, ordinary-user offload root, no-deletion boundary, and zero downstream job authority.
- scripts/run_h3_offload.py -> preflight(root: Path, record: Mapping[str, object], host: SshHostLike) -> dict
  spec: read-only host preflight validates target identity, source existence/type/size/hash, destination-root mount containment, free space, collisions, and records all facts without mutation.
- scripts/run_h3_offload.py -> execute(root: Path, record: Mapping[str, object], host: SshHostLike) -> dict
  spec: after preflight, stage one sh script through RenderHost/SshHost, execute exactly one authorized offload attempt, hash/verify each moved file, and automatically reverse partial progress on failure before returning a typed result.
- datasets/runs/maestro-parity/h3-offload/host-run/ -> immutable evidence bundle
  event: authorization, repository commit/tree, exact commands/staged-script identities, host facts, before/after hashes/sizes/free bytes, move outcomes, rollback state if applicable, and recovery mapping.
- tests/test_h3_offload.py -> real-process local regressions
  event: authorization parsing, fail-closed preflight/move script generation, command/path containment, rollback behavior, evidence invariants, and no network/model/queue action in local tests.

CONSUMES:
- WD-1s5s: datasets/runs/maestro-parity/storage-remediation-prep/inputs.json -> `wangp-dspy.storage-remediation-input/v1`
  source: superseded candidate IDs/sizes, offload root, doctor floor, stale disk snapshots, and no-deletion boundary; live values must be re-measured.
- WD-1s5s: datasets/runs/maestro-parity/storage-remediation-prep/local-plan.json -> `wangp-dspy.storage-remediation-plan/v1`
  source: projection and `snapshot_only=true`; the projection may not be treated as a live result.
- (existing): host/render_host.py -> `SshHost.__init__(*, target: str, wgp_root: str, pull_root: str, sp: Callable = _sp, port: Optional[int] = None, asset_map: Optional[dict] = None)`
  source: use its `run_probe(argv, timeout=30) -> (rc, stdout, stderr)`, `push_file(local, remote) -> str`, and `run_argv(cmd, *, cwd, timeout) -> result` seams rather than ad-hoc inline SSH strings.
- (existing): wangp/doctor.py -> `REMOTE_MINIMUM_FREE_GB: float = 50.0`
  source: report whether the post-offload root filesystem reaches the current 50-GiB doctor floor, but do not modify the constant.

## Story Acceptance Criteria

1. [State] Before mutation, a read-only preflight on host `3090` proves both exact source paths are regular non-symlink files, have the exact recorded sizes, obtains each live SHA-256, verifies `/mnt/bulk-hdd` is the containing mounted filesystem, verifies or safely creates the exact ordinary-user offload root, and verifies enough live bulk-HDD free space for the combined `44,288,216,793` bytes plus at least 1 GiB margin.
2. [Unwanted] Preflight fails closed with a typed diagnostic and zero host mutation if host identity, source path/type/size, root containment, write permission, destination collision, free space, or script identity is absent, ambiguous, mismatched, symlinked, or outside the authorized set.
3. [State] The sole mutation attempt moves exactly the two candidates with no-clobber semantics to their exact destination paths, performs no `rm`, truncate, rewrite, download, hard-link, symlink, privileged command, or unrelated filesystem action, and records source-absent/destination-present outcomes.
4. [State] For each candidate, post-move byte size equals the recorded size and post-move SHA-256 equals the live pre-move SHA-256; the evidence records both hashes and a reversible source-to-destination recovery mapping.
5. [State] If any step fails after the first move, the same authorized attempt automatically reverses already-moved files to their exact original paths, verifies size/hash, records rollback evidence, and leaves no partial offload claim; a rollback failure is a typed critical boundary and must not be retried automatically.
6. [State] Post-offlight records live root and bulk-HDD free bytes, states whether the root filesystem reaches the 53,687,091,200-byte doctor floor, and clearly labels this storage result as neither a generation result nor a hardware-verdict/capability promotion.
7. [Unwanted] No WD-bw0h retry, WD-28ac download/inference, model download/read for inference, GPU work, provider spend, queue job, protected-engine edit, unrelated host mutation, deletion, or accepted-story evidence overwrite occurs.
8. [State] Focused real-process tests, the undeselected full suite, `pvg verify` on the runner/tests/authorization, `pvg lint --backlog`, `wgp release verify` with `release=ready` and `tag_created=false`, protected-file parity, `git diff --check`, and exact-head CI pass.

## Testing Requirements

- Unit: authorization validation, exact candidate set/totals, remote script syntax/path containment, typed preflight failures, no-clobber move semantics, rollback ordering, and evidence invariants.
- Integration: MANDATORY with no mocked host operation for the authorized run. Use the real `SshHost` path against host `3090` and a real staged script; do not patch SSH, hashing, move, filesystem, or evidence behavior.
- Negative paths: wrong host, wrong size, absent source, symlink source, destination exists, insufficient bulk space, offload root outside `/mnt/bulk-hdd`, unauthorized third path, and partial-move rollback.
- Local tests must not contact the host; the sole live integration is the one authorized execution.
- Commands: focused pytest, undeselected full pytest, pvg verify, backlog lint, release verification, protected parity, diff check, and exact-head CI.

## MANDATORY SKILLS

- pvg
- tool-systematic-debugging

## Delivery Requirements

- Record verbatim authorization, exact repository commit, clean tree identity, host/user/filesystem identities, before/after hashes/sizes/free bytes, staged script SHA-256, move timing/outcome, rollback state, evidence file hashes, PR, and CI.
- Include `## Implementation Evidence`, `Summary:`, `Commands run:`, `SHA:`, `### CI/Test Results`, `### AC Verification`, and `LEARNINGS:`.
- If preflight or execution fails, stop after recording the typed boundary and any automatic rollback; do not retry or substitute an artifact.
- Deliver through `pvg story deliver`; do not self-accept.

## nd_contract
status: new

### evidence
- Created from verbatim operator approval `Approved authorized` at `2026-09-30T19:57:10Z`, merged main `498a9cb4c994033064161cace2a98165c0a1dbb2`, accepted WD-1s5s packet, and the exact two-candidate reversible-offload boundary above.

### proof
- [ ] Pending live preflight, sole reversible offload execution, post-move hash/size/free verification, evidence bundle, tests, standing gates, and exact-head CI.

## Acceptance Criteria


## Design


## Notes
## Implementation Boundary (FINAL READ-ONLY PREFLIGHT)

- Final adjudicated retry command: `uv run --frozen --extra dev python scripts/run_h3_offload.py --authorization datasets/runs/maestro-parity/h3-offload/operator-authorization.json --execute`
- Producing commit/tree/branch: `5500a9be0da2daf9402c1c67555dd4d9c1ef22ad` / `fafb8ed40e6098604e9d35fcf467b05075741ee1` / `story/WD-cuzw`
- Mount adjudication result: passed. The exact `systemd-1`/`autofs` plus `/dev/sda4`/`ext4` namespace was accepted and both rows were recorded by the runner.
- New typed boundary: `H3_ROOT_CONTAINMENT_INVALID`
- Observed fact: authorized offload root did not exist; its existing bulk-HDD parent was a non-symlink directory on device `2052` but `writable=false` for the ordinary remote user.
- Boundary consequence: ordinary-user root creation was not attempted; `SshHost.push_file` and `SshHost.run_argv` were not reached.
- Preserved byte-identically under `datasets/runs/maestro-parity/h3-offload/host-run/boundary-attempts/20260930T214158Z/`:
  - `attempt.json` SHA-256 `36220166b4e198cca9237dd3bdf84c94f12f132412ab631eb05e4dd66d410f39`
  - `failure.json` SHA-256 `0ca3097140a285047b8f4744de8867f83b0a2dea9858c37b3353cafb1c4605af`
  - `evidence.sha256` SHA-256 `1fa69bf07ae1a5fc5bbe501b6c3b32068bf7dcc85769809f26cae5865c145c5b`
- No staged script, root creation, source move, destination write, rollback, retry, model download/inference, GPU work, provider action, or queue admission occurred. The sole mutation budget remains unconsumed.
- Per the final adjudication, this third read-only boundary stops for operator review. No permissions repair, sudo, alternate root, retry, PR, delivery, or self-acceptance is permitted.

## Implementation Boundary (SECOND READ-ONLY PREFLIGHT)

- Adjudicated retry command: `uv run --frozen --extra dev python scripts/run_h3_offload.py --authorization datasets/runs/maestro-parity/h3-offload/operator-authorization.json --execute`
- Producing commit/tree/branch: `e7dcb1e623fe919128521cfc3479b5ee75ff98f7` / `005fc86cd55abca7c9184230420b46a1d93475fc` / `story/WD-cuzw`
- Typed boundary: `H3_ROOT_CONTAINMENT_INVALID`
- Actual rows recorded in `failure.json`:
  - `{'target': '/mnt/bulk-hdd', 'source': 'systemd-1', 'filesystem_type': 'autofs'}`
  - `{'target': '/mnt/bulk-hdd', 'source': '/dev/sda4', 'filesystem_type': 'ext4'}`
- Preserved byte-identically under `datasets/runs/maestro-parity/h3-offload/host-run/boundary-attempts/20260930T213452Z/`:
  - `attempt.json` SHA-256 `173aedbc649a4a19fb731fc50c1a2b17e35404e071191dd458c910397bf45ddc`
  - `failure.json` SHA-256 `8b7eb5bf6828b514c88de104bad09772f55d2fd3e16133675893df16fb6eab9d`
  - `evidence.sha256` SHA-256 `bd2e2dc68ba8dcb201caf05eb5e5b857f1c19e347b22380ac0803a207e72c04a`
- Boundary proof: the run stopped before `SshHost.push_file` and `SshHost.run_argv`; no staged script, root creation, source move, destination write, rollback, retry, model download/inference, GPU work, provider action, or queue admission occurred.
- The single mutation budget remains unconsumed, but this second boundary requires a fresh dispatcher/operator decision as adjudicated. Stopping without repair, retry, PR, delivery, or self-acceptance.

## Implementation Boundary (FAILED PREFLIGHT)

- Command: `uv run --frozen --extra dev python scripts/run_h3_offload.py --authorization datasets/runs/maestro-parity/h3-offload/operator-authorization.json --execute`
- Producing commit/tree: `4e157f298b69699889bf01f2d78d4df2d702f140` / `523a4118e3f8ae64520f6e15526404113655e7b6`
- Typed boundary: `H3_ROOT_CONTAINMENT_INVALID`; `findmnt` returned 2 rows for `/mnt/bulk-hdd`.
- Evidence: `datasets/runs/maestro-parity/h3-offload/host-run/attempt.json` and `failure.json`; manifest hashes are in `evidence.sha256`.
- Process boundary: `stage.json`, `execution.json`, `offload-result.json`, and `run-summary.json` are absent; `SshHost.push_file` and `SshHost.run_argv` were never reached.
- No root creation, source move, destination write, rollback, retry, model download/inference, GPU work, provider action, or queue admission was issued.
- Stopping without delivery or retry as required.

DISCOVERED_BUG:
  title: H3 offload attempt evidence records an invalid branch identity
  context: The one read-only preflight failed correctly on ambiguous mount output, but `attempt.json` recorded branch as the literal `--abbrev-ref HEAD` instead of `story/WD-cuzw`. Root cause is passing `--abbrev-ref HEAD` to `git rev-parse` as one argv element rather than separate arguments. The failed evidence must remain immutable; fix requires a new story/authorization path because this story must not retry.
  affected_files: scripts/run_h3_offload.py; datasets/runs/maestro-parity/h3-offload/host-run/attempt.json
  discovered_during: WD-cuzw

## History
- 2026-09-30T20:00:02Z dep_added: blocks WD-fay0
- 2026-09-30T20:00:02Z dep_added: blocks WD-bw0h
- 2026-09-30T20:00:02Z dep_added: blocks WD-28ac
- 2026-09-30T20:00:52Z status: open -> in_progress
- 2026-09-30T20:00:52Z auto-follows: linked to predecessor WD-he8i
- 2026-09-30T20:00:52Z claimed by dev-WD-cuzw
- 2026-09-30T21:09:40Z status: in_progress -> open
- 2026-09-30T21:09:40Z released by speed
- 2026-09-30T21:15:01Z status: open -> in_progress
- 2026-09-30T21:15:01Z auto-follows: linked to predecessor WD-qthq
- 2026-09-30T21:15:01Z claimed by dev-WD-cuzw
- 2026-09-30T21:35:42Z status: in_progress -> open
- 2026-09-30T21:35:42Z released by speed
- 2026-09-30T21:36:55Z status: open -> in_progress
- 2026-09-30T21:36:55Z auto-follows: linked to predecessor WD-23rs
- 2026-09-30T21:36:55Z claimed by dev-WD-cuzw
- 2026-09-30T21:42:32Z status: in_progress -> open
- 2026-09-30T21:42:32Z released by speed
- 2026-10-01T19:00:26Z status: open -> in_progress
- 2026-10-01T19:00:27Z auto-follows: linked to predecessor WD-p587
- 2026-10-01T19:00:27Z claimed by dev-WD-cuzw

## Links
- Parent: [[WD-3nod]]
- Blocks: [[WD-fay0]], [[WD-bw0h]], [[WD-28ac]]
- Follows: [[WD-1s5s]], [[WD-he8i]], [[WD-qthq]], [[WD-23rs]], [[WD-p587]]

## Comments

### 2026-09-30T21:15:01Z speed
DISPATCHER ADJUDICATION: the 2026-09-30T21:08:21Z H3_ROOT_CONTAINMENT_INVALID boundary was read-only and provably stopped before push_file/run_argv/root creation/move. It did not consume the single mutation attempt. Preserve it immutably under boundary-attempts, repair the local mount parsing and branch argv defect, retry read-only preflight once, and only then use the original operator approval for the sole mutation attempt. No H3 retry/LTX/download/queue authority is added.

### 2026-09-30T21:36:54Z speed
FINAL DISPATCHER ADJUDICATION: the second boundary proved the expected mount namespace, not an unsafe mount: systemd autofs plus /dev/sda4 ext4 both target /mnt/bulk-hdd. Accept exactly that shape, record both rows, select the unique non-autofs ext4 block mount, and enforce resolved-root containment. One final read-only preflight retry is approved; mutation budget remains one. Any other shape or third preflight failure stops for operator review.

### 2026-09-30T21:44:26Z speed
Local evidence found an alternative already-proven ordinary-user destination: accepted WD-osfm successfully stored a 34,038,903,007-byte H3 checkpoint at /Users/Shared/HermesWorkspace/model-offload/wangp-3090/ and verified size/SHA before freeing the remote source. Current local free space is about 71 GiB, enough for the two 44,288,216,793-byte candidates but with only about 27 GiB headroom. This is not authorization to use it; an explicit offload-root change and verified-copy/free-source semantics are required.

### 2026-09-30T21:45:23Z speed
Read-only alternate-destination audit at 2026-09-30T21:46Z: both exact candidate destination names are absent under /Users/Shared/HermesWorkspace/model-offload/wangp-3090. Live local free space is 76,998,832,128 bytes; required candidate bytes are 44,288,216,793; projected headroom is 32,710,615,335 bytes, passing a 2-GiB safety margin. The only existing file there is the accepted WD-osfm 34,038,903,007-byte checkpoint. No host contact, file creation, move, deletion, or remote-source unlink occurred. Operator approval is still required to switch destinations and use verified-copy-then-free-remote-source semantics.

### 2026-10-01T19:00:27Z speed
OPERATOR DESTINATION DECISION at 2026-10-01T00:00:00Z. Verbatim user input: You decide. Dispatcher decision: use the already-proven ordinary-user destination /Users/Shared/HermesWorkspace/model-offload/wangp-3090/ for both exact superseded H3 candidates. Required semantics: sequential resumable local .part copies, exact pre/post size and SHA-256 verification, atomic promotion to final names, verify BOTH local copies before freeing either remote source, preserve restoration mappings, and stop/rollback on any mismatch. This decision does not authorize H3 generation, LTX download, inference, GPU work, queue admission, or unrelated storage mutation.

### 2026-10-01T19:01:02Z speed
TIMESTAMP CORRECTION: the immediately preceding destination-decision comment recorded 2026-10-01T00:00:00Z in error. The verbatim You decide decision was observed and recorded at 2026-10-01T19:00:26Z. Decision text and boundary are unchanged.
