# WangP parity/release inventory — 2026-09-13

## Scope and evidence limits

- Repository audited read-only: `/Users/Shared/HermesWorkspace/wangp-dspy`.
- Snapshot at collection: branch `codex/golden-v3-lf003-repro`, HEAD
  `23dd219ff76b406f8d41d81ea4f66583f936d966`; 41 tracked files were modified
  and 68 paths were listed untracked. Later concurrent work added/changed
  material (notably finding #51 and the identity-test portability fix), so that
  initial count is a snapshot rather than the final worktree count.
- No GPU, SSH, commit, push, export, or source modification was performed by
  this inventory pass. Independent root validation results are reported as
  supplied and were not rerun here.
- Concurrent cleanup was in progress in runtime modules while this inventory
  was taken. Comparisons below identify overlap but intentionally do not revert
  or normalize anyone's edits.

## 1. Findings status ledger

Classification below distinguishes an explicitly implemented engineering fix
from operational acceptance/closure. It does not mark a finding closed merely
because narrative language says a fix landed.

| Finding | Actual document status | Classification |
|---|---|---|
| #32 premise/content coherence | `docs/findings/32-premise-content-coherence.md:3` says “Confirmed and guarded”; lines 61–88 describe the implemented plan/submit guard. Lines 90–96 still say the visual verdict ledger is **NEEDS REVIEW**. | Engineering fix closed; creative/visual review remains open. |
| #33 acceptance runner | Lines 3–4 say runner implemented, but “current bundle is blocked by Finding #35.” #35 itself was subsequently resolved in commit `490066c`. | Runner fix closed; the embedded blocker statement is historical/stale. |
| #34 live vision adapter | Lines 3–4 say adapter implemented while live credentials/premise roster remain required for a rerun; lines 17–27 describe both ModelScope and local adapters. | Code closed; live operational rerun requirement was open at that document time. |
| #35 bundle premise registration | Lines 3–4 say confirmed and resolved on data side in `490066c`; next stop is the credential gate. | Data-side fix closed. |
| #36 host asset map | Lines 3–4 say resolved for acceptance host by environment mapping; lines 12–14 require the explicit operator-supplied map rather than guessing. | Closed for that host, with an intentional external runtime prerequisite. |
| #37 ModelScope transport hang | Line 3 says confirmed/fixed with bounded transport seam; lines 13–20 describe the deadline and fail-closed behavior. | Engineering fix closed. |
| #38 style anchor coherence | Line 3 says implemented with acceptance bundle update; lines 12–17 describe SHA binding and temporary legacy compatibility. | Closed, with legacy-premise compatibility caveat. |
| #39 local Qwen contract | Lines 3–4 say confirmed/fixed; lines 21–31 describe response budget/grammar and strict parsing. | Engineering fix closed. |
| #40 remote curl tokenization | Lines 3–4 say confirmed/fixed by remote smoke; lines 14–18 specify the one-token header and regression. | Engineering fix closed. |
| #41 local-judge latency | Lines 3–4 only say confirmed; lines 14–19 propose GPU launch or a measured timeout. No closure/status line is present. | Open operational/deployment issue. |
| #42 GPU contention/lifecycle | Lines 3–4 say executor lifecycle seam fixed but “acceptance rerun pending”; lines 19–25 describe stop/start ordering and retain readiness smoke. | Hybrid: code fix landed, rerun/readiness validation open. |
| #43 prose truncation | Lines 3–4 say confirmed/fixed; lines 12–18 describe 1024 tokens, JSON grammar, and fail-closed validation. | Engineering fix closed. |
| #44 visual reseed retry | No `Status:` heading. Lines 18–27 explicitly say “Fix (landed)”; lines 29–34 describe regression coverage. | Engineering fix closed based on explicit landed language. |
| #45 cut-4 systematic continuity | Lines 5–10 record three-seed failure/dead-letter. Lines 28–35 say “Next PR (not applied here)” and require a fresh anchored render. No closure line exists. | Open/stale relative to later work; not closed in this file. |
| #46 vision evidence preservation | Lines 12–18 explicitly say “Fix (landed)”; lines 23–28 describe durable evidence regressions. | Engineering fix closed. |
| #47 spatial anchor hardening | Lines 19–27 explicitly say fix landed. Lines 28–32 require fresh verification and say “Reopen only after…” | Hybrid: code fix landed, fresh verification open. |
| #48 final-turn identity drift | Lines 5–10 record cut 6 failing all three seeds and no assembly. Lines 26–32 classify it as a model/conditioning seam. Lines 34–41 say “Next PR (not applied here).” No closure or implemented-fix section exists. | **Open in its own finding.** #50's later correction says the broader v3 dispatch/conditioning bug explains the earlier “latent ceiling” interpretation, but that does not retroactively close #48 without a #48 status update. |
| #50 v3 recipe parity | Original lines 42–49 say the minimal PR was “not applied here.” Follow-up lines 51–81 now records the recovered request/measured-output distinction, native dispatch/audio repair, exact local reproduction, hashes, and read-only canary pass. Lines 83–87 explicitly state exact reproduction is verified in the uncommitted local tree while source-only release validation and review remain distinct. | **Hybrid/open for release:** implementation and exact-pair evidence exist, but no commit/merge; review/source-only release validation remained outstanding at those lines. Root's later isolated suite result narrows the remaining release concern but does not itself create a commit. |
| #51 identity-test portability | `docs/findings/51-repository-identity-test-checkout-portability.md:3-7` marks it confirmed with test-only fix in progress. Lines 22–25 record the sole isolated-suite failure (literal Hermes checkout path). Lines 41–49 define the minimal test-only repair. Lines 51–56 limit validation scope. | Initially open/test-only. Root later reports the fix complete and both actual and isolated suites green; this report has not independently rerun that result. |

There is no `docs/findings/49-*.md` in the audited directory.

## 2. Pre-existing patch and current overlap

`/tmp/wangp-before-parity-fix/preexisting.patch` touches ten tracked files:

1. `host/wangp_adapter.py`
2. `predict/audio_prep.py`
3. `predict/continuation_lane.py`
4. `predict/render_profiles.py`
5. `qc/audio_critic/modelscope_vision_judge.py`
6. `qc/audio_critic/whisper_cli.py`
7. `scripts/run_jobs.py`
8. `services/chain/controller.py`
9. `services/director/run.py`
10. `tests/test_audio_prep.py`

All ten were already modified in the current worktree. Their baseline copies
are under `/tmp/wangp-before-parity-fix/`. Current byte-for-byte comparison:

- **Unchanged since the pre-existing snapshot (preserve exactly):**
  - `qc/audio_critic/whisper_cli.py`
  - `services/director/run.py`
  - `tests/test_audio_prep.py`
- **Changed since the snapshot:** the other seven files. These contain
  functional repair edits as well as later comment/docstring cleanup.
  Their semantics cannot be inferred from line counts.

**Orchestrator correction:** the initial draft's deletion-only comparison and
table were invalid and have been removed. Independent `git diff --no-index
--numstat` checks showed additions as well as deletions (for example, 46/38
in `host/wangp_adapter.py`). The inventory agent hit an inference 429 retry
limit before it could apply this review correction. The root preserved the
verified three-unchanged/seven-overlapping inventory, not the invalid counts.

The pre-existing patch therefore overlaps the release candidate directly; an
isolated export cannot omit it or replace these files with HEAD versions. Other
tracked modified runtime/test files outside that patch must also be exported as
the candidate's current tracked edits, not discarded as unrelated local noise.

## 3. Exact new source/test inventory

### Eleven repair-critical new files

These match the eleven explicitly selected new files used by root's isolated
candidate:

1. `host/ref2va_evidence.py`
2. `host/ref2va_recovery.py`
3. `predict/ref2va_settings.py`
4. `predict/v3_canary.py`
5. `predict/v3_recipe.py`
6. `scripts/run_v3_native_control.py`
7. `tests/test_completed_ref2va_recovery.py`
8. `tests/test_host_native_assembly.py`
9. `tests/test_ssh_probe_argv.py`
10. `tests/test_v3_canary.py`
11. `tests/test_v3_native_parity.py`

### Other currently untracked Python entry points

These were present in the worktree but were not part of the eleven-file
source-only validation set:

- `scripts/run_v2_control.py`
- `scripts/run_v3_pair.py`
- `scripts/run_v3_single.py`

They should remain separate/excluded from the minimal release export unless an
owner explicitly wants the experimental entry points.

### Modified tracked runtime modules relevant to parity

At minimum the candidate's current edits to these tracked runtime modules are
needed: `host/ref2va_runtime.py`, `host/render_host.py`,
`host/wangp_adapter.py`, `predict/audio_dataplane.py`,
`predict/audio_prep.py`, `predict/continuation_lane.py`,
`predict/render_profiles.py`, the five changed modules under
`qc/audio_critic/`, `scripts/run_acceptance.py`, `scripts/run_jobs.py`,
`services/chain/controller.py`, `services/director/run.py`,
`services/director/wiring.py`, and `services/jobs/executor.py`.
The corresponding modified test modules must also be taken as a set. This is an
inventory, not a claim that each change is individually minimal.

## 4. Native-control and canary dependency overlap

### `scripts/run_v3_native_control.py`

Direct runtime dependencies/imports include:

- `host.render_host.SshHost`
- `predict.continuation_lane.ContinuationExtras`
- `services.director.premises.Premise`
- `services.director.run.DirectorRun` / `DirectorRunPlan`
- `services.director.wiring.assemble_media`
- `services.director.run_records.append_dataset_run`
- `predict.v3_recipe.golden_prompt` / `V3_RECIPE`
- `services.jobs.queue.JobQueue`
- `scripts.run_jobs` (`_default_vision_judge` and `drain_once`)
- delayed use of `services.jobs.states`
- delayed verification through `predict.v3_canary.verify_v3_canary`

Important overlap with existing edits: `host/render_host.py`,
`host/wangp_adapter.py`, `host/ref2va_runtime.py`,
`predict/continuation_lane.py`, `predict/audio_dataplane.py`,
`predict/audio_prep.py`, `predict/render_profiles.py`,
`qc/audio_critic/*`, `scripts/run_jobs.py`,
`services/chain/controller.py`, `services/director/run.py`,
`services/director/wiring.py`, and `services/jobs/executor.py` are on the
plan/render/QC path. These need the reconciled current versions, not HEAD plus
only the new files.

Operational fixture references at
`scripts/run_v3_native_control.py:40-46` and `:59-79` are:

- `assets/acceptance/v3-control/grandma_frame2.png`
- `assets/acceptance/v3-control/soul_frame.png`
- `assets/acceptance/v3-control/grandma_frame.png`
- `assets/acceptance/v3-control/dgshort_g.wav`
- `assets/acceptance/v3-control/dgshort_s.wav`

The script can fetch these from `/home/straughter/...` when absent. They are
needed to execute the actual host control, but they are **not** needed by the
unit suite: `tests/test_v3_canary.py:120-127` monkeypatches `_host` and
`_ensure_assets`, while other native tests use `tmp_path` fixtures.

### `predict/v3_canary.py`

- Direct repo dependency: `predict.v3_recipe.V3_RECIPE`.
- External executable dependency: `ffprobe` (invoked at
  `predict/v3_canary.py:23-30`) for exact stream/frame/timing checks.
- Golden hashes are declared in `predict/v3_recipe.py:24-29` for cut 1, cut 2,
  pair, and chain seed; request resolution is `480x832` while measured output
  is documented as `704x576` at `predict/v3_recipe.py:4-5`.
- Unit tests do not require the real media: `tests/test_v3_canary.py:12-25`
  creates temporary bytes and derives test hashes; lines 45-49 avoid probing
  mismatches; lines 62-65 monkeypatch `_probe`; lines 105-150 monkeypatch host,
  queue, judge, drain, assembly, and asset pulling.

## 5. Source-only full-suite fixture inventory

Required source/test fixture:

- `datasets/runs/provenance/v3_pair_generator.py` is already **tracked** and is
  read by `tests/test_v3_native_parity.py:26-33` to compare recovered prompts
  verbatim. It must be included in any source export, but it is not an
  untracked local fixture.

No untracked media, queue database, or experimental entry point is required for
the complete test suite based on the new parity tests and root's independent
runs. Root reports that the isolated candidate omitted operator media, queue
DBs, and experimental scripts and encountered no missing local dependency.

External host tools:

- `tests/test_v3_native_parity.py:126-129` skips the real v3 audio-prep test
  when `ffmpeg` or `ffprobe` is absent.
- Root's final results indicate the configured validation environment had the
  required tooling except for the one recorded intentional skip.

Python dependencies should be supplied from tracked `pyproject.toml` and
`uv.lock`; the test/dev requirements include pytest/httpx and the project's
runtime dependency set. GPU extras are not needed by the source-only suite.

## 6. Independent validation status supplied by root

Root's first isolated source-only run collected 1,314 tests:

- 1,312 passed
- 1 failed: `tests/test_run_identity.py::test_repository_identity_resolves_repo_root_and_head`
- 1 skipped

Finding #51 records that the sole failure was the literal expected path
`/Users/Shared/HermesWorkspace/wangp-dspy`, while the isolated checkout correctly
resolved to `/private/tmp/wangp-parity-source-only-20260913-bJlI0Z`
(`docs/findings/51-repository-identity-test-checkout-portability.md:18-25`).

After the delegated test-only portability fix, root reports both the actual
repository and isolated candidate passed:

- **1,315 passed / 1 skipped**
- Evidence paths supplied by root:
  `/tmp/wangp-parity-root-verified-20260913.xml` and
  `/tmp/wangp-parity-isolated-verified-20260913.xml`.

This inventory agent did not rerun those suites and does not convert that test
result into a merged-release claim.

## 7. Remaining uncertainties / release cautions

1. Finding #48 has no closure line and should not be represented as closed;
   #50's later architecture diagnosis supersedes part of its interpretation but
   does not update #48's status section.
2. #50's exact reproduction is explicitly uncommitted at HEAD
   `23dd219ff76b406f8d41d81ea4f66583f936d966`; review/commit remains a separate
   release gate.
3. #45 and #47 retain open “next verification” language in their own files even
   if later parity work addressed the underlying recipe path.
4. #41 remains an operations/deployment timeout question rather than a source
   test failure.
5. Concurrency: comments/docstrings cleanup was active during comparison; the
   three byte-identical pre-existing files must remain untouched. Functional
   repair overlaps in the other seven must be reconciled before publication.
6. The exact-pair canary is a pinned-artifact check, not a new-premise quality
   or fresh-clone GPU acceptance verdict; #50 explicitly preserves that scope.
