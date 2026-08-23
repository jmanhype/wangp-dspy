"""Judge backends: one interface, three implementations.

vote_pair(instructions, u1, u2, lp1, lp2) -> dict with best_candidate
(+ reasoning, raw_response, input/output_tokens when available).

- LocalVLLM: OpenAI-compatible server (default: 3090 host, qwen 27B).
  Known convention: API video = ~1s frame sampling, NO audio.
- ZaiGLM: glm-4.6v with video_url content parts.
- Gemini: optional passthrough for cross-validation only.
"""
from __future__ import annotations

import os
import re
import time
from pathlib import Path

from .core import parse_vote


class JudgeError(Exception):
    pass


class LocalVLLMJudge:
    """OpenAI-compatible video judge (vLLM on the 3090).

    Video upload semantics follow the OpenAI chat-completions video
    convention (content part {type: video_url, video_url: {url: ...}}
    with a file:// or http URL, or base64 data URL). Caveat: API video
    support means ~1s frame sampling and NO audio — scores are
    correlation experiments until calibrated (see README).
    """

    def __init__(self, model=None, base_url=None, api_key=None,
                 max_retries=3, retry_delay=10, fps=None,
                 transcript_dir=None):
        self.model = model or os.getenv(
            "COMIC_VLLM_MODEL", "qwen2.5-vl-27b-instruct")
        self.base_url = base_url or os.getenv(
            "COMIC_VLLM_BASE_URL", "http://100.94.237.121:18020/v1")
        self.api_key = api_key or os.getenv("COMIC_VLLM_API_KEY", "EMPTY")
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.fps = fps or os.getenv("COMIC_VLLM_FPS")
        self.transcript_dir = transcript_dir or os.getenv("COMIC_TRANSCRIPTS")
        self._client = None

    @property
    def client(self):
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI(base_url=self.base_url,
                                  api_key=self.api_key)
        return self._client

    def _video_part(self, url_or_path):
        p = str(url_or_path)
        if p.startswith(("http://", "https://", "data:")):
            uri = p
        else:
            uri = "file://" + str(Path(p).resolve())
        part = {"type": "video_url",
                "video_url": {"url": uri}}
        if self.fps:
            # some servers accept an fps hint next to the url
            part["video_url"]["fps"] = float(self.fps)
        return part

    def _transcript_text(self, url_or_path):
        """Best-effort whisper transcript for a local video, as a text block.

        Looks for <stem>.txt in TRANSCRIPT_DIR (populated offline by whisper
        CLI). Returns None when absent — transcript enhancement is optional.
        """
        if not self.transcript_dir:
            return None
        p = str(url_or_path)
        if p.startswith(("http://", "https://", "data:")):
            return None
        tf = Path(self.transcript_dir) / (Path(p).stem + ".txt")
        if not tf.is_file():
            return None
        txt = tf.read_text(errors="replace").strip()
        if not txt:
            return None
        return {"type": "text",
                "text": f"[dialogue transcript for this video]\n{txt}"}

    def vote_pair(self, instructions, u1, u2, lp1=None, lp2=None):
        c1, c2 = self._video_part(lp1 or u1), self._video_part(lp2 or u2)
        t1 = self._transcript_text(lp1 or u1)
        t2 = self._transcript_text(lp2 or u2)
        content = [
            {"type": "text", "text": instructions},
            {"type": "text", "text": "Candidate Videos:\nCandidate #1:"},
            c1,
        ]
        if t1:
            content.append(t1)
        content.append({"type": "text", "text": "Candidate #2:"})
        content.append(c2)
        if t2:
            content.append(t2)
        content.append({"type": "text", "text": (
                "Please evaluate all candidate videos and provide your "
                "response following the format specified in your "
                "instructions. Select the best candidate (1 or 2).")})
        err = None
        for att in range(self.max_retries):
            try:
                r = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": content}],
                    max_tokens=4096, temperature=0.0)
                txt = r.choices[0].message.content or ""
                out = parse_vote(txt)
                out["raw_response"] = txt
                u = getattr(r, "usage", None)
                if u:
                    out["input_tokens"] = getattr(u, "prompt_tokens", None)
                    out["output_tokens"] = getattr(
                        u, "completion_tokens", None)
                return out
            except Exception as e:  # noqa: BLE001 — transport errors
                err = e
                time.sleep(self.retry_delay * (att + 1))
        return {"best_candidate": 1, "reasoning": "",
                "error": f"{type(err).__name__}: {err}"}


