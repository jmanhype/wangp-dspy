# Marathon production loop

Unattended back-to-back H3 film production on the 3090.

- `driver.sh` — waits for GPU idle, banks each render to ~/marathon/,
  then loops: NEXT_JOB.json -> wgp --process -> bank -> repeat.
- `queue_feeder.sh` — promotes QUEUE/*.json into NEXT_JOB.json (FIFO).
- `manifest.py` — rebuilds manifest.json (md5 + durations) for the bank.

Job schema: see docs/h3-continuation-recipe.md (Mode A). Each job is a
wgp settings override: premise, plate (image_start + image_refs),
video_length 362, resolution 480x832, and the SHOT 1/CUT TO prompt.

Ops runbook (learned the hard way, 2026-09-04):
- spawn renders via Python subprocess start_new_session (SSH-reap-proof)
- zombie wgp + /tmp/wgp_queue.lock = false "Queue completed": check
  log mtime vs clock, pkill all wgp, rm lock
- 362f renders need --profile 2 on 24GB cards
- plates MUST be verified on disk before queueing a job (a missing
  plate fails validation with "provide at least one Reference Image")
- root disk: archive idle model dirs to /mnt/bulk with symlinks
