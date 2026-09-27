# WD-m25k operation plan

The target cells are independently probed. A successful native control produces a hashed media artifact. A rejected control records its exact native boundary and cannot inherit another row or operation.

| Row | Operation | Native plan |
| --- | --- | --- |
| KFI | create | KFI control without an injected frame; expect typed source-input rejection |
| KFI | extend | extend the accepted KFI-generated source with injected frame control |
| KFI | blend | two-guide blend control plus KFI identity; expect FL2VA guide rejection |
| KFI | edit | guide plus KFI frame injection and audio preservation |
| KFI | outpaint | guide plus outpaint margins; expect disabled-control rejection |
| KFI | repaint | guide plus mask on the KFI-generated source |
| KFI | recast | image-reference recast control; expect Ref2VA requirement rejection |
| KFI | upscale | lossless postprocessing of the KFI-generated source |
| audio refinement | create | refinement audio mode without source video; expect typed source-input rejection |
| audio refinement | extend | extend accepted audio-refinement source in audio mode |
| audio refinement | blend | two-guide blend control plus audio mode; expect FL2VA guide rejection |
| audio refinement | retake | retake accepted audio-refinement first frame in audio mode |
| audio refinement | outpaint | guide plus outpaint margins and audio mode; expect disabled-control rejection |
| audio refinement | repaint | guide, mask, and audio preservation on the accepted source |
| audio refinement | recast | image-reference recast control plus audio mode; expect Ref2VA requirement rejection |
| audio refinement | upscale | lossless postprocessing of the audio-refinement source |

The two source videos are accepted `WD-2gyw` outputs, not new evidence for this story. Their hashes are rechecked before and after execution:

- KFI source: `datasets/runs/maestro-parity/WD-2gyw/outputs/wd_2gyw_h3_kfi_frames_injection.mp4`
- Audio-refinement source: `datasets/runs/maestro-parity/WD-2gyw/outputs/wd_2gyw_h3_audio_refinement.mp4`
