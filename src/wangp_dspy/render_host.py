"""WD-h0vk: RenderHost seam — renderer locality (Qwen-approved design).

The adapter makes NO direct filesystem syscalls; every FS/exec
operation goes through a RenderHost. LocalHost preserves today's
byte-identical local behavior; SshHost runs the renderer on a remote
GPU box over ssh with rsync push/pull. Remote timeouts wrap the
command in `timeout <t>` REMOTE-SIDE — killing only the local ssh
process would leak the remote GPU.

Typed taxonomy (all WanGPError subclasses so callers keep one except
path): RenderHostError -> MissingExecutableError / PushError /
PullError / RemoteTimeoutError.
"""
from __future__ import annotations

import os
import subprocess
import time
from typing import Callable, Optional, Sequence

from wangp_dspy.wangp_adapter import WanGPError


class RenderHostError(WanGPError):
    """Base: a host-transport failure (local FS or ssh/rsync)."""


class MissingExecutableError(RenderHostError):
    """Renderer venv/wgp missing or not executable on the host."""


class PushError(RenderHostError):
    """Pushing files to the host failed (rsync)."""


class PullError(RenderHostError):
    """Pulling rendered outputs from the host failed (rsync)."""


class RemoteTimeoutError(RenderHostError):
    """Remote command exceeded its timeout AND remote-side cleanup
    (`timeout <t>`) already killed it; the remote GPU is free."""


def _sp(argv, **kw):
    return subprocess.Popen(argv, **kw)


def _mkresult(returncode, stdout, stderr):
    class _R:
        pass
    r = _R()
    r.returncode = returncode
    r.stdout = stdout
    r.stderr = stderr
    return r


class LocalHost:
    """Today's behavior, verbatim, behind the seam."""

    def __init__(self, runner: Optional[Callable] = None):
        self._runner = runner

    # -- FS surface -------------------------------------------------
    def check_executable(self, path: str) -> None:
        if not (os.path.isfile(path) and os.access(path, os.X_OK)):
            raise MissingExecutableError(
                f"venv python not found or not executable: {path!r} — "
                "is the Wan2GP venv present?")

    def write_text(self, path: str, text: str) -> str:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        return path

    def makedirs(self, path: str) -> None:
        os.makedirs(path, exist_ok=True)

    def join(self, *parts: str) -> str:
        return os.path.join(*parts)

    def prepare_run(self, wgp_script: str):
        """(cwd, env) for a wgp invocation — local conventions."""
        env = dict(os.environ)
        local_bin = os.path.join(os.path.expanduser("~"), ".local", "bin")
        env["PATH"] = local_bin + os.pathsep + env.get("PATH", "")
        cwd = os.path.dirname(os.path.abspath(wgp_script)) or "."
        return cwd, env

    def run(self, cmd, cwd, env, timeout, runner=None):
        runner = runner or self._runner
        if runner is None:
            raise RenderHostError(
                "LocalHost.run requires a runner (adapter injects its own)")
        return runner(cmd, cwd, env, timeout)

    def fetch_videos(self, dirs: Sequence[str], local_dir: str,
                     newer_than: float) -> tuple:
        """Local: scan directly. Remote implementations pull then scan
        the local mirror — the returned paths are local-namespace."""
        found = []
        for d in dirs:
            if not os.path.isdir(d):
                continue
            for n in os.listdir(d):
                if not n.lower().endswith((".mp4", ".mov", ".webm")):
                    continue
                p = os.path.join(d, n)
                try:
                    if os.path.getmtime(p) + 1e-6 < newer_than:
                        continue
                except OSError:
                    continue
                found.append(p)
        return tuple(sorted(found))


