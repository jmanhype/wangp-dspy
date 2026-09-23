---
id: WD-gc09
title: "Non-destructive multi-track editing surface for governed generation"
status: in_progress
priority: 2
type: feature
labels: [capability, capstone]
parent: WD-t741
created_at: 2026-09-22T20:24:45Z
created_by: speed
updated_at: 2026-09-23T13:46:31Z
content_hash: "sha256:208949a4b78073f5b22071c99adc3bad128fbfbb29d6b936faef7af9b92374ab"
was_blocked_by: [WD-6tox, WD-4d90, WD-soa4, WD-pcen, WD-6ml6, WD-fasw, WD-tkuz, WD-8ioj, WD-eq1i]
assignee: dev-WD-gc09
follows: [WD-6tox, WD-4d90, WD-soa4, WD-pcen, WD-6ml6, WD-fasw, WD-tkuz, WD-8ioj, WD-eq1i]
---

## Description

## USER INTENT
Observable outcome: a non-destructive multi-track editor can import governed artifacts, arrange video/audio/image/text tracks, revise edits without overwriting sources, and emit a deterministic assembly/render plan through the director and queue.

## Context (Embedded)
- The governed repository path is plan -> durable queue -> host render -> QC gates -> assembly -> provenance/recipe; `wgp` is the stable CLI and GPU execution is never implied by planning.
- This is a product surface over immutable source assets and governed jobs, not a second renderer or QC bypass.
- Non-destructive means edits are serialized decisions with source hashes; source files and accepted evidence remain unchanged.
- The editor consumes director output but must also permit manual arrangement and review checkpoints.

## OUT OF SCOPE
- In-place source editing, hidden generation, direct GPU dispatch, or assembly that bypasses existing QC/provenance.
- A proprietary project format without export/reconstruction evidence.

## DIFF BUDGET
Roughly 12 files, under 1,000 authored changed LOC, excluding generated media and GUI dependencies.

## Boundary Map
PRODUCES:
- wangp/editor_project.py -> typed multi-track project model with clips, transitions, text, audio, images, review marks, and source hashes
- services/editor/project_store.py -> portable save/load, migration checks, source verification, and non-destructive history
- services/editor/assembly_exporter.py -> deterministic project-to-assembly/director request translation
- editor/ -> minimal maintainable UI or equivalent CLI/TUI surface that exercises the same project service; a browser/GUI choice must be documented and testable without GPU
- wangp/editor_cli.py -> headless project validation/export commands so UI is never the only correctness path
- docs/editor.md -> track model, non-destructive guarantees, export semantics, and review/queue path
- tests/test_editor_project.py -> real-process project/export coverage; no mocks
- datasets/runs/maestro-parity/WD-gc09/ -> authorized rendered export bundle

CONSUMES:
- services/director/composition.py -> accepted director request/review model
  spec: accepted director request/review model
- predict/assembler.py -> existing assembly path
  spec: existing assembly path
- services/jobs/queue.py -> durable queue record and attempt transitions
  spec: durable queue record and attempt transitions
- services/jobs/preflight.py -> typed missing source/project failures
  spec: typed missing source/project failures
- predict/v3_recipe.py -> immutable reconstruction/provenance contract
  spec: immutable reconstruction/provenance contract
- wangp/diagnostics.py -> actionable headless/UI diagnostics
  spec: actionable headless/UI diagnostics
- wangp/cli.py -> stable verb registration and exit-code contract
  spec: stable verb registration and exit-code contract


## Required Outcomes
### no-GPU verifiable now
- Real tests create/save/reopen a multi-track project in a clean temporary directory, import committed media, move/trim/reorder clips and text, and prove every source hash and prior decision remains recoverable.
- Export emits the same deterministic director/assembly JSON across repeated export and after project round-trip; missing/mutated source files fail typed.
- Undo/redo or equivalent history records a real edit sequence and never rewrites imported source bytes.
- The headless validation/export verb runs in CI without a display, GPU, network, or generation claim.

### requires an authorized host render
- One separately authorized export/render through the governed director/queue path produces a real finished artifact from a non-destructive project, with all mandatory gates and assembly provenance.
- The run bundle includes project hash, source hashes, export request, queue attempts, command, model provenance, output hashes, and QC/review evidence.

## Testing Requirements
- `uv run --frozen --extra dev pytest tests/test_editor_project.py -q` plus the UI/headless test selected by the implementation; real filesystem/CLI/subprocess only, no mocks.
- Use committed media and prove source bytes are unchanged after edits and exports.
- Authorized export evidence is reviewed through ffprobe, hashes, queue records, and recipe reconstruction; planning alone cannot be called rendering.

## MANDATORY SKILLS
- pvg

