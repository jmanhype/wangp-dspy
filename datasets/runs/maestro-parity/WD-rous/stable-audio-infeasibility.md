# Stable Audio 48 kHz target infeasibility

The authorized native WanGP Stable Audio 3 Small operation completed, but its emitted audio cannot satisfy this lane's fixed 48 kHz target:

- Requirement: 48,000 Hz stereo from `docs/music-capabilities.md`.
- Native model configuration: `models/TTS/stable_audio3/configs/stable_audio3_small_config.json` declares `sample_rate: 44100`; `models/TTS/stable_audio3/pipeline.py` defines `STABLE_AUDIO3_SAMPLE_RATE = 44100`.
- Measured emitted artifact: `outputs/wd_rous_stable_generate.wav` is 10.000000 seconds, 2 channels, `pcm_s16le`, and **44,100 Hz**.
- The output is non-blank and real generation evidence, but it is not relabeled or resampled as a 48 kHz generation pass.
- Stable Audio Medium is separately blocked in the WanGP runtime because `flash_attn` is absent (`ModuleNotFoundError`), while Small does not require it. The ACE-Step virtualenv does have `flash_attn`; this is a runtime-specific boundary, not a global host claim.

Therefore `stable_audio` Generate is recorded `unsupported_on_this_hardware` for this governed 48 kHz output requirement, based on the model's measured output requirement mismatch. The pre-existing `stable_audio` Style-adapt planning-unsupported boundary remains unchanged.
