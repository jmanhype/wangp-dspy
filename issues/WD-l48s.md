---
id: WD-l48s
title: "E2e: build the preflight spend-gate corpus with leakage-safe replay"
status: in_progress
priority: 1
type: feature
labels: [walking-skeleton, capstone, e2e, delivered]
parent: WD-as25
created_at: 2026-09-21T05:44:13Z
created_by: speed
updated_at: 2026-09-23T16:04:25Z
content_hash: "sha256:adbedc6f8cfb92b0a2247a9e727b8c74186ce4c5cb108a5ae460a4f42effea76"
closed_at: 2026-09-21T12:31:05Z
close_reason: "Accepted at 5f0035b1c911: WD-v6xp carries the deferred production fail-open seam under WD-as25; preregistration amendment preserves all original invariant fields and accurately discloses 1e-9 to 1e-6; all three added regression tests are meaningful; 11/11 targeted tests pass, exact-head CI is green, protected paths match main, corpus remains 36/18/5/7, and fresh-checkout replay returns insufficient_data/infeasible_at_budget."
assignee: dev-WD-l48s
blocked_by: [WD-rf1a, WD-v6xp]
---

## Description
## USER INTENT
A film operator wants to know, before a clip is admitted to the GPU queue, whether the available preflight signal can avoid a render that current post-render gates will reject. The immediate deliverable is honest replay evidence and a growing outcome corpus—not a production admission change.

## Context (Embedded)
### Measured corpus at repository main 3094b14
- There are **36 valid `datasets/runs/**/qc-evidence.json` files** on the current evidence checkout: **31 under `datasets/runs/pull`** and **5 under `datasets/runs/provenance`**. Every one parses as JSON.
- Usable gate outcomes are:
  - Whisper `pre`: **36 pass / 0 fail**; it has no discriminative signal in this corpus.
  - Whisper `post`: **27 pass / 9 fail**.
  - Vision: **25 pass / 0 fail**; 11 rows have no usable vision outcome.
  - SyncNet/AV: **18 usable outcomes: 13 pass / 5 fail**. This is more precise than key presence: 23 files declare `av_sync_gate`, 4 contain literal `null`, and 1 records `{"status": "failed", "error": "SyncNetRunnerError..."}` rather than a gate verdict. The execution error is a failure class, not a fifth AV rejection.
- Only **18 rows have usable outcomes for all four gates** (Whisper pre, Whisper post, vision, and AV), and **5 of those 18 fail at least one gate**. The primary comparative evaluation must use exactly these 18 rows unless regeneration finds different bytes; if counts differ, the artifact must report the regenerated counts and the manifest must explain the source selection.
- Schema drift is not determined safely by top-level directory. Across the 36 files, **13 contain only `{vision_judge, whisper_gates}`** and **23 also contain `av_sync_gate`**. The 5 `provenance` files are all two-gate files; `pull` contains both shapes (8 two-gate and 23 AV-bearing). Every claim must be restricted to gates each run both declared and actually recorded.
- Each of the 36 render directories on this checkout contains all ten joinable sidecars/media: `qc-evidence.json`, `settings.json`, `wgp-settings.json`, `runtime-evidence.json`, `speaker_manifest.json`, `conditioning-evidence.json`, `audio_manifest.json`, `render.log`, `raw.mp4`, and `remux.mp4`.
- **Portability correction:** Git tracks only **21 of the 36 QC rows**, and `datasets/runs/pull/` is ignored by default; several additional sidecars are local-only. Therefore the small normalized corpus and its source hashes must be committed so replay works from a fresh clone without ignored media. Indexing the full 36 requires this evidence checkout and an explicit local-evidence mode; it must record per-source Git availability rather than claiming every source is tracked.
- Exactly **five `datasets/*.jobs.db` files are Git-tracked**: four LF003 queues plus `lf004-operator-dogfood-56f-recovery-20260921.jobs.db`. Their `jobs` rows carry `state`, `failure_count`, and `failure_class`; `job_attempts`/`job_attempt_failures` carry durable attempts. Queue joins are expected to be partial. A row with no committed queue match must say `queue_join_status: unavailable`, not invent job state.
- The LF004 recovery `final-provenance.json` cut rows are the reference row shape. Their exact key set is `av_sync, clip_index, dialogue, gates, job_id, media, qc_evidence_path, qc_evidence_sha256, render_fingerprint, seed, speaker, vision, whisper`. Extend—not rename—that shape with plan/settings features and explicit coverage.
- Existing current-policy facts verified in source: `check_guide_duration` uses a `1e-9` guide-versus-shot tolerance; `JobExecutor` defaults `max_failures=3` and both default vision/Whisper retry budgets to 2; `DEFAULT_MAX_ATTEMPTS == 3`. None of these policies may change.

### Preregistered replay (fixed before results)
- Evaluation label: a complete row is **bad** iff at least one of Whisper post, vision, or AV recorded `false`; Whisper pre is recorded as a feature, not part of the post-render failure target.
- Group leakage key: stable `run_group_id` derived from plan/run identity (never individual clip alone). All cuts from one production run remain in the same fold.
- Splits: deterministic sorted leave-one-run-group-out cross-validation, seed `17`.
- Primary metric: **mean failed-render-attempts avoided per production run at a fixed false-admit budget of 0.10**, where false-admit is `(admitted bad rows / admitted rows)` on out-of-fold decisions. The report must also expose raw row counts; if no abstaining policy can meet the budget, the primary result is `infeasible_at_budget`, never a swept alternative.
- Confidence: group-level bootstrap over production-run groups, **2,000 samples, seed 17**, reporting the 2.5th/97.5th percentiles. Undefined folds/strata are reported as undefined, never silently dropped.
- Calibrated baseline: deterministic logistic model using preflight-only features, fit inside training folds only, with raw and calibrated probability tables and abstention when calibrated confidence is below **0.70**. Threshold sweeps are exploratory sensitivity context and cannot select or replace the primary result.
- Decision rule, evaluated in order:
  1. fewer than 50 complete rows, fewer than 10 bad complete rows, or fewer than 8 run groups => `insufficient_data` (the expected honest result for 18 complete rows);
  2. no policy meeting false-admit <= 0.10, or a bootstrap lower bound that does not exceed both deterministic and transparent baselines => `not_warranted`;
  3. otherwise => `warrant_future_training_story`. This story still does not train or deploy a production model.