## Delivery Requirements
- Developer must use `pvg story deliver`, paste real command output, and provide an AC table plus hashes for every produced artifact and read-only input.
- A GPU-dependent claim may be made only from a recorded run bundle with command, repository commit, model/asset provenance, queue record, exit status, output hashes, QC/gate evidence, and operator authorization for that run. A plan, prompt, unit test, or intention is not generation evidence.
- No story may silently download a model, contact a host, use a paid provider, or claim a capability the matrix marks unverified.

## nd_contract
status: new

### evidence
- Created 2026-09-22 under epic WD-t741 from the Maestro v2.3.0 capability inventory.

### proof
- [ ] Pending implementation and independent PM acceptance.


## Acceptance Criteria


## Design


## Notes
## Implementation Evidence
Summary: Delivered the no-GPU editor slice: typed video/audio/image/text tracks and clips with in/out points, transitions, review marks, hash-pinned portable sources; atomic save/load, schema checks, typed source verification, and snapshot history with undo/redo; deterministic export through the real director compiler and MultiShotAssembler plus optional real JobQueue submission; `wgp editor validate|export`; README integration; and real-process no-mock tests. A GUI/browser surface is deliberately deferred (no GPU/display in this lane, headless CI, and the CLI exercises the same project service); this is documented in `docs/editor.md` and is not an omission. No render, GPU, SSH, model download, paid provider, or generated/edited-media claim was made. Renderer, queue, QC, AV, gate, and retry semantics were not weakened.

Commands run:
- `pvg nd show WD-gc09`
- `uv run --frozen --extra dev pytest tests/test_editor_project.py -q --junitxml=/tmp/wd-gc09-editor-final.xml` → exit 0; JUnit `tests=5 failures=0 errors=0 skipped=0`.
- `uv run --frozen --extra dev pytest tests/test_readme_quickstart.py -q --junitxml=/tmp/wd-gc09-readme-final.xml` → exit 0; JUnit `tests=5 failures=0 errors=0 skipped=0`.
- `uv run --frozen --extra dev pytest -q --junitxml=/tmp/wd-gc09-full-final.xml` → exit 0; JUnit `tests=1972 failures=0 errors=0 skipped=1`.
- Human + `--json` validation/export captures: `/tmp/wd-gc09-cli-evidence/{validate-human,validate-json,export-human,export-json}.{out,err}`; success exits 0.
- Typed exit-2 captures: `EDITOR_PROJECT_MISSING`, `EDITOR_PROJECT_SCHEMA_UNSUPPORTED`, `EDITOR_SOURCE_MISSING`, and `EDITOR_SOURCE_HASH_MISMATCH` in `/tmp/wd-gc09-cli-evidence/*-json.out`; every emitted `next_command` resolves to live `wgp editor validate|export`.
- Determinism/non-destruction proof: `cmp` succeeded for initial export, repeated exports, and export after project round-trip; export SHA-256 `ac07ab20b06258da00b7944463b08a2d00abfad030f477f743bfcf03ae1aa446`; original and project-copy source hashes remained equal for MP4/WAV/PNG, and an appended source mutation failed typed.
- Source hashes: MP4 `b53e5d37457f61db8c1bfa31d11d8d873139bf0aabddf97e0efa245de4d702a3`; WAV `f3d66cac4458d0d33870ff6dc97df75eff95d57b154180dd303be4f955c91857`; PNG `d552c768b4676592a08c561f889e26af9ade9eb54e7d5ce6d7bf8c289491edfd`.
- `uv build --out-dir <tmp>` → one wheel + one sdist; wheel SHA-256 `79362f88af9e41d119c842e5322aea968f5f837c56f16db5778e36fc31d84418`; sdist SHA-256 `4f636e5222d0ed8a8fc482bbfe752c29692117908a2da515f81dd163d440be99`.
- `gh pr create` → https://github.com/jmanhype/wangp-dspy/pull/174.
- Exact-head check-run poll for `841625de02446ae2d98e5a8024fae29c29e28702` → `test completed success`, https://github.com/jmanhype/wangp-dspy/actions/runs/35866970430/job/107200934088.

SHA: 841625de02446ae2d98e5a8024fae29c29e28702

### CI/Test Results
- Targeted editor: exit 0; parsed JUnit tests=5, failures=0, errors=0, skipped=0.
- README drift: exit 0; parsed JUnit tests=5, failures=0, errors=0, skipped=0.
- Full suite: exit 0; parsed JUnit tests=1972, failures=0, errors=0, skipped=1.
- Build: exit 0; exactly one wheel and one sdist produced in `/tmp/wd-gc09-final-artifacts`.
- GitHub check at exact PR head: `test` = completed/success.

