# Finding #33 — no repo-owned acceptance bundle runner

**Status:** Confirmed and runner implemented 2026-09-07; current bundle is
blocked by Finding #35.

Before the closing PR, `assets/acceptance/staging_r2.json` was a committed data
bundle without a repo-owned CLI/module entrypoint that consumed it and performed the complete
`DirectorRun.plan -> DirectorRun.submit -> run_jobs` flow. `DirectorRun` is a
Python API and `scripts/run_film.py` accepts hand-supplied script/plate
arguments; neither reads the bundle format (including its media manifest).

That gap is now closed by `scripts/run_acceptance.py`. It normalizes the
bundle, resolves the premise, invokes `DirectorRun.plan`, submits to
`JobQueue`, drains through `run_jobs`, assembles with `assemble_media`, and
emits an append-only completed run record. It refuses before queue creation
when the premise cannot be resolved (Finding #35).

## Minimal PR

Add a repo-owned command (for example `scripts/run_acceptance.py`) that reads
the committed bundle, resolves the registered premise, invokes
`DirectorRun.plan`, submits to `JobQueue`, drains through `run_jobs`, and emits
the assembled artifact and append-only ledger. The command must reject an
unrecognized bundle schema and record the bundle SHA in the run record.
