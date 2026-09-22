# Installing Wangp

## Prerequisites

- Python 3.11 or newer.
- [`uv`](https://docs.astral.sh/uv/), plus `ffmpeg` and `ffprobe` on `PATH`.
- About 1 GB of free disk space. A render host, GPU, model download, API key, and SSH configuration are **not** required for installation or the no-GPU lane.

If `uv` is missing, install it first:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## One-command install

Install the latest `main` source into uv's user tool directory, then run the readiness check:

```bash
curl -LsSf https://raw.githubusercontent.com/jmanhype/wangp-dspy/main/install.sh | sh
```

No root or sudo is needed. To preview the commands, save or inspect `install.sh` and run `install.sh --dry-run`; to install from another checkout or Git URL, pass `--source <path-or-url>`. The script fail-closes before installation when `uv` is missing.

## Verify

Run `wgp doctor`. A ready local install ends with `ready=yes`; it checks Python, uv, dependencies, media tools, local disk, and the queue runtime, while leaving an unconfigured render host safely skipped. Ensure uv's executable directory (typically `~/.local/bin`) is on `PATH`.

The tool install is the **install-only surface**: `doctor`, `brief validate`, and `plan --brief <path> --plates <dir>` work with explicit input paths and do not need a checkout. It does not carry `VERSION`, `CHANGELOG.md`, Git metadata, or `datasets/` evidence. Repository-scoped operations—`recipe write`, `recipe verify`, `release verify`, and workflows that consume committed LF004 evidence—must be run from a clean checkout containing those files. An installed `release verify` therefore reports a release-version input failure rather than claiming readiness.

## Upgrade and uninstall

Repeat the one-command install; it requests `uv tool install --upgrade`. Remove the user tool with:

```bash
uv tool uninstall wangp-dspy
```

## Contributor path

Development uses a clone and the locked test environment:

```bash
git clone https://github.com/jmanhype/wangp-dspy.git
cd wangp-dspy
uv sync --extra dev
```

Run `uv run --frozen --extra dev pytest -q` before requesting review. The checkout remains required for provenance-bearing planning, recipes, release verification, and committed evidence.
