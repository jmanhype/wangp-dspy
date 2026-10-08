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

## Clean-machine install, plan, and honest refusal

From a disposable Git checkout (not an operator checkout), this one command installs
the locked tool into an isolated workspace, clones another disposable checkout, emits
the tested LF004 no-GPU plan, and then refuses generation before SSH, model download,
queue admission, inference, or GPU work:

```bash
sh install.sh --source "$PWD" --clean-proof "${TMPDIR:-/tmp}/wangp-clean-machine"
```

The workspace must not already exist. The command deliberately exits `3` when host
and model authorization are absent. Its output must contain both state markers:
`PLAN_ONLY ... generated_artifact=false` and `GENERATION_REFUSED ... exit=3`.
It also emits the established typed diagnostics (`HOST_CONFIGURATION_INCOMPLETE`
for a missing host and `MODEL_MANIFEST_REQUIRED` for absent model provenance) with
safe next actions. The generated `proof/blocked-record.json` records command argv,
source and resolved commit, dirty state, tool identities, plan hash and summary, and
`host_run_verified=false`.

This is install-and-plan evidence only. It is never generated-artifact evidence.
The generated-artifact half remains blocked pending per-batch render-host authorization,
model-download approval, and a complete authorized host/model manifest.

## Separately authorized clean-machine H3 generated proof

WD-bw0h records the operator-approved `Authorize` no-new-download retry. The
committed authorization for that retry has been consumed by recorded typed
failures; the command below is the historical command shape, not permission to
rerun it. A fresh generated proof requires a new committed authorization path.

```bash
sh install.sh --source "$PWD" --clean-generated-proof "${TMPDIR:-/tmp}/wangp-clean-generated" --generated-authorization datasets/runs/maestro-parity/clean-generated/operator-authorization.json --generated-manifest datasets/runs/maestro-parity/clean-generated/model-assets.json
```

Unlike `--clean-proof`, this mode supplies complete committed authorization, host, and four-asset manifest inputs before SSH. It uses isolated HOME/cache/tool/checkout/pull paths, verifies the four exact local H3 assets, admits exactly one durable H3 standard-create queue job, and runs the existing Wan2GP adapter under offline Hub variables. A v2 authorization binds the exact SHA-256 bytes of the installer, recorder, canonical checker, and model manifest; this avoids a circular commit-hash reference while still rejecting any implementation drift. It declares no superseded relocations: root headroom must already pass, and the exact remote work root must be absent before staging. The command records native argv/log, queue/retry state, output hash, ffprobe metadata, first frame/contact sheet, objective gates, and the canonical checker result. It fails closed rather than substituting an existing artifact.

This section is authorization-scoped evidence for WD-bw0h, not a general download path. The no-GPU refusal command above remains the default clean-machine proof and still exits `3` without host contact.
The recorder rejects the retained authorization with `AUTHORIZATION_ALREADY_CONSUMED`
before creating a workspace. An authorized isolated runtime can be supplied through
the committed host configuration without rebuilding the absent legacy Wan2GP
virtual environment.

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
