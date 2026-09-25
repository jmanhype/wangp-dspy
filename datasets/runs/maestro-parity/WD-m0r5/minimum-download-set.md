# Minimum WD-m0r5 checkpoint set

## Code-path conclusion

The repository planning surface has **no preset-to-native-checkpoint mapping and no preset-specific backend behavior**:

- `predict/image_capabilities.py:33-46` defines the four preset labels and only checks that each preset belongs to its family.
- `host/image_backends.py:72-87` dispatches by family (`qwen_image` or `flux_kontext`), not by preset.
- `predict/image_capabilities.py:339-375` requires one immutable operator-supplied SHA-256 manifest entry per family/preset; it does not require the two presets in one family to have different hashes.
- `predict/image_capabilities.py:399-407` and `services/image/request_compiler.py:80-90` attach and record that operator-selected identity.

Therefore the smallest code-consistent set can share one transformer inside each family. The selected mapping is:

| Repo rows | Shared native checkpoint | Quantization | Bytes | Evidence |
| --- | --- | --- | ---: | --- |
| `qwen_image/qwen-standard` + `qwen_image/qwen-professional` | Qwen Image Edit Plus 2509 20B, SVDQuant INT4 r128, Lightning 4-step | int4 | 12,654,443,144 | `native-defaults/qwen_image_edit_plus_20B_nunchaku_r128_int4.json`; the host qwen handler marks all Qwen image architectures `image_outputs: true` |
| `flux_kontext/flux-standard` + `flux_kontext/flux-kontext` | FLUX.1 Kontext Dev 12B | quanto int8 | 11,974,893,901 | `native-defaults/flux_dev_kontext.json`; the host flux handler maps Kontext into the same `flux` family and supports image output/inpaint/reference editing |

This is a deliberate operator-manifest mapping. It must not be described as a discovery that the repository itself names these native checkpoints; the repository deliberately leaves model identity to the operator.

## Option table from the model indexes

| Option | Bytes | Rows covered | Decision |
| --- | ---: | --- | --- |
| Qwen Image 20B int8 | 20,488,214,767 | qwen-standard only under distinct-checkpoint mapping | Not selected; larger than shared edit INT4 |
| Qwen Image Edit Plus 2 (2511) int8 | 20,488,214,755 | qwen-professional only | Not selected; exact newer edit variant is larger |
| Qwen Image Edit Plus 2509 SVDQuant INT4 r128 | 12,654,443,144 | both Qwen rows through shared manifest identity | **Selected** |
| Qwen Image Edit 2509 FP4 r128 | 13,081,386,856 | both Qwen rows if shared | Rejected; host default says sm120+/RTX 50xx, not RTX 3090 |
| FLUX.1-dev int8 | 11,974,893,901 | flux-standard | Native `flux.json` candidate |
| FLUX.1-schnell int8 | 11,954,433,942 | text-to-image, but lacks the Kontext reference-edit contract | Rejected |
| FLUX.1 Kontext-dev int8 | 11,974,893,901 | both Flux rows through shared manifest identity | **Selected** |
| FLUX.1 Kontext-dev bf16 | 23,802,947,360 | both Flux rows through shared identity | Rejected; more than double the int8 bytes |

No W4A8/FP8 Flux option exists in the selected WanGP model index. No smaller Qwen option compatible with the RTX 3090 exists in that index.

## Exact selected total

`selected-model-assets.json` contains 28 files: two shared transformers plus every Qwen/Flux encoder, VAE, upscaler, inpainting, tokenizer, and config file declared by the host handlers. Its exact total from the Hugging Face tree LFS/blob sizes is **42,365,515,370 bytes**. `wgp doctor --capabilities` reports all 28 absent with that total and `wangp_downloads=false`.

For comparison, a four-distinct-transformer int8 plan plus the same dependencies totals 82,662,396,379 bytes. Treating the Qwen 2509 INT4 file as a professional fallback gives 74,828,624,768 bytes. The selected shared two-transformer plan is the minimum credible plan that preserves all four row identities in the repository's operator-supplied manifest model.
