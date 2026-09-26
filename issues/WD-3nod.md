---
id: WD-3nod
title: "Maestro parity: generation evidence"
status: closed
priority: 1
type: epic
labels: [capability, evidence, accepted]
created_at: 2026-09-24T14:14:05Z
created_by: speed
updated_at: 2026-09-26T04:06:53Z
content_hash: "sha256:2f5010a2245620350ea0412df73da08d03d151f8ea552e4ba19fc536de00abd2"
closed_at: 2026-09-26T04:06:49Z
close_reason: "All 13 child stories are closed."
---

## Description
Temporary creation body; authoritative body is installed immediately after ID assignment.

## Acceptance Criteria


## Design


## Notes


## History
- 2026-09-26T04:06:49Z status: open -> closed

## Links


## Comments

### 2026-09-24T16:33:45Z speed
Programme status at 8f0b225: WD-651z (fail-closed parity evidence checker + canonical bundle contract) delivered, independently accepted, and merged. All 10 child stories now have authoritative bodies. Remaining scope is entirely host-gated: 45 capability rows still read 'planned' and no bundle exists under datasets/runs/maestro-parity/ because the operator's per-batch GPU-host authorization and model-download approval have not been given. The no-GPU install half of the 'better than Maestro' proof already exists and is tested in a clean worktree (tests/test_readme_quickstart.py).

### 2026-09-25T03:15:53Z speed
PROGRAMME MILESTONE at merged main d8671f3: image lane (WD-m0r5) is COMPLETE and on main - 16 image cells host_run_verified from a real authorized host bundle, 4 Flux upscale/outpaint cells unsupported with reasons; docs/image-capabilities.md reflects it. Independent review recomputed 16/16 artifact hashes, reproduced every objective gate and the identity cosines, and visually confirmed real distinct non-blank images per row. WD-e4r7 (fail-closed GPU preflight) also merged. Remaining lanes still need host authorization per batch, and the render host is at 13G free (below the 50G preflight floor), which must be resolved before the next download.

### 2026-09-25T03:34:28Z speed
HOST REPAIR (dispatcher): the uv-managed CPython 3.11.14 interpreter previously removed by the quarantine deletion was restored with 'uv python install 3.11.14' (~100 MB). This recovered TWO environments that had been left with no working interpreter rather than deleting them: /mnt/bulk/straughter/ACE-Step-1.5/.venv (the MUSIC lane's environment) and /home/straughter/qwen-voicedesign-trial/venv — about 16.3 GB of installed packages that would otherwise have needed re-downloading. Verified: all three venvs (ACE-Step, qwen-voicedesign, Wan2GP) now report a working Python (3.11.14, 3.11.14, 3.11.15). Prior collateral damage is now fully repaired.

### 2026-09-25T03:35:50Z speed
DISPATCH PROCESS GAP (dispatcher, corrected): the music lane (WD-rous) was first dispatched to a worktree that had never been created — the branch, worktree and claim were skipped. The agent ran for a while producing nothing and was interrupted; the main checkout remained CLEAN and untouched (verified: no stray files, main still at d8671f3, only WD-m0r5 under datasets/runs/maestro-parity/), so there was no collateral damage. Corrected by creating story/WD-rous from main, adding .claude/worktrees/dev-WD-rous, claiming the story, and re-dispatching. RULE for every lane dispatch: create the branch, add the worktree, and atomically claim the story BEFORE spawning the developer; then verify the worktree exists and is clean. Combined with the earlier push rule (verify the branch is PUSHED, not merely committed), these are the two integration steps the dispatcher must perform rather than assume.

### 2026-09-25T07:07:14Z speed
PROGRAMME MILESTONE at merged main c91a6d8 — every lane NOT gated by video is complete and independently accepted. Rows dispositioned on main: image 4 (16 cells host_run_verified + 4 unsupported), music 2 (ace_step generate+style verified; stable_audio unsupported at measured 44.1 kHz), sfx 3 (vibevoice revoice + deepfilternet refinement verified with ffmpeg-confirmed identical video packet hashes 5f820953...; stable_audio sound_effect unsupported). That is 9 of 45 rows with terminal evidence dispositions. Also landed: WD-651z fail-closed parity evidence checker, WD-e4r7 GPU preflight fail-closed (authorized protected-file change, independently accepted), WD-0zj8 clean-machine install no-GPU half (generated-artifact half explicitly blocked). Efficiency: the sfx lane reused the music lane's Stable Audio assets, so its incremental download was 8,677,764 B. REMAINING 36 ROWS (video 11 + finishing 5 + voice 2 + character 9 + director 9) are all behind the video lane, which is blocked on two operator decisions: (1) VRAM contention - the operator's llama-server endpoint holds 7.75 GB on the 3090 and auto-recovers after being killed, while H3 renders need ~20+ GB, so video rendering and that service cannot coexist; (2) the non-H3 families (LTX-2.3/2.5, SCAIL-2, Hunyuan int8) are not installed and need 119 GB on a host with ~10 GB free, which would require authorizing the 78 GB prune of superseded H3 weights. The H3 rank8 FL/Ref weights ARE present, so H3-based video rows need zero download and are blocked only by the VRAM contention.
