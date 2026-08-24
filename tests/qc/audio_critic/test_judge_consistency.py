"""RED tests: judge consistency — sampled defaults + median ensemble.

Live evidence: greedy decode gave perfect determinism but
INVERTED ordering (operator's best take 8/40, mediocre 35) —
classic greedy degeneration on judge tasks.

(1) generation_kwargs() DEFAULT: do_sample=True, temperature=0.3,
    top_p=1.0 (greedy still reachable via caller override).
(2) /critique ensemble: run_critique 3x @ temp 0.3, score =
    MEDIAN; prose from the median-scoring run; scores_list +
    ensemble=true in the response; AUDIO_CRITIC_ENSEMBLE env-tuned
    (default 3); 1 = old single-shot behavior.
"""
import os

import pytest

from qc.audio_critic.criticize import generation_kwargs


# ── (1) new sampled defaults ───────────────────────────────────────

def test_defaults_now_sampled_temp_03():
    kw = generation_kwargs()
    assert kw["do_sample"] is True
    assert kw["temperature"] == 0.3
    assert kw["top_p"] == 1.0
    assert kw["max_new_tokens"] == generation_kwargs()["max_new_tokens"]


def test_greedy_override_seam_intact():
    merged = {**generation_kwargs(), "do_sample": False}
    assert merged["do_sample"] is False


# ── (2) ensemble aggregation ───────────────────────────────────────

from qc.audio_critic.criticize import ensemble_scores


def test_median_odd_list_picks_middle():
    assert ensemble_scores([10, 35, 40]) == 35
    assert ensemble_scores([40, 8, 35]) == 35
    assert ensemble_scores([1, 2, 100]) == 2


def test_median_of_median_run_picks_its_prose():
    from qc.audio_critic.criticize import aggregate_ensemble
    runs = [
        {"score": 40, "prose": "high"},
        {"score": 8, "prose": "low"},
        {"score": 35, "prose": "mid"},
    ]
    out = aggregate_ensemble(runs)
    assert out["score"] == 35
    assert out["prose"] == "mid"
    assert out["scores_list"] == [40, 8, 35]
    assert out["ensemble"] is True


def test_ensemble_size_env_tunable_default_3(monkeypatch):
    from qc.audio_critic import service
    monkeypatch.delenv("AUDIO_CRITIC_ENSEMBLE", raising=False)
    assert service.ensemble_size() == 3
    monkeypatch.setenv("AUDIO_CRITIC_ENSEMBLE", "1")
    assert service.ensemble_size() == 1
    monkeypatch.setenv("AUDIO_CRITIC_ENSEMBLE", "5")
    assert service.ensemble_size() == 5


def test_ensemble_1_single_shot_backward_compat(monkeypatch):
    """AUDIO_CRITIC_ENSEMBLE=1 -> run_critique called exactly once,
    response carries the single score, ensemble=false."""
    monkeypatch.setenv("AUDIO_CRITIC_ENSEMBLE", "1")
    from qc.audio_critic import service
    calls = []

    def fake_gen(prompt, **kw):
        calls.append(kw)
        return ("The vocals are clear and on-beat. I would rate "
                "the flow, timing, and vocal clarity of this track "
                "as 36 out of 40.")

    from qc.audio_critic.service import _run_ensemble
    out = _run_ensemble("music", fake_gen,
                        audio=_tiny_waveform(),
                        size=service.ensemble_size())
    assert len(calls) == 1
    assert out["ensemble"] is False
    assert out["scores_list"] == [36]


def test_ensemble_3_runs_three_times_median(monkeypatch):
    scores = iter([36, 10, 36])

    def fake_gen(prompt, **kw):
        s = next(scores)
        word = {36: "good", 10: "bad"}[s]
        return (f"The vocals are {word} and on-beat. I would rate "
                f"the flow, timing, and vocal clarity of this track "
                f"as {s} out of 40.")

    from qc.audio_critic.service import _run_ensemble
    out = _run_ensemble("music", fake_gen,
                        audio=_tiny_waveform(), size=3)
    assert out["score"] == 36
    assert out["scores_list"] == [36, 10, 36]
    assert out["ensemble"] is True


def _tiny_waveform():
    import numpy as np
    return np.zeros(160, dtype="float32")


# ── (3) deps declared ──────────────────────────────────────────────

def test_qc_gpu_extra_declares_accelerate_and_soundfile():
    import tomllib
    with open("pyproject.toml", "rb") as fh:
        proj = tomllib.load(fh)
    extra = proj["project"]["optional-dependencies"]["qc-gpu"]
    assert any("accelerate" == d.split(">=")[0].split("<")[0].strip()
               or d.startswith("accelerate") for d in extra)
    assert any(d.startswith("soundfile") for d in extra)
