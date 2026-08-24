"""WD-c4uh RED tests: MultiShotAssembler — shot chain, continuity lock,
mistake-lock. Pure logic; DummyLM only where an LM is involved at all.
"""
import pytest

from predict.prompt_director import RenderBrief
from predict.profile_selector import ProfileDecision
from predict.assembler import (
    AssembledChain, ChainValidationError, MultiShotAssembler, ShotPlan,
)

DECISION = ProfileDecision(
    model="h3", resolution="768p", shot_length_frames=176,
    seed_policy="fixed_per_story", wangp_profile="profile3")

STYLE_A = "16mm Ektachrome archival grain, warm faded tones"
STYLE_A2 = "16mm Ektachrome archival grain, warm faded tones"  # verbatim
STYLE_B = "clean digital 4K, cool neutral tones"


def _brief(subject="astronaut, cracked visor", motion="slow head turn",
           camera="dolly in", style=STYLE_A):
    return RenderBrief(subject=subject, motion=motion, camera=camera,
                       style=style)


def _shot(terminal_state, *, style=STYLE_A, subject="astronaut, cracked visor",
          deviations=(), motion="slow head turn"):
    return ShotPlan(
        brief=_brief(style=style, subject=subject, motion=motion),
        decision=DECISION,
        terminal_state=terminal_state,
        declared_deviations=tuple(deviations))


# ── 1: ShotPlan schema ───────────────────────────────────────────────────

def test_shot_plan_frozen():
    sp = _shot("astronaut facing right, visor cracked")
    with pytest.raises(Exception):
        sp.terminal_state = "x"


def test_shot_plan_rejects_empty_terminal_state():
    with pytest.raises(Exception):
        ShotPlan(brief=_brief(), decision=DECISION,
                 terminal_state="  ", declared_deviations=())


def test_shot_plan_rejects_empty_deviation_strings():
    with pytest.raises(Exception):
        ShotPlan(brief=_brief(), decision=DECISION,
                 terminal_state="ok", declared_deviations=("ok", ""))


# ── 2: chain bounds 2-20 ─────────────────────────────────────────────────

def _chain(n, **kw):
    """Fixture: shot i's subject carries shot i-1's terminal key term,
    so the chain rule is satisfied by construction."""
    shots = []
    prev_term = None
    for i in range(n):
        subject = prev_term if prev_term else f"subject {i} anchor"
        terminal = f"subject {i + 1} anchor"
        shots.append(_shot(terminal, subject=subject, **kw))
        prev_term = terminal
    return MultiShotAssembler().assemble(shots)


def test_empty_chain_rejected():
    with pytest.raises(ChainValidationError):
        MultiShotAssembler().assemble([])


def test_single_shot_rejected():
    with pytest.raises(ChainValidationError):
        _chain(1)


def test_two_shot_chain_ok():
    chain = _chain(2)
    assert isinstance(chain, AssembledChain)
    assert len(chain.shots) == 2
    assert chain.continuity_digest


def test_chain_over_20_rejected():
    with pytest.raises(ChainValidationError):
        _chain(21)


def test_chain_exactly_20_ok():
    assert len(_chain(20).shots) == 20


# ── 3: continuity lock ───────────────────────────────────────────────────

def test_style_descriptor_must_carry_verbatim():
    """Continuity lock: the style descriptor carries VERBATIM between
    consecutive shots. A changed style mid-chain is a typed violation."""
    shots = [_shot("s0 end", style=STYLE_A), _shot("s1 end", style=STYLE_B)]
    with pytest.raises(ChainValidationError) as ei:
        MultiShotAssembler().assemble(shots)
    assert "style" in str(ei.value).lower()


def test_style_verbatim_passes():
    shots = [_shot("subject 1 anchor", subject="subject 0 anchor", style=STYLE_A),
             _shot("subject 2 anchor", subject="subject 1 anchor", style=STYLE_A2)]
    chain = MultiShotAssembler().assemble(shots)
    assert len(chain.shots) == 2


def test_subject_anchor_consistency():
    """The subject anchor (first key noun phrase) must be consistent
    across the chain; a drifting subject is a typed violation."""
    shots = [_shot("s0 end", subject="astronaut, cracked visor"),
             _shot("s1 end", subject="a red sports car on salt flats")]
    with pytest.raises(ChainValidationError) as ei:
        MultiShotAssembler().assemble(shots)
    assert "subject" in str(ei.value).lower()


