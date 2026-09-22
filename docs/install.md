# Installing Wangp

## Prerequisites

- Python 3.11 or newer.
- [`uv`](https://docs.astral.sh/uv/), plus `ffmpeg` and `ffprobe` on `PATH`.
- About 1 GB of free disk space. A render host, GPU, model download, API key, and SSH configuration are **not** required for installation or the no-GPU lane.

If `uv` is missing, install it first:

```bash
curl -LsSf https://astral.sh/uv/install.sh -o uv-installer.sh
```

Inspect the downloaded installer, then run it:

```bash
sh uv-installer.sh
```

## One-command install

Download the repository installer:

```bash
curl -LsSf https://raw.githubusercontent.com/jmanhype/wangp-dspy/main/install.sh -o install.sh
```

Then invoke the saved script. No root or sudo is needed:

```bash
sh install.sh
```

To preview the commands, run `sh install.sh --dry-run`; to install from another checkout or Git URL, pass `--source <path-or-url>`. The script fail-closes before installation when `uv` is missing.

## Verify

Run `wgp doctor`. A ready local install ends with `ready=yes`; it checks Python, uv, dependencies, media tools, local disk, and the queue runtime, while leaving an unconfigured render host safely skipped. Ensure uv's executable directory (typically `~/.local/bin`) is on `PATH`.

The tool install is the **install-only surface**: `doctor`, `brief validate`, and plain `content` work without a checkout, while provenance-bearing `plan`, `recipe write`, `recipe verify`, `release verify`, and `content --submit` need a Wangp Git checkout. An installed `plan` outside a checkout now exits `2` with `INPUT_INVALID`, redacts the package location, and says to run inside a checkout or set `WANGP_REPOSITORY_ROOT=<repository>` (a `--repository-root` flag is also available on repository-scoped verbs); with that explicit checkout, provenance is recorded for the named checkout without weakening the no-repository/no-provenance rule.

To install and obtain that checkout in one script invocation, pass an absent destination:

```bash
sh install.sh --checkout "$HOME/src/wangp-dspy"
```

The installer resolves uv's real executable directory with `uv tool dir --bin` (unless `UV_TOOL_BIN_DIR` overrides it), verifies `wgp` exists there, clones the selected repository, and prints the exact `cd`, `uv sync`, and no-GPU quickstart commands.

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
