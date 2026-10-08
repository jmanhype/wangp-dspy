---
id: WD-nkdv
title: "Record Wangp runner execution identity for LTX operations"
status: open
priority: 0
type: task
labels: [bug, evidence, qc, rejected]
parent: WD-3nod
created_at: 2026-10-08T22:01:40Z
created_by: speed
updated_at: 2026-10-08T23:04:53Z
content_hash: "sha256:4c7b674d0e6802a0fd5cf485c9a53ce7e5d8a3d84d222c97fdbf274444889fd8"
blocks: [WD-b7ek, WD-fay0]
follows: [WD-5d19, WD-28ac]
---

## Description

Bug: 
Bug: make LTX final-operation stage inventory prove exact Wangp runner identity

## Context (Embedded)

- Brownfield base is merged main `582014de1464424ad22e9bb7e85eea717409622f` (PR #232).
- This bug was discovered while auditing deferred `WD-b7ek` (LTX-2.3 Upscale promotion). `WD-b7ek` remains deferred and must not be implemented, accepted, or unblocked by editing evidence.
- Preserved retry3 evidence is read-only at `datasets/runs/maestro-parity/ltx-dependency-terminalization/final-cell-retry3-20261008/`. Its 42-file manifest, four `ltx23-upscale` operation hashes, source input, authorization digest, and source/output media probes were independently verified.
- The blocker is provenance, not media existence. `stage-inventory.json` in that bundle records only `root=/tmp/ltx-final-cell-retry3/repository`, `file_count=13`, and 13 path strings. It has no Wangp commit, no clean/dirty status, and no per-file size or SHA-256.
- Existing native/preflight commit fields identify Wan2GP execution trees: `4c93b64a47b5b0a915f2abec2ce754be98227150` (WD-osfm) or `faea82d15bf10b3479c42c0ea430892aae975870` (WD-m7xw). Those commits must remain source-tree facts; they are not Wangp runner identity.
- `authorization.metadata_correction.repository_revision=6aa898aea1d968febdd834dc29e1dbef35340aeb` is model-metadata provenance and must not be relabeled as the runner commit.
- The resulting promotion boundary is exactly `EXECUTION_REPOSITORY_IDENTITY_UNPROVEN`. Preservation merge `582014de` must not be substituted for the missing execution identity.
- The audit source available during story creation was `/tmp/WD-b7ek-identity-audit.json`: 6,108 bytes, SHA-256 `5a50d08edb75cdb733a3704b55333acf4318f549ae7a5a13ecfa4d91fb0d52f7`. The complete verbatim bytes are embedded below so this story does not depend on `/tmp`.
- Current source surfaces are real and exist at this HEAD:
  - `scripts/run_ltx_final_operations.py`
  - `scripts/prepare_ltx_operations.py`
  - `services/director/run_ledger.py`
  - `tests/test_ltx_final_operations_runner.py`
  - `tests/test_ltx_phase_b_preparation.py`
- Codebase-memory reported no graph record for those exact files (generation 2026-08-23), so this contract is based on direct source reads, not graph-only inference.

## USER INTENT

The operator needs future LTX evidence to bind execution outputs to the exact Wangp runner revision and every staged runner byte, not merely to a list of filenames or to the Wan2GP trees that host the native process. The immediate user outcome is a local, test-backed repair that makes future stage inventory generation succeed only with complete Wangp identity and fail closed on dirty, missing, malformed, or drifted state. This repairs the producer of future evidence; it does not make the existing retry3 bundle promotable.

Observable outcome: a developer can run focused local tests that show a clean Wangp checkout producing a complete hashed inventory and dirty/missing/hash-drift fixtures producing typed failures, with no host, render, download, or matrix action.

## Required Inventory Contract

The final-operation stage inventory must use a versioned object with at least:

```json
{
  "schema_version": "wangp-dspy.ltx-stage-inventory/v2",
  "repository": {
    "repo_root": "<absolute Wangp repository root>",
    "commit_sha": "<lowercase 40-character SHA-1>",
    "status_porcelain_v1": "<verbatim git status --porcelain=v1 output>",
    "clean_tree": true,
    "dirty_tree": false,
    "status_sha256": "<64 lowercase hex characters>"
  },
  "staged_root": "<absolute staged runner root>",
  "file_count": 13,
  "files": [
    {
      "path": "<repo-relative POSIX path>",
      "size_bytes": 0,
      "sha256": "<64 lowercase hex characters>"
    }
  ]
}
```

Contract rules:

- `repository` must identify the Wangp repository that supplies the runner bytes. It must never be populated from `operation["source_root"]`, because those roots are Wan2GP trees.
- `status_porcelain_v1`, `clean_tree`, and `dirty_tree` must be captured explicitly and agree with each other. Empty status means clean; any nonempty status is dirty.
- This story provides no dirty-run override. A nonempty Wangp status fails closed; any future dirty-execution exception requires separate operator authorization.
- `files` must be derived recursively from the actual staged root and cover every regular staged runner file. Paths must be sorted, POSIX-relative, duplicate-free, and free of `..`; symlinks, directories, devices, and unexpected/missing paths are invalid.
- The current retry3 13-path list is regression context, not a hard-coded allowlist: the inventory must describe the actual staged set and must not hide an added or removed runner file.
- An inventory with absent, malformed, extra, missing, or hash-drifted repository/file facts is invalid and must produce a typed `FinalOperationError`; inability to prove identity at the promotion boundary remains `EXECUTION_REPOSITORY_IDENTITY_UNPROVEN`.

## OUT OF SCOPE

- Any SSH/host-3090 contact, health/QC-service contact, native execution, queue admission, render, retry, model access, download, package install, provider spend, or network request: this is a local code/test/evidence story only; future execution needs separate authorization.
- Promoting `WD-b7ek` or changing `docs/video-capabilities.md`, the parity index, census, checker thresholds, or any matrix cell: `WD-b7ek` is the separately deferred consumer and remains blocked on provenance plus any required future authorized execution.
- Rewriting, backfilling, rehashing, or reinterpreting the preserved retry3 bundle to manufacture a Wangp commit: historical evidence remains immutable; absence of identity stays a fail-closed fact.
- Replacing Wan2GP source-tree identity checks in `scripts/prepare_ltx_operations.py` or `scripts/run_ltx_final_operations.py`: those Wan2GP commits/statuses remain distinct required facts. Only the missing Wangp runner identity contract is added.
- Broad provenance-checker redesign, protected-engine changes, model-manifest changes, unrelated LTX stories, or cleanup of old evidence: consume existing contracts and file unrelated findings separately.

## DIFF BUDGET

- About 5 files and under 550 authored/evidence LOC, including the byte-exact 6,108-byte audit JSON and focused tests.
- Expected surfaces: `scripts/run_ltx_final_operations.py`, `tests/test_ltx_final_operations_runner.py`, one durable audit JSON under the LTX terminalization evidence root, and narrowly related planner/runner test fixtures if required.
- Gross overrun is a PM investigation trigger, not an automatic rejection.

## Boundary Map

PRODUCES:

- `scripts/run_ltx_final_operations.py -> build_stage_inventory(repository_root: Path, staged_root: Path) -> dict[str, Any]`
  spec: derive the explicit Wangp repository identity and recursively hash every regular staged runner file; reject a non-Wangp root, dirty status, git failure, symlink/non-regular path, duplicate/unsafe path, missing file, or unreadable bytes with a stable typed `FinalOperationError`.
- `scripts/run_ltx_final_operations.py -> validate_stage_inventory(inventory: Mapping[str, Any], repository_root: Path, staged_root: Path) -> None`
  spec: re-run the same identity/file derivation and require an exact match to schema, commit, verbatim status, clean/dirty booleans, file count/order, sizes, and SHA-256 values; return `None` only when every fact is proven.
- `scripts/run_ltx_final_operations.py -> stage_settings(operation: Mapping[str, Any], template_root: Path) -> dict[str, Any]`
  event: unchanged public behavior for exact template staging, now protected by a complete stage-inventory validation before it can participate in execution.
- `scripts/run_ltx_final_operations.py -> run_batch(plan: Mapping[str, Any], authorization: Mapping[str, Any], template_root: Path, queue_db: Path, *, executor: Callable[[Sequence[str], str, int, str], int] | None = None, runtime_state: Mapping[str, Any] | None = None) -> dict[str, Any]`
  event: validate complete Wangp identity/file hashes before queue construction or any operation staging/execution; an absent or invalid inventory must stop as `EXECUTION_REPOSITORY_IDENTITY_UNPROVEN` or a more specific stable stage-inventory code.
- `datasets/runs/maestro-parity/ltx-dependency-terminalization/WD-b7ek-identity-audit.json -> immutable audit evidence`
  bytes: exactly 6,108 bytes, SHA-256 `5a50d08edb75cdb733a3704b55333acf4318f549ae7a5a13ecfa4d91fb0d52f7`; copy the verbatim audit, never regenerate or normalize it.
- `tests/test_ltx_final_operations_runner.py -> real local stage-identity integration tests`
  spec: exercise real temporary Git/Wangp-shaped repositories and actual staged files; cover clean success, dirty rejection, missing file, hash drift, and Wan2GP identity substitution without host contact or mocks of filesystem/git/hash behavior.

CONSUMES:

- `WD-28ac: datasets/runs/maestro-parity/ltx-dependency-terminalization/final-cell-retry3-20261008/stage-inventory.json -> preserved defective inventory`
  source: read-only context with `root=/tmp/ltx-final-cell-retry3/repository`, `file_count=13`, and the exact 13 listed paths; preserve it unchanged.
- `(existing): services/director/run_ledger.py -> repository_identity(repo_root: Optional[os.PathLike[str] | str] = None) -> dict`
  source: exact current signature. Its returned Wangp identity fields are `repo_root`, `commit_sha`, `clean_tree`, `dirty_tree`, `status_sha256`, `tracked_diff_sha256`, `untracked_content_sha256`, `changed_path_count`, and `untracked_path_count`. It raises `RepositoryIdentityError` on an unprovable root/HEAD; translate that into the final-operation typed boundary rather than bypassing it. Add verbatim `status_porcelain_v1` at the LTX stage-inventory layer unless an exact existing source already supplies it.
- `(existing): scripts/run_ltx_final_operations.py -> FinalOperationError(code: str, observed: str, remediation: str) -> None`
  source: constructor fields are `code`, `observed`, and `remediation`; preserve this shape.
- `(existing): scripts/run_ltx_final_operations.py -> stage_settings(operation: Mapping[str, Any], template_root: Path) -> dict[str, Any]`
  source: current exact template hash/copy behavior; do not weaken `NATIVE_TEMPLATE_ABSENT` or `NATIVE_TEMPLATE_HASH_MISMATCH`.
- `(existing): scripts/run_ltx_final_operations.py -> run_batch(plan: Mapping[str, Any], authorization: Mapping[str, Any], template_root: Path, queue_db: Path, *, executor: Callable[[Sequence[str], str, int, str], int] | None = None, runtime_state: Mapping[str, Any] | None = None) -> dict[str, Any]`
  source: current authorized batch gate; add the identity gate ahead of queue construction without making host execution reachable in this story.
- `(existing): tests/test_ltx_final_operations_runner.py -> test_final_runner_dry_run_and_host_guard(tmp_path: Path) -> None`
  source: preserve host-guard behavior; extend the file with the new real local identity tests.

## Story Acceptance Criteria

1. [State] The verbatim audit is preserved at `datasets/runs/maestro-parity/ltx-dependency-terminalization/WD-b7ek-identity-audit.json`, is exactly 6,108 bytes with SHA-256 `5a50d08edb75cdb733a3704b55333acf4318f549ae7a5a13ecfa4d91fb0d52f7`, and the preserved retry3 evidence directory remains byte-for-byte unchanged.
2. [State] `build_stage_inventory(repository_root: Path, staged_root: Path) -> dict[str, Any]` records a versioned Wangp repository identity containing the absolute root, lowercase 40-character commit SHA, verbatim `git status --porcelain=v1` output, mutually consistent clean/dirty booleans, and status SHA-256, plus ordered POSIX path, exact byte size, and lowercase SHA-256 for every regular staged runner file.
3. [Unwanted] A non-Wangp repository root, failed Git query, or nonempty/dirty Wangp status is rejected with a stable typed `FinalOperationError`; no dirty-run override is added in this story.
4. [State] `validate_stage_inventory(inventory: Mapping[str, Any], repository_root: Path, staged_root: Path) -> None` accepts the complete clean inventory and rejects absent/malformed repository identity, Wan2GP commit substitution, status disagreement, extra/missing/symlinked/non-regular files, unsafe/duplicate paths, size drift, and SHA-256 drift with distinct stable typed diagnostics.
5. [State] The final-operation execution path validates the inventory before queue construction or operation staging; missing/unproven identity cannot reach `stage_settings`, queue admission, native execution, or a success result, and the unproven-identity boundary remains `EXECUTION_REPOSITORY_IDENTITY_UNPROVEN`.
6. [State] Real local tests cover clean success with the retry3 13-path fixture shape and all three required negative paths: dirty Wangp status, missing staged file, and one-file SHA-256 drift; they also prove a Wan2GP `source_commit` is not accepted as Wangp identity.
7. [Unwanted] No host/SSH/QC contact, native render/retry, queue admission, model/body/network request, package install, retry3 rewrite, docs/index change, or matrix-cell promotion occurs.
8. [State] Focused tests, the full local suite, `pvg lint --backlog` with 0 errors, and whitespace checks pass; recorded output includes exact commands, JUnit counters, audit hash, and proof that all negative paths fail closed.

## Testing Requirements

- Real integration tests are mandatory. Use real temporary Git repositories, real files, real `git status`/`rev-parse` behavior, and real SHA-256 derivation. Do not mock Git, the filesystem, hashing, or `FinalOperationError`.
- Success test: a clean Wangp-shaped repository clone plus a staged root containing the exact retry3 13 relative paths yields `file_count=13`, exact commit/status facts, sorted paths, exact sizes/hashes, and no absolute/symlink path.
- Dirty test: mutate one tracked file in the temporary Wangp repository and require typed rejection before an inventory is accepted; the observed diagnostic must include the nonempty status evidence without authorizing execution.
- Missing test: remove one staged file and require typed rejection that names the missing relative path.
- Hash-drift test: alter one staged file byte-for-byte without changing the recorded inventory and require typed rejection that names the path and observed/expected hashes.
- Wrong-repository test: supply `4c93b64a47b5b0a915f2abec2ce754be98227150` or `faea82d15bf10b3479c42c0ea430892aae975870` as the Wangp commit and require typed rejection; those values remain valid only as Wan2GP facts.
- Execution-order test: an invalid inventory must fail before queue construction and before `stage_settings` can stage anything; no test may call a host or native executor.
- Commands to run locally: `uv run --frozen --extra dev pytest -q tests/test_ltx_final_operations_runner.py --junitxml=/tmp/ltx-stage-identity-focused.xml`; `timeout 1800 uv run --frozen --extra dev pytest -q --junitxml=/tmp/ltx-stage-identity-full.xml`; `pvg lint --backlog --json`; `git diff --check`.
- Record JUnit totals and failures/errors/skips. Missing local fixture files are failures; do not add skip-if-missing behavior.

## Delivery Requirements

- Deliver only this bug repair. Keep `WD-b7ek` deferred and do not package/promote its cell in this PR.
- Record the durable audit path, byte count, SHA-256, focused/full test commands and counters, negative-path codes, lint output, whitespace result, and exact changed-file list.
- Include an AC verification table mapping every AC to code and real test evidence.
- State explicitly that the preserved retry3 directory was not modified and no host, network, render, queue, download, or matrix action occurred.
- If complete Wangp identity cannot be derived or validated, stop at the typed boundary rather than substituting `582014de`, a Wan2GP commit, model metadata revision, or a reconstructed inventory.
- Update the authoritative `nd_contract` through the Paivot delivery command; do not hand-edit tracker files.

## MANDATORY SKILLS

- developer: implement exactly this bounded bug story and no matrix promotion.
- tool-systematic-debugging: preserve root-cause/fail-closed reasoning if a test or identity path fails.
- codebase-memory: verify current source/call context before edits; use direct source fallback whenever graph coverage is stale.
- pvg: shared tracker operations, delivery proof, and backlog lint; never manual status/label choreography.
- nd: maintain the authoritative append-only story contract.

## Audit Snapshot (verbatim bytes)

The bytes between the BEGIN and END marker lines are the exact 6,108-byte audit, including its final newline before the END marker. Copy the audit bytes from this story if `/tmp/WD-b7ek-identity-audit.json` is absent, then verify the required length and SHA-256; never normalize or regenerate it.

<<<BEGIN_WD_B7EK_IDENTITY_AUDIT>>>
{
  "boundary": "EXECUTION_REPOSITORY_IDENTITY_UNPROVEN",
  "basis": "Preserved stage-inventory lists 13 source paths but no file hashes or Wangp execution commit. Native/preflight commits identify Wan2GP, not the Wangp runner. authorization.metadata_correction.repository_revision identifies model metadata, not runner execution.",
  "source_hashes_verified": {
    "ltx23-upscale/operation-record.json": "68243778f4ac0c5a93ec58c995cf76903c06cecfec229736af2318da601be1bb",
    "ltx23-upscale/settings.json": "acf08e67b4827e7715956b107023ca57fcd6efe03c7280817d9df18d4770bddd",
    "ltx23-upscale/native.log": "7db387686e322ebbb1573e6b4d1e8ba361b4b5e468f442a1c390465937efc33b",
    "ltx23-upscale/native-output/wd_osfm_create_post.mp4": "2cfa857496e16b6f6f9e1e27c7bc0a6b1faf03e3a44a18b512e744bccbf4706f"
  },
  "authorization_canonical_sha256": "70f23626575fcc55e6310ecb6ac201039148584452ae52cfaf6f98684c61f1a3",
  "source_input_sha256": "d489d46173a3fe54e21577353ed98c76cf351610eafa0f44e279e8241a932957",
  "probes": {
    "source": {
      "dimensions": [
        448,
        832
      ],
      "duration": "1.375000",
      "audio": true
    },
    "output": {
      "dimensions": [
        896,
        1664
      ],
      "duration": "1.375000",
      "audio": true
    }
  },
  "preserved_file_count": 42,
  "preserved_manifest_sha256": "5b24952bae5ab5f8346b048378746d107282471c116e4a65dcd423a1082e61a0",
  "preserved_manifest": {
    "authorization-consumption.json": "6d913e0e1ed2e9a19a2ed5c4ec5811ef159718de7ee6910747b22a34b589e7db",
    "authorization.canonical.json": "70f23626575fcc55e6310ecb6ac201039148584452ae52cfaf6f98684c61f1a3",
    "authorization.json": "9473b73010712638106d42a9b30f692eaf71f2a85e0219bc650ecf4fe52aa51f",
    "batch.stderr": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "batch.stdout": "7fe76bd8c2c177dc8ff5e7383b73dfa4bde2d9e5744c38acb6051deb9ea8dab6",
    "boundary.md": "0e9907f8a7689579a8ed4f141960459294e0a5cdba6305d5ff47a600757b664b",
    "jobs.db": "e8a8e45f0af65f1ad677445916250605068aa53ab57c762fffec8d6404202fe3",
    "ltx23-outpaint/native-output/2026-10-08-15h04m04s_seed3706_LTX-2.3 outpaint boundary widen the rooftop scene with more skyline..mp4": "b075a604e6947e0ae2c93ba800e38963b7a8ed802787bba2f74291d354fff7e5",
    "ltx23-outpaint/native.log": "52241984988e030e284b819f9546393514b4b99e13968b7f4e397a32290a6c44",
    "ltx23-outpaint/operation-record.json": "9f0be3e4d605d1163461503fb510df930a80fbeed4458cad78c3d5a896966e0d",
    "ltx23-outpaint/settings.json": "8b3450245b99bed8d3d6af29e39efa8b72968218290987611ccf499cddf202b8",
    "ltx23-recast/native-output/2026-10-08-15h06m17s_seed3708_LTX-2.3 recast boundary using an alternate reference frame while preserving staging..mp4": "26995b579b20ff9959dfef3d690ac7eef73e350118a712678c3053f1435abfe7",
    "ltx23-recast/native.log": "f2b8e728c6b3dc2fdf5536073f41402e01fe85d73d536eb46dc258bc37b3cee3",
    "ltx23-recast/operation-record.json": "8137596ce4d553280eefb63986dcf2a10351f9b4fa92185075206d038ef79399",
    "ltx23-recast/settings.json": "1d07daa89b7e81b319e4fc4b011023ea1490d89d1c9d45399e04141099cbdd97",
    "ltx23-upscale/native-output/wd_osfm_create_post.mp4": "2cfa857496e16b6f6f9e1e27c7bc0a6b1faf03e3a44a18b512e744bccbf4706f",
    "ltx23-upscale/native.log": "7db387686e322ebbb1573e6b4d1e8ba361b4b5e468f442a1c390465937efc33b",
    "ltx23-upscale/operation-record.json": "68243778f4ac0c5a93ec58c995cf76903c06cecfec229736af2318da601be1bb",
    "ltx23-upscale/settings.json": "acf08e67b4827e7715956b107023ca57fcd6efe03c7280817d9df18d4770bddd",
    "ltx25-outpaint/native-output/wd_m7xw_outpaint.mp4": "d83d8f6fdea18a494ca8e02ec9bb8561a762dabeb73e89a6918c5615e8d38162",
    "ltx25-outpaint/native.log": "3333409698c681563e7f4340025102f25ccf53b05a9c16e91e614382b3265de4",
    "ltx25-outpaint/operation-record.json": "87b56118121344f376035015a1c727feef053b003961fa886bf750685c0ba757",
    "ltx25-outpaint/settings.json": "76183330b7898eb95ac94236083eaa3092fabbcb01696fd7a930d4113afb8e83",
    "ltx25-recast/native-output/wd_m7xw_recast.mp4": "4ec3c4baad5b367ea928d4ad3c25c41769207005e3b81fad2c32871387b26b78",
    "ltx25-recast/native.log": "27fe73c4e4b816fbbdc0fd2e165876a1eb96c1d4d556f70c6dc3019473d7d2c0",
    "ltx25-recast/operation-record.json": "685cdc1d6aa24d60d14208575cc83e5aefe0497e2686acd15ec012b38cb5c6d2",
    "ltx25-recast/settings.json": "40a1c1c4f5399fcd0052484f6ca562fc16c65c9ac166c41f6e4a8b3558a90f20",
    "ltx25-repaint/native-output/wd_m7xw_repaint.mp4": "a30ba72bef142d5efb32a79e4ee8d02d7afc437a333c90767a02f1f7fa2126d5",
    "ltx25-repaint/native.log": "b52503618c9f7ae6dd7465a3808e86f8cae3f7c303022777257cfca79e07b91e",
    "ltx25-repaint/operation-record.json": "d1f9a370d3a0c5b9d613ce0065a1907a155bea3df4867f49fed5dcb1f0644dbd",
    "ltx25-repaint/settings.json": "36d4ce9527d1d9f6188767eae8c34293113dba9e80e5c588897ec28cbc0fd928",
    "ltx25-upscale/native-output/wd_m7xw_create_post.mp4": "a82df16dcfa74f40c33fc4912acad98d0ff26c8d06ca7c0cfa9f72ee6cc980e9",
    "ltx25-upscale/native.log": "831afcebc1e242e0a21e893c544079c2ec500d52747233208fada23435a526bc",
    "ltx25-upscale/operation-record.json": "952808480cdf2535903a3f557ffdd9d65c44a54ffbe49f086f728c6e8228ba9b",
    "ltx25-upscale/settings.json": "31a093fbbab7367ab51e6a47a6d0fdbc749a612ec6ad5790a2f90c01f984667d",
    "plan.json": "4afa0c81033dad5d3b27e4be3721f3566018b42f136a0737446a62920d440d8d",
    "preflight.json": "c05e0e807fd7f247cf53019ccf582b7b31266b5b4dad525af41fc238bcab0523",
    "preflight.py": "9560e5c6ce39222002a129d12a37bbaaae0d669007ef9acf41d2171a702a3ba4",
    "queue-summary.json": "7c002fffe25465c958d0565e017aa5e22dfc186b3f07e7b2b91280a8dde3becf",
    "runtime-state.json": "8dc5e002cd09af84e8f546f27375e2c63752c6c0b7ba25a4771f6562771aa5bd",
    "stage-inventory.json": "c9f8a771accbf913f43fd9bddda50417561edba965e57d68926effe52cb56197",
    "summary.json": "76861279233d2fcac5498cf970db9dba05472140301af53e55edaf8d28908827"
  },
  "worktree_git_status": "",
  "implementation_changes": false,
  "matrix_promoted": false,
  "host_network_render_actions": false
}
<<<END_WD_B7EK_IDENTITY_AUDIT>>>

## nd_contract
status: new

### evidence
- Created on 2026-10-08 from Wangp main `582014de1464424ad22e9bb7e85eea717409622f`, current source at that HEAD, read-only retry3 evidence, existing deferred WD-b7ek, and the embedded audit whose SHA-256 is `5a50d08edb75cdb733a3704b55333acf4318f549ae7a5a13ecfa4d91fb0d52f7`. No implementation, claim, host action, render, commit, or push was performed while creating this story.

### proof
- [ ] AC #1: Durable verbatim audit preserved without changing retry3 evidence.
- [ ] AC #2: Complete Wangp identity and per-file SHA-256 inventory generated.
- [ ] AC #3: Dirty/non-Wangp state rejected with no override.
- [ ] AC #4: Inventory validator rejects identity/path/size/hash drift.
- [ ] AC #5: Final-operation path gates before queue or staging.
- [ ] AC #6: Real success and dirty/missing/hash-drift tests pass.
- [ ] AC #7: No prohibited host/render/network/promotion action occurs.
- [ ] AC #8: Focused/full/lint/whitespace gates pass with recorded evidence.

## Acceptance Criteria

## Acceptance Criteria


## Design


## Notes
### CI/Test Results

- Focused: 38 tests, 0 failures, 0 errors, 0 skipped.
- Full local: 2341 tests, 0 failures, 0 errors, 1 skipped, 967.502s.
- GitHub exact-head CI: pending; PM acceptance must wait for success.

### AC Verification

| AC | Result | Evidence |
|---|---|---|
| 1 | PASS | Audit is 6,108 bytes, SHA-256 `5a50d08edb75cdb733a3704b55333acf4318f549ae7a5a13ecfa4d91fb0d52f7`; all 42 retry3 files byte-equal. |
| 2 | PASS | `build_stage_inventory` records Wangp commit/status and all staged file sizes/hashes. |
| 3 | PASS | Dirty/non-Wangp/query failures reject with typed errors; no override. |
| 4 | PASS | Validator rejects schema/root/status/path/size/hash/source drift. |
| 5 | PASS | Gate precedes runtime validation, queue construction, staging, and execution. |
| 6 | PASS | Real success, dirty, missing, hash-drift, and Wan2GP-substitution tests pass. |
| 7 | PASS | Changed-file/test scope proves no prohibited action; retry3 remained unchanged. |
| 8 | PASS locally / CI pending | Focused/full/verifier/lint/release/protected/diff gates pass; exact-head GitHub CI pending. |


## nd_contract
status: rejected

### evidence
- PM rejection applied via pvg story reject on 2026-10-08.

### proof
- [ ] Story requires another developer delivery before it can be accepted.


## nd_contract
status: delivered

### evidence
- PR head `7638cee29e2a2b2d868f096f8181ee2f440576d6`.
- Full local JUnit tests=2341 failures=0 errors=0 skipped=1.
- Independent review APPROVED.
- Exact-head CI pending.

### proof
- [x] AC #1: Audit preserved and historical evidence unchanged.
- [x] AC #2: Complete identity and per-file hashes generated.
- [x] AC #3: Dirty/non-Wangp rejection has no override.
- [x] AC #4: Drift validation fails closed.
- [x] AC #5: Execution-order gate precedes queue/staging.
- [x] AC #6: Real success and negative tests pass.
- [x] AC #7: No prohibited action occurred.
- [x] AC #8: Local gates pass; CI pending and acceptance waits.

## Implementation Evidence

Summary: WD-nkdv now makes future LTX execution evidence prove the exact clean Wangp runner repository and every staged runner byte before runtime validation, queue construction, settings staging, or native execution. This is a future-evidence producer repair only; it does not promote the existing retry3 output or authorize host execution.

Commit SHA: 7638cee29e2a2b2d868f096f8181ee2f440576d6
PR: https://github.com/jmanhype/wangp-dspy/pull/234

Changed files:
- `scripts/run_ltx_final_operations.py`
- `tests/test_ltx_final_operations_runner.py`
- `tests/test_ltx_native_runtime_integration.py`
- `datasets/runs/maestro-parity/ltx-dependency-terminalization/WD-b7ek-identity-audit.json`

Implementation boundaries:
- Versioned stage inventory records clean Wangp repository root, commit, verbatim porcelain status, clean/dirty agreement, status hash, and ordered path/size/SHA-256 for all staged files.
- Staged bytes must match tracked HEAD bytes.
- Wan2GP commit substitution is rejected as `STAGE_INVENTORY_REPOSITORY_MISMATCH`.
- Dirty repository, missing/extra file, unsafe/non-regular path, size drift, hash drift, and unversioned/source mismatch all fail closed with stable typed codes.
- Missing inventory/runner repository fails as `EXECUTION_REPOSITORY_IDENTITY_UNPROVEN` before queue construction or staging.
- No dirty-run override exists.
- Historical retry3 evidence remained byte-for-byte unchanged; all 42 files were independently compared to main.
- No host/SSH/QC contact, native render/retry, queue admission, network/model/package request, install, protected-file change, docs/index change, or matrix promotion occurred.

Durable audit:
- Path: `datasets/runs/maestro-parity/ltx-dependency-terminalization/WD-b7ek-identity-audit.json`
- Size: 6,108 bytes
- SHA-256: `5a50d08edb75cdb733a3704b55333acf4318f549ae7a5a13ecfa4d91fb0d52f7`

## CI/Test Results

- Focused runner/native-runtime tests: 38 tests, 0 failures, 0 errors, 0 skipped.
- Full local suite at exact PR head: 2341 tests, 0 failures, 0 errors, 1 skipped, 967.502 seconds.
- `pvg verify scripts/run_ltx_final_operations.py tests/test_ltx_final_operations_runner.py tests/test_ltx_native_runtime_integration.py --format=text --include-tests`: PASSED, 0 issues.
- `pvg lint --backlog`: PASSED, 0 errors, 2 non-blocking story-format review findings.
- `wgp release verify`: release=ready, tag_created=false.
- Protected-file parity versus `origin/main`: PASS (empty diff).
- `git diff --check`: PASS.
- Independent adversarial review: `REVIEW_RESULT: APPROVED`.
- Exact-head GitHub CI: IN PROGRESS at the time of this delivery block; PM acceptance must wait for success.

Commands run:
- `/Users/Shared/HermesWorkspace/wangp-dspy/.venv/bin/python -m pytest -q tests/test_ltx_final_operations_runner.py tests/test_ltx_native_runtime_integration.py --junitxml=/tmp/WD-nkdv-independent.xml`
- `uv run --offline --frozen --extra dev pytest -q --junitxml=/tmp/WD-nkdv-full-local.xml`
- `pvg verify scripts/run_ltx_final_operations.py tests/test_ltx_final_operations_runner.py tests/test_ltx_native_runtime_integration.py --format=text --include-tests`
- `pvg lint --backlog`
- `uv run --offline --frozen --extra dev wgp release verify`
- `git diff --exit-code origin/main -- services/jobs/queue.py services/director/renderers/policy.py services/director/wiring.py services/jobs/preflight.py scripts/run_film.py`
- `git diff --check`

## AC Verification

- [x] AC #1: Audit is exactly 6,108 bytes with the required SHA-256; all 42 historical retry3 files are byte-equal. Code/test: story PR; evidence: independent hash comparison.
- [x] AC #2: `build_stage_inventory` records complete clean Wangp identity plus ordered per-file size/hash rows. Code: `scripts/run_ltx_final_operations.py`; tests: focused runner suite.
- [x] AC #3: Dirty/non-Wangp/query failures reject with typed errors and no override. Code/tests: `STAGE_INVENTORY_DIRTY_REPOSITORY`, `STAGE_INVENTORY_REPOSITORY_INVALID/MISMATCH`, `EXECUTION_REPOSITORY_IDENTITY_UNPROVEN`.
- [x] AC #4: Validator rejects schema/root/status/path/size/hash/source drift. Code/tests: focused runner suite.
- [x] AC #5: Validation precedes runtime validation, queue construction, settings staging, and execution. Code/tests: execution-order tests.
- [x] AC #6: Real Git/filesystem/hash tests cover success, dirty, missing, hash drift, and Wan2GP substitution. Tests: 38 focused tests.
- [x] AC #7: No prohibited host/network/render/promotion action occurred. Evidence: changed-file list, test scope, clean preserved retry3 comparison.
- [x] AC #8: Focused/full/lint/verifier/release/protected/diff gates pass locally. CI remains pending and acceptance must wait.

## nd_contract
status: delivered

### evidence
- PR head: `7638cee29e2a2b2d868f096f8181ee2f440576d6`
- PR: https://github.com/jmanhype/wangp-dspy/pull/234
- Focused tests: 38/38 pass.
- Full local JUnit: tests=2341, failures=0, errors=0, skipped=1.
- Audit SHA-256: `5a50d08edb75cdb733a3704b55333acf4318f549ae7a5a13ecfa4d91fb0d52f7`.
- Independent review: APPROVED.
- Exact-head CI is not yet terminal; do not accept before success.

### proof
- [x] AC #1: Durable exact audit preserved; retry3 evidence unchanged.
- [x] AC #2: Complete Wangp identity and per-file hashes generated.
- [x] AC #3: Dirty/non-Wangp state rejected with no override.
- [x] AC #4: Identity/path/size/hash drift rejected.
- [x] AC #5: Identity gate precedes runtime, queue, staging, and execution.
- [x] AC #6: Real success and negative-path tests pass.
- [x] AC #7: No prohibited host/network/render/promotion action occurred.
- [x] AC #8: Local gates pass; exact-head CI pending.

## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-10-08.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## History
- 2026-10-08T22:03:15Z dep_added: blocks WD-b7ek
- 2026-10-08T22:03:15Z dep_added: blocks WD-fay0
- 2026-10-08T22:03:56Z status: open -> in_progress
- 2026-10-08T22:03:56Z auto-follows: linked to predecessor WD-5d19
- 2026-10-08T22:03:56Z claimed by dev-WD-nkdv
- 2026-10-08T22:58:40Z status: in_progress -> in_progress
- 2026-10-08T22:58:40Z auto-follows: linked to predecessor WD-28ac
- 2026-10-08T23:04:52Z status: in_progress -> open
- 2026-10-08T23:04:52Z released by speed

## Links
- Parent: [[WD-3nod]]
- Blocks: [[WD-b7ek]], [[WD-fay0]]
- Follows: [[WD-5d19]], [[WD-28ac]]

## Comments

### 2026-10-08T23:04:53Z speed
## PM Decision
REJECTED [2026-10-08]: Technical evidence is otherwise complete, but the delivery notes omit the mandatory Retro-consumable LEARNINGS section.

EXPECTED: pm_acceptor requires every delivered story to carry a LEARNINGS section in addition to commands, counters, commit SHA, coverage/test evidence, and the AC verification mapping.
DELIVERED: WD-nkdv records the exact PR head, focused/full local gates, audit hash, AC mapping, and independent review; live PR #234 remains at 7638cee29e2a2b2d868f096f8181ee2f440576d6 and exact-head CI run 37854653689 is now successful. A shared-vault `pvg nd show WD-nkdv` search finds no LEARNINGS section.
GAP: The delivery is process-incomplete for Retro harvesting; this is a tracker-evidence gap, not a finding against the implementation.
FIX: Without changing code, PR, protected files, or retry3 evidence, append a concise real LEARNINGS section describing reusable insights from this repair, record exact-head CI run 37854653689 as successful, and redeliver WD-nkdv at the unchanged PR head.

## nd_contract
status: rejected

### evidence
- Live PR #234 head verified at 7638cee29e2a2b2d868f096f8181ee2f440576d6.
- GitHub CI run 37854653689 verified completed/success at that exact head.
- Static PM checks passed: 4-file/435-insertion scope, no stub markers, whitespace clean, protected-file and retry3 parity clean, audit 6108 bytes with SHA-256 5a50d08edb75cdb733a3704b55333acf4318f549ae7a5a13ecfa4d91fb0d52f7.
- Delivery proof preflight passed 9/9, but the authoritative notes contain no LEARNINGS section.

### proof
- [ ] Delivery completeness: Retro-consumable LEARNINGS section must be added and the story redelivered.
