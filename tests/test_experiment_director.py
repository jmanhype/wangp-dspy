"""tests/test_experiment_director.py — hermes-a1005314.

Controlled Experiment Director: pure single-variable experiment
planning on top of (baseline brief, frozen settings, world snapshot,
resource budget, prior signals). Spec:
docs/specs/controlled-experiment-director.md
"""
from __future__ import annotations

import json

import pytest

from experiments.director import (
    ControlledExperimentPlan,
    InvalidBudget,
    InvalidProposal,
    InvalidWorldSnapshot,
    ResourceOverrun,
    ResourceBudget,
    WorldSnapshot,
    plan_controlled_experiment,
)

VALID_HASH = "a" * 64
OTHER_HASH = "b" * 64

BASELINE = {
    "subject": "a lone figure crosses a rain-slick alley",
    "motion": "walking at a steady pace, coat trailing",
    "camera": "static medium shot from across the street",
    "style": "16mm ektachrome archival footage, heavy grain",
    "audio_direction": "rain and distant traffic only",
    "negatives": "no text overlays, no day-for-night",
    "identity_lock": "tall silhouette, long coat, hat brim shadow",
    "canon_citations": ["alley-intro.md#L4"],
}

FROZEN = {
    "model": "h3",
    "profile": "3",
    "resolution": "fhd",
    "seed": 1234,
    "attention": "sdpa",
    "process": True,
}


def make_world(**over):
    kw = dict(
        world_id="wd-oa4i-world",
        version=1,
        continuity_refs=("alley", "rain"),
        identity_lock="tall silhouette, long coat, hat brim shadow",
        invariants=("no proper nouns", "16mm grain"),
        source_hash=VALID_HASH,
    )
    kw.update(over)
    return WorldSnapshot(**kw)


def make_budget(**over):
    kw = dict(max_gpu_minutes=60.0, max_disk_gb=40.0, reserve_disk_gb=10.0)
    kw.update(over)
    return ResourceBudget(**kw)


def make_proposer(field="motion", value="striding fast, splashing through puddles",
                  calls=None):
    def proposer(context):
        if calls is not None:
            calls.append(context)
        return {"changed_field": field, "new_value": value,
                "rationale": "test single-variable proposal"}
    return proposer


def make_estimator(gpu=10.0, disk=20.0, calls=None):
    def estimator(baseline_spec, challenger_spec):
        if calls is not None:
            calls.append((baseline_spec, challenger_spec))
        return {"gpu_minutes": gpu, "disk_gb": disk}
    return estimator


# ---------------------------------------------------------------- world

def test_world_snapshot_requires_64_hex_source_hash():
    for bad in ("", "z" * 64, "a" * 63, "A" * 64, "aB" * 32):
        with pytest.raises(InvalidWorldSnapshot):
            make_world(source_hash=bad)


def test_world_snapshot_canonical_round_trip_deterministic():
    w = make_world()
    c1, c2 = w.canonical(), make_world().canonical()
    assert c1 == c2
    assert json.loads(c1)["world_id"] == "wd-oa4i-world"


# ---------------------------------------------------------------- budget

@pytest.mark.parametrize("kw", [
    dict(max_gpu_minutes=0), dict(max_gpu_minutes=-1),
    dict(max_disk_gb=0), dict(max_disk_gb=-5),
    dict(reserve_disk_gb=-1),
    dict(max_disk_gb=10.0, reserve_disk_gb=10.0),
    dict(max_variants=1), dict(max_variants=0),
])
def test_invalid_budgets_rejected(kw):
    with pytest.raises(InvalidBudget):
        make_budget(**kw)


def test_budget_defaults_and_max_variants():
    b = ResourceBudget(max_gpu_minutes=10.0, max_disk_gb=20.0)
    assert b.max_variants == 2 and b.reserve_disk_gb == 0.0


# ---------------------------------------------------------------- plan

