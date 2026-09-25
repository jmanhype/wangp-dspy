# WD-bxhc execution summary

- Used existing HF-native **VibeVoice-7B-hf**; inspected but did not use weights-only VibeVoice-Large.
- Planned/verified Chatterbox downloads: **3,208,948,928 bytes**. Runtime wheels added **277,648 bytes**, total wheel payload **3,209,226,576 bytes** under the 20 GB ceiling.
- Derived disk floor: **18.91 GiB before download** (selected bytes + 0.20 GiB work + 0.50 GiB execution margin + 15 GiB safety); **15 GiB after download**.
- Real outputs: Chatterbox plain speech; VibeVoice plain/one-reference/two-reference speech; deterministic model-free character image and video from one `.wgpcharacter` anchor.
- All speech is 24 kHz mono and passes Whisper 0.8.
- Reworked provenance identifies primary `b013…` as the operator-owned LF002/WD-cpow target voice and secondary `e371…` as the WD-cpow VibeVoice-prepared output. Cross-story cloning-reuse consent is **not evidenced**, so both clone rows, Saved voice binding, and Cross-mode identity preservation are not `host_run_verified`.
- Standard renderer preflight failed closed on its global 50 GiB/idle-GPU policy. The recorded lane coexistence preflight passed for the operator-reserved llama-server; no global gate was changed.
- Reviewer verdict remains **pending**; the canonical checker is therefore expected to fail only reviewer approval until PM review.
