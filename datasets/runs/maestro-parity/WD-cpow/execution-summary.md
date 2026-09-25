# WD-cpow native execution summary

All operations ran synchronously under explicit local/remote timeouts. The
durable queue reached `rendering` before native work and `done` afterward.

1. Stable Audio attempt: `timeout 700 ssh ... 3090 timeout 620 bash /home/straughter/Wan2GP/wd_c_pow_stable_sfx.sh`.
2. VibeVoice revoice supply: `timeout 2400 .../run-vibevoice-remote.sh`; seed 9201 was rejected at Whisper 0.714, and seed 9202 passed at 1.000.
3. Revoice mux: `timeout 360 ssh ... 3090 timeout 300 bash /home/straughter/Wan2GP/wd_c_pow_revoice_mux.sh`.
4. DeepFilterNet refinement: `timeout 900 ssh ... 3090 timeout 840 /home/straughter/Wan2GP/venv/bin/python /home/straughter/Wan2GP/wd_c_pow_refine.py`.

The source, revoice, and refinement video packet stream hashes all equal
`5f820953a1c90bacf9934652a69894dade272ab00852a03035595febe0cbf941`. The
revoice and refinement outputs measure 704x576, 24 fps, 48 kHz stereo AAC.
The refinement measures -18.0 LUFS integrated and changes audio with a decoded
A/B mean absolute delta of 0.0031915837117848897.

The Stable Audio attempt is real but measures 44,100 Hz, so it is recorded as
`unsupported_on_this_hardware` in `stable-audio-infeasibility.md`. No training,
GUI, registry publication, or protected engine change ran.