## OUT OF SCOPE
- Training or deploying a production admission model: this story permits offline fitting only for leakage-safe replay; a future operator-approved story is required.
- Changing, weakening, tightening, reordering, or bypassing any Whisper, vision, mouth-box, SyncNet, retry, or provenance gate: the corpus must measure current policy, not alter it; lands never without separate authorization.
- Any GPU render, remote host work, model inference, or network/API call: this is an offline committed-data story; future renders belong in governed render stories.
- Changing the Content Brief Gateway: its queue-envelope omissions are already recorded as discovered during WD-g125 and require separate triage.
- PyPI or any other publishing: this remains repository-local evidence tooling; lands never.
- Retuning thresholds based on the threshold sweep: sweeps are explorer-only context, not a selection procedure.

## DIFF BUDGET
- Roughly 6 authored implementation/test files, under **600 authored changed LOC**. Deterministic generated JSON/JSONL/Markdown corpus artifacts are required deliverables and are reported separately, not used to hide implementation creep.
- Gross authored-file or LOC overrun triggers PM investigation; it is not automatically acceptable simply because the corpus is broad.

## Boundary Map
PRODUCES:
- training/spend_gate.py -> `SpendGateRow normalize_row(render_dir: Path, *, repository_root: Path, queue_rows: Mapping[str, Mapping[str, object]] | None = None) -> SpendGateRow`
  schema: `wangp-dspy.spend-gate-row/v1`; explicit gate outcome `pass | fail | null`, declared/recorded coverage, failure class, source hashes, prompt/settings features, queue join status, and media envelope.
- training/spend_gate.py -> `SpendGateCorpus build_corpus(repository_root: Path, *, evidence_mode: Literal["tracked", "all-local"] = "tracked") -> SpendGateCorpus`
  source: read-only over run directories and committed queue DBs; normalizes all 36 only under explicit `all-local` mode.
- training/spend_gate.py -> `Path write_corpus(corpus: SpendGateCorpus, output_dir: Path) -> Path`
  schema: canonical JSONL plus a manifest containing row count, gate-coverage counts, source-selection mode, source hashes, repository identity, corpus SHA-256, and schema-drift record.
- training/spend_gate.py -> `Path write_live_row(qc_evidence_path: Path, *, repository_root: Path, queue_rows: Mapping[str, Mapping[str, object]] | None = None, job_id: str | None = None, clip_index: int | None = None) -> Path`
  event: called by the production QC completion seam after `qc-evidence.json` exists; writes `spend-gate-row.json` atomically beside the evidence and never changes a gate verdict.
- training/spend_gate_replay.py -> `ReplayReport replay_baselines(corpus_path: Path, *, seed: int = 17, bootstrap_samples: int = 2000, false_admit_budget: float = 0.10) -> ReplayReport`
  event: deterministic no-GPU replay of all four declared baselines with identical rows/folds and a raw-versus-calibrated report.
- scripts/build_spend_gate_corpus.py -> `main(argv: Sequence[str] | None = None) -> int`
  endpoint: `--repository-root`, `--evidence-mode {tracked,all-local}`, `--output-dir`, `--replay`, and `--verify-artifact`; nonzero exit on malformed/unhashable evidence.
- tests/test_spend_gate.py -> unit and real-artifact integration tests for normalization, null semantics, queue joins, deterministic hashes, replay, and LF004 row parity.
- datasets/spend-gate/v1/corpus.jsonl -> one normalized row per recorded rendered clip.
- datasets/spend-gate/v1/manifest.json -> canonical manifest hash and gate/schema-drift summary.
- datasets/spend-gate/v1/schema-drift.json -> per-run-group declared/recorded gate coverage.
- datasets/spend-gate/v1/preregistration.json -> the fixed label, folds, primary metric, budget, thresholds, bootstrap, and decision rule.
- datasets/spend-gate/v1/replay-report.md -> four-baseline table, raw-versus-calibrated table, confidence intervals, explicit limits, negative result, and decision-rule outcome.
- datasets/spend-gate/v1/replay-metrics.json -> machine-readable metrics required by regression tests.

CONSUMES:
- WD-ssdt: predict/content_brief.py -> `load_content_brief(path: str | Path) -> ContentBrief`
  spec: use only when a recorded source brief exists; preserve `ContentBrief.brief_hash` verbatim and use `null` when no brief is available.
- WD-ssdt: predict/content_brief.py -> `build_run_film_inputs(brief: ContentBrief, plates_dir: str | Path, *, run_dir: str | Path) -> dict[str, Any]`
  spec: current measured-guide preflight semantics; replay must not invoke its output-side-effect path.
- (existing): services/director/renderers/policy.py -> `check_duration_on_grid(duration_s: float, fps: int = 24) -> int`
  spec: deterministic frame-grid policy replay; preserve the existing typed rejection behavior.
- (existing): services/director/renderers/policy.py -> `check_facing(plate_path: str, requirement: str) -> str`
  spec: deterministic plate-facing policy replay; unavailable historical plates must remain explicit null/unknown, never default to pass.
- (existing): services/director/renderers/policy.py -> `check_guide_duration(guide_duration_s: float, shot_duration_s: float) -> None`
  spec: exact current `1e-9` guide-versus-shot comparison.
- (existing): services/jobs/queue.py -> `effective_render_fingerprint(clip: Dict) -> str`
  source: effective renderer-input identity excluding queue bookkeeping.
- (existing): services/jobs/queue.py -> `JobQueue.get(self, job_id: str) -> JobRecord`
  spec: read-only queue-row join; `JobRecord` carries `job_id`, `state`, `clips`, `failure_count`, `failure_class`, `failure_detail`, and `created_at`.
