"""RED tests: the service must pipe the decoded audio to generate.

Live smoke #2: /critique validates audio_b64 (size, duration) then
calls run_critique(req.profile, gen) — the decoded bytes are
DISCARDED. The model replied 'I don't have access to audio files'
and hallucinated a score.
"""
import base64
import io
import struct
import wave

import pytest
from fastapi.testclient import TestClient

from qc.audio_critic.service import build_app

CLEAN = ("The delivery is crisp. I would rate it as 34 out of 40.")


def _wav_bytes(seconds: float = 0.5, rate: int = 16000,
               channels: int = 1, width: int = 2) -> bytes:
    """Real little-endian mono 16-bit WAV, N frames of a soft tone."""
    n = int(seconds * rate)  # FRAMES per channel
    total = n * channels
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(channels)
        w.setsampwidth(width)
        w.setframerate(rate)
        w.writeframes(b"".join(
            struct.pack("<h", int(10000 * ((i % 100) / 100))) for
            i in range(total)))
    return buf.getvalue()


WAV = _wav_bytes(0.5)          # 8000 samples @ 16kHz
WAV_B64 = base64.b64encode(WAV).decode()


def test_waveform_arrives_at_generate():
    """RED: fake generate captures kw['audio'] — non-empty array,
    right sample count for the fixture wav bytes."""
    seen = {}

    def gen(prompt, audio=None, **kw):
        seen["audio"] = audio
        seen["prompt"] = prompt
        return CLEAN
    app = build_app(generate=gen)
    r = TestClient(app).post("/critique", json={
        "audio_b64": WAV_B64, "profile": "music", "mime": "audio/wav"})
    assert r.status_code == 200, r.text
    import numpy as np
    a = seen["audio"]
    assert a is not None
    a = np.asarray(a)
    assert a.size == 8000, a.size           # 0.5s * 16kHz
    assert np.issubdtype(a.dtype, np.floating)  # decoded to float


def test_stereo_downmixed_and_normalized():
    """Decode converts to 16kHz MONO float regardless of input."""
    import numpy as np
    st = _wav_bytes(0.25, channels=2)
    seen = {}

    def gen(prompt, audio=None, **kw):
        seen["audio"] = audio
        return CLEAN
    app = build_app(generate=gen)
    r = TestClient(app).post("/critique", json={
        "audio_b64": base64.b64encode(st).decode(), "profile": "music",
        "mime": "audio/wav"})
    assert r.status_code == 200, r.text
    a = np.asarray(seen["audio"])
    assert a.ndim == 1                       # mono
    assert a.size == 4000                    # 0.25s * 16kHz


def test_run_critique_passes_audio_through():
    """run_critique accepts audio= (and audios=) and forwards to
    generate per the PR #49 contract."""
    seen = {}

    def gen(prompt, audio=None, audios=None, **kw):
        seen["audio"] = audio
        seen["audios"] = audios
        return CLEAN
    from qc.audio_critic.criticize import run_critique
    wf = [0.1, 0.2, 0.3]
    out = run_critique("music", gen, audio=wf)
    assert out["record"]["score"] == 34
    assert seen["audio"] == wf


def test_decode_helper_lazy_and_typed():
    """decode_wav is a pure helper, lazy-imports soundfile/scipy,
    and raises typed AudioCriticError on garbage."""
    from qc.audio_critic.service import decode_wav
    import numpy as np
    wf = decode_wav(WAV)
    assert np.asarray(wf).size == 8000
    with pytest.raises(Exception) as ei:
        decode_wav(b"not a wav at all")
    assert "decode" in str(ei.value).lower()
