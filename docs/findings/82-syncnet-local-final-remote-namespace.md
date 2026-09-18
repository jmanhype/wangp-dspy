# 82 — Remote SyncNet assumed the local final artifact existed host-side

Status: implemented on this branch.

## Failure boundary

The first full-gate LF003 rerun rendered and passed native provenance, pre/post
Whisper, and identity vision for Tess. SyncNet then failed before inference:

```text
SyncNetRunnerError: video and SyncNet model paths are required
```

The remote worker contained `raw.mp4`, but the QC final `remux.mp4` is created
in the local pull namespace. `RemoteSyncNetAVSyncJudge` mapped the local final
path to its remote counterpart without publishing that file, so the host-side
runner correctly refused an absent path. The failure was a namespace transport
gap, not scored AV rejection.

## Change

The remote SyncNet judge now:

* requires the local final video to exist;
* hashes that exact artifact;
* creates its remote parent directory;
* publishes it through `RenderHost.push_file`;
* verifies the staged path return value;
* passes `--video-sha256` to the host runner;
* rejects any host video hash mismatch before model inference;
* records `video_sha256` and `remote_video_path` in evidence.

## Verification

Model-free tests cover exact artifact staging, hash argument dispatch, remote
path provenance, missing-local-file rejection, and existing judge behavior.
