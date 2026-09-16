# 59 — acceptance inputs were not staged by the runner

Status: CLOSED in PR #89 / commit `d63e75b`; acceptance inputs stage through
the RenderHost contract on `main`.

## Evidence

The LF002 fresh-clone bundle can commit its plate/reference/WAV inputs, but
`scripts/run_acceptance.py` did not publish them to the configured render
host. A successful run therefore depended on those assets already existing in
the remote mapped namespace. That violates the fresh-clone/repo-owned
execution contract even though the render itself used `render_for_job()`.

## Minimal fix

Before creating the durable queue, resolve the host and judge, then stage every
media-manifest and per-cut plate input through:

```text
RenderHost.map_asset()
RenderHost.makedirs()
RenderHost.push_asset()
```

Missing host seams fail closed. No direct scp/SSH transport is permitted.

## Resolution

`scripts/run_acceptance.py` resolves every media-manifest and per-cut plate
input through the required host seams before queue creation. Regression
coverage is in `tests/test_run_acceptance.py`; Finding #68 later added complete
local preflight before remote upload. The full suite at `9b70be1` passed 1380
tests with one intentional skip and no failures.
