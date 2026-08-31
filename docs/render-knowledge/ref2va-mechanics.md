# Ref2VA Mechanics — `verified` (operational constraints)

From the `wangp-h3-multishot` skill + live use on the 3090.

- `audio_prompt_type=A` is **mandatory** when using `audio_guide`.
- Audio references: **2-15s**.
- Render range: **4-15s**.
- Up to **9 image references**.
- Generated audio is **always synthesized** — remux real audio
  afterwards; do not expect the engine's audio track to be the source
  audio.
- `<d>` tags carry lexical content for lip-sync/dialogue.

## Evidence

- WANGP-H3-SKILL: `wangp-h3-multishot` skill (Hermes).
- Consistent with PR-51/PR-52 runtime work in this repo
  (`predict/`, `evaluate/` Ref2VA data plane).
