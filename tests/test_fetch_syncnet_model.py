import hashlib
from pathlib import Path

from scripts.fetch_syncnet_model import fetch
from qc.audio_critic.syncnet_runner import SYNCNET_MODEL_SHA256


class _Source:
    def __init__(self, payload):
        self.payload = payload

    def read(self, size):
        if self.payload:
            chunk = self.payload[:size]
            self.payload = self.payload[size:]
            return chunk
        return b""

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


def test_fetch_rejects_tampered_model(tmp_path, monkeypatch):
    destination = tmp_path / "syncnet.model"
    monkeypatch.setattr(
        "urllib.request.urlopen", lambda *_args, **_kwargs: _Source(b"bad"))
    try:
        fetch(destination)
    except ValueError as exc:
        assert "SHA-256 mismatch" in str(exc)
    else:
        raise AssertionError("tampered model was accepted")
    assert not destination.exists()
    assert not destination.with_name(destination.name + ".partial").exists()


def test_fetch_accepts_pinned_model(tmp_path, monkeypatch):
    destination = tmp_path / "syncnet.model"
    payload = b"model-bytes"
    monkeypatch.setattr(
        "urllib.request.urlopen", lambda *_args, **_kwargs: _Source(payload))
    monkeypatch.setattr(
        "qc.audio_critic.syncnet_runner.SYNCNET_MODEL_SHA256",
        hashlib.sha256(payload).hexdigest())
    monkeypatch.setattr(
        "scripts.fetch_syncnet_model.SYNCNET_MODEL_SHA256",
        hashlib.sha256(payload).hexdigest())
    assert fetch(destination) == hashlib.sha256(payload).hexdigest()
    assert destination.read_bytes() == payload
