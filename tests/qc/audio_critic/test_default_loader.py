"""RED tests: default loader wiring (deployment bug, live 3090).

The module-level 'app = build_app()' had NO loader, so real uvicorn
deployments returned 503 'model not loaded' forever — tests never
caught it because they inject generate=.
"""
import importlib

import pytest
from fastapi.testclient import TestClient

from qc.audio_critic.service import build_app

def _tiny_wav(seconds: float = 0.01) -> bytes:
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


B64S = __import__("base64").b64encode(_tiny_wav()).decode()

CLEAN = ("The delivery is crisp. I would rate it as 34 out of 40.")


def test_module_level_app_has_loader_wired(monkeypatch):
    """RED: the default module-level app must carry a real loader,
    not the loader-less build_app() that 503s forever."""
    import qc.audio_critic.criticize as crit
    stub_calls = []

    def stub_loader():
        stub_calls.append(1)

        def gen(prompt, **kw):
            return CLEAN
        return gen
    monkeypatch.setattr(crit, "load_real_model", stub_loader)
    import qc.audio_critic.service as svc
    importlib.reload(svc)
    assert svc.app is not None
    r = TestClient(svc.app).post("/critique", json={
        "audio_b64": B64S, "profile": "delivery",
        "mime": "audio/wav"})
    assert r.status_code == 200, r.text
    assert stub_calls == [1]  # loader invoked lazily on first request
    assert r.json()["score"] == 34
    importlib.reload(svc)  # restore for other tests


def test_loader_lazy_on_first_critique_only(monkeypatch):
    import qc.audio_critic.criticize as crit
    calls = []

    def stub_loader():
        calls.append(1)

        def gen(prompt, **kw):
            return CLEAN
        return gen
    monkeypatch.setattr(crit, "load_real_model", stub_loader)
    app = build_app(loader=stub_loader)
    c = TestClient(app)
    assert c.get("/health").json()["model_loaded"] is False
    assert c.post("/critique", json={
        "audio_b64": B64S, "profile": "delivery",
        "mime": "audio/wav"}).status_code == 200
    assert c.post("/critique", json={
        "audio_b64": B64S, "profile": "delivery",
        "mime": "audio/wav"}).status_code == 200
    assert calls == [1]  # loaded ONCE, not per request
    assert c.get("/health").json()["model_loaded"] is True


def test_ac_model_id_env_honored(monkeypatch):
    """AC_MODEL_ID must feed the transformers from_pretrained id."""
    captured = {}

    class FakeFeatureExtractor:
        sampling_rate = 16000

    class FakeProcessor:
        feature_extractor = FakeFeatureExtractor()

        def apply_chat_template(self, conv, **kw):
            return "tpl"

        def __call__(self, text=None, audio=None, **kw):
            captured["text"] = text

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

        def to(self, *a, **kw):
            return self

    def fake_autoproc(model_id=None, **kw):
        captured["model_id"] = model_id
        return FakeProcessor()

    def fake_model_cls(model_id=None, **kw):
        return FakeModel()
    # build fake transformers module
    import types, sys
    tfm = types.ModuleType("transformers")
    tfm.AutoProcessor = type(
        "AP", (), {"from_pretrained": staticmethod(fake_autoproc)})
    tfm.__dict__["Qwen2AudioForConditionalGeneration"] = type(
        "M", (), {"from_pretrained": staticmethod(fake_model_cls)})
    torch = types.ModuleType("torch")
    torch.bfloat16 = "bf16"

    class _cm:  # no_grad context stub
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False
    torch.no_grad = lambda: _cm()
    monkeypatch.setitem(sys.modules, "transformers", tfm)
    monkeypatch.setitem(sys.modules, "torch", torch)

    from qc.audio_critic.criticize import load_real_model
    monkeypatch.setenv("AC_MODEL_ID", "Custom/Model-XY")
    gen = load_real_model()
    assert captured["model_id"] == "Custom/Model-XY"
    out = gen("prompt text", max_new_tokens=512)
    assert out == CLEAN
    assert captured["gen_kw"].get("max_new_tokens") == 512
