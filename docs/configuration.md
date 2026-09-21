# Wangp render-host configuration

Wangp planning is deliberately usable with no render host. The optional render lane resolves one
complete host before it can construct SSH or invoke the existing preflight seam.

## Keys

| Key | Environment override | Meaning |
| --- | --- | --- |
| `host.target` | `WANGP_SSH_TARGET` | SSH destination alias, or `localhost` when running on the render host. |
| `host.wgp_root` | `WANGP_WGP_ROOT` | Absolute remote (or on-host) Wan2GP checkout root. |
| `host.pull_root` | `WANGP_PULL_ROOT` | Absolute local directory used to stage inputs and pull outputs. |
| `host.wgp_python` | `WANGP_WGP_PYTHON` | Absolute Python executable used to run Wan2GP. This supports arbitrary virtual environments, Conda, and system-Python installations. |

All three keys are required together. Partial configuration is an error that names every missing
key; Wangp never fills a gap with an operator-specific host or home directory. Rendering also
needs `host.wgp_python`; a detected `localhost` target can safely fill it from the current
Python executable, while remote hosts require an explicit absolute path. The SyncNet-specific
`WANGP_SYNCNET_PYTHON` override still wins when present, with `host.wgp_python` as its fallback.

## Resolution precedence

For each key independently:

1. Environment variable: `WANGP_SSH_TARGET`, `WANGP_WGP_ROOT`, `WANGP_PULL_ROOT`, or `WANGP_WGP_PYTHON`.
2. User configuration: `~/.config/wangp/config.toml`, or the file selected by `WANGP_CONFIG`.
3. Repository configuration: `wangp.toml` beside the installed package or in the current checkout.
4. Safe local detection, described below.

A lower layer is used only when no higher layer supplies that key. `wgp doctor` reports each
resolved value as `environment`, `user_config`, `repository_config`, or `detection`, including the
originating file where applicable. Absent values are reported as `unconfigured`.

The repository's `wangp.toml` is a commented template:

```toml
[host]
# target = "your-ssh-alias"
# wgp_root = "/absolute/path/to/Wan2GP"
# pull_root = "/absolute/local/staging/path"
# wgp_python = "/absolute/path/to/python"
```

For a user-level installation, copy the values into `~/.config/wangp/config.toml`:

```toml
[host]
target = "your-ssh-alias"
wgp_root = "/absolute/path/to/Wan2GP"
pull_root = "/absolute/local/staging/path"
wgp_python = "/absolute/path/to/python"
```

Unknown tables or fields, empty values, non-string path values, and relative `wgp_root`,
`pull_root`, or `wgp_python` values are rejected with the file/environment and field context.
`WANGP_CONFIG` may select any filename, but it does not change key precedence.

## Safe local detection

If neither `host.target` nor `host.wgp_root` is otherwise configured, Wangp looks only at local
filesystem markers:

- `<repository-root>/Wan2GP/wgp.py`
- a sibling `<repository-root>/../Wan2GP/wgp.py`
- `<current-directory>/Wan2GP/wgp.py`

If one exists, `host.wgp_root` is that local checkout, `host.target` is `localhost`, and the source
reported by doctor is `detection`. If either target or root was explicitly configured, detection
does not fill the other side, so explicit remote settings cannot be mixed with a local checkout.
If no marker exists, both remain unconfigured. Detection never runs SSH, DNS, GPU, model-endpoint,
or remote-service probes and never guesses a remote alias.

When no other pull root is configured, a source checkout uses
`<repository-root>/datasets/runs/pull`. An installed wheel uses
`${XDG_DATA_HOME:-~/.local/share}/wangp/runs/pull`, so it never creates data beneath site-packages.
These defaults do not make an incomplete host usable for rendering.

## No-host and partial-host behavior

With no host:

```bash
uv run --frozen --extra dev wgp doctor
uv run --frozen --extra dev wgp plan --brief datasets/content_briefs/lf004-operator-dogfood-56f/brief.json --plates datasets/content_briefs/lf004-operator-dogfood/plates --out "${TMPDIR:-/tmp}/wangp-cli/plan.json"
```

`doctor` reports `host_configuration` as skipped and remains ready. The plan still emits the
documented four-clip, no-GPU summary. Configuration loading performs no host call.

A host-dependent entry point fails before constructing SSH with one actionable message naming every
missing key, the corresponding environment variables, the config-file locations, and `wgp doctor`.
For example, a completely unconfigured host names both `host.target` and `host.wgp_root`; a missing
pull root names only `host.pull_root`.

## Explicit host probing

`wgp doctor` only resolves and reports configuration; it does not contact the host. The explicit
command below is the only doctor mode that invokes the existing preflight seam:

```bash
uv run --frozen --extra dev wgp doctor --probe-host --models models.json
```

The configured `host.wgp_root` is passed unchanged as both the model namespace and disk-check root.
Preflight's SSH, model, disk, GPU, and QC checks and thresholds are unchanged.