- (existing): services/jobs/queue.py -> `JobQueue.attempt_history(self, job_id: str) -> List[Dict]`
  spec: read-only attempt/failure history used to count existing attempts; never mutate a committed DB.
- (existing): services/jobs/executor.py -> `JobExecutor.__init__(self, *, queue, preflight: Callable, render: Callable[[dict], RenderOutcome], qc: Callable[[dict], tuple], ref2va_render: Optional[Callable[[dict], RenderOutcome]] = None, pre_render: Optional[Callable[[dict], None]] = None, max_failures: int = 3, staleness_s: float = 600.0, picker: Optional[Callable[[], Optional[str]]] = None)`
  source: the production post-QC seam where the new recorder must be called after evidence exists without altering admission or retry behavior.
- (existing): services/director/run_ledger.py -> `repository_identity(repo_root: Optional[os.PathLike[str] | str] = None) -> dict`
  source: canonical repository root/HEAD/dirty-tree identity for corpus manifest attribution.
- WD-g125: datasets/runs/pull/lf004-operator-dogfood-56f-recovery-20260921/final-provenance.json -> cut-row schema
  schema: `av_sync, clip_index, dialogue, gates, job_id, media, qc_evidence_path, qc_evidence_sha256, render_fingerprint, seed, speaker, vision, whisper`; this is the compatibility oracle for row parity.

## Required Outcomes
1. `build_corpus(..., evidence_mode="all-local")` emits exactly one stable row per QC-bearing render directory in this evidence checkout (36 at authoring time), and the committed `corpus.jsonl` remains replayable in a fresh clone even where ignored source media is absent. Row IDs and manifest hashes are deterministic across two invocations; no wall-clock value participates in the row hash.
2. Every normalized row preserves the LF004 key vocabulary where applicable and adds stable run/job/clip identity, brief/plan hash when available (`null` otherwise), seed, speaker, mode/policy version, prompt-derived features, declared guide versus shot duration, resolution/frame envelope versus delivered media, per-gate declared/recorded status and outcome (`pass`, `fail`, or explicit `null`), failure class, queue state/attempt facts when joinable, source-path Git availability, and SHA-256 for every source used. A missing fact remains `null`; it is never imputed, defaulted to pass, or inferred from gate absence.
3. The schema-drift artifact reports per run group which gates were declared and which produced usable outcomes. At authoring time it must reconcile exactly to: 36/36 usable Whisper pre and post; 25 usable vision; 18 usable AV outcomes (13 pass/5 fail) out of 23 AV keys, with four null AV values and one SyncNet execution error distinguished; and 18 complete four-gate rows, 5 of which fail at least one gate. Regenerated counts are allowed only when source bytes/selection differ, and the difference is fail-closed and explained in the manifest.
4. Queue normalization reads only the five Git-tracked DBs in replay mode, records each DB SHA-256, joins rows without mutating them, and records `job_id`, `state`, `failure_count`, `failure_class`, attempt count, and last failure when available. Unmatched rows explicitly use `queue_join_status: unavailable`; no row fabricates attempts or failure state.
5. The versioned artifact set is committed under `datasets/spend-gate/v1/`, its canonical manifest hash validates, and a fresh-checkout replay consumes the committed corpus without network, GPU, API credentials, remote host access, or presence of ignored media. Two replay runs produce byte-identical `replay-metrics.json` (excluding no fields) under the fixed seed.
6. `replay_baselines(...)` evaluates all four baselines on the same complete-row subset and identical grouped folds: (a) current deterministic preflight replay (duration/grid, guide existence and duration equality, plate facing, resolution/frame envelope), (b) always-admit with the existing recorded retry/attempt policy, (c) the fixed LLM-free transparent heuristic, and (d) the train-fold-calibrated model with abstention. The report proves no production-run group crosses a training/held-out boundary and no post-render outcome is accidentally used as a preflight feature.
7. The transparent heuristic is fixed in `preregistration.json` before results and uses only preflight features. The calibrated model is fit only inside training folds; raw and calibrated held-out coverage, abstentions, correct/incorrect decisions, false-admit rate, Brier score, log loss (when defined), and confidence bins are reported side by side. Empty bins remain visible.
8. The primary metric is exactly the preregistered failed-render-attempts avoided per production run at false-admit <= 0.10, with grouped bootstrap confidence intervals. A threshold-sweep table is labeled exploratory. With 18 complete rows, the report must state plainly that the result is underpowered and must execute the decision rule (expected `insufficient_data`) rather than claiming model value or hiding negative calibration results.
9. The production QC completion seam invokes `write_live_row(...)` once evidence exists, writes an atomic `spend-gate-row.json`, preserves all existing gate/retry decisions and timings, and fails closed with a typed recording error rather than silently omitting the guarantee. Replaying the existing four LF004 recovery render directories through this function produces rows equal to the corpus LF004 rows for every shared field.
10. No Whisper, vision, mouth-box, SyncNet, QC, retry, admission, Content Brief Gateway, or provenance-gate semantic changes are present in the source diff. The implementation performs no GPU render, remote host command, model inference, network/API call, package publication, or mutation of historical evidence/queues.

## Testing Requirements
- Unit:
  - malformed/missing/null gate evidence becomes explicit null and a typed source/failure status, never pass;
  - AV `{status: failed}` is an execution-error class while `{passed: false}` is an AV failure;
  - stable row IDs, canonical JSON, manifest hash, and source availability are deterministic;
  - unmatched queue rows are honest and matched rows preserve `failure_count`, state, and attempt count;
  - grouped folds keep every production run intact, and bootstrap/threshold behavior is deterministic for seed 17;
  - unknown preflight features cause abstention/recording failure rather than zero-filling.
