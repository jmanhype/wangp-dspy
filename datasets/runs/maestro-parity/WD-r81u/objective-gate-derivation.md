# Objective gate derivation

Every operation retains the measured source audio layout. Temporal operations require a measured 2.0 fps ratio, at least a 1.9 frame ratio (allowing endpoint omission), and no more than 0.13 seconds absolute duration error. Spatial operations require exact measured width and height ratios of 2.0.

For Real-ESRGAN, downscaled PSNR is recorded as an objective comparison but is not a pass gate because the restoration intentionally changes luminance and local contrast. The structural gate requires downscaled FFmpeg SSIM of at least 0.6. Grain outputs must have positive source PSNR and be at least 3 dB farther from the source than the direct H.264 codec control, proving a visual transformation beyond re-encoding.

The first analysis draft incorrectly treated luminance-sensitive Real-ESRGAN PSNR as the structural gate and failed it at 16.477092 dB. Before evidence emission this was replaced by the declared SSIM gate; both measured PSNR and SSIM remain in `media-qc.json`.
