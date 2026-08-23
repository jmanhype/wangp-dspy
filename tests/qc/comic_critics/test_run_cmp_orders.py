"""Regression: run_cmp order tuples must place gen in candidate slot matching gw2.

Found in production 2026-08-22: all three order tuples were slot-malformed,
so double-evaluated runs cancelled to exactly 0.5 win rate regardless of
judge opinion, and single-order local runs errored with "Missing video".
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from qc.comic_critics.core import Ref, Gen, run_cmp  # noqa: E402


class RecordingAgent:
    """Records (cand1, cand2) per call; votes candidate 2 always."""

    def __init__(self):
        self.calls = []

    def evaluate(self, u1, u2, lp1=None, lp2=None):
        c1, c2 = (lp1 or u1), (lp2 or u2)
        assert c1 and c2, f"empty candidate slot: u1={u1!r} u2={u2!r} lp1={lp1!r} lp2={lp2!r}"
        self.calls.append((c1, c2))
        return {"best_candidate": 2, "agent_name": "rec"}


def test_order_slots_double(monkeypatch=None):
    agent = RecordingAgent()
    ref = Ref("R", "/ref.mp4", "CH")
    gen = Gen("M", Path("/gen.mp4"))
    run_cmp(agent, [ref], [gen], "M", "CH", True, 0)
    assert len(agent.calls) == 2, agent.calls
    first, second = agent.calls
    assert first == ("/ref.mp4", "/gen.mp4"), first
    assert second == ("/gen.mp4", "/ref.mp4"), second
    # agent always votes #2; gen wins once (when it IS #2), loses once
    print("double-order slots OK:", first, second)


def test_order_slots_flipped(monkeypatch=None):
    agent = RecordingAgent()
    ref = Ref("R", "/ref.mp4", "CH")
    gen = Gen("M", Path("/gen.mp4"))
    # force rng flip: seed chosen so rng.random() < 0.5 -> elif branch replaces order
    import qc.comic_critics.core as core
    orig = core.random.Random
    class FlippedRng:
        def __init__(self, seed): pass
        def random(self): return 0.0  # 0.0 >= 0.5 is False -> elif NOT taken
    # use seed where elif triggers: need random() >= 0.5
    class TakeFlip(FlippedRng):
        def random(self): return 0.9
    core.random.Random = TakeFlip
    try:
        run_cmp(agent, [ref], [gen], "M", "CH", False, 0)
    finally:
        core.random.Random = orig
    assert agent.calls == [("/gen.mp4", "/ref.mp4")], agent.calls
    print("flipped-order slots OK:", agent.calls[0])


if __name__ == "__main__":
    test_order_slots_double()
    test_order_slots_flipped()
    print("ALL PASS")