class ZaiGLMJudge:
    """glm-4.6v via the Z.ai/OpenAI-compatible video endpoint."""

    def __init__(self, model=None, api_key=None, base_url=None,
                 max_retries=3, retry_delay=10):
        self.model = model or os.getenv("COMIC_GLM_MODEL", "glm-4.6v")
        self.api_key = api_key or os.getenv("ZAI_API_KEY") \
            or os.getenv("GLM_API_KEY")
        self.base_url = base_url or os.getenv(
            "COMIC_GLM_BASE_URL", "https://api.z.ai/api/paas/v4/")
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    @property
    def client(self):
        if not self.api_key:
            raise JudgeError("ZAI_API_KEY / GLM_API_KEY not set")
        from openai import OpenAI
        key = self.api_key
        return OpenAI(base_url=self.base_url, api_key=key)

    def _video_part(self, url_or_path):
        p = str(url_or_path)
        if not p.startswith(("http://", "https://")):
            # glm video_url parts expect public URLs; local files must
            # be served (e.g. via a tunnel). file paths are rejected.
            raise JudgeError(
                f"glm-4.6v requires an http(s) video URL, got {p!r} — "
                "serve local renders (e.g. `python -m http.server` + "
                "tunnel) and pass the URL")
        return {"type": "video_url", "video_url": {"url": p}}

    def vote_pair(self, instructions, u1, u2, lp1=None, lp2=None):
        content = [
            {"type": "text", "text": instructions},
            {"type": "text", "text": "Candidate Videos:\nCandidate #1:"},
            self._video_part(u1 or lp1),
            {"type": "text", "text": "Candidate #2:"},
            self._video_part(u2 or lp2),
            {"type": "text", "text": (
                "Please evaluate all candidate videos and provide your "
                "response following the format specified in your "
                "instructions. Select the best candidate (1 or 2).")},
        ]
        err = None
        for att in range(self.max_retries):
            try:
                r = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": content}],
                    max_tokens=4096, temperature=0.0)
                txt = r.choices[0].message.content or ""
                out = parse_vote(txt)
                out["raw_response"] = txt
                return out
            except Exception as e:  # noqa: BLE001
                err = e
                time.sleep(self.retry_delay * (att + 1))
        return {"best_candidate": 1, "reasoning": "",
                "error": f"{type(err).__name__}: {err}"}


class GeminiJudge:
    """Optional passthrough to the original Gemini backend —
    cross-validation against the eval_20260821_232933 baseline only."""

    MAX_RETRIES = 10
    RETRY_DELAY = 30

    def __init__(self, model=None, api_key=None):
        self.model = model or os.getenv(
            "COMIC_GEMINI_MODEL", "gemini-3-flash-preview")
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY") \
            or os.getenv("GEMINI_API_KEY")

    @property
    def client(self):
        if not self.api_key:
            raise JudgeError(
                "GOOGLE_API_KEY / GEMINI_API_KEY not set")
        from google import genai
        from google.genai import types as gtypes
        self._gtypes = gtypes
        return genai.Client(api_key=self.api_key)

    def _wait_active(self, f, c, timeout=300):
        gtypes = self._gtypes
        t0 = time.time()
        while time.time() - t0 < timeout:
            s = c.files.get(name=f.name).state
            if s == gtypes.FileState.ACTIVE:
                return True
            if s == gtypes.FileState.FAILED:
                return False
            time.sleep(5)
        return False

    def _add_vid(self, parts, url, lp, c, ufs):
        gtypes = self._gtypes
        if lp:
            f = c.files.upload(file=lp)
            ufs.append(f)
            if self._wait_active(f, c):
                parts.append(c.files.get(name=f.name))
                return
        parts.append(gtypes.Part(file_data=gtypes.FileData(file_uri=url)))

    def vote_pair(self, instructions, u1, u2, lp1=None, lp2=None):
        try:
            c = self.client
        except JudgeError as e:
            return {"best_candidate": 1, "reasoning": "", "error": str(e)}
        ufs = []
        err = None
        try:
            p = [instructions, "Candidate Videos:\n", "Candidate #1:"]
            self._add_vid(p, u1, lp1, c, ufs)
            p.append("Candidate #2:")
            self._add_vid(p, u2, lp2, c, ufs)
            p.append("Please evaluate all candidate videos and provide "
                     "your response following the format specified in "
                     "your instructions. Select the best candidate "
                     "(1 or 2).")
            for att in range(self.MAX_RETRIES):
                try:
                    r = c.models.generate_content(model=self.model,
                                                  contents=p)
                    out = parse_vote(r.text or "")
                    out["raw_response"] = r.text
                    u = getattr(r, "usage_metadata", None)
                    if u:
                        out["input_tokens"] = getattr(
                            u, "prompt_token_count", None)
                        out["output_tokens"] = getattr(
                            u, "candidates_token_count", None)
                    return out
                except Exception as e:  # noqa: BLE001
                    err = e
                    if att < self.MAX_RETRIES - 1:
                        time.sleep(self.RETRY_DELAY * (att + 1))
        finally:
            for f in ufs:
                try:
                    c.files.delete(name=f.name)
                except Exception:  # noqa: BLE001
                    pass
        return {"best_candidate": 1, "reasoning": "",
                "error": str(err)}


