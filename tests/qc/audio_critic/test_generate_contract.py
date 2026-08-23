"""RED tests: canonical generate-contract at the run_critique seam.

Live 3090 traceback (Luna flag, PR #48): load_real_model's callable
did processor.apply_chat_template(<string>) -> AttributeError
'str' object has no attribute 'get' — run_critique passes a PROMPT
STR, the callable must build the chat conversation itself.
"""
import sys
import types

import pytest

from qc.audio_critic.criticize import (
    GenerateCallable, load_real_model, run_critique,
)


import base64 as _b64
import io as _io
import struct as _struct
import wave as _wave


def _tiny_wav(seconds: float = 0.01) -> bytes:
    """Real 16kHz mono wav — /critique now DECODES the payload."""
    n = int(seconds * 16000)
    buf = _io.BytesIO()
    with _wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes(b"".join(
            _struct.pack("<h", (i % 100) * 100) for i in range(n)))
    return buf.getvalue()


B64S = _b64.b64encode(_tiny_wav()).decode()

CLEAN = ("The delivery is crisp. I would rate it as 34 out of 40.")


def _fake_transformer_mods(captured):
    class FakeFeatureExtractor:
        sampling_rate = 16000

    class FakeProcessor:
        feature_extractor = FakeFeatureExtractor()

        def apply_chat_template(self, conv, **kw):
            captured["conv"] = conv
            return "tpl"

        def __call__(self, text=None, audio=None, **kw):
            captured["proc_audio"] = audio

            class T:
                def to(self, *a, **kw2):
                    return self

                def __iter__(self):
                    return iter([[1]])
            return {"input_ids": T()}

        def batch_decode(self, ids, **kw):
            return [CLEAN]

    class FakeModel:
        device = "cpu"

        def generate(self, **kw):
            captured["gen_kw"] = kw
            return [[1, 2, 3]]

    tfm = types.ModuleType("transformers")

    def fake_proc(model_id=None, **kw):
        captured["proc_model_id"] = model_id
        return FakeProcessor()

    def fake_model(model_id=None, **kw):
        captured["model_dtype"] = kw.get("torch_dtype")
        return FakeModel()
    tfm.AutoProcessor = type("AP", (),
                             {"from_pretrained": staticmethod(fake_proc)})
    tfm.Qwen2AudioForConditionalGeneration = type(
        "M", (), {"from_pretrained": staticmethod(fake_model)})
    torch = types.ModuleType("torch")
    torch.bfloat16 = "bf16"

    class _cm:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False
    torch.no_grad = lambda: _cm()
    return tfm, torch


def test_type_alias_exists_and_documented():
    """The seam shape is pinned by a named alias."""
    assert GenerateCallable is not None


def test_loader_callable_accepts_prompt_str_builds_conversation(monkeypatch):
    """RED (live crash): driven through run_critique + the
    loader-returned callable — apply_chat_template must receive a
    LIST of message dicts, never the prompt string."""
    captured = {}
    tfm, torch = _fake_transformer_mods(captured)
    monkeypatch.setitem(sys.modules, "transformers", tfm)
    monkeypatch.setitem(sys.modules, "torch", torch)
    gen = load_real_model()
    # the exact call shape run_critique makes:
    out = run_critique("music", gen)
    assert out["record"]["score"] == 34
    conv = captured["conv"]
    assert isinstance(conv, list), type(conv)
    msg = conv[0]
    assert msg["role"] == "user"
    kinds = [c["type"] for c in msg["content"]]
    assert "text" in kinds
    text = [c for c in msg["content"] if c["type"] == "text"][0]
    assert "0 to 40" in text["text"]  # the music profile prompt
    assert captured["gen_kw"].get("max_new_tokens") == 512


def test_loader_callable_audio_kwarg_becomes_audio_part(monkeypatch):
    """audio= (waveform array) flows through as an audio content
    part, factory-script pattern: audio part(s) first, then text."""
    captured = {}
    tfm, torch = _fake_transformer_mods(captured)
    monkeypatch.setitem(sys.modules, "transformers", tfm)
    monkeypatch.setitem(sys.modules, "torch", torch)
    gen = load_real_model()
    gen("critique this", audio=[0.0, 1.0], max_new_tokens=512)
    conv = captured["conv"]
    kinds = [c["type"] for c in conv[0]["content"]]
    assert kinds == ["audio", "text"]  # audio part precedes text
    assert captured["proc_audio"] == [0.0, 1.0]


def test_service_loader_failure_is_typed_503(monkeypatch):
    """GLM nit: loader() raising must yield typed 503, never a 500
    traceback body."""
    from fastapi.testclient import TestClient
    from qc.audio_critic.service import build_app

    def bad_loader():
        raise RuntimeError("CUDA out of memory")
    app = build_app(loader=bad_loader)
    r = TestClient(app).post("/critique", json={
        "audio_b64": B64S, "profile": "music", "mime": "audio/wav"})
    assert r.status_code == 503
    assert "model load failed" in r.json()["detail"]
