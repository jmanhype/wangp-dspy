"""Whisper CLI adapter for the repo-owned QC worker.

The model process remains an external runtime (the repo intentionally does
not vendor Whisper/VibeVoice), but command construction, output handling, and
the host seam live here so ``run_jobs.py`` does not need a side-script bridge.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Callable, Optional, Sequence


class WhisperCLIError(RuntimeError):
    """Typed failure from the Whisper command or transcript artifact."""


def _parts(result):
    if isinstance(result, tuple):
        if len(result) >= 3:
            return int(result[0]), str(result[1] or ""), str(result[2] or "")
        if len(result) == 2:
            return int(result[0]), str(result[1] or ""), ""
    return (int(getattr(result, "returncode", 0)),
            str(getattr(result, "stdout", "") or ""),
            str(getattr(result, "stderr", "") or ""))


def whisper_transcriber(
    audio_path: str,
    *,
    runner: Callable[[Sequence[str]], object],
    model: str = "small",
    output_dir: str = "/tmp/wangp-whisper",
) -> str:
    """Transcribe one local or remote artifact through argv-only commands."""
    if not isinstance(audio_path, str) or not audio_path:
        raise WhisperCLIError("audio_path: required")
    if not model or not output_dir:
        raise WhisperCLIError("model and output_dir are required")
    rc, _out, err = _parts(runner(["mkdir", "-p", output_dir]))
    if rc != 0:
        raise WhisperCLIError(f"mkdir output_dir failed: {err[:240]}")
    argv = ["whisper", audio_path, "--model", model,
            "--task", "transcribe", "--language", "en",
            "--output_format", "txt", "--output_dir", output_dir]
    rc, stdout, stderr = _parts(runner(argv))
    if rc != 0:
        raise WhisperCLIError(f"Whisper failed (rc={rc}): {stderr[:240]}")
    transcript_path = str(Path(output_dir) / (Path(audio_path).stem + ".txt"))
    rc, transcript, cat_err = _parts(runner(["cat", transcript_path]))
    if rc != 0:
        # Some Whisper wrappers return the transcript directly rather than
        # materializing the txt artifact. Accept that only when nonempty.
        transcript = stdout.strip()
        if not transcript:
            raise WhisperCLIError(
                f"Whisper transcript artifact missing: {transcript_path}; "
                f"cat error: {cat_err[:240]}")
    transcript = transcript.strip()
    if not transcript:
        raise WhisperCLIError("Whisper returned an empty transcript")
    return transcript


def host_whisper_transcriber(host, *, model: str = "small",
                             output_dir: str = "/tmp/wangp-whisper"):
    """Build a transcriber using an existing SshHost.run_probe seam."""
    run_probe = getattr(host, "run_probe", None)
    if not callable(run_probe):
        raise WhisperCLIError("host must expose run_probe(argv, timeout=...)")

    def run(argv):
        return run_probe(list(argv), timeout=900)

    return lambda audio_path: whisper_transcriber(
        audio_path, runner=run, model=model, output_dir=output_dir)


__all__ = ["WhisperCLIError", "whisper_transcriber", "host_whisper_transcriber"]