- Integration: MANDATORY and real, with no mocks, skipped evidence, or cached scores in the integration tests.
  - In this evidence checkout, build the full corpus with explicit `--evidence-mode all-local`, validate all 36 source directories and ten sidecars per render, and assert the measured gate counts above.
  - From a clean temporary Git checkout (or equivalent repository-owned fresh-copy fixture that does not rely on ignored media), verify the committed corpus manifest and replay all baselines twice.
  - Replay the four real LF004 recovery directories against `final-provenance.json`, the committed queue DB, real sidecars, and real media metadata; compare shared LF004 fields.
  - Exercise `write_live_row` against copies of real evidence directories and prove atomic replacement plus typed failure on missing/unreadable evidence.
- Commands to run:
  - `uv run --frozen --extra dev pytest -q tests/test_spend_gate.py`
  - `uv run --frozen --extra dev python scripts/build_spend_gate_corpus.py --repository-root . --evidence-mode all-local --output-dir datasets/spend-gate/v1 --replay --verify-artifact`
  - a fresh-checkout replay of the same corpus without the `all-local` mode, exact command printed by the CLI help/test output;
  - `git diff --check`.
- No GPU/remote test is permitted. Any test that cannot obtain required committed evidence must fail; it must not skip based on environment.

## MANDATORY SKILLS
- pvg — story governance, append-only evidence, delivery transition, and dispatch safety.
- None additional; this story deliberately avoids GPU/render skills.

## Delivery Requirements
- Developer must paste exact unit/integration command output tails, corpus row/gate counts, canonical manifest SHA-256, replay artifact hashes, decision-rule outcome, and fresh-checkout replay proof into nd notes.
- Developer must provide an AC verification table mapping every AC to code, test, and artifact evidence, including the source-diff check that no gate/retry semantics changed.
- Developer must include the four-baseline comparison and raw-versus-calibrated table in the delivery note, including negative or undefined results.
- Developer must update the authoritative `nd_contract` to `delivered` and add the `delivered` label using the pvg workflow; PM acceptance remains separate.

## nd_contract
status: new

### evidence
- Created: 2026-09-21 at repository main 3094b14 after direct recount of the 36 QC files, gate/schema distributions, tracked/untracked evidence, five committed queue DBs, LF004 provenance keys, and verified source signatures above.

### proof
- [ ] Pending implementation


## Acceptance Criteria


## Design


## Notes


## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-21.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## Implementation Evidence (Rework 3: eight pre-merge review defects)

PROOF:

### Commit / PR
- Branch: story/WD-l48s
- Pushed head: c7963e82bd013ac7757933c9f44444583ae47425
- Commits: 579f8b9c6100593324993df2c41ee82aa611ef73 (implementation), c8e2ad003de4c41641cb5df32c393a5fc2dce81c (row-identity hardening), c7963e82bd013ac7757933c9f44444583ae47425 (CI environment-independent assertion)
- PR: https://github.com/jmanhype/wangp-dspy/pull/150
- PR state after push: OPEN, MERGEABLE, mergeStateStatus=CLEAN, required test=SUCCESS.
- Intermediate CI 35603399376 failed at c8e2ad0 because I briefly added a whole-row ID comparison across host environments. It was removed in c7963e8; assertions now target identity-independent path fields and content-derived replay fields, as required.

### Eight-defect verification
| # | Review finding | Fix / code evidence | Regression evidence | Artifact evidence |
|---|---|---|---|---|
| 1 | P(bad) polarity was inverted | `_raw_probability_decision`, `_calibrated_probability_decision`, and `_threshold_probability_decision` admit only when P(bad) is low; calibrated confidence remains `max(p,1-p) >= 0.70` (training/spend_gate_replay.py:153-173, 309-329, 327-329) | tests/test_spend_gate.py:105-118 asserts low P(bad) admits, high P(bad) rejects/does not admit, and sweep direction | replay-metrics.json records `model_probability_definition="P(bad)"`, explicit `decision_polarity`, and corrected raw/calibrated/sweep tables |
| 2 | Queue loader retained only clips[0] and joined on job ID alone | Queue keys are `(job_id, clip_index)` composites; every serialized clip is loaded; exact and fallback matches require clip identity plus path identity (training/spend_gate.py:113-181, 257-283) | tests/test_spend_gate.py:121-141 builds a real two-clip SQLite queue and proves clip 2 gets clip 2's fingerprint | corpus queue rows and LF004 joins regenerate at 36 rows with the expected 5 tracked DB sources |
| 3 | Unknown attempts became 0+1 avoided attempts | `_known_attempt_count` preserves unknown as null; `_score` excludes unknown rejected-bad rows from the numerator and reports exclusions (training/spend_gate_replay.py:176-208) | tests/test_spend_gate.py:144-157 asserts known attempt cost 3, one unknown excluded, and metric 1.0 rather than fabricated 2.0 | replay-metrics baseline fields `known_attempt_rejected_bad_rows`, `unknown_attempt_rows`, and `unknown_attempt_rejected_bad_rows_excluded`; report discloses deterministic_preflight=5 exclusions |
| 4 | Bootstrap numerator used distinct groups rather than draws | `_score(group_draws=...)` divides by the number of group draws; `_bootstrap` passes `len(draws)` (training/spend_gate_replay.py:181-208, 211-227) | tests/test_spend_gate.py:158-159 asserts duplicated group draw value 0.75, not the inflated distinct-denominator value | bootstrap fields regenerate byte-identically under seed 17 |
| 5 | False-admit budget hard-coded 0.10 in scoring | `false_admit_budget` threads through `_score`, probability tables, bootstrap, and every sweep row (training/spend_gate_replay.py:181-227, 317-329) | tests/test_spend_gate.py:160-168 asserts 0.10 infeasible versus 0.50 feasible and proves bootstrap receives the configured budget | replay-metrics records `false_admit_budget=0.1` and all feasibility uses that value |
| 6 | Decision warranted on feasibility alone | `_decision_rule` requires a feasible challenger CI lower bound to beat BOTH deterministic and transparent baseline upper bounds; insufficient-data remains first (training/spend_gate_replay.py:251-282, 324-326) | tests/test_spend_gate.py:171-186 proves a feasible but weaker CI is `not_warranted`, while a CI beating both comparators warrants | replay-metrics `decision_rule_evaluation` records comparators/stage; current honest decision remains `insufficient_data` |
| 7 | Absolute/path-only fields made row IDs checkout-dependent | Paths are recursively canonicalized relative to repository anchors; path fields, source-git availability, and plate path availability are excluded from row identity (training/spend_gate.py:119-168, 252-253) | tests/test_spend_gate.py:189-212 proves path/availability changes do not alter identity but content hash changes do; fresh-checkout replay remains environment-independent | corpus contains no absolute path values; canonical corpus SHA below |
| 8 | verify_artifact ignored drift digest and row count | `verify_artifact` checks corpus digest, schema-drift digest, manifest self-digest, and declared row count versus nonempty corpus lines (training/spend_gate.py:379-394) | tests/test_spend_gate.py:215-226 tampers schema drift and a self-consistent false row count and requires typed failures | CLI `--verify-artifact` passes on the committed artifact |

