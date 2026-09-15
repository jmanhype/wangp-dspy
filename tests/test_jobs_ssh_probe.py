"""SshHost.run_probe — host-seam extension consumed by preflight."""
import pytest

from host.render_host import SshHost


class FakeProc:
    def __init__(self, rc, out, err):
        self.returncode = rc
        self._out = out.encode()
        self._err = err.encode()

    def communicate(self, timeout=None):
        return self._out, self._err


def make_host(tmp_path, *, procs=None):
    calls = []

    def sp(argv, **kw):
        calls.append(argv)
        return (procs or {}).get(tuple(argv[1:]) if False else None) or \
            FakeProc(0, "ok", "")

    host = SshHost(target="3090", wgp_root="/home/straughter/Wan2GP",
                   pull_root=str(tmp_path / "pull"), sp=sp)
    return host, calls


def test_run_probe_returns_rc_stdout_stderr(tmp_path):
    def sp(argv, **kw):
        return FakeProc(0, "abc123  /path/model.safetensors\n", "")
    host = SshHost(target="3090", wgp_root="/w", pull_root=str(tmp_path),
                   sp=sp)
    rc, out, err = host.run_probe(["sha256sum", "/path/model.safetensors"],
                                  timeout=15)
    assert rc == 0
    assert out.startswith("abc123")
    assert err == ""


def test_run_probe_carries_remote_argv_over_ssh(tmp_path):
    seen = {}

    def sp(argv, **kw):
        seen["argv"] = argv
        return FakeProc(0, "", "")

    host = SshHost(target="3090", wgp_root="/w", pull_root=str(tmp_path),
                   sp=sp)
    host.run_probe(["df", "-BG", "/mnt/bulk"], timeout=10)
    argv = seen["argv"]
    assert argv[0] == "ssh"
    import shlex
    assert shlex.split(argv[-1]) == ["df", "-BG", "/mnt/bulk"]


def test_run_probe_failure_returns_rc(tmp_path):
    def sp(argv, **kw):
        return FakeProc(1, "", "No such file")
    host = SshHost(target="3090", wgp_root="/w", pull_root=str(tmp_path),
                   sp=sp)
    rc, out, err = host.run_probe(["sha256sum", "/gone"], timeout=10)
    assert rc == 1
    assert "No such file" in err
