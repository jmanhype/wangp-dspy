# Stable Audio sound-effect 48 kHz target infeasibility

The authorized native WanGP Stable Audio 3 Small operation completed, but its
emitted sound effect cannot satisfy this lane's fixed 48 kHz stereo WAV target:

- Required layout: 48,000 Hz stereo `pcm_s16le`.
- Measured output: `outputs/wd_cpow_stable_sfx.wav` is 2.250000 seconds, two
  channels, `pcm_s16le`, and **44,100 Hz**.
- Artifact SHA-256: `f0897dfc2c00eb3239ac244e7cf668d3949fce97a2a2bc9253f06ff45830ef7b`.
- The output is non-blank (measured RMS 0.789872426854435), so this is a real
  failed-target attempt rather than absent generation.
- The complete 2,356,908,559-byte Stable Audio model set was already present
  from WD-rous; WD-cpow pulled zero additional bytes for it.

The result is not resampled or relabeled as native 48 kHz generation.
`stable_audio/sound_effect` is therefore `unsupported_on_this_hardware` for
this governed 48 kHz requirement. The pre-existing planning-unsupported
off-diagonal Stable Audio cells remain unchanged.
