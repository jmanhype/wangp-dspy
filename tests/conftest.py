import pytest
from host.wangp_adapter import WanGPAdapter, FRAME_COUNT_UNVERIFIED
from tests.lf003_fixtures import verify_lf003_fixtures


@pytest.fixture(autouse=True)
def _stub_ffprobe_for_fake_videos(monkeypatch):
    """WD-u4rv: readback verification ffprobes rendered videos; unit
    tests write fake byte files that real ffprobe rejects. Default the
    counter to the UNVERIFIED sentinel (adapter skips the check);
    frame-verification tests override _ffprobe_frames themselves."""
    monkeypatch.setattr(
        WanGPAdapter, "_ffprobe_frames",
        staticmethod(lambda host, path: FRAME_COUNT_UNVERIFIED))


@pytest.fixture
def lf003_fixtures():
    """Fail closed before LF003/AV tests use portable evidence bytes."""
    return verify_lf003_fixtures()
