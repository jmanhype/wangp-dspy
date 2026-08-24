"""WD-qn1a scratch hygiene: SshHost.fetch_videos must purge stale
video files from the pull mirror (story isolation).

Live cycle-4 finding: the pull6 mirror carried unrelated historical
renders because rsync -a copies the WHOLE shared wgp outputs dir and
the scan filter only hid the stale files — it did not remove them.
"""
import os
import time

import pytest

from host.render_host import SshHost


class _FakeProc:
    returncode = 0
    stdout = b""
    stderr = b""


def _make_host(tmp_path, monkeypatch):
    host = SshHost(target="gpu-box", wgp_root="/home/g/wgp",
                   pull_root=str(tmp_path / "pull"))
    # rsync is stubbed: pretend the remote dir contains one stale
    # and one fresh video; rsync "materializes" both in the mirror.
    remote_outputs = "/home/g/wgp/outputs"

    def fake_run(cmd, label):
        # emulate rsync -a: copy fakes into the mirror
        mirror = tmp_path / "pull" / "outputs"
        mirror.mkdir(parents=True, exist_ok=True)
        past = time.time() - 3600
        stale = mirror / "ancient_render.mp4"
        stale.write_bytes(b"old")
        os.utime(stale, (past, past))
        fresh = mirror / "this_attempt.mp4"
        fresh.write_bytes(b"new")
        return 0, b"", b""

    monkeypatch.setattr(host, "_run", fake_run)
    return host, remote_outputs


def test_purge_removes_stale_videos_from_mirror(tmp_path, monkeypatch):
    host, remote_outputs = _make_host(tmp_path, monkeypatch)
    now = time.time()
    videos = host.fetch_videos((remote_outputs,), remote_outputs,
                               newer_than=now - 5)
    mirror = tmp_path / "pull" / "outputs"
    names = sorted(os.listdir(mirror))
    # the stale render must NOT survive the pull (story isolation)
    assert "ancient_render.mp4" not in names, (
        "stale historical render survived in the pull mirror — "
        "WD-qn1a scratch-hygiene regression")
    # the fresh one stays and is returned
    assert "this_attempt.mp4" in names
    assert [os.path.basename(v) for v in videos] == ["this_attempt.mp4"]


def test_scan_filter_still_guards_without_deletion(tmp_path, monkeypatch):
    """Even if the purge is best-effort, returned paths are fresh only."""
    host, remote_outputs = _make_host(tmp_path, monkeypatch)
    now = time.time()
    videos = host.fetch_videos((remote_outputs,), remote_outputs,
                               newer_than=now - 5)
    assert all("ancient" not in v for v in videos)
