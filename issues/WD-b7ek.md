---
id: WD-b7ek
title: "Promote final LTX-2.3 Upscale evidence"
status: open
priority: 1
type: task
labels: [capability, video, evidence, integration, qc]
parent: WD-3nod
created_at: 2026-10-08T21:30:42Z
created_by: speed
updated_at: 2026-10-08T21:30:42Z
content_hash: "sha256:979188ce9e390d41d7665882203025e1b707f975d3998cd254a337d5193294e6"
---

## Description
## Context (Embedded)

- Brownfield base is merged main `582014de1464424ad22e9bb7e85eea717409622f` (PR #232). PR #232 only preserves retry3 evidence; it does not promote a capability cell.
- Read-only source run: `datasets/runs/maestro-parity/ltx-dependency-terminalization/final-cell-retry3-20261008/`.
- The only promotable cell is `docs/video-capabilities.md`, row `ltx/2.3`, cell `Upscale`. It is currently `dependency_blocked`; the other six retry3 operations already have separately accepted Gate 22 evidence and must not be repackaged here.
- The retry3 batch contains seven native operations in `rendered_pending_qc`, seven queue jobs with zero failures, and a consumed one-shot authorization whose canonical SHA-256 is `70f23626575fcc55e6310ecb6ac201039148584452ae52cfaf6f98684c61f1a3`. Independent review approved preservation only, not QC, promotion, story acceptance, or merge.
- Exact preserved `ltx23-upscale` bytes:
  - `operation-record.json`: `68243778f4ac0c5a93ec58c995cf76903c06cecfec229736af2318da601be1bb`
  - `settings.json`: `acf08e67b4827e7715956b107023ca57fcd6efe03c7280817d9df18d4770bddd`
  - `native.log`: `7db387686e322ebbb1573e6b4d1e8ba361b4b5e468f442a1c390465937efc33b`
  - `native-output/wd_osfm_create_post.mp4`: `2cfa857496e16b6f6f9e1e27c7bc0a6b1faf03e3a44a18b512e744bccbf4706f`, 3,729,463 bytes
- Exact local source input: `datasets/runs/maestro-parity/WD-osfm/outputs/create/wd_osfm_create.mp4`, SHA-256 `d489d46173a3fe54e21577353ed98c76cf351610eafa0f44e279e8241a932957`, 984,165 bytes. Preserved probes establish `448x832` input and `896x1664` output, both 1.375 s with audio.
- Current canonical index census is 95 `host_run_verified`, 1 `dependency_blocked`, 110 `terminal_unsupported_or_fail_closed`, and 2 `not_applicable` over 208 matrix cells. After this story it must be exactly 96, 0, 110, and 2.
- Provenance warning: `582014de` is the evidence-preservation merge commit, not automatically the Wangp commit that executed retry3. The bundle must derive and record the exact execution/packaging source identity from preserved evidence; if that identity cannot be proven, fail closed rather than substituting `582014de`.

## USER INTENT

The operator wants the final preserved LTX-2.3 Upscale render to receive one honest, checker-valid, locally reviewed evidence bundle and matrix promotion, without another host action and without weakening any boundary. A reviewer must be able to run the canonical checker and current index validator and see that every LTX matrix cell is terminal.

## OUT OF SCOPE

- Any render, native retry, queue admission, SSH/host-3090 contact, health/QC-service contact, network request, model download, or package download: retry3 is consumed and this story is offline.
- Packaging or promoting the other six retry3 operations or changing any matrix cell other than `ltx/2.3 / Upscale`: those cells already have accepted Gate 22 evidence; this story owns exactly one transition.
- Reinterpreting the PR #232 preservation review as QC, matrix promotion, PM acceptance, or merge approval: a new mechanical media/contact-sheet review is required.
- Changing canonical checker semantics, warning ownership, thresholds, protected engine files, model manifests, WD-bw0h, or the first-run boundary: consume the existing contracts and leave unrelated boundaries unchanged.
- Any second evidence standard or direct matrix edit without a passing canonical bundle.

## DIFF BUDGET

- About 8 files and under 700 authored/evidence LOC, excluding copied immutable media/record bytes and generated ffprobe/contact-sheet artifacts.
- Expected surfaces: the WD-28ac builder, this story's one canonical bundle, `docs/video-capabilities.md`, the WD-fay0 index JSON/Markdown/validator, and real builder/index tests.

## Boundary Map

PRODUCES:
- scripts/build_wd28ac_parity_bundles.py -> build_retry3_ltx23_upscale(repo_root: Path) -> dict[str, Any]
  spec: offline fail-closed builder verifies every preserved hash, copies only the named source/input bytes into `datasets/runs/maestro-parity/WD-b7ek/`, derives model/reference provenance, creates mechanical media review artifacts, writes one `wangp-dspy.maestro-parity-evidence/v1` record, and invokes the canonical checker before returning a summary.
- scripts/build_wd28ac_parity_bundles.py -> build_all(repo_root: Path, evidence_root: Path | None = None) -> dict[str, Any]
  spec: preserve deterministic Gate 22 six-bundle behavior while adding an explicit retry3 final-cell mode; do not silently reinterpret `TERMINAL_EXCLUDED_OPERATION`.
- datasets/runs/maestro-parity/WD-b7ek/ -> canonical `wangp-dspy.maestro-parity-evidence/v1` bundle
  event: contains exactly one promoted operation and regular in-bundle files for `evidence.json`, copied `operation-record.json`, `settings.json`, `native.log`, source input, output media, ffprobe, visual review, and reviewer verdict; no symlinks or absolute paths.
- docs/video-capabilities.md -> exact `ltx/2.3` `Upscale` transition
  event: only this cell changes from `dependency_blocked` to `host_run_verified` with a relative link to `datasets/runs/maestro-parity/WD-b7ek/evidence.json`; the stale narrative claim that every row is `planned` is removed without changing another cell.
- datasets/runs/maestro-parity/WD-fay0/evidence-index.json -> current `wangp-dspy.maestro-parity-current-index/v1` inventory
  schema: 208 rows; totals exactly 96 `host_run_verified`, 0 `dependency_blocked`, 110 `terminal_unsupported_or_fail_closed`, 2 `not_applicable`; target row points to the new evidence; no LTX dependency boundary remains.
- datasets/runs/maestro-parity/WD-fay0/evidence-index.md -> rendered index exactly derived from the JSON inventory
  event: no prose claim that the target cell remains dependency-blocked.
- datasets/runs/maestro-parity/WD-fay0/validate_index.py -> validate_index(index_path: Path = BUNDLE / "evidence-index.json", repo_root: Path = REPO) -> dict[str, object]
  spec: pins the 96/0/110/2 census, new matrix identity, 45-file evidence manifest, and zero remaining LTX dependency cells, and fails closed on target-row, census, manifest, or non-target drift.
- tests/test_wd28ac_parity_bundle_builder.py and tests/test_current_parity_index.py -> real local integration and drift tests
  spec: exercise the actual builder, local media, ffmpeg/ffprobe, canonical checker, index, and validator with no mocks; prove negative paths fail closed.

CONSUMES:
- WD-28ac: datasets/runs/maestro-parity/ltx-dependency-terminalization/final-cell-retry3-20261008/ltx23-upscale -> operation-record.json, settings.json, native.log, and native-output/wd_osfm_create_post.mp4
  source: require the four exact SHA-256 values above plus `operation_id == "ltx23-upscale"`, `admission_state == "admitted"`, native returncode 0, `status == "rendered_pending_qc"`, output size/hash match, settings destination hash match, queue id/job id/retry id, and argv; never mutate this directory.
- WD-28ac: datasets/runs/maestro-parity/ltx-dependency-terminalization/final-cell-retry3-20261008 -> summary.json, authorization.json, authorization.canonical.json, authorization-consumption.json, preflight.json, runtime-state.json, and stage-inventory.json
  source: derive consumed authorization digest `70f23626575fcc55e6310ecb6ac201039148584452ae52cfaf6f98684c61f1a3`, retry3 model identities/downloads, runtime identity, source-tree identities, and the exact execution/packaging commit; do not infer missing provenance.
- WD-osfm: datasets/runs/maestro-parity/WD-osfm/outputs/create/wd_osfm_create.mp4 -> spatial_upscale_source_video
  source: copy exact bytes and require SHA-256 `d489d46173a3fe54e21577353ed98c76cf351610eafa0f44e279e8241a932957`, 984,165 bytes, `448x832`, 1.375 s.
- WD-23rs: scripts/verify_maestro_parity.py -> verify_bundle(bundle: Path) -> VerificationReport
  source: `VerificationReport(bundle: Path, passed: bool, diagnostics: tuple[Diagnostic, ...], warnings: tuple[EvidenceWarning, ...] = ())`; the bundle is valid only when `passed is True`, diagnostics are empty, and any warnings are explicitly owned.
- WD-fay0: datasets/runs/maestro-parity/WD-fay0/validate_index.py -> parse_document_rows(repo_root: Path = REPO) -> list[dict[str, str]]
  source: current authority for matrix-row extraction; update its pinned constants rather than bypassing it.
- WD-fay0: datasets/runs/maestro-parity/WD-fay0/validate_index.py -> matrix_identity(rows: list[dict[str, str]]) -> str and evidence_manifest(rows: list[dict[str, str]], repo_root: Path = REPO) -> dict[str, str]
  source: recompute the new matrix identity and all real evidence-file hashes; the expected manifest count is 45.
- WD-fay0: datasets/runs/maestro-parity/WD-fay0/validate_index.py -> render_markdown(index: dict[str, Any]) -> str
  source: regenerate `evidence-index.md` from the updated JSON rather than editing stale prose independently.

## Story Acceptance Criteria

1. [State] Before building, the exact preserved operation record, settings, native log, output, retry3 authorization digest, source input, and dimensions are hash/field verified; the retry3 source directory remains byte-for-byte unchanged and no file there is replaced by a symlink.
2. [State] The builder creates exactly one canonical bundle at `datasets/runs/maestro-parity/WD-b7ek/` for `ltx23-upscale` from the named preserved bytes and local WD-osfm source input; copied bytes match their source hashes, model/reference provenance is derived from preserved native/authorization/preflight evidence, and queue evidence truthfully records native success plus historical `rendered_pending_qc`, followed by this story's local mechanical review.
3. [State] The bundle contains a real local ffprobe record and deterministic visual artifacts: source and output probes show `448x832 -> 896x1664` (exactly 2x width and height), duration/audio remain plausible, a first frame and `fps=6,scale=240:-1,tile=4x2` contact sheet are nonempty/nonblank, black/blank detection passes, and their SHA-256 values and reviewer links are recorded. No image model or network review is used.
4. [State] `python3 scripts/verify_maestro_parity.py datasets/runs/maestro-parity/WD-b7ek` exits 0 with `PASS`; the report has zero diagnostics and every warning is explicitly owned. A checker failure stops delivery and prevents the docs/index transition.
5. [State] `docs/video-capabilities.md` changes exactly the `ltx/2.3` `Upscale` cell from `dependency_blocked` to `host_run_verified`, linking `datasets/runs/maestro-parity/WD-b7ek/evidence.json`; all other 207 matrix rows/cells retain their baseline state/evidence identity from `582014de`, and the stale all-rows-planned narrative sentence is removed without making another capability claim.
6. [State] The updated index and validator report exactly 208 matrix rows with `host_run_verified=96`, `dependency_blocked=0`, `terminal_unsupported_or_fail_closed=110`, and `not_applicable=2`; the target row is the only transition, the manifest contains exactly 45 real hashed evidence files, the matrix identity is recomputed, and no remaining LTX dependency boundary contradicts the verified bundle.
7. [State] `tests/test_current_parity_index.py` and the WD-fay0 validator no longer pin 95/1; they fail closed on old census, any residual dependency-blocked LTX cell, wrong target link, wrong manifest count/hash, non-target row drift from `582014de`, and stale rendered prose.
8. [Unwanted] No render, retry, host contact, network/download, package install, queue admission, protected-engine/threshold change, other-cell promotion, or mutation of preserved retry3 evidence occurs.
9. [State] Focused real integration tests, the undeselected full suite, canonical checker, index validator, `pvg lint --backlog`, release verification with `release=ready` and `tag_created=false`, protected-file parity from `582014de`, `git diff --check`, and exact-head CI pass.

## Testing Requirements

- Real integration tests are mandatory with no mocks for file hashing, ffmpeg/ffprobe, visual derivation, builder behavior, canonical checker, index parsing, or validator behavior.
- Builder success-path test must run against the real preserved source/input bytes and assert exact hashes, one output, 2x dimensions, bundle-relative regular files, provenance coverage, queue truth, visual hashes, and checker PASS.
- Negative tests must use real mutated temporary copies and prove typed/fail-closed behavior for: any source-hash mismatch, settings drift, non-success/native-log drift, output tampering, wrong operation id, missing/blank visual artifact, unexpected repository identity, attempting any other operation, target link drift, old 95/1 census, nonzero dependency-blocked count, wrong 96/0/110/2 total, wrong 45-file manifest, and any non-target row change from `582014de`.
- Commands to run: `uv run --frozen --extra dev pytest -q tests/test_wd28ac_parity_bundle_builder.py tests/test_current_parity_index.py --junitxml=/tmp/WD-b7ek-focused.xml`; `python3 scripts/verify_maestro_parity.py datasets/runs/maestro-parity/WD-b7ek`; `python3 datasets/runs/maestro-parity/WD-fay0/validate_index.py`; `timeout 1800 uv run --frozen --extra dev pytest -q --junitxml=/tmp/WD-b7ek-full.xml`; `pvg lint --backlog`; `uv run --frozen --extra dev wgp release verify`; `git diff --check`; plus exact-head CI.
- Parse and record JUnit counters; do not skip tests when local media is absent—absence is a failure.

## Delivery Requirements

- Deliver one separate story PR; do not mix this promotion with WD-bw0h, another finding, or a checker-semantics change.
- Record the builder summary, bundle identity/path and file count/size, every copied/source SHA-256, source and output ffprobe dimensions, visual hashes/blackdetect result, checker stdout/exit, validator JSON, exact census, matrix identity, manifest count, focused/full JUnit counters, lint/release/diff/protected-parity results, PR head, and exact-head CI run.
- Include an AC verification table and explicit statements that the retry3 source directory was not modified and no host/network/render action occurred.
- If repository execution identity, model provenance, source bytes, media review, checker, or index validation cannot be proven, stop with the typed boundary and leave the matrix cell unpromoted.

## MANDATORY SKILLS

- pvg: story workflow, worktree/claim discipline, delivery proof, and gates.
- tool-systematic-debugging: required if any builder, checker, validator, or media gate fails; diagnose from exact bytes/logs before changing code.

## nd_contract
status: new

### evidence
- Created on 2026-10-08 from merged main `582014de1464424ad22e9bb7e85eea717409622f`, preserved retry3 bytes, the local WD-osfm source input, current docs/index/tests, and the canonical checker/validator contracts. This story is not implemented, claimed, delivered, or accepted.

### proof
- [ ] AC #1: Preserved-source identity and immutability verified.
- [ ] AC #2: One canonical ltx23-upscale bundle built with truthful provenance.
- [ ] AC #3: Real ffprobe/visual/contact-sheet review passes.
- [ ] AC #4: Canonical checker exits 0/PASS with owned warnings.
- [ ] AC #5: Exactly the target docs cell transitions.
- [ ] AC #6: Index census is exactly 96/0/110/2 with 45 hashed files.
- [ ] AC #7: Validator and tests fail closed on old/drifted state.
- [ ] AC #8: No forbidden host/network/render/other-cell action occurs.
- [ ] AC #9: All focused, full, lint, release, parity, diff, and CI gates pass.

## Acceptance Criteria


## Design


## Notes


## History


## Links
- Parent: [[WD-3nod]]

## Comments