def test_valid_one_field_challenger_two_specs_and_stable_hash():
    plan = plan_controlled_experiment(
        baseline_brief=BASELINE, frozen_settings=FROZEN,
        world=make_world(), budget=make_budget(),
        proposer=make_proposer(),
        resource_estimator=make_estimator())
    assert isinstance(plan, ControlledExperimentPlan)
    specs = plan.to_generation_specs()
    assert len(specs) == 2
    for spec in specs:
        for k, v in FROZEN.items():
            assert spec[k] == v
        assert spec["seed"] == 1234
        assert spec["identity_lock"] == BASELINE["identity_lock"]
        assert spec["canon_citations"] == BASELINE["canon_citations"]
        assert spec["world_ref"] == VALID_HASH
    b, c = specs
    assert b["motion"] == BASELINE["motion"]
    assert c["motion"] == "striding fast, splashing through puddles"
    # everything else identical
    diff = {k for k in set(b) | set(c) if b.get(k) != c.get(k)}
    assert diff == {"motion", "role"}
    assert {s["role"] for s in specs} == {"baseline", "challenger"}
    assert plan.changed_field == "motion"
    assert plan.plan_hash == plan.__class__.compute_hash(plan).plan_hash
    again = plan_controlled_experiment(
        baseline_brief=BASELINE, frozen_settings=FROZEN,
        world=make_world(), budget=make_budget(),
        proposer=make_proposer(),
        resource_estimator=make_estimator())
    assert again.canonical() == plan.canonical()
    assert again.plan_hash == plan.plan_hash and again.plan_id == plan.plan_id


@pytest.mark.parametrize("field", ["motion", "camera",
                                   "audio_direction", "negatives"])
def test_allowlist_fields_accepted(field):
    plan = plan_controlled_experiment(
        baseline_brief=BASELINE, frozen_settings=FROZEN,
        world=make_world(), budget=make_budget(),
        proposer=make_proposer(field=field, value="changed"),
        resource_estimator=make_estimator())
    assert plan.changed_field == field


@pytest.mark.parametrize("field,value", [
    ("subject", "new subject"),            # not in allowlist
    ("identity_lock", "someone else"),     # identity
    ("canon_citations", ["x.md"]),
    ("style", "digital clean"),
])
def test_identity_and_non_allowlist_mutations_rejected(field, value):
    with pytest.raises(InvalidProposal):
        plan_controlled_experiment(
            baseline_brief=BASELINE, frozen_settings=FROZEN,
            world=make_world(), budget=make_budget(),
            proposer=make_proposer(field=field, value=value),
            resource_estimator=make_estimator())


def test_zero_changed_fields_rejected():
    with pytest.raises(InvalidProposal):
        plan_controlled_experiment(
            baseline_brief=BASELINE, frozen_settings=FROZEN,
            world=make_world(), budget=make_budget(),
            proposer=lambda ctx: {"rationale": "no change"},
            resource_estimator=make_estimator())


def test_two_changed_fields_rejected():
    def proposer(ctx):
        return {"changes": [{"changed_field": "motion", "new_value": "a"},
                            {"changed_field": "camera", "new_value": "b"}]}
    with pytest.raises(InvalidProposal):
        plan_controlled_experiment(
            baseline_brief=BASELINE, frozen_settings=FROZEN,
            world=make_world(), budget=make_budget(),
            proposer=proposer, resource_estimator=make_estimator())


@pytest.mark.parametrize("frozen_key,bad_value", [
    ("model", "different-model"), ("profile", "9"),
    ("resolution", "hd"), ("seed", 999),
])
def test_frozen_setting_mutations_rejected(frozen_key, bad_value):
    def proposer(ctx):
        return {"changed_field": "motion", "new_value": "x",
                "settings_override": {frozen_key: bad_value}}
    with pytest.raises(InvalidProposal):
        plan_controlled_experiment(
            baseline_brief=BASELINE, frozen_settings=FROZEN,
            world=make_world(), budget=make_budget(),
            proposer=proposer, resource_estimator=make_estimator())


