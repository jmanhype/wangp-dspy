"""Fetch and optionally stage the content-addressed SyncNet v2 model."""
from __future__ import annotations

import argparse
import hashlib
import sys
import tempfile
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parent.parent
from qc.audio_critic.syncnet_runner import (  # noqa: E402
    SYNCNET_MODEL_SHA256, SYNCNET_MODEL_URL,
)


def fetch(destination: Path) -> str:
    destination.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    temporary = destination.with_name(destination.name + ".partial")
    try:
        with urllib.request.urlopen(SYNCNET_MODEL_URL, timeout=300) as source:
            with temporary.open("wb") as target:
                while True:
                    chunk = source.read(1024 * 1024)
                    if not chunk:
                        break
                    target.write(chunk)
                    digest.update(chunk)
        actual = digest.hexdigest()
        if actual != SYNCNET_MODEL_SHA256:
            temporary.unlink(missing_ok=True)
            raise ValueError(
                f"SyncNet model SHA-256 mismatch: {actual}")
        temporary.replace(destination)
        return actual
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def stage_remote(local: Path, target: str, remote_path: str) -> str:
    from host.render_host import SshHost

    host = SshHost(
        target=target, wgp_root=str(Path(remote_path).anchor or "/"),
        pull_root=str(ROOT / "datasets" / "runs" / "pull"))
    remote = Path(remote_path)
    host.run_probe(["mkdir", "-p", str(remote.parent)], timeout=60)
    return host.push_file(str(local), remote_path)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="fetch-syncnet-model")
    parser.add_argument(
        "--output", type=Path,
        default=ROOT / "assets" / "models" / "syncnet_v2.model")
    parser.add_argument("--remote-target")
    parser.add_argument("--remote-path")
    args = parser.parse_args(argv)
    try:
        if args.output.is_file():
            actual = hashlib.sha256(args.output.read_bytes()).hexdigest()
            if actual != SYNCNET_MODEL_SHA256:
                raise ValueError(
                    f"existing SyncNet model SHA-256 mismatch: {actual}")
        else:
            actual = fetch(args.output)
        if args.remote_target or args.remote_path:
            if not (args.remote_target and args.remote_path):
                raise ValueError(
                    "--remote-target and --remote-path must be supplied together")
            stage_remote(args.output, args.remote_target, args.remote_path)
        print(SYNCNET_MODEL_SHA256)
        return 0
    except Exception as exc:
        print(f"fetch-syncnet-model refused: {type(exc).__name__}: {exc}",
              file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
