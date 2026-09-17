# 73 — Repo-owned remote VibeVoice dispatch

Status: IMPLEMENTED IN LOCAL CHANGESET; pending review/merge. No live GPU run.

## Boundary

Finding #52 supplied local generation and publishing, but did not dispatch the
supplier on a model-equipped host. `supply_vibevoice_turns_remote` now stages
explicitly selected local references with RenderHost asset methods, writes an
isolated run manifest, executes `python -m predict.vibevoice` using the new
`run_argv` host seam, and fetches raw WAVs, prepared WAVs, provenance and report
with `fetch_file`. It introduces no separate SSH/rsync helper or render dispatch.

CLI: supply `--remote-target`, `--host-python`, `--host-repo`, `--host-model`,
and `--report` alongside the manifest. `WANGP_ASSET_MAP` must cover the manifest
directory (for the unique run namespace) and each reference. Host paths must be
absolute. The deployed host checkout and Python environment must already provide
the repo module, VibeVoice backend, ffmpeg/ffprobe and Whisper. Code/model deployment
and GPU availability are not inferred or performed by this command.

## Fail-closed checks

- All supplied reference audio streams must measure at least 2 seconds and pass
  the non-silence check before dispatch or backend construction. No padding of a
  short reference is permitted. The host repeats this preflight before loading
  the model. Clean, single-speaker selection remains the operator's responsibility;
  duration/RMS measurements do not certify speaker isolation or remove silence.
- Structured remote argv preserves spaces, quotes and shell metacharacters.
  Remote timeout is enforced on-host, with a local SSH timeout backstop.
- Fresh remote namespaces and empty local pull directories prevent stale-file
  fallback. Existing local output/report paths are rejected; remote resume is
  intentionally unsupported.
- Every expected turn, provenance identity, reference/raw/prepared hash,
  preparation record and transcript pre-gate must match before local publication.
  Missing, invalid, failed or mismatching host artifacts yield no complete report.
  The original host report is retained beside the localized report; localized
  provenance retains host execution paths.

## Verification

Model-free tests in `tests/test_vibevoice.py` exercise local #52 behavior, short
and invalid references, complete host staging/execution/pull, missing artifacts,
tampered hashes/provenance/reports/gates, and failed execution.
`tests/test_render_host.py` pins argv boundary preservation for spaces, quotes and
shell metacharacters. Tests use injected seams and do not load a GPU model or
contact the render host. No live supply success or finished render is claimed.