# ── 4: end-state chaining rule ───────────────────────────────────────────

def test_end_state_chaining_rule_documented_and_enforced():
    """Rule: shot N+1's opening (its brief's motion) must continue from
    shot N's terminal_state — explicit continuation match: the FIRST
    key term of shot N's terminal_state must appear in shot N+1's
    subject or motion (continuation carries the state forward)."""
    good = [
        _shot("astronaut mid-turn, dust rising"),
        ShotPlan(brief=_brief(subject="astronaut mid-turn, dust rising",
                              motion="completes the turn to camera"),
                 decision=DECISION,
                 terminal_state="astronaut facing camera",
                 declared_deviations=()),
    ]
    chain = MultiShotAssembler().assemble(good)
    assert len(chain.shots) == 2


def test_end_state_chaining_violation_caught():
    bad = [
        _shot("astronaut mid-turn, dust rising"),
        ShotPlan(brief=_brief(subject="a diner at midnight, neon sign",
                              motion="camera pans across the counter"),
                 decision=DECISION,
                 terminal_state="diner exterior, dawn",
                 declared_deviations=()),
    ]
    with pytest.raises(ChainValidationError) as ei:
        MultiShotAssembler().assemble(bad)
    assert "terminal" in str(ei.value).lower() or "chain" in str(ei.value).lower()


# ── 5: mistake-lock ──────────────────────────────────────────────────────

def test_mistake_lock_passthrough():
    """Declared deviations are pinned canon: the assembler MUST accept
    them verbatim (recorded in the digest) and never 'correct' them."""
    dev = ("six fingers on left glove (intentional canon deviation)",)
    shots = [_shot("subject 1 anchor", subject="subject 0 anchor", deviations=dev),
             _shot("subject 2 anchor", subject="subject 1 anchor", deviations=dev)]
    chain = MultiShotAssembler().assemble(shots)
    assert chain.shots[0].declared_deviations == dev  # pinned verbatim
    # ...and recorded: same chain WITHOUT the declaration digests differ
    plain = MultiShotAssembler().assemble([
        _shot("subject 1 anchor", subject="subject 0 anchor"),
        _shot("subject 2 anchor", subject="subject 1 anchor")])
    assert chain.continuity_digest != plain.continuity_digest


def test_undeclared_deviation_is_not_special():
    """Without declaration, nothing changes — deviations are pure
    metadata; QC interplay is out of scope here."""
    chain = _chain(2)
    assert all(not s.declared_deviations for s in chain.shots)


# ── 6: continuity digest ─────────────────────────────────────────────────

def test_digest_changes_when_chain_changes():
    d1 = _chain(2).continuity_digest
    shots = [
        _shot("subject 1 anchor", subject="subject 0 anchor"),
        _shot("totally different end", subject="subject 1 anchor",
              motion="a different movement entirely"),
    ]
    d2 = MultiShotAssembler().assemble(shots).continuity_digest
    assert d1 != d2


def test_digest_stable_for_identical_chains():
    assert _chain(2).continuity_digest == _chain(2).continuity_digest


# ── GLM minors: M1 annotation + M3 min key-term length ───────────────────

def test_m3_degenerate_short_key_term_rejected():
    # terminal_state whose key term is < 3 chars cannot carry continuity
    import pytest as _pytest
    from predict.assembler import (ChainValidationError, MultiShotAssembler,
                                      ShotPlan)
    from predict.prompt_director import RenderBrief
    from predict.profile_selector import ProfileDecision
    brief = RenderBrief(subject="kaiju", motion="wades ashore",
                        camera="low wide", style="grainy 16mm")
    dec = ProfileDecision(model="h3", resolution="768p",
                          shot_length_frames=96,
                          seed_policy="fixed_per_story",
                          wangp_profile="profile3")
    s1 = ShotPlan(brief=brief, decision=dec, terminal_state="a",
                  declared_deviations=())
    s2 = ShotPlan(brief=brief, decision=dec, terminal_state="kaiju rampaging",
                  declared_deviations=())
    with _pytest.raises(ChainValidationError):
        MultiShotAssembler().assemble((s1, s2))
