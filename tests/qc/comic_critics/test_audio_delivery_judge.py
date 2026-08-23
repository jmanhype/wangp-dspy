"""AudioDeliveryJudge RED tests (slice 4).

Contract: docs/PROPOSAL_audio_critic_service.md — the comic lane's
deaf-to-delivery gap. Same vote_pair interface as LocalVLLMJudge;
fake HTTP transport injected (slice-2 pattern) — no network, no
ffmpeg execution (argv asserted only).
"""
import json
import pathlib
from pathlib import Path

import pytest

from qc.audio_critic.profiles import PROFILES
from qc.comic_critics.judges import AudioDeliveryJudge
from qc.comic_critics.core import parse_vote


def _resp(body, status=200):
    class R:
        pass
    r = R()
    r.status_code = status
    r.text = json.dumps(body) if isinstance(body, dict) else body
    r.json = (lambda b=body: b) if isinstance(body, dict) else None
    return r


def _ok(score, flags=(), decision="pass"):
    return {"schema": "audio-critic/1", "profile": "delivery",
            "score": score, "score_scale": [0, 40], "flags": list(flags),
            "reason": "delivered with crisp timing",
            "decision": decision,
            "model": "Qwen/Qwen2-Audio-7B-Instruct",
            "parse_ok": True}


class FakeTransport:
    def __init__(self, responses):
        self.responses = list(responses)
        self.posts = []

    def post(self, url, json=None, timeout=None):
        self.posts.append({"url": url, "json": json, "timeout": timeout})
        r = self.responses.pop(0)
        if isinstance(r, Exception):
            raise r
        return r


VID1 = "/tmp/cand1.mp4"
VID2 = "/tmp/cand2.mp4"


def _judge(transport, ffmpeg=None):
    return AudioDeliveryJudge(
        transport=transport, ffmpeg=ffmpeg or FakeFfmpeg())


class FakeFfmpeg:
    def __init__(self):
        self.argvs = []

    def __call__(self, argv, timeout=None):
        self.argvs.append(list(argv))
        Path(argv[-1]).write_bytes(b"RIFFfake")  # the wav 'output"

        class P:
            returncode = 0
        return P()


# ── delivery rubric (profiles) ────────────────────────────────────

def test_delivery_rubric_in_profiles():
    p = PROFILES["delivery"]
    assert p["score_scale"] == [0, 40]
    assert p["flags"] == ["flat_delivery", "rushed_pacing",
                          "timing_off", "weak_commit", "mumbled"]
    assert p["decisions"] == ("pass", "revise", "reject")
    assert "delivery" in p["system_prompt"].lower()
    for word in ("pacing", "timing"):
        assert word in p["system_prompt"].lower()


# ── happy path: two candidates -> verdict machinery ───────────────

def test_vote_pair_happy_path_renders_voting_contract():
    t = FakeTransport([_resp(_ok(36)), _resp(_ok(22))])
    j = _judge(t)
    out = j.vote_pair("INSTR", VID1, VID2)
    assert out["best_candidate"] == 1
    assert out["raw_response"]
    parsed = parse_vote(out["raw_response"])
    assert parsed["best_candidate"] == 1
    assert "36" in out["raw_response"] and "22" in out["raw_response"]


def test_vote_pair_higher_score_candidate2_wins():
    t = FakeTransport([_resp(_ok(12)), _resp(_ok(38))])
    j = _judge(t)
    out = j.vote_pair("INSTR", VID1, VID2)
    assert out["best_candidate"] == 2


def test_service_request_shape():
    t = FakeTransport([_resp(_ok(30)), _resp(_ok(30))])
    j = _judge(t)
    j.vote_pair("INSTR", VID1, VID2)
    assert len(t.posts) == 2
    for p in t.posts:
        assert p["url"].endswith("/critique")
        assert p["json"]["profile"] == "delivery"
        assert p["json"]["mime"] == "audio/wav"
        assert p["json"]["audio_b64"]


# ── failure isolation ────────────────────────────────────────────

def test_service_500_deterministic_candidate1_fallback():
    t = FakeTransport([_resp("boom", status=500)] * 4)
    j = _judge(t)
    out = j.vote_pair("INSTR", VID1, VID2)
    assert out["best_candidate"] == 1
    assert out.get("error")


def test_service_timeout_deterministic_fallback():
    t = FakeTransport([TimeoutError("t")] * 4)
    j = _judge(t)
    out = j.vote_pair("INSTR", VID1, VID2)
    assert out["best_candidate"] == 1
    assert out.get("error")


def test_partial_service_failure_still_votes_on_successes():
    # candidate 1's critique fails, candidate 2 succeeds -> 2 wins
    # on the only available signal (documented fallback semantics)
    t = FakeTransport([_resp("err", status=503), _resp(_ok(35))])
    j = _judge(t)
    out = j.vote_pair("INSTR", VID1, VID2)
    assert out["best_candidate"] == 2
    assert out.get("error")  # the miss is noted, never silent


# ── URL candidates: graceful skip ─────────────────────────────────

def test_url_candidate_skips_audio_judging():
    t = FakeTransport([_resp(_ok(30))])
    j = _judge(t)
    out = j.vote_pair("INSTR", "http://x/v1.mp4", VID2)
    assert len(t.posts) == 1  # only the local candidate POSTed
    assert out.get("skipped") == ["1"]  # candidate 1 skipped, noted
    assert out["best_candidate"] in (1, 2)


def test_both_url_candidates_full_fallback():
    t = FakeTransport([])
    j = _judge(t)
    out = j.vote_pair("INSTR", "http://x/a.mp4", "http://x/b.mp4")
    assert len(t.posts) == 0
    assert out["best_candidate"] == 1
    # a full URL-skip is not an error — it is a clean, noted skip
    assert out["skipped"] == ["1", "2"]
    assert out["reasoning"] == "no audio critiques available"


# ── ffmpeg argv correctness (asserted, never executed) ───────────

def test_ffmpeg_extraction_argv():
    ff = FakeFfmpeg()
    t = FakeTransport([_resp(_ok(30)), _resp(_ok(30))])
    j = _judge(t, ffmpeg=ff)
    j.vote_pair("INSTR", VID1, VID2)
    assert len(ff.argvs) == 2
    for argv in ff.argvs:
        assert argv[0] == "ffmpeg"
        assert "-i" in argv
        assert "-ac" in argv and argv[argv.index("-ac") + 1] == "1"
        assert argv[argv.index("-ar") + 1] == "16000"
        assert "-t" in argv and argv[argv.index("-t") + 1] == "90"
        assert argv[-1].endswith(".wav")


def test_flag_vocab_passthrough_into_verdict():
    t = FakeTransport([_resp(_ok(36, flags=["rushed_pacing"])),
                       _resp(_ok(20, flags=["flat_delivery",
                                            "mumbled"]))])
    j = _judge(t)
    out = j.vote_pair("INSTR", VID1, VID2)
    assert "rushed_pacing" in out["raw_response"]
    assert "flat_delivery" in out["raw_response"]
