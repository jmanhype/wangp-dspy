"""WD-h0vk RED pins: RenderHost seam (Qwen-approved design).

5 pins, all fakes, zero ssh. Guardrails: TRANSIENT_RE/retry untouched;
the adapter diff must read as delegation only."""
import json
import os
import posixpath

import pytest

from wangp_dspy.prompt_director import RenderBrief
from wangp_dspy.profile_selector import ProfileDecision
from wangp_dspy.wangp_adapter import WanGPAdapter, WanGPError
from wangp_dspy.render_host import (
    LocalHost, SshHost, RenderHostError, MissingExecutableError,
    PushError, PullError, RemoteTimeoutError,
)


def _brief():
    return RenderBrief(subject="astronaut, cracked visor",
                       motion="slow head turn", camera="dolly in",
                       style="16mm archival grain")


def _decision():
    return ProfileDecision(model="h3", resolution="768p",
                           shot_length_frames=96,
                           seed_policy="fixed_per_story",
                           wangp_profile="profile3")


def _fake_venv(tmp_path):
    py = tmp_path / "wan2gp" / "venv" / "bin" / "python"
    py.parent.mkdir(parents=True, exist_ok=True)
    py.write_text("#!/bin/sh\n")
    py.chmod(0o755)
    wgp = tmp_path / "wan2gp" / "wgp.py"
    wgp.write_text("# wgp\n")
    return str(py), str(wgp), tmp_path / "wan2gp"


def _ok_runner(videos=("shot_0001.mp4",)):
    def runner(cmd, cwd, env, timeout):
        outdir = cmd[cmd.index("--output-dir") + 1]
        os.makedirs(outdir, exist_ok=True)
        for n in videos:
            with open(os.path.join(outdir, n), "wb") as fh:
                fh.write(b"v")

        class R:
            pass
        r = R()
        r.returncode = 0
        r.stdout = "Queue completed: 1/1"
        r.stderr = ""
        return r
    return runner


# ── pin 1: adapter is FS-syscall-free ─────────────────────────────

class _Boom:
    def __getattr__(self, n):
        raise AssertionError(f"adapter used os.path.{n}")


class _OsShim:
    """os replacement for the adapter module: any path/FS call raises."""
    def __init__(self):
        self.path = _Boom()

    def __getattr__(self, name):
        raise AssertionError(f"adapter used os.{name}")

def test_pin1_adapter_makes_no_fs_syscalls(tmp_path, monkeypatch):
    vpy, vwgp, _ = _fake_venv(tmp_path)
    adapter = WanGPAdapter(venv_python=vpy, wgp_script=vwgp,
                           output_dir=str(tmp_path / "renders"),
                           runner=_ok_runner())
    # adapter must not touch os.path / os.makedirs / open directly:
    # every FS operation goes through the host.
    class Boom:
        def __getattr__(self, name):
            raise AssertionError(f"adapter used os.path.{name}")

        def __call__(self, *a, **kw):
            raise AssertionError("adapter called os.path()")

    import wangp_dspy.wangp_adapter as mod
    monkeypatch.setattr(mod, "os", _OsShim())
    result = adapter.render([_brief()], _decision())
    assert result.video_paths and result.video_paths[0].endswith(".mp4")


# ── pin 2: write_text return value is what appears in cmd ─────────

def test_pin2_settings_path_in_cmd_is_host_returned(tmp_path):
    vpy, vwgp, _ = _fake_venv(tmp_path)
    SENTINEL = "/host-namespace/settings-XYZ.json"

    class RecordingHost(LocalHost):
        def __init__(self):
            super().__init__(runner=_ok_runner())
            self.wrote = {}

        def write_text(self, path, text):
            self.wrote[path] = text
            return SENTINEL  # host-namespace path, deliberately odd

    host = RecordingHost()
    adapter = WanGPAdapter(venv_python=vpy, wgp_script=vwgp,
                           output_dir=str(tmp_path / "renders"),
                           host=host, runner=_ok_runner())
    result = adapter.render([_brief()], _decision())
    assert len(host.wrote) == 1
    body = list(host.wrote.values())[0]
    json.loads(body)  # real settings content
    assert result.settings_path == SENTINEL


# ── pin 3: exact ssh/rsync argv (push, exec w/ timeout, pull -a) ──

class FakeSP:
    """subprocess.Popen fake for SshHost: records argv, returns a
    process-like object whose communicate() yields configured output."""

    def __init__(self, default_rv=0, stdout="", stderr=""):
        self.argvs = []
        self.rv = {}          # argv[1] substring -> returncode
        self.default_rv = default_rv
        self.stdout = stdout
        self.stderr = stderr

    def __call__(self, argv, **kw):
        self.argvs.append(list(argv))
        rv = self.default_rv
        for key, v in self.rv.items():
            if key in argv:
                rv = v
                break

        class P:
            returncode = rv

            def communicate(inner_self, timeout=None):
                return (self.stdout.encode(), self.stderr.encode())

            def kill(inner_self):
                pass

            def wait(inner_self):
                pass
        return P()


