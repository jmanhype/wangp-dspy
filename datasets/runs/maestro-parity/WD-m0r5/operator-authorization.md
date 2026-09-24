# WD-m0r5 operator authorization and disk correction

## Verbatim authorization

1. `I agree`
   - Original scope: host batch 1 = image lane (WD-m0r5); report the download-plan byte total and stop above 20 GB.
2. `you need to kill whatever that is that was holding up the GPU and get back to work so that we can finish and complete this`
3. `Unblock and cont`

Messages 2 and 3 extend batch 1 through the minimum checkpoint download and the four real image runs. The original `I agree` remains part of the authorization chain. The operator later corrected the disk instruction: quarantine-only `mv` on the single filesystem freed zero bytes; the operator then deleted the already-audited quarantine set.

## Disk correction and freed inventory

The host filesystem is `/dev/nvme0n1p4` (800G total). Before deletion it reported 755G used / 37G available / 96%. After the operator deleted the audited quarantine it reported 734G used / 58G available / 93%. The freed set was:

- Six generated `.ce/.pixi` environments, 19,255,262,184 bytes by `du -sb` with hard links counted once: `depthanythingv3-nodes`, `geometrypack-blender`, `geometrypack-gpu`, `geometrypack-main`, `geometrypack-nodes`, and `sam3dbodyfixed-nodes`. `/home/straughter/.ce/pixi.toml` and `pixi.lock` remain; the recorded regeneration command is `cd /home/straughter/.ce && pixi install`. No rattler/pixi package cache remains, so recreation will download packages.
- Old Wan2GP outputs: 1,624,514,426 bytes.
- Old acceptance outputs: 142,554,009 bytes.
- Small regenerable caches: 1,322,829,037 bytes in aggregate.

The quarantine root was emptied by the operator after deletion. No model weight or operator project was deleted by this agent.

## License boundary

The operator authorized `license_accepted: true` only for the exact selected checkpoints in this lane. This is a research/evaluation batch; no commercial-use authorization is claimed. The FLUX.1-dev/Kontext upstream license is explicitly `flux-1-dev-non-commercial-license`. Qwen upstream metadata identifies Apache-2.0, but the operator's authorization does not broaden use beyond this evaluation, and commercial terms remain the operator's responsibility.
