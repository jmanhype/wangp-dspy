# WD-m7xw dependency boundaries

These four boundaries are exact no-download host dependency failures. They are
not `unsupported_on_this_hardware`, not model-capability verdicts, and must not
inherit the successful create output.

| Operation | Native exit | Failing stage | Required absent asset | Output bytes |
| --- | ---: | --- | --- | ---: |
| recast | 1 | model loaded, then system-LoRA resolution | `ltx-2.3-22b-ic-lora-ingredients-0.9.safetensors` | 0 |
| outpaint | 1 | model loaded, then system-LoRA resolution | `ltx-2.3-22b-ic-lora-outpaint.safetensors` | 0 |
| repaint | 1 | model loaded, then system-LoRA resolution | `ltx-2.3-22b-ic-lora-in-outpainting-0.9.safetensors` | 0 |
| upscale | 1 | postprocessing asset preflight/download | `ltx-2.5-22b-ic-lora-pixel-spatial-upscaler-x2-1.0.safetensors` | 0 |

The exact argv, full native logs, GPU state, and per-operation host snapshots are
in `host-logs-resumed/`. `HF_HUB_OFFLINE=1` and `TRANSFORMERS_OFFLINE=1`
prevented download bytes; all four target files remained absent at final
postflight. The isolated source tree briefly gained a runtime-generated
`.pyi` change during failing model-load attempts and was restored after each;
final state is the required commit with only the expected untracked `ckpts`
symlink. The live Wan2GP HEAD and dirty identity remained unchanged.