class SshHost(LocalHost):
    """Remote GPU host: ssh exec (timeout wrapped remote-side) +
    rsync push/pull. Paths the ADAPTER sees are LOCAL (pull_root
    namespace); paths the RUNNER sees are remote (wgp_root namespace).

    ``map_path`` translates local -> remote for cmd construction; the
    adapter passes host-returned (remote) settings paths straight
    through, so no guessing ever happens in the adapter.

    NAMESPACE CONTRACT (Qwen, WD-h0vk): ``render_dir`` has a dual
    identity — it is the REMOTE write path during the run (settings
    live and wgp reads them there) and the LOCAL pull mirror after
    ``fetch_videos`` materializes it. The default ``wgp_outputs_dir``
    derivation (<wgp_root>/outputs) is posix because wgp_root is a
    remote posix path by construction; local consumers only see it
    after pull. Cross-namespace consumers must go through
    ``map_path``/``write_text`` returns, never os.path.join mixing.
    """

    def __init__(self, *, target: str, wgp_root: str, pull_root: str,
                 sp: Callable = _sp, port: Optional[int] = None):
        super().__init__()
        self.target = target
        self.wgp_root = wgp_root
        self.pull_root = os.path.abspath(pull_root)
        self.sp = sp
        self.port = port
        os.makedirs(self.pull_root, exist_ok=True)

    # -- ssh/rsync plumbing ----------------------------------------
    def _ssh_base(self):
        base = ["ssh"]
        if self.port:
            base += ["-p", str(self.port)]
        base.append(self.target)
        return base

    def _run_ssh(self, argv, **kw):
        return self.sp(self._ssh_base() + argv, **kw)

    def _run(self, argv, what):
        proc = self.sp(argv, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE)
        try:
            out, err = proc.communicate()
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
            raise RemoteTimeoutError(f"{what} timed out")
        return proc.returncode, \
            out.decode("utf-8", "replace"), \
            err.decode("utf-8", "replace")

    def map_path(self, local: str) -> str:
        """local pull_root namespace -> remote wgp_root namespace."""
        rel = os.path.relpath(local, self.pull_root)
        # GLM F1: refuse escapes — a local path outside pull_root must
        # never map to ../ outside wgp_root (rsync dest containment).
        if rel == ".." or rel.startswith(".." + os.sep):
            raise RenderHostError(
                "path escapes pull_root; refusing to map outside wgp_root")
        return self.wgp_root + "/" + rel.replace(os.sep, "/")

    # -- RenderHost surface ----------------------------------------
    def check_executable(self, path: str) -> None:
        rc, _o, err = self._run(
            self._ssh_base() + ["test", "-x", path], "ssh test -x")
        if rc != 0:
            raise MissingExecutableError(
                f"remote venv python not executable on {self.target}: "
                f"{path!r} ({err.strip()[:200]})")

    def write_text(self, path: str, text: str) -> str:
        """path is REMOTE-namespace; content pushed via rsync."""
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".json",
                                         delete=False) as tf:
            tf.write(text)
            local_tmp = tf.name
        try:
            rc, _o, err = self._run(
                ["rsync", "-a", local_tmp, f"{self.target}:{path}"],
                "rsync push")
        finally:
            os.unlink(local_tmp)
        if rc != 0:
            raise PushError(f"rsync push to {self.target}:{path} "
                            f"failed: {err.strip()[:300]}")
        return path

    def makedirs(self, path: str) -> None:
        """Remote mkdir -p (live T0 finding: rsync pushing a FILE does
        NOT create parent dirs, so the no-op made write_text fail on a
        fresh render-NNNN dir). Local pull mirror still lazy."""
        rc, _o, err = self._run(
            self._ssh_base() + ["mkdir", "-p", path], "ssh mkdir")
        if rc != 0:
            raise RenderHostError(
                f"remote mkdir -p {path} on {self.target} failed: "
                f"{err.strip()[:200]}")

    def join(self, *parts: str) -> str:
        # preserve absoluteness: stripping leading "/" from the first
        # part turns an absolute output_dir into a home-relative path,
        # breaking rsync push ("3090:home/..." -> ~/"home/...").
        # Live T0 acceptance finding (WD-h0vk).
        parts = tuple(p for p in parts if p)
        if not parts:
            return ""
        lead = "/" if parts[0].startswith("/") else ""
        return lead + "/".join(p.strip("/") for p in parts)

    def run(self, cmd, cwd, env, timeout, runner=None):
        """cmd/cwd are REMOTE-namespace. `timeout <t>` wraps the
        command REMOTE-SIDE so an expired render is killed on the GPU
        box (killing local ssh alone would leak the GPU).

        Live T0 finding: wgp resolves 'models/_settings.json' against
        its CWD — without `cd <cwd>` first, ssh runs in the remote home
        and wgp dies on a relative path. Prefix `cd` runs cwd-setting
        without a shell (exec'ed via argv, no quoting hazards)."""
        t = int(timeout)
        argv = self._ssh_base() + ["timeout", str(t),
                                   "cd", cwd, "&&"] + list(cmd)
        proc = self.sp(argv, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE)
        try:
            out, err = proc.communicate(timeout=timeout + 30)
        except subprocess.TimeoutExpired:
            # ssh-side backstop (remote timeout should have fired
            # first); kill local ssh — remote `timeout` has already
            # reaped the renderer.
            proc.kill()
            proc.wait()
            raise RemoteTimeoutError(
                f"remote render exceeded {timeout}s; remote-side "
                "timeout reaped the GPU process")
        return _mkresult(proc.returncode,
                         out.decode("utf-8", "replace"),
                         err.decode("utf-8", "replace"))

    def fetch_videos(self, dirs: Sequence[str], local_dir: str,
                     newer_than: float) -> tuple:
        """Pull each remote output dir into the local mirror, then
        reuse the local scan on the mirror (mtime filter: rsync -a
        preserves remote mtimes, so 'newer than attempt start' works
        exactly as locally)."""
        os.makedirs(local_dir, exist_ok=True)
        for d in dirs:
            remote = d  # dirs arrive host-namespace (remote) already
            rc, _o, err = self._run(
                ["rsync", "-a", f"{self.target}:{remote}/",
                 local_dir + "/"], "rsync pull")
            if rc != 0:
                raise PullError(f"rsync pull from {self.target}:{remote}"
                                f" failed: {err.strip()[:300]}")
        return LocalHost.fetch_videos(
            self, (local_dir,), local_dir, newer_than=newer_than)
