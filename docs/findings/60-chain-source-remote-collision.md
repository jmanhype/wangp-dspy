# 60 — chain advance trusts an occupied remote final-artifact path

Status: CLOSED in PR #90 / commit `3faaf9a`; chain-source identity checks are
on `main`.

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

## Live verification

The first fresh LF002 attempt produced the exact cut 1 hash but extracted a
stale 480x832 remote artifact as its chain seed, causing cut 2 to fail native
Whisper. After the hash check/publish/verify repair, the regenerated chain
frame was the pinned 704x576 seed and the retried cut 2 reproduced the exact
operator-accepted SHA-256. The assembled pair also matched exactly.

## Resolution

`services/director/wiring.py` now compares local and remote artifact identity
before chain extraction, with regression coverage in
`tests/test_director_wiring.py`. Finding #69 later required a present local
source and streaming hashing. The full suite at `9b70be1` passed 1380 tests
with one intentional skip and no failures.
