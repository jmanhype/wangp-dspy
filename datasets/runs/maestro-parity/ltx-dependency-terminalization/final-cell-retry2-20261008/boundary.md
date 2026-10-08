# WD-28ac final-cell retry2 — 2026-10-08

## Outcome

The operator-approved retry2 native batch ran once in a fresh namespace and queue database. It stopped on the first terminal failure as required.

- Six operations rendered and are preserved as `rendered_pending_qc`.
- `ltx23-upscale` exited 1 with no output and is preserved as `failed`.
- No retry or substitution was attempted.
- No model, dependency, or package download occurred.
- No provider spend, training, deletion, threshold change, or protected-engine change occurred.

## Source preparation succeeded

The previously missing 7,605,507,256-byte distilled LoRA was exposed through a zero-copy symbolic link:

```text
/home/straughter/Wan2GP-story-WD-osfm/loras/ltx2/ltx-2.3-22b-distilled-lora-384-1.1.safetensors
  -> /home/straughter/Wan2GP/loras/ltx2/ltx-2.3-22b-distilled-lora-384-1.1.safetensors
```

The link was hash-verified:

```text
f5d4953f3386197a4b4f5abdb17616ff256171e8075c111d6e7d2dfa6e823b3a
```

## New terminal boundary

The native runner then requested a second distinct asset:

```text
ltx-2.3-22b-ic-lora-pixel-spatial-upscaler-x2-0.9.safetensors
size:   654465286 bytes
sha256: 0667334e23af9fc0ab3fdff2e059c805ac0d162b1f96f18a462801478027451e
source: https://huggingface.co/DeepBeepMeep/LTX-2/resolve/main/ltx-2.3-22b-ic-lora-pixel-spatial-upscaler-x2-0.9.safetensors
```

A host-wide read-only search found no local copy. Offline mode correctly blocked the model download.

## Authorization disposition

The retry2 authorization is consumed. Its canonical SHA-256 and no-retry disposition are recorded in `authorization-consumption.json`.
