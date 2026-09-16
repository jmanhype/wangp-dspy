# 60 — chain advance trusts an occupied remote final-artifact path

Status: OPEN; source repair staged for review.

## Evidence

The first fresh-clone LF002 cut reproduced the operator-accepted cut exactly:

```text
64916cd42d40e0f81a51dd750d2134d194dd59c8318bf3d6f75fbc8649d97770
```

But its chain frame was `480x832`, not `704x576`. The mapped remote
`remux.mp4` path already contained a stale artifact from an earlier external
remux experiment. `advance_chain` tested only that the remote path existed,
then extracted the stale file. The resulting cut 2 received the wrong seed
image and native audio failed Whisper (`score 0.167`).

## Minimal fix

When the accepted final MP4 exists locally, hash it. Before remote extraction,
run `sha256sum` on the mapped remote path. If the remote file is missing or
its hash differs, publish the local accepted artifact through
`RenderHost.push_file` and verify the remote hash before extraction.

Existence alone is never artifact identity.
