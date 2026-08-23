"""Transcript injection: judge prompts include whisper transcripts when available."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from qc.comic_critics.judges import LocalVLLMJudge


def make(td):
    return LocalVLLMJudge(base_url="http://x", transcript_dir=td)


def test_transcript_injected_for_local_video(tmp_path):
    vid = tmp_path / "v1.mp4"
    vid.write_bytes(b"x")
    (tmp_path / "v1.txt").write_text("Hello there. General Kenobi.")
    j = make(str(tmp_path))
    t = j._transcript_text(str(vid))
    assert t is not None and "General Kenobi" in t["text"]


def test_no_transcript_returns_none(tmp_path):
    vid = tmp_path / "v2.mp4"
    vid.write_bytes(b"x")
    j = make(str(tmp_path))
    assert j._transcript_text(str(vid)) is None


def test_urls_and_missing_dir_return_none(tmp_path):
    j = make(str(tmp_path))
    assert j._transcript_text("https://youtu.be/x") is None
    j2 = LocalVLLMJudge(base_url="http://x")  # no transcript_dir
    assert j2._transcript_text("/nonexistent/a.mp4") is None
