# WD-dmf2 operator authorization

## Verbatim authorization

> the operator approved host batch 1 with a 20 GB download ceiling and has
> repeatedly instructed to continue/unblock the programme. This lane's need
> (~0.48 GB) is far below it, so it is covered. Record the authorization
> verbatim in `operator_authorization` as the other lanes did, including the
> operator's quoted words, the ceiling, and the bytes actually pulled.

Additional operator host boundary supplied by the dispatcher:

> the operator's `llama-server` is RUNNING and holds ~7.7 GB of the 24 GB card
> — leave it alone, do not stop it; size your work to the remaining ~16 GB.

## Recorded scope

- Story: WD-dmf2 only.
- Host: `3090`, user `straughter`, WanGP root `/home/straughter/Wan2GP`.
- Planned download: 483,617,219 bytes for Whisper small under the operator's
  20,000,000,000-byte batch ceiling.
- Bytes actually pulled in this execution: 0. The required Whisper small file
  was already present at `/home/straughter/.cache/whisper/small.pt` and its
  measured SHA-256 matched the manifest before any transfer.
- Operations: synchronous governed director planning, real FFmpeg composition,
  Whisper/SyncNet evidence where applicable, queue-state transitions, hash
  collection, and bounded diagnostics.
- Prohibited: stopping or restarting `llama-server`, unrelated GPU work,
  protected-engine changes, unrelated stories, and downloads beyond the lane.

## Disk derivation

- Required model transfer after host inventory: 0 bytes.
- Expected bundle/working set: under 0.2 decimal GB (selected upstream media,
  composed MP4s, logs, JSON, and queue databases).
- Safety margin: the dispatcher requires execution to stop if free space would
  fall below approximately 15 GB.
- Derived `min_free_gb`: 15.0 decimal GB (15,000,000,000 bytes).
- Host free bytes at inventory: 41,020,891,136, comfortably above the floor.
