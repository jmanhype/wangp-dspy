---
id: WD-ln0n
title: "E2e: build the preflight spend-gate corpus with leakage-safe replay"
status: open
priority: 1
type: feature
labels: [walking-skeleton, capstone, e2e]
parent: WD-as25
created_at: 2026-09-21T05:41:54Z
created_by: speed
updated_at: 2026-09-21T05:41:54Z
content_hash: "sha256:d3c4ca688e4b9195c2f308593d7224574d7ba7d9ce375aa08c2e26631fa56c0b"
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
  - SyncNet/AV: **18 usable outcomes: 13 pass / 5 fail**. This is more precise than key presence: 23 files declare `av_sync_gate`, 4 contain literal `null`, and 1 records `{\"status\": \"failed\", \"error\": \"SyncNetRunnerError...\"}` rather than a gate verdict. The execution error is a failure class, not a fifth AV rejection.
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
- training/spend_gate.py -> `SpendGateCorpus build_corpus(repository_root: Path, *, evidence_mode: Literal[\"tracked\", \"all-local\"] = \"tracked\") -> SpendGateCorpus`
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

## Acceptance Criteria
1. `build_corpus(..., evidence_mode=\"all-local\")` emits exactly one stable row per QC-bearing render directory in this evidence checkout (36 at authoring time), and the committed `corpus.jsonl` remains replayable in a fresh clone even where ignored source media is absent. Row IDs and manifest hashes are deterministic across two invocations; no wall-clock value participates in the row hash.
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


## History


## Links
- Parent: [[WD-as25]]

## Comments