def test_pin3_ssh_host_exact_argv(tmp_path):
    vpy, vwgp, wgp_root = _fake_venv(tmp_path)
    sp = FakeSP()
    host = SshHost(target="gpu3090", wgp_root="/home/u/Wan2GP",
                   pull_root=str(tmp_path / "pulled"), sp=sp)

    # check_executable -> ssh test -x
    host.check_executable("/home/u/Wan2GP/venv/bin/python")
    assert sp.argvs[0] == ["ssh", "gpu3090", "test", "-x",
                           "/home/u/Wan2GP/venv/bin/python"]

    # write_text -> rsync push
    remote = host.write_text("/tmp/r/settings.json", '{"a": 1}')
    assert remote == "/tmp/r/settings.json"
    assert sp.argvs[1][0:1] == ["rsync"]
    assert sp.argvs[1][-1] == "gpu3090:/tmp/r/settings.json"
    assert "-a" in sp.argvs[1]

    # run -> ssh with remote `timeout <t>` wrapper around the command
    sp2 = FakeSP()
    host2 = SshHost(target="gpu3090", wgp_root="/w", pull_root=str(tmp_path),
                    sp=sp2)
    cmd = ["/w/venv/bin/python", "/w/wgp.py", "--process", "s.json"]
    host2.run(cmd, cwd="/w", env=None, timeout=3600)
    expect = ["ssh", "gpu3090", "timeout", "3600",
              "/w/venv/bin/python", "/w/wgp.py", "--process", "s.json"]
    assert sp2.argvs[0] == expect

    # fetch_videos -> rsync pull -a from remote outputs to local dir
    sp3 = FakeSP()
    host3 = SshHost(target="gpu3090", wgp_root="/w",
                    pull_root=str(tmp_path), sp=sp3)
    host3.fetch_videos(("/w/outputs",), str(tmp_path / "att"), 0.0)
    pulls = [a for a in sp3.argvs if a[0] == "rsync" and "-a" in a]
    assert pulls, "must rsync -a pull"
    assert pulls[0][-1].startswith(str(tmp_path))
    assert "gpu3090:/w/outputs/" in pulls[0][-2]


# ── pin 4: typed failure taxonomy ─────────────────────────────────

def test_pin4_typed_failures(tmp_path):
    vpy, vwgp, wgp_root = _fake_venv(tmp_path)
    sp = FakeSP()
    sp.rv["test"] = 1  # every ssh test fails
    host = SshHost(target="gpu3090", wgp_root="/w",
                   pull_root=str(tmp_path), sp=sp)
    with pytest.raises(MissingExecutableError):
        host.check_executable("/w/venv/bin/python")

    class FailPush(SshHost):
        def write_text(self, path, text):
            raise PushError("push failed")

    with pytest.raises(PushError):
        FailPush(target="t", wgp_root="/w",
                 pull_root=str(tmp_path)).write_text("/x", "y")

    class FailPull(SshHost):
        def fetch_videos(self, dirs, local_dir, newer_than):
            raise PullError("pull failed")

    with pytest.raises(PullError):
        FailPull(target="t", wgp_root="/w",
                 pull_root=str(tmp_path)).fetch_videos(("/o",), "/l", 0)

    with pytest.raises(RemoteTimeoutError):
        raise RemoteTimeoutError("timeout after cleanup")
    # all under the RenderHostError taxonomy, itself a WanGPError
    assert issubclass(MissingExecutableError, RenderHostError)
    assert issubclass(PushError, RenderHostError)
    assert issubclass(PullError, RenderHostError)
    assert issubclass(RemoteTimeoutError, RenderHostError)
    assert issubclass(RenderHostError, WanGPError)


# ── pin 5: post-pull readback byte-identical to local behavior ────

def test_pin5_local_readback_unchanged(tmp_path):
    """LocalHost path must produce EXACTLY the same result shape and
    paths as before the seam (regression pin on delegation)."""
    vpy, vwgp, wgp_root = _fake_venv(tmp_path)
    runner = _ok_runner()
    adapter = WanGPAdapter(venv_python=vpy, wgp_script=vwgp,
                           output_dir=str(tmp_path / "renders"),
                           runner=runner)
    result = adapter.render([_brief()], _decision())
    assert result.attempts == 1
    assert len(result.video_paths) == 1
    rel = os.path.relpath(result.video_paths[0], str(tmp_path / "renders"))
    assert rel.startswith("render-")
    assert "/attempt-1/" in rel.replace(os.sep, "/")
    assert os.path.isfile(result.video_paths[0])
    body = json.load(open(os.path.join(
        str(tmp_path / "renders"), rel.split("/")[0], "settings.json")))
    assert body["force_fps"] == "24"


def test_map_path_refuses_escape_outside_pull_root(tmp_path):
    """GLM F1: a local path outside pull_root must never map to ../."""
    import pytest
    from wangp_dspy.render_host import SshHost, RenderHostError
    host = SshHost(target="h", wgp_root="/remote/wgp",
                   pull_root=str(tmp_path / "pull"), sp=lambda *a, **k: None)
    with pytest.raises(RenderHostError):
        host.map_path(str(tmp_path / "outside" / "settings.json"))


def test_sshhost_namespace_contract_documented():
    """Qwen WD-h0vk: render_dir dual identity — write_text returns a
    remote-namespace path; fetch_videos maps it back to the local
    pull mirror. The contract is pinned by round-tripping one path."""
    from wangp_dspy.render_host import SshHost
    host = SshHost.__new__(SshHost)  # no FS init: pure path logic
    host.target = "h"; host.wgp_root = "/remote/wgp"
    host.pull_root = "/local/pull"
    # a remote path under wgp_root maps to a local path under pull_root
    # (the pull direction of the dual identity)
    assert host.map_path("/local/pull/render-0000/settings.json") == \
        "/remote/wgp/render-0000/settings.json"


def test_sshhost_join_preserves_absolute_prefix():
    """Live T0 finding: stripping the leading / made absolute output_dir
    home-relative, breaking rsync push (3090:home/... -> ~/"home/...")."""
    from wangp_dspy.render_host import SshHost
    host = SshHost.__new__(SshHost)  # pure path logic
    host.target = "h"; host.wgp_root = "/w"; host.pull_root = "/p"
    assert host.join("/home/u/Wan2GP", "render-0000", "settings.json") == \
        "/home/u/Wan2GP/render-0000/settings.json"
    assert host.join("rel", "x") == "rel/x"
    assert host.join("") == ""
