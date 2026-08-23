"""Unit tests for qc.comic_critics — recorded fixtures only, NO live API.

TDD: written RED first against the port spec.
"""
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from qc.comic_critics.core import (  # noqa: E402
    INSTRUCTIONS, Ref, Gen, load_critics, load_refs, parse_vote,
    run_cmp, metrics,
)

FIX = Path(__file__).parent / "fixtures"


# ── persona loading ──────────────────────────────────────────────────────

def test_load_critics_global_best():
    critics = load_critics(FIX / "global_best.json")
    assert len(critics) == 1
    c = critics[0]
    assert c["id"] == "Comedy_Critic_1"
    assert c["name"] == "Marcus Chen"
    # instruction template substitution: upstream replaces the
    # TASK-SPECIFIC placeholder with INSTRUCTIONS
    agent = None  # persona spec feeds agent constructor; see below
    assert "{TASK-SPECIFIC INSTRUCTIONS WILL BE INSERTED HERE}" in \
        c["content"]


def test_load_critics_channel_best_and_map():
    critics = load_critics(FIX / "channel_best.json")
    assert len(critics) == 5
    assert {c["id"] for c in critics} == {
        "Comedy_Critic_2", "Comedy_Critic_3", "Comedy_Critic_6",
        "Comedy_Critic_7", "Comedy_Critic_10"}
    d = json.loads((FIX / "channel_best.json").read_text())
    assert d["channel_leads_map"]["Key_&_Peele"] == "Comedy_Critic_2"


def test_load_critics_accepts_bare_list():
    assert load_critics(FIX / "bare_list.json") == [{"id": "X"}]


# ── vote parsing: the deterministic-fallback contract ────────────────────

GOOD = ("[VOTING START]\n\n[WINNER START]Candidate #2[WINNER END]\n\n"
        "[REVIEW START]\nGreat timing on the second one.\n[REVIEW END]\n\n"
        "[VOTING END]")

def test_parse_vote_good():
    v = parse_vote(GOOD)
    assert v["best_candidate"] == 2
    assert "timing" in v["reasoning"]
    assert "parse_error" not in v


def test_parse_vote_no_voting_block():
    """Malformed -> DETERMINISTIC candidate-1 fallback + parse_error
    (upstream used random.choice — that MUST be replaced)."""
    v = parse_vote("I liked the first one better honestly")
    assert v["best_candidate"] == 1
    assert v["parse_error"] == "missing_voting_block"
    assert v["reasoning"] == ""


def test_parse_vote_out_of_range_winner():
    v = parse_vote("[VOTING START]\n[WINNER START]Candidate #7[WINNER END]\n"
                   "[VOTING END]")
    assert v["best_candidate"] == 1
    assert v["parse_error"] == "winner_out_of_range"


def test_parse_vote_no_winner_tag():
    v = parse_vote("[VOTING START]\nI choose the second.\n[VOTING END]")
    assert v["best_candidate"] == 1
    assert v["parse_error"] == "winner_not_parsed"


def test_parse_vote_deterministic_across_calls():
    """The exact regression this port exists to fix: same malformed input
    ALWAYS yields the same fallback — no randomness."""
    outs = {json.dumps(parse_vote("garbage")) for _ in range(20)}
    assert len(outs) == 1


def test_parse_vote_n_candidates():
    v = parse_vote("[VOTING START]\n[WINNER START]Candidate #3[WINNER END]"
                   "\n[VOTING END]", n=3)
    assert v["best_candidate"] == 3


# ── ref loading (middle.txt contract) ────────────────────────────────────

def test_load_refs_middle_txt(tmp_path):
    p = tmp_path / "middle.txt"
    p.write_text(
        "# Chan_A\nvid1 https://youtu.be/abc12345678\n"
        "vid2 https://www.youtube.com/watch?v=xyz98765432\n\n"
        "# Chan_B\nvid3 https://youtu.be/qqq11122233\n")
    refs = load_refs(p)
    assert set(refs) == {"Chan_A", "Chan_B"}
    assert refs["Chan_A"][0].id == "vid1"
    assert refs["Chan_A"][0].url.endswith("abc12345678")
    assert refs["Chan_B"][0].channel == "Chan_B"


# ── run_cmp with a stub judge ────────────────────────────────────────────

