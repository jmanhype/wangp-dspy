# 59 — acceptance inputs were not staged by the runner

Status: OPEN; source repair staged for review.

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
