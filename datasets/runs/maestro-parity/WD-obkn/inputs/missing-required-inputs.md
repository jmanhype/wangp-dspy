# Required inputs that remain absent

## Face refinement

The only consumed source is `inputs/source.mp4`, the WD-2gyw H3 standard compass scene. Its measured mid-frame review extract `review/source-mid.png` shows a brass compass on a map and no human face. No face-track detector, normalized temporal/geometric bounds, selected-track identity, rights record, or consent record was supplied by the operator or predecessor bundle.

Therefore neither the `ffmpeg` face-refinement cell nor the `neural_frame_gen` face-refinement cell is executed or labeled infeasible. Missing consent and track provenance are unresolved required inputs, not hardware verdicts.

## neural_frame_gen interpolation and spatial upscale

`neural-frame-gen-boundary-probe.txt` records zero hits for `neural_frame_gen` across the WanGP postprocessing tree, `wgp.py`, and `setup_config.json`, plus zero files matching `*neural*frame*`. WanGP has a separate H3 face refiner implementation, but it is not the named `neural_frame_gen` backend and cannot be relabelled as such.

The repository's no-GPU command graph for this backend falls back to FFmpeg/RIFE/Real-ESRGAN-shaped commands and its optional neural declaration is a typed unavailable path. Reusing those commands would fabricate a `neural_frame_gen` verdict. The two planned neural cells therefore remain unresolved implementation-boundary gaps, not `unsupported_on_this_hardware` claims.