class StubJudge:
    """Returns a fixed winner; records calls for order assertions."""
    def __init__(self, winner=2):
        self.winner = winner
        self.calls = []

    def evaluate(self, u1, u2, lp1=None, lp2=None, **kw):
        self.calls.append((u1, u2, lp1, lp2))
        return {"best_candidate": self.winner, "reasoning": "stub",
                "agent_name": "stub"}


def test_run_cmp_win_rate_and_fields():
    refs = [Ref("r1", "https://youtu.be/aaaaaaaaaaa", "Ch")]
    gens = [Gen("ours", Path("/x/a.mp4"))]
    j = StubJudge(2)
    row = run_cmp(j, refs, gens, "ours", "Ch",
                  double=False, delay=0, order_seed=0)
    assert row["trials"] == 1
    # order determines which side candidate-2 is; derive from the stub's
    # recorded call: candidate slots are (lp1 or u1) and (lp2 or u2).
    u1, u2, lp1, lp2 = j.calls[0]
    cand1, cand2 = (lp1 or u1), (lp2 or u2)
    gen_is_two = cand2 == str(gens[0].path)
    call = json.loads(row["evaluation_calls"])[0]
    assert call["gen_wins"] == gen_is_two
    assert row["wins"] == int(gen_is_two)
    assert row["win_rate"] == float(gen_is_two)
    assert json.loads(row["method_video_ids"]) == ["a"]
    assert json.loads(row["reference_video_ids"]) == ["r1"]


def test_run_cmp_double_evaluation_both_orders():
    refs = [Ref("r1", "u", "Ch")]
    gens = [Gen("ours", Path("/x/a.mp4"))]
    row = run_cmp(StubJudge(1), refs, gens, "ours", "Ch",
                  double=True, delay=0, order_seed=0)
    assert row["trials"] == 2
    calls = json.loads(row["evaluation_calls"])
    # stub says candidate-1 both times: ref-first order => ref wins;
    # gen-first order => gen wins
    assert calls[0]["gen_wins"] is False
    assert calls[1]["gen_wins"] is True
    assert row["wins"] == 1


def test_run_cmp_seeded_order_is_deterministic():
    """Order flip uses a SEEDED RNG, never global random."""
    refs = [Ref("r1", "u", "Ch")]
    gens = [Gen("ours", Path("/x/a.mp4"))]
    j1, j2 = StubJudge(1), StubJudge(1)
    run_cmp(j1, refs, gens, "ours", "Ch", double=False, delay=0, order_seed=7)
    run_cmp(j2, refs, gens, "ours", "Ch", double=False, delay=0, order_seed=7)
    assert [c[:2] for c in j1.calls] == [c[:2] for c in j2.calls]


# ── metrics (baseline-comparable shapes) ─────────────────────────────────

def _row(eid, calls, method="ours", ch="Ch"):
    return {"method": method, "test_channel": ch, "win_rate": 0.0,
            "wins": 0, "trials": 0,
            "method_video_ids": "[]", "reference_video_ids": "[]",
            "evaluation_calls": json.dumps(calls),
            "input_tokens": 0, "output_tokens": 0, "gemini_outputs": "[]",
            "critic_id": eid, "critic_name": eid, "critic_set": "s"}


def test_metrics_all_wins():
    calls = [{"ref_id": "r", "gen_id": "g", "gen_wins": True}]
    m = metrics([_row("E1", calls), _row("E2", calls)])
    assert m["avg_win_rate"] == 1.0
    assert m["g_norm_inter"] == 0.0
    assert m["g_norm_intra"] == 0.0


def test_metrics_split():
    # two method videos (g1, g2) judged by two critics: g1 splits the
    # critics (intra variance), g2 splits the methods (inter variance)
    rows = [
        _row("E1", [{"ref_id": "r", "gen_id": "g1", "gen_wins": True},
                    {"ref_id": "r", "gen_id": "g2", "gen_wins": True}]),
        _row("E2", [{"ref_id": "r", "gen_id": "g1", "gen_wins": False},
                    {"ref_id": "r", "gen_id": "g2", "gen_wins": True}]),
    ]
    m = metrics(rows)
    assert m["avg_win_rate"] == 0.75
    assert m["g_norm_inter"] > 0.0


def test_metrics_empty():
    assert metrics([])["avg_win_rate"] == 0.0
