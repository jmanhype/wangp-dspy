# LF003 four-cut probe — transcription and timing

- Repository run: `lf003-four-cut-fullgate-20260919`
- Cut duration policy: 56 frames at 24 fps (`2.333333 s`)
- Cut 1 Tess: pre-Whisper 0.833 / post-Whisper 0.833; transcript `Tomorrow's sunrise is only a project.`
- Cut 2 Rho: pre-Whisper 0.833 / post-Whisper 0.667; transcript `can give me a real horizon here.`
- Cut 3 Tess: pre-Whisper 1.000 / post-Whisper 1.000; transcript `The projector died at midnight.`
- Cut 3 was rejected before SyncNet because the repository vision gate did not receive the required three-frame `speaker_mouth_bboxes`; therefore no mouth-box consensus or AV-sync score is claimed.
- Cut 4 remained pending on its chain dependency and was not rendered. No four-cut assembly was produced.
