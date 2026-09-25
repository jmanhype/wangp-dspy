# Download hash correction

The first authorized synchronous attempt downloaded both planned assets totaling 71,567,775 bytes, then stopped before extraction or rendering because the Real-ESRGAN portable archive did not match the provisional Nix `fetchzip` SRI-derived hash `d5888fcefd5e1a71eb6b324546f977efe0b5176c67a046cdd144189312d3f894`. That derivation represented Nix's extracted fetchzip output, not the exact GitHub release ZIP bytes.

The measured archive bytes on host `3090` hash to `e5aa6eb131234b87c0c51f82b89390f5e3e642b7b70f2b9bbe95b6a285a40c96`; size remains 46,931,474 bytes. The manifest and run gate were corrected to that exact-byte hash before any rendering. RIFE matched its planned hash on the first attempt. No bytes beyond the two planned assets were fetched.

The corrected second attempt extracted the v0.2.5.0 portable archive and stopped before rendering because this archive has no top-level directory: `realesrgan-ncnn-vulkan`, `models/`, and documentation unpack directly into the destination. The execution path was corrected to that observed layout before any model inference or media transformation.

The extracted Ubuntu executable arrived without its executable bit on this host. A third pre-render attempt stopped at unzip's interactive overwrite prompt. The final gate checks for the extracted regular file and applies `chmod +x` explicitly; it performs no additional network transfer and does not overwrite any already-extracted file.

The first media attempt captured a real host incompatibility in the planned command graph: Ubuntu FFmpeg 6.1.1 refuses FFV1 in an MP4 container (`Could not find tag for codec ffv1`). The lossless intermediate container was changed to Matroska while preserving the exact FFV1 transformation and final H.264/MP4 graph; this changes staging only, not source bytes or declared output semantics.
