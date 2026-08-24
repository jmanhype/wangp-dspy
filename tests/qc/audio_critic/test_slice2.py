"""Audio critic slice 2 RED tests: criticize core + FastAPI service.

Contract: docs/PROPOSAL_audio_critic_service.md. All tests use a
FAKE model callable + recorded generations — no GPU, no network.
Divergences noted in the PR body, not here.
"""
import base64
import json
import threading
import time

import pytest
from fastapi.testclient import TestClient

from qc.audio_critic.criticize import (
    NUDGE, criticize_once, run_critique, assemble_conversation,
)
from qc.audio_critic.schema import AudioCriticError
from qc.audio_critic.service import (
    MAX_AUDIO_SECONDS, MAX_QUEUE, app, build_app,
)

CLEAN = ("The vocals are clear and on-beat. I would rate the flow, "
         "timing, and vocal clarity of this track as 36 out of 40.")
MALFORMED = "Nice track! Sounds pleasant overall, no complaints."
def _tiny_wav(seconds: float = 0.01) -> bytes:
    """Real 16kHz mono 16-bit WAV — /critique now DECODES the
    payload (fix/audio-critic-pipe-waveform); fake bytes 422."""
    import io as _io
    import struct as _struct
    import wave as _wave
    n = int(seconds * 16000)
    buf = _io.BytesIO()
    with _wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes(b"".join(
            _struct.pack("<h", (i % 100) * 100) for i in range(n)))
    return buf.getvalue()


B64 = base64.b64encode(_tiny_wav()).decode()


def test_assemble_conversation_matches_factory_shape():
    conv = assemble_conversation(
        "music", audio_path="/a/x.wav", reference_path="/r/ref.wav")
    assert conv[0]["role"] == "user"
    kinds = [c["type"] for c in conv[0]["content"]]
    assert kinds == ["audio", "audio", "text"]  # ref first, like factory
    conv2 = assemble_conversation("music", audio_path="/a/x.wav")
    assert [c["type"] for c in conv2[0]["content"]] == ["audio", "text"]
    # the text part carries the profile's (byte-identical) prompt
    from qc.audio_critic.profiles import MUSIC_SYSTEM_PROMPT
    text = [c for c in conv[0]["content"] if c["type"] == "text"][0]
    assert text["text"] == MUSIC_SYSTEM_PROMPT


def test_criticize_once_returns_prose_and_structured():
    out = criticize_once("music", CLEAN, model="fake")
    assert out["prose"] == CLEAN
    assert out["structured"]["score"] == 36
    assert out["structured"]["parse_ok"] is True


def test_run_critique_clean_first_try_no_retry():
    calls = []

    def gen(prompt, **kw):
        calls.append(prompt)
        return CLEAN

    out = run_critique("music", gen)
    assert len(calls) == 1
    assert out["record"]["score"] == 36
    assert out["retried"] is False


def test_run_critique_malformed_retries_once_with_nudge():
    calls = []

    def gen(prompt, **kw):
        calls.append(prompt)
        return CLEAN if len(calls) == 2 else MALFORMED

    out = run_critique("music", gen)
    assert len(calls) == 2
    assert NUDGE in calls[1]            # nudge appended on retry
    assert out["retried"] is True
    assert out["record"]["score"] == 36


def test_run_critique_persistent_malformed_typed_error():
    def gen(prompt, **kw):
        return MALFORMED

    with pytest.raises(AudioCriticError, match="parse"):
        run_critique("music", gen)


# ── service ───────────────────────────────────────────────────────

@pytest.fixture()
def client():
    app = build_app(generate=mock_generate, audio_seconds=lambda b: 1.0)
    return TestClient(app)


def mock_generate(prompt, **kw):
    return CLEAN


def test_health_reports_model_and_queue(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["model_loaded"] is True
    assert r.json()["queue_depth"] == 0


def test_critique_ok(client):
    r = client.post("/critique", json={
        "audio_b64": B64, "profile": "music", "mime": "audio/wav"})
    assert r.status_code == 200
    body = r.json()
    assert body["schema"] == "audio-critic/1"
    assert body["profile"] == "music"
    assert body["score"] == 36
    assert body["parse_ok"] is True


def test_unknown_profile_typed_422(client):
    r = client.post("/critique", json={
        "audio_b64": B64, "profile": "poetry", "mime": "audio/wav"})
    assert r.status_code == 422
    assert "profile" in r.json()["detail"]


def test_audio_over_90s_rejected(client):
    app2 = build_app(generate=mock_generate,
                     audio_seconds=lambda b: 91.0)
    r = TestClient(app2).post("/critique", json={
        "audio_b64": B64, "profile": "music", "mime": "audio/wav"})
    assert r.status_code == 422
    assert "90" in r.json()["detail"]


def test_lock_serializes_concurrent_critiques(monkeypatch):
    # ensemble off for THIS test: it pins lock serialization, not
    # judge aggregation (ensemble=3 would triplicate start/end)
    monkeypatch.setenv("AUDIO_CRITIC_ENSEMBLE", "1")
    order = []
    app = build_app(generate=lambda p, **k: slow_gen(order),
                    audio_seconds=lambda b: 1.0)
    client = TestClient(app)
    results = []

    def slow_gen(order):
        order.append("start")
        time.sleep(0.15)
        order.append("end")
        return CLEAN

    def post():
        r = client.post("/critique", json={
            "audio_b64": B64, "profile": "music",
            "mime": "audio/wav"})
        results.append(r.status_code)

    threads = [threading.Thread(target=post) for _ in range(3)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert results == [200, 200, 200]
    # serialized: no interleaved start/start
    assert order == ["start", "end", "start", "end", "start", "end"]


def test_queue_overflow_returns_503():
    app = build_app(generate=lambda p, **k: (time.sleep(0.3) or CLEAN),
                    audio_seconds=lambda b: 1.0)
    client = TestClient(app)
    codes = []

    def post():
        codes.append(client.post("/critique", json={
            "audio_b64": B64, "profile": "music",
            "mime": "audio/wav"}).status_code)

    threads = [threading.Thread(target=post)
               for _ in range(MAX_QUEUE + 3)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert 200 in codes
    assert codes.count(503) >= 1


def test_max_constants_pinned():
    assert MAX_AUDIO_SECONDS == 90
    assert MAX_QUEUE == 8


# ── GLM F1 (MEDIUM): pre-decode request size cap ──────────────────

def test_oversized_audio_b64_rejected_413_model_not_invoked():
    """RED (GLM review PR #44 F1): len(audio_b64) beyond the cap is
    rejected with typed 413 BEFORE base64.b64decode — the model
    callable must never see the request."""
    from qc.audio_critic.service import MAX_B64_CHARS
    called = []

    def gen(prompt, **kw):
        called.append(prompt)
        return CLEAN

    app = build_app(generate=gen, audio_seconds=lambda b: 1.0)
    r = TestClient(app).post("/critique", json={
        "audio_b64": "A" * (MAX_B64_CHARS + 1),
        "profile": "music", "mime": "audio/wav"})
    assert r.status_code == 413
    assert called == []           # model NOT invoked
    assert "4 MB" in r.json()["detail"] or "b64" in r.json()["detail"]


def test_b64_cap_env_tunable(monkeypatch):
    monkeypatch.setenv("AUDIO_CRITIC_MAX_B64", "100")
    import importlib
    import qc.audio_critic.service as svc
    importlib.reload(svc)
    assert svc.MAX_B64_CHARS == 100
    monkeypatch.delenv("AUDIO_CRITIC_MAX_B64")
    importlib.reload(svc)  # restore for other tests
