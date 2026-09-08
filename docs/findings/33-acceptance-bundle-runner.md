# Finding #33 — no repo-owned acceptance bundle runner

**Status:** Confirmed 2026-09-07; blocks the requested repo-only rerun.

`assets/acceptance/staging_r2.json` is a committed data bundle, but the repo
has no CLI/module entrypoint that consumes it and performs the complete
`DirectorRun.plan -> DirectorRun.submit -> run_jobs` flow. `DirectorRun` is a
Python API and `scripts/run_film.py` accepts hand-supplied script/plate
arguments; neither reads the bundle format (including its media manifest).

Starting the rerun therefore requires an ad-hoc wrapper, which would violate
the repo-only acceptance rule and recreate the staging seam this guard was
intended to remove.

## Minimal PR

Add a repo-owned command (for example `scripts/run_acceptance.py`) that reads
the committed bundle, resolves the registered premise, invokes
`DirectorRun.plan`, submits to `JobQueue`, drains through `run_jobs`, and emits
the assembled artifact and append-only ledger. The command must reject an
unrecognized bundle schema and record the bundle SHA in the run record.
