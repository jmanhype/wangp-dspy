"""experiments/director.py — Controlled Experiment Director (hermes-a1005314).

Pure, generation-ready experiment planner: turns a baseline
RenderBrief-like mapping + frozen render settings + a WorldSnapshot +
a ResourceBudget + read-only prior signals into a SINGLE-variable
controlled experiment plan (baseline vs challenger). It never renders;
`next_action` only names the generation seam. Spec:
docs/specs/controlled-experiment-director.md
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field, asdict
from typing import Any, Callable, Mapping

_HEX64_RE = re.compile(r"^[0-9a-f]{64}$")

# Creative fields a proposal may change — everything else is identity,
# world, canon, or a frozen render setting.
ALLOWED_CREATIVE_FIELDS = frozenset(
    ("motion", "camera", "audio_direction", "negatives"))

# Frozen keys pinned to parity between variants regardless of what the
# proposer returns.
PINNED_FROZEN_KEYS = ("model", "profile", "resolution", "seed")


class DirectorError(ValueError):
    """Typed base for director failures (fail closed, loud)."""


class InvalidWorldSnapshot(DirectorError):
    pass


class InvalidBudget(DirectorError):
    pass


class InvalidProposal(DirectorError):
    pass


class ResourceOverrun(DirectorError):
    pass


def _canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, default=_json_default)


def _json_default(obj: Any) -> Any:
    if isinstance(obj, (tuple, set, frozenset)):
        return sorted(obj) if not isinstance(obj, tuple) else list(obj)
    if isinstance(obj, Mapping):
        return dict(obj)
    if hasattr(obj, "canonical"):
        return json.loads(obj.canonical())
    raise TypeError(f"not canonical-serializable: {type(obj)!r}")


@dataclass(frozen=True)
class WorldSnapshot:
    """Immutable typed world model reference. The 64-hex source hash
    pins the exact world state the experiment ran against."""
    world_id: str
    version: int
    continuity_refs: tuple
    identity_lock: str
    invariants: tuple
    source_hash: str

    def __post_init__(self) -> None:
        if not isinstance(self.world_id, str) or not self.world_id.strip():
            raise InvalidWorldSnapshot("world_id must be a nonempty string")
        if not isinstance(self.version, int) or isinstance(self.version, bool) \
                or self.version < 1:
            raise InvalidWorldSnapshot(
                f"version must be an int >= 1, got {self.version!r}")
        if not _HEX64_RE.match(self.source_hash or ""):
            raise InvalidWorldSnapshot(
                "source_hash is REQUIRED and must be exactly 64 lowercase "
                f"hex chars, got {self.source_hash!r}")
        for name in ("continuity_refs", "invariants"):
            v = getattr(self, name)
            if not isinstance(v, tuple):
                raise InvalidWorldSnapshot(
                    f"{name} must be a tuple of str, got {type(v)!r}")
            if any(not isinstance(r, str) for r in v):
                raise InvalidWorldSnapshot(f"{name} entries must be str")
        if not isinstance(self.identity_lock, str):
            raise InvalidWorldSnapshot("identity_lock must be str")

    def canonical(self) -> str:
        return _canonical_json({
            "world_id": self.world_id,
            "version": self.version,
            "continuity_refs": list(self.continuity_refs),
            "identity_lock": self.identity_lock,
            "invariants": list(self.invariants),
            "source_hash": self.source_hash,
        })


@dataclass(frozen=True)
class ResourceBudget:
    """Hard resource envelope for one controlled experiment."""
    max_variants: int = 2
    max_gpu_minutes: float = 0.0
    max_disk_gb: float = 0.0
    reserve_disk_gb: float = 0.0

    def __post_init__(self) -> None:
        if not isinstance(self.max_variants, int) \
                or isinstance(self.max_variants, bool) \
                or self.max_variants < 2:
            raise InvalidBudget(
                f"max_variants must be an int >= 2, got {self.max_variants!r}")
        for name in ("max_gpu_minutes", "max_disk_gb", "reserve_disk_gb"):
            v = getattr(self, name)
            if not isinstance(v, (int, float)) or isinstance(v, bool) \
                    or v < 0:
                raise InvalidBudget(
                    f"{name} must be a nonnegative number, got {v!r}")
        if self.max_gpu_minutes <= 0:
            raise InvalidBudget("max_gpu_minutes must be > 0")
        if self.max_disk_gb <= 0:
            raise InvalidBudget("max_disk_gb must be > 0")
        if self.reserve_disk_gb >= self.max_disk_gb:
            raise InvalidBudget(
                f"reserve_disk_gb ({self.reserve_disk_gb}) must leave usable "
                f"disk: it must be < max_disk_gb ({self.max_disk_gb})")

    @property
    def usable_disk_gb(self) -> float:
        return self.max_disk_gb - self.reserve_disk_gb


_SPEC_BRIEF_KEYS = ("subject", "motion", "camera", "style",
                    "audio_direction", "negatives", "identity_lock",
                    "canon_citations")


@dataclass(frozen=True)
class ControlledExperimentPlan:
    """Generation-ready single-variable experiment plan. Directly
    convertible to exactly two generation specs via to_generation_specs();
    the director itself never renders."""
    plan_id: str
    plan_hash: str
    baseline_spec: dict
    challenger_spec: dict
    changed_field: str
    old_value: Any
    new_value: Any
    target_metric: str
    rationale: str
    frozen_settings: dict
    world: WorldSnapshot
    world_ref: str
    predicted_resources: dict
    evidence_state: str
    prior_signals: dict
    next_action: str = "generate_two_variants"

    def to_generation_specs(self) -> list:
        return [dict(self.baseline_spec), dict(self.challenger_spec)]

    def canonical(self) -> str:
        return _canonical_json({
            "plan_id": self.plan_id,
            "plan_hash": self.plan_hash,
            "baseline_spec": self.baseline_spec,
            "challenger_spec": self.challenger_spec,
            "changed_field": self.changed_field,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "target_metric": self.target_metric,
            "rationale": self.rationale,
            "frozen_settings": self.frozen_settings,
            "world": json.loads(self.world.canonical()),
            "world_ref": self.world_ref,
            "predicted_resources": self.predicted_resources,
            "evidence_state": self.evidence_state,
            "prior_signals": self.prior_signals,
            "next_action": self.next_action,
        })

    @staticmethod
    def compute_hash(plan: "ControlledExperimentPlan"
                     ) -> "ControlledExperimentPlan":
        """Recompute the content hash over canonical content WITHOUT the
        hash-bearing fields themselves (id/hash excluded from digest)."""
        payload = json.loads(plan.canonical())
        payload.pop("plan_id"), payload.pop("plan_hash")
        plan_hash = hashlib.sha256(
            _canonical_json(payload).encode("utf-8")).hexdigest()
        plan_id = "cep-" + plan_hash[:12]
        return ControlledExperimentPlan(
            plan_id=plan_id, plan_hash=plan_hash,
            baseline_spec=plan.baseline_spec,
            challenger_spec=plan.challenger_spec,
            changed_field=plan.changed_field,
            old_value=plan.old_value, new_value=plan.new_value,
            target_metric=plan.target_metric, rationale=plan.rationale,
            frozen_settings=plan.frozen_settings, world=plan.world,
            world_ref=plan.world_ref,
            predicted_resources=plan.predicted_resources,
            evidence_state=plan.evidence_state,
            prior_signals=plan.prior_signals,
            next_action=plan.next_action)


def plan_controlled_experiment(
    baseline_brief: Mapping,
    frozen_settings: Mapping,
    world: WorldSnapshot,
    budget: ResourceBudget,
    proposer: Callable[[Mapping], Mapping],
    resource_estimator: Callable[[Mapping, Mapping], Mapping],
    prior_signals: Mapping | None = None,
    target_metric: str = "qc_score",
) -> ControlledExperimentPlan:
    """Plan one controlled generation experiment.

    Pure: the only external knowledge enters via the injected
    `proposer` (called EXACTLY once) and `resource_estimator`.
    Fails closed with typed errors on invalid world/budget/proposal
    or resource overrun — always BEFORE any generation seam.
    """
    if not isinstance(world, WorldSnapshot):
        raise InvalidWorldSnapshot(f"world must be WorldSnapshot, "
                                   f"got {type(world)!r}")
    if not isinstance(budget, ResourceBudget):
        raise InvalidBudget(f"budget must be ResourceBudget, "
                            f"got {type(budget)!r}")
    baseline_brief = dict(baseline_brief)
    frozen = dict(frozen_settings)
    for key in PINNED_FROZEN_KEYS:
        if key not in frozen:
            raise InvalidProposal(
                f"frozen settings must pin {key!r} for variant parity; "
                f"got keys {sorted(frozen)}")

    prior = dict(prior_signals) if prior_signals else {}
    evidence_state = (prior.get("audience") if isinstance(prior.get("audience"), str)
                      else ("available" if prior.get("audience")
                            else "insufficient_evidence"))
    # Read-only context handoff — never mutated, never augmented with
    # invented metrics.
    context = {
        "baseline_brief": baseline_brief,
        "frozen_settings": frozen,
        "world": world.canonical(),
        "prior_signals": prior if prior else {"audience":
                                              "insufficient_evidence"},
        "allowlist": sorted(ALLOWED_CREATIVE_FIELDS),
    }
    proposal = proposer(context)

    # ---- validate proposal: exactly ONE allowed creative field -------
    changes = []
    if proposal is None:
        raise InvalidProposal("proposer returned None; exactly one "
                              "allowlisted field must change")
    if isinstance(proposal, Mapping) and "changes" in proposal:
        changes = list(proposal["changes"])
    elif isinstance(proposal, Mapping) and "changed_field" in proposal \
            and proposal["changed_field"] is not None:
        changes = [{"changed_field": proposal["changed_field"],
                    "new_value": proposal.get("new_value")}]
    if not changes:
        raise InvalidProposal(
            "proposal changes ZERO fields — a controlled experiment needs "
            f"exactly one of {sorted(ALLOWED_CREATIVE_FIELDS)}")
    if len(changes) > 1:
        raise InvalidProposal(
            f"proposal changes {len(changes)} fields — a controlled "
            "experiment changes EXACTLY ONE field (isolate the variable)")
    changed_field = changes[0].get("changed_field")
    new_value = changes[0].get("new_value")
    if changed_field not in ALLOWED_CREATIVE_FIELDS:
        raise InvalidProposal(
            f"changed_field {changed_field!r} is outside the allowlist "
            f"{sorted(ALLOWED_CREATIVE_FIELDS)} — identity/world/canon/"
            "subject/style and every frozen setting must remain unchanged")
    if new_value is None or (isinstance(new_value, str)
                             and not new_value.strip()):
        raise InvalidProposal(
            f"new_value for {changed_field!r} must be nonempty")
    override = proposal.get("settings_override") if isinstance(
        proposal, Mapping) else None
    if override:
        raise InvalidProposal(
            f"frozen render settings are immutable; proposer attempted "
            f"settings_override for {sorted(dict(override))}")

    old_value = baseline_brief.get(changed_field)

    # ---- build the two specs: identical except the one field ---------
    def _spec(role: str, field_value) -> dict:
        spec = {k: baseline_brief[k] for k in _SPEC_BRIEF_KEYS
                if k in baseline_brief}
        spec[changed_field] = field_value
        spec.update(frozen)  # same model/profile/resolution/seed on both
        spec["world_ref"] = world.source_hash
        spec["role"] = role
        return spec

    baseline_spec = _spec("baseline", old_value)
    challenger_spec = _spec("challenger", new_value)

    # ---- resource gate: fail closed BEFORE the generation seam -------
    estimate = resource_estimator(baseline_spec, challenger_spec)
    try:
        gpu_minutes = float(estimate["gpu_minutes"])
        disk_gb = float(estimate["disk_gb"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ResourceOverrun(
            f"resource estimator returned unusable estimate "
            f"{estimate!r}: {exc}") from exc
    if gpu_minutes > budget.max_gpu_minutes:
        raise ResourceOverrun(
            f"predicted gpu_minutes {gpu_minutes} exceeds budget "
            f"{budget.max_gpu_minutes} — failing closed before generation")
    if disk_gb > budget.usable_disk_gb:
        raise ResourceOverrun(
            f"predicted disk_gb {disk_gb} exceeds usable disk "
            f"{budget.usable_disk_gb} (max {budget.max_disk_gb} - reserve "
            f"{budget.reserve_disk_gb}) — failing closed before generation")

    rationale = (proposal.get("rationale") if isinstance(proposal, Mapping)
                 else "") or "single-variable controlled experiment"

    plan = ControlledExperimentPlan(
        plan_id="pending", plan_hash="pending",
        baseline_spec=baseline_spec, challenger_spec=challenger_spec,
        changed_field=changed_field, old_value=old_value,
        new_value=new_value, target_metric=target_metric,
        rationale=rationale, frozen_settings=frozen, world=world,
        world_ref=world.source_hash,
        predicted_resources={"gpu_minutes": gpu_minutes,
                             "disk_gb": disk_gb},
        evidence_state=evidence_state, prior_signals=prior)
    return ControlledExperimentPlan.compute_hash(plan)