def test_proposer_called_once_with_world_and_prior_context():
    calls = []
    priors = {"audience": "insufficient_evidence",
              "qc_signals": []}
    plan = plan_controlled_experiment(
        baseline_brief=BASELINE, frozen_settings=FROZEN,
        world=make_world(), budget=make_budget(),
        proposer=make_proposer(calls=calls),
        resource_estimator=make_estimator(),
        prior_signals=priors)
    assert len(calls) == 1
    ctx = calls[0]
    assert json.loads(ctx["world"])["source_hash"] == VALID_HASH
    assert ctx["prior_signals"] == priors
    assert ctx["baseline_brief"] == BASELINE
    assert set(ctx["allowlist"]) == {"motion", "camera",
                                     "audio_direction", "negatives"}
    assert ctx["frozen_settings"] == FROZEN
    assert plan.evidence_state == "insufficient_evidence"
    # no metric invented anywhere in the plan
    assert "improvement" not in plan.canonical()


def test_missing_priors_reported_as_insufficient_evidence():
    plan = plan_controlled_experiment(
        baseline_brief=BASELINE, frozen_settings=FROZEN,
        world=make_world(), budget=make_budget(),
        proposer=make_proposer(), resource_estimator=make_estimator())
    assert plan.evidence_state == "insufficient_evidence"


def test_available_priors_passed_through_without_improvement_claim():
    plan = plan_controlled_experiment(
        baseline_brief=BASELINE, frozen_settings=FROZEN,
        world=make_world(), budget=make_budget(),
        proposer=make_proposer(), resource_estimator=make_estimator(),
        prior_signals={"audience": {"retention_pct": 41.2}})
    assert plan.prior_signals == {"audience": {"retention_pct": 41.2}}
    assert "improvement" not in plan.canonical()


# ---------------------------------------------------------------- resources

def test_budget_overrun_rejected_before_generation_seam():
    est_calls = []
    with pytest.raises(ResourceOverrun):
        plan_controlled_experiment(
            baseline_brief=BASELINE, frozen_settings=FROZEN,
            world=make_world(), budget=make_budget(max_gpu_minutes=5.0),
            proposer=make_proposer(),
            resource_estimator=make_estimator(gpu=10.0, calls=est_calls))
    assert len(est_calls) == 1  # estimator consulted, plan not produced
    with pytest.raises(ResourceOverrun):
        plan_controlled_experiment(
            baseline_brief=BASELINE, frozen_settings=FROZEN,
            world=make_world(),
            budget=make_budget(max_disk_gb=25.0, reserve_disk_gb=10.0),
            proposer=make_proposer(),
            resource_estimator=make_estimator(disk=20.0))
    # usable = 15 < 20


def test_budget_exactly_fitting_is_accepted():
    plan = plan_controlled_experiment(
        baseline_brief=BASELINE, frozen_settings=FROZEN,
        world=make_world(), budget=make_budget(max_gpu_minutes=10.0),
        proposer=make_proposer(),
        resource_estimator=make_estimator(gpu=10.0, disk=30.0))
    assert plan.predicted_resources == {"gpu_minutes": 10.0,
                                        "disk_gb": 30.0}
    assert plan.next_action == "generate_two_variants"


# ---------------------------------------------------------------- determinism

def test_canonical_round_trip_deterministic():
    plan = plan_controlled_experiment(
        baseline_brief=BASELINE, frozen_settings=FROZEN,
        world=make_world(), budget=make_budget(),
        proposer=make_proposer(), resource_estimator=make_estimator())
    canon = plan.canonical()
    reloaded = json.loads(canon)
    assert reloaded["plan_id"] == plan.plan_id
    assert reloaded["plan_hash"] == plan.plan_hash
    assert reloaded["world"]["source_hash"] == VALID_HASH


# ---------------------------------------------------------------- preservation

def test_generic_gepa_h3_path_untouched():
    """The director must not import or alter the GEPA/H3 baseline path."""
    import experiments.director as d
    src = open(d.__file__).read()
    for banned in ("run_baseline_then_gepa", "qc_feedback",
                   "render_qc", "wangp_adapter"):
        assert banned not in src
