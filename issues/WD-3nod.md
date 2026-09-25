---
id: WD-3nod
title: "Maestro parity: generation evidence"
status: open
priority: 1
type: epic
labels: [capability, evidence]
created_at: 2026-09-24T14:14:05Z
created_by: speed
updated_at: 2026-09-25T03:34:28Z
content_hash: "sha256:cb86db3af4757729a429a0d2e04ac88c51123bb90cdafcdec34116133957131d"
---

## Description
Temporary creation body; authoritative body is installed immediately after ID assignment.

## Acceptance Criteria


## Design


## Notes


## History


## Links


## Comments

### 2026-09-24T16:33:45Z speed
Programme status at 8f0b225: WD-651z (fail-closed parity evidence checker + canonical bundle contract) delivered, independently accepted, and merged. All 10 child stories now have authoritative bodies. Remaining scope is entirely host-gated: 45 capability rows still read 'planned' and no bundle exists under datasets/runs/maestro-parity/ because the operator's per-batch GPU-host authorization and model-download approval have not been given. The no-GPU install half of the 'better than Maestro' proof already exists and is tested in a clean worktree (tests/test_readme_quickstart.py).

### 2026-09-25T03:15:53Z speed
PROGRAMME MILESTONE at merged main d8671f3: image lane (WD-m0r5) is COMPLETE and on main - 16 image cells host_run_verified from a real authorized host bundle, 4 Flux upscale/outpaint cells unsupported with reasons; docs/image-capabilities.md reflects it. Independent review recomputed 16/16 artifact hashes, reproduced every objective gate and the identity cosines, and visually confirmed real distinct non-blank images per row. WD-e4r7 (fail-closed GPU preflight) also merged. Remaining lanes still need host authorization per batch, and the render host is at 13G free (below the 50G preflight floor), which must be resolved before the next download.

### 2026-09-25T03:34:28Z speed
HOST REPAIR (dispatcher): the uv-managed CPython 3.11.14 interpreter previously removed by the quarantine deletion was restored with 'uv python install 3.11.14' (~100 MB). This recovered TWO environments that had been left with no working interpreter rather than deleting them: /mnt/bulk/straughter/ACE-Step-1.5/.venv (the MUSIC lane's environment) and /home/straughter/qwen-voicedesign-trial/venv — about 16.3 GB of installed packages that would otherwise have needed re-downloading. Verified: all three venvs (ACE-Step, qwen-voicedesign, Wan2GP) now report a working Python (3.11.14, 3.11.14, 3.11.15). Prior collateral damage is now fully repaired.