### Corrected replay result (polarity fixed; stale values not preserved)
Corpus/headline invariants:
- Rows: 36 total / 18 complete / 5 bad / 7 complete-row run groups
- Decision: `insufficient_data`
- Primary result: `infeasible_at_budget`
- Primary metric: undefined/null (no feasible calibrated policy at budget)

| Baseline | Admitted | Abstained | False admit | Avoided/run | Bootstrap 95% CI |
|---|---:|---:|---:|---:|---:|
| always_admit | 18 | 0 | 0.278 | undefined | [0.000, 0.000] |
| deterministic_preflight | 0 | 0 | undefined | undefined | undefined |
| transparent_heuristic | 18 | 0 | 0.278 | undefined | [0.000, 0.000] |
| calibrated_model | 5 | 13 | 0.800 | undefined | undefined |

Raw versus calibrated:
| Policy | Coverage | Correct | Incorrect | False admit | Brier | Log loss |
|---|---:|---:|---:|---:|---:|---:|
| raw P(bad) | 13/18 | 10 | 8 | 0.308 | 0.444 | 15.351 |
| calibrated | 5/18 | 1 | 4 | 0.800 | 0.254 | 0.736 |

Exploratory sweep (maximum tolerated P(bad)): thresholds 0.5, 0.6, 0.7, 0.8, and 0.9 each admit 18 rows with false-admit 0.278. Sweep remains exploratory and did not select the primary result.

### Artifact evidence / determinism
- corpus.jsonl SHA-256: 4bf1fb1e9e6367c43933176f21d2597b366c8c7b9074f5d99d9840340f46188e
- manifest.json file SHA-256: 90c7f8f41652f33b32470b56381bf3a587aebedaa858c19fd31991f229d6d455
- manifest self-digest: 43eb41ef07a77569532886dbc6df88c410176141b8630727105161744366ecbd
- preregistration.json SHA-256: 84ad3471aa4ed6d22ea69904285d2a05c157c5198e2ef84286d92e448e081479
- replay-metrics.json SHA-256: 2aea4f6c5de8bb63d1ff6ead2915f96b8b5f39469ff90feead64e8ae0dda2afd
- replay-report.md SHA-256: 5a5c41d0f6753b8b14507ce44bdd47b4fc0ec69584962c317bbf7dc562637b79
- schema-drift.json SHA-256: 538712be86789709c8d296a3cca08c45861ffa1df8fab0a3b452de0f261d0c5f
- `verify_artifact` validated corpus digest, schema-drift digest, row count 36, and manifest self-digest.
- Two consecutive all-local builds to the same external output directory produced identical SHA-256 manifests for all six artifact files (`diff -u ... == no differences`).

### CI/Test Results
- Commands run:
  - `uv run --frozen --extra dev pytest -q tests/test_spend_gate.py`
  - `uv run --frozen --extra dev pytest -q`
  - `uv run --frozen --extra dev python scripts/build_spend_gate_corpus.py --repository-root . --evidence-mode all-local --output-dir datasets/spend-gate/v1 --replay --verify-artifact`
  - `git diff --check`
  - `git diff --exit-code main -- services/ qc/ host/ predict/ scripts/run_film.py scripts/run_jobs.py`
  - `pvg verify ... --format=text`
- Targeted tail: `................. [100%]` — 17/17 tests PASS, 0 failed, 0 skipped.
- Full-suite tail: progress completed at 100%; 1,575 PASS, 1 pre-existing optional-host test skipped (`tests/test_jobs_integration_3090.py:15-17`, not run because GPU/host work is explicitly forbidden), 0 failed. Collection: 1,576 tests.
- Coverage: stdlib `trace` measured 100% executed-line coverage for both changed training modules from the targeted suite (`training.spend_gate`: 275 lines; `training.spend_gate_replay`: 294 lines). The frozen dev environment has no coverage package, so stdlib trace was used.
- `git diff --check`: PASS (no output).
- Protected-path parity: exit 0. No production runner, QC, AV, retry, renderer, or gate semantics changed.
- `pvg verify`: `VERIFY: PASSED (4 files scanned, 0 issues)`.
- Required CI at pushed head: run 35603725188, head c7963e82bd013ac7757933c9f44444583ae47425, workflow CI, conclusion SUCCESS (test job 106345685155).
- No GPU, remote host, render, queue submission, model inference, package publication, or gate mutation was run.

### Warnings / observations (not silently ignored)
- Local full suite exposes one pre-existing dependency warning: FastAPI/Starlette TestClient deprecates httpx compatibility when imported by `tests/qc/audio_critic/test_default_loader.py`.
- Final CI is green but emits runner annotations that actions/setup-python@v5 and astral/set-uv@v6 are forced from deprecated Node.js 20 onto Node 24, and ubuntu-latest will migrate to Ubuntu 26 on 2026-10-19.
- `pvg notes search` could not be used in this checkout because `.paivot/config.yaml` names vault `Claude`, while the available vault list does not contain it. I did not alter unrelated vault configuration.

