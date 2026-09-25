# Download hash correction

The first authorized synchronous attempt downloaded both planned assets totaling 71,567,775 bytes, then stopped before extraction or rendering because the Real-ESRGAN portable archive did not match the provisional Nix `fetchzip` SRI-derived hash `d5888fcefd5e1a71eb6b324546f977efe0b5176c67a046cdd144189312d3f894`. That derivation represented Nix's extracted fetchzip output, not the exact GitHub release ZIP bytes.

The measured archive bytes on host `3090` hash to `e5aa6eb131234b87c0c51f82b89390f5e3e642b7b70f2b9bbe95b6a285a40c96`; size remains 46,931,474 bytes. The manifest and run gate were corrected to that exact-byte hash before any rendering. RIFE matched its planned hash on the first attempt. No bytes beyond the two planned assets were fetched.
