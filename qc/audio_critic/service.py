"""FastAPI audio-critic service (slice 2) — 3090-side app.

Contract: docs/PROPOSAL_audio_critic_service.md:
- POST /critique {audio_b64, profile, mime}
- single-flight in-process lock: one critique at a time, concurrent
  requests queue (bounded MAX_QUEUE=8, typed 503 when full)
- 90s audio cap, typed rejection beyond
- GET /health: model loaded, queue depth
- FastAPI, 1 worker

Model loading is INJECTABLE via build_app(generate=..., loader=...):
tests pass fakes; the real deployment passes the transformers-loaded
Qwen2-Audio callable. This module is deliberately thin — the
substantive logic lives in schema/profiles/criticize so tests never
need the model (proposal: service.py "deliberately NOT imported by
tests" — we keep that spirit: tests exercise behavior through
build_app with injected fakes, never the GPU path).
"""
from __future__ import annotations

import base64
import threading
import os
import time
from typing import Callable, Optional

from fastapi import FastAPI
from pydantic import BaseModel

from qc.audio_critic.criticize import (
    DEFAULT_MODEL_ID, run_critique,
)
from qc.audio_critic.profiles import PROFILES
from qc.audio_critic.schema import AudioCriticError

MAX_AUDIO_SECONDS = 90   # proposal: caps 90s audio per request
MAX_QUEUE = 8            # bounded queue, typed 503 when full

# GLM PR#44 review F1 (MEDIUM): PRE-DECODE request size cap. Reject
# with typed 413 before base64.b64decode() — a bound consistent with
# 90s of 16kHz mono 16-bit WAV (90 * 32000 B = 2.88 MB raw, ~3.84 MB
# base64). Env-tunable via AUDIO_CRITIC_MAX_B64 (b64 characters).
import os as _os
_DEFAULT_MAX_B64 = 4 * 1024 * 1024  # ~4 MB of base64 text
MAX_B64_CHARS = int(_os.environ.get("AUDIO_CRITIC_MAX_B64",
                                    _DEFAULT_MAX_B64))

# audio duration estimation is injected so tests never decode media.
# Default heuristic (LOW nit, GLM): assumes 16kHz MONO 16-bit WAV
# (~32kB/s). Real deployments should inject a probing estimator;
# slice 3 will parse the true duration from the audio container.
_DEFAULT_BYTES_PER_SEC = 32000


def _default_audio_seconds(payload: bytes) -> float:
    return len(payload) / _DEFAULT_BYTES_PER_SEC


def decode_wav(payload: bytes):
    """Decode wav BYTES to a 16kHz MONO float waveform.

    WAV is the only accepted mime (per the judge client).
    soundfile is lazy-imported so CPU-only/test environments that
    never decode real audio don't need it. Raises typed
    AudioCriticError on undecodable bytes.
    """
    import io

    import numpy as np  # soundfile dependency, always present with it

    from qc.audio_critic.criticize import AudioCriticError
    try:
        import soundfile as sf
    except ImportError as e:
        raise AudioCriticError(
            f"audio decode unavailable (soundfile missing): {e}") from e
    try:
        data, sr = sf.read(io.BytesIO(payload), dtype="float32",
                            always_2d=True)
    except Exception as e:
        raise AudioCriticError(
            f"audio decode failed: {type(e).__name__}: {e}") from e
    if data.shape[1] > 1:  # downmix to mono
        data = data.mean(axis=1)
    else:
        data = data[:, 0]
    if sr != 16000:  # resample linear to 16kHz
        n_out = int(round(data.size * 16000 / sr))
        idx = np.linspace(0.0, data.size - 1, n_out)
        data = np.interp(idx, np.arange(data.size), data)
    return data


class CritiqueRequest(BaseModel):
    audio_b64: str
    profile: str
    mime: str = "audio/wav"


class _Gate:
    """Bounded single-flight gate: one critique at a time, at most
    MAX_QUEUE waiting. Overflow gets a typed 503 immediately."""

    def __init__(self, max_queue: int = MAX_QUEUE):
        self._lock = threading.Lock()
        self._sem = threading.Semaphore(1)
        self._queue = threading.Semaphore(max_queue)
        self.depth = 0
        self._depth_lock = threading.Lock()

    def acquire(self) -> bool:
        if not self._queue.acquire(blocking=False):
            return False
        self._sem.acquire()
        with self._depth_lock:
            self.depth += 1
        self._queue.release()  # slot moves from waiting to active
        return True

    def release(self):
        with self._depth_lock:
            self.depth = max(0, self.depth - 1)
        self._sem.release()

    def queue_depth(self) -> int:
        with self._depth_lock:
            return self.depth