LEARNINGS:
- Model probability direction must be named at every policy boundary: P(bad), confidence, and threshold direction are three separate contracts and can still be combined backwards.
- Queue identity is clip-level, not job-level; a composite key makes the wrong-clip join impossible without changing the public queue mapping type.
- Attempt utility is undefined until a durable attempt count is present. Reporting exclusions is more honest than treating null as zero.
- Cross-environment tests must compare content-derived fields, not whole row IDs: ffprobe/toolchain and local evidence availability can legitimately differ even after path canonicalization.

### DISCOVERED_BUG (reported, not created)
  title: pvg notes points at unavailable Claude vault
  context: `pvg notes search "WD-l48s spend gate replay polarity"` and a simpler query failed with `vlt: vault "Claude" not found`; `.paivot/config.yaml` selects `Claude` while available vaults include `.vault`, `nd-vault`, `Obsidian Vault`, and others. This blocked the developer skill's optional knowledge search but not nd story operations.
  affected_files: .paivot/config.yaml
  discovered_during: WD-l48s

### DISCOVERED_BUG (reported, not created)
  title: Full suite emits FastAPI/Starlette httpx deprecation warning
  context: Every full pytest run warns when repository tests such as tests/qc/audio_critic/test_default_loader.py import FastAPI/Starlette TestClient: using httpx with starlette.testclient is deprecated and recommends httpx2. Tests still pass, but this is a future-breaking dependency warning.
  affected_files: tests/qc/audio_critic/test_default_loader.py (repository test importing the dependency surface; no story file changed)
  discovered_during: WD-l48s


## Rejection 2 (pre-merge review, PR #150): eight correctness findings

Independent code review of the accepted artifact found eight real defects. The first is
headline-level and I verified it myself:

1. **Inverted decision polarity (verified).** `_bad()` supplies the positive label, so the
   fitted `probability` estimates **P(bad)**. The code then does
   `raw_decisions = "admit" if probability >= 0.5 else "reject"` and
   `calibrated_model = "abstain" if confidence < 0.70 else "admit" if calibrated >= 0.5 else "reject"`,
   and the threshold sweep uses `admit if calibrated >= threshold`. Every one of those admits the
   rows most likely to FAIL. Observed in the artifact: a row with `raw_probability = 1.0`
   (certain bad) is recorded as `admit`. The raw table, the calibrated table, the correctness
   counts and the exploratory sweep are therefore all computed against inverted decisions.
   Required: admit when P(bad) is LOW. Keep the frozen `calibrated_confidence_threshold = 0.70`
   semantics (abstain when max(p, 1-p) < 0.70), and make the admit/reject direction explicit and
   tested in both the raw, calibrated and sweep policies.
2. `_load_queue_rows` keeps only `clips[0]` per job and `_queue_match` returns that record on a
   job-id match alone, so later clips inherit the first clip's fingerprint and artifact paths.
   Represent queue records per (job_id, clip_index), load every serialized clip, and require both
   to match.
3. `_score` turns an absent queue record or attempt count into zero and then adds one, so an
   unmatched rejected bad row contributes a fabricated avoided attempt. Track unknown attempt
   counts as unknown and exclude them from (or report them separately from) the avoided-work
   metric.
4. `_bootstrap` resamples run groups with replacement and concatenates their rows, but `_score`
   divides by the number of DISTINCT groups, so duplicated draws inflate the numerator. Divide by
   the number of group draws, keeping duplicates as distinct bootstrap units.
5. `replay_baselines` accepts and records `false_admit_budget` but `_score` hard-codes 0.10, so a
   caller using another budget gets metrics labelled with it while feasibility and the primary
   result still use ten percent. Thread the configured budget through scoring and bootstrap.
6. The preregistration requires a feasible policy whose confidence interval beats BOTH baselines;
   the decision returns `warrant_future_training_story` whenever any policy merely meets the
   budget. Implement the registered comparison (or record an explicit amendment if the rule is
   being changed).
7. Canonical rows carry machine-specific absolute paths and path-bearing fields, which is why
   `row_id` is not reproducible across checkouts and why a fresh clone cannot rebuild the corpus.
   Canonicalize stored paths relative to the repository and drop path-only fields from the hashed
   identity.
8. `verify_artifact` checks only the corpus digest and the manifest self-digest; it ignores the
   declared schema-drift digest and the corpus row count, so a swapped `schema-drift.json` or a
   manifest with a false row count passes verification. Verify both.

Also required: tests that would fail against each defect (especially a polarity test asserting a
low-P(bad) row is admitted and a high-P(bad) row is not), a regenerated artifact with updated
hashes, and CI green at the new head. No GPU work and no change to any QC/AV/retry/renderer/gate
semantics. The accepted corpus counts (36/18/5) and the honest headline (`insufficient_data`,
`infeasible_at_budget`) must remain true after the fixes; if the polarity fix changes the
per-baseline numbers, report the corrected table rather than preserving stale values.

## nd_contract
status: accepted

### evidence
- PM closeout applied via pvg story accept on 2026-09-21.

### proof
- [x] Story closed after accepted label was applied.


## Rework 3: CI caught an environment-dependent assertion in my own test (head 5f0035b)

The first rework pushed a new test that compared a whole corpus row against a freshly
written live row. `row_id` folds in per-artifact source-git availability, which legitimately
differs between this all-local evidence checkout and a fresh clone, so required CI failed at
`bdb78e6` with a row_id mismatch.

Fixed at `5f0035b`: the test now keys off the tracked LF004 provenance hash and asserts
content-derived fields (`qc_evidence_sha256`, `clip_index`, `source_path`), byte-stability
across two consecutive writes, and the absence of `*.tmp-*` leftovers. It is now
environment-independent.

Required CI: run 35598879984 failed at bdb78e6 (this defect); the run at head
`5f0035b1c911` is SUCCESS.

