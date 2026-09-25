# Pre-download plan boundary

This artifact preserves the no-pull capability plan. Hugging Face metadata exposes SHA-256 for the four LFS objects but only Git blob IDs for three small plain-text JSON files. Those three entries are represented by all-zero placeholders in `model-assets.json` solely for the pre-pull byte-count surface; the files are absent on the host, so no hash is claimed. The placeholder hashes will be replaced only after the operator-approved download by measured `sha256sum` values. No asset bytes have been pulled at the point this note and plan are recorded.
