# WD-m7xw successful-output QC

All four successful outputs contain H.264 448x832 24 fps video and AAC
48000 Hz stereo audio. Each has a distinct SHA-256 and an eight-panel contact
sheet showing the same compass/paper-crane environment with position changes
across time. There is no dialogue, so speech transcription is not applicable.

| Output | Duration | Visual review | Objective gate |
| --- | ---: | --- | --- |
| create | 1.375 s | premise and blue paper crane are visible from the first frame; no black/empty sequence | exact requested 33-frame duration and audio present |
| extend | 4.033 s | same identity and continuous crane motion; useful continuation ending | output is longer than the 1.375 s source |
| retake | 1.375 s | same anchored first-frame composition with a distinct later take | first-frame SSIM 0.988417; output hash differs |
| edit | 1.375 s | composition and continuity retained while grading/detail change | whole-video PSNR 38.302450 dB versus source |

The four dependency-boundary operations have no output bytes to QC and are not
quality verdicts.
