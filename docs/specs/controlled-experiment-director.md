# Spec: Controlled Experiment Director (hermes-a1005314)

## Problem

The pipeline can validate outcomes and select winners
(`experiments/records.py` on origin/main), but nothing proposes a
generation experiment. `predict/prompt_director.py` emits one
RenderBrief with no memory of the world state or prior signals, and
resource logic is a reactive OOM downshift. We need the missing
upstream half: a pure planner that turns (baseline brief, frozen
settings, world snapshot, budget, prior signals) into a
generation-ready, single-variable experiment plan — without rendering.

## Scope

New module `experiments/director.py` only. No changes to
`training/run_baseline_then_gepa.py`, `metrics/qc_feedback.py`,
`evaluate/render_qc.py`, or the generic H3 adapter.

## Contract

### WorldSnapshot (frozen dataclass, JSON-canonical)
- `world_id: str`, `version: int` (>=1), `continuity_refs: tuple[str,...]`,
  `identity_lock: str`, `invariants: tuple[str,...]`,
  `source_hash: str` — REQUIRED, exactly 64 lowercase hex.
- `canonical()` → deterministic JSON (`sort_keys`, compact separators).

### ResourceBudget (frozen dataclass)
- `max_variants` (int, default 2, >=2), `max_gpu_minutes` (>0),
  `max_disk_gb` (>0), `reserve_disk_gb` (>=0, < max_disk_gb).
- Negative/insufficient budgets → typed `InvalidBudget`.

### ControlledExperimentPlan (frozen dataclass)
- `plan_id` (`cep-<12hex>`), `plan_hash` (64 hex) — sha256 of the
  canonical plan content; same inputs+proposal → byte-identical plan.
- `baseline_spec`, `challenger_spec`: brief fields + frozen settings
  merged; identical except the single changed field.
- `target_metric: str`, `changed_field`, `old_value`, `new_value`,
  `rationale: str`, `frozen_settings` (recorded verbatim),
  `world` snapshot + `world_ref` (its source_hash),
  `predicted_resources {gpu_minutes, disk_gb}` (both variants summed),
  `evidence_state` (e.g. `insufficient_evidence` — never an invented
  metric), `next_action: "generate_two_variants"`.

### `plan_controlled_experiment(...)` (pure)
Args: baseline brief mapping, frozen render settings mapping,
WorldSnapshot, ResourceBudget, injected `proposer` callable,
injected `resource_estimator` callable, optional read-only
`prior_signals` mapping.

- Proposer called EXACTLY ONCE with a context dict containing the
  canonical world snapshot, prior signals (or explicit
  `insufficient_evidence`), the baseline brief, and the allowlist.
- Proposal must name exactly ONE field from the allowlist
  (`motion`, `camera`, `audio_direction`, `negatives`) and a new
  value. Zero or >1 changed fields, identity/world/canon refs, or any
  frozen key (`model`, `profile`, `resolution`, `seed` + all frozen
  settings) → typed `InvalidProposal`. challenger uses the same
  seed/model/profile/resolution/identity/world refs as baseline.
- Estimator returns `{gpu_minutes, disk_gb}` for both variants;
  must fit `max_gpu_minutes` and usable disk
  (`max_disk_gb - reserve_disk_gb`) or fail closed with
  `ResourceOverrun` BEFORE any generation seam. The director never
  renders; `next_action` only names the seam.

## Non-goals

GLM wiring (proposer is injectable), rendering, GPU work, world-model
persistence format changes, GEPA/H3 behavior.
