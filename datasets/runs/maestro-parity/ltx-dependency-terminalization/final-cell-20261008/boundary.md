# WD-28ac final-cell retry — 2026-10-08

## Outcome

The newly authorized seven-operation native batch ran once in a fresh namespace and queue database. It stopped on the first terminal failure as required.

- Six operations rendered and are preserved as `rendered_pending_qc`.
- `ltx23-upscale` exited 1 with no output and is preserved as `failed`.
- No retry or substitution was attempted.
- No model, dependency, or package download occurred.
- No provider spend, training, deletion, threshold change, or protected-engine change occurred.

## Exact terminal cause

The native runner requested:

```text
ltx-2.3-22b-distilled-lora-384-1.1.safetensors
size:   7605507256 bytes
sha256: f5d4953f3386197a4b4f5abdb17616ff256171e8075c111d6e7d2dfa6e823b3a
source: https://huggingface.co/DeepBeepMeep/LTX-2/resolve/main/ltx-2.3-22b-distilled-lora-384-1.1.safetensors
```

Offline mode correctly blocked a model download because the file was absent from the WD-osfm source tree.

A byte-identical local copy was subsequently found and hash-verified at:

```text
/home/straughter/Wan2GP/loras/ltx2/ltx-2.3-22b-distilled-lora-384-1.1.safetensors
```

No staging or mutation of that local asset has been performed. A future retry requires a new one-shot authorization to expose this exact local asset to the WD-osfm source boundary without downloading bytes.

## Authorization disposition

The 2026-10-08 authorization is consumed. Its canonical SHA-256 and no-retry disposition are recorded in `authorization-consumption.json`.