Lesson recorded for the next story: a test may not compare a whole row across environments;
only content-derived fields are stable.

## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-21.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## Scope Amendment (dispatcher review) + Rework (head bdb78e6)

Independent acceptance rejected the first delivery on three grounds. All three are now
resolved; one of them required an authoritative scope change, recorded here.

### Amendment: Required Outcome 9's production seam is deferred to WD-v6xp

The story demanded both (a) a production QC-completion seam invoking the live recorder and
(b) protected-path parity that forbids a `services/` change. Those two cannot both hold.
The dispatcher's ruling: the seam is deferred to **WD-v6xp** ("Emit the spend-gate decision
row from the production QC seam (fail-open)"), because the naive version reviewed in the
first draft imported `training/` into `services/jobs/executor.py` inside the QC loop and
re-raised a recording error, which could fail a render attempt.

For WD-l48s the recording guarantee is satisfied by the standalone post-run recorder plus
the indexer, with `services/` byte-identical to main. WD-v6xp carries the seam with the
fail-open and layering constraints made explicit.

Wording correction: "nothing under `scripts/` imports `training`" was imprecise. The rule is
that production runner scripts must not import `training/`; `scripts/build_spend_gate_corpus.py`
is the sanctioned analysis entry point and does import it.

### Rework 1: preregistration amendment recorded instead of silent drift

`preregistration.json` now carries an explicit `amendments` entry for the transparent
heuristic's tolerance correction (frozen 1e-9 -> production 1e-6), with the original value,
the reason (the frozen value was itself a defect that rejected every recorded row), the
evidence (guide gap 3.3333333338e-07; 18/18 rejected at 1e-9, 0/18 at 1e-6), and an explicit
statement that the primary metric, decision rule, budget, seed and folds were NOT changed.
The replay report limits disclose the amendment and the fact that it was declared after
first results.

### Rework 2: the three missing tests added

- missing facing sidecar still reaches `admit`, and a `profile` facing still rejects;
- the clipped-probability disclosure (epsilon 1e-15, raw clipped == complete row count,
  calibrated clipped == 0, raw log loss > 5, report line present);
- atomic replacement of an existing `spend-gate-row.json` with no `*.tmp-*` left behind.

### Also disclosed in the report limits

Per-artifact untracked-media counts: delivered `remux.mp4` untracked for 12 rows, 16 rows
have at least one untracked artifact, 20 rows have all ten artifacts tracked (the earlier
"15 of 36" figure was true for raw source media/evidence but not for delivered remux).

### Verification at bdb78e6

- 11 targeted tests pass (was 8).
- Artifacts regenerated; corpus row content unchanged; manifest/preregistration/metrics/report updated.
- Protected-path parity with main exits 0.

## nd_contract
status: rejected

### evidence
- PM rejection applied via pvg story reject on 2026-09-21.

### proof
- [ ] Story requires another developer delivery before it can be accepted.


## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-21.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## Delivery Evidence (head 7a46211, dispatcher-completed after a provider 429)

The developer agent was rate-limited out (429) mid-story. I completed the delivery myself after
reviewing its commit and finding three measurement defects that made its baseline table
unusable; the corrections and the resulting finding are below.

### Corrections made in review

1. Wrong tolerance in the deterministic baseline: an ffprobe-rounded guide (2.333333) was
   compared against the declared shot (56/24) with check_guide_duration's 1e-9 invariant, which
   only holds between two plan-declared values. The ~3e-7 gap rejected 13/13 known-good renders.
   Now uses the production AUDIO_DURATION_TOLERANCE_S (1e-6). The transparent heuristic had the
   same bug and is fixed.
2. Facing branch returned abstain whenever the plate sidecar was missing, so no row could ever be
   admitted. Production falls back to the character's declared requirement; replay now mirrors
   that and treats a missing sidecar as unevaluated.
3. Raw log loss (15.351) was undisclosed as a clip artifact: probabilities are clipped at 1e-15
   and 18/18 raw rows hit the clip. Clip epsilon and clipped-row counts are now reported.

Each rejection is now attributed by reason and rendered into the report. A raw CalledProcessError
was replaced by a typed SpendGateSourceError when tracked mode runs outside a git worktree.

### Result

- Decision: insufficient_data (preregistered rule: complete<50, bad<10, groups<8). Primary
  result: infeasible_at_budget. No production model is warranted by this run; the report says so.
- Corpus: 36 rows / 18 complete / 5 bad / 7 run groups / 5 joined queue DBs. The committed corpus
  is all-local: 15 of 36 rows come from media not tracked by git, so a fresh clone can REPLAY but
  not REBUILD it (tracked rebuild = 21 rows / 13 complete). Both facts are now in the report limits.
- Corrected-baseline finding: deterministic_preflight rejects 18/18 complete rows for one reason,
  delivered_resolution_contradicts_envelope. The envelope resolution field contradicts delivered
  media for every recorded render (delivered 704x576 vs envelope 480x832 on the accepted LF004
  recovery film). Recorded as WD-rf1a rather than papered over.

### Verification

- 8 targeted tests pass (tests/test_spend_gate.py), including new tests for the tolerance, the
  reason attribution, the all-local disclosure, and the non-git tracked rejection.
- Protected-path parity with main exits 0: services/ qc/ host/ predict/ scripts/run_film.py
  scripts/run_jobs.py. No gate, retry, or renderer semantics changed. No GPU or host work.
- Required CI: run 35570749029 at head 7a462111210ca626cd5d3c43be1d4b310dac7cf1 -> success.
- Artifact regeneration is byte-stable across repeated rebuilds (asserted by the fresh-checkout test).

### AC mapping