def build_app(
    *,
    generate: Optional[Callable[..., str]] = None,
    loader: Optional[Callable[[], Callable[..., str]]] = None,
    audio_seconds: Callable[[bytes], float] = _default_audio_seconds,
    idle_unload_secs: float = 900.0,
    max_queue: int = MAX_QUEUE,
) -> FastAPI:
    app = FastAPI(title="audio-critic", version="1")
    state = {"generate": generate, "model_loaded": generate is not None,
             "last_used": time.monotonic()}
    gate = _Gate(max_queue)

    if loader is not None and generate is None:
        # deferred load (real deployment); tests inject generate
        state["generate"] = None  # loaded on first request / startup

    @app.get("/health")
    def health():
        return {"model_loaded": state["model_loaded"],
                "queue_depth": gate.queue_depth()}

    @app.post("/critique")
    def critique(req: CritiqueRequest):
        if req.profile not in PROFILES:
            return _typed(422, f"unknown profile: {req.profile!r} "
                               f"(allowed: {sorted(PROFILES)})")
        if len(req.audio_b64) > MAX_B64_CHARS:
            return _typed(
                413,
                f"audio_b64 too large: {len(req.audio_b64)} chars "
                f"exceeds the {MAX_B64_CHARS}-char cap (~4 MB base64, "
                "consistent with 90s of 16kHz mono WAV)")
        try:
            payload = base64.b64decode(req.audio_b64, validate=True)
        except Exception:
            return _typed(422, "audio_b64 is not valid base64")
        secs = audio_seconds(payload)
        if secs > MAX_AUDIO_SECONDS:
            return _typed(
                422,
                f"audio too long: {secs:.0f}s exceeds the "
                f"{MAX_AUDIO_SECONDS}s cap")
        if not gate.acquire():
            return _typed(
                503,
                f"queue full (max {max_queue} waiting); back off")
        try:
            state["last_used"] = time.monotonic()
            gen = state["generate"]
            if gen is None:
                if loader is None:
                    return _typed(503, "model not loaded")
                try:
                    gen = loader()
                except Exception as e:  # GLM nit: typed, never 500
                    return _typed(
                        503,
                        f"model load failed: {type(e).__name__}: {e}")
                state["generate"] = gen
                state["model_loaded"] = True
            try:
                waveform = decode_wav(payload)
            except AudioCriticError as e:
                return _typed(422, str(e))
            body = _run_ensemble(req.profile, gen, audio=waveform,
                                 size=ensemble_size())
            return body
        except AudioCriticError as e:
            return _typed(422, str(e))
        finally:
            gate.release()

    def _typed(status: int, message: str):
        return JSONResponse({"detail": message}, status_code=status)

    from fastapi.responses import JSONResponse
    return app


# module-level default app for `uvicorn qc.audio_critic.service:app`.
# Deployment fix (live 3090): the loader IS wired — the real model
# loads lazily on the first /critique. The loader import is guarded
# so importing this module never needs torch/transformers.
def _default_loader():
    from qc.audio_critic.criticize import load_real_model
    return load_real_model()


app = build_app(loader=_default_loader)



# ── judge-consistency ensemble (PR #17 follow-up) ───────────────────
# Greedy degenerated the judge ordering; sampled temp-0.3 runs
# are aggregated by MEDIAN for stability. Size env-tuned
# (AUDIO_CRITIC_ENSEMBLE, default 3; 1 = single-shot).

def ensemble_size() -> int:
    raw = os.environ.get("AUDIO_CRITIC_ENSEMBLE", "3")
    try:
        n = int(raw)
    except ValueError:
        n = 3
    return max(1, n)


def _run_ensemble(profile: str, generate, *, audio=None, audios=None,
                  size: int = 3) -> dict:
    """Run run_critique `size` times; aggregate by median score,
    keep the median run's prose, record all scores."""
    from .criticize import aggregate_ensemble
    runs = []
    for _ in range(max(1, size)):
        out = run_critique(profile, generate, audio=audio,
                           audios=audios)
        runs.append({
            "score": out["record"]["score"],
            "prose": out["prose"],
            "record": out["record"],
            "retried": out["retried"],
        })
    agg = aggregate_ensemble(runs)
    body = dict(agg["record"])
    body["prose"] = agg["prose"]
    body["retried"] = agg["retried"]
    body["scores_list"] = agg["scores_list"]
    body["ensemble"] = agg["ensemble"]
    return body
