# Wangp

Wangp is a governed short-film generation engine for the MiniMax H3 / Wan2GP render stack. A typed content brief becomes a deterministic, no-GPU plan; production runs enter a durable queue, render on a trusted host, and must pass Whisper transcript, identity-vision, three-frame mouth-box, and SyncNet audiovisual gates before assembly. Every reviewable result is anchored by hashes and repository provenance rather than by an unsupported quality claim.

## What Wangp does

- Validates typed content briefs, cast plates, and turn audio before planning.
- Produces deterministic dry-run plans with no model inference, SSH, queue work, or GPU use.
- Submits governed per-cut jobs to a durable SQLite queue for a single trusted render host.
- Applies fail-closed pre-render and post-render transcript, vision, mouth-box, and SyncNet gates.
- Assembles accepted cuts and writes hash-identified media, probes, contact sheets, and `final-provenance.json`.
- Preserves rejected attempts and operator decisions as evidence instead of overwriting them.

## Requirements

- Python 3.11 or newer.
- [`uv`](https://docs.astral.sh/uv/) for reproducible environment installation.
- `ffprobe` on `PATH` for planning; `ffmpeg` as well for the paths that prepare or
  post-process media (materializing absent guides, remuxing, assembly). Planning a brief whose
  guides already exist needs `ffprobe` only.
- A clean Git checkout for provenance-bearing planning and rendering.
- Optional for renders only: an SSH-reachable GPU host with the Wan2GP environment and required models.

The tested path below needs no API key, model download, SSH host, queue, or GPU.

## Install

From a fresh clone:

```bash
git clone https://github.com/jmanhype/wangp-dspy.git
cd wangp-dspy
uv sync --extra dev
```

CI and local development use the full command below. It is deliberately outside the tested quickstart block because executing it from the README doc test would recursively run that test.

```bash
uv run --frozen --extra dev pytest -q
```

## Tested no-GPU quickstart

Run the commands from the repository root. The first installs the locked development environment. The second consumes only committed assets and writes its outputs outside the checkout under `${TMPDIR:-/tmp}/wangp-quickstart`; this keeps repository provenance clean.

```bash
uv sync --extra dev
uv run --frozen --extra dev python scripts/run_content_brief.py --brief datasets/content_briefs/lf004-operator-dogfood-56f/brief.json --plates datasets/content_briefs/lf004-operator-dogfood/plates --output "${TMPDIR:-/tmp}/wangp-quickstart/plan.json" --run-dir "${TMPDIR:-/tmp}/wangp-quickstart/run"
```

Expected console shape:

```text
brief=sha256:<content-addressed-id> clips=4 plan=.../wangp-quickstart/plan.json
```

Expected `summary` object in `plan.json`:

| Field | Value |
| --- | --- |
| `clip_count` | `4` |
| `planned_duration_s` | `9.332` |
| `dry_run` | `true` |
| `gpu_work` | `false` |
| `queue_submitted` | `false` |

The command validates the committed LF004 brief, probes its four committed WAV guides, invokes the deterministic `run_film(..., dry_run=True)` planner, and writes canonical schema `wangp-dspy.content-plan/v1`. The artifact is a four-cut render plan plus `run/script.txt` and `run/run_ledger.json`; it is not a film and performs no model inference, SSH, queue submission, or GPU work.

`tests/test_readme_quickstart.py` extracts and executes both commands in a clean temporary Git worktree. The test also proves that an invalid brief and a missing cast plate fail with typed `ContentBriefError` output before a partial plan is written.

## `wgp` operator CLI

The product command is `wgp`. It is a thin wrapper over the tested engine seams, not a second planner:

```bash
uv run wgp doctor
uv run wgp plan --brief datasets/content_briefs/lf004-operator-dogfood-56f/brief.json --plates datasets/content_briefs/lf004-operator-dogfood/plates --out "${TMPDIR:-/tmp}/wangp-cli/plan.json"
```

`doctor` is safe in the no-host lane: it checks the local environment and reports the render-host seam as skipped. Planning keeps the same canonical no-GPU summary and prints the plan and ledger paths. See [docs/wgp-cli.md](docs/wgp-cli.md) for `brief validate`, durable `status`, provenance `review`, explicit host preflight, JSON output, and stable exit codes.

## Render-host configuration

The no-GPU lane requires no host. Rendering requires one complete host configuration with the keys `host.target`, `host.wgp_root`, and `host.pull_root`. Resolution precedence is environment variable, then `~/.config/wangp/config.toml` (or the file named by `WANGP_CONFIG`), then repository `wangp.toml`, then safe local detection. The variables are `WANGP_SSH_TARGET`, `WANGP_WGP_ROOT`, and `WANGP_PULL_ROOT`.

The committed `wangp.toml` is a commented template; it deliberately contains no host. Detection only checks local filesystem markers for a sibling `Wan2GP/wgp.py` checkout and never probes SSH, DNS, GPU, model, or remote services. With no complete host, `wgp doctor` remains ready and `wgp plan` works, while a render entry point fails before SSH with the exact missing keys. See [docs/configuration.md](docs/configuration.md).

## Optional GPU render lane

Actual rendering is intentionally separate from planning. Configure a complete host as described above, verify it with `wgp doctor`, and use `wgp doctor --probe-host --models MANIFEST` only when you explicitly want the existing preflight checks to contact that host. Running directly on the render host can set `host.target = "localhost"` (or `WANGP_SSH_TARGET=localhost`) while still supplying its absolute Wan2GP and pull roots.

Host preflight checks SSH, model hashes, disk headroom, GPU state, and the QC service before queue admission. The configured root is passed unchanged to that existing seam. Do not start a render merely to test this repository: CI and the quickstart prove the no-GPU path.

## Reviewing governed results

The preserved LF004 recovery run is the clearest review example:

- The four accepted LF004 recovery worker directories under
  `datasets/runs/pull/acceptance/<worker>/render-*/` — `worker-511ee9ee6a8f/render-0000`,
  `worker-8c113b8f1396/render-0001`, `worker-99f88572dfb7/render-0002`,
  `worker-fda9bc258c06/render-0003` — each carrying `raw.mp4` or `remux.mp4`, `render.log`,
  `settings.json`, `runtime-evidence.json`, and `qc-evidence.json`. Other
  `datasets/runs/pull/acceptance/*` directories are deliberately preserved partial or refused
  attempts and are not all complete; treat a directory as authoritative only when its
  `qc-evidence.json` exists.
- Staging and immutable provenance: `datasets/runs/provenance/lf004-operator-dogfood-56f-recovery-20260921/`.
- Final review bundle: `datasets/runs/pull/lf004-operator-dogfood-56f-recovery-20260921/`.
- Film and machine probe: `assembled.mp4` and `probe.json` in the final review bundle.
- Human review aids: `review/cut*.contact_sheet.jpg`, `review/film.contact_sheet.jpg`, and `review.md` in that bundle.
- Gate-to-source chain: `final-provenance.json` in the same bundle.

Read `probe.json` for duration, frame count, resolution, and SHA-256. Read `qc-evidence.json` for a rejected or accepted cut's transcript, vision, mouth-box, and SyncNet details. Read `final-provenance.json` by section (its top-level keys are serialized alphabetically, so do not read it as a narrative order): repository and input identities, per-cut gate results and media hashes, retry policy, assembly command, final-media hash, and operator approval status. Older LF002/LF003 review exports also appear under `renders/review_*`.

## Troubleshooting

- **Missing ffmpeg or ffprobe:** `ffprobe` is required for planning; brief validation probes supplied guide audio and fails before emitting a plan if `ffprobe` is unavailable or returns an unusable duration. `ffmpeg` is required only for paths that prepare or post-process media (materializing absent guides, remuxing, assembly). Install both and verify with `command -v ffprobe` and `command -v ffmpeg`.
- **Invalid brief or audio duration:** the CLI reports a typed `ContentBriefError` naming the field or turn. Correct the JSON, speaker roster, plate count, or guide duration and rerun. No partial plan should be trusted after a failure.
- **Missing or duplicate plates:** the plates directory must contain exactly one `anchor.*` and exactly one plate per named character. Resolve accidental duplicates or add the missing file; do not edit the plan to bypass discovery.
- **No render host configured:** this is expected for planning and is reported as a skipped doctor check. Before rendering, set `host.target`, `host.wgp_root`, and `host.pull_root` in `wangp.toml`, your user config, or the matching environment variables. Partial configuration fails closed and names every missing key.
- **Render-host disk headroom:** preflight blocks admission when the configured Wan2GP root lacks the configured free space. Free capacity or choose sanctioned storage without deleting run evidence; then rerun preflight.
- **Gate rejection:** open the failed worker's `qc-evidence.json`, its `render.log`, the queue database, and the run ledger. The failure class names the gate (for example Whisper, identity vision, mouth-box consensus, or SyncNet), and bounded retries preserve each attempt. Do not weaken a gate or fabricate a score to continue.
- **Opaque untracked embedded worktree:** planning can fail with `RepositoryIdentityError: untracked embedded repository or opaque directory changes are not safely hashable`. This is intentional fail-closed provenance behavior when Git reports an untracked directory such as `.claude/worktrees/*`: Wangp cannot safely attribute a plan to unknown, mutable content. Preserve any needed evidence, inspect `git status --short --untracked-files=normal`, remove only a disposable registered worktree with Git's worktree commands, move genuinely unrelated opaque content outside the checkout, or run from a fresh clean checkout. Do not disable provenance or ignore untracked paths.

## Architecture

- `predict/` — typed input schemas, deterministic planning, prompt/profile contracts, and pure validation.
- `services/director/` — brief-to-plan orchestration, schemas, lineage, and repository identity.
- `services/chain/` and `services/jobs/` — continuity planning, durable queue state, preflight, execution, and bounded retries.
- `host/` — SSH/render-host transport and the Wan2GP adapter; no direct host filesystem shortcuts.
- `qc/` — Whisper, vision, mouth-box, SyncNet, audio, and assembly evidence gates.
- `scripts/` — operator entry points for planning and queue execution.
- `datasets/` and `renders/` — committed run inputs and hash-addressed evidence/review artifacts.

The engine is deliberately product-shaped but not yet a one-command consumer product: planning is public and tested, rendering requires an explicitly configured trusted host, and governance/evidence are part of the runtime rather than release paperwork.

## Governance and evidence

Wangp development uses the Paivot/pvg workflow and nd stories. Plans and runs record repository commit and dirty-tree identity, artifact hashes, gate evidence, retries, and operator decisions. This discipline exists because generated film claims are easy to make and expensive to verify: evidence turns “it worked” into a reviewable chain. Rejections are retained, scores are never invented, and operator acceptance remains a separate human decision.

## Version, changes, contribution, and licences

- Current version: [VERSION](VERSION).
- Release history: [CHANGELOG.md](CHANGELOG.md); decision-record history remains in [docs/CHANGELOG.md](docs/CHANGELOG.md).
- Development and evidence rules: [CONTRIBUTING.md](CONTRIBUTING.md).
- Repository code licence: [LICENSE](LICENSE).
- Separate model and third-party constraints: [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