| AC | Evidence |
|---|---|
| Normalized per-clip rows with explicit nulls and source hashes | corpus.jsonl (36 rows), manifest.json gate_counts + source_hashes/source_git_available |
| Never impute a missing gate outcome | gate_coverage outcome=None when unusable; 4 null_value + 1 execution_error distinguished; test_committed_counts_null_and_execution_error_semantics |
| Schema-drift record | schema-drift.json + schema_drift_sha256 in manifest |
| Four baselines on identical rows and grouped folds | replay-metrics.json baselines + grouped_folds (no train/held-out row overlap) |
| Leakage-safe fitting and bootstrap CIs | grouped leave-one-run-group-out folds; bootstrap_ci_2_5/97_5 per baseline |
| Preregistered primary metric stated before results | preregistration.json (primary_metric, budget 0.10, decision_rule) |
| Honest underpowered / negative reporting | decision=insufficient_data; limits include the negative calibration result |
| Recording guarantee | write_completed_run_rows reproduces all four LF004 recovery rows (test_post_run_recorder_reproduces_all_lf004_rows), with no production coupling |
| Committed corpus replayable in a fresh checkout | --verify-artifact replay path asserted by test_fresh_corpus_replay_is_deterministic_group_safe_and_honest |
| No gate/retry/production change | protected-path parity exits 0 |

## History
- 2026-09-21T05:46:58Z status: open -> in_progress
- 2026-09-21T05:46:58Z claimed by dev-WD-l48s
- 2026-09-21T07:00:16Z status: in_progress -> in_progress
- 2026-09-21T12:16:33Z status: in_progress -> open
- 2026-09-21T12:16:33Z released by speed
- 2026-09-21T12:19:41Z status: open -> in_progress
- 2026-09-21T12:24:08Z status: in_progress -> in_progress
- 2026-09-21T12:31:05Z status: in_progress -> closed
- 2026-09-21T12:35:04Z status: closed -> open
- 2026-09-21T13:14:06Z status: open -> in_progress

- 2026-09-23T16:02:18Z dep_added: blocked_by WD-rf1a

- 2026-09-23T16:02:19Z dep_added: blocked_by WD-v6xp

## Links
- Parent: [[WD-as25]]
- Blocked by: [[WD-rf1a]], [[WD-v6xp]]

## Comments

### 2026-09-21T12:16:33Z speed
## PM Decision
REJECTED [2026-09-21]: Independently reproduced the corpus and the three replay corrections, but the delivery does not satisfy the story's production-recording or preregistration contract.

### Independently reproduced
- Corpus: 36 rows; gate outcomes 36/0 Whisper pre, 27/9 Whisper post, 25/0 vision, 13/5 AV; 18 complete rows; 5 bad complete rows; replay uses 7 complete-row run groups (the full 36-row corpus has 13 row-group labels). All unusable gate outcomes are explicit null; AV failure classes are 4 null_value, 1 execution_error, 13 undeclared, 18 usable.
- Corrections: at 1e-9, 18/18 complete rows reject for measured_guide_contradicts_declared_shot (gap 3.3333333338e-07); at 1e-6 that reason disappears and the sole reason is delivered_resolution_contradicts_envelope. A missing facing sidecar changes from abstain to reachable admit. Raw log-loss clipping is disclosed as 18/18 rows at epsilon 1e-15.
- WD-rf1a: all 18 recorded complete rows plan 480x832 while recorded ffprobe reports 704x576; spot-checked source settings/WGP and remux hashes agree with the rows.
- Verification: 8/8 targeted tests pass at 7a462111210ca626cd5d3c43be1d4b310dac7cf1; GitHub test check run 35570749029 is SUCCESS at that SHA; repeated all-local regeneration is byte-identical; tracked rebuild is 21 rows / 13 complete.

EXPECTED: Required Outcome 9 says the production QC completion seam invokes write_live_row once evidence exists, preserves gate/retry decisions and timings, and fails closed with a typed recording error.
DELIVERED: Only the standalone post-run helper exists (training/spend_gate.py:318-329). services/jobs/executor.py:_qc_clips still runs QC and updates the queue without calling the recorder; tests merely exercise write_completed_run_rows and do not invoke the production seam.
GAP: Future production QC rows are not guaranteed to be recorded, and there is no seam/timing integration proof.
FIX: Wire the post-QC recorder into the real completion path without changing admission/retry semantics, and add a real integration test that proves one atomic spend-gate-row.json per completed cut plus typed failure while decisions/timings remain unchanged.

EXPECTED: AC 7 says the transparent heuristic is fixed in preregistration.json before results and replay follows it.
DELIVERED: preregistration.json specifies a 1e-9 guide comparison, while the corrected implementation uses 1e-6 (training/spend_gate_replay.py:143-150) after results were observed.
GAP: The post-hoc correction is substantively right but is not disclosed as an amendment, so the report still calls the policy preregistered unchanged.
FIX: Disclose a dated correction/amendment in both preregistration and report, retain the original 1e-9 result as an exploratory/pre-correction sensitivity row, and add a test tying the amended tolerance and disclosure together.

EXPECTED: The test contract covers atomic replacement and the two other corrected behaviors.
DELIVERED: The tolerance regression test fails against a temporary pre-fix copy, but no committed test covers missing-sidecar facing fallback or clipped-row disclosure; the live-row test does not prove replacement of an existing output, and it writes transiently into real local evidence rather than a copied evidence directory.
GAP: Corrections 2 and 3 can silently regress; atomic failure/replacement behavior is unproven.
FIX: Add focused tests for sidecar fallback admit reachability and clip-count disclosure, and test atomic success/failure against copied real evidence.

## nd_contract
status: rejected

### evidence
- PM independently reran corpus derivation, tracked/all-local rebuilds, replay comparisons, targeted pytest, boundary diff, manifest hashes, and PR check lookup at head 7a462111210ca626cd5d3c43be1d4b310dac7cf1.
- Production seam gap verified from services/jobs/executor.py and tests/test_spend_gate.py.

### proof
- [ ] AC #9: production QC seam invocation, timing preservation, and typed failure are unproven.
- [ ] AC #7: implemented transparent heuristic no longer matches the frozen preregistration and the post-hoc change is undisclosed.
- [ ] Testing Requirements: facing fallback, clip disclosure, and atomic replacement coverage are insufficient.