### AC Verification
| AC | Result | Evidence |
| --- | --- | --- |
| Create/save/reopen a multi-track project in a clean temporary directory; import committed media; move/trim/reorder clips and text; recover all source hashes and prior decisions | PASS | `tests/test_editor_project.py::test_round_trip_history_edits_and_non_destruction`; targeted JUnit 5/0 |
| Deterministic director/assembly JSON across repeated export and after round-trip; missing/mutated sources fail typed | PASS | `test_deterministic_export_round_trip_and_real_queue_consumption`; `test_cli_success_and_every_typed_failure_has_live_next_command`; byte `cmp` and typed exit-2 captures |
| Undo/redo records a real edit sequence and never rewrites imported source bytes | PASS | `test_round_trip_history_edits_and_non_destruction`; original/copy SHA-256 equality after edits and undo/redo |
| Headless validation/export runs in CI without display, GPU, network, or generation claim | PASS | `test_cli_success_and_every_typed_failure_has_live_next_command`; full suite 1972/0/0/1 skipped; forbidden host-binary call log remained empty |
| Real governed export/render bundle with all mandatory gates and provenance | not verified - requires authorized host run | No authorized host run was requested or performed; no render or media claim made |

## nd_contract
status: delivered

### evidence
- Implementation and tests at SHA `841625de02446ae2d98e5a8024fae29c29e28702`; PR #174 exact-head CI `test` completed with success.
- Parsed JUnit results above; deterministic export, source-byte preservation, mutation failure, queue consumption, README drift, and full-suite outputs recorded.

### proof
- [x] Clean-temp create/save/reopen, committed-media import, move/trim/reorder, source hashes, and prior decisions remain recoverable.
- [x] Repeated and round-trip export are byte-identical; missing and mutated sources fail with typed exit-2 diagnostics.
- [x] Undo/redo covers a real edit sequence without rewriting imported source bytes.
- [x] Headless validation/export runs without display, GPU, network, generation, renderer admission, QC bypass, or media claim; GUI is explicitly deferred.

## History
- 2026-09-22T20:24:47Z dep_added: blocked_by WD-eq1i
- 2026-09-22T20:26:48Z dep_added: blocked_by WD-fasw
- 2026-09-22T20:26:48Z dep_added: blocked_by WD-8ioj
- 2026-09-22T20:26:49Z dep_added: blocked_by WD-4d90
- 2026-09-22T20:27:36Z dep_added: blocked_by WD-6tox
- 2026-09-22T20:27:37Z dep_added: blocked_by WD-pcen
- 2026-09-22T20:27:37Z dep_added: blocked_by WD-soa4
- 2026-09-22T20:27:37Z dep_added: blocked_by WD-6ml6
- 2026-09-22T20:27:37Z dep_added: blocked_by WD-tkuz
- 2026-09-22T22:50:11Z dep_removed: was_blocked_by WD-6tox
- 2026-09-23T01:35:54Z dep_removed: was_blocked_by WD-4d90
- 2026-09-23T01:38:43Z dep_removed: was_blocked_by WD-soa4
- 2026-09-23T04:22:27Z dep_removed: was_blocked_by WD-pcen
- 2026-09-23T06:49:08Z dep_removed: was_blocked_by WD-6ml6
- 2026-09-23T09:14:05Z dep_removed: was_blocked_by WD-fasw
- 2026-09-23T09:16:29Z dep_removed: was_blocked_by WD-tkuz
- 2026-09-23T11:26:58Z dep_removed: was_blocked_by WD-8ioj
- 2026-09-23T12:34:15Z dep_removed: was_blocked_by WD-eq1i
- 2026-09-23T12:35:58Z status: open -> in_progress
- 2026-09-23T12:35:58Z auto-follows: linked to predecessor WD-6tox
- 2026-09-23T12:35:58Z auto-follows: linked to predecessor WD-4d90
- 2026-09-23T12:35:58Z auto-follows: linked to predecessor WD-soa4
- 2026-09-23T12:35:58Z auto-follows: linked to predecessor WD-pcen
- 2026-09-23T12:35:58Z auto-follows: linked to predecessor WD-6ml6
- 2026-09-23T12:35:58Z auto-follows: linked to predecessor WD-fasw
- 2026-09-23T12:35:58Z auto-follows: linked to predecessor WD-tkuz
- 2026-09-23T12:35:58Z auto-follows: linked to predecessor WD-8ioj
- 2026-09-23T12:35:58Z auto-follows: linked to predecessor WD-eq1i
- 2026-09-23T12:35:58Z claimed by dev-WD-gc09

## Links
- Parent: [[WD-t741]]
- Was blocked by: [[WD-6tox]], [[WD-4d90]], [[WD-soa4]], [[WD-pcen]], [[WD-6ml6]], [[WD-fasw]], [[WD-tkuz]], [[WD-8ioj]], [[WD-eq1i]]
- Follows: [[WD-6tox]], [[WD-4d90]], [[WD-soa4]], [[WD-pcen]], [[WD-6ml6]], [[WD-fasw]], [[WD-tkuz]], [[WD-8ioj]], [[WD-eq1i]]

## Comments
