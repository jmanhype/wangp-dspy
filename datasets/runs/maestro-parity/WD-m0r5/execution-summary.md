# WD-m0r5 host execution summary

## Checkpoint selection and bytes

The selected two-transformer manifest was **42,365,515,370 bytes** across 28
files. It shares Qwen Edit Plus 2509 SVDQuant INT4 across both Qwen presets
and FLUX.1 Kontext Dev INT8 across both Flux presets.

WanGP then loaded three runtime dependencies that the hand-built manifest had
not enumerated: PiD Qwen upsampler (1,516,789,399 bytes), Gemma-2 2B INT8
(3,205,937,786 bytes), and rembg/BRIA-RMBG (1,024,331,469 bytes). Those
runtime dependencies total **5,747,058,654 bytes**. An InsightFace bootstrap
mistakenly downloaded a duplicate 281,857-byte archive before using the
existing model. Total model bytes actually pulled, including that accidental
duplicate, were **48,112,855,881 bytes**. The pre-existing InsightFace
embedding model was not downloaded and is recorded separately in `evidence.json`.

The selected and runtime model hashes are in `selected-download.log`,
`upscaler-retry-sha256.txt`, and `runtime-extra-model-hashes.txt`.

## Host and preflight

- Before download, with the sanctioned judge started, SSH, local/remote disk,
  GPU, and QC passed; all 28 selected assets were intentionally absent.
- After download, all 28 selected hashes passed. Disk was 13G (below the 50G
  preflight floor) and QC was down because the judge had been stopped for GPU
  work. The post-download report is retained rather than relabeled.
- Final GPU state is 83 MiB used / 24,033 MiB free; no compute app remains.
- The WanGP Python interpreter was restored with `uv python install 3.11`
  after quarantine deletion removed the managed interpreter cached under
  `~/.local/share/uv`; the venv symlinks were restored and imports reverified.

## Real operations

The host emitted 16 selected JPEG artifacts:

- Qwen standard: generate, edit, upscale, outpaint, identity edit.
- Qwen professional: generate, edit, upscale, outpaint, identity edit.
- Flux standard: generate, edit, identity edit.
- Flux Kontext: generate, edit, identity edit.

`evidence.json` records every output SHA-256, dimensions, image metadata,
model/reference provenance, native queue logs, and 16 objective gates. All 16
gates pass. Selected InsightFace identity cosines are 0.950228 (Qwen
standard), 0.792692 (Qwen professional), 0.942699 (Flux standard), and
0.950500 (Flux Kontext) against threshold 0.75.

Initial low-quality identity attempts are retained under `outputs/*attempt*`
and their logs; they are not included in the canonical 16-output set.

## Checker and disposition

`scripts/verify_maestro_parity.py` reports exactly one failure:

```text
FAIL reviewer_verdict.decision: must be approved
```

This is intentional: reviewer approval belongs to the independent reviewer,
not this developer. Therefore **no row is flipped to `host_run_verified` yet**.
All four rows are `evidence_complete_pending_review` in `evidence.json`.