def make_judge(name: str, **kw):
    name = name.lower()
    if name == "local":
        return LocalVLLMJudge(**kw)
    if name == "glm":
        return ZaiGLMJudge(**kw)
    if name == "gemini":
        return GeminiJudge(**kw)
    raise JudgeError(f"unknown judge {name!r} (local|glm|gemini)")


class AudioDeliveryJudge:
    """Audio-critic service judge (slice 4, delivery profile).

    Feeds the comic lane's deaf spot: vision+transcript judges can't
    hear comedic delivery/timing/pacing. For each candidate with a
    LOCAL video path, extracts 16kHz mono wav via ffmpeg (90s cap,
    consistent with the service's audio cap), POSTs to the
    audio-critic service (env AUDIO_CRITIC_URL, default
    http://100.94.237.121:18022/critique), and renders both
    structured critiques into the [VOTING]/[WINNER] contract the
    existing parse machinery consumes.

    Failure isolation mirrors the other judges: ANY service error
    degrades deterministically (candidate-1 default when nothing
    scored; score-based when one critique succeeded) — never crashes
    the eval run. URL candidates (http...) have no local file to
    extract: skipped and noted in the vote ("skipped").
    """

    def __init__(self, *, transport=None, ffmpeg=None,
                 endpoint=None, timeout=300.0):
        self.endpoint = endpoint or os.environ.get(
            "AUDIO_CRITIC_URL",
            "http://100.94.237.121:18022/critique")
        self.timeout = timeout
        if transport is None:
            import requests
            transport = requests
        self.transport = transport
        if ffmpeg is None:
            ffmpeg = _run_ffmpeg
        self.ffmpeg = ffmpeg

    def _extract_wav_b64(self, video_path):
        """ffmpeg -> temp 16kHz mono wav (90s cap) -> base64."""
        import base64
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            wav = str(Path(td) / "audio.wav")
            argv = ["ffmpeg", "-y", "-i", str(video_path),
                    "-vn", "-ac", "1", "-ar", "16000",
                    "-t", "90", wav]
            proc = self.ffmpeg(argv, timeout=120)
            if getattr(proc, "returncode", 1) != 0:
                raise JudgeError(
                    "ffmpeg extraction failed for %s" % video_path)
            with open(wav, "rb") as fh:
                return base64.b64encode(fh.read()).decode()

    def _critique(self, video_path):
        audio_b64 = self._extract_wav_b64(video_path)
        r = self.transport.post(self.endpoint, timeout=self.timeout,
                                json={"audio_b64": audio_b64,
                                      "profile": "delivery",
                                      "mime": "audio/wav"})
        status = getattr(r, "status_code", 0)
        if status != 200:
            raise JudgeError("audio-critic HTTP %s" % status)
        body = r.json()
        if body.get("schema") != "audio-critic/1":
            raise JudgeError("audio-critic schema mismatch")
        return body

    @staticmethod
    def _render(critiques, skipped, err):
        lines = ["[VOTING START]", ""]
        for i, c in enumerate(critiques, 1):
            if c is None:
                lines.append("Candidate #%d: (audio critique "
                             "unavailable)" % i)
                continue
            lines.append("Candidate #%d: score %d/40 decision %s%s"
                         % (i, c["score"], c["decision"],
                            (" flags " + ",".join(c["flags"]))
                            if c["flags"] else ""))
            lines.append("  " + c["reason"])
        lines.append("")
        scored = [(i, c["score"]) for i, c in
                  enumerate(critiques, 1) if c]
        if not scored:
            winner, review = 1, "no audio critiques available"
        else:
            winner = max(scored, key=lambda t: t[1])[0]
            review = ("higher delivery score wins %s; skipped=%s"
                      % (dict(scored), skipped or "none"))
        lines.append("[WINNER START]Candidate #%d[WINNER END]" % winner)
        lines.append("")
        lines.append("[REVIEW START]")
        lines.append(review + (("; error=" + err) if err else ""))
        lines.append("[REVIEW END]")
        lines.append("")
        lines.append("[VOTING END]")
        return "\n".join(lines)

    def vote_pair(self, instructions, u1, u2, lp1=None, lp2=None):
        critiques, skipped, err = [None, None], [], None
        for idx, cand in enumerate((lp1 or u1, lp2 or u2)):
            p = str(cand)
            if p.startswith(("http://", "https://", "data:")):
                skipped.append(str(idx + 1))
                continue
            try:
                critiques[idx] = self._critique(p)
            except Exception as e:  # noqa: BLE001 — failure isolation
                err = "%s: %s" % (type(e).__name__, e)
        raw = self._render(critiques, skipped, err)
        out = parse_vote(raw)
        out["raw_response"] = raw
        if skipped:
            out["skipped"] = skipped
        if err:
            out["error"] = err
        return out


def _run_ffmpeg(argv, timeout=120):
    import subprocess
    return subprocess.run(argv, capture_output=True, timeout=timeout)
