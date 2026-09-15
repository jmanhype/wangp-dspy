import pathlib
from types import SimpleNamespace

import pytest

from services.director.wiring import MediaAssemblyError, assemble_media


def test_assemble_media_uses_repo_ffmpeg_argv_and_records_inputs(tmp_path):
    videos = []
    for i in range(2):
        p = pathlib.Path(tmp_path) / f"cut{i + 1}.mp4"
        p.write_bytes(b"video")
        videos.append(str(p))
    output = pathlib.Path(tmp_path) / "film.mp4"
    calls = []

    def run(argv):
        calls.append(list(argv))
        output.write_bytes(b"assembled")
        return SimpleNamespace(returncode=0)

    result = assemble_media(videos, str(output), runner=run)
    assert result["video_paths"] == videos
    assert calls[0][:8] == ["ffmpeg", "-y", "-v", "error", "-i", videos[0],
                             "-i", videos[1]]
    assert "[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1[v][a]" in calls[0]
    assert calls[0][-1] == str(output)
    assert "file '" + videos[0] + "'" in pathlib.Path(
        result["manifest_path"]).read_text()


def test_assemble_media_fails_closed_on_missing_cut(tmp_path):
    with pytest.raises(MediaAssemblyError, match="unreadable"):
        assemble_media([str(pathlib.Path(tmp_path) / "missing.mp4")],
                       str(pathlib.Path(tmp_path) / "film.mp4"))


def test_assemble_media_fails_closed_on_ffmpeg_error(tmp_path):
    p = pathlib.Path(tmp_path) / "cut.mp4"
    p.write_bytes(b"video")

    def run(_):
        return 1

    with pytest.raises(MediaAssemblyError, match="ffmpeg assembly failed"):
        assemble_media([str(p)], str(pathlib.Path(tmp_path) / "film.mp4"),
                       runner=run)
