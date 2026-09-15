# VibeVoice-7B Dialogue for H3 Films (validated 2026-09-04)

## The working API — ONLY this path (7 attempts to find it)

```python
# venv: ~/vb7-venv (transformers FROM SOURCE + librosa; WanGP's env CANNOT load it)
from transformers import AutoProcessor, AutoModelForTextToWaveform, set_seed
processor = AutoProcessor.from_pretrained("/home/straughter/models/VibeVoice-7B-hf")
model = AutoModelForTextToWaveform.from_pretrained("/home/straughter/models/VibeVoice-7B-hf", device_map="auto")
set_seed(42)
conversation = [{"role": "0", "content": [
    {"type": "audio", "url": "/path/to/voice_ref.wav"},   # plain PATH, not file://
    {"type": "text", "text": "the line to speak"},
]}]
inputs = processor.apply_chat_template(conversation, return_dict=True, tokenize=True,
                                       add_generation_prompt=True).to(model.device, model.dtype)
audio = model.generate(**inputs)
processor.save_audio(audio, "out.wav")
```

## Dead ends (do NOT retry)
- `AutoModelForCausalLM` / `VibeVoiceForConditionalGeneration` direct calls → wrong class / meta-tensor errors
- Hand-built `[S1]` text inputs → 99s of BABBLE ("You... You..."); tags don't anchor a voice
- `file://` audio URLs → resolver rejects; plain path only
- Missing librosa → silent load failure of audio refs
- CPU fp32 run → OOM-killed (needs GPU, bf16, GPU-free at load — 24G card)

## Speaker isolation (USER DOCTRINE — non-negotiable)
ONE generate() call PER TURN with the correct speaker's voice ref.
Never feed a mixed-speaker wav to a render — H3 gives the wrong
character the lips (grandma mouthing the prisoner's line, verified).

## Constraints
- Output floor 2.0s (H3 audio-ref min). Pad short lines: `apad=pad_dur=0.6`
- Voice clone quality needs a CLEAN single-speaker ref (grandma_2s.wav works)
- Multi-speaker single-pass works too (roles "0","1",...) for scene audio,
  but per-turn isolation is what drives lip-sync chains

## Slicing a conversation into turns
Whisper timestamps per turn + `ffmpeg silencedetect` AFTER `highpass=f=100`
(raw silencedetect finds nothing; room tone masks gaps). Cut at turn starts,
pad any sub-2s slice.

## Model location
`vibevoice/VibeVoice-7B-hf` (HF-native conversion, tokenizer included).
The aoi-ot "VibeVoice-Large" mirror is WEIGHTS-ONLY (no tokenizer) — useless alone.
Local: 3090:/home/straughter/models/VibeVoice-7B-hf (symlink into /mnt/bulk).
