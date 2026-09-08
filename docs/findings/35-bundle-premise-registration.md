# Finding #35 — acceptance bundle has no resolvable DG premise roster

**Status:** Confirmed while executing the repo-owned runner, 2026-09-07.

`assets/acceptance/staging_r2.json` declares `media_manifest.premise_id` as
`dg-acceptance`, but `datasets/lost-futures/index.json` contains only `lf-001`
through `lf-003`. The bundle also carries no `premise` object or character
descriptions. `scripts/run_acceptance.py` therefore refuses before queue
creation; it cannot construct the `DirectorRun` roster or send identity-rich
context to the vision judge without inventing session knowledge.

## Minimal PR

Register the Devil's Grandma premise in the repo index (including stable
character names/SN tags/descriptions), or add a signed `bundle.premise` object
with the same fields. Ensure the media manifest plate keys and per-turn audio
speakers resolve to that roster. Then the runner can plan and submit without
out-of-band creative data.
